# Task 2: Global Sustainable Energy Dashboard

This Streamlit dashboard uses `global-data-on-sustainable-energy.csv` to explore global sustainable energy indicators from 2000 to 2020.

## Files

- `app.py` — main Streamlit dashboard
- `global-data-on-sustainable-energy.csv` — dataset
- `requirements.txt` — Python packages needed to run the dashboard
- `design_report_draft.md` — report draft you can adapt for submission

## How to run in VS Code

1. Create a new folder for Task 2.
2. Put `app.py`, `requirements.txt`, and `global-data-on-sustainable-energy.csv` in the same folder.
3. Open the folder in VS Code.
4. Open the terminal in VS Code.
5. Install the required packages:

```bash
pip install -r requirements.txt
```

6. Run the dashboard:

```bash
streamlit run app.py
```

The dashboard should open in your browser automatically.

## Dashboard visualisations

1. Geographic distribution map
2. Global average trend over time
3. Electricity generation mix over time
4. Country drill-down trend
5. Country ranking bar chart
6. GDP per capita vs energy consumption scatter plot
7. Electricity access vs clean fuels access scatter plot
8. Correlation heatmap

## Important data note

The CO₂ emissions column is mostly missing for 2020, so 2019 is used as the recommended default year for CO₂-based comparisons.
