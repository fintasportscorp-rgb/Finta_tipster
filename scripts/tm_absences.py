#!/usr/bin/env python3
"""
tm_absences.py — Transfermarkt ausfallzeiten scraper (Big 5 leagues)

Scrapes per-matchweek absence/presence data from transfermarkt.fr.

Test mode  : parses local mnm.html (or fetches one team live) so you can
             verify parsing before running the full scrape.
Full mode  : scrapes all Big 5 leagues → data/tm_absences_YYYYMMDD_HHMM.csv

Output columns:
  League, Team, Player, Position, Matchweek, Match_status,
  Absence_type, Absence_detail, Matches_Missed, From_MW, To_date

Match_status values:
  Starting lineup | Sub in | Bench | Not called up |
  Injured | Suspended | Not included (<detail>) | No match

Absence_type values (blank when playing):
  Injury description | Suspension reason | empty for transfers/youth
"""

import os
import re
import sys
import time
import random
from datetime import datetime

import urllib.parse
import requests
import urllib3
import cloudscraper
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd

# ── Windows console fix ──────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Test settings ────────────────────────────────────────────────────────────
TEST_MODE = False         # True = single team; False = all Big 5
TEST_HTML = os.path.join(os.path.dirname(__file__), "mnm.html")   # local file
TEST_TEAM = "Chelsea FC"
TEST_LEAGUE = "Premier League"
TEST_URL  = "https://www.transfermarkt.com/fc-chelsea/ausfallzeiten/verein/631"
# True = fetch live data for the test team; False = parse TEST_HTML only
TEST_LIVE_FETCH = True

# ── Resume / completion mode ─────────────────────────────────────────────────
# Set RESUME_MODE = True to only scrape teams missing from an existing CSV.
# RESUME_CSV: path to the existing CSV to complete. Leave empty to auto-detect
# the most recent tm_absences_*.csv in the data/ folder.
# The result is APPENDED to the existing CSV (new timestamp file).
RESUME_MODE = False
RESUME_CSV  = ""   # e.g. r"C:\...\data\tm_absences_20260512_1717.csv"
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://www.transfermarkt.com"

LEAGUES = {
    "Ligue 1":        "https://www.transfermarkt.com/ligue-1/startseite/wettbewerb/FR1",
    "Premier League": "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1",
    "La Liga":        "https://www.transfermarkt.com/laliga/startseite/wettbewerb/ES1",
    "Serie A":        "https://www.transfermarkt.com/serie-a/startseite/wettbewerb/IT1",
    "Bundesliga":     "https://www.transfermarkt.com/bundesliga/startseite/wettbewerb/L1",
}

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer":         "https://www.transfermarkt.com/",
    "Connection":      "keep-alive",
}

# ausfallzeiten_<suffix> → human-readable match status
_STATUS_MAP: dict[str, str] = {
    "s":         "Starting lineup",
    "k":         "Bench",
    "e":         "Sub in",
    "r":         "Not called up",
    "v":         "Injured",
    "a":         "Suspended",
    "bg_rot_20": "Not included",   # overridden to 'Played for <club>' / 'Youth team' at parse time
    "":          "No match",
}

