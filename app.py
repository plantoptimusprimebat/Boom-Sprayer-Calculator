"""Boom Sprayer Calibration calculator."""
from __future__ import annotations

import math
from io import BytesIO

from datetime import datetime
from zoneinfo import Zoneinfo

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import streamlit as st

st.set_page_config(page_title="Boom Sprayer Calibration", page_icon="🚜", layout="centered")

# The theme in .streamlit/config.toml is the primary setting. These explicit
# colours prevent a white-background/white-text conflict if a visitor has a
# different saved Streamlit appearance preference.
st.markdown(
    """
<style>
:root { color-scheme: dark; }
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #101914 !important;
    color: #f3f8f4 !important;
}
[data-testid="stHeader"] { background: #101914 !important; }
[data-testid="stMainBlockContainer"], .stApp p, .stApp li, .stApp label,
[data-testid="stCaptionContainer"] { color: #f3f8f4 !important; }
h1, h2, h3 { color: #8bd5a7 !important; }
[data-testid="stExpander"], [data-testid="stExpanderDetails"] {
    background: #18251d !important; border-color: #385443 !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary span {
    color: #f3f8f4 !important;
}
div[data-baseweb="input"] { background: #1a2920 !important; border-color: #52705d !important; }
div[data-baseweb="input"] input { color: #f3f8f4 !important; -webkit-text-fill-color: #f3f8f4 !important; }
div[data-baseweb="input"] input::placeholder { color: #aabaae !important; -webkit-text-fill-color: #aabaae !important; opacity: 1; }
div[data-testid="stMetric"] { background: #1a2920 !important; border: 1px solid #385443; border-radius: 10px; padding: .65rem .8rem; }
div[data-testid="stMetricLabel"] p { color: #b9d1c0 !important; }
div[data-testid="stMetricValue"] { color: #8bd5a7 !important; }
[data-testid="stAlert"], [data-testid="stCode"] { color: #f3f8f4 !important; }
[data-testid="stCode"] { background: #18251d !important; }
</style>
""",
    unsafe_allow_html=True,
)

BASE_KEYS = [
    "distance",
    "travel_time",
    "spray_width",
    "nozzle_count",
    "tank_volume",
    "product_count",
]
UNIT_OPTIONS = ("ml", "g", "L", "kg")


def valid(value: object) -> bool:
    """Return true only for finite numbers."""
    return value is not None and isinstance(value, (int, float)) and math.isfinite(value)


def show(value: object, decimals: int = 1) -> str:
    """Format a number for display or return a dash when unavailable."""
    return f"{value:,.{decimals}f}" if valid(value) else "—"


def reset() -> None:
    """Restore the original calculator state, including all product rows."""
    keys = set(BASE_KEYS) | {
        key
        for key in st.session_state
        if key.startswith("nozzle_") or key.startswith("product_")
    }
    for key in keys:
        st.session_state.pop(key, None)


def product_entries(product_count: int, area_per_tank: float | None) -> list[dict[str, object]]:
    """Render product rows and return their calculated tank quantities."""
    entries: list[dict[str, object]] = []
    for index in range(product_count):
        st.markdown(f"##### Product {index + 1}")
        name_column, rate_column, unit_column, amount_column = st.columns([1.5, 1.15, 0.85, 1.15])
        with name_column:
            name = st.text_input(
                "Product name",
                placeholder=f"Product {index + 1}",
                key=f"product_name_{index}",
                label_visibility="visible",
            ).strip()
        with rate_column:
            rate = st.number_input(
                "Label rate",
                min_value=0.0,
                step=0.1,
                value=None,
                placeholder="e.g. 150",
                key=f"product_rate_{index}",
            )
        with unit_column:
            unit = st.selectbox(
                "Rate unit",
                options=UNIT_OPTIONS,
                key=f"product_unit_{index}",
            )
        amount = area_per_tank * rate if valid(area_per_tank) and valid(rate) else None
        with amount_column:
            st.metric(f"Per tank ({unit})", show(amount, 3))
        entries.append(
            {
                "name": name or f"Product {index + 1}",
                "rate": rate,
                "unit": unit,
                "amount": amount,
            }
        )
    return entries


