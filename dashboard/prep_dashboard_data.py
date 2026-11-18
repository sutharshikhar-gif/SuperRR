#!/usr/bin/env python3
"""Prepare compact, offline dashboard data from the reviewed analysis outputs."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


BAT_FINAL = [
    "Heinrich Klaasen", "Suryakumar Yadav", "Shivam Dube", "Namboori Tilak Varma",
    "Shashank Singh", "Tristan Stubbs", "Moeen Ali", "Marcus Stoinis", "Tim David", "Towhid Hridoy",
]
BOWL_FINAL = [
    "Matheesha Pathirana", "Joshua Little", "Wanindu Hasaranga", "Rashid Khan",
    "Khaleel Ahmed", "Brad Evans", "Vaibhav Arora", "Mitchell Starc", "Dushmantha Chameera", "Lungi Ngidi",
]
BAT_A = [
    "Shashank Singh", "Jimmy Neesham", "Mark Chapman", "Shivam Dube", "Suryakumar Yadav",
    "Andre Russell", "Marcus Stoinis", "George Dockrell", "Heinrich Klaasen", "Moeen Ali",
]
BOWL_A = [
    "Joshua Little", "Khaleel Ahmed", "Vaibhav Arora", "Sunil Narine", "Brad Evans",
    "Hardik Pandya", "Mitchell Starc", "Rashid Khan", "Lungi Ngidi", "Shaheen Afridi",
]


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def source_ball_file(source_dir: Path) -> Path:
    for candidate in [source_dir / "ball_by_ball.csv", source_dir / "6af855c0e8386_ball_by_ball.csv"]:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Expected ball_by_ball.csv or 6af855c0e8386_ball_by_ball.csv in --source-dir")


def display_names(mapping: pd.DataFrame) -> dict[int, str]:
    m = mapping.copy()
    m["player_id"] = pd.to_numeric(m.player_id, errors="coerce")
    return m.groupby("player_id").player_name.agg(lambda s: s.value_counts().index[0]).to_dict()


def team_names(mapping: pd.DataFrame) -> dict[int, str]:
    m = mapping.copy()
    m["player_id"] = pd.to_numeric(m.player_id, errors="coerce")
    return m.groupby("player_id").team_name.agg(lambda s: ", ".join(sorted(set(s.astype(str))))).to_dict()


def team_labels(mapping: pd.DataFrame) -> tuple[dict[int, str], dict[int, str]]:
    m = mapping.copy()
    m["player_id"] = pd.to_numeric(m.player_id, errors="coerce")
    is_ipl = m.comp_name.astype(str).str.contains("IPL", case=False, na=False)
    def collect(frame: pd.DataFrame) -> dict[int, str]:
        if frame.empty:
            return {}
        return frame.groupby("player_id").team_name.agg(lambda s: ", ".join(sorted(set(s.astype(str))))).to_dict()
    return collect(m[is_ipl]), collect(m[~is_ipl])


def validate_headline_lists(analysis_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bat_a = read_csv(analysis_dir / "batting_rankings.csv")
    bowl_a = read_csv(analysis_dir / "bowling_rankings.csv")
    bat_b = read_csv(analysis_dir / "batting_rankings_score2.csv")
    bowl_b = read_csv(analysis_dir / "bowling_rankings_score2.csv")
    for label, frame, expected in [
        ("Model A batters", bat_a, BAT_A), ("Model A bowlers", bowl_a, BOWL_A),
        ("Model B batters", bat_b, BAT_FINAL), ("Model B bowlers", bowl_b, BOWL_FINAL),
    ]:
        actual = frame.sort_values("rank").head(10).name.tolist()
        if actual != expected:
            raise ValueError(f"{label} list does not match the user-specified order. Expected {expected}; found {actual}. Stopping without changing the lists.")
    return bat_a, bowl_a, bat_b, bowl_b


def model_c_baseline(source_dir: Path, display: dict[int, str], team: dict[int, str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recreate the simple Colab baseline as a comparison model, before app load."""
    d = read_csv(source_ball_file(source_dir))
    matches = read_csv(source_dir / "matches.csv")
    comps = read_csv(source_dir / "competitions.csv")
    meta = matches.merge(comps[["comp_id", "comp_name", "match_format", "season"]], on="comp_id", how="left", validate="many_to_one")
    meta["season_year"] = pd.to_numeric(meta.season.astype(str).str[:4], errors="coerce")
    meta["competition"] = np.where(meta.comp_name.astype(str).str.contains("IPL", case=False), "IPL", np.where(meta.match_format.eq("T20I"), "T20I", "OTHER"))
    meta = meta[(meta.season_year >= 2022) & meta.competition.isin(["IPL", "T20I"])]
    d = d.merge(meta[["match_id", "competition"]], on="match_id", how="inner", validate="many_to_one")
    d = d[d.innings.isin([1, 2])].copy()
    for c in ["is_four", "is_six", "is_wicket"]:
        d[c] = d[c].astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"])
    for c in ["runs", "extras1_runs", "extras_2_runs", "innings_ball_num", "overid", "innings", "striker_id", "bowler_id", "dismissed_player_id"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["extras_type"] = d.extras_type.fillna("").astype(str).str.strip().str.lower()
    d[["runs", "extras1_runs", "extras_2_runs"]] = d[["runs", "extras1_runs", "extras_2_runs"]].fillna(0)
    d["total_runs"] = d.runs + d.extras1_runs + d.extras_2_runs
    d["is_batter_ball"] = ~d.extras_type.isin(["wide", "wides"])
    d["legal_ball"] = ~d.extras_type.isin(["wide", "wides", "overstep", "noballs", "no_ball", "no ball", "penalty"])
    d = d.sort_values(["match_id", "innings", "innings_ball_num"], kind="mergesort").reset_index(drop=True)
    g = d.groupby(["match_id", "innings"], sort=False)
    d["runs_before"] = g.total_runs.cumsum() - d.total_runs
    d["wkts_before"] = g.is_wicket.cumsum() - d.is_wicket.astype(int)
    d["legal_before"] = g.legal_ball.cumsum() - d.legal_ball.astype(int)
    first = d[d.innings.eq(1)].groupby("match_id").total_runs.sum()
    d["target"] = d.match_id.map(first) + 1
    d["rrr"] = np.where(d.innings.eq(2), (d.target - d.runs_before) * 6 / (120 - d.legal_before).clip(lower=1), np.nan)
    s1 = d.innings.eq(2) & d.rrr.between(10, 18, inclusive="both") & d.overid.ge(7)
    s2 = (d.wkts_before.ge(3) & d.overid.lt(12)) | (d.wkts_before.ge(5) & d.overid.lt(18))
    d["pressure"] = s1 | s2
    d["death"] = d.overid.ge(17)

    # Preserve the original baseline's global expectation by over and wickets lost.
    bats = d[d.is_batter_ball].groupby(["overid", "wkts_before"]).agg(exp_runs=("runs", "mean"), exp_wicket=("is_wicket", "mean"))
    d = d.join(bats, on=["overid", "wkts_before"])
    d["batter_rae"] = np.where(d.is_batter_ball,
                               (d.runs - d.exp_runs.fillna(0)) - 15 * (d.is_wicket.astype(int) - d.exp_wicket.fillna(0)), 0.0)

    extras_not_bowler = d.extras1_runs.where(d.extras_type.isin(["byes", "legbyes"]), 0) + d.extras_2_runs.where(d.extras_type.isin(["byes", "legbyes"]), 0)
    d["bowler_runs"] = (d.total_runs - extras_not_bowler).clip(lower=0)
    credited = {"bowled", "caught", "lbw", "stump", "hit wicket"}
    d["bowler_wicket"] = d.is_wicket & d.dismissal_type.fillna("").astype(str).str.strip().str.lower().isin(credited)
    legal_states = d[d.legal_ball].groupby(["overid", "wkts_before"]).agg(exp_runs=("bowler_runs", "mean"), exp_wicket=("bowler_wicket", "mean"))
    legal_states = legal_states.rename(columns={"exp_runs": "exp_bowler_runs", "exp_wicket": "exp_bowler_wicket"})
    d = d.join(legal_states, on=["overid", "wkts_before"])
    d["bowler_rae"] = np.where(d.legal_ball, (d.exp_bowler_runs.fillna(0) - d.bowler_runs) + 15 * (d.bowler_wicket.astype(int) - d.exp_bowler_wicket.fillna(0)), 0.0)

    def rank_role(player_col: str, score_col: str, balls_mask: pd.Series) -> pd.DataFrame:
        q = d[d.pressure & d[player_col].notna()].copy()
        q["player_id"] = q[player_col].astype(int)
        q["legal_n"] = balls_mask.loc[q.index].astype(int)
        q["death_rae"] = q[score_col].where(q.death, 0.0)
        q["death_legal_n"] = q.legal_n.where(q.death, 0)
        z = q.groupby("player_id", as_index=False).agg(
            pressure_balls=("legal_n", "sum"), pressure_matches=("match_id", "nunique"),
            rae=(score_col, "sum"), death_rae=("death_rae", "sum"), death_balls=("death_legal_n", "sum"))
        z = z[z.pressure_balls >= 100].copy()
        z["overall_RAE"] = 100 * z.rae / z.pressure_balls.clip(lower=1)
        z["death_RAE"] = 100 * z.death_rae / z.death_balls.replace(0, np.nan)
        z["blended_RAE"] = .70 * z.overall_RAE + .30 * z.death_RAE.fillna(z.overall_RAE)
        z["Final_Score"] = z.blended_RAE * z.pressure_balls / (z.pressure_balls + 150)
        z["name"] = z.player_id.map(display)
        z["teams"] = z.player_id.map(team).fillna("")
        z = z.sort_values(["Final_Score", "pressure_balls"], ascending=[False, False]).reset_index(drop=True)
        z.insert(0, "rank", np.arange(1, len(z) + 1))
        return z

    bat_c = rank_role("striker_id", "batter_rae", d.is_batter_ball)
    bowl_c = rank_role("bowler_id", "bowler_rae", d.legal_ball)
    return bat_c, bowl_c


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True, help="Folder with the supplied ball-by-ball and reference CSVs")
    parser.add_argument("--analysis-dir", type=Path, default=Path(__file__).resolve().parent.parent, help="Folder with the completed analysis outputs")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "data")
    parser.add_argument("--pdf", type=Path, default=Path(__file__).resolve().parent / "data" / "methodology_report.pdf", help="Methodology PDF v3 used for published comparison ranks")
    parser.add_argument("--allow-model-c-mismatch", action="store_true", help="Continue with published v3 ranks when the local Model C rebuild disagrees")
    args = parser.parse_args()
    source, analysis, out = args.source_dir.resolve(), args.analysis_dir.resolve(), args.output_dir.resolve()
    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"Methodology PDF not found: {pdf_path}")
    out.mkdir(parents=True, exist_ok=True)
    bat_a, bowl_a, bat_b, bowl_b = validate_headline_lists(analysis)
    mapping = read_csv(source / "competition_team_player_mapping.csv")
    name_map, team_map = display_names(mapping), team_names(mapping)
    bat_c, bowl_c = model_c_baseline(source, name_map, team_map)

    # Published Model C ranks in v3 are retained as a parity check for final-list players.
    published_c = {
        "batter": {"Heinrich Klaasen":49,"Suryakumar Yadav":45,"Shivam Dube":60,"Namboori Tilak Varma":13,"Shashank Singh":4,"Tristan Stubbs":6,"Moeen Ali":98,"Marcus Stoinis":69,"Tim David":5,"Towhid Hridoy":16},
        "bowler": {"Matheesha Pathirana":47,"Joshua Little":55,"Wanindu Hasaranga":12,"Rashid Khan":7,"Khaleel Ahmed":58,"Brad Evans":None,"Vaibhav Arora":133,"Mitchell Starc":51,"Dushmantha Chameera":137,"Lungi Ngidi":35},
    }
    mismatches = []
    for role, ranked, expected in [("batter", bat_c, published_c["batter"]), ("bowler", bowl_c, published_c["bowler"] )]:
        ranks = ranked.set_index("name")["rank"].to_dict()
        for player, rank in expected.items():
            got = ranks.get(player)
            if rank is not None and got != rank:
                mismatches.append(f"{role}: {player} rebuilt={got}, published_v3={rank}")
            if rank is None and got is not None:
                mismatches.append(f"{role}: {player} rebuilt={got}, published_v3=below minimum")
    if mismatches and not args.allow_model_c_mismatch:
        raise ValueError("Model C disagrees with methodology PDF v3. Rerun with --allow-model-c-mismatch to use published ranks:\n" + "\n".join(mismatches))
    if mismatches:
        print("Model C mismatch accepted by flag; dashboard comparisons will use published v3 ranks:\n" + "\n".join(mismatches))
    published_rows = []
    for role, ranks, pool in [("Batter", published_c["batter"], 160), ("Bowler", published_c["bowler"], 155)]:
        for name, rank in ranks.items():
            published_rows.append({"role": role, "name": name, "published_rank": rank, "pool_size": pool,
                                   "status": "below minimum" if rank is None else "ranked", "source": "methodology_report.pdf · v3"})
    pd.DataFrame(published_rows).to_csv(out / "model_c_published_ranks.csv", index=False)

    # Compact, selected delivery data; state is pre-ball and inherited from the reviewed analysis.
    b = pd.read_csv(analysis / "delivery_pressure_features.csv.gz", low_memory=False)
    matches = read_csv(source / "matches.csv")
    match_meta = matches[["match_id", "match_date", "home_team", "away_team", "home_team_id", "away_team_id"]].copy()
    b = b.merge(match_meta, on="match_id", how="left", validate="many_to_one")
    b["striker_id"] = pd.to_numeric(b.striker_id, errors="coerce")
    b["bowler_id"] = pd.to_numeric(b.bowler_id, errors="coerce")
    b["striker_name"] = b.striker_id.map(name_map)
    b["bowler_name"] = b.bowler_id.map(name_map)
    b["batting_team"] = np.where(b.batting_team_id.eq(b.home_team_id), b.home_team, b.away_team)
    b["bowling_team"] = np.where(b.bowling_team_id.eq(b.home_team_id), b.home_team, b.away_team)
    delivery_cols = [
        "match_id","innings","overid","over_ball_num","innings_ball_num","striker_id","striker_name","bowler_id","bowler_name",
        "dismissed_player_id","batting_order","batting_team_id","bowling_team_id","batting_team","bowling_team","runs","total_runs",
        "extras_type","extras1_runs","extras_2_runs","is_four","is_six","is_wicket","dismissal_type","legal_ball","bowler_runs_conceded",
        "bowler_wicket","batter_dismissed","competition","season","match_date","team_score_before","wickets_lost_before","wickets_in_hand",
        "balls_bowled_legal","balls_remaining","current_run_rate","required_run_rate","rrr_minus_crr","par_gap","recent12_team_runs",
        "recent12_team_rpo","batting_pressure","bowling_pressure","batting_pressure_continuous","bowling_pressure_continuous","general_pressure_score",
        "phase","pace_or_spin","target","runs_required","expected_batter_runs","expected_batter_dismissal","expected_bowler_runs",
        "expected_bowler_wicket","batter_rae","batter_wicket_above_expected","bowler_runs_saved","bowler_wicket_above_expected","win_prob_proxy",
    ]
    d = b[delivery_cols].copy()
    d.rename(columns={"team_score_before":"score_before","wickets_lost_before":"wickets_before","balls_bowled_legal":"legal_balls_before",
                      "current_run_rate":"crr","required_run_rate":"rrr","rrr_minus_crr":"rrr_crr_gap",
                      "recent12_team_runs":"recent12_runs","batting_pressure":"bat_pressure_flag","bowling_pressure":"bowl_pressure_flag",
                      "batting_pressure_continuous":"bat_pressure_score","bowling_pressure_continuous":"bowl_pressure_score"}, inplace=True)
    d["season_year"] = pd.to_numeric(d.season.astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce").astype("Int16")
    for col in ["striker_name", "bowler_name", "batting_team", "bowling_team", "extras_type", "dismissal_type", "competition", "season", "phase", "pace_or_spin"]:
        if col in d:
            d[col] = d[col].astype("category")
    try:
        d.to_parquet(out / "deliveries.parquet", index=False, compression="zstd")
        delivery_file = "deliveries.parquet"
    except ImportError:
        d.to_csv(out / "deliveries.csv.gz", index=False, compression="gzip")
        delivery_file = "deliveries.csv.gz"

    def merge_player(role: str, main: pd.DataFrame, final: pd.DataFrame, c: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
        idcol = "player_id"
        x = final.copy().rename(columns={"rank":"model_b_rank", "Final_Score":"model_b_score", "blended_RAE":"model_b_blended_rae"})
        a = main.copy().rename(columns={"rank":"model_a_rank", "rating":"model_a_rating"})
        keep = [idcol,"model_a_rank","model_a_rating","rating_ci_low","rating_ci_high","bootstrap_top10_pct","rank_uncertain","clutch_delta",
                "pressure_rae_per_ball","baseline_rae_per_ball","pressure_dot_pct","baseline_dot_pct","pressure_boundary_pct","baseline_boundary_pct",
                "pressure_run_rate","baseline_run_rate","beat_match_share"]
        if role == "batter": keep += ["pressure_strike_rate","baseline_strike_rate","overall_strike_rate","pressure_balls_per_dismissal","baseline_balls_per_dismissal","dismissal_rate_vs_expected","pressure_gap_closed_per_ball"]
        else: keep += ["pressure_economy","baseline_economy","overall_economy","pressure_wickets_per_ball","baseline_wickets","baseline_balls","wickets_above_expected"]
        a = a[[col for col in keep if col in a]].copy()
        x = x.merge(a, on=idcol, how="left", validate="one_to_one")
        cc = c[["player_id","rank","pressure_balls","pressure_matches","Final_Score"]].rename(columns={"rank":"model_c_rank","pressure_balls":"model_c_pressure_balls","pressure_matches":"model_c_matches","Final_Score":"model_c_score"})
        x = x.merge(cc, on=idcol, how="left", validate="one_to_one")
        x["name"] = x.player_id.map(name_map)
        x["teams"] = x.player_id.map(team_map).fillna("")
        published_ranks = published_c["batter" if role == "batter" else "bowler"]
        x["model_c_rank"] = x.name.map(published_ranks)
        x["model_c_status"] = np.where(x.model_c_rank.notna(), "ranked", "not published in v3 table")
        if role == "bowler":
            x.loc[x.name.eq("Brad Evans"), "model_c_status"] = "below minimum"
        x["model_c_pool_size"] = 160 if role == "batter" else 155
        franchise_map, national_map = team_labels(mapping)
        x["ipl_franchises"] = x.player_id.map(franchise_map).fillna("")
        x["national_sides"] = x.player_id.map(national_map).fillna("")
        if role == "bowler":
            x["baseline_wickets_per_ball"] = pd.to_numeric(x.get("baseline_wickets"), errors="coerce") / pd.to_numeric(x.get("baseline_balls"), errors="coerce").replace(0, np.nan)
        split = comp.pivot(index="player_id", columns="competition", values="rating_comp")
        for competition in ["IPL", "T20I"]:
            x[f"{competition.lower()}_rating"] = x.player_id.map(split[competition]) if competition in split else np.nan
        splits = comp.groupby("player_id").apply(lambda q: json.dumps({str(r.competition): {"pressure_balls": int(r.pressure_balls), "rating": float(r.rating_comp)} for _, r in q.iterrows()}, separators=(",", ":")), include_groups=False)
        x["competition_splits_json"] = x.player_id.map(splits)
        return x.sort_values("model_b_rank").reset_index(drop=True)

    bat_comp = read_csv(analysis / "batters_by_competition.csv")
    bowl_comp = read_csv(analysis / "bowlers_by_competition.csv")
    player_bat = merge_player("batter", bat_a, bat_b, bat_c, bat_comp)
    player_bowl = merge_player("bowler", bowl_a, bowl_b, bowl_c, bowl_comp)
    player_bat.to_csv(out / "player_batting.csv", index=False)
    player_bowl.to_csv(out / "player_bowling.csv", index=False)

    pm_bat = read_csv(analysis / "batter_match_performance.csv")
    pm_bowl = read_csv(analysis / "bowler_match_performance.csv")
    pm_bat = pm_bat.rename(columns={"average_RAE_per_ball":"pressure_impact_per_ball"})
    pm_bat["role"] = "Batter"
    pm_bowl["pressure_impact_per_ball"] = pm_bowl.runs_saved_per_ball
    pm_bowl["role"] = "Bowler"
    pm = pd.concat([pm_bat, pm_bowl], ignore_index=True, sort=False)
    competitions = read_csv(source / "competitions.csv")
    match_meta = matches[["match_id", "match_date", "comp_id"]].merge(
        competitions[["comp_id", "season"]], on="comp_id", how="left", validate="many_to_one")
    match_meta["season_year"] = pd.to_numeric(match_meta.season.astype(str).str.extract(r"(\d{4})", expand=False), errors="coerce").astype("Int16")
    pm = pm.merge(match_meta[["match_id", "match_date", "season", "season_year"]], on="match_id", how="left", validate="many_to_one")
    pm["name"] = pm.player_id.map(name_map)
    pm["teams"] = pm.player_id.map(team_map).fillna("")
    pm.to_csv(out / "player_match_pressure.csv", index=False)

    final = []
    for role, names, rankdf in [("Batter", BAT_FINAL, bat_b), ("Bowler", BOWL_FINAL, bowl_b)]:
        ids = rankdf.set_index("name").player_id.to_dict()
        for rank, name in enumerate(names, 1):
            if name not in ids:
                raise ValueError(f"Final Model B player {name} is absent from the score file; stopping.")
            final.append({"rank": rank, "role": role, "player_id": int(ids[name]), "name": name})
    final_df = pd.DataFrame(final)
    fixed_final_path = out / "final_top10.csv"
    if fixed_final_path.exists():
        existing_final = read_csv(fixed_final_path)
        if existing_final.to_csv(index=False) != final_df.to_csv(index=False):
            raise ValueError("Existing final_top10.csv differs from the fixed specification; refusing to overwrite it.")
    else:
        final_df.to_csv(fixed_final_path, index=False)
    for role, stem in [("Batter", "top10_batters.csv"), ("Bowler", "top10_bowlers.csv")]:
        expected_top = final_df[final_df.role.eq(role)][["rank", "role", "player_id", "name"]].reset_index(drop=True)
        target = out / stem
        if target.exists():
            if not read_csv(target).reset_index(drop=True).equals(expected_top):
                raise ValueError(f"Existing {stem} differs from the fixed final list; refusing to overwrite it.")
        else:
            expected_top.to_csv(target, index=False)

    comp_rank_a = {"Batter": bat_a.set_index("name")["rank"].to_dict(), "Bowler": bowl_a.set_index("name")["rank"].to_dict()}
    comp_rank_c = {"Batter": published_c["batter"], "Bowler": published_c["bowler"]}
    rows = []
    for _, r in final_df.iterrows():
        rows.append({"role": r.role, "player_id": r.player_id, "name": r["name"], "model_b_rank": r["rank"],
                     "model_a_rank": comp_rank_a[r.role].get(r["name"]), "model_c_rank": comp_rank_c[r.role].get(r["name"]),
                     "model_c_status": "below minimum" if comp_rank_c[r.role].get(r["name"]) is None else "ranked",
                     "model_c_pool_size": 160 if r.role == "Batter" else 155,
                     "model_c_eligible": comp_rank_c[r.role].get(r["name"]) is not None})
    pd.DataFrame(rows).to_csv(out / "model_comparison.csv", index=False)
    bat_c.to_csv(out / "model_c_batting.csv", index=False)
    bowl_c.to_csv(out / "model_c_bowling.csv", index=False)

    # Compact evidence tables used by dashboard pages.
    for fn in ["win_probability_crosscheck.csv", "split_half_reliability.csv", "season_top10_stability.csv", "sensitivity_analysis.csv"]:
        shutil.copy2(analysis / fn, out / fn)

    # Section 2 uses batter runs (off the bat) for batting run rate and dots.
    features = read_csv(analysis / "delivery_pressure_features.csv.gz")
    comparison_rows = []
    for role, flag in [("Batting", "batting_pressure"), ("Bowling", "bowling_pressure")]:
        q = features.copy()
        if role == "Batting":
            q["metric_runs"] = q.runs
            q["metric_dot"] = q.legal_ball & q.runs.eq(0)
        else:
            q["metric_runs"] = q.bowler_runs_conceded
            q["metric_dot"] = q.legal_ball & q.bowler_runs_conceded.eq(0)
        q["metric_boundary"] = q.is_four.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"]) | q.is_six.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y"])
        q["metric_wicket"] = q.bowler_wicket if role == "Bowling" else q.is_wicket
        for (competition, pressured), group in q.groupby(["competition", flag], dropna=False):
            balls = int(group.legal_ball.sum())
            total = int(q.loc[q.competition.eq(competition), "legal_ball"].sum())
            comparison_rows.append({"role": role, "competition": competition,
                "pressure_group": "Pressure" if bool(pressured) else "Non-pressure", "deliveries": balls,
                "share_of_legal_deliveries": balls / max(total, 1),
                "run_rate_per_over": group.metric_runs.sum() * 6 / max(balls, 1),
                "boundary_pct": group.metric_boundary.sum() / max(balls, 1),
                "dot_pct": group.metric_dot.sum() / max(balls, 1),
                "wickets_per_100_balls": group.metric_wicket.sum() * 100 / max(balls, 1)})
    pd.DataFrame(comparison_rows).to_csv(out / "pressure_vs_nonpressure.csv", index=False)

    # Player-level odd/even rank evidence for the split-half reliability plot.
    half_tables = []
    for role, flag, player_col, impact_col, ranked in [
        ("Batter", "batting_pressure", "striker_id", "batter_rae", bat_a),
        ("Bowler", "bowling_pressure", "bowler_id", "bowler_runs_saved", bowl_a)]:
        q = features[features[flag] & features[player_col].notna()].copy()
        q["player_id"] = q[player_col].astype(int)
        q["half"] = np.where(q.match_id.astype(int) % 2 == 0, "Even", "Odd")
        q["legal_balls"] = q.legal_ball.astype(int)
        group = q.groupby(["player_id", "half"], as_index=False).agg(impact=(impact_col, "sum"), legal_balls=("legal_balls", "sum"))
        group["impact_per_ball"] = group.impact / group.legal_balls.clip(lower=1)
        wide = group.pivot(index="player_id", columns="half", values="impact_per_ball").dropna().reset_index()
        wide = wide[wide.player_id.isin(set(ranked.player_id))].copy()
        wide["odd_rank"] = wide.Odd.rank(ascending=False, method="min")
        wide["even_rank"] = wide.Even.rank(ascending=False, method="min")
        wide["role"] = role
        wide["name"] = wide.player_id.map(name_map)
        half_tables.append(wide.rename(columns={"Odd":"odd_impact_per_ball", "Even":"even_impact_per_ball"}))
    pd.concat(half_tables, ignore_index=True).to_csv(out / "split_half_players.csv", index=False)

    raw_keys = read_csv(source_ball_file(source))[["match_id"]]
    scoped_matches = int(d.match_id.nunique())
    audit = {"raw_rows": int(len(raw_keys)), "raw_matches_with_ball_data": int(raw_keys.match_id.nunique()),
             "dashboard_deliveries": int(len(d)), "dashboard_legal_balls": int(d.legal_ball.fillna(False).astype(bool).sum()),
             "dashboard_matches": scoped_matches,
             "note": "PDF reports 867 source matches; dashboard parquet is the IPL/T20I analysis scope and excludes 30 non-IPL T20 Asia Cup Rising Stars matches."}
    (out / "source_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if pdf_path != (out / "methodology_report.pdf").resolve():
        shutil.copy2(pdf_path, out / "methodology_report.pdf")

    # Final-list mismatch guard is explicit and fails closed.
    actual_bat = final_df[final_df.role.eq("Batter")].sort_values("rank").name.tolist()
    actual_bowl = final_df[final_df.role.eq("Bowler")].sort_values("rank").name.tolist()
    if actual_bat != BAT_FINAL or actual_bowl != BOWL_FINAL:
        raise ValueError("Final Model B lists do not match the specified headline lists; stopping.")
    sizes = [(f.name, f.stat().st_size) for f in out.iterdir() if f.is_file()]
    total = sum(size for _, size in sizes)
    print(f"Prepared {delivery_file}: {len(d):,} deliveries, {len(player_bat)} batters, {len(player_bowl)} bowlers.")
    print(f"Dashboard data total: {total / 1024 / 1024:.2f} MiB; largest file {max(sizes, key=lambda x:x[1])[0]} ({max(size for _,size in sizes)/1024/1024:.2f} MiB).")
    print("Model B headline lists verified exactly against the user-specified order.")
    print("Model C comparison ranks use the published v3 table; the local baseline is retained separately for diagnosis.")


if __name__ == "__main__":
    main()