# Suffixes that indicate absence (used for Matches_Missed / From_MW blocks)
_ABSENCE_SUFFIXES = {"v", "a", "bg_rot_20"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_suffix(td_classes: list[str]) -> str:
    """Extract the single-char (or longer) suffix from ausfallzeiten_* class."""
    for cls in td_classes:
        if cls.startswith("ausfallzeiten_") and cls != "ausfallzeiten_pos":
            return cls[len("ausfallzeiten_"):]
    return ""


def _parse_injury_title(title: str) -> tuple[str, str]:
    """
    EN: 'Muscle injury - Return expected on 06/01/2026' → ('Muscle injury', '06/01/2026')
    EN: 'Head injury - Return unknown'                  → ('Head injury', 'Unknown')
    FR: 'Blessure musculaire - Retour espéré le 6 janv. 2026' → (injury, date)
    FR: 'Blessure à la tête - Date de retour inconnue'        → (injury, 'Unknown')
    """
    if not title:
        return "", ""
    for sep in (" - Return expected on ", " - Retour espéré le "):
        if sep in title:
            parts = title.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    for unknown_marker in (" - Return unknown", " - Date de retour inconnue"):
        if unknown_marker in title:
            return title.split(unknown_marker)[0].strip(), "Unknown"
    return title.strip(), ""


def _parse_suspension_title(title: str) -> tuple[str, str]:
    """
    EN: 'Red card suspension · Premier League · until 05/10/2025'
        → ('Red card suspension', '05/10/2025')
    FR: 'Suspension pour carton rouge · Premier League · Jusqu'à 5 oct. 2025'
        → ('Suspension pour carton rouge', '5 oct. 2025')
    No end date: 'Suspension · cross-competition'
        → ('Suspension', '')
    """
    if not title:
        return "", ""
    parts = [p.strip() for p in re.split(r"[·•]", title)]
    description = parts[0] if parts else title
    to_date = ""
    for part in parts:
        low = part.lower()
        # English: "until DD/MM/YYYY"
        if low.startswith("until "):
            to_date = part[len("until "):].strip()
        # French: "Jusqu'à DATE"
        elif "jusqu'" in low:
            to_date = re.sub(r"jusqu'[àa]\s*", "", part, flags=re.IGNORECASE).strip()
    return description.strip(), to_date


def _not_included_detail(td: BeautifulSoup) -> tuple[str, str]:
    """
    Return (kind, label) for a bg_rot_20 cell.

    kind   = "away_club" | "youth_team"
    label  = club name (e.g. 'Bolton Wanderers') or team code (e.g. 'U21', 'Jgd')

    How to tell them apart:
      - href="/spielbericht/..."           → youth/reserve match report  → youth_team
      - href="/.../startseite/verein/..."  → club or national-team page  → away_club
    """
    inner_span = td.find("span", id=True) or td.find("span")
    if not inner_span:
        return "youth_team", ""
    a_tag = inner_span.find("a")
    if not a_tag:
        return "youth_team", inner_span.get_text(strip=True)
    href = a_tag.get("href", "")
    if "/spielbericht/" in href:
        # Youth/reserve appearance — text is "U21", "U18", "Jgd", etc.
        return "youth_team", a_tag.get_text(strip=True)
    else:
        # Away or affiliated club — title attr holds the club name
        label = a_tag.get("title", "").strip() or a_tag.get_text(strip=True)
        return "away_club", label


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_ausfallzeiten(html: str, league: str, team: str) -> pd.DataFrame:
    """Parse a transfermarkt ausfallzeiten HTML page into a DataFrame."""
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="ausfallzeiten-table")
    if not table:
        print(f"  WARNING: no ausfallzeiten-table found for {team}")
        return pd.DataFrame()

    all_rows = table.find_all("tr")
    if len(all_rows) < 2:
        return pd.DataFrame()

    # Header: th[0] spans 3 cols (player info), th[1..N] = matchweek numbers
    header_ths = all_rows[0].find_all("th")
    matchweeks: list[str] = [th.get_text(strip=True) for th in header_ths[1:]]

    all_records: list[dict] = []

    for row in all_rows[1:]:
        tds = row.find_all("td")
        if len(tds) < 4:
            continue

        # td[0] = position colour bar (skip)
        # td[1] = player name link
        # td[2] = position abbreviation
        name_td = tds[1]
        a_tag = name_td.find("a")
        player_name = a_tag.text.strip() if a_tag else name_td.get_text(strip=True)

        position = tds[2].get_text(strip=True)

        # Visible matchweek cells: indices 4, 6, 8, ...  (hidden ones at 3, 5, 7, ...)
        visible_cell_indices = list(range(4, len(tds), 2))

        # --- Build raw records for this player ---
        raw: list[dict] = []

        for mw_idx, td_idx in enumerate(visible_cell_indices):
            if mw_idx >= len(matchweeks):
                break
            td = tds[td_idx]
            td_classes = td.get("class") or []

            suffix = _get_suffix(td_classes)
            match_status = _STATUS_MAP.get(suffix, f"Unknown ({suffix})")

            absence_type = ""
            absence_detail  = ""
            to_date      = ""

            if suffix == "v":
                absence_type = "Injury"
                verletzt_span = td.find("span", class_="verletzt-table")
                if verletzt_span:
                    absence_detail, to_date = _parse_injury_title(
                        verletzt_span.get("title", "")
                    )

            elif suffix == "a":
                svg_span = td.find("span", class_="svg-icon")
                raw_title = svg_span.get("title", "") if svg_span else ""
                low_title = raw_title.lower()
                if "non-" in low_title or "not eligible" in low_title or "ineligible" in low_title:
                    absence_type = "Non-eligible"
                elif "suspension" in low_title:
                    absence_type = "Suspended"
                else:
                    absence_type = "Absent"
                absence_detail, to_date = _parse_suspension_title(raw_title)

            elif suffix == "bg_rot_20":
                kind, detail = _not_included_detail(td)
                if kind == "away_club":
                    match_status = f"Played for {detail}" if detail else "Played for away club"
                    absence_type = f"Played for {detail}" if detail else "Away club"
                    absence_detail  = ""
                else:
                    match_status = "Youth team"
                    absence_type = f"Youth team ({detail})" if detail else "Youth team"
                    absence_detail  = ""

            raw.append({
                "League":        league,
                "Team":          team,
                "Player":        player_name,
                "Position":      position,
                "Matchweek":     matchweeks[mw_idx],
                "Match_status":  match_status,
                "Absence_type":  absence_type,
                "Absence_detail":        absence_detail,
                "Matches_Missed": "",
                "From_MW":       "",
                "To_date":       to_date,
                "_is_absent":    suffix in _ABSENCE_SUFFIXES,
            })

        # --- Post-process: fill Matches_Missed and From_MW for absence blocks ---
        n = len(raw)
        i = 0
        while i < n:
            if raw[i]["_is_absent"]:
                j = i
                while j < n and raw[j]["_is_absent"]:
                    j += 1
                block_size = j - i
                from_mw = raw[i]["Matchweek"]
                for k in range(i, j):
                    raw[k]["Matches_Missed"] = block_size
                    raw[k]["From_MW"]        = from_mw
                i = j
            else:
                i += 1

        for r in raw:
            del r["_is_absent"]

        all_records.extend(raw)

    df = pd.DataFrame(all_records)
    absent_count = (df["Absence_type"] != "").sum()
    print(f"  -> {len(df)} rows ({absent_count} absence rows) for {team}")
    return df


