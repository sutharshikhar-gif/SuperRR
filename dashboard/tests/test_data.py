"""Regression checks against methodology report v3 and fixed submitted lists."""
import json
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

BAT_FINAL = [
    "Heinrich Klaasen", "Suryakumar Yadav", "Shivam Dube", "Namboori Tilak Varma",
    "Shashank Singh", "Tristan Stubbs", "Moeen Ali", "Marcus Stoinis", "Tim David", "Towhid Hridoy",
]
BOWL_FINAL = [
    "Matheesha Pathirana", "Joshua Little", "Wanindu Hasaranga", "Rashid Khan", "Khaleel Ahmed",
    "Brad Evans", "Vaibhav Arora", "Mitchell Starc", "Dushmantha Chameera", "Lungi Ngidi",
]
MODEL_A_BAT = ["Shashank Singh", "Jimmy Neesham", "Mark Chapman", "Shivam Dube", "Suryakumar Yadav", "Andre Russell", "Marcus Stoinis", "George Dockrell", "Heinrich Klaasen", "Moeen Ali"]
MODEL_A_BOWL = ["Joshua Little", "Khaleel Ahmed", "Vaibhav Arora", "Sunil Narine", "Brad Evans", "Hardik Pandya", "Mitchell Starc", "Rashid Khan", "Lungi Ngidi", "Shaheen Afridi"]

# PDF Table 3: pressure balls/matches, pressure SR/economy, baseline, Model A rating/CI, inclusion %.
TABLE3 = {
    "Shashank Singh": (90,10,180.0,158.1,1.86,.12,2.47,58.0),
    "Shivam Dube": (186,23,165.1,153.0,1.42,-.26,2.39,51.0),
    "Suryakumar Yadav": (241,18,147.3,168.7,1.30,-.27,1.63,35.0),
    "Marcus Stoinis": (185,19,153.5,154.2,1.24,-.38,1.65,34.0),
    "Heinrich Klaasen": (244,20,150.4,171.2,1.10,-.01,1.82,42.5),
    "Moeen Ali": (129,11,150.4,140.9,1.09,-.04,1.63,35.0),
    "Joshua Little": (38,8,9.47,7.72,2.52,.92,3.13,51.5),
    "Khaleel Ahmed": (119,19,11.14,8.69,1.90,-.14,2.33,60.5),
    "Vaibhav Arora": (48,10,9.62,9.78,1.88,.24,2.52,68.5),
    "Brad Evans": (39,8,8.46,9.09,1.38,-.08,2.55,39.5),
    "Mitchell Starc": (34,8,8.12,9.97,1.08,-.37,2.51,19.0),
    "Rashid Khan": (81,22,10.37,7.34,1.06,-.49,1.76,39.5),
    "Lungi Ngidi": (71,13,10.90,8.67,.91,-.33,1.56,31.0),
}

PDF_C = {
    "Batter": {"Heinrich Klaasen":49,"Suryakumar Yadav":45,"Shivam Dube":60,"Namboori Tilak Varma":13,"Shashank Singh":4,"Tristan Stubbs":6,"Moeen Ali":98,"Marcus Stoinis":69,"Tim David":5,"Towhid Hridoy":16},
    "Bowler": {"Matheesha Pathirana":47,"Joshua Little":55,"Wanindu Hasaranga":12,"Rashid Khan":7,"Khaleel Ahmed":58,"Brad Evans":None,"Vaibhav Arora":133,"Mitchell Starc":51,"Dushmantha Chameera":137,"Lungi Ngidi":35},
}
PDF_A = {
    "Batter":{"Heinrich Klaasen":9,"Suryakumar Yadav":5,"Shivam Dube":4,"Namboori Tilak Varma":None,"Shashank Singh":1,"Tristan Stubbs":None,"Moeen Ali":10,"Marcus Stoinis":7,"Tim David":None,"Towhid Hridoy":None},
    "Bowler":{"Matheesha Pathirana":None,"Joshua Little":1,"Wanindu Hasaranga":None,"Rashid Khan":8,"Khaleel Ahmed":2,"Brad Evans":5,"Vaibhav Arora":3,"Mitchell Starc":7,"Dushmantha Chameera":None,"Lungi Ngidi":9},
}

class DashboardDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.final = pd.read_csv(DATA / "final_top10.csv")
        cls.comparison = pd.read_csv(DATA / "model_comparison.csv")
        cls.pressure = pd.read_csv(DATA / "pressure_vs_nonpressure.csv")
        cls.batters = pd.read_csv(DATA / "player_batting.csv")
        cls.bowlers = pd.read_csv(DATA / "player_bowling.csv")
        cls.audit = json.loads((DATA / "source_audit.json").read_text())

    def test_final_lists_are_fixed_and_ordered(self):
        self.assertEqual(len(self.final),20)
        self.assertEqual(self.final.player_id.nunique(),20)
        self.assertEqual(self.final[self.final.role.eq("Batter")].sort_values("rank").name.tolist(), BAT_FINAL)
        self.assertEqual(self.final[self.final.role.eq("Bowler")].sort_values("rank").name.tolist(), BOWL_FINAL)

    def test_model_a_top_tens_match_submission_pdf(self):
        self.assertEqual(self.batters.sort_values("model_a_rank").head(10).name.tolist(), MODEL_A_BAT)
        self.assertEqual(self.bowlers.sort_values("model_a_rank").head(10).name.tolist(), MODEL_A_BOWL)

    def test_model_c_published_ranks_match_pdf_tables_1_and_2(self):
        published = pd.read_csv(DATA / "model_c_published_ranks.csv")
        for role, expected in PDF_C.items():
            part=published[published.role.eq(role)]
            actual={r['name']:(None if pd.isna(r.published_rank) else int(r.published_rank)) for _,r in part.iterrows()}
            self.assertEqual(actual, expected)
        for _, row in self.comparison.iterrows():
            want=PDF_C[row.role][row['name']]
            self.assertTrue(pd.isna(row.model_c_rank) if want is None else int(row.model_c_rank)==want)
            model_a_want=PDF_A[row.role][row['name']]
            self.assertTrue(row.model_a_rank>10 if model_a_want is None else int(row.model_a_rank)==model_a_want)
            self.assertEqual(int(row.model_b_rank),int(self.final.loc[(self.final.role==row.role)&(self.final.name==row['name']),'rank'].iloc[0]))

    def test_table_3_metrics_match_pdf(self):
        all_players = pd.concat([self.batters.assign(role="Batter"), self.bowlers.assign(role="Bowler")])
        indexed = all_players.set_index("name")
        for name, expected in TABLE3.items():
            row = indexed.loc[name]
            actual_rate = row.pressure_strike_rate if row.role == "Batter" else row.pressure_economy
            baseline_rate = row.baseline_strike_rate if row.role == "Batter" else row.baseline_economy
            actual = (int(row.pressure_balls),int(row.pressure_matches),actual_rate,baseline_rate,row.model_a_rating,
                      row.rating_ci_low,row.rating_ci_high,row.bootstrap_top10_pct)
            for j,(got,want) in enumerate(zip(actual,expected)):
                delta=.051 if j in (2,3) else .011
                self.assertAlmostEqual(float(got),float(want),delta=delta,msg=f"{name}: {got} != {want}")

    def test_pressure_shares_and_section_2_values_match_pdf(self):
        expected = {
            ("Batting","IPL","Non-pressure"):(.9386,8.89,.206,.354,5.38),
            ("Batting","IPL","Pressure"):(.0614,8.05,.170,.358,4.22),
            ("Batting","T20I","Non-pressure"):(.9275,8.17,.179,.382,5.94),
            ("Batting","T20I","Pressure"):(.0725,6.97,.128,.390,5.34),
            ("Bowling","IPL","Non-pressure"):(.9393,9.00,.200,.360,4.89),
            ("Bowling","IPL","Pressure"):(.0607,11.80,.270,.255,6.80),
            ("Bowling","T20I","Non-pressure"):(.9568,8.24,.172,.387,5.50),
            ("Bowling","T20I","Pressure"):(.0432,11.57,.253,.271,7.49),
        }
        for key, want in expected.items():
            row=self.pressure[(self.pressure.role.eq(key[0]))&(self.pressure.competition.eq(key[1]))&(self.pressure.pressure_group.eq(key[2]))].iloc[0]
            got=(row.share_of_legal_deliveries,row.run_rate_per_over,row.boundary_pct,row.dot_pct,row.wickets_per_100_balls)
            for value,target in zip(got,want): self.assertAlmostEqual(float(value),float(target),delta=.006,msg=f"{key}")

    def test_pdf_source_counts_and_scoped_parquet_are_both_documented(self):
        # PDF front page is the raw-source count; the analysis parquet intentionally scopes to IPL + T20I.
        self.assertEqual(self.audit['raw_rows'],200999)
        self.assertEqual(self.audit['raw_matches_with_ball_data'],867)
        self.assertEqual(len(pd.read_parquet(DATA/'deliveries.parquet')),self.audit['dashboard_deliveries'])
        self.assertEqual(pd.read_parquet(DATA/'deliveries.parquet').match_id.nunique(),self.audit['dashboard_matches'])
        self.assertEqual(self.audit['dashboard_matches'],837)

    def test_batter_death_rae_missingness_is_explicit(self):
        self.assertEqual(len(self.batters),64)
        self.assertTrue(self.batters.death_RAE_per_100_balls.isna().all())

    def test_parquet_and_match_level_season_fields(self):
        d=pd.read_parquet(DATA/'deliveries.parquet')
        self.assertIn('season_year',d.columns)
        self.assertTrue(pd.api.types.is_integer_dtype(d.season_year.dtype))
        self.assertIsInstance(d.competition.dtype,pd.CategoricalDtype)
        pm=pd.read_csv(DATA/'player_match_pressure.csv')
        self.assertIn('season_year',pm.columns)
        self.assertIn('match_date',pm.columns)

if __name__ == '__main__':
    unittest.main()
