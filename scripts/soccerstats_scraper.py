"""
soccerstats_scraper.py — Scrape goal timing data (GF/GA per 15-min segment) from SoccerStats.

Uses Selenium with anti-detection to bypass the site's headless blocking.
For each Big 5 league team, extracts goals for/against by time segment:
  0-15, 16-30, 31-45, 46-60, 61-75, 76-90

Output: understat_data/goal_timing_YYYYMMDD_HHMM.csv
"""

import sys
import os
import time
import platform
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.parent  # project root (scripts live in scripts/)
OUTPUT_DIR = SCRIPT_DIR / "understat_data"
OUTPUT_DIR.mkdir(exist_ok=True)

LEAGUES = {
    "england": "Premier League",
    "spain": "La Liga",
    "italy": "Serie A",
    "germany": "Bundesliga",
    "france": "Ligue 1",
}

# SoccerStats team slug -> Understat name
SS_TO_UNDERSTAT = {
    "arsenal": "Arsenal", "aston-villa": "Aston Villa", "bournemouth": "Bournemouth",
    "brentford": "Brentford", "brighton": "Brighton", "chelsea": "Chelsea",
    "crystal-palace": "Crystal Palace", "everton": "Everton", "fulham": "Fulham",
    "hull": "Hull", "ipswich": "Ipswich", "leeds": "Leeds",
    "liverpool": "Liverpool", "manchester-city": "Manchester City",
    "manchester-united": "Manchester United", "newcastle-united": "Newcastle United",
    "nottingham-forest": "Nottingham Forest", "sunderland": "Sunderland",
    "tottenham-hotspur": "Tottenham", "west-ham-united": "West Ham",
    "wolverhampton-wanderers": "Wolverhampton Wanderers", "burnley": "Burnley",
    "leicester-city": "Leicester", "southampton": "Southampton",
    "coventry-city": "Coventry",
    "atletico-madrid": "Atletico Madrid", "athletic-club": "Athletic Club",
    "barcelona": "Barcelona", "real-madrid": "Real Madrid",
    "real-betis": "Real Betis", "real-sociedad": "Real Sociedad",
    "villarreal": "Villarreal", "sevilla": "Sevilla",
    "valencia": "Valencia", "celta-vigo": "Celta Vigo",
    "getafe": "Getafe", "girona": "Girona", "osasuna": "Osasuna",
    "mallorca": "Mallorca", "espanyol": "Espanyol",
    "rayo-vallecano": "Rayo Vallecano", "deportivo-alaves": "Alaves",
    "levante": "Levante", "elche": "Elche",
    "racing-santander": "Racing Santander", "deportivo-la-coruna": "Deportivo La Coruna",
    "malaga": "Malaga",
    "inter": "Inter", "juventus": "Juventus", "napoli": "Napoli",
    "milan": "AC Milan", "roma": "Roma", "lazio": "Lazio",
    "atalanta": "Atalanta", "fiorentina": "Fiorentina",
    "bologna": "Bologna", "torino": "Torino", "udinese": "Udinese",
    "genoa": "Genoa", "cagliari": "Cagliari", "como": "Como",
    "parma": "Parma", "monza": "Monza", "lecce": "Lecce",
    "frosinone": "Frosinone", "sassuolo": "Sassuolo", "venezia": "Venezia",
    "bayern-munich": "Bayern Munich", "borussia-dortmund": "Dortmund",
    "bayer-leverkusen": "Leverkusen", "rb-leipzig": "RB Leipzig",
    "eintracht-frankfurt": "Eintracht Frankfurt", "vfb-stuttgart": "Stuttgart",
    "fc-augsburg": "Augsburg", "sc-freiburg": "Freiburg",
    "vfl-wolfsburg": "Wolfsburg", "1-fc-union-berlin": "Union Berlin",
    "werder-bremen": "Werder Bremen", "borussia-mgladbach": "Borussia M.Gladbach",
    "fc-st-pauli": "St. Pauli", "holstein-kiel": "Holstein Kiel",
    "1-fc-heidenheim-1846": "FC Heidenheim", "1-fc-koln": "FC Cologne",
    "mainz-05": "Mainz 05", "hoffenheim": "Hoffenheim",
    "psg": "Paris Saint-Germain", "paris-saint-germain": "Paris Saint-Germain",
    "marseille": "Olympique de Marseille", "lyon": "Olympique Lyonnais",
    "monaco": "AS Monaco", "lille": "Lille", "nice": "Nice",
    "rennes": "Stade Rennais", "lens": "RC Lens", "strasbourg": "RC Strasbourg",
    "nantes": "Nantes", "toulouse": "Toulouse", "montpellier": "Montpellier",
    "brest": "Stade Brestois", "le-havre": "Le Havre", "auxerre": "Auxerre",
    "angers": "Angers", "lorient": "Lorient", "troyes": "Troyes",
    "paris-fc": "Paris FC", "le-mans": "Le Mans", "nimes": "Nimes",
}

