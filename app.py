"""Boom Sprayer Calibration calculator."""
from __future__ import annotations

import math
import streamlit as st

st.set_page_config(page_title="Boom Sprayer Calibration", page_icon="🚜", layout="centered")

# The theme in .streamlit/config.toml is the primary setting.  These explicit
# colours prevent the white-background/white-text conflict if a viewer has a
# different saved Streamlit appearance preference.
st.markdown("""
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
""", unsafe_allow_html=True)

BASE_KEYS = ["distance", "travel_time", "spray_width", "nozzle_count", "tank_volume", "label_rate"]

def valid(value):
    return value is not None and isinstance(value, (int, float)) and math.isfinite(value)

def show(value, decimals=1):
    return f"{value:,.{decimals}f}" if valid(value) else "—"

def reset():
    for key in set(BASE_KEYS) | {key for key in st.session_state if key.startswith("nozzle_")}:
        st.session_state.pop(key, None)

def build_summary(d, seconds, width, readings, total_l, mean, low, high, volume, speed, tank, rate, area, product):
    rows = [
        "BOOM SPRAYER CALIBRATION", "",
        f"Test distance: {show(d)} m", f"Time over distance: {show(seconds)} s", f"Spray width: {show(width, 2)} m", "",
        "Individual nozzle catches:",
    ]
    rows += [f"  Nozzle {i + 1}: {show(r)} ml" for i, r in enumerate(readings)]
    rows += ["", f"Total catch: {show(total_l, 3)} L", f"Mean per nozzle: {show(mean)} ml",
             f"Lowest / highest: {show(low)} / {show(high)} ml", f"Travel speed: {show(speed, 2)} km/h",
             f"Spray volume: {show(volume)} L/ha", "", f"Tank volume: {show(tank, 0)} L",
             f"Label rate: {show(rate, 0)} ml/ha", f"Area per tank: {show(area, 2)} ha",
             f"Product per tank: {show(product, 3)} ml"]
    return "\n".join(rows)

st.title("Boom Sprayer Calibration")
st.write("Enter the catch from each nozzle separately. The calculator finds the average output, identifies uneven nozzles, and calculates spray volume.")

with st.expander("Field test method", expanded=True):
    st.markdown("""1. Measure the test distance: normally **100 m for a tractor** or **30 m for a knapsack**.
2. Travel that distance at normal spraying speed and record the time.
3. Run the sprayer for the same time and catch the output from **every nozzle on the boom**. Enter each catch below in ml.

Use clean water. Clean or replace blocked, worn, or visibly uneven nozzles before spraying.""")

st.header("1. Calibration details")
st.caption("The nozzle count should match the number of nozzles for the boom width entered.")
c1, c2 = st.columns(2)
with c1:
    distance = st.number_input("Test distance (m)", min_value=0.1, value=100.0, step=0.1, key="distance")
    width = st.number_input("Spray width (m)", min_value=0.0, value=None, step=0.01, placeholder="e.g. 12", key="spray_width")
with c2:
    seconds = st.number_input("Time over distance (seconds)", min_value=0.0, value=None, step=0.1, placeholder="e.g. 60", key="travel_time")
    count = int(st.number_input("Number of boom nozzles", min_value=1, max_value=120, value=4, step=1, key="nozzle_count"))

st.subheader("Individual nozzle catches")
st.caption("Catch volume in the same time taken to travel the test distance.")
for start in range(0, count, 3):
    cols = st.columns(3)
    for col, index in zip(cols, range(start, min(start + 3, count))):
        with col:
            st.number_input(f"Nozzle {index + 1} (ml)", min_value=0.0, value=None, step=1.0, placeholder="ml", key=f"nozzle_{index}")

readings = [st.session_state.get(f"nozzle_{i}") for i in range(count)]
entered = [r for r in readings if valid(r) and r >= 0]
complete = len(entered) == count
if complete:
    total_ml = sum(entered); total_l = total_ml / 1000; mean = total_ml / count
    low, high = min(entered), max(entered)
else:
    total_l = mean = low = high = None
volume = 10_000 * total_l / (distance * width) if complete and valid(width) and width > 0 else None
speed = distance / seconds * 3.6 if valid(seconds) and seconds > 0 else None

st.caption(f"**{len(entered)} of {count}** readings entered")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total catch (L)", show(total_l, 3)); m2.metric("Mean per nozzle (ml)", show(mean))
m3.metric("Lowest / highest (ml)", f"{show(low, 0)} / {show(high, 0)}" if complete else "—")
m4.metric("Spray volume (L/ha)", show(volume))

outliers = []
if complete and mean > 0:
    st.markdown("##### Nozzle variation from mean")
    variations = st.columns(3)
    for i, reading in enumerate(readings):
        deviation = (reading - mean) / mean * 100
        flagged = abs(deviation) > 10
        if flagged: outliers.append(i + 1)
        variations[i % 3].caption(f"{'⚠️' if flagged else '✓'} Nozzle {i + 1}: {deviation:+.1f}% vs mean")

if len(entered) < count:
    left = count - len(entered)
    st.warning(f"Enter {left} remaining nozzle reading{'s' if left != 1 else ''} to calculate the result.")
if outliers:
    st.warning(f"Check nozzle{'s' if len(outliers) > 1 else ''} {', '.join(map(str, outliers))}: output differs by more than 10% from the mean.")
if valid(speed) and not 3 <= speed <= 12:
    st.warning("Travel speed is outside the common 3–12 km/h range; verify the measurement and safe operating speed.")
st.info("**Spray volume (L/ha)** = 10,000 × total nozzle catch (L) ÷ [test distance (m) × spray width (m)].")

st.header("2. Speed and product per tank")
c1, c2 = st.columns(2)
with c1:
    tank = st.number_input("Tank volume (L)", min_value=0.0, value=None, step=1.0, placeholder="e.g. 600", key="tank_volume")
with c2:
    rate = st.number_input("Label rate (ml/ha)", min_value=0.0, value=None, step=1.0, placeholder="e.g. 150", key="label_rate")
area = tank / volume if valid(tank) and valid(volume) and volume > 0 else None
product = area * rate if valid(area) and valid(rate) else None
m1, m2, m3 = st.columns(3)
m1.metric("Travel speed (km/h)", show(speed, 2)); m2.metric("Area per tank (ha)", show(area, 2)); m3.metric("Product per tank (ml)", show(product, 3))
st.info("**Product per tank (ml)** = tank volume (L) × label rate (ml/ha) ÷ spray volume (L/ha).")

st.header("Adjusting spray volume")
st.table({"To increase spray volume": ["Larger nozzle", "Higher pressure", "Lower speed"], "To reduce spray volume": ["Smaller nozzle", "Lower pressure", "Higher speed"]})
summary = build_summary(distance, seconds, width, readings, total_l, mean, low, high, volume, speed, tank, rate, area, product)
left, right = st.columns(2)
with left:
    with st.expander("Copy results"):
        st.caption("Use the copy icon in the top-right of the result box.")
        st.code(summary, language=None)
with right:
    st.button("Reset calculator", on_click=reset, type="secondary", use_container_width=True)

st.divider()
st.caption("This is a field-calibration aid. Follow the registered product label, equipment guidance, PPE requirements, and local operating procedures. Check entries and units before mixing or application.")
