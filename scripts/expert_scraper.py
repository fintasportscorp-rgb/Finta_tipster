#!/usr/bin/env python3
"""
Betting Tips Scraper v4
=======================
Scrapes BettingExpert.com and OLBG.com for football betting tips.
- BettingExpert: Playwright (extract tips from page DOM, no popup cycling)
- OLBG: requests (SvelteKit embedded JS data extraction)
Date range: today -> next Sunday (inclusive)
Output: CSV with columns: website, league, match, date, tip, comment, rating
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Configuration ────────────────────────────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
_INPUT_DIR = os.path.join(_SCRIPT_DIR, 'input')
os.makedirs(_INPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(_INPUT_DIR, "betting_tips.csv")

TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# Dynamic date range: today -> next Sunday (inclusive)
days_until_sunday = (6 - TODAY.weekday()) % 7
if days_until_sunday == 0:
    days_until_sunday = 7  # if today is Sunday, go to next Sunday
START_DATE = TODAY
END_DATE = TODAY + timedelta(days=days_until_sunday)

BE_BASE = "https://www.bettingexpert.com"
OLBG_BASE = "https://www.olbg.com"

BE_LEAGUES = {
    "Bundesliga": "/football/germany/1-bundesliga",
    "Serie A": "/football/italy/serie-a",
    "LaLiga": "/football/spain/laliga",
    "Ligue 1": "/football/france/ligue-1",
    "Premier League": "/football/england/premier-league",
}

OLBG_LEAGUES = {
    "Serie A": "/betting-tips/Football/European_Competitions/Italy_Serie_A/1",
    "Bundesliga": "/betting-tips/Football/European_Competitions/Germany_Bundesliga_I/1",
    "La Liga": "/betting-tips/Football/European_Competitions/Spain_Primera_Liga/1",
    "Premier League": "/betting-tips/Football/UK/England_Premier_League/1",
    "Ligue 1": "/betting-tips/Football/European_Competitions/France_Ligue_1/1",
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}


@dataclass
class Tip:
    website: str
    league: str
    match: str
    date: str
    tip: str
    comment: str
    rating: str


# ── Date helpers ─────────────────────────────────────────────────────────────

def parse_date(text: str) -> Optional[datetime]:
    text = text.strip()
    low = text.lower()
    if low.startswith("today"):
        return TODAY
    if low.startswith("tomorrow"):
        return TODAY + timedelta(days=1)
    if low.startswith("yesterday"):
        return TODAY - timedelta(days=1)
    # Try common date formats
    cleaned = re.sub(r"[@,]", " ", text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for fmt in [
        "%d %b %H:%M", "%d %b %Y %H:%M", "%d %b %Y",
        "%d %b", "%b %d %H:%M", "%b %d %Y %H:%M",
        "%A %d %B %Y", "%A, %d %B %Y",
        "%d/%m/%Y", "%Y-%m-%d",
        "%d %B %Y", "%d %B",
    ]:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=TODAY.year)
            return dt
        except ValueError:
            pass
    # Try extracting just a date pattern from longer text
    m = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text, re.I)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%d %b")
            return dt.replace(year=TODAY.year)
        except ValueError:
            pass
    return None


def in_range(dt: Optional[datetime], lenient: bool = False) -> bool:
    if dt is None:
        return lenient  # Only accept None dates when explicitly lenient (OLBG)
    return START_DATE <= dt.replace(hour=0, minute=0, second=0, microsecond=0) <= END_DATE


DATE_RE = re.compile(
    r"(Today\s+\d{2}:\d{2})"
    r"|(Tomorrow\s+\d{2}:\d{2})"
    r"|(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2}:\d{2})"
    r"|(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})"
    r"|(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))"
    r"|((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*@?\s*\d{2}:\d{2})"
    r"|((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,\s]+\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))",
    re.I,
)


def find_date(text: str) -> Optional[str]:
    m = DATE_RE.search(text)
    return next((g for g in m.groups() if g), None) if m else None


# ══════════════════════════════════════════════════════════════════════════════
#  OLBG SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

class OLBGScraper:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)

    def get_matches(self, league: str, path: str) -> List[dict]:
        url = OLBG_BASE + path
        print(f"  [OLBG] {league}: {url}")
        r = self.s.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        matches, seen = [], set()

        # Find all match links (event_id pattern)
        for a in soup.find_all("a", href=re.compile(r"event_id=")):
            href = a["href"]
            if href in seen:
                continue
            # Try h5 first, then h4, then any heading
            heading = a.find("h5") or a.find("h4") or a.find("h3")
            if not heading:
                continue
            name = heading.get_text(strip=True)
            if ' v ' not in name.lower() and ' vs ' not in name.lower():
                continue

            text = (a.parent or a).get_text(" ", strip=True)
            ds = find_date(text)
            dt = parse_date(ds) if ds else None
            if not in_range(dt, lenient=True):
                continue
            seen.add(href)
            matches.append({
                "name": name,
                "url": href if href.startswith("http") else OLBG_BASE + href,
                "date": dt.strftime("%Y-%m-%d") if dt else (ds or "Unknown"),
                "league": league,
            })
        print(f"         -> {len(matches)} matches in range ({START_DATE.strftime('%b %d')} - {END_DATE.strftime('%b %d')})")
        return matches

    def get_tips(self, match: dict) -> List[Tip]:
        print(f"    -> {match['name']}")
        r = self.s.get(match["url"], timeout=20)
        r.raise_for_status()
        tips = self._extract(r.text, match)
        print(f"      {len(tips)} tips")
        return tips

    def _extract(self, html: str, match: dict) -> List[Tip]:
        soup = BeautifulSoup(html, "html.parser")
        tips = []
        for script in soup.find_all("script"):
            text = script.string or ""
            if "__sveltekit" not in text or "comments:[" not in text:
                continue
            for block in re.split(r'(?=\bid:"[a-f0-9]{20,}")', text):
                if "comments:[" not in block:
                    continue
                sel_m = re.search(r'selection:"([^"]*)"', block)
                mkt_m = re.search(r'market_name:"([^"]*)"', block)
                conf_m = re.search(r'confidence:(\d+)', block)
                selection = sel_m.group(1) if sel_m else "Unknown"
                market = mkt_m.group(1) if mkt_m else ""
                confidence = int(conf_m.group(1)) if conf_m else 0

                for cm in re.finditer(r'\{sport:"Football"(.*?)(?=\}\s*,\s*\{sport:|\}\s*\])', block, re.DOTALL):
                    raw = cm.group(0)
                    user = self._f(r'user:"([^"]*)"', raw)
                    comment = self._f(r'comment:"((?:[^"\\]|\\.)*)"', raw)
                    comment = comment.replace('\\"', '"').replace('\\n', ' ')
                    odds = self._f(r'(?<![a-z_])odds:([\d.]+)', raw)
                    expert = bool(re.search(r'expert:1', raw))
                    profit = self._f(r'currentYearProfit:(-?\d+)', raw)
                    strike = self._f(r'currentYearStrike:(\d+)', raw)
                    mprofit = self._f(r'currentMonthProfit:(-?\d+)', raw)

                    tip_str = selection
                    if market:
                        tip_str += f" ({market})"
                    if odds:
                        tip_str += f" @{odds}"

                    parts = []
                    if confidence:
                        parts.append(f"{confidence}% conf")
                    if profit:
                        parts.append(f"YrProfit:{profit}")
                    if mprofit:
                        parts.append(f"MoProfit:{mprofit}")
                    if strike:
                        parts.append(f"Strike:{strike}%")
                    if expert:
                        parts.append("Expert")

                    tips.append(Tip(
                        website="OLBG",
                        league=match["league"],
                        match=match["name"],
                        date=match["date"],
                        tip=tip_str,
                        comment=f"[{user}] {comment}" if user else comment,
                        rating=" | ".join(parts) or "N/A",
                    ))
            if tips:
                return tips
        return tips

    @staticmethod
    def _f(pattern, text):
        m = re.search(pattern, text)
        return m.group(1) if m else ""

    def scrape(self) -> List[Tip]:
        all_tips = []
        for league, path in OLBG_LEAGUES.items():
            try:
                for m in self.get_matches(league, path):
                    try:
                        all_tips.extend(self.get_tips(m))
                        time.sleep(0.8)
                    except Exception as e:
                        print(f"      (!) {e}")
            except Exception as e:
                print(f"    (!) {e}")
        return all_tips


# ══════════════════════════════════════════════════════════════════════════════
#  BETTINGEXPERT SCRAPER (v5 - requests + Next.js RSC extraction)
#  The old Playwright/DOM approach broke when BettingExpert moved to Next.js RSC.
#  Tips are now extracted from embedded RSC script data using regex.
# ══════════════════════════════════════════════════════════════════════════════

class BettingExpertScraper:
    """Requests-based scraper for BettingExpert.

    BettingExpert is now a Next.js app using React Server Components (RSC).
    Tips are embedded in <script> tags as serialized RSC payloads.
    We extract tip data (tipster, selection, odds, winner) via regex.
    """

    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)

    def scrape(self) -> List[Tip]:
        all_tips = []
        for league, path in BE_LEAGUES.items():
            try:
                matches = self._get_matches(league, path)
                for m in matches:
                    try:
                        tips = self._get_tips(m)
                        all_tips.extend(tips)
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"      (!) {str(e)[:120]}")
            except Exception as e:
                print(f"    (!) {str(e)[:120]}")
        return all_tips

    def _get_matches(self, league: str, path: str) -> List[dict]:
        url = BE_BASE + path
        print(f"  [BE] {league}: {url}")
        r = self.s.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        matches, seen = [], set()
        for a in soup.find_all("a", href=re.compile(r"-vs-")):
            href = a.get("href", "")
            if href in seen:
                continue
            # Skip non-match links (navigation, related articles)
            link_text = a.get_text(" ", strip=True)
            if len(link_text) < 5:
                continue

            ds = find_date(link_text)
            dt = parse_date(ds) if ds else None
            if not in_range(dt, lenient=False):
                continue

            seen.add(href)
            slug = href.rstrip("/").split("/")[-1]
            name = slug.replace("-vs-", " vs ").replace("-", " ").title()
            full = href if href.startswith("http") else BE_BASE + href
            matches.append({
                "name": name,
                "url": full,
                "date": dt.strftime("%Y-%m-%d") if dt else (ds or "Unknown"),
                "league": league,
            })

        print(f"         -> {len(matches)} matches in range ({START_DATE.strftime('%b %d')} - {END_DATE.strftime('%b %d')})")
        return matches

    def _get_tips(self, match: dict) -> List[Tip]:
        print(f"    -> {match['name']}")
        r = self.s.get(match["url"], timeout=20)
        r.raise_for_status()
        html = r.text

        tips = self._extract_tips_from_rsc(html, match)
        print(f"      -> {len(tips)} tips extracted")
        return tips

    def _extract_tips_from_rsc(self, html: str, match: dict) -> List[Tip]:
        """Extract tips from Next.js RSC script data.

        BettingExpert embeds tip data in RSC payloads inside <script> tags.
        Each tip object contains: tipId, oneliner, description, odds (in bet),
        home/away names (in match), and user (tipster info).
        """
        soup = BeautifulSoup(html, "html.parser")
        tips = []
        seen_tip_ids = set()

        # Collect all script content into one string
        all_script_text = ""
        for script in soup.find_all("script"):
            text = script.string or ""
            if len(text) > 200:
                all_script_text += "\n" + text

        if not all_script_text:
            return tips

        # Normalize escaped quotes (RSC payloads use \" instead of ")
        all_script_text = all_script_text.replace('\\"', '"')

        # Find all tipId occurrences — each marks a tip
        tip_id_matches = list(re.finditer(r'"tipId":(\d+)', all_script_text))

        if not tip_id_matches:
            return tips

        for tm in tip_id_matches:
            tip_id = tm.group(1)
            if tip_id in seen_tip_ids:
                continue
            seen_tip_ids.add(tip_id)

            # Use a large window — tip object can be 5000+ chars
            start = tm.start()
            window = all_script_text[start:start + 10000]

            # Extract oneliner (tip summary, e.g. "Arsenal -2.00 (AH)")
            oneliner_m = re.search(r'"oneliner":"([^"]*)"', window)
            oneliner = oneliner_m.group(1) if oneliner_m else ""

            # Extract odds from bet object
            odds_m = re.search(r'"odds":([\d.]+)', window)
            odds = odds_m.group(1) if odds_m else ""

            # Extract home and away team names from match object
            home_m = re.search(r'"home":\{"id":\d+,"name":"([^"]*)"', window)
            away_m = re.search(r'"away":\{"id":\d+,"name":"([^"]*)"', window)
            home_team = home_m.group(1) if home_m else ""
            away_team = away_m.group(1) if away_m else ""

            # Extract tipster name from user object (name/username near profileImage)
            tipster_m = re.search(
                r'"(?:username|name)":"([^"]{2,40})"[^}]{0,200}"profileImage"', window
            )
            if not tipster_m:
                tipster_m = re.search(
                    r'"name":"([^"]{2,40})"[^}]{0,300}"stats":\{"rating"', window
                )
            tipster = tipster_m.group(1) if tipster_m else ""

            # Extract description (tipster's analysis)
            desc_m = re.search(r'"description":"([^"]{0,500})', window)
            comment = desc_m.group(1) if desc_m else ""

            # Build tip text — prefer oneliner, fall back to selection data
            if oneliner:
                tip_text = oneliner
            else:
                # Fallback: try selection_type + winner
                sel_m = re.search(r'"selection_type":"([^"]*)"', window)
                winner_m = re.search(r'"winner":"([12Xx])"', window)
                sel_type = sel_m.group(1) if sel_m else ""
                winner = winner_m.group(1) if winner_m else ""
                if sel_type == "win" and winner:
                    if winner == "1":
                        tip_text = f"{home_team} to win" if home_team else "Home to win"
                    elif winner == "2":
                        tip_text = f"{away_team} to win" if away_team else "Away to win"
                    else:
                        tip_text = "Draw"
                elif sel_type:
                    tip_text = sel_type.replace("_", " ").title()
                else:
                    tip_text = "Tip"

            if odds:
                tip_text += f" @{odds}"

            # Build rating
            rating_parts = []
            if tipster:
                rating_parts.append(f"tipster: {tipster}")
            if odds:
                rating_parts.append(f"odds {odds}")
            rating_parts.append("src:RSC")

            tips.append(Tip(
                website="BettingExpert",
                league=match["league"],
                match=match["name"],
                date=match["date"],
                tip=tip_text,
                comment=comment,
                rating=" | ".join(rating_parts),
            ))

        return tips

    async def _get_tips_popup_fallback(self, page, match: dict) -> List[Tip]:
        """Fallback: try clicking 'Read more' and cycling through popup."""
        await page.evaluate(
            'document.querySelectorAll("h2").forEach(h=>{'
            'if(h.textContent.includes("Featured Community Tips"))h.scrollIntoView()'
            '})'
        )
        await page.wait_for_timeout(1000)

        clicked = await page.evaluate("""() => {
            for (const slide of document.querySelectorAll('.embla__slide')) {
                for (const btn of slide.querySelectorAll('button')) {
                    if (btn.textContent.trim() === 'Read more') {
                        btn.click();
                        return true;
                    }
                }
            }
            return false;
        }""")

        if not clicked:
            return []

        await page.wait_for_timeout(3000)

        extract_js = """() => {
            const popup = document.querySelector('.z-50.fixed');
            if (!popup) return null;
            const inner = popup.querySelector('.bg-white') || popup;
            const tipsterLink = inner.querySelector('a[href*="/user/profile/"]');
            const tipster = tipsterLink
                ? (tipsterLink.querySelector('span')?.textContent?.trim() || 'Unknown')
                : 'Unknown';
            const filledStars = inner.querySelectorAll('svg[data-icon="star"].text-yellow').length;
            const totalStars = inner.querySelectorAll('svg[data-icon="star"]').length;
            const h1 = inner.querySelector('h1');
            const tip = h1 ? h1.textContent.trim() : 'Unknown';
            const text = inner.textContent;
            const oddsMatch = text.match(/Tipped at\\s+([\\d.]+)/);
            const odds = oddsMatch ? oddsMatch[1] : '';
            let comment = '';
            const stakeMatch = text.match(/Stake\\s+\\S+/);
            if (stakeMatch) {
                const idx = text.indexOf(stakeMatch[0]) + stakeMatch[0].length;
                comment = text.substring(idx).trim();
            }
            return { tipster, filledStars, totalStars, tip, odds, comment: comment.substring(0, 500) };
        }"""

        next_js = """() => {
            const popup = document.querySelector('.z-50.fixed');
            if (!popup) return false;
            const nextBtn = popup.querySelector('.bg-primary.rounded-full');
            if (nextBtn) { nextBtn.click(); return true; }
            return false;
        }"""

        close_js = """() => {
            const popup = document.querySelector('.z-50.fixed');
            if (!popup) return;
            const xmark = popup.querySelector('.fa-xmark');
            if (xmark) {
                const btn = xmark.closest('div[class*="cursor-pointer"]') || xmark.parentElement;
                if (btn) btn.click();
            } else { popup.remove(); }
        }"""

        tips_data = []
        seen_keys = set()
        for i in range(20):
            tip = await page.evaluate(extract_js)
            if not tip:
                break
            key = f"{tip['tipster']}|{tip['tip']}|{tip['odds']}"
            if key in seen_keys:
                break
            seen_keys.add(key)
            tips_data.append(tip)
            has_next = await page.evaluate(next_js)
            if not has_next:
                break
            await page.wait_for_timeout(1500)

        await page.evaluate(close_js)
        await page.wait_for_timeout(500)

        tips = []
        for td in tips_data:
            rating = f"{td['filledStars']}/5 stars (tipster: {td['tipster']})"
            if td["odds"]:
                rating += f" | odds {td['odds']}"
            tips.append(Tip(
                website="BettingExpert",
                league=match["league"],
                match=match["name"],
                date=match["date"],
                tip=td["tip"],
                comment=td["comment"][:500],
                rating=rating,
            ))
        return tips


# ══════════════════════════════════════════════════════════════════════════════
#  CSV + MAIN
# ══════════════════════════════════════════════════════════════════════════════

def save_csv(tips: List[Tip], path: str):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["website", "league", "match", "date", "tip", "comment", "rating"])
        w.writeheader()
        for t in tips:
            w.writerow(asdict(t))
    print(f"\n=> Saved {len(tips)} tips to {path}")


def main():
    print("=" * 65)
    print("  BETTING TIPS SCRAPER v5")
    print(f"  {START_DATE.strftime('%a %d %b')} -> {END_DATE.strftime('%a %d %b %Y')}")
    print("=" * 65)

    all_tips: List[Tip] = []

    print("\n--- OLBG (requests) -----------------------------------------")
    olbg = OLBGScraper()
    olbg_tips = olbg.scrape()
    all_tips.extend(olbg_tips)
    print(f"\n  OLBG total: {len(olbg_tips)} tips")

    print("\n--- BettingExpert (requests + RSC) --------------------------")
    be = BettingExpertScraper()
    be_tips = be.scrape()
    all_tips.extend(be_tips)
    print(f"\n  BettingExpert total: {len(be_tips)} tips")

    print("\n--- Output --------------------------------------------------")
    save_csv(all_tips, OUTPUT_FILE)

    # Summary by league
    leagues = {}
    for t in all_tips:
        leagues.setdefault(t.league, {"OLBG": 0, "BettingExpert": 0})
        leagues[t.league][t.website] += 1

    print(f"\n{'=' * 65}")
    print(f"  DONE -- {len(all_tips)} tips total")
    print(f"  OLBG: {len(olbg_tips)} | BettingExpert: {len(be_tips)}")
    for lg, counts in sorted(leagues.items()):
        print(f"    {lg}: OLBG={counts['OLBG']} BE={counts['BettingExpert']}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
