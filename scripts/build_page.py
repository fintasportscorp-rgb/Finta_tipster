#!/usr/bin/env python3
"""
build_page.py — Builds index.html: condensed + extended view for all upcoming Big 5 matches.

Condensed view: table of all upcoming matches with key indicators per team.
Extended view: full metrics breakdown for a selected match (clickable from table).

Reads pre-generated CSVs from the scrapers, computes composite form scores (0-100),
and outputs a self-contained index.html with embedded JSON.

Usage:
    python build_page.py
"""

import json
import os
import re
import glob
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
# This script lives in <project-root>/scripts/. Data dirs (understat_data/, data/,
# input/) and the web/ app live at the project root, so PROJECT_ROOT is one level up.
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_DIR = PROJECT_ROOT
FALLBACK_DATA = SCRIPT_DIR.parent / "football_scraper" / "data"

UNDERSTAT_PATH = SCRIPT_DIR / "understat_data" / "big5_understat_2026.csv"
UNDERSTAT_FALLBACK = FALLBACK_DATA / "big5_understat_2026.csv"

# Friendly matches (pre-season) — used to supplement form when league matches < 5
FRIENDLIES_DIR = SCRIPT_DIR / "understat_data"

# Last season fallback — used when current season has insufficient data
UNDERSTAT_PREV_SEASON = FALLBACK_DATA / "big5_understat_2025.csv"

ABSENCES_DIR = SCRIPT_DIR / "data"
ABSENCES_FALLBACK_DIR = FALLBACK_DATA

FORMATIONS_PATH = SCRIPT_DIR.parent / "data" / "big5_formations_2025.csv"
FORMATIONS_FALLBACK = FALLBACK_DATA / "big5_formations_2025.csv"

GOAL_TIMING_DIR = SCRIPT_DIR / "understat_data"

ODDS_DIR = SCRIPT_DIR / "input"
TIPS_PATH = SCRIPT_DIR / "input" / "betting_tips.csv"

OUTPUT_PATH = SCRIPT_DIR / "index.html"
# The React app (web/) consumes this at runtime from its public/ dir.
DATA_JSON_PATH = SCRIPT_DIR / "web" / "public" / "data.json"

# ── Config ───────────────────────────────────────────────────────────────────
ROLLING_WINDOW = 6
# If a team has > this many league matches, skip friendly/last-season fallback
LEAGUE_MATCH_THRESHOLD = 5
# Weight applied to friendly matches in form computation (lower = less trust)
FRIENDLY_WEIGHT = 0.3
# Weight applied to last-season matches in form computation
PREV_SEASON_WEIGHT = 0.4
WEIGHTS = {
    "results": 0.25,
    "xg": 0.20,
    "availability": 0.20,
    "odds": 0.15,
    "tips": 0.10,
    "timing": 0.10,
}
DAYS_AHEAD = 14  # how far ahead to look for upcoming matches

# ── Team name mapping (TM → Understat) ───────────────────────────────────────
TM_TO_UNDERSTAT = {
    "AFC Bournemouth": "Bournemouth", "Arsenal FC": "Arsenal",
    "Brentford FC": "Brentford", "Brighton & Hove Albion": "Brighton",
    "Burnley FC": "Burnley", "Chelsea FC": "Chelsea",
    "Everton FC": "Everton", "Fulham FC": "Fulham",
    "Leeds United": "Leeds", "Liverpool FC": "Liverpool",
    "Sunderland AFC": "Sunderland", "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham", "Ipswich Town": "Ipswich",
    "Leicester City": "Leicester", "Southampton FC": "Southampton",
    "Athletic Bilbao": "Athletic Club", "Atlético de Madrid": "Atletico Madrid",
    "CA Osasuna": "Osasuna", "Celta de Vigo": "Celta Vigo",
    "Deportivo Alavés": "Alaves", "Elche CF": "Elche",
    "FC Barcelona": "Barcelona", "Getafe CF": "Getafe",
    "Girona FC": "Girona", "Levante UD": "Levante",
    "RCD Espanyol Barcelona": "Espanyol", "RCD Mallorca": "Mallorca",
    "Real Betis Balompié": "Real Betis", "Sevilla FC": "Sevilla",
    "Valencia CF": "Valencia", "Villarreal CF": "Villarreal",
    "UD Las Palmas": "Las Palmas", "CD Leganés": "Leganes",
    "Real Valladolid CF": "Valladolid", "Rayo Vallecano": "Rayo Vallecano",
    "1.FC Heidenheim 1846": "FC Heidenheim", "1.FC Köln": "FC Cologne",
    "1.FC Union Berlin": "Union Berlin", "1.FSV Mainz 05": "Mainz 05",
    "Bayer 04 Leverkusen": "Bayer Leverkusen",
    "Borussia Mönchengladbach": "Borussia M.Gladbach",
    "FC Augsburg": "Augsburg", "FC St. Pauli": "St. Pauli",
    "RB Leipzig": "RasenBallsport Leipzig", "SC Freiburg": "Freiburg",
    "SV Werder Bremen": "Werder Bremen", "TSG 1899 Hoffenheim": "Hoffenheim",
    "VfL Wolfsburg": "Wolfsburg", "Holstein Kiel": "Holstein Kiel",
    "ACF Fiorentina": "Fiorentina", "AS Roma": "Roma",
    "Atalanta BC": "Atalanta", "Bologna FC 1909": "Bologna",
    "Cagliari Calcio": "Cagliari", "Como 1907": "Como",
    "Genoa CFC": "Genoa", "Hellas Verona": "Verona",
    "Inter Milan": "Inter", "Juventus FC": "Juventus",
    "Pisa Sporting Club": "Pisa", "SS Lazio": "Lazio",
    "SSC Napoli": "Napoli", "Torino FC": "Torino",
    "US Cremonese": "Cremonese", "US Lecce": "Lecce",
    "US Sassuolo": "Sassuolo", "Udinese Calcio": "Udinese",
    "Parma Calcio 1913": "Parma Calcio 1913", "AC Monza": "Monza",
    "AJ Auxerre": "Auxerre", "AS Monaco": "Monaco",
    "Angers SCO": "Angers", "FC Lorient": "Lorient",
    "FC Metz": "Metz", "FC Nantes": "Nantes",
    "FC Toulouse": "Toulouse", "LOSC Lille": "Lille",
    "Le Havre AC": "Le Havre", "OGC Nice": "Nice",
    "Olympique Lyon": "Lyon", "Olympique Marseille": "Marseille",
    "Paris Saint-Germain": "Paris Saint Germain", "RC Lens": "Lens",
    "RC Strasbourg Alsace": "Strasbourg", "Stade Brestois 29": "Brest",
    "Stade Rennais FC": "Rennes", "Stade Reims": "Reims",
    "Montpellier HSC": "Montpellier", "Paris FC": "Paris FC",
}

UNDERSTAT_TO_TM = {v: k for k, v in TM_TO_UNDERSTAT.items()}

# Sofascore → Understat team name mapping (for odds-sourced matches)
SOFASCORE_TO_UNDERSTAT = {
    "Tottenham Hotspur": "Tottenham", "Aston Villa": "Aston Villa",
    "Manchester City": "Manchester City", "Manchester United": "Manchester United",
    "Newcastle United": "Newcastle United", "Brighton & Hove Albion": "Brighton",
    "Nottingham Forest": "Nottingham Forest", "Crystal Palace": "Crystal Palace",
    "Liverpool FC": "Liverpool", "West Ham United": "West Ham",
    "Ipswich Town": "Ipswich", "Leeds United": "Leeds",
    "Coventry City": "Coventry", "Hull City": "Hull",
    "Sunderland": "Sunderland", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Everton": "Everton",
    "Fulham": "Fulham", "Arsenal": "Arsenal", "Chelsea": "Chelsea",
    "Burnley": "Burnley", "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Leicester City": "Leicester", "Southampton": "Southampton",
    # La Liga
    "Atlético Madrid": "Atletico Madrid", "Athletic Club": "Athletic Club",
    "FC Barcelona": "Barcelona", "Real Madrid": "Real Madrid",
    "Real Betis": "Real Betis", "Real Sociedad": "Real Sociedad",
    "Villarreal": "Villarreal", "Sevilla": "Sevilla",
    "Valencia": "Valencia", "Celta Vigo": "Celta Vigo",
    "Getafe": "Getafe", "Girona": "Girona", "Osasuna": "Osasuna",
    "Mallorca": "Mallorca", "Espanyol": "Espanyol",
    "Rayo Vallecano": "Rayo Vallecano", "Deportivo Alavés": "Alaves",
    "Levante UD": "Levante", "Elche": "Elche",
    "Real Racing Club": "Racing Santander", "Deportivo de A Coruña": "Deportivo La Coruna",
    "Málaga CF": "Malaga",
    # Serie A
    "Inter": "Inter", "Juventus": "Juventus", "SSC Napoli": "Napoli",
    "AC Milan": "AC Milan", "AS Roma": "Roma", "SS Lazio": "Lazio",
    "Atalanta": "Atalanta", "Fiorentina": "Fiorentina",
    "Bologna": "Bologna", "Torino": "Torino", "Udinese": "Udinese",
    "Genoa": "Genoa", "Cagliari": "Cagliari", "Como": "Como",
    "Parma": "Parma", "Monza": "Monza", "Lecce": "Lecce",
    "Verona": "Verona", "Sassuolo": "Sassuolo",
    "Frosinone": "Frosinone", "Venezia": "Venezia",
    "Cremonese": "Cremonese", "Pisa": "Pisa",
    # Ligue 1
    "Paris Saint-Germain": "Paris Saint Germain", "AS Monaco": "Monaco",
    "Olympique de Marseille": "Marseille", "Olympique Lyonnais": "Lyon",
    "LOSC Lille": "Lille", "RC Lens": "Lens", "OGC Nice": "Nice",
    "RC Strasbourg": "Strasbourg", "Stade Rennais": "Rennes",
    "Stade Brestois": "Brest", "FC Nantes": "Nantes",
    "FC Toulouse": "Toulouse", "AJ Auxerre": "Auxerre",
    "Angers": "Angers", "FC Lorient": "Lorient",
    "Le Havre": "Le Havre", "Paris FC": "Paris FC",
    "ESTAC Troyes": "Troyes", "Le Mans": "Le Mans",
}

