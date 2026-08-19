#!/usr/bin/env python3
"""
friendly_scraper.py — Scrape friendly/pre-season matches for Big 5 teams from Sofascore.

Uses the same Selenium approach as get_odds.py to bypass Sofascore's 403 on requests.

For each Big 5 team:
  1. Search Sofascore for the team ID
  2. Fetch the team's last matches
  3. Filter for friendlies (uniqueTournament.name contains "Friendlies" or "Club Friend")
  4. Extract: datetime, home_team, away_team, home_goals, away_goals

Output: understat_data/friendlies_YYYYMMDD_HHMM.csv
Columns match understat format: league, datetime, home_team, away_team,
  home_goals, away_goals, home_xG (null), away_xG (null), gameweek (null),
  match_id, forecast_* (null)
"""

import sys
import os
import json
import time
import platform
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.parent  # project root (scripts live in scripts/)
OUTPUT_DIR = SCRIPT_DIR / "understat_data"
OUTPUT_DIR.mkdir(exist_ok=True)

API_BASE = "https://www.sofascore.com/api/v1"

# Only keep friendlies from preseason (June, July, August of current year)
PRESEASON_MONTHS = {6, 7, 8}
CURRENT_YEAR = datetime.now().year

# Big 5 leagues and their team name sources
LEAGUES = {
    "Premier League": (17, 96668),
    "La Liga":        (8,  97268),
    "Bundesliga":     (35, 97464),
    "Serie A":        (23, 95836),
    "Ligue 1":        (34, 96127),
}

# Team name normalization for matching Sofascore → Understat
# (Sofascore uses different names than Understat)
SOFASCORE_TO_UNDERSTAT = {
    "Tottenham Hotspur": "Tottenham", "Aston Villa": "Aston Villa",
    "Manchester City": "Manchester City", "Manchester United": "Manchester United",
    "Newcastle United": "Newcastle United", "Brighton & Hove Albion": "Brighton",
    "Nottingham Forest": "Nottingham Forest", "Crystal Palace": "Crystal Palace",
    "Liverpool FC": "Liverpool", "West Ham United": "West Ham",
    "Ipswich Town": "Ipswich", "Leeds United": "Leeds",
    "Sunderland": "Sunderland", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Everton": "Everton",
    "Fulham": "Fulham", "Arsenal": "Arsenal", "Chelsea": "Chelsea",
    "Burnley": "Burnley", "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Leicester City": "Leicester", "Southampton": "Southampton",
    "Coventry City": "Coventry", "Hull City": "Hull",
    "Atletico Madrid": "Atletico Madrid", "Athletic Club": "Athletic Club",
    "FC Barcelona": "Barcelona", "Real Madrid": "Real Madrid",
    "Real Betis": "Real Betis", "Real Sociedad": "Real Sociedad",
    "Villarreal": "Villarreal", "Sevilla": "Sevilla",
    "Valencia": "Valencia", "Celta Vigo": "Celta Vigo",
    "Getafe": "Getafe", "Girona": "Girona", "Osasuna": "Osasuna",
    "Mallorca": "Mallorca", "Espanyol": "Espanyol",
    "Rayo Vallecano": "Rayo Vallecano", "Deportivo Alaves": "Alaves",
    "Levante": "Levante", "Elche": "Elche",
    "Racing Santander": "Racing Santander", "Deportivo La Coruna": "Deportivo La Coruna",
    "Malaga": "Malaga",
    "Inter": "Inter", "Juventus": "Juventus", "Napoli": "Napoli",
    "AC Milan": "AC Milan", "Roma": "Roma", "Lazio": "Lazio",
    "Atalanta": "Atalanta", "Fiorentina": "Fiorentina",
    "Bologna": "Bologna", "Torino": "Torino", "Udinese": "Udinese",
    "Genoa": "Genoa", "Cagliari": "Cagliari", "Como": "Como",
    "Parma": "Parma", "Monza": "Monza", "Lecce": "Lecce",
    "Verona": "Verona", "Sassuolo": "Sassuolo",
    "Frosinone": "Frosinone", "Venezia": "Venezia",
    "Cremonese": "Cremonese", "Pisa": "Pisa",
    "Paris Saint-Germain": "Paris Saint Germain", "AS Monaco": "Monaco",
    "Olympique de Marseille": "Marseille", "Olympique Lyonnais": "Lyon",
    "LOSC Lille": "Lille", "RC Lens": "Lens", "OGC Nice": "Nice",
    "RC Strasbourg": "Strasbourg", "Stade Rennais": "Rennes",
    "Stade Brestois": "Brest", "FC Nantes": "Nantes",
    "FC Toulouse": "Toulouse", "AJ Auxerre": "Auxerre",
    "Angers": "Angers", "FC Lorient": "Lorient",
    "Le Havre": "Le Havre", "Paris FC": "Paris FC",
    "Troyes": "Troyes", "Le Mans": "Le Mans",
    "Bayer 04 Leverkusen": "Bayer Leverkusen",
    "Borussia Dortmund": "Borussia Dortmund",
    "Bayern Munich": "Bayern Munich",
    "RB Leipzig": "RasenBallsport Leipzig",
    "SC Freiburg": "Freiburg", "FC Augsburg": "Augsburg",
    "VfL Wolfsburg": "Wolfsburg", "SV Werder Bremen": "Werder Bremen",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "1.FC Union Berlin": "Union Berlin", "1.FSV Mainz 05": "Mainz 05",
    "Borussia M.Gladbach": "Borussia M.Gladbach",
    "FC St. Pauli": "St. Pauli", "Holstein Kiel": "Holstein Kiel",
    "1.FC Heidenheim 1846": "FC Heidenheim", "1.FC Koln": "FC Cologne",
}


