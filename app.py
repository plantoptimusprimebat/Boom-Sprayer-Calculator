"""Sprayer Calibration hub."""
from __future__ import annotations

from pathlib import Path
import runpy

import streamlit as st

st.set_page_config(page_title="Sprayer Calibration", page_icon="🚜", layout="centered")

st.markdown("""
<style>
:root { color-scheme: dark; }
html, body, [data-testid="stAppViewContainer"], .stApp { background: #101914 !important; color: #f3f8f4 !important; }
[data-testid="stHeader"] { background: #101914 !important; }
[data-testid="stMainBlockContainer"], .stApp p, .stApp li, .stApp label, [data-testid="stCaptionContainer"] { color: #f3f8f4 !important; }
h1, h2, h3 { color: #8bd5a7 !important; }
div[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stExpanderDetails"] { background: #18251d !important; border-color: #385443 !important; }
</style>
""", unsafe_allow_html=True)

CALCULATORS = {
    "boom": {
        "title": "Boom Sprayer",
        "description": "Calibrate boom nozzles using three catch-test replications, nozzle deviation checks, tank products, and Excel export.",
        "button": "Open Boom Sprayer calculator",
    },
    "orchard": {
        "title": "Orchard Sprayer",
        "description": "Calculate timed-catch flow rate from three replications in ml/s or L/s.",
        "button": "Open Orchard Sprayer calculator",
    },
    "mistblower": {
        "title": "Mistblower",
        "description": "Calibration workflow for mistblowers and air-assisted applications.",
        "button": "Open Mistblower calculator",
    },
}


def choose(calculator: str) -> None:
    st.session_state["selected_calculator"] = calculator


selected = st.session_state.get("selected_calculator")
if selected == "boom":
    runpy.run_path(str(Path(__file__).parent / "calculators" / "boom_sprayer.py"))
elif selected == "orchard":
    runpy.run_path(str(Path(__file__).parent / "calculators" / "orchard_sprayer.py"))
elif selected == "mistblower":
    from calculators.placeholder import render
    card = CALCULATORS[selected]
    render(card["title"], card["description"])
else:
    st.title("Sprayer Calibration")
    st.write("Select the equipment type to open the appropriate calibration calculator.")
    st.caption("Boom Sprayer and Orchard Sprayer are available now. Mistblower will be added once its field method is confirmed.")

    columns = st.columns(3)
    for column, key in zip(columns, CALCULATORS):
        card = CALCULATORS[key]
        with column:
            st.subheader(card["title"])
            st.write(card["description"])
            st.button(card["button"], key=f"open_{key}", on_click=choose, args=(key,), use_container_width=True)

    st.divider()
    st.caption("This is a field-calibration aid. Follow registered product labels, equipment guidance, PPE requirements, and local operating procedures.")
