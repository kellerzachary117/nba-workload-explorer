import csv
import glob
import math
from collections import defaultdict
from datetime import datetime, timedelta

SEASON = "2023-24"
MIN_GAMES = 40
LOAD_THRESHOLD = 70.0   # minutes in prior 7 days
REST_THRESHOLD = 1      # 0-1 days rest counts as "low rest"


def parse_minutes(s):
    if not s:
        return 0.0
    if ":" in s:
        mm, ss = s.split(":")
        return int(mm) + int(ss) / 60.0
    return float(s)


players = defaultdict(list)
for path in sorted(glob.glob("regular_season_box_scores_2010_2024_part_*.csv")):
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row["season_year"] == SEASON and row["minutes"]:
                players[row["personId"]].append(row)

records = []  # pid, name, date, rest_days, rolling7min, ts_pct
qualifying = 0
for pid, games in players.items():
    if len(games) < MIN_GAMES:
        continue
    qualifying += 1
    games.sort(key=lambda r: r["game_date"])
    parsed = []
    for r in games:
        d = datetime.strptime(r["game_date"][:10], "%Y-%m-%d")
        parsed.append((d, parse_minutes(r["minutes"]), r))

    for i, (date_i, _, r) in enumerate(parsed):
        prev_date = parsed[i - 1][0] if i > 0 else None
        rest_days = (date_i - prev_date).days - 1 if prev_date else None
        if rest_days is None:
            continue

        rolling7 = sum(
            m for d, m, _ in parsed[:i]
            if timedelta(0) < (date_i - d) <= timedelta(days=7)
        )

        pts = float(r["points"])
        fga = float(r["fieldGoalsAttempted"])
        fta = float(r["freeThrowsAttempted"])
        denom = 2 * (fga + 0.44 * fta)
        if denom <= 0:
            continue
        ts_pct = pts / denom * 100

        records.append([pid, r["personName"], r["game_date"][:10], rest_days, rolling7, ts_pct])

print(f"Qualifying players (>= {MIN_GAMES} games): {qualifying}")
print(f"Total game-rows: {len(records)}\n")

# --- Per-player z-score normalization of TS% ---
by_player = defaultdict(list)
for rec in records:
    by_player[rec[0]].append(rec)

dropped_zero_sd = 0
for pid, recs in by_player.items():
    vals = [rec[5] for rec in recs]
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
    if sd == 0:
        dropped_zero_sd += len(recs)
        for rec in recs:
            rec.append(None)
        continue
    for rec in recs:
        rec.append((rec[5] - m) / sd)

records = [rec for rec in records if rec[-1] is not None]
print(f"Dropped {dropped_zero_sd} rows from players with zero TS% variance")
print(f"Rows in z-score analysis: {len(records)}\n")

n = len(records)
rest = [r[3] for r in records]
load = [r[4] for r in records]
z_ts = [r[6] for r in records]


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx ** 0.5 * vy ** 0.5)


r_rest = pearson(rest, z_ts)
r_load = pearson(load, z_ts)
print("=== Correlations with per-player z-scored TS% ===")
print(f"Pearson r (rest_days vs z_TS):        {r_rest:.4f}")
print(f"Pearson r (rolling7min vs z_TS):      {r_load:.4f}")

mx1, mx2, my = sum(rest) / n, sum(load) / n, sum(z_ts) / n
Sxx1 = sum((x - mx1) ** 2 for x in rest)
Sxx2 = sum((x - mx2) ** 2 for x in load)
Sx1x2 = sum((x1 - mx1) * (x2 - mx2) for x1, x2 in zip(rest, load))
Sx1y = sum((x1 - mx1) * (y - my) for x1, y in zip(rest, z_ts))
Sx2y = sum((x2 - mx2) * (y - my) for x2, y in zip(load, z_ts))
Syy = sum((y - my) ** 2 for y in z_ts)

det = Sxx1 * Sxx2 - Sx1x2 ** 2
b1 = (Sx1y * Sxx2 - Sx2y * Sx1x2) / det
b2 = (Sx2y * Sxx1 - Sx1y * Sx1x2) / det
r2_combined = (b1 * Sx1y + b2 * Sx2y) / Syy
print(f"Combined R^2 (rest_days + rolling7min -> z_TS): {r2_combined:.5f}")
print(f"  (single-variable R^2 for reference: rest={r_rest**2:.5f}, load={r_load**2:.5f})\n")

# --- Group comparison on z-scored TS% ---
group_a = [r[6] for r in records if r[4] > LOAD_THRESHOLD and r[3] <= REST_THRESHOLD]
group_b = [r[6] for r in records if not (r[4] > LOAD_THRESHOLD and r[3] <= REST_THRESHOLD)]


def mean_std(xs):
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return m, v ** 0.5


ma, sa = mean_std(group_a)
mb, sb = mean_std(group_b)
na, nb = len(group_a), len(group_b)

t_stat = (ma - mb) / math.sqrt(sa ** 2 / na + sb ** 2 / nb)
p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))  # normal approx (large n)

print("=== Group comparison on per-player z-scored TS% ===")
print(f'Group A: "high recent load (>{LOAD_THRESHOLD} min/7d) + low rest (<={REST_THRESHOLD}d)"')
print(f"  n={na}  mean z_TS={ma:+.4f}  sd={sa:.3f}")
print(f"Group B: everyone else")
print(f"  n={nb}  mean z_TS={mb:+.4f}  sd={sb:.3f}")
print(f"Difference (A - B): {ma - mb:+.4f} sd units")
print(f"Welch's t-stat: {t_stat:.3f}  (normal-approx two-tailed p={p_value:.4f})")
