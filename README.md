# Aadhaar Enrolment Societal Analytics

Analytics on Aadhaar enrolment records: demand trends over time, district pressure, pincode growth clusters, abnormal surges and a 60-day forecast. It ships two front ends built on the same analysis modules:

- **Website** (`docs/`): a static, fully responsive dashboard with state and district filters. Open `docs/index.html` in a browser, or host the `docs/` folder on GitHub Pages.
- **Streamlit app** (`app.py`): the live, interactive version.

> The bundled dataset (`data/sample_aadhaar.csv`) is **synthetic**. It exists so everything runs out of the box. Put your real file at `data/aadhaar.csv` to use it instead.

## Project layout

```
app.py                      Streamlit dashboard
preprocess.py               Load and clean the CSV (dates, totals)
analysis.py                 Trends, district pressure, K-means pincode clusters
anomaly.py                  Isolation Forest surge detection
forecast.py                 Prophet 60-day forecast
build_site_data.py          Runs the modules for every filter choice -> docs/data.js
requirements.txt            Python dependencies
data/sample_aadhaar.csv     Synthetic sample data
scripts/generate_sample_data.py   Regenerates the sample data
docs/index.html             The website
docs/data.js                Pre-computed results the website reads
```

## Dataset format

A CSV with these columns (dates are day-first, e.g. `25-03-2025`):

| column | meaning |
|---|---|
| `date` | enrolment date, `dd-mm-yyyy` |
| `state`, `district` | location names |
| `pincode` | 6-digit pincode |
| `age_0_5`, `age_5_17`, `age_18_greater` | enrolments by age group |

`total` is computed as the sum of the three age columns.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Streamlit app**

```bash
streamlit run app.py
```

**Website**

```bash
python build_site_data.py          # uses data/aadhaar.csv if present, else the sample
# then open docs/index.html in a browser
```

To use a file elsewhere: `python build_site_data.py --input path/to/file.csv`.

Whenever the data changes, run `build_site_data.py` again so `docs/data.js` is refreshed.

## Publish the website on GitHub Pages

Repository **Settings > Pages > Build and deployment**: choose *Deploy from a branch*, branch `main`, folder `/docs`.

## How the analysis works

- **Trends:** total enrolments per day.
- **District pressure:** mean enrolments per record by district. Districts above twice the average are flagged for new enrolment centres.
- **Clusters:** K-means (k=3) on each pincode's average, giving low, medium and high volume tiers.
- **Anomalies:** Isolation Forest (3% contamination) on record totals.
- **Forecast:** Prophet with yearly seasonality, 60 days ahead.

## Notes

- Prophet is required (`forecast.py` imports it). If `pip install prophet` fails on your system, see the Prophet install guide.
- The website needs internet only to load its fonts. Without it, it falls back to system fonts.