def build_summary(
    distance: float,
    seconds: float | None,
    width: float | None,
    readings: list[float | None],
    total_litres: float | None,
    mean: float | None,
    low: float | None,
    high: float | None,
    spray_volume: float | None,
    speed: float | None,
    tank_volume: float | None,
    area_per_tank: float | None,
    products: list[dict[str, object]],
) -> str:
    """Build the copy-ready result summary."""
    rows = [
        "BOOM SPRAYER CALIBRATION",
        "",
        f"Test distance: {show(distance)} m",
        f"Time over distance: {show(seconds)} s",
        f"Spray width: {show(width, 2)} m",
        "",
        "Individual nozzle catches:",
    ]
    rows.extend(f"  Nozzle {index + 1}: {show(reading)} ml" for index, reading in enumerate(readings))
    rows.extend(
        [
            "",
            f"Total catch: {show(total_litres, 3)} L",
            f"Mean per nozzle: {show(mean)} ml",
            f"Lowest / highest: {show(low)} / {show(high)} ml",
            f"Travel speed: {show(speed, 2)} km/h",
            f"Spray volume: {show(spray_volume)} L/ha",
            "",
            f"Tank volume: {show(tank_volume, 0)} L",
            f"Area per tank: {show(area_per_tank, 2)} ha",
            "",
            "Products per tank:",
        ]
    )
    for product in products:
        unit = product["unit"]
        rows.append(
            f"  {product['name']}: {show(product['rate'], 3)} {unit}/ha → "
            f"{show(product['amount'], 3)} {unit} per tank"
        )
    return "\n".join(rows)