# ── Network ──────────────────────────────────────────────────────────────────

def _make_session() -> cloudscraper.CloudScraper:
    s = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    s.headers.update(REQUEST_HEADERS)
    return s


# When SCRAPINGANT_KEY is set (CI), route Transfermarkt through ScrapingAnt's unlocker
# API (datacenter+no-browser = 1 credit/request, which cracks TM's Cloudflare). Locally,
# with no key, we go direct via the cloudscraper session (residential home IP, free).
_SCRAPINGANT_KEY = os.getenv("SCRAPINGANT_KEY")

# ScrapingAnt returns HTTP 200 even on soft-blocks (a tiny Cloudflare interstitial),
# so we escalate the proxy strength per attempt and treat a small body as a block.
# Real Transfermarkt pages are ~500KB+; interstitials are a few KB.
_SA_MODES = [
    "browser=false&proxy_type=datacenter",   # ~1 credit  (works ~60% of the time)
    "browser=false&proxy_type=residential",  # ~25 credits (retry on block)
    "browser=true&proxy_type=residential",   # ~125 credits (last resort)
]
_SA_MIN_BYTES = 50_000


def fetch_html(session: requests.Session, url: str, retries: int = 3) -> str | None:
    for attempt in range(1, retries + 1):
        try:
            if _SCRAPINGANT_KEY:
                mode = _SA_MODES[min(attempt - 1, len(_SA_MODES) - 1)]
                api = (
                    "https://api.scrapingant.com/v2/general?url="
                    + urllib.parse.quote(url, safe="")
                    + f"&x-api-key={_SCRAPINGANT_KEY}&{mode}"
                )
                resp = requests.get(api, timeout=120)
                if resp.status_code == 200 and len(resp.text) >= _SA_MIN_BYTES:
                    return resp.text
                print(
                    f"  ScrapingAnt HTTP {resp.status_code}, {len(resp.text)}B "
                    f"for {url} (attempt {attempt} — escalating)"
                )
            else:
                resp = session.get(url, timeout=30)
                if resp.status_code == 200:
                    return resp.text
                print(f"  HTTP {resp.status_code} for {url} (attempt {attempt})")
        except Exception as exc:
            print(f"  Error fetching {url}: {exc} (attempt {attempt})")
        if attempt < retries:
            time.sleep(random.uniform(3, 6))
    return None


