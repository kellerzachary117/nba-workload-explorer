"""
Pulls all 2025-26 regular season player box scores from stats.nba.com via nba_api,
matching the column schema of regular_season_box_scores_2010_2024_part_*.csv.

Resumable: re-running skips game_ids already present in the output CSV, so an
interrupted run can just be started again.
"""
import csv
import os
import sys
import time

from nba_api.stats.endpoints import boxscoretraditionalv3, leaguegamelog

SEASON = sys.argv[1] if len(sys.argv) > 1 else "2025-26"
OUTPUT_PATH = f"regular_season_box_scores_{SEASON.replace('-', '_')}.csv"
REQUEST_DELAY = 0.6  # seconds between box score calls, to stay polite to the API
MAX_RETRIES = 5

FIELDNAMES = [
    "season_year", "game_date", "gameId", "matchup", "teamId", "teamCity",
    "teamName", "teamTricode", "teamSlug", "personId", "personName", "position",
    "comment", "jerseyNum", "minutes", "fieldGoalsMade", "fieldGoalsAttempted",
    "fieldGoalsPercentage", "threePointersMade", "threePointersAttempted",
    "threePointersPercentage", "freeThrowsMade", "freeThrowsAttempted",
    "freeThrowsPercentage", "reboundsOffensive", "reboundsDefensive",
    "reboundsTotal", "assists", "steals", "blocks", "turnovers",
    "foulsPersonal", "points", "plusMinusPoints",
]


def already_fetched_game_ids():
    if not os.path.exists(OUTPUT_PATH):
        return set()
    with open(OUTPUT_PATH, newline="") as f:
        return {row["gameId"] for row in csv.DictReader(f)}


def fetch_game_log():
    gl = leaguegamelog.LeagueGameLog(
        season=SEASON, season_type_all_star="Regular Season", timeout=30
    )
    df = gl.get_data_frames()[0]
    # (game_id, team_id) -> (game_date, matchup)
    lookup = {}
    for _, row in df.iterrows():
        lookup[(row["GAME_ID"], row["TEAM_ID"])] = (row["GAME_DATE"], row["MATCHUP"])
    game_ids = sorted(df["GAME_ID"].unique())
    return lookup, game_ids


def fetch_box_score(game_id):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            bs = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, timeout=30)
            return bs.get_data_frames()[0]
        except Exception as e:
            wait = 2 ** attempt
            print(f"    attempt {attempt}/{MAX_RETRIES} failed ({e}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch box score for game {game_id} after {MAX_RETRIES} attempts")


def main():
    print(f"Fetching {SEASON} regular season game log...")
    lookup, game_ids = fetch_game_log()
    print(f"Found {len(game_ids)} games.")

    done = already_fetched_game_ids()
    remaining = [g for g in game_ids if g not in done]
    print(f"Already fetched: {len(done)}. Remaining: {len(remaining)}.")

    write_header = not os.path.exists(OUTPUT_PATH)
    with open(OUTPUT_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        for i, game_id in enumerate(remaining, 1):
            print(f"[{i}/{len(remaining)}] game {game_id}")
            player_df = fetch_box_score(game_id)

            rows = []
            for _, r in player_df.iterrows():
                key = (game_id, r["teamId"])
                game_date, matchup = lookup.get(key, ("", ""))
                rows.append({
                    "season_year": SEASON,
                    "game_date": game_date,
                    "gameId": game_id,
                    "matchup": matchup,
                    "teamId": r["teamId"],
                    "teamCity": r["teamCity"],
                    "teamName": r["teamName"],
                    "teamTricode": r["teamTricode"],
                    "teamSlug": r["teamSlug"],
                    "personId": r["personId"],
                    "personName": f"{r['firstName']} {r['familyName']}".strip(),
                    "position": r["position"],
                    "comment": r["comment"],
                    "jerseyNum": r["jerseyNum"],
                    "minutes": r["minutes"],
                    "fieldGoalsMade": r["fieldGoalsMade"],
                    "fieldGoalsAttempted": r["fieldGoalsAttempted"],
                    "fieldGoalsPercentage": r["fieldGoalsPercentage"],
                    "threePointersMade": r["threePointersMade"],
                    "threePointersAttempted": r["threePointersAttempted"],
                    "threePointersPercentage": r["threePointersPercentage"],
                    "freeThrowsMade": r["freeThrowsMade"],
                    "freeThrowsAttempted": r["freeThrowsAttempted"],
                    "freeThrowsPercentage": r["freeThrowsPercentage"],
                    "reboundsOffensive": r["reboundsOffensive"],
                    "reboundsDefensive": r["reboundsDefensive"],
                    "reboundsTotal": r["reboundsTotal"],
                    "assists": r["assists"],
                    "steals": r["steals"],
                    "blocks": r["blocks"],
                    "turnovers": r["turnovers"],
                    "foulsPersonal": r["foulsPersonal"],
                    "points": r["points"],
                    "plusMinusPoints": r["plusMinusPoints"],
                })

            writer.writerows(rows)
            f.flush()
            time.sleep(REQUEST_DELAY)

    print(f"Done. Wrote to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