POSITION_WEIGHTS = {"GK": 2.0, "CB": 1.5, "DM": 1.5}
DEFAULT_POS_WEIGHT = 1.0
AVAILABLE_STATUSES = {"Starting lineup", "Sub in", "Bench"}
ABSENT_STATUSES = {"Injured", "Suspended", "Youth team", "Loaned out", "International duty"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def find_latest_file(directory, pattern):
    files = sorted(glob.glob(str(directory / pattern)))
    return Path(files[-1]) if files else None


def normalize_name(name):
    if not isinstance(name, str):
        return ""
    import unicodedata
    n = unicodedata.normalize("NFKD", name)
    n = n.encode("ascii", "ignore").decode("ascii")
    n = n.lower().strip()
    n = re.sub(r"[^\w\s]", "", n)
    n = re.sub(
        r"\b(fc|cf|ac|sc|afc|club|calcio|united|city|town|athletic|de|la|real|royal|deportivo)\b",
        "",
        n,
    )
    n = n.replace("real racing club", "racing santander")
    n = re.sub(r"\bsantander\b", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


# ── Data loaders ─────────────────────────────────────────────────────────────

def load_understat():
    path = UNDERSTAT_PATH
    if not path.exists():
        path = Path("understat_data") / "big5_understat_2025.csv"
    if not path.exists() and UNDERSTAT_FALLBACK.exists():
        path = UNDERSTAT_FALLBACK
    if not path.exists():
        print("  WARNING: understat data not found")
        return None
    print(f"  Loading understat: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


def load_friendlies():
    """Load the most recent friendlies CSV."""
    f = find_latest_file(FRIENDLIES_DIR, "friendlies_*.csv")
    if not f:
        print("  No friendlies data found")
        return None
    print(f"  Loading friendlies: {f.name}")
    df = pd.read_csv(f, encoding="utf-8-sig")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    # Only keep preseason friendlies (June, July, August of current year)
    now = pd.Timestamp.now()
    df = df[df["datetime"].dt.month.isin([6, 7, 8]) & (df["datetime"].dt.year == now.year)]
    return df


def load_prev_season():
    """Load last season's understat data as fallback."""
    if not UNDERSTAT_PREV_SEASON.exists():
        print("  No previous season data found")
        return None
    print(f"  Loading prev season: {UNDERSTAT_PREV_SEASON.name}")
    df = pd.read_csv(UNDERSTAT_PREV_SEASON, encoding="utf-8-sig")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df


def load_absences():
    f = find_latest_file(ABSENCES_DIR, "tm_absences_*.csv")
    if not f:
        f = find_latest_file(ABSENCES_FALLBACK_DIR, "tm_absences*.csv")
    if not f:
        print("  WARNING: no absences data found")
        return None
    print(f"  Loading absences: {f.name}")
    return pd.read_csv(f, encoding="utf-8-sig")


_FORM_RE = re.compile(r"(\d-\d-\d(?:-\d)?)")


def load_formations():
    path = FORMATIONS_PATH
    if not path.exists() and FORMATIONS_FALLBACK.exists():
        path = FORMATIONS_FALLBACK
    if not path.exists():
        print("  WARNING: formations data not found")
        return None
    print(f"  Loading formations: {path.name}")
    return pd.read_csv(path, encoding="utf-8-sig")


def load_goal_timing():
    f = find_latest_file(GOAL_TIMING_DIR, "goal_timing_*.csv")
    if not f:
        print("  No goal timing data found")
        return None
    print(f"  Loading goal timing: {f.name}")
    return pd.read_csv(f, encoding="utf-8-sig")


def load_odds():
    f = find_latest_file(ODDS_DIR, "big5_odds_*.csv")
    if not f:
        print(f"  WARNING: no odds data in {ODDS_DIR}")
        return None
    print(f"  Loading odds: {f.name}")
    return pd.read_csv(f, encoding="utf-8-sig")


def load_tips():
    if not TIPS_PATH.exists():
        print(f"  WARNING: no tips data at {TIPS_PATH}")
        return None
    print(f"  Loading tips: {TIPS_PATH.name}")
    return pd.read_csv(TIPS_PATH, encoding="utf-8-sig")


# ── Understat: form metrics ──────────────────────────────────────────────────

def find_all_upcoming_matches(xg_df, days_ahead=DAYS_AHEAD):
    now = pd.Timestamp.now()
    horizon = now + timedelta(days=days_ahead)
    unplayed = xg_df["home_goals"].isna() & xg_df["away_goals"].isna()
    future = xg_df["datetime"] > now
    upcoming = xg_df[unplayed & future & (xg_df["datetime"] <= horizon)]
    if upcoming.empty:
        upcoming = xg_df[unplayed & future]
    if upcoming.empty:
        upcoming = xg_df[unplayed]
    if upcoming.empty:
        return []
    return upcoming.sort_values("datetime").to_dict("records")


def find_matches_from_odds(odds_df, days_ahead=DAYS_AHEAD):
    """Extract unique upcoming matches from the odds CSV as fallback match source."""
    if odds_df is None:
        return []
    now = pd.Timestamp.now()
    horizon = now + timedelta(days=days_ahead)

    matches = []
    seen = set()
    for match_name in odds_df["match_name"].dropna().unique():
        parts = re.split(r"\s+vs?\s+", str(match_name), maxsplit=1)
        if len(parts) != 2:
            continue
        home_team = parts[0].strip()
        away_team = parts[1].strip()

        row = odds_df[odds_df["match_name"] == match_name].iloc[0]
        match_dt = pd.to_datetime(row.get("match_date"), errors="coerce")
        if pd.isna(match_dt) or match_dt < now:
            continue
        if match_dt > horizon:
            continue

        key = f"{home_team}|{away_team}"
        if key in seen:
            continue
        seen.add(key)

        league = row.get("league", "Unknown")
        matches.append({
            "home_team": home_team,
            "away_team": away_team,
            "datetime": match_dt,
            "league": league,
            "gameweek": None,
            "match_id": str(row.get("game_id", "")),
            "home_goals": None,
            "away_goals": None,
            "home_xG": None,
            "away_xG": None,
            "forecast_home_win": None,
            "forecast_draw": None,
            "forecast_away_win": None,
            "_source": "odds",
        })
    matches.sort(key=lambda m: m["datetime"])
    return matches


def merge_match_sources(understat_matches, odds_matches):
    """Merge matches from understat and odds, deduplicating by team names."""
    merged = list(understat_matches)
    existing_keys = set()
    for m in merged:
        key = (normalize_name(m["home_team"]), normalize_name(m["away_team"]))
        existing_keys.add(key)

    for m in odds_matches:
        key = (normalize_name(m["home_team"]), normalize_name(m["away_team"]))
        if key not in existing_keys:
            m["_source"] = "odds"
            merged.append(m)
            existing_keys.add(key)

    merged.sort(key=lambda m: m["datetime"] if pd.notna(m["datetime"]) else pd.Timestamp.max)
    return merged


def get_team_matches(xg_df, team, n=ROLLING_WINDOW,
                      friendlies_df=None, prev_season_df=None):
    """Get recent matches for a team.

    Conditional rule: if the team has > LEAGUE_MATCH_THRESHOLD league matches
    in the current season, use only those. Otherwise, supplement with:
    1. Friendly matches (weighted lower, no xG)
    2. Last season's final matches (weighted lower, has xG)
    """
    played = xg_df[xg_df["home_goals"].notna() & xg_df["away_goals"].notna()] if xg_df is not None else pd.DataFrame()
    if xg_df is not None:
        tm = played[(played["home_team"] == team) | (played["away_team"] == team)]
    else:
        tm = pd.DataFrame()

    league_count = len(tm)
    matches = tm.sort_values("datetime", ascending=False).head(n).sort_values("datetime")

    # Conditional rule: only supplement if league matches are below threshold
    if league_count <= LEAGUE_MATCH_THRESHOLD:
        needed = n - league_count

        # 1. Supplement with friendlies
        if friendlies_df is not None and needed > 0:
            friendly_played = friendlies_df[friendlies_df["home_goals"].notna() & friendlies_df["away_goals"].notna()]
            fm = friendly_played[(friendly_played["home_team"] == team) | (friendly_played["away_team"] == team)]
            fm = fm.sort_values("datetime", ascending=False).head(needed).sort_values("datetime")
            if not fm.empty:
                fm = fm.copy()
                fm["match_type"] = "friendly"
                matches = pd.concat([matches, fm], ignore_index=True) if not matches.empty else fm
                needed = n - len(matches)

        # 2. Supplement with last season
        if prev_season_df is not None and needed > 0:
            prev_played = prev_season_df[prev_season_df["home_goals"].notna() & prev_season_df["away_goals"].notna()]
            pm = prev_played[(prev_played["home_team"] == team) | (prev_played["away_team"] == team)]
            pm = pm.sort_values("datetime", ascending=False).head(needed).sort_values("datetime")
            if not pm.empty:
                pm = pm.copy()
                pm["match_type"] = "prev_season"
                matches = pd.concat([matches, pm], ignore_index=True) if not matches.empty else pm

    return matches.sort_values("datetime", ascending=False).head(n).sort_values("datetime")


def compute_results_form(matches, team):
    if matches.empty:
        return 0.5
    points = 0
    for _, m in matches.iterrows():
        if m["home_team"] == team:
            gf, ga = m["home_goals"], m["away_goals"]
        else:
            gf, ga = m["away_goals"], m["home_goals"]
        if gf > ga:
            points += 3
        elif gf == ga:
            points += 1
    return points / (3 * len(matches))


def compute_xg_form(matches, team):
    if matches.empty:
        return 0.5
    diffs = []
    for _, m in matches.iterrows():
        if m["home_team"] == team:
            xf, xa = m["home_xG"], m["away_xG"]
        else:
            xf, xa = m["away_xG"], m["home_xG"]
        if pd.notna(xf) and pd.notna(xa):
            diffs.append(xf - xa)
    if not diffs:
        return 0.5
    return float(sigmoid(np.mean(diffs) * 1.5))


def get_form_string(matches, team):
    results = []
    for _, m in matches.iterrows():
        if m["home_team"] == team:
            gf, ga = m["home_goals"], m["away_goals"]
        else:
            gf, ga = m["away_goals"], m["home_goals"]
        if gf > ga:
            results.append("W")
        elif gf == ga:
            results.append("D")
        else:
            results.append("L")
    return results


def compute_xg_rolling(matches, team):
    """Return list of {xg, xga, diff} for sparkline."""
    data = []
    for _, m in matches.iterrows():
        if m["home_team"] == team:
            xf, xa = m["home_xG"], m["away_xG"]
        else:
            xf, xa = m["away_xG"], m["home_xG"]
        if pd.notna(xf) and pd.notna(xa):
            data.append({"xg": round(float(xf), 2), "xga": round(float(xa), 2), "diff": round(float(xf - xa), 2)})
    return data


def serialize_form_matches(matches, team):
    """Return list of recent matches with details for display in extended view."""
    out = []
    for _, m in matches.iterrows():
        is_home = m["home_team"] == team
        if is_home:
            gf, ga = m["home_goals"], m["away_goals"]
            xf, xa = m.get("home_xG"), m.get("away_xG")
            opponent = m["away_team"]
        else:
            gf, ga = m["away_goals"], m["home_goals"]
            xf, xa = m.get("away_xG"), m.get("home_xG")
            opponent = m["home_team"]
        if gf > ga:
            result = "W"
        elif gf == ga:
            result = "D"
        else:
            result = "L"
        mt = m.get("match_type")
        if pd.isna(mt) or mt is None:
            mt = "league"
        out.append({
            "date": pd.Timestamp(m["datetime"]).strftime("%b %d") if pd.notna(m["datetime"]) else "",
            "opponent": opponent,
            "home_away": "H" if is_home else "A",
            "gf": int(gf) if pd.notna(gf) else 0,
            "ga": int(ga) if pd.notna(ga) else 0,
            "xg": round(float(xf), 2) if pd.notna(xf) else None,
            "xga": round(float(xa), 2) if pd.notna(xa) else None,
            "result": result,
            "type": mt,
        })
    return out


def compute_h2h(xg_df, team_a, team_b, n=10):
    """Head-to-head record between two teams."""
    played = xg_df[xg_df["home_goals"].notna() & xg_df["away_goals"].notna()]
    mask = (
        ((played["home_team"] == team_a) & (played["away_team"] == team_b))
        | ((played["home_team"] == team_b) & (played["away_team"] == team_a))
    )
    h2h = played[mask].sort_values("datetime", ascending=False).head(n)
    if h2h.empty:
        return None
    a_wins = d_wins = b_wins = 0
    a_gf = a_ga = 0
    matches_list = []
    for _, m in h2h.iterrows():
        if m["home_team"] == team_a:
            af, ag = m["home_goals"], m["away_goals"]
        else:
            af, ag = m["away_goals"], m["home_goals"]
        a_gf += af
        a_ga += ag
        if af > ag:
            a_wins += 1
        elif af < ag:
            b_wins += 1
        else:
            d_wins += 1
        matches_list.append({
            "date": pd.Timestamp(m["datetime"]).strftime("%Y-%m-%d"),
            "score": f"{int(af)}-{int(ag)}",
            "winner": "a" if af > ag else ("b" if af < ag else "d"),
        })
    return {
        "a_wins": a_wins, "draws": d_wins, "b_wins": b_wins,
        "a_gf": a_gf, "a_ga": a_ga,
        "matches": matches_list,
    }


# ── Absences ─────────────────────────────────────────────────────────────────

def compute_availability(abs_df, team_understat, matchweek):
    if abs_df is None:
        return None
    team_tm = UNDERSTAT_TO_TM.get(team_understat, team_understat)
    mw_str = str(int(matchweek)) if pd.notna(matchweek) else ""
    team_abs = abs_df[
        (abs_df["Team"] == team_tm)
        & (abs_df["Matchweek"].astype(str) == mw_str)
    ]
    if team_abs.empty:
        team_norm = normalize_name(team_tm)
        team_abs = abs_df[abs_df["Matchweek"].astype(str) == mw_str]
        team_abs = team_abs[
            team_abs["Team"].apply(lambda t: normalize_name(t) == team_norm)
        ]
    if team_abs.empty:
        return None

    active = team_abs[team_abs["Match_status"] != "No match"]
    if active.empty:
        return None

    total_w = 0.0
    avail_w = 0.0
    absent_players = []
    for _, row in active.iterrows():
        pos = str(row.get("Position", "")).upper().strip()
        w = POSITION_WEIGHTS.get(pos, DEFAULT_POS_WEIGHT)
        total_w += w
        status = str(row.get("Match_status", ""))
        if status in AVAILABLE_STATUSES:
            avail_w += w
        else:
            absent_players.append({
                "player": row.get("Player", ""),
                "position": row.get("Position", ""),
                "status": status,
                "detail": row.get("Absence_detail", ""),
                "type": row.get("Absence_type", ""),
            })

    if total_w == 0:
        return None
    return {"score": avail_w / total_w, "absent_players": absent_players}


# ── Formations ───────────────────────────────────────────────────────────────

def compute_formation_stability(form_df, team_understat, n=ROLLING_WINDOW):
    if form_df is None:
        return None
    team_tm = UNDERSTAT_TO_TM.get(team_understat, team_understat)
    team_norm = normalize_name(team_tm)

    mask = form_df["home_team"].apply(normalize_name) == team_norm
    mask |= form_df["away_team"].apply(normalize_name) == team_norm
    team_matches = form_df[mask].sort_values("matchday", ascending=False).head(n * 2)

    if team_matches.empty:
        return None

    formations = []
    for _, row in team_matches.iterrows():
        text = str(row.get("formation_text", ""))
        m = _FORM_RE.search(text)
        if not m:
            continue
        is_home = row.get("is_home", True)
        if isinstance(is_home, str):
            is_home = is_home.lower() == "true"
        if is_home:
            side_match = normalize_name(row.get("home_team", "")) == team_norm
        else:
            side_match = normalize_name(row.get("away_team", "")) == team_norm
        if side_match:
            formations.append({
                "formation": m.group(1),
                "matchday": int(row.get("matchday", 0)) if pd.notna(row.get("matchday")) else 0,
            })

    if not formations:
        return None

    changes = 0
    for i in range(1, len(formations)):
        prev_def = int(formations[i - 1]["formation"].split("-")[0])
        curr_def = int(formations[i]["formation"].split("-")[0])
        if prev_def != curr_def:
            changes += 1

    stability = 1.0 - (changes / max(len(formations) - 1, 1))
    return {
        "score": stability,
        "recent_formations": formations,
        "last_formation": formations[0]["formation"] if formations else "",
        "radical_changes": changes,
    }


# ── Odds ─────────────────────────────────────────────────────────────────────

def extract_match_odds(odds_df, home_team, away_team):
    if odds_df is None:
        return None
    home_norm = normalize_name(home_team)
    away_norm = normalize_name(away_team)

    def match_names(match_name):
        parts = re.split(r"\s+vs?\s+", str(match_name).lower())
        if len(parts) != 2:
            return False
        h = normalize_name(parts[0])
        a = normalize_name(parts[1])
        return (h == home_norm and a == away_norm) or (h == away_norm and a == home_norm)

    match_odds = odds_df[odds_df["match_name"].apply(match_names)]
    if match_odds.empty:
        return None

    market_1x2 = match_odds[
        match_odds["market_name"].str.contains("1X2|Match Result|Full Time", case=False, na=False)
    ]
    if market_1x2.empty:
        market_1x2 = match_odds[match_odds["choice_name"].isin(["1", "X", "2", "Home", "Draw", "Away"])]
    if market_1x2.empty:
        return None

    odds = {}
    for _, row in market_1x2.iterrows():
        choice = str(row["choice_name"]).strip()
        current = row.get("current_odds")
        if pd.isna(current):
            current = row.get("opening_odds")
        if pd.notna(current):
            if choice in ("1", "Home"):
                odds["home"] = float(current)
            elif choice in ("X", "Draw"):
                odds["draw"] = float(current)
            elif choice in ("2", "Away"):
                odds["away"] = float(current)

    if "home" not in odds or "away" not in odds:
        return None
    odds.setdefault("draw", 0.0)

    total_inv = 0.0
    for k in ("home", "draw", "away"):
        if odds[k] > 0:
            total_inv += 1.0 / odds[k]
    if total_inv == 0:
        return None

    # Also extract other markets for extended view
    other_markets = {}
    for _, row in match_odds.iterrows():
        mkt = str(row.get("market_name", ""))
        if "1X2" in mkt or "Match Result" in mkt or "Full Time" in mkt:
            continue
        current = row.get("current_odds")
        if pd.isna(current):
            current = row.get("opening_odds")
        if pd.notna(current):
            other_markets.setdefault(mkt, []).append({
                "choice": str(row.get("choice_name", "")),
                "odds": float(current),
            })

    return {
        "home_odds": odds["home"],
        "draw_odds": odds.get("draw") or None,
        "away_odds": odds["away"],
        "implied_home": (1.0 / odds["home"]) / total_inv if odds["home"] > 0 else 0,
        "implied_away": (1.0 / odds["away"]) / total_inv if odds["away"] > 0 else 0,
        "other_markets": other_markets if other_markets else None,
    }


# ── Tips ─────────────────────────────────────────────────────────────────────

def extract_match_tips(tips_df, home_team, away_team):
    if tips_df is None:
        return None
    home_norm = normalize_name(home_team)
    away_norm = normalize_name(away_team)

    def match_names(match_name):
        parts = re.split(r"\s+(?:vs?|Vs)\s+", str(match_name), flags=re.I)
        if len(parts) != 2:
            return False
        h = normalize_name(parts[0])
        a = normalize_name(parts[1])
        return (h == home_norm and a == away_norm) or (h == away_norm and a == home_norm)

    match_tips = tips_df[tips_df["match"].apply(match_names)]
    if match_tips.empty:
        return None

    home_tips = 0
    away_tips = 0
    tip_list = []
    for _, row in match_tips.iterrows():
        tip_text = str(row.get("tip", "")).lower()
        tip_norm = normalize_name(tip_text)
        home_in = len(home_norm) > 2 and home_norm in tip_norm
        away_in = len(away_norm) > 2 and away_norm in tip_norm

        if "to win" in tip_text or "win" in tip_text:
            if home_in and not away_in:
                home_tips += 1
                favor = "home"
            elif away_in and not home_in:
                away_tips += 1
                favor = "away"
            else:
                favor = "neutral"
        elif "draw" in tip_text:
            favor = "draw"
        else:
            favor = "neutral"

        tip_list.append({
            "tipster": str(row.get("comment", ""))[:100],
            "tip": row.get("tip", ""),
            "website": row.get("website", ""),
            "rating": str(row.get("rating", "")),
            "favor": favor,
        })

    total = home_tips + away_tips
    if total == 0:
        hs, as_ = 0.5, 0.5
    else:
        hs = home_tips / total
        as_ = away_tips / total

    return {
        "home_score": hs,
        "away_score": as_,
        "tips": tip_list,
        "home_count": home_tips,
        "away_count": away_tips,
    }


# ── Composite score ──────────────────────────────────────────────────────────

_TIMING_SEGMENTS = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"]


def compute_timing_score(team_row, opp_row):
    """Timing edge (0-100): high when a team scores in the very periods the opponent
    concedes most. Overlap of the team's goals-for distribution with the opponent's
    goals-against distribution, scaled so a uniform/no-edge profile ~= 50."""
    if team_row is None or opp_row is None:
        return None
    tgf = [float(team_row.get(f"gf_{s}", 0) or 0) for s in _TIMING_SEGMENTS]
    oga = [float(opp_row.get(f"ga_{s}", 0) or 0) for s in _TIMING_SEGMENTS]
    ttgf, toga = sum(tgf), sum(oga)
    if ttgf == 0 or toga == 0:
        return None
    tdist = [g / ttgf for g in tgf]
    odist = [g / toga for g in oga]
    overlap = sum(tdist[i] * odist[i] for i in range(len(_TIMING_SEGMENTS)))
    # 0-1 scale (matches the other components): uniform/no-edge ~= 0.5, strong edge -> 1.0
    return min(1.0, overlap / (1.0 / len(_TIMING_SEGMENTS)) * 0.5)


def compute_composite(components, weights):
    available = {k: v for k, v in components.items() if v is not None}
    if not available:
        return 0.0
    total_w = sum(weights[k] for k in available)
    if total_w == 0:
        return 0.0
    return sum(available[k] * weights[k] for k in available) / total_w * 100.0


# ── Team metric cache ────────────────────────────────────────────────────────

_team_cache = {}


def get_team_form_data(xg_df, team, friendlies_df=None, prev_season_df=None):
    """Cached form data for a team (matches, results, xg, form string, xg rolling)."""
    cache_key = team
    if cache_key in _team_cache:
        return _team_cache[cache_key]
    matches = get_team_matches(xg_df, team, ROLLING_WINDOW, friendlies_df, prev_season_df)

    # Count match types
    league_count = friendly_count = prev_season_count = 0
    if not matches.empty:
        if "match_type" in matches.columns:
            mt = matches["match_type"]
            league_count = int(mt.isna().sum())
            friendly_count = int((mt == "friendly").sum())
            prev_season_count = int((mt == "prev_season").sum())
        else:
            league_count = len(matches)

    data = {
        "matches": matches,
        "results": compute_results_form(matches, team),
        "xg": compute_xg_form(matches, team),
        "form_string": get_form_string(matches, team),
        "xg_rolling": compute_xg_rolling(matches, team),
        "league_count": league_count,
        "friendly_count": friendly_count,
        "prev_season_count": prev_season_count,
    }
    _team_cache[team] = data
    return data


# ── Build match data ─────────────────────────────────────────────────────────

def build_match_data(xg_df, abs_df, form_df, odds_df, tips_df, match_row,
                     friendlies_df=None, prev_season_df=None, goal_timing_df=None):
    """Build full data for one match (both condensed + extended fields)."""
    home_team = match_row["home_team"]
    away_team = match_row["away_team"]
    match_dt = pd.Timestamp(match_row["datetime"])
    league = match_row["league"]
    gameweek = match_row.get("gameweek")
    match_id = str(match_row.get("match_id", ""))

    # Map Sofascore names to Understat names for form lookups
    home_us = SOFASCORE_TO_UNDERSTAT.get(home_team, home_team)
    away_us = SOFASCORE_TO_UNDERSTAT.get(away_team, away_team)

    home_form = get_team_form_data(xg_df, home_us, friendlies_df, prev_season_df) if xg_df is not None else {"matches": pd.DataFrame(), "results": 0.5, "xg": 0.5, "form_string": [], "xg_rolling": [], "league_count": 0, "friendly_count": 0, "prev_season_count": 0}
    away_form = get_team_form_data(xg_df, away_us, friendlies_df, prev_season_df) if xg_df is not None else {"matches": pd.DataFrame(), "results": 0.5, "xg": 0.5, "form_string": [], "xg_rolling": [], "league_count": 0, "friendly_count": 0, "prev_season_count": 0}

    home_avail = compute_availability(abs_df, home_us, gameweek)
    away_avail = compute_availability(abs_df, away_us, gameweek)

    home_form_stab = compute_formation_stability(form_df, home_us)
    away_form_stab = compute_formation_stability(form_df, away_us)

    match_odds = extract_match_odds(odds_df, home_team, away_team)
    match_tips = extract_match_tips(tips_df, home_team, away_team)

    # Fallback: use understat forecast if no odds
    if match_odds is None:
        fh = match_row.get("forecast_home_win")
        fd = match_row.get("forecast_draw")
        fa = match_row.get("forecast_away_win")
        if pd.notna(fh) and pd.notna(fa):
            total = (fh or 0) + (fd or 0) + (fa or 0)
            if total > 0:
                match_odds = {
                    "home_odds": None, "draw_odds": None, "away_odds": None,
                    "implied_home": (fh or 0) / total,
                    "implied_away": (fa or 0) / total,
                    "other_markets": None,
                }

    # Timing edge: does each team score when THIS opponent tends to concede?
    home_gt_row = away_gt_row = None
    if goal_timing_df is not None:
        _h = goal_timing_df[goal_timing_df["team"] == home_us]
        _a = goal_timing_df[goal_timing_df["team"] == away_us]
        home_gt_row = _h.iloc[0] if not _h.empty else None
        away_gt_row = _a.iloc[0] if not _a.empty else None
    home_timing = compute_timing_score(home_gt_row, away_gt_row)
    away_timing = compute_timing_score(away_gt_row, home_gt_row)

    home_components = {
        "results": home_form["results"],
        "xg": home_form["xg"],
        "availability": home_avail["score"] if home_avail else None,
        "odds": match_odds["implied_home"] if match_odds else None,
        "tips": match_tips["home_score"] if match_tips else None,
        "timing": home_timing,
    }
    away_components = {
        "results": away_form["results"],
        "xg": away_form["xg"],
        "availability": away_avail["score"] if away_avail else None,
        "odds": match_odds["implied_away"] if match_odds else None,
        "tips": match_tips["away_score"] if match_tips else None,
        "timing": away_timing,
    }

    home_score = compute_composite(home_components, WEIGHTS)
    away_score = compute_composite(away_components, WEIGHTS)

    h2h = compute_h2h(xg_df, home_us, away_us) if xg_df is not None else None

    def pct(v):
        return round(v * 100, 1) if v is not None else None

    def sanitize_absences(players):
        out = []
        for p in (players or []):
            out.append({
                "player": str(p.get("player", "") or ""),
                "position": str(p.get("position", "") or ""),
                "status": str(p.get("status", "") or ""),
                "detail": str(p.get("detail", "") or "") if pd.notna(p.get("detail")) else "",
                "type": str(p.get("type", "") or "") if pd.notna(p.get("type")) else "",
            })
        return out

    home_absent_count = len(home_avail["absent_players"]) if home_avail else 0
    away_absent_count = len(away_avail["absent_players"]) if away_avail else 0

    has_results = bool(home_form["form_string"] or away_form["form_string"])
    has_xg = bool(home_form["xg_rolling"] or away_form["xg_rolling"])
    has_availability = home_avail is not None or away_avail is not None
    has_formation = home_form_stab is not None or away_form_stab is not None
    has_odds = match_odds is not None
    has_tips = match_tips is not None and len(match_tips.get("tips", [])) > 0
    has_h2h = h2h is not None

    has_timing = home_timing is not None or away_timing is not None
    sources = {
        "results": has_results,
        "xg": has_xg,
        "availability": has_availability,
        "odds": has_odds,
        "tips": has_tips,
        "timing": has_timing,
    }
    validity_count = sum(1 for v in sources.values() if v)
    validity_total = len(sources)

    # ── Value bets: compare form-based probability vs odds-implied probability ─
    value_bets = []
    if match_odds and match_odds.get("implied_home") is not None:
        total_score = home_score + away_score
        if total_score > 0:
            form_home_prob = home_score / total_score
            form_away_prob = away_score / total_score
            implied_home = match_odds["implied_home"]
            implied_away = match_odds["implied_away"]

            edge_home = form_home_prob - implied_home
            edge_away = form_away_prob - implied_away

            # Also factor in tipster consensus
            tip_home_boost = 0
            tip_away_boost = 0
            if match_tips:
                total_tips = (match_tips.get("home_count", 0) + match_tips.get("away_count", 0))
                if total_tips > 0:
                    tip_home_boost = (match_tips["home_count"] / total_tips - 0.5) * 0.1
                    tip_away_boost = (match_tips["away_count"] / total_tips - 0.5) * 0.1

            edge_home_adj = edge_home + tip_home_boost
            edge_away_adj = edge_away + tip_away_boost

            THRESHOLD = 0.05
            if edge_home_adj > THRESHOLD:
                value_bets.append({
                    "side": "home",
                    "team": home_team,
                    "odds": match_odds.get("home_odds"),
                    "form_prob": round(form_home_prob * 100),
                    "implied_prob": round(implied_home * 100),
                    "edge": round(edge_home_adj * 100, 1),
                })
            if edge_away_adj > THRESHOLD:
                value_bets.append({
                    "side": "away",
                    "team": away_team,
                    "odds": match_odds.get("away_odds"),
                    "form_prob": round(form_away_prob * 100),
                    "implied_prob": round(implied_away * 100),
                    "edge": round(edge_away_adj * 100, 1),
                })
            # Sort by edge descending
            value_bets.sort(key=lambda v: v["edge"], reverse=True)

    goal_timing = None
    if goal_timing_df is not None:
        segments = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"]
        home_gt = goal_timing_df[goal_timing_df["team"] == home_us]
        away_gt = goal_timing_df[goal_timing_df["team"] == away_us]
        if not home_gt.empty or not away_gt.empty:
            goal_timing = {"segments": segments}
            for side, gt in [("home", home_gt), ("away", away_gt)]:
                if not gt.empty:
                    row = gt.iloc[0]
                    goal_timing[side] = {
                        "gf": [int(row.get(f"gf_{s}", 0)) for s in segments],
                        "ga": [int(row.get(f"ga_{s}", 0)) for s in segments],
                    }
                else:
                    goal_timing[side] = {"gf": [0]*6, "ga": [0]*6}

    return {
        "id": match_id,
        "league": league,
        "datetime": match_dt.strftime("%Y-%m-%d %H:%M"),
        "date_short": match_dt.strftime("%b %d %H:%M"),
        "gameweek": int(gameweek) if pd.notna(gameweek) else None,
        "home_team": home_team,
        "away_team": away_team,
        "home": {
            "team": home_team,
            "score": round(home_score, 1),
            "components": {
                "results": pct(home_form["results"]),
                "xg": pct(home_form["xg"]),
                "availability": pct(home_avail["score"]) if home_avail else None,
                "odds": pct(match_odds["implied_home"]) if match_odds else None,
                "tips": pct(match_tips["home_score"]) if match_tips else None,
                "timing": pct(home_timing),
            },
            "form_string": home_form["form_string"],
            "xg_rolling": home_form["xg_rolling"],
            "absences": sanitize_absences(home_avail["absent_players"]) if home_avail else [],
            "absent_count": home_absent_count,
            "last_formation": home_form_stab["last_formation"] if home_form_stab else None,
            "formation_history": home_form_stab["recent_formations"] if home_form_stab else [],
            "radical_changes": home_form_stab["radical_changes"] if home_form_stab else 0,
            "form_breakdown": {
                "league": home_form.get("league_count", 0),
                "friendly": home_form.get("friendly_count", 0),
                "prev_season": home_form.get("prev_season_count", 0),
            },
            "form_matches": serialize_form_matches(home_form["matches"], home_us),
        },
        "away": {
            "team": away_team,
            "score": round(away_score, 1),
            "components": {
                "results": pct(away_form["results"]),
                "xg": pct(away_form["xg"]),
                "availability": pct(away_avail["score"]) if away_avail else None,
                "odds": pct(match_odds["implied_away"]) if match_odds else None,
                "tips": pct(match_tips["away_score"]) if match_tips else None,
                "timing": pct(away_timing),
            },
            "form_string": away_form["form_string"],
            "xg_rolling": away_form["xg_rolling"],
            "absences": sanitize_absences(away_avail["absent_players"]) if away_avail else [],
            "absent_count": away_absent_count,
            "last_formation": away_form_stab["last_formation"] if away_form_stab else None,
            "formation_history": away_form_stab["recent_formations"] if away_form_stab else [],
            "radical_changes": away_form_stab["radical_changes"] if away_form_stab else 0,
            "form_breakdown": {
                "league": away_form.get("league_count", 0),
                "friendly": away_form.get("friendly_count", 0),
                "prev_season": away_form.get("prev_season_count", 0),
            },
            "form_matches": serialize_form_matches(away_form["matches"], away_us),
        },
        "odds": {
            "home": match_odds["home_odds"] if match_odds else None,
            "draw": match_odds["draw_odds"] if match_odds else None,
            "away": match_odds["away_odds"] if match_odds else None,
            "other_markets": match_odds["other_markets"] if match_odds else None,
        },
        "tips": match_tips["tips"] if match_tips else [],
        "tips_summary": {
            "home": match_tips["home_count"] if match_tips else 0,
            "away": match_tips["away_count"] if match_tips else 0,
        } if match_tips else None,
        "h2h": h2h,
        "sources": sources,
        "validity": validity_count,
        "validity_total": validity_total,
        "value_bets": value_bets,
        "goal_timing": goal_timing,
    }


# ── HTML generation ──────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Big 5 — Match Form Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0f1117;--card:#1a1d27;--card2:#22252f;--border:#2a2d3a;--border2:#363945;
  --text:#e4e6eb;--dim:#8b8e98;--dimmer:#5a5d68;
  --green:#00d97e;--yellow:#ffc107;--red:#f44336;--accent:#6c5ce7;--blue:#3b82f6;
}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;padding:16px;min-height:100vh;overflow-x:hidden}
.container{max-width:1100px;margin:0 auto;width:100%}
.table-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}