def get_teams_from_league(
    session: requests.Session,
    league_name: str,
    league_url: str,
) -> dict[str, str]:
    """Return {team_display_name: absences_url}."""
    print(f"Getting teams from {league_name} ...")
    html = fetch_html(session, league_url)
    if not html:
        print(f"  ERROR: could not fetch league page for {league_name}")
        return {}

    soup = BeautifulSoup(html, "html.parser")

    # xpath: //*[@id="wettbewerbsstartseite"]/div[1]/div[2]
    container = soup.select_one("#wettbewerbsstartseite > div:first-child > div:nth-child(2)")
    if not container:
        container = soup   # broad fallback

    pattern = re.compile(r"^/([^/]+)/startseite/verein/(\d+)")
    teams: dict[str, str] = {}

    for a_tag in container.find_all("a", href=True):
        m = pattern.match(a_tag["href"])
        if not m:
            continue
        slug, verein_id = m.group(1), m.group(2)
        name = a_tag.get("title", "").strip() or a_tag.get_text(strip=True)
        if len(name) < 2:
            continue
        url = f"{BASE_URL}/{slug}/ausfallzeiten/verein/{verein_id}"
        if name not in teams:
            teams[name] = url

    print(f"  -> {len(teams)} teams found")
    return teams


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    session = _make_session()
    all_dfs: list[pd.DataFrame] = []

    if TEST_MODE:
        if TEST_LIVE_FETCH:
            print(f"[TEST MODE – LIVE] Fetching {TEST_URL}")
            html = fetch_html(session, TEST_URL)
        else:
            print(f"[TEST MODE – LOCAL] Parsing {TEST_HTML}")
            with open(TEST_HTML, "r", encoding="utf-8", errors="replace") as fh:
                html = fh.read()

        if html:
            df = parse_ausfallzeiten(html, TEST_LEAGUE, TEST_TEAM)
            if not df.empty:
                all_dfs.append(df)

    elif RESUME_MODE:
        # ── Resume / completion mode ──────────────────────────────────────────
        # Load the existing CSV and figure out which teams are already present.
        csv_path = RESUME_CSV
        if not csv_path:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            candidates = sorted(
                (f for f in os.listdir(data_dir) if f.startswith("tm_absences_") and f.endswith(".csv")),
                reverse=True,
            )
            if not candidates:
                print("ERROR: no existing tm_absences_*.csv found in data/. Set RESUME_CSV.")
                sys.exit(1)
            csv_path = os.path.join(data_dir, candidates[0])

        print(f"[RESUME MODE] Loading existing data from:\n  {csv_path}")
        existing_df = pd.read_csv(csv_path)
        all_dfs.append(existing_df)

        # Build set of already-scraped teams per league
        already_done: dict[str, set[str]] = {}
        for league_name in existing_df["League"].unique():
            already_done[league_name] = set(
                existing_df.loc[existing_df["League"] == league_name, "Team"].unique()
            )

        print("Already scraped:")
        for lg, tms in already_done.items():
            print(f"  {lg}: {len(tms)} teams")

        n_leagues  = len(LEAGUES)
        total_rows = len(existing_df)
        teams_done = 0
        start_time = time.time()

        for league_idx, (league_name, league_url) in enumerate(LEAGUES.items(), 1):
            done_set = already_done.get(league_name, set())
            print(f"\n[{league_idx}/{n_leagues}] {league_name}")
            all_teams = get_teams_from_league(session, league_name, league_url)
            if not all_teams:
                continue

            # Filter to only teams not yet in the CSV
            missing_teams = {k: v for k, v in all_teams.items() if k not in done_set}
            if not missing_teams:
                print(f"  All teams already present — skipping.")
                continue

            print(f"  Missing teams ({len(missing_teams)}): {', '.join(missing_teams)}")
            n_teams = len(missing_teams)

            for i, (team_name, team_url) in enumerate(missing_teams.items(), 1):
                elapsed = time.time() - start_time
                teams_done_now = teams_done + i
                eta_str = ""
                if teams_done_now > 1:
                    avg_sec = elapsed / (teams_done_now - 1)
                    remaining = (n_teams - i) + sum(
                        3 for _ in range(n_leagues - league_idx)
                    )
                    eta_sec = avg_sec * remaining
                    eta_str = f"  ETA ~{int(eta_sec//60)}m{int(eta_sec%60):02d}s"

                print(f"  [{i:2d}/{n_teams}] {team_name}{eta_str}", flush=True)

                html = fetch_html(session, team_url)
                if html:
                    df = parse_ausfallzeiten(html, league_name, team_name)
                    if not df.empty:
                        all_dfs.append(df)
                        total_rows += len(df)

                print(f"         Total rows so far: {total_rows}", flush=True)
                time.sleep(random.uniform(5, 10))

            teams_done += n_teams
            print(f"  ✓ {league_name} completion done ({n_teams} new teams)")

    else:
        n_leagues     = len(LEAGUES)
        total_rows    = 0
        teams_done    = 0
        start_time    = time.time()

        for league_idx, (league_name, league_url) in enumerate(LEAGUES.items(), 1):
            print(f"\n[{league_idx}/{n_leagues}] {league_name}")
            teams = get_teams_from_league(session, league_name, league_url)
            if not teams:
                continue
            n_teams = len(teams)

            for i, (team_name, team_url) in enumerate(teams.items(), 1):
                elapsed   = time.time() - start_time
                teams_done_now = teams_done + i
                eta_str   = ""
                if teams_done_now > 1:
                    avg_sec = elapsed / (teams_done_now - 1)
                    remaining = (sum(len(t) for t in [teams]) - i) + sum(
                        20 for _ in range(n_leagues - league_idx)   # ~20 teams per unseen league
                    )
                    eta_sec = avg_sec * remaining
                    eta_str = f"  ETA ~{int(eta_sec//60)}m{int(eta_sec%60):02d}s"

                print(f"  [{i:2d}/{n_teams}] {team_name}{eta_str}", flush=True)

                html = fetch_html(session, team_url)
                if html:
                    df = parse_ausfallzeiten(html, league_name, team_name)
                    if not df.empty:
                        all_dfs.append(df)
                        total_rows += len(df)

                print(f"         Total rows so far: {total_rows}", flush=True)
                time.sleep(random.uniform(5, 10))

            teams_done += n_teams
            print(f"  ✓ {league_name} done ({n_teams} teams)")

    if not all_dfs:
        print("No data collected.")
        sys.exit(0)

    final_df = pd.concat(all_dfs, ignore_index=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if TEST_MODE:
        out_path = os.path.join(script_dir, f"test_tm_absences_{timestamp}.csv")
        final_df.to_csv(out_path, index=False)
        print(f"\nTest CSV saved: {out_path}")
        print(f"Total rows: {len(final_df)}")

        # Summary: show absence rows only
        absence_df = final_df[final_df["Absence_type"] != ""].copy()
        print(f"\nAbsence rows ({len(absence_df)}):")
        cols = ["Player", "Position", "Matchweek", "Match_status",
                "Absence_type", "Absence_detail", "Matches_Missed", "From_MW", "To_date"]
        print(absence_df[cols].to_string(index=False))
    else:
        data_dir = os.path.join(os.path.dirname(script_dir), "data")  # project root/data
        os.makedirs(data_dir, exist_ok=True)
        out_path = os.path.join(data_dir, f"tm_absences_{timestamp}.csv")
        final_df.to_csv(out_path, index=False)
        print(f"\nDone! {len(final_df)} total rows → {out_path}")
        absent_count = (final_df["Absence_type"] != "").sum()
        print(f"Absence rows: {absent_count}")
        print(final_df["Team"].value_counts().head(10))