def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    if platform.system() == "Linux":
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
    elif platform.system() == "Windows":
        chrome_options.add_argument('--disable-extensions')
    return webdriver.Chrome(options=chrome_options)


def fetch_json(driver, url, timeout=15):
    """Fetch JSON from a Sofascore API URL using Selenium."""
    driver.get(url)
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.TAG_NAME, "pre"))
        )
        return json.loads(el.text)
    except (TimeoutException, json.JSONDecodeError):
        return None


def get_team_ids_from_league(driver, tournament_id, season_id):
    """Get team IDs from a league's season teams endpoint."""
    url = f"{API_BASE}/unique-tournament/{tournament_id}/season/{season_id}/standings/total"
    data = fetch_json(driver, url)
    if not data:
        return {}

    teams = {}
    # Sofascore standings: data["standings"] is a list of table objects,
    # each with a "rows" field containing team rows
    standings = data.get("standings", [])
    rows = []
    for table in standings:
        rows.extend(table.get("rows", []))
    # Fallback: some responses have rows at top level
    if not rows:
        rows = data.get("rows", [])

    for row in rows:
        team = row.get("team", {})
        tid = team.get("id")
        name = team.get("name", "")
        if tid and name:
            teams[name] = tid
    return teams


def search_team(driver, team_name):
    """Search for a team by name and return their Sofascore ID."""
    url = f"{API_BASE}/search?text={team_name}"
    data = fetch_json(driver, url, timeout=10)
    if not data:
        return None
    for item in data.get("teams", []):
        sport = item.get("sport", {})
        if sport.get("name") == "Football" or sport.get("id") == 1:
            return item.get("id")
    return None


def fetch_team_last_events(driver, team_id, n=30):
    """Fetch the last N events for a team (across multiple pages if needed)."""
    all_events = []
    page = 0
    while len(all_events) < n:
        url = f"{API_BASE}/team/{team_id}/events/last/{page}"
        data = fetch_json(driver, url)
        if not data:
            break
        events = data.get("events", [])
        if not events:
            break
        all_events.extend(events)
        if not data.get("hasNextPage"):
            break
        page += 1
        time.sleep(0.3)
    return all_events[:n]


def is_friendly(event):
    """Check if an event is a friendly match."""
    tour = event.get("tournament", {})
    ut = tour.get("uniqueTournament", {})
    ut_name = (ut.get("name") or "").lower()
    t_name = (tour.get("name") or "").lower()
    return "friend" in ut_name or "friend" in t_name


