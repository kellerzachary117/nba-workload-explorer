import csv
import glob
from datetime import datetime

PLAYER_ID = "2544"  # LeBron James
SEASON = "2023-24"

rows = []
for path in sorted(glob.glob("regular_season_box_scores_2010_2024_part_*.csv")):
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if (
                row["personId"] == PLAYER_ID
                and row["season_year"] == SEASON
                and row["minutes"]  # exclude DNP/DND rows (empty minutes)
            ):
                rows.append(row)

rows.sort(key=lambda r: r["game_date"])

prev_date = None
print(f"{'game_date':10} {'matchup':10} {'minutes':7} {'rest_days':9} {'TS%':6}")
for r in rows:
    game_date = datetime.strptime(r["game_date"][:10], "%Y-%m-%d")
    rest_days = (game_date - prev_date).days - 1 if prev_date else None
    prev_date = game_date

    pts = float(r["points"])
    fga = float(r["fieldGoalsAttempted"])
    fta = float(r["freeThrowsAttempted"])
    denom = 2 * (fga + 0.44 * fta)
    ts_pct = (pts / denom * 100) if denom > 0 else 0.0

    rest_str = str(rest_days) if rest_days is not None else "N/A"
    print(f"{r['game_date'][:10]:10} {r['matchup']:10} {r['minutes']:7} {rest_str:9} {ts_pct:5.1f}%")

print(f"\nTotal games: {len(rows)}")
