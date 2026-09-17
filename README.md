# Boom Sprayer Calibration

A public Streamlit calculator for field calibration of boom sprayers. It captures individual nozzle catches, calculates spray volume, highlights nozzle outputs that vary by more than ±10% from the mean, and estimates product required per tank.

## Features

- Individual nozzle catch readings in ml
- Mean, total, lowest, and highest nozzle output
- Automatic alert for readings more than ±10% from the mean
- Travel-speed calculation and a 3–12 km/h verification alert
- Spray-volume calculation in L/ha
- Area and product quantity per tank
- Copy-ready text summary and reset control

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Add `app.py`, `requirements.txt`, `.gitignore`, and this `README.md` to the root of the GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Select **Create app**.
4. Choose the repository `plantoptimusprimebat/Boom-Sprayer-Calculator`, branch `main`, and main file path `app.py`.
5. Select **Deploy**.

No secrets, database, or additional configuration are required. The app can be deployed publicly from a public repository.

## Calculation basis

- **Spray volume (L/ha)** = 10,000 × total nozzle catch (L) ÷ [test distance (m) × spray width (m)]
- **Travel speed (km/h)** = test distance (m) ÷ time (s) × 3.6
- **Product per tank (ml)** = tank volume (L) × label rate (ml/ha) ÷ spray volume (L/ha)

This tool is a field-calibration aid. Always follow the registered product label, equipment guidance, PPE requirements, and local operating procedures.
