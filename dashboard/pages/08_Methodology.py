import streamlit as st
from utils import *
st.title('Methodology and Downloads')
st.markdown('''### Analysis pipeline
1. **Define pressure** using the submitted batting and bowling rules on pre-ball match state.
2. **Compare with expectation** using state-based expected runs and dismissal or wicket probabilities; measure each player against their usual level.
3. **Rank and stress-test** using the supplied impact, consistency, shrinkage, competition-normalized models, and reliability checks.

### Pressure rules
- **Batting:** striker in slot 4–7; wickets lost ≥ 3 before over 12 or ≥ 4 before over 15; behind the rate (chase: RRR−CRR ≥ 1.5; batting first: at least 15 runs below par).
- **Bowling:** overs 16–20, wickets fallen ≤ 4, batting side scored ≥ 10 runs per over in the previous 12 legal balls.

### Model labels and published values
- **Model A:** main model from the analysis outputs, combining impact and consistency with separate competition normalization and shrinkage. Its rating and 95% interval are shown alongside the submitted Model B score.
- **Model B:** the submitted final order. The source exports call the numeric column `Final_Score`; the dashboard labels it **Model B score** and preserves its supplied values.
- **Model C:** published v3 comparison ranks. The comparison table shows the published rank and pool size (160 batters, 155 bowlers); Brad Evans is marked below minimum.

The supplied Model B score values follow the blended RAE × n/(n+150) export, while the PDF's model description specifies impact-only shrinkage with k=120 for batters and k=60 for bowlers. The supplied batter `death_RAE_per_100_balls` field is empty for all 64 ranking rows. These source-field differences are reported without changing the values or final order.

### Data-count reconciliation
The PDF's 200,999 deliveries and 867 matches are raw-source counts. The dashboard's IPL/T20I analysis parquet has 193,988 deliveries and 837 matches; it omits 30 non-IPL T20 Asia Cup Rising Stars matches. Pressure comparisons use the IPL/T20I scope, and their competition-specific flagged shares match the PDF.

### Data handling and reproducibility
The dashboard reads only precomputed local data at runtime. It excludes super overs as represented in the prepared analysis, uses player IDs for joins and mapped names for display, and keeps final Model B lists fixed. Continuous-pressure controls affect exploratory views; they do not recalculate headline rankings. See the methodology PDF for detailed data audit, formulas, and exclusions.
''')
files=[('Final top 10 · combined','final_top10.csv'),('Top 10 batters','top10_batters.csv'),('Top 10 bowlers','top10_bowlers.csv'),('Full batting rankings','player_batting.csv'),('Full bowling rankings','player_bowling.csv'),('Model comparison','model_comparison.csv'),('Methodology report PDF','methodology_report.pdf')]
for label,name in files:
    p=DATA/name
    if p.exists(): st.download_button(f'Download {label}',p.read_bytes(),file_name=name,mime='application/pdf' if name.endswith('.pdf') else 'text/csv',key='dl_'+name)
else: pass
footer()
