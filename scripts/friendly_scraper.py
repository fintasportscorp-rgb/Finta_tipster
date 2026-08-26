"""
friendly_scraper.py - pre-season club friendlies for Big-5 teams via ESPN's free
public API (site.api.espn.com, no key, not bot-blocked, works from cloud + local).

Replaces the old Sofascore/Selenium scraper (Sofascore blocks datacenter IPs).

Output: understat_data/friendlies_YYYYMMDD_HHMM.csv with the understat schema
build_page expects: league, datetime, home_team, away_team, home_goals,
away_goals, home_xG (null), away_xG (null), gameweek (null).

build_page matches friendly rows to teams by EXACT name equality against the
understat team names, so ESPN display names are mapped back to those exact names.
"""

import os
import re
import glob
import time
import json
import unicodedata
from datetime import datetime, date
import pandas as pd
from curl_cffi import requests as cffi_requests  # impersonates Chrome TLS (ESPN WAF)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Data dirs live at the project root (scripts/'s parent), same as understat.py/build_page.
UNDERSTAT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "understat_data")
os.makedirs(UNDERSTAT_DIR, exist_ok=True)

ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/club.friendly/scoreboard"

# ESPN display name -> exact understat name, for cases the generic normalizer misses.
ALIASES = {
    "Internazionale": "Inter",
    "Inter Milan": "Inter",
    "Atlético Madrid": "Atletico Madrid",
    "Atletico Madrid": "Atletico Madrid",
    "Paris Saint-Germain": "Paris Saint Germain",
    "Bayern Munich": "Bayern Munich",
    "Borussia Monchengladbach": "Borussia M.Gladbach",
    "Borussia Mönchengladbach": "Borussia M.Gladbach",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Newcastle United": "Newcastle United",
    "Real Betis": "Real Betis",
    "Real Sociedad": "Real Sociedad",
}


def normalize_name(name):
    """Mirror of build_page.normalize_name so matched names collapse the same way."""
    if not isinstance(name, str):
        return ""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    n = n.lower().strip()
    n = re.sub(r"[^\w\s]", "", n)
    n = re.sub(
        r"\b(fc|cf|ac|sc|afc|club|calcio|united|city|town|athletic|de|la|real|royal|deportivo)\b",
        "",
        n,
    )
    return re.sub(r"\s+", " ", n).strip()


def load_big5():
    """Return (exact_names set, normalized->exact map, team->league map) from understat."""
    files = sorted(glob.glob(os.path.join(UNDERSTAT_DIR, "big5_understat_2026.csv")))
    if not files:
        # fall back to any big5 understat file
        files = sorted(glob.glob(os.path.join(UNDERSTAT_DIR, "big5_understat_*.csv")))
    if not files:
        print("  WARNING: no understat team list found; cannot map friendly teams.")
        return set(), {}, {}
    df = pd.read_csv(files[-1])
    teams, team_league = set(), {}
    for _, r in df.iterrows():
        lg = r.get("league")
        for side in ("home_team", "away_team"):
            t = r.get(side)
            if isinstance(t, str) and t:
                teams.add(t)
                team_league.setdefault(t, lg)
    norm_map = {}
    for t in teams:
        norm_map.setdefault(normalize_name(t), []).append(t)
    return teams, norm_map, team_league


def make_matcher(exact, norm_map):
    def match(espn_name):
        if espn_name in exact:
            return espn_name
        if espn_name in ALIASES and ALIASES[espn_name] in exact:
            return ALIASES[espn_name]
        cands = norm_map.get(normalize_name(espn_name))
        if cands and len(cands) == 1:  # unambiguous
            return cands[0]
        return None
    return match


def fetch_day(day):
    url = f"{ESPN}?dates={day:%Y%m%d}"
    # verify=True works in CI; a local TLS-intercepting AV/proxy needs verify=False.
    for verify in (True, False):
        try:
            r = cffi_requests.get(url, impersonate="chrome", timeout=30, verify=verify)
            if r.status_code == 200:
                return r.json().get("events", []) or []
            print(f"  {day:%Y-%m-%d}: HTTP {r.status_code}")
            return []
        except Exception as exc:
            if verify and "certificate" in str(exc).lower():
                continue  # local interception -> retry without verification
            print(f"  {day:%Y-%m-%d}: {str(exc)[:80]}")
            return []
    return []


def main():
    exact, norm_map, team_league = load_big5()
    match = make_matcher(exact, norm_map)
    if not exact:
        print("No Big-5 team list; aborting friendlies.")
        return

    year = datetime.now().year
    start = date(year, 6, 1)
    end = date.today()
    print(f"Fetching club friendlies {start} -> {end} from ESPN (Big-5 teams only)...")

    rows, seen = [], set()
    d = start
    while d <= end:
        for ev in fetch_day(d):
            comp = (ev.get("competitions") or [{}])[0]
            if not comp.get("status", {}).get("type", {}).get("completed"):
                continue
            cs = comp.get("competitors", [])
            home = next((c for c in cs if c.get("homeAway") == "home"), None)
            away = next((c for c in cs if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue
            h_name = (home.get("team") or {}).get("displayName", "")
            a_name = (away.get("team") or {}).get("displayName", "")
            h_match, a_match = match(h_name), match(a_name)
            if not h_match and not a_match:
                continue  # neither side is a Big-5 team
            key = ev.get("id")
            if key in seen:
                continue
            seen.add(key)
            try:
                hg = int(home.get("score"))
                ag = int(away.get("score"))
            except (TypeError, ValueError):
                continue
            lg = team_league.get(h_match) or team_league.get(a_match) or "Friendly"
            rows.append({
                "league": lg,
                "datetime": ev.get("date"),
                "home_team": h_match or h_name,
                "away_team": a_match or a_name,
                "home_goals": hg,
                "away_goals": ag,
                "home_xG": None,
                "away_xG": None,
                "gameweek": None,
            })
        time.sleep(0.15)
        d = date.fromordinal(d.toordinal() + 1)

    if not rows:
        print("No Big-5 friendlies found in the window.")
        return
    out = pd.DataFrame(rows).drop_duplicates(subset=["datetime", "home_team", "away_team"])
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = os.path.join(UNDERSTAT_DIR, f"friendlies_{ts}.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")
    n_big5 = out[["home_team", "away_team"]].apply(lambda r: (r["home_team"] in exact) or (r["away_team"] in exact), axis=1).sum()
    print(f"Exported -> {path} ({len(out)} friendlies, {n_big5} involving a Big-5 team)")


if __name__ == "__main__":
    main()
