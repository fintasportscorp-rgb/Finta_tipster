from understatapi import UnderstatClient
import pandas as pd
from pathlib import Path

# Configuration
season = "2026"
leagues = {
    "EPL": "EPL",
    "La_Liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A": "Serie A",
    "Ligue_1": "Ligue 1"
}

understat = UnderstatClient()

all_dfs = []

for league_key, league_name in leagues.items():
    print(f"Fetching {league_name} ({season})...")

    try:
        matches = understat.league(league=league_key).get_match_data(season=season)

        rows = []
        for match in matches:
            rows.append({
                "league": league_name,
                "match_id": match.get("id"),
                "datetime": match.get("datetime"),
                "gameweek": match.get("week"),
                "home_team": match.get("h", {}).get("title"),
                "away_team": match.get("a", {}).get("title"),
                "home_goals": match.get("goals", {}).get("h"),
                "away_goals": match.get("goals", {}).get("a"),
                "home_xG": match.get("xG", {}).get("h"),
                "away_xG": match.get("xG", {}).get("a"),
                "forecast_home_win": match.get("forecast", {}).get("w"),
                "forecast_draw": match.get("forecast", {}).get("d"),
                "forecast_away_win": match.get("forecast", {}).get("l")
            })

        if not rows:
            print(f"  -> 0 matches (season not available yet)")
            continue

        df = pd.DataFrame(rows)

        # Convert datetime and sort
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)

        # Rebuild gameweek if missing
        if df["gameweek"].isna().all() or df["gameweek"].eq(0).all():
            matches_per_week = 10 if league_key == "EPL" else 9
            df["gameweek"] = (df.index // matches_per_week) + 1

        all_dfs.append(df)
        print(f"  -> {len(df)} matches fetched")

    except Exception as e:
        print(f"  -> Error fetching {league_name}: {e}")

if not all_dfs:
    print("\nNo data fetched. Exiting.")
    exit(1)

# Combine all leagues
final_df = pd.concat(all_dfs, ignore_index=True)

# Final sorting
final_df = final_df.sort_values(["league", "datetime"]).reset_index(drop=True)

# Save files
output_dir = Path(__file__).parent.parent / "understat_data"  # project root/understat_data
output_dir.mkdir(exist_ok=True)

# One combined file + separate files per league
final_df.to_csv(output_dir / f"big5_understat_{season}.csv", index=False)

for league_name, df_league in final_df.groupby("league"):
    safe_name = league_name.lower().replace(" ", "_").replace("_1", "1")
    df_league.to_csv(output_dir / f"{safe_name}_understat_{season}.csv", index=False)

print(f"\nDone! {len(final_df)} total matches across Big 5 leagues.")
print(f"Files saved to: {output_dir}/")
print(final_df.groupby("league").size())
