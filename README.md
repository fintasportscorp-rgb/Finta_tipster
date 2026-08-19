# Finta Tipster — Big 5 Match Form Dashboard

Scrapes form, xG, absences, formations, odds and expert tips for the top-5 European
leagues, computes a composite form score per team, and renders an interactive,
fully responsive dashboard (React + Vite + Tailwind).

## Project layout

```
.
├── scripts/                # All Python scrapers + the page builder
│   ├── understat.py            # xG / results  -> understat_data/*.csv
│   ├── friendly_scraper.py     # pre-season friendlies -> understat_data/*.csv
│   ├── soccerstats_scraper.py  # goal-timing -> understat_data/goal_timing_*.csv
│   ├── tm_absences.py          # injuries/suspensions -> data/tm_absences_*.csv
│   ├── formation_analysis.py   # formations -> data/big5_formations_2025.csv
│   ├── get_odds.py             # bookmaker odds -> input/big5_odds_*.csv
│   ├── expert_scraper.py       # tipster picks -> input/betting_tips.csv
│   └── build_page.py           # builds web/public/data.json (+ legacy index.html)
├── understat_data/  data/  input/   # scraped CSV inputs (read by build_page.py)
├── web/                    # React app (consumes public/data.json at runtime)
│   └── public/data.json        # produced by build_page.py
└── index.html             # legacy self-contained page (fallback, still generated)
```

The scrapers write CSVs into `understat_data/`, `data/`, `input/`. `build_page.py`
reads those CSVs and writes `web/public/data.json`, which the React app fetches.

## Prerequisites

- Python 3.10+ with: `pandas numpy requests beautifulsoup4 selenium understatapi tqdm`
- Node.js 18+ (ships with npm)

```bash
pip install pandas numpy requests beautifulsoup4 selenium understatapi tqdm
cd web && npm install      # first time only
```

## Run the full process → build the page → publish

All commands are run from the **project root** (this folder).

```bash
# 1. Scrape the source data (run the ones you need; each is standalone)
python scripts/understat.py
python scripts/friendly_scraper.py
python scripts/soccerstats_scraper.py
python scripts/tm_absences.py
python scripts/formation_analysis.py
python scripts/get_odds.py
python scripts/expert_scraper.py

# 2. Build the dashboard data (writes web/public/data.json)
python scripts/build_page.py

# 3. Build the web app and publish/update the GitHub Pages site
cd web
npm run deploy      # builds dist/ and pushes it to the gh-pages branch
```

### One-liner (refresh data already scraped → rebuild → publish)

```bash
python scripts/build_page.py && cd web && npm run deploy && cd ..
```

`npm run deploy` runs `vite build` and then `gh-pages -d dist`, pushing the built
site to the `gh-pages` branch of the `origin` remote.

## First-time GitHub Pages setup

1. Push this repo to `https://github.com/fintasportscorp-rgb/Finta_tipster.git`.
2. Run `cd web && npm run deploy` once to create the `gh-pages` branch.
3. In the repo **Settings → Pages**, set **Source = Deploy from a branch**,
   **Branch = `gh-pages` / root**, and save.
4. The site publishes at **https://fintasportscorp-rgb.github.io/Finta_tipster/**
   (the Vite `base` in `web/vite.config.ts` is set to `/Finta_tipster/` to match).

> Deploying to a different repo/path? Set the base at build time:
> `BASE_PATH=/your-repo/ npm run deploy`  (use `BASE_PATH=/` for a root/user site).

## Local development

```bash
cd web
npm run dev        # http://localhost:5173  (reads public/data.json)
```

Re-run `python scripts/build_page.py` any time to refresh `web/public/data.json`.

## Dashboard features

- Sortable, filterable table of all upcoming matches (filter by data source).
- Click/tap a row to expand: team form breakdown, recent matches, H2H, rolling xG,
  formation history, absences, **odds with the model-predicted pick highlighted**,
  value bets and expert tips.
- Mobile-first responsive layout — non-essential columns collapse on small screens
  and the full detail stays in the expandable row.