def parse_event(event):
    """Parse a Sofascore event into a row dict matching understat format."""
    ts = event.get("startTimestamp", 0)
    dt = datetime.fromtimestamp(ts) if ts else None

    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    home_name = home.get("name", "")
    away_name = away.get("name", "")

    # Map to Understat names
    home_us = SOFASCORE_TO_UNDERSTAT.get(home_name, home_name)
    away_us = SOFASCORE_TO_UNDERSTAT.get(away_name, away_name)

    hs = event.get("homeScore", {})
    as_ = event.get("awayScore", {})
    home_goals = hs.get("current") if hs.get("current") is not None else hs.get("display")
    away_goals = as_.get("current") if as_.get("current") is not None else as_.get("display")

    # Only include if match has been played (has a final score)
    if home_goals is None or away_goals is None:
        return None

    # Only keep friendlies from preseason (June-August of current year)
    if dt and (dt.month not in PRESEASON_MONTHS or dt.year != CURRENT_YEAR):
        return None

    return {
        "league": "Friendlies",
        "match_id": event.get("id"),
        "datetime": dt.strftime("%Y-%m-%d %H:%M") if dt else "",
        "gameweek": None,
        "home_team": home_us,
        "away_team": away_us,
        "home_goals": float(home_goals),
        "away_goals": float(away_goals),
        "home_xG": None,
        "away_xG": None,
        "forecast_home_win": None,
        "forecast_draw": None,
        "forecast_away_win": None,
    }


def main():
    print("=" * 60)
    print("  FRIENDLY MATCH SCRAPER — Big 5 Teams")
    print("=" * 60)

    driver = setup_webdriver()
    all_rows = []
    seen_match_ids = set()

    try:
        # Phase 1: Get team IDs from league standings
        print("\nPhase 1: Getting team IDs from league standings...")
        all_teams = {}  # {team_name: (team_id, league)}

        for league_name, (tid, sid) in LEAGUES.items():
            print(f"  {league_name}...")
            teams = get_team_ids_from_league(driver, tid, sid)
            if not teams:
                # Fallback: try category-based search
                print(f"    Standings failed, trying team search...")
                # We'll search by known team names later
                continue
            for name, team_id in teams.items():
                all_teams[name] = (team_id, league_name)
            print(f"    -> {len(teams)} teams found")
            time.sleep(0.5)

        print(f"\n  Total teams: {len(all_teams)}")

        # Phase 2: Fetch last events for each team and filter friendlies
        print("\nPhase 2: Fetching last events for each team...")
        for i, (team_name, (team_id, league)) in enumerate(all_teams.items(), 1):
            print(f"  [{i}/{len(all_teams)}] {team_name} ({league})...", end="", flush=True)
            events = fetch_team_last_events(driver, team_id, n=50)
            friendlies = [e for e in events if is_friendly(e)]
            print(f" {len(friendlies)} friendlies")

            for ev in friendlies:
                row = parse_event(ev)
                if not row:
                    continue
                mid = row["match_id"]
                if mid in seen_match_ids:
                    continue
                seen_match_ids.add(mid)
                row["league"] = league  # Use the team's league, not "Friendlies"
                all_rows.append(row)
                time.sleep(0.3)

            time.sleep(0.5)

    finally:
        driver.quit()

    if not all_rows:
        print("\nNo friendly matches found.")
        return

    # Phase 3: Save
    df = pd.DataFrame(all_rows)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime", ascending=False).reset_index(drop=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = OUTPUT_DIR / f"friendlies_{timestamp}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"\nDone! {len(df)} friendly matches -> {out_path}")
    print(f"Teams with friendlies: {df['home_team'].nunique() + df['away_team'].nunique()}")
    print(f"Date range: {df['datetime'].min()} -> {df['datetime'].max()}")
    print("\nSample:")
    print(df[["datetime", "home_team", "away_team", "home_goals", "away_goals"]].head(10).to_string())


if __name__ == "__main__":
    main()