SEGMENTS = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"]


def setup_webdriver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--log-level=3')
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--window-size=1920,1080')
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    if platform.system() == "Linux":
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


def get_team_links(driver, league_key):
    """Get team stats links from the results page."""
    url = f"https://www.soccerstats.com/results.asp?league={league_key}"
    driver.get(url)
    time.sleep(3)
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='teamstats']")
    teams = {}
    for link in links:
        href = link.get_attribute("href") or ""
        text = (link.get_attribute("textContent") or "").strip()
        if not href or not text:
            continue
        # Extract slug from URL: teamstats.asp?league=england&stats=u324-arsenal
        if "stats=" in href:
            slug = href.split("stats=")[-1]
            # Remove ID prefix (u324-arsenal -> arsenal)
            if "-" in slug:
                slug = slug.split("-", 1)[1] if slug.startswith("u") else slug
            teams[slug] = href
    return teams


def parse_timing_table(soup):
    """Find the 'GOALS PER TIME SEGMENT (total)' table and extract GF/GA per segment."""
    tables = soup.find_all("table")
    for table in tables:
        text = table.get_text(strip=True)
        if "GOALS PER TIME SEGMENT (total)" not in text:
            continue
        rows = table.find_all("tr")
        data = {}
        current_segment = None
        for row in rows:
            cells = row.find_all("td")
            vals = [c.get_text(strip=True) for c in cells]
            if not vals:
                continue
            # Check if first cell is a segment label
            if vals[0] in SEGMENTS:
                current_segment = vals[0]
                # Row format: ['0-15', 'GF', '3', '']
                if len(vals) >= 3 and vals[1] == "GF":
                    gf = vals[2]
                    data.setdefault(current_segment, {})["gf"] = int(gf) if gf.isdigit() else 0
            elif current_segment and len(vals) >= 2 and vals[0] == "GA":
                ga = vals[1]
                data[current_segment]["ga"] = int(ga) if ga.isdigit() else 0
        return data
    return None


def scrape_league(driver, league_key, league_name):
    """Scrape goal timing for all teams in a league."""
    print(f"\n  {league_name} ({league_key})")
    teams = get_team_links(driver, league_key)
    print(f"    Found {len(teams)} teams")

    results = []
    for slug, url in teams.items():
        team_name = SS_TO_UNDERSTAT.get(slug, slug.replace("-", " ").title())
        print(f"    {team_name}...", end=" ", flush=True)
        try:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            timing = parse_timing_table(soup)
            if timing:
                row = {"team": team_name, "league": league_name}
                for seg in SEGMENTS:
                    d = timing.get(seg, {})
                    row[f"gf_{seg}"] = d.get("gf", 0)
                    row[f"ga_{seg}"] = d.get("ga", 0)
                results.append(row)
                total_gf = sum(timing.get(s, {}).get("gf", 0) for s in SEGMENTS)
                total_ga = sum(timing.get(s, {}).get("ga", 0) for s in SEGMENTS)
                print(f"GF={total_gf} GA={total_ga}")
            else:
                print("no timing data")
        except Exception as e:
            print(f"error: {e}")
        time.sleep(1)

    return results


def main():
    print("=" * 60)
    print("  SOCCERSTATS GOAL TIMING SCRAPER")
    print("=" * 60)

    driver = setup_webdriver()

    all_results = []
    for league_key, league_name in LEAGUES.items():
        try:
            results = scrape_league(driver, league_key, league_name)
            all_results.extend(results)
        except Exception as e:
            print(f"\n  ERROR for {league_name}: {e}")

    driver.quit()

    if not all_results:
        print("\nNo data scraped!")
        return

    df = pd.DataFrame(all_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = OUTPUT_DIR / f"goal_timing_{timestamp}.csv"
    df.to_csv(output, index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(df)} teams to {output}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
