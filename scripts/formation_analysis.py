import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
from tqdm import tqdm

# ====================== CONFIG ======================
SEASON = "2026"  # 2026/27 season
BIG5 = {
    "Premier League": "GB1",
    "La Liga":        "ES1",
    "Bundesliga":     "L1",
    "Serie A":        "IT1",
    "Ligue 1":        "FR1"
}

MAX_MATCHDAYS = 38
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Save directly where preprocessing expects it
OUTPUT_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "big5_formations_2025.csv")
)
# ===================================================

_FORMATION_RE = re.compile(r"(\d-\d-\d(?:-\d)?)")


def parse_match_report(url: str) -> list[dict] | None:
    """
    Fetch a TM match report and return a list of 1–2 dicts:
      {team_name, formation_code, formation_text, is_home}

    Strategy:
      1. Find the div.box whose text starts with 'Line-Ups'.
      2. Its direct div children (excluding .clearer) are [home_side, away_side].
      3. Team name  → <a class="sb-vereinslink"> inside each side.
      4. Formation  → <div class="formation-subtitle"> inside each side.
      5. Full text  → side.get_text(strip=True)  — no truncation.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
    except Exception:
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Locate the Line-Ups box
    lineups_box = None
    for box in soup.find_all("div", class_="box"):
        text_start = box.get_text(strip=True)[:20]
        if "Line-Ups" in text_start or "Line-up" in text_start:
            lineups_box = box
            break

    if lineups_box is None:
        return None

    # Direct div children — home is index 0, away is index 1
    sides = [
        c for c in lineups_box.children
        if getattr(c, "name", None) == "div"
        and "clearer" not in c.get("class", [])
    ]

    if not sides:
        return None

    rows = []
    for i, side in enumerate(sides[:2]):         # at most 2 sides
        # Team name
        team_a = side.find("a", class_="sb-vereinslink")
        team_name = team_a.get_text(strip=True) if team_a else "Unknown"

        # Formation code
        form_div  = side.find("div", class_="formation-subtitle")
        form_text = form_div.get_text(strip=True) if form_div else ""
        m = _FORMATION_RE.search(form_text)
        formation_code = m.group(1) if m else ""

        if not formation_code:
            continue                              # skip if no formation found

        rows.append({
            "team_name":      team_name,
            "formation_code": formation_code,
            "formation_text": side.get_text(strip=True),   # full, no truncation
            "is_home":        i == 0,
        })

    return rows if rows else None


# ====================== MAIN LOOP ======================
all_data = []

print("Starting Transfermarkt Big 5 Formations Scraper\n")

for league_name, comp_id in BIG5.items():
    print(f"Scraping {league_name}...")

    for matchday in tqdm(range(1, MAX_MATCHDAYS + 1), desc=league_name):
        url = (
            f"https://www.transfermarkt.com/premier-league/spieltag"
            f"/wettbewerb/{comp_id}/saison_id/{SEASON}/spieltag/{matchday}"
        )

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # Each match on the matchday page has a link to the spielbericht
            seen_urls = set()
            for a in soup.find_all("a", href=lambda x: x and "spielbericht" in x):
                match_url = "https://www.transfermarkt.com" + a["href"]
                if match_url in seen_urls:
                    continue
                seen_urls.add(match_url)

                time.sleep(0.8)
                rows = parse_match_report(match_url)
                if not rows:
                    continue

                # home_team / away_team from the pair (for context columns)
                home_name = next((r["team_name"] for r in rows if r["is_home"]),  "Unknown")
                away_name = next((r["team_name"] for r in rows if not r["is_home"]), "Unknown")

                for row in rows:
                    all_data.append({
                        "league":         league_name,
                        "season":         f"{SEASON}/{int(SEASON) + 1}",
                        "matchday":       matchday,
                        "home_team":      home_name,
                        "away_team":      away_name,
                        "is_home":        row["is_home"],
                        "formation_text": row["formation_text"],
                        "match_url":      match_url,
                    })

        except Exception as e:
            print(f"  Error on {league_name} MD{matchday}: {e}")

        time.sleep(1.5)

# ====================== SAVE ======================
if all_data:
    df = pd.DataFrame(all_data)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    # Quick validation
    from preprocessing import _FORMATION_RE as _RE  # reuse same regex
    df["_fc"] = df["formation_text"].apply(
        lambda t: m.group(1) if (m := _RE.search(str(t))) else ""
    )
    parsed_pct = df["_fc"].ne("").mean() * 100

    print(f"\nFINISHED")
    print(f"Total rows     : {len(df)}  (~{len(df)//2} matches)")
    print(f"Fully paired   : {(df.groupby('match_url').size() == 2).sum()} matches with both sides")
    print(f"Formation parse: {parsed_pct:.1f}%")
    print(f"Output         : {OUTPUT_PATH}")
    print("\n=== Most common formations ===")
    print(df["_fc"].value_counts().head(10))
    print("\n=== Home vs Away counts ===")
    print(df["is_home"].value_counts())
    print("\n=== Rows per league ===")
    print(df.groupby("league").size())
else:
    print("No data collected.")
