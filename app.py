"""Boom Sprayer Calibration calculator for Streamlit."""

from __future__ import annotations

import math
from typing import Any

import streamlit as st


PAGE_TITLE = "Boom Sprayer Calibration"
BASE_KEYS = [
    "distance",
    "travel_time",
    "spray_width",
    "nozzle_count",
    "tank_volume",
    "label_rate",
]


st.set_page_config(page_title=PAGE_TITLE, page_icon="🚜", layout="centered")

st.markdown(
    """
    <style>
      .stApp { background: #f1f4f1; }
      h1, h2, h3 { color: #0b5b3d; }
      div[data-testid="stMetric"] {
        background: #e8f4ed;
        border-radius: 10px;
        padding: 0.65rem 0.8rem;
      }
      div[data-testid="stMetricLabel"] { color: #426452; }
      div[data-testid="stMetricValue"] { color: #0b5b3d; }
    </style>
    """,
    unsafe_allow_html=True,
)


def is_number(value: Any) -> bool:
    """Return True only for finite numeric values."""
    return value is not None and isinstance(value, (int, float)) and math.isfinite(value)


def format_value(value: Any, decimals: int = 1) -> str:
    """Format a number for display, or show a dash when it is unavailable."""
    if not is_number(value):
        return "—"
    return f"{value:,.{decimals}f}"


def reset_calculator() -> None:
    """Clear calculator values and restore the original defaults."""
    keys_to_remove = set(BASE_KEYS) | {
        key for key in st.session_state if key.startswith("nozzle_")
    }
    for key in keys_to_remove:
        st.session_state.pop(key, None)


def nozzle_readings(count: int) -> list[float | None]:
    """Return current readings for the displayed nozzles."""
    return [st.session_state.get(f"nozzle_{index}") for index in range(count)]


def results_text(
    distance: float,
    travel_time: float | None,
    width: float | None,
    readings: list[float | None],
    total_litres: float | None,
    mean_ml: float | None,
    low_ml: float | None,
    high_ml: float | None,
    spray_volume: float | None,
    speed: float | None,
    tank_volume: float | None,
    label_rate: float | None,
    area_per_tank: float | None,
    product_per_tank: float | None,
) -> str:
    """Build a plain-text calculation summary that Streamlit can copy."""
    lines = [
        "BOOM SPRAYER CALIBRATION",
        "",
        f"Test distance: {format_value(distance, 1)} m",
        f"Time over distance: {format_value(travel_time, 1)} s",
        f"Spray width: {format_value(width, 2)} m",
        "",
        "Individual nozzle catches:",
    ]
    lines.extend(
        f"  Nozzle {index + 1}: {format_value(reading, 1)} ml"
        for index, reading in enumerate(readings)
    )
    lines.extend(
        [
            "",
            f"Total catch: {format_value(total_litres, 3)} L",
            f"Mean per nozzle: {format_value(mean_ml, 1)} ml",
            f"Lowest / highest: {format_value(low_ml, 1)} / {format_value(high_ml, 1)} ml",
            f"Travel speed: {format_value(speed, 2)} km/h",
            f"Spray volume: {format_value(spray_volume, 1)} L/ha",
            "",
            f"Tank volume: {format_value(tank_volume, 0)} L",
            f"Label rate: {format_value(label_rate, 0)} ml/ha",
            f"Area per tank: {format_value(area_per_tank, 2)} ha",
            f"Product per tank: {format_value(product_per_tank, 3)} ml",
        ]
    )
    return "\n".join(lines)


st.title(PAGE_TITLE)
st.write(
    "Enter the catch from each nozzle separately. The calculator finds the average "
    "output, identifies uneven nozzles, and calculates spray volume."
)

with st.expander("Field test method", expanded=True):
    st.markdown(
        """
1. Measure the test distance: normally **100 m for a tractor** or **10 m for a knapsack**.
2. Travel that distance at normal spraying speed and record the time.
3. Run the sprayer for the same time and catch the output from **every nozzle on the boom**. Enter each catch below in ml.

Use clean water. Clean or replace blocked, worn, or visibly uneven nozzles before spraying.
        """
    )

st.header("1. Calibration details")
st.caption("The nozzle count should match the number of nozzles for the boom width entered.")

left_column, right_column = st.columns(2)
with left_column:
    distance = st.number_input(
        "Test distance (m)",
        min_value=0.1,
        step=0.1,
        value=100.0,
        key="distance",
    )
    width = st.number_input(
        "Spray width (m)",
        min_value=0.0,
        step=0.01,
        value=None,
        placeholder="e.g. 12",
        key="spray_width",
    )
with right_column:
    travel_time = st.number_input(
        "Time over distance (seconds)",
        min_value=0.0,
        step=0.1,
        value=None,
        placeholder="e.g. 60",
        key="travel_time",
    )
    nozzle_count = st.number_input(
        "Number of boom nozzles",
        min_value=1,
        max_value=120,
        step=1,
        value=4,
        key="nozzle_count",
    )

nozzle_count = int(nozzle_count)
st.subheader("Individual nozzle catches")
st.caption("Catch volume in the same time taken to travel the test distance.")

# Widget keys persist when the count is temporarily reduced, so a user's prior
# readings are retained if the nozzle count is increased again.