def build_excel_export(
    distance: float,
    seconds: float | None,
    width: float | None,
    readings: list[float | None],
    tank_volume: float | None,
    products: list[dict[str, object]],
) -> bytes:
    """Create a formatted Excel workbook with editable inputs and formulas."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Calibration"
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"

    dark_green = "0B5B3D"
    soft_green = "E8F4ED"
    pale_yellow = "FFF2CC"
    white = "FFFFFF"
    thin_green = Side(style="thin", color="7FA98B")
    section_fill = PatternFill("solid", fgColor=dark_green)
    input_fill = PatternFill("solid", fgColor=pale_yellow)
    result_fill = PatternFill("solid", fgColor=soft_green)
    border = Border(left=thin_green, right=thin_green, top=thin_green, bottom=thin_green)

    sheet.merge_cells("A1:D1")
    sheet["A1"] = "Boom Sprayer Calibration Results"
    sheet["A1"].font = Font(bold=True, color=white, size=16)
    sheet["A1"].fill = section_fill
    sheet["A1"].alignment = Alignment(horizontal="center")
    sheet.row_dimensions[1].height = 26

    sheet["A3"] = "Calibration inputs"
    sheet["A3"].font = Font(bold=True, color=white)
    sheet["A3"].fill = section_fill
    sheet.merge_cells("A3:D3")

    inputs = [
        ("Test distance (m)", distance),
        ("Time over distance (seconds)", seconds),
        ("Spray width (m)", width),
        ("Number of boom nozzles", len(readings)),
        ("Tank volume (L)", tank_volume),
    ]
    for row, (label, value) in enumerate(inputs, start=4):
        sheet.cell(row, 1, label)
        value_cell = sheet.cell(row, 2, value)
        value_cell.fill = input_fill
        value_cell.border = border
        value_cell.font = Font(color="0000FF")
        value_cell.number_format = "0.000"
        sheet.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)

    nozzle_header_row = 10
    sheet.cell(nozzle_header_row, 1, "Nozzle readings")
    sheet.cell(nozzle_header_row, 1).font = Font(bold=True, color=white)
    sheet.cell(nozzle_header_row, 1).fill = section_fill
    sheet.merge_cells(start_row=nozzle_header_row, start_column=1, end_row=nozzle_header_row, end_column=4)
    for column, heading in enumerate(["Nozzle", "Catch (ml)", "Deviation vs mean", "Status"], start=1):
        cell = sheet.cell(nozzle_header_row + 1, column, heading)
        cell.font = Font(bold=True, color=white)
        cell.fill = section_fill
        cell.border = border

    nozzle_first_row = nozzle_header_row + 2
    nozzle_last_row = nozzle_first_row + len(readings) - 1
    for index, reading in enumerate(readings, start=1):
        row = nozzle_first_row + index - 1
        sheet.cell(row, 1, index)
        reading_cell = sheet.cell(row, 2, reading)
        reading_cell.fill = input_fill
        reading_cell.border = border
        reading_cell.font = Font(color="0000FF")
        reading_cell.number_format = "0.000"
        deviation_cell = sheet.cell(row, 3, f'=IFERROR((B{row}-$B${nozzle_last_row + 4})/$B${nozzle_last_row + 4},"")')
        deviation_cell.number_format = "0.0%"
        status_cell = sheet.cell(row, 4, f'=IF(C{row}="","",IF(ABS(C{row})>10%,"Check","OK"))')
        for column in range(1, 5):
            sheet.cell(row, column).border = border

    result_header_row = nozzle_last_row + 2
    sheet.cell(result_header_row, 1, "Calculated results")
    sheet.cell(result_header_row, 1).font = Font(bold=True, color=white)
    sheet.cell(result_header_row, 1).fill = section_fill
    sheet.merge_cells(start_row=result_header_row, start_column=1, end_row=result_header_row, end_column=4)

    result_rows = [
        ("Total catch (L)", f'=IFERROR(SUM(B{nozzle_first_row}:B{nozzle_last_row})/1000,"")', "0.000"),
        ("Mean per nozzle (ml)", f'=IFERROR(AVERAGE(B{nozzle_first_row}:B{nozzle_last_row}),"")', "0.000"),
        ("Lowest nozzle catch (ml)", f'=IFERROR(MIN(B{nozzle_first_row}:B{nozzle_last_row}),"")', "0.000"),
        ("Highest nozzle catch (ml)", f'=IFERROR(MAX(B{nozzle_first_row}:B{nozzle_last_row}),"")', "0.000"),
        ("Spray volume (L/ha)", f'=IFERROR(10000*B{result_header_row + 1}/($B$4*$B$6),"")', "0.000"),
        ("Travel speed (km/h)", '=IFERROR($B$4/$B$5*3.6,"")', "0.00"),
        ("Area per tank (ha)", f'=IFERROR($B$8/B{result_header_row + 5},"")', "0.000"),
    ]
    for offset, (label, formula, number_format) in enumerate(result_rows, start=1):
        row = result_header_row + offset
        sheet.cell(row, 1, label)
        result_cell = sheet.cell(row, 2, formula)
        result_cell.number_format = number_format
        result_cell.fill = result_fill
        result_cell.font = Font(bold=True)
        for column in range(1, 5):
            sheet.cell(row, column).border = border
        sheet.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)

    area_cell = f"B{result_header_row + len(result_rows)}"
    product_header_row = result_header_row + len(result_rows) + 2
    sheet.cell(product_header_row, 1, "Products per tank")
    sheet.cell(product_header_row, 1).font = Font(bold=True, color=white)
    sheet.cell(product_header_row, 1).fill = section_fill
    sheet.merge_cells(start_row=product_header_row, start_column=1, end_row=product_header_row, end_column=4)
    for column, heading in enumerate(["Product", "Label rate", "Unit", "Required per tank"], start=1):
        cell = sheet.cell(product_header_row + 1, column, heading)
        cell.font = Font(bold=True, color=white)
        cell.fill = section_fill
        cell.border = border

    for index, product in enumerate(products, start=1):
        row = product_header_row + 1 + index
        name_cell = sheet.cell(row, 1, product["name"])
        rate_cell = sheet.cell(row, 2, product["rate"])
        unit_cell = sheet.cell(row, 3, product["unit"])
        amount_cell = sheet.cell(row, 4, f'=IFERROR({area_cell}*B{row},"")')
        for cell in (name_cell, rate_cell, unit_cell):
            cell.fill = input_fill
            cell.font = Font(color="0000FF")
        rate_cell.number_format = "0.000"
        amount_cell.number_format = "0.000"
        amount_cell.fill = result_fill
        amount_cell.font = Font(bold=True)
        for column in range(1, 5):
            sheet.cell(row, column).border = border

    note_row = product_header_row + len(products) + 4
    sheet.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=4)
    sheet.cell(note_row, 1, "Yellow cells are editable inputs; green cells are calculated in Excel.")
    sheet.cell(note_row, 1).font = Font(italic=True, color="555555")

    sheet.column_dimensions["A"].width = 30
    sheet.column_dimensions["B"].width = 18
    sheet.column_dimensions["C"].width = 20
    sheet.column_dimensions["D"].width = 22
    sheet.freeze_panes = "A4"

    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


st.title("Boom Sprayer Calibration")
st.write(
    "Enter the catch from each nozzle separately. The calculator finds the average "
    "output, identifies uneven nozzles, and calculates spray volume."
)

with st.expander("Field test method", expanded=True):
    st.markdown(
        """1. Measure the test distance: normally **100 m for a tractor** or **30 m for a knapsack**.