.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.page-header h1{font-size:20px;font-weight:700}
.page-header .meta{font-size:12px;color:var(--dim)}

/* Filters */
.filters{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;align-items:center}
.filters .label{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:1px;margin-right:4px}
.filter-chip{padding:5px 12px;border:1px solid var(--border);border-radius:20px;background:var(--card);color:var(--dim);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;user-select:none}
.filter-chip:hover{border-color:var(--border2);color:var(--text)}
.filter-chip.active{background:var(--accent);border-color:var(--accent);color:#fff}
.filter-chip .count{font-size:10px;opacity:.7;margin-left:3px}

/* Table */
.match-table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
.match-table th{padding:10px 8px;text-align:left;color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid var(--border);position:sticky;top:0;background:var(--bg);z-index:1;white-space:nowrap}
.match-table th.sortable{cursor:pointer;user-select:none}
.match-table th.sortable:hover{color:var(--text)}
.match-table th.sort-active{color:var(--accent)}
.sort-arrow{font-size:9px;margin-left:2px}
.match-table td{padding:10px 8px;border-bottom:1px solid var(--border);cursor:pointer;transition:background .12s;vertical-align:middle}
.match-table tr:hover td{background:var(--card)}
.match-table tr.selected td{background:var(--card2)}
.match-table tr.hidden{display:none}

.league-badge{font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600;white-space:nowrap}
.lg-Serie-A{background:rgba(0,120,255,.15);color:#4d9fff}
.lg-Premier-League{background:rgba(239,62,43,.15);color:#ef3e2f}
.lg-La-Liga{background:rgba(255,140,0,.15);color:#ff8c00}
.lg-Bundesliga{background:rgba(220,0,0,.15);color:#dc0000}
.lg-Ligue-1{background:rgba(180,0,220,.15);color:#b400dc}

.date-cell{color:var(--dim);font-size:12px;white-space:nowrap}
.team-cell{font-weight:600;white-space:nowrap}
.team-cell.away{text-align:right}
.score-cell{font-weight:800;font-size:18px;text-align:center;width:44px;white-space:nowrap}
.form-cell{text-align:center;white-space:nowrap}
.form-mini{display:inline-flex;width:18px;height:18px;border-radius:4px;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#fff;vertical-align:middle}
.form-mini.W{background:var(--green)}
.form-mini.D{background:var(--yellow);color:#333}
.form-mini.L{background:var(--red)}
.form-mini.empty{background:var(--border);color:var(--dimmer)}

.abs-cell{text-align:center;font-size:11px}
.abs-num{padding:2px 6px;border-radius:4px;font-weight:600}
.abs-num.zero{color:var(--dimmer)}
.abs-num.some{background:rgba(255,193,7,.15);color:var(--yellow)}
.abs-num.high{background:rgba(244,67,54,.15);color:var(--red)}

.odds-cell{text-align:center;font-size:12px;color:var(--dim);white-space:nowrap}
.odds-cell .fav{color:var(--accent);font-weight:600}

/* Validity */
.validity-cell{text-align:center;white-space:nowrap}
.validity-dots{display:inline-flex;gap:3px;align-items:center}
.vdot{width:7px;height:7px;border-radius:50%;background:var(--border)}
.vdot.on{background:var(--green)}
.validity-num{font-size:11px;font-weight:700;margin-left:5px;color:var(--dim)}
.validity-num.high{color:var(--green)}
.validity-num.mid{color:var(--yellow)}
.validity-num.low{color:var(--red)}

/* Source indicators in table */
.src-cell{text-align:center}
.src-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 1px;background:var(--border)}
.src-dot.on{background:var(--green)}

/* Expanded row */
.expanded-row td{padding:0;border-bottom:1px solid var(--border);background:var(--card)}
.expanded-content{padding:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px}
.expanded-content .full{grid-column:1/-1}

/* Team card inside expanded */
.team-block{background:var(--card2);border:1px solid var(--border2);border-radius:10px;padding:16px}
.team-block .tn{font-size:15px;font-weight:700;margin-bottom:2px}
.team-block .ts{font-size:36px;font-weight:800;line-height:1}
.team-block .tf{display:flex;gap:3px;margin:8px 0}
.team-block .tf .form-box{width:22px;height:22px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff}
.team-block .tf .form-box.W{background:var(--green)}
.team-block .tf .form-box.D{background:var(--yellow);color:#333}
.team-block .tf .form-box.L{background:var(--red)}
.team-block .tf .form-box.empty{background:var(--border);color:var(--dimmer)}

.metric{margin:8px 0}
.metric-label{display:flex;justify-content:space-between;font-size:11px;color:var(--dim);margin-bottom:2px}
.metric-track{height:5px;background:var(--border);border-radius:3px;overflow:hidden}
.metric-fill{height:100%;border-radius:3px}
.fill-good{background:var(--green)}
.fill-mid{background:var(--yellow)}
.fill-bad{background:var(--red)}

.section-title{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--dim);margin-bottom:8px;margin-top:12px}
.absence-item{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);font-size:12px}
.absence-item:last-child{border-bottom:none}
.absence-item .pn{font-weight:600}
.absence-item .pp{color:var(--dim);font-size:10px;margin-left:3px}
.abs-badge{font-size:9px;padding:2px 6px;border-radius:3px;font-weight:600}
.abs-badge.Injured{background:rgba(244,67,54,.15);color:var(--red)}
.abs-badge.Suspended{background:rgba(255,140,0,.15);color:#ff8c00}
.abs-badge.Loaned{background:rgba(59,130,246,.15);color:var(--blue)}
.abs-badge.Not{background:rgba(107,92,231,.15);color:var(--accent)}
.abs-badge.International{background:rgba(0,217,126,.15);color:var(--green)}

.form-history{display:flex;gap:4px;flex-wrap:wrap}
.form-hist-item{padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;background:var(--card2);border:1px solid var(--border2)}
.form-hist-item .mw{color:var(--dim);font-size:8px;margin-left:2px}

.xg-spark{display:flex;align-items:flex-end;gap:2px;height:36px}
.xg-bar{flex:1;border-radius:2px 2px 0 0;min-height:2px}
.xg-bar.pos{background:var(--green)}
.xg-bar.neg{background:var(--red)}

.h2h-bar{display:flex;height:22px;border-radius:5px;overflow:hidden;margin:6px 0}
.h2h-seg{display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff}
.h2h-seg.a{background:var(--green)}
.h2h-seg.d{background:var(--yellow);color:#333}
.h2h-seg.b{background:var(--red)}
.h2h-matches{display:flex;gap:6px;flex-wrap:wrap;margin-top:4px}
.h2h-match{font-size:10px;padding:2px 6px;border-radius:4px;background:var(--card2);border:1px solid var(--border2)}

.odds-row{display:flex;justify-content:center;gap:20px}
.odd{text-align:center;min-width:50px}
.odd .label{font-size:10px;color:var(--dim);text-transform:uppercase}
.odd .value{font-size:18px;font-weight:700}
.odds-table{width:100%;font-size:11px;margin-top:6px;border-collapse:collapse}
.odds-table td{padding:5px 4px;border-bottom:1px solid var(--border);vertical-align:top}
.odds-table .mkt{color:var(--dim);white-space:nowrap;padding-right:8px}
.odds-table .val{display:flex;flex-wrap:wrap;gap:4px;justify-content:flex-end}
.od{display:inline-block;padding:2px 7px;border-radius:5px;background:var(--card);border:1px solid var(--border);color:var(--dim);font-weight:600;white-space:nowrap}
.od-pred{background:rgba(0,217,126,.15);border-color:rgba(0,217,126,.45);color:var(--green)}
.od-pred b{color:var(--green);font-weight:800}
.od-note{font-size:9px;color:var(--dimmer);margin-top:6px;text-align:center;line-height:1.4}

.tip-item{display:flex;align-items:center;gap:10px;padding:4px 0;border-bottom:1px solid var(--border);font-size:12px}
.tip-item:last-child{border-bottom:none}
.tip-source{color:var(--accent);font-weight:600;min-width:80px;font-size:11px}
.tip-text{flex:1}
.tip-favor{font-size:10px;padding:2px 6px;border-radius:3px;font-weight:600}
.tip-favor.home{background:rgba(0,217,126,.15);color:var(--green)}
.tip-favor.away{background:rgba(244,67,54,.15);color:var(--red)}
.tip-favor.neutral,.tip-favor.draw{background:rgba(255,193,7,.15);color:var(--yellow)}

.no-data{text-align:center;color:var(--dim);padding:40px;font-size:16px}
.footer{text-align:center;margin-top:20px;color:var(--dim);font-size:11px}

/* Value bets */
.vb-cell{text-align:center;white-space:nowrap}
.vb-tag{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;margin:1px}
.vb-high{background:rgba(0,217,126,.2);color:var(--green);border:1px solid rgba(0,217,126,.3)}
.vb-mid{background:rgba(255,193,7,.2);color:var(--yellow);border:1px solid rgba(255,193,7,.3)}
.vb-low{background:rgba(107,92,231,.15);color:var(--accent);border:1px solid rgba(107,92,231,.25)}

@media(max-width:768px){
  body{padding:10px}
  .page-header{flex-direction:column;align-items:flex-start;gap:4px}
  .expanded-content{grid-template-columns:1fr;padding:14px;gap:12px}
  .match-table{font-size:11px}
  .match-table th,.match-table td{padding:5px 3px}
  .score-cell{font-size:15px;width:36px}
  .form-mini{width:14px;height:14px;font-size:7px}
  .team-block{padding:12px}
  .team-block .ts{font-size:30px}
}
@media(max-width:600px){
  /* Trim the match table to the essentials; details live in the expanded row */
  .match-table th:nth-child(2),.match-table td:nth-child(2),
  .match-table th:nth-child(5),.match-table td:nth-child(5),
  .match-table th:nth-child(6),.match-table td:nth-child(6),
  .match-table th:nth-child(8),.match-table td:nth-child(8),
  .match-table th:nth-child(9),.match-table td:nth-child(9),
  .match-table th:nth-child(12),.match-table td:nth-child(12){display:none}
}
@media(max-width:480px){
  body{padding:6px}
  .page-header h1{font-size:17px}
  .filters{gap:4px}
  .filter-chip{padding:4px 9px;font-size:11px}
  .expanded-content{padding:10px}
  .odds-table .val{justify-content:flex-start}
  .odds-table .mkt{white-space:normal}
}
</style>
</head>
<body>
<div id="app"></div>
<script>
const DATA = __JSON__;
const ROLLING_WINDOW = __ROLLING_WINDOW__;
const LEAGUE_MATCH_THRESHOLD = __LEAGUE_MATCH_THRESHOLD__;
const METRICS=[
  {key:'results',label:'Results',w:'25%'},
  {key:'xg',label:'xG',w:'20%'},
  {key:'availability',label:'Avail',w:'20%'},
  {key:'formation',label:'Form',w:'10%'},
  {key:'odds',label:'Odds',w:'15%'},
  {key:'tips',label:'Tips',w:'10%'},
];
const SOURCES=[
  {key:'results',label:'Results'},
  {key:'xg',label:'xG'},
  {key:'availability',label:'Absences'},
  {key:'formation',label:'Formation'},
  {key:'odds',label:'Odds'},
  {key:'tips',label:'Tipsters'},
  {key:'h2h',label:'H2H'},
];
let selectedIdx=-1;
let activeFilters=new Set();
let sortKey=null;
let sortDir=1;

function scoreClass(s){return s>=70?'score-good':s>=50?'score-mid':'score-bad'}
function fillClass(v){return v>=60?'fill-good':v>=40?'fill-mid':'fill-bad'}
function leagueClass(l){return 'lg-'+l.replace(/[^a-zA-Z]/g,'-')}
function absClass(n){return n===0?'zero':n<=3?'some':'high'}
function valClass(n,total){return n>=total*0.7?'high':n>=total*0.4?'mid':'low'}

function formBoxes(arr,mini){
  const cls=mini?'form-mini':'form-box';
  if(!arr||arr.length===0){
    if(mini) return '<div class="form-mini empty">-</div>';
    return '<div class="form-box empty">-</div>';
  }
  return arr.map(r=>'<div class="'+cls+' '+r+'">'+r+'</div>').join('');
}

function matchPassesFilters(m){
  if(activeFilters.size===0) return true;
  for(const f of activeFilters){
    if(!m.sources[f]) return false;
  }
  return true;
}

function formScore(formString){
  if(!formString||formString.length===0) return 0;
  let s=0;
  for(const r of formString){ if(r==='W') s+=3; else if(r==='D') s+=1; }
  return s;
}

const VB_SCORE_THRESHOLD=50;
const VB_SOURCE_THRESHOLD=4;
const VB_SCORE_GAP=20;
function getValueEdge(m,side){
  const score=side==='home'?m.home.score:m.away.score;
  const oppScore=side==='home'?m.away.score:m.home.score;
  if(score<VB_SCORE_THRESHOLD||m.validity<VB_SOURCE_THRESHOLD) return null;
  if(score<oppScore-VB_SCORE_GAP) return null;
  const vbs=m.value_bets;
  if(!vbs||vbs.length===0) return null;
  const filtered=vbs.filter(v=>v.side===side);
  if(filtered.length===0) return null;
  return Math.max(...filtered.map(v=>v.edge));
}

function getSortValue(m,key){
  switch(key){
    case 'league': return m.league;
    case 'date': return m.date_short;
    case 'home_team': return m.home.team;
    case 'home_score': return m.home.score;
    case 'home_form': return formScore(m.home.form_string);
    case 'home_abs': return m.home.absent_count;
    case 'away_score': return m.away.score;
    case 'away_form': return formScore(m.away.form_string);
    case 'away_abs': return m.away.absent_count;
    case 'away_team': return m.away.team;
    case 'odds': return m.odds.home||0;
    case 'validity': return m.validity;
    case 'value_home': return getValueEdge(m,'home');
    case 'value_away': return getValueEdge(m,'away');
    default: return 0;
  }
}

function sortBy(key){
  if(sortKey===key){ sortDir=-sortDir; }
  else { sortKey=key; sortDir=1; }
  render();
}

function renderFilters(){
  let html='<div class="filters"><span class="label">Filter by source:</span>';
  SOURCES.forEach(s=>{
    const count=DATA.matches.filter(m=>m.sources[s.key]).length;
    const active=activeFilters.has(s.key)?'active':'';
    html+='<span class="filter-chip '+active+'" onclick="toggleFilter(\''+s.key+'\')">'+s.label+'<span class="count">'+count+'</span></span>';
  });
  if(activeFilters.size>0){
    html+='<span class="filter-chip" onclick="clearFilters()" style="border-color:var(--red);color:var(--red)">Clear</span>';
  }
  html+='</div>';
  return html;
}

function renderValidity(m){
  let dots='';
  SOURCES.forEach(s=>{
    dots+='<div class="vdot '+(m.sources[s.key]?'on':'')+'" title="'+s.label+'"></div>';
  });
  const vc=valClass(m.validity,m.validity_total);
  return '<div class="validity-cell"><div class="validity-dots">'+dots+'</div><span class="validity-num '+vc+'">'+m.validity+'/'+m.validity_total+'</span></div>';
}

function renderValueBetCell(m,side){
  const edge=getValueEdge(m,side);
  if(edge===null) return '<span style="color:var(--dimmer);font-size:11px">—</span>';
  const vbs=m.value_bets;
  const filtered=vbs?vbs.filter(v=>v.side===side):[];
  if(filtered.length===0) return '<span style="color:var(--dimmer);font-size:11px">—</span>';
  return filtered.map(v=>{
    const cls=v.edge>=15?'vb-high':v.edge>=10?'vb-mid':'vb-low';
    return '<div class="vb-tag '+cls+'" title="'+v.team+' @ '+v.odds+' — Form: '+v.form_prob+'% vs Implied: '+v.implied_prob+'%">+'+v.edge+'%</div>';
  }).join('');
}

function renderTable(){
  if(!DATA.matches||DATA.matches.length===0){
    return '<div class="no-data">No upcoming matches found.</div>';
  }
  let indexedMatches=DATA.matches.map((m,i)=>({m,i}));
  if(sortKey){
    indexedMatches.sort((a,b)=>{
      const va=getSortValue(a.m,sortKey);
      const vb=getSortValue(b.m,sortKey);
      if(va===null&&vb===null) return 0;
      if(va===null) return 1;
      if(vb===null) return -1;
      if(typeof va==='string'&&typeof vb==='string'){
        return va.localeCompare(vb)*sortDir;
      }
      return ((va||0)-(vb||0))*sortDir;
    });
  }
  let rows='';
  indexedMatches.forEach(({m,i})=>{
    const passes=matchPassesFilters(m);
    const hidden=passes?'':'hidden';
    const sel=i===selectedIdx?'selected':'';
    const h=m.home,a=m.away;
    const oddsHtml=m.odds.home?'<span class="fav">'+m.odds.home+'</span> / '+m.odds.away:'—';
    rows+='<tr class="'+sel+' '+hidden+'" onclick="toggleMatch('+i+')">'
      +'<td><span class="league-badge '+leagueClass(m.league)+'">'+m.league+'</span></td>'
      +'<td class="date-cell">'+m.date_short+'</td>'
      +'<td class="team-cell">'+h.team+'</td>'
      +'<td class="score-cell '+scoreClass(h.score)+'">'+Math.round(h.score)+'</td>'
      +'<td class="form-cell">'+formBoxes(h.form_string,true)+'</td>'
      +'<td class="abs-cell"><span class="abs-num '+absClass(h.absent_count)+'">'+h.absent_count+'</span></td>'
      +'<td class="score-cell '+scoreClass(a.score)+'">'+Math.round(a.score)+'</td>'
      +'<td class="form-cell">'+formBoxes(a.form_string,true)+'</td>'
      +'<td class="abs-cell"><span class="abs-num '+absClass(a.absent_count)+'">'+a.absent_count+'</span></td>'
      +'<td class="team-cell away">'+a.team+'</td>'
      +'<td class="odds-cell">'+oddsHtml+'</td>'
      +'<td>'+renderValidity(m)+'</td>'
      +'<td class="vb-cell">'+renderValueBetCell(m,'home')+'</td>'
      +'<td class="vb-cell">'+renderValueBetCell(m,'away')+'</td>'
      +'</tr>';
    if(i===selectedIdx && passes){
      rows+='<tr class="expanded-row"><td colspan="14">'+renderExpanded(m)+'</td></tr>';
    }
  });
  const visibleCount=DATA.matches.filter(matchPassesFilters).length;
  function th(key,label){
    const active=sortKey===key?'sort-active':'';
    const arrow=sortKey===key?(sortDir>0?'<span class="sort-arrow">\u2191</span>':'<span class="sort-arrow">\u2193</span>'):'';
    return '<th class="sortable '+active+'" onclick="sortBy(\''+key+'\')">'+label+arrow+'</th>';
  }
  return '<div class="table-wrap"><table class="match-table"><thead><tr>'
    +th('league','League')+th('date','Date')
    +th('home_team','Home')+th('home_score','Score')+th('home_form','Form')+th('home_abs','Abs')
    +th('away_score','Score')+th('away_form','Form')+th('away_abs','Abs')
    +th('away_team','Away')+th('odds','Odds')+th('validity','Sources')+th('value_home','Val H')+th('value_away','Val A')
    +'</tr></thead><tbody>'+rows+'</tbody></table></div>'
    +'<div style="text-align:center;color:var(--dim);font-size:12px;margin-top:8px">'+visibleCount+' / '+DATA.matches.length+' matches</div>';
}

function renderMetricBars(c){
  return METRICS.map(m=>{
    const v=c[m.key];
    if(v===null||v===undefined)return '';
    return '<div class="metric"><div class="metric-label"><span>'+m.label+' <span style="opacity:.5">('+m.w+')</span></span><span>'+Math.round(v)+'</span></div><div class="metric-track"><div class="metric-fill '+fillClass(v)+'" style="width:'+v+'%"></div></div></div>';
  }).join('');
}

function renderAbsences(abs){
  if(!abs||abs.length===0) return '<div style="color:var(--dim);font-size:12px">No absences</div>';
  return abs.map(a=>{
    const bt=(a.type||a.status||'').split('(')[0].trim()||'Unknown';
    const bc=bt.split(' ')[0];
    return '<div class="absence-item"><div><span class="pn">'+a.player+'</span><span class="pp">'+a.position+'</span></div><span class="abs-badge '+bc+'">'+bt+'</span></div>';
  }).join('');
}

function renderFormHist(h){
  if(!h||h.length===0) return '<div style="color:var(--dim);font-size:12px">No data</div>';
  return '<div class="form-history">'+h.slice(0,8).map(f=>'<span class="form-hist-item">'+f.formation+'<span class="mw">MW'+f.matchday+'</span></span>').join('')+'</div>';
}

function renderXgSpark(r){
  if(!r||r.length===0) return '<div style="color:var(--dim);font-size:12px">No xG data</div>';
  const mx=Math.max(...r.map(x=>Math.abs(x.diff)),0.5);
  return '<div class="xg-spark">'+r.map(x=>'<div class="xg-bar '+(x.diff>=0?'pos':'neg')+'" style="height:'+Math.abs(x.diff)/mx*100+'%" title="xG:'+x.xg+' xGA:'+x.xga+'"></div>').join('')+'</div>';
}

function renderH2H(h2h,ht,at){
  if(!h2h) return '<div style="color:var(--dim);font-size:12px">No H2H data</div>';
  const t=h2h.a_wins+h2h.draws+h2h.b_wins;
  if(t===0) return '<div style="color:var(--dim);font-size:12px">No H2H data</div>';
  const aP=Math.round(h2h.a_wins/t*100),dP=Math.round(h2h.draws/t*100),bP=100-aP-dP;
  let bar='<div class="h2h-bar">';
  if(aP>0) bar+='<div class="h2h-seg a" style="width:'+aP+'%">'+h2h.a_wins+'</div>';
  if(dP>0) bar+='<div class="h2h-seg d" style="width:'+dP+'%">'+h2h.draws+'</div>';
  if(bP>0) bar+='<div class="h2h-seg b" style="width:'+bP+'%">'+h2h.b_wins+'</div>';
  bar+='</div>';
  let ms='<div class="h2h-matches">'+h2h.matches.slice(0,6).map(m=>{
    const c=m.winner==='a'?'color:var(--green)':m.winner==='b'?'color:var(--red)':'color:var(--yellow)';
    return '<span class="h2h-match"><span style="'+c+';font-weight:600">'+m.score+'</span> '+m.date+'</span>';
  }).join('')+'</div>';
  return '<div style="font-size:11px;color:var(--dim);margin-bottom:3px">'+ht+' W - D - '+at+' W</div>'+bar+ms;
}

// Predict the likely outcome from the form data we already have, so we can
// highlight the single matching odd per market (not every choice).
function avgGoals(fm){
  if(!fm||!fm.length) return null;
  let gf=0,ga=0,n=0;
  fm.forEach(x=>{gf+=(x.gf||0);ga+=(x.ga||0);n++;});
  return n?{gf:gf/n,ga:ga/n}:null;
}
function matchPrediction(m){
  const hg=avgGoals(m.home.form_matches), ag=avgGoals(m.away.form_matches);
  let eh=null,ea=null,total=null;
  if(hg&&ag){ eh=(hg.gf+ag.ga)/2; ea=(ag.gf+hg.ga)/2; total=eh+ea; }
  const diff=(m.home.score||0)-(m.away.score||0);
  const result=diff>5?'H':diff<-5?'A':'D';
  return {eh,ea,total,result};
}
function parseLine(s){
  const mch=String(s).match(/(\d+(?:\.\d+)?)/);
  return mch?parseFloat(mch[1]):null;
}
// Returns the index of the choice our model predicts, or -1 if we can't map it.
function predictedIndex(name,choices,pred,m){
  const mn=(name||'').toLowerCase();
  const norm=choices.map(c=>String(c[0]).toLowerCase().trim());
  // Over / Under (match total, or team total when the market names a side)
  const isOU=norm.some(c=>/(^|\s)(over|under|o|u)(\s|$|\d|\/)/.test(c))||/over|under|o\/u/.test(mn);
  if(isOU&&pred.total!=null){
    let ref=pred.total;
    if(/home/.test(mn)&&pred.eh!=null) ref=pred.eh;
    else if(/away/.test(mn)&&pred.ea!=null) ref=pred.ea;
    let line=null;
    norm.forEach(c=>{const l=parseLine(c);if(l!=null)line=l;});
    if(line==null) line=parseLine(mn);
    if(line==null) line=2.5;
    const wantOver=ref>line;
    for(let i=0;i<norm.length;i++){
      if(wantOver&&/over|^o/.test(norm[i])) return i;
      if(!wantOver&&/under|^u/.test(norm[i])) return i;
    }
  }
  // Both teams to score
  if(/both teams|btts|gg\/ng/.test(mn)||(norm.includes('yes')&&norm.includes('no'))){
    if(pred.eh!=null&&pred.ea!=null){
      const yes=pred.eh>=0.8&&pred.ea>=0.8;
      for(let i=0;i<norm.length;i++){
        if(yes&&/yes|gg/.test(norm[i])) return i;
        if(!yes&&/no|ng/.test(norm[i])) return i;
      }
    }
  }
  // Double chance
  if(/double chance/.test(mn)||norm.some(c=>/^(1x|12|x2)$/.test(c.replace(/\s/g,'')))){
    for(let i=0;i<norm.length;i++){
      const c=norm[i].replace(/\s/g,'');
      if(pred.result==='H'&&/(1x|12)/.test(c)) return i;
      if(pred.result==='A'&&/(x2|12)/.test(c)) return i;
      if(pred.result==='D'&&/(1x|x2)/.test(c)) return i;
    }
  }
  // Match result / 1X2 / team names
  const home=(m.home_team||'').toLowerCase(), away=(m.away_team||'').toLowerCase();
  function cat(c){
    if(c==='1'||c==='home'||(home&&c===home)) return 'H';
    if(c==='2'||c==='away'||(away&&c===away)) return 'A';
    if(c==='x'||c==='draw'||c==='tie') return 'D';
    return null;
  }
  if(norm.some(c=>cat(c)!==null)){
    for(let i=0;i<norm.length;i++) if(cat(norm[i])===pred.result) return i;
  }
  return -1;
}
function renderOdds(m){
  if(!m.odds) return '<div style="color:var(--dim);font-size:12px">No odds data</div>';
  const pred=matchPrediction(m);
  const markets=[];
  if(m.odds.home){
    const ch=[['Home',m.odds.home],['Draw',m.odds.draw],['Away',m.odds.away]].filter(c=>c[1]);
    if(ch.length>=2) markets.push(['Match Result',ch]);
  }
  if(m.odds.other_markets){
    for(const [mk,list] of Object.entries(m.odds.other_markets)){
      if(!list||list.length<2||list.length>6) continue;
      const ch=list.filter(c=>c.odds>0).map(c=>[String(c.choice),c.odds]);
      if(ch.length>=2) markets.push([mk,ch]);
    }
  }
  if(!markets.length) return '<div style="color:var(--dim);font-size:12px">No odds data</div>';
  let rows='';
  for(const [name,ch] of markets){
    const pi=predictedIndex(name,ch,pred,m);
    const cells=ch.map((c,i)=>{
      const o=(+c[1]).toFixed(2);
      if(i===pi) return '<span class="od od-pred" title="Model pick from recent form">'+c[0]+' <b>'+o+'</b></span>';
      return '<span class="od">'+c[0]+' '+o+'</span>';
    }).join('');
    rows+='<tr><td class="mkt">'+name+'</td><td class="val">'+cells+'</td></tr>';
  }
  let note='';
  if(pred.total!=null){
    note='<div class="od-note">Model from recent form — exp. goals '+m.home_team+' '+pred.eh.toFixed(1)
      +' · '+m.away_team+' '+pred.ea.toFixed(1)+' (total '+pred.total.toFixed(1)
      +'). Highlighted = predicted pick.</div>';
  }
  return '<table class="odds-table">'+rows+'</table>'+note;
}

function renderTips(m){
  if(!m.tips||m.tips.length===0) return '<div style="color:var(--dim);font-size:12px">No tipster data</div>';
  return m.tips.slice(0,8).map(t=>'<div class="tip-item"><span class="tip-source">'+t.website+'</span><span class="tip-text">'+t.tip+'</span><span class="tip-favor '+t.favor+'">'+t.favor+'</span></div>').join('');
}

function renderTeamBlock(t){
  const sc=scoreClass(t.score);
  let fb='';
  if(t.form_breakdown){
    const bd=t.form_breakdown;
    const parts=[];
    if(bd.league)parts.push('<span style="color:var(--green)">'+bd.league+'L</span>');
    if(bd.friendly)parts.push('<span style="color:var(--blue)">'+bd.friendly+'F</span>');
    if(bd.prev_season)parts.push('<span style="color:var(--yellow)">'+bd.prev_season+'S</span>');
    if(parts.length)fb='<div style="text-align:center;font-size:10px;color:var(--dim);margin-bottom:4px">Form: '+parts.join(' · ')+'</div>';
  }
  return '<div class="team-block">'
    +'<div class="tn">'+t.team+'</div>'
    +'<div class="ts '+sc+'">'+Math.round(t.score)+'</div>'
    +fb
    +'<div class="tf">'+formBoxes(t.form_string,false)+'</div>'
    +renderMetricBars(t.components)
    +(t.last_formation?'<div style="text-align:center;margin-top:6px;font-size:12px;color:var(--dim)">Last: <strong style="color:var(--accent)">'+t.last_formation+'</strong></div>':'')
    +'</div>';
}

function renderFormMatches(t){
  if(!t.form_matches||t.form_matches.length===0) return '<div style="color:var(--dim);font-size:12px">No form matches</div>';
  const tc={W:'var(--green)',D:'var(--yellow)',L:'var(--red)'};
  const bc={league:'',friendly:'var(--blue)',prev_season:'var(--yellow)'};
  const bl={league:'L',friendly:'F',prev_season:'S'};
  let rows=t.form_matches.map(function(m){
    const c=tc[m.result]||'var(--dim)';
    const bc2=bc[m.type]||'';
    const bl2=bl[m.type]||'L';
    const xg=m.xg!==null?'<span style="color:var(--dim)"> xG '+m.xg+'-'+m.xga+'</span>':'';
    return '<tr>'
      +'<td style="color:var(--dim);font-size:11px;white-space:nowrap">'+m.date+'</td>'
      +'<td style="font-size:11px">'+m.home_away+'</td>'
      +'<td style="font-size:11px">'+m.opponent+'</td>'
      +'<td style="font-size:11px;text-align:center">'+m.gf+'-'+m.ga+'</td>'
      +'<td style="font-size:11px;text-align:center;color:'+c+';font-weight:700">'+m.result+'</td>'
      +'<td style="font-size:10px;text-align:center;color:'+bc2+'">'+bl2+'</td>'
      +'</tr>';
  }).join('');
  return '<table style="width:100%;border-collapse:collapse"><thead><tr>'
    +'<th style="text-align:left;font-size:10px;color:var(--dim)">Date</th>'
    +'<th style="text-align:left;font-size:10px;color:var(--dim)">H/A</th>'
    +'<th style="text-align:left;font-size:10px;color:var(--dim)">Opp</th>'
    +'<th style="text-align:center;font-size:10px;color:var(--dim)">Sc</th>'
    +'<th style="text-align:center;font-size:10px;color:var(--dim)">R</th>'
    +'<th style="text-align:center;font-size:10px;color:var(--dim)">T</th>'
    +'</tr></thead><tbody>'+rows+'</tbody></table>';
}

function renderExpanded(m){
  const h=m.home,a=m.away;
  return '<div class="expanded-content">'
    +'<div class="full" style="text-align:center;margin-bottom:4px"><span style="color:var(--dim);font-size:12px">'+m.league+' · GW '+(m.gameweek||'?')+' · '+m.datetime+'</span></div>'
    +'<div class="full" style="display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:stretch">'
    +renderTeamBlock(h)+'<div style="display:flex;align-items:center;color:var(--dim);font-weight:700;font-size:16px">VS</div>'+renderTeamBlock(a)
    +'</div>'
    +'<div><div class="section-title">Form Matches ('+h.team+')</div>'+renderFormMatches(h)+'</div>'
    +'<div><div class="section-title">Form Matches ('+a.team+')</div>'+renderFormMatches(a)+'</div>'
    +'<div class="full"><div class="section-title">Head to Head</div>'+renderH2H(m.h2h,m.home_team,m.away_team)+'</div>'
    +'<div><div class="section-title">xG Rolling ('+ROLLING_WINDOW+')</div><div style="font-size:12px;color:var(--accent);margin-bottom:4px">'+h.team+'</div>'+renderXgSpark(h.xg_rolling)+'</div>'
    +'<div><div class="section-title">xG Rolling ('+ROLLING_WINDOW+')</div><div style="font-size:12px;color:var(--accent);margin-bottom:4px">'+a.team+'</div>'+renderXgSpark(a.xg_rolling)+'</div>'
    +'<div><div class="section-title">Formations ('+h.radical_changes+' changes)</div>'+renderFormHist(h.formation_history)+'</div>'
    +'<div><div class="section-title">Formations ('+a.radical_changes+' changes)</div>'+renderFormHist(a.formation_history)+'</div>'
    +'<div><div class="section-title">Absences ('+h.absent_count+')</div>'+renderAbsences(h.absences)+'</div>'
    +'<div><div class="section-title">Absences ('+a.absent_count+')</div>'+renderAbsences(a.absences)+'</div>'
    +'<div class="full"><div class="section-title">Odds</div>'+renderOdds(m)+'</div>'
    +'<div class="full"><div class="section-title">Value Bets</div>'+renderValueBetsExpanded(m.value_bets)+'</div>'
    +'<div class="full"><div class="section-title">Expert Tips ('+(m.tips||[]).length+')</div>'+renderTips(m)+'</div>'
    +'</div>';
}

function renderValueBetsExpanded(vbs){
  if(!vbs||vbs.length===0) return '<div style="color:var(--dim);font-size:12px">No value bets detected — form assessment aligns with market odds</div>';
  return '<table class="odds-table"><thead><tr><th>Side</th><th>Team</th><th>Odds</th><th>Form %</th><th>Implied %</th><th>Edge</th></tr></thead><tbody>'
    +vbs.map(v=>{
      const cls=v.edge>=15?'vb-high':v.edge>=10?'vb-mid':'vb-low';
      return '<tr><td class="vb-tag '+cls+'" style="display:inline-block">'+(v.side==='home'?'Home':'Away')+'</td><td>'+v.team+'</td><td style="font-weight:600">'+v.odds+'</td><td>'+v.form_prob+'%</td><td>'+v.implied_prob+'%</td><td style="font-weight:700;color:var(--green)">+'+v.edge+'%</td></tr>';
    }).join('')
    +'</tbody></table>';
}

function toggleFilter(key){
  if(activeFilters.has(key)) activeFilters.delete(key);
  else activeFilters.add(key);
  if(selectedIdx>=0 && !matchPassesFilters(DATA.matches[selectedIdx])) selectedIdx=-1;
  render();
}
function clearFilters(){activeFilters.clear();render();}
function toggleMatch(i){
  selectedIdx = selectedIdx===i ? -1 : i;
  render();
}

function render(){
  const app=document.getElementById('app');
  let html='<div class="container">';
  html+='<div class="page-header"><h1>Big 5 — Match Form Dashboard</h1><div class="meta">'+DATA.matches.length+' matches · '+DATA.generated_at+'</div></div>';
  html+=renderFilters();
  html+=renderTable();
  html+='<div class="footer">Weights: Results 25% · xG 20% · Availability 20% · Formation 10% · Market 15% · Tipsters 10% · Form: L=League F=Friendly S=Last Season (friendlies used when <'+LEAGUE_MATCH_THRESHOLD+' league matches) · Click row to expand</div>';
  html+='</div>';
  app.innerHTML=html;
}
render();
</script>
</body>
</html>"""


def _data_to_json(data):
    json_str = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False, default=str)
    return json_str.replace("NaN", "null").replace("Infinity", "null")


def generate_html(data):
    html = HTML_TEMPLATE.replace("__JSON__", _data_to_json(data))
    html = html.replace("__ROLLING_WINDOW__", str(data.get("rolling_window", 6)))
    html = html.replace("__LEAGUE_MATCH_THRESHOLD__", str(data.get("league_match_threshold", 5)))
    return html


def write_data_json(data):
    """Write the match data the React app (web/) consumes at runtime."""
    DATA_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_JSON_PATH.write_text(_data_to_json(data), encoding="utf-8")
    print(f"  data.json -> {DATA_JSON_PATH}")


# ── Main ─────────────────────────────────────────────────────────────────────

def build_page():
    print("=" * 60)
    print("  BUILD PAGE — Match Form Dashboard")
    print("=" * 60)

    print("\nLoading data...")
    xg_df = load_understat()
    abs_df = load_absences()
    form_df = load_formations()
    odds_df = load_odds()
    tips_df = load_tips()
    friendlies_df = load_friendlies()
    prev_season_df = load_prev_season()
    goal_timing_df = load_goal_timing()

    if xg_df is None and odds_df is None:
        print("\nERROR: No understat or odds data found. Run a scraper first.")
        empty = {"matches": [], "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        OUTPUT_PATH.write_text(generate_html(empty), encoding="utf-8")
        write_data_json(empty)
        print(f"Placeholder written to {OUTPUT_PATH}")
        return

    print("\nFinding upcoming matches...")
    understat_matches = find_all_upcoming_matches(xg_df) if xg_df is not None else []
    odds_matches = find_matches_from_odds(odds_df) if odds_df is not None else []
    upcoming = merge_match_sources(understat_matches, odds_matches)

    if not upcoming:
        print("No upcoming matches found.")
        empty = {"matches": [], "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        OUTPUT_PATH.write_text(generate_html(empty), encoding="utf-8")
        write_data_json(empty)
        return

    us_count = sum(1 for m in upcoming if m.get("_source") != "odds")
    od_count = sum(1 for m in upcoming if m.get("_source") == "odds")
    print(f"  Found {len(upcoming)} upcoming matches ({us_count} from understat, {od_count} from odds)")

    # Clear team cache to pick up new data
    _team_cache.clear()

    print("\nComputing metrics for each match...")
    matches_data = []
    for i, m in enumerate(upcoming):
        md = build_match_data(xg_df, abs_df, form_df, odds_df, tips_df, m,
                              friendlies_df, prev_season_df, goal_timing_df)
        matches_data.append(md)
        print(f"  [{i+1}/{len(upcoming)}] {md['league']}: {md['home_team']} vs {md['away_team']} — {md['home']['score']:.0f} vs {md['away']['score']:.0f}")

    data = {
        "matches": matches_data,
        "weights": WEIGHTS,
        "rolling_window": ROLLING_WINDOW,
        "league_match_threshold": LEAGUE_MATCH_THRESHOLD,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print("\nGenerating output...")
    OUTPUT_PATH.write_text(generate_html(data), encoding="utf-8")
    write_data_json(data)
    print(f"\nDone! -> {OUTPUT_PATH}")
    print(f"  {len(matches_data)} matches embedded")


if __name__ == "__main__":
    build_page()