for start in range(0, nozzle_count, 3):
    columns = st.columns(3)
    for column, index in zip(columns, range(start, min(start + 3, nozzle_count))):
        with column:
            st.number_input(
                f"Nozzle {index + 1} (ml)",
                min_value=0.0,
                step=1.0,
                value=None,
                placeholder="ml",
                key=f"nozzle_{index}",
            )

readings = nozzle_readings(nozzle_count)
valid_readings = [reading for reading in readings if is_number(reading) and reading >= 0]
complete = len(valid_readings) == nozzle_count

if complete:
    total_ml = sum(valid_readings)
    total_litres = total_ml / 1000
    mean_ml = total_ml / nozzle_count
    low_ml = min(valid_readings)
    high_ml = max(valid_readings)
else:
    total_litres = mean_ml = low_ml = high_ml = None

spray_volume = (
    10_000 * total_litres / (distance * width)
    if complete and is_number(width) and width > 0
    else None
)
speed = distance / travel_time * 3.6 if is_number(travel_time) and travel_time > 0 else None

st.caption(f"**{len(valid_readings)} of {nozzle_count}** readings entered")
metric_columns = st.columns(4)
metric_columns[0].metric("Total catch (L)", format_value(total_litres, 3))
metric_columns[1].metric("Mean per nozzle (ml)", format_value(mean_ml, 1))
metric_columns[2].metric(
    "Lowest / highest (ml)",
    f"{format_value(low_ml, 0)} / {format_value(high_ml, 0)}" if complete else "—",
)
metric_columns[3].metric("Spray volume (L/ha)", format_value(spray_volume, 1))

outlier_numbers: list[int] = []
if complete and mean_ml and mean_ml > 0:
    st.markdown("##### Nozzle variation from mean")
    variation_columns = st.columns(3)
    for index, reading in enumerate(valid_readings):
        deviation = (reading - mean_ml) / mean_ml * 100
        indicator = "⚠️" if abs(deviation) > 10 else "✓"
        if abs(deviation) > 10:
            outlier_numbers.append(index + 1)
        variation_columns[index % 3].caption(
            f"{indicator} Nozzle {index + 1}: {deviation:+.1f}% vs mean"
        )

warnings: list[str] = []
remaining = nozzle_count - len(valid_readings)
if remaining:
    warnings.append(f"Enter {remaining} remaining nozzle reading{'s' if remaining != 1 else ''} to calculate the result.")
if outlier_numbers:
    warnings.append(
        f"Check nozzle{'s' if len(outlier_numbers) > 1 else ''} "
        f"{', '.join(map(str, outlier_numbers))}: output differs by more than 10% from the mean."
    )
if is_number(speed) and (speed < 3 or speed > 12):
    warnings.append("Travel speed is outside the common 3–12 km/h range; verify the measurement and safe operating speed.")
for warning in warnings:
    st.warning(warning)

st.info(
    "**Spray volume (L/ha)** = 10,000 × total nozzle catch (L) ÷ "
    "[test distance (m) × spray width (m)]."
)

st.header("2. Speed and product per tank")
tank_column, rate_column = st.columns(2)
with tank_column:
    tank_volume = st.number_input(
        "Tank volume (L)",
        min_value=0.0,
        step=1.0,
        value=None,
        placeholder="e.g. 600",
        key="tank_volume",
    )
with rate_column:
    label_rate = st.number_input(
        "Label rate (ml/ha)",
        min_value=0.0,
        step=1.0,
        value=None,
        placeholder="e.g. 150",
        key="label_rate",
    )

area_per_tank = (
    tank_volume / spray_volume
    if is_number(tank_volume) and is_number(spray_volume) and spray_volume > 0
    else None
)
product_per_tank = (
    area_per_tank * label_rate
    if is_number(area_per_tank) and is_number(label_rate)
    else None
)

speed_column, area_column, product_column = st.columns(3)
speed_column.metric("Travel speed (km/h)", format_value(speed, 2))
area_column.metric("Area per tank (ha)", format_value(area_per_tank, 2))
product_column.metric("Product per tank (ml)", format_value(product_per_tank, 3))
st.info("**Product per tank (ml)** = tank volume (L) × label rate (ml/ha) ÷ spray volume (L/ha).")

st.header("Adjusting spray volume")
st.table(
    {
        "To increase spray volume": ["Larger nozzle", "Higher pressure", "Lower speed"],
        "To reduce spray volume": ["Smaller nozzle", "Lower pressure", "Higher speed"],
    }
)

summary = results_text(
    distance,
    travel_time,
    width,
    readings,
    total_litres,
    mean_ml,
    low_ml,
    high_ml,
    spray_volume,
    speed,
    tank_volume,
    label_rate,
    area_per_tank,
    product_per_tank,
)

copy_column, reset_column = st.columns(2)
with copy_column:
    with st.expander("Copy results", expanded=False):
        st.caption("Use the copy icon in the top-right of the result box.")
        st.code(summary, language=None)
with reset_column:
    st.button("Reset calculator", type="secondary", on_click=reset_calculator, use_container_width=True)

st.divider()
st.caption(
    "This is a field-calibration aid. Follow the registered product label, equipment guidance, "
    "PPE requirements, and local operating procedures. Check entries and units before mixing or application."
)
