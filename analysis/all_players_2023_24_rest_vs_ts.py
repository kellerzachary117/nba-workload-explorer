import csv
import glob
from collections import defaultdict
from datetime import datetime

SEASON = "2023-24"
MIN_GAMES = 40

players = defaultdict(list)  # personId -> list of row dicts

for path in sorted(glob.glob("regular_season_box_scores_2010_2024_part_*.csv")):
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["season_year"] == SEASON and row["minutes"]:
                players[row["personId"]].append(row)

# Build per-game records: (personId, personName, date, rest_days, ts_pct)
records = []
qualifying_player_count = 0
for pid, games in players.items():
    if len(games) < MIN_GAMES:
        continue
    qualifying_player_count += 1
    games.sort(key=lambda r: r["game_date"])
    prev_date = None
    for r in games:
        game_date = datetime.strptime(r["game_date"][:10], "%Y-%m-%d")
        rest_days = (game_date - prev_date).days - 1 if prev_date else None
        prev_date = game_date

        if rest_days is None:
            continue  # no prior game to measure rest from

        pts = float(r["points"])
        fga = float(r["fieldGoalsAttempted"])
        fta = float(r["freeThrowsAttempted"])
        denom = 2 * (fga + 0.44 * fta)
        if denom <= 0:
            continue  # no shot attempts, TS% undefined

        ts_pct = pts / denom * 100
        records.append((pid, r["personName"], r["game_date"][:10], rest_days, ts_pct))

print(f"Qualifying players (>= {MIN_GAMES} games): {qualifying_player_count}")
print(f"Total game-rows in correlation sample: {len(records)}\n")

# Pearson correlation between rest_days and ts_pct
n = len(records)
xs = [r[3] for r in records]
ys = [r[4] for r in records]
mean_x = sum(xs) / n
mean_y = sum(ys) / n
cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
var_x = sum((x - mean_x) ** 2 for x in xs)
var_y = sum((y - mean_y) ** 2 for y in ys)
r = cov / (var_x ** 0.5 * var_y ** 0.5)

print(f"Mean rest days: {mean_x:.2f}")
print(f"Mean TS%: {mean_y:.2f}")
print(f"Pearson correlation (rest_days vs TS%): {r:.4f}")

# Breakdown by rest-day bucket for sanity check
buckets = defaultdict(list)
for _, _, _, rd, ts in records:
    key = rd if rd < 4 else "4+"
    buckets[key].append(ts)

print("\nAvg TS% by rest days:")
for key in sorted(buckets.keys(), key=lambda k: (isinstance(k, str), k)):
    vals = buckets[key]
    print(f"  rest={key}: n={len(vals):4d}  avg TS%={sum(vals)/len(vals):.1f}")
