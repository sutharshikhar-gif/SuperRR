# SupeRR Selector Season 2 · Round 1

## Who Delivers When It Matters?

An interactive Streamlit and Plotly dashboard for exploring the SupeRR Selector Season 2 Round 1 analysis of player performance under pressure. It presents the prepared analysis outputs; it does not recalculate or alter the pressure definitions or published final rankings.

## Dashboard

The app includes eight pages:

- **Overview** — headline results, Model A uncertainty bars, and selectable ranking views.
- **What is Pressure?** — definitions, pressure-versus-ordinary comparisons, win-probability cross-checks, pressure heatmaps, and score distributions.
- **Match Explorer** — filtered ball-by-ball match state, pressure flags, and two example matches.
- **Batter Deep-Dive** and **Bowler Deep-Dive** — pressure and baseline metrics, player comparisons, match evidence, and context splits.
- **Final Top 10 and Evidence** — the fixed final lists and comparisons with Models A and C.
- **Reliability and Limits** — bootstrap uncertainty, split-half stability, season overlap, and sensitivity results.
- **Methodology and Downloads** — definitions, assumptions, and downloadable analysis files.

The global sidebar filters apply to views that can be filtered. The final submitted rankings remain fixed in the provided order.

## Pressure definitions

**Batting — collapse and rescue:** the striker is in batting positions 4–7; at least 3 wickets have fallen before over 12 or at least 4 before over 15; and the side is behind the rate (a chase has RRR − CRR of at least 1.5, or a first innings is at least 15 runs below par).

**Bowling — set batters hitting freely in the death:** overs 16–20; no more than 4 wickets have fallen; and the batting side scored at least 10 runs per over across the previous 12 legal balls.

The definitions and ranking outputs are fixed for this dashboard release.

## Run locally

Requires Python 3.12. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

Then open the local URL printed by Streamlit, usually `http://localhost:8501`.

The prepared files in `dashboard/data/` are included, so no source data download or preprocessing is needed to run the dashboard.

## Deploy on Streamlit Community Cloud

1. Push this project folder to a GitHub repository, including `dashboard/data/` and `dashboard/requirements.txt`.
2. In Streamlit Community Cloud, select the repository and branch.
3. Set **Main file path** to `dashboard/app.py` and choose Python 3.12.
4. Deploy. The app reads its precomputed local files and does not require secrets or runtime network access.

## Data and methodology notes

The dashboard's analysis scope is IPL and T20I, 2022 onwards. The included delivery table contains 193,988 deliveries across 837 matches. The methodology PDF's raw-source count is 200,999 deliveries across 867 matches; the 30-match difference is from non-IPL T20 Asia Cup Rising Stars matches outside the IPL/T20I analysis scope. The source audit is in `dashboard/data/source_audit.json`.

Headline final lists are fixed to the published submission order. The published v3 Model C ranks are included for comparison. The rebuilt local Model C diagnostic did not reproduce all published ranks, so the dashboard labels the PDF values as **published v3 ranks** rather than substituting its local rebuild.

The PDF describes Model B as impact-only, while the supplied numeric Model B score exports use blended RAE multiplied by `n / (n + 150)`. The dashboard preserves the supplied values and labels them **Model B score**; Model A ratings and their 95% confidence intervals are shown alongside where available. Batter death-over RAE is unavailable in the supplied player table and is displayed as `n/a`.

Reliability results indicate low split-half rank stability (Spearman about 0.1). Some eligible player samples are small (roughly 35–90 pressure balls). Venue and opposition strength are not adjusted for, and Model C is a weak bowler cross-check. See the Methodology and Reliability pages for detail.

## Rebuild prepared dashboard data (optional)

This step is only needed when regenerating `dashboard/data/` from the original source and analysis exports. It requires the source files and PDF v3 locally:

```bash
python dashboard/prep_dashboard_data.py \
  --source-dir /path/to/source-files \
  --analysis-dir /path/to/analysis-outputs \
  --pdf dashboard/data/methodology_report.pdf \
  --allow-model-c-mismatch
```

The mismatch flag is required when the local simple Model C rebuild differs from published v3 ranks. The script uses the published ranks for dashboard comparisons and retains rebuilt diagnostic outputs separately. It checks the existing fixed final lists and will stop rather than silently changing them.

## Tests and screenshots

From the repository root, run the data regression checks:

```bash
python -m unittest discover -s dashboard/tests -v
```

To capture full-page screenshots with the dashboard running, install Playwright and a supported browser, then run:

```bash
python -m pip install playwright
python -m playwright install chromium
python dashboard/screenshots/capture_screenshots.py
```

The eight PNG captures are stored in `dashboard/screenshots/`.

## Project layout

```text
dashboard/
├── app.py
├── pages/                 # Streamlit pages
├── data/                  # Precomputed analysis tables and methodology PDF
├── screenshots/           # Full-page captures and capture script
├── tests/                 # Data regression checks
├── prep_dashboard_data.py # Optional source-to-dashboard preparation
├── utils.py
├── requirements.txt
└── .streamlit/config.toml
```