2. Travel that distance at normal spraying speed and record the time.
3. Run the sprayer for the same time and catch the output from **every nozzle on the boom**. Enter each catch below in ml.

Use clean water. Clean or replace blocked, worn, or visibly uneven nozzles before spraying."""
    )

st.header("1. Calibration details")
st.caption("The nozzle count should match the number of nozzles for the boom width entered.")
column_1, column_2 = st.columns(2)
with column_1:
    distance = st.number_input("Test distance (m)", min_value=0.1, value=100.0, step=0.1, key="distance")
    width = st.number_input("Spray width (m)", min_value=0.0, value=None, step=0.01, placeholder="e.g. 12", key="spray_width")
with column_2:
    seconds = st.number_input("Time over distance (seconds)", min_value=0.0, value=None, step=0.1, placeholder="e.g. 60", key="travel_time")
    count = int(st.number_input("Number of boom nozzles", min_value=1, max_value=120, value=4, step=1, key="nozzle_count"))

st.subheader("Individual nozzle catches")
st.caption("Catch volume in the same time taken to travel the test distance.")
for start in range(0, count, 3):
    columns = st.columns(3)
    for column, index in zip(columns, range(start, min(start + 3, count))):
        with column:
            st.number_input(
                f"Nozzle {index + 1} (ml)",
                min_value=0.0,
                value=None,
                step=1.0,
                placeholder="ml",
                key=f"nozzle_{index}",
            )

readings = [st.session_state.get(f"nozzle_{index}") for index in range(count)]
entered = [reading for reading in readings if valid(reading) and reading >= 0]
complete = len(entered) == count
if complete:
    total_ml = sum(entered)
    total_litres = total_ml / 1000
    mean = total_ml / count
    low, high = min(entered), max(entered)
else:
    total_litres = mean = low = high = None

spray_volume = 10_000 * total_litres / (distance * width) if complete and valid(width) and width > 0 else None
speed = distance / seconds * 3.6 if valid(seconds) and seconds > 0 else None

st.caption(f"**{len(entered)} of {count}** readings entered")
metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Total catch (L)", show(total_litres, 3))
metric_2.metric("Mean per nozzle (ml)", show(mean))
metric_3.metric("Lowest / highest (ml)", f"{show(low, 0)} / {show(high, 0)}" if complete else "—")
metric_4.metric("Spray volume (L/ha)", show(spray_volume))

outliers: list[int] = []
if complete and mean > 0:
    st.markdown("##### Nozzle variation from mean")
    variation_columns = st.columns(3)
    for index, reading in enumerate(readings):
        deviation = (reading - mean) / mean * 100
        flagged = abs(deviation) > 10
        if flagged:
            outliers.append(index + 1)
        variation_columns[index % 3].caption(f"{'⚠️' if flagged else '✓'} Nozzle {index + 1}: {deviation:+.1f}% vs mean")

if len(entered) < count:
    remaining = count - len(entered)
    st.warning(f"Enter {remaining} remaining nozzle reading{'s' if remaining != 1 else ''} to calculate the result.")
if outliers:
    st.warning(f"Check nozzle{'s' if len(outliers) > 1 else ''} {', '.join(map(str, outliers))}: output differs by more than 10% from the mean.")
if valid(speed) and not 3 <= speed <= 12:
    st.warning("Travel speed is outside the common 3–12 km/h range; verify the measurement and safe operating speed.")
st.info("**Spray volume (L/ha)** = 10,000 × total nozzle catch (L) ÷ [test distance (m) × spray width (m)].")

st.header("2. Speed and products per tank")
st.caption("Enter the tank volume once, then add each product and its registered label rate.")
tank_column, product_count_column = st.columns(2)
with tank_column:
    tank_volume = st.number_input("Tank volume (L)", min_value=0.0, value=None, step=1.0, placeholder="e.g. 600", key="tank_volume")
with product_count_column:
    product_count = int(
        st.number_input(
            "Number of products to add",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key="product_count",
        )
    )

area_per_tank = tank_volume / spray_volume if valid(tank_volume) and valid(spray_volume) and spray_volume > 0 else None
speed_metric, area_metric = st.columns(2)
speed_metric.metric("Travel speed (km/h)", show(speed, 2))
area_metric.metric("Area per tank (ha)", show(area_per_tank, 2))

st.subheader("Products to add")
st.caption("Use the product's registered label rate. Product amounts are calculated from the area covered by one tank.")
products = product_entries(product_count, area_per_tank)
st.info("**Product per tank** = area per tank (ha) × label rate (unit/ha). Check each product label and approved tank-mix guidance before application.")

st.header("Adjusting spray volume")
st.table(
    {
        "To increase spray volume": ["Larger nozzle", "Higher pressure", "Lower speed"],
        "To reduce spray volume": ["Smaller nozzle", "Lower pressure", "Higher speed"],
    }
)

summary = build_summary(
    distance,
    seconds,
    width,
    readings,
    total_litres,
    mean,
    low,
    high,
    spray_volume,
    speed,
    tank_volume,
    area_per_tank,
    products,
)
excel_file = build_excel_export(distance, seconds, width, readings, tank_volume, products)
copy_column, export_column, reset_column = st.columns(3)
with copy_column:
    with st.expander("Copy results"):
        st.caption("Use the copy icon in the top-right of the result box.")
        st.code(summary, language=None)
with export_column:
    export_timestamp = datetime.now(
    ZoneInfo("Africa/Johannesburg")
).strftime("%Y_%m_%d %H-%M")
    st.download_button(
        "Export results to Excel",
        data=excel_file,
        file_name=f"boom_sprayer_calibration_{export_timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with reset_column:
    st.button("Reset calculator", on_click=reset, type="secondary", use_container_width=True)

st.divider()
st.caption(
    "This is a field-calibration aid. Follow the registered product label, equipment guidance, "
    "PPE requirements, and local operating procedures. Check entries and units before mixing or application."
)
