import sys
import io
import json
import os
import platform
import time
from fractions import Fraction
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ================= FIX: Patch datafc's broken webdriver setup =================
# ChromeDriverManager downloads wrong version - use Selenium Manager instead

def patched_setup_webdriver():
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
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ================= BIG 5 LEAGUES CONFIG =================
# Format: (tournament_id, season_id, name)
# Season IDs for 2025/26 - update these each season

LEAGUES = [
    (17, 76986, "Premier League"),
    (8,  77559, "La Liga"),
    (35, 77333, "Bundesliga"),
    (23, 76457, "Serie A"),
    (34, 77356, "Ligue 1"),
]

BIG5_TOURNAMENT_IDS = {tid for tid, _, _ in LEAGUES}
LEAGUE_NAMES = {tid: name for tid, _, name in LEAGUES}

API_BASE = "https://www.sofascore.com"

# ================= DATE HELPERS =================

def get_current_week_dates():
    """Return list of date strings (YYYY-MM-DD) for the current Mon-Sun week."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

# ================= FETCH EVENTS BY DATE =================

def fetch_events_for_date(driver, date_str):
    """Fetch all Big 5 league events for a given date (YYYY-MM-DD)."""
    results = []

    for tid, _, league_name in LEAGUES:
        url = f"{API_BASE}/api/v1/unique-tournament/{tid}/scheduled-events/{date_str}"
        driver.get(url)

        try:
            el = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.TAG_NAME, "pre"))
            )
            data = json.loads(el.text)
        except (TimeoutException, json.JSONDecodeError) as e:
            continue

        events = data.get("events", data.get("scheduledEvents", []))

        for ev in events:
            ts = ev.get("startTimestamp", 0)
            match_dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

            round_num = ev.get("roundInfo", {}).get("round", "")
            status_desc = ev.get("status", {}).get("description", "")

            results.append({
                "game_id": ev.get("id"),
                "home_team": ev.get("homeTeam", {}).get("name", ""),
                "away_team": ev.get("awayTeam", {}).get("name", ""),
                "start_timestamp": ts,
                "match_datetime": match_dt,
                "status": status_desc,
                "round": round_num,
                "tournament_id": tid,
                "league": league_name,
            })

        time.sleep(0.5)

    return results

# ================= FETCH ODDS =================

def fetch_odds_for_game(driver, game_id):
    """Fetch all odds markets for a single game_id."""
    url = f"{API_BASE}/api/v1/event/{game_id}/odds/1/all"
    driver.get(url)

    try:
        el = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.TAG_NAME, "pre"))
        )
        data = json.loads(el.text)
    except TimeoutException:
        print(f"    Warning: timeout fetching odds for game {game_id}")
        return []
    except json.JSONDecodeError:
        print(f"    Warning: invalid JSON for odds of game {game_id}")
        return []

    markets = data.get("markets", [])
    odds_rows = []

    for market in markets:
        for choice in market.get("choices", []):
            odds_rows.append({
                "game_id": game_id,
                "market_name": market.get("marketName", "Unknown"),
                "is_live": market.get("isLive", False),
                "choice_name": choice.get("name", ""),
                "initial_fractional_value": choice.get("initialFractionalValue", ""),
                "current_fractional_value": choice.get("fractionalValue", ""),
                "change": choice.get("change", 0),
            })

    return odds_rows

# ================= HELPERS =================

def frac_to_decimal(frac_str):
    """Convert fractional odds like '27/20' to decimal like 2.35"""
    try:
        f = Fraction(frac_str)
        return round(float(f) + 1, 2)
    except (ValueError, ZeroDivisionError):
        return None

# ============= THE ODDS API (free, current, always-on) =============
# Sofascore is bot-blocked from the cloud, so when THEODDS_KEY is set we pull
# 1X2 odds from The Odds API (the-odds-api.com) instead — 1 request/league,
# mapped to the exact big5_odds_*.csv schema build_page expects.

THEODDS_LEAGUES = [
    ("EPL",        "soccer_epl"),
    ("La Liga",    "soccer_spain_la_liga"),
    ("Bundesliga", "soccer_germany_bundesliga"),
    ("Serie A",    "soccer_italy_serie_a"),
    ("Ligue 1",    "soccer_france_ligue_one"),
]


def main_theodds(key):
    rows = []
    for league_name, sport in THEODDS_LEAGUES:
        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
            f"?apiKey={key}&regions=eu&markets=h2h&oddsFormat=decimal"
        )
        try:
            r = requests.get(url, timeout=40)
            if r.status_code != 200:
                print(f"  {league_name}: HTTP {r.status_code} {r.text[:120]}")
                continue
            events = r.json()
        except Exception as exc:
            print(f"  {league_name}: error {exc}")
            continue
        print(f"  {league_name}: {len(events)} matches")
        for ev in events:
            home, away = ev.get("home_team"), ev.get("away_team")
            if not home or not away:
                continue
            agg = {"Home": [], "Draw": [], "Away": []}
            for bk in ev.get("bookmakers", []):
                for mkt in bk.get("markets", []):
                    if mkt.get("key") != "h2h":
                        continue
                    for oc in mkt.get("outcomes", []):
                        nm, price = oc.get("name"), oc.get("price")
                        if price is None:
                            continue
                        if nm == home:
                            agg["Home"].append(price)
                        elif nm == away:
                            agg["Away"].append(price)
                        elif nm == "Draw":
                            agg["Draw"].append(price)
            match_name = f"{home} vs {away}"
            for choice in ("Home", "Draw", "Away"):
                vals = agg[choice]
                if not vals:
                    continue
                dec = round(sum(vals) / len(vals), 2)  # avg across bookmakers
                rows.append({
                    "league": league_name,
                    "match_date": ev.get("commence_time"),
                    "match_name": match_name,
                    "game_id": ev.get("id"),
                    "market_name": "Full Time Result",
                    "choice_name": choice,
                    "opening_odds": dec,
                    "current_odds": dec,
                    "change": 0,
                    "is_live": False,
                })
    if not rows:
        print("No odds returned from The Odds API.")
        return
    out = pd.DataFrame(rows)[[
        "league", "match_date", "match_name", "game_id", "market_name",
        "choice_name", "opening_odds", "current_odds", "change", "is_live",
    ]].sort_values(["match_date", "league", "match_name"]).reset_index(drop=True)
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "input")
    os.makedirs(input_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = os.path.join(input_dir, f"big5_odds_{timestamp}.csv")
    out.to_csv(filename, index=False, encoding="utf-8")
    print(f"\nExported -> {filename} ({len(out)} rows, {out['match_name'].nunique()} matches)")


# ================= MAIN =================

def main():
    _theodds_key = os.getenv("THEODDS_KEY")
    if _theodds_key:
        print("Fetching Big 5 odds via The Odds API (current, free)...")
        return main_theodds(_theodds_key)

    week_dates = get_current_week_dates()
    print(f"Fetching Big 5 matches for week: {week_dates[0]} to {week_dates[-1]}")
    print(f"Leagues: {', '.join(name for _, _, name in LEAGUES)}")

    driver = patched_setup_webdriver()

    try:
        # ---- Phase 1: Collect all Big 5 matches for the week ----
        all_events = []
        seen_game_ids = set()

        for date_str in week_dates:
            print(f"\n  Fetching events for {date_str}...")
            events = fetch_events_for_date(driver, date_str)

            new_count = 0
            for ev in events:
                if ev["game_id"] not in seen_game_ids:
                    seen_game_ids.add(ev["game_id"])
                    all_events.append(ev)
                    new_count += 1

            print(f"    Found {len(events)} Big 5 events, {new_count} new")
            time.sleep(1)

        if not all_events:
            print("\nNo Big 5 matches found for this week.")
            return

        print(f"\nTotal unique matches collected: {len(all_events)}")
        for league_name in dict.fromkeys(ev["league"] for ev in all_events):
            count = sum(1 for ev in all_events if ev["league"] == league_name)
            print(f"  {league_name}: {count} matches")

        # ---- Phase 2: Fetch odds for each game ----
        print(f"\nFetching odds for {len(all_events)} matches...")
        all_odds_rows = []

        for i, ev in enumerate(all_events, 1):
            print(f"  [{i}/{len(all_events)}] {ev['home_team']} vs {ev['away_team']} ({ev['league']})...")
            odds_rows = fetch_odds_for_game(driver, ev["game_id"])
            all_odds_rows.extend(odds_rows)

            if i < len(all_events):
                time.sleep(1)

        if not all_odds_rows:
            print("\nNo odds data collected.")
            return

        # ---- Phase 3: Build output DataFrame ----
        odds_df = pd.DataFrame(all_odds_rows)
        events_df = pd.DataFrame(all_events)

        match_names = events_df.set_index("game_id").apply(
            lambda r: f"{r['home_team']} vs {r['away_team']}", axis=1
        ).to_dict()
        match_dates = events_df.set_index("game_id")["match_datetime"].to_dict()
        match_leagues = events_df.set_index("game_id")["league"].to_dict()

        odds_df["match_name"] = odds_df["game_id"].map(match_names)
        odds_df["match_date"] = odds_df["game_id"].map(match_dates)
        odds_df["league"] = odds_df["game_id"].map(match_leagues)

        odds_df["opening_odds"] = odds_df["initial_fractional_value"].apply(frac_to_decimal)
        odds_df["current_odds"] = odds_df["current_fractional_value"].apply(frac_to_decimal)

        out = odds_df[[
            "league", "match_date", "match_name", "game_id", "market_name",
            "choice_name", "opening_odds", "current_odds", "change", "is_live"
        ]]

        out = out.sort_values(["match_date", "league", "match_name"]).reset_index(drop=True)

        # ---- Phase 4: Export CSV ----
        input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'input')
        os.makedirs(input_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = os.path.join(input_dir, f"big5_odds_{timestamp}.csv")
        out.to_csv(filename, index=False, encoding="utf-8")
        print(f"\nExported -> {filename} ({len(out)} rows, {odds_df['game_id'].nunique()} matches)")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
