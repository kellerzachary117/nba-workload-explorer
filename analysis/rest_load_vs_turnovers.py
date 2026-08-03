"""
Same rest/workload methodology as multiseason_rest_load_vs_ts.py, applied to
turnover rate instead of shooting efficiency.

Uses TOV% (turnovers per 100 plays: TOV / (FGA + 0.44*FTA + TOV + AST)) rather
than raw turnovers per game, for the same reason TS% was used instead of raw
points: raw turnover counts would just track who handles the ball more (a
recent-workload proxy on its own), not ball security under fatigue. TOV% is
then z-scored against each player's own season baseline, exactly like TS% was.
"""
import glob
import math
from collections import defaultdict
from datetime import datetime, timedelta

MIN_GAMES = 40
LOAD_THRESHOLD = 70.0   # minutes in prior 7 days
REST_THRESHOLD = 1      # 0-1 days rest counts as "low rest"
SEASONS = ["2023-24", "2024-25", "2025-26"]


def files_for_season(season):
    if season == "2023-24":
        return sorted(glob.glob("regular_season_box_scores_2010_2024_part_*.csv"))
    return [f"regular_season_box_scores_{season.replace('-', '_')}.csv"]


def parse_minutes(s):
    if not s:
        return 0.0
    if ":" in s:
        mm, ss = s.split(":")
        return int(mm) + int(ss) / 60.0
    return float(s)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / (vx ** 0.5 * vy ** 0.5)


def mean_std(xs):
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return m, v ** 0.5


def analyze_season(season):
    import csv

    players = defaultdict(list)
    for path in files_for_season(season):
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                if row["season_year"] == season and row["minutes"]:
                    players[row["personId"]].append(row)

    records = []  # pid, name, date, rest_days, rolling7min, tov_pct
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

            fga = float(r["fieldGoalsAttempted"])
            fta = float(r["freeThrowsAttempted"])
            tov = float(r["turnovers"])
            ast = float(r["assists"])
            plays = fga + 0.44 * fta + tov + ast
            if plays <= 0:
                continue
            tov_pct = tov / plays * 100

            records.append([pid, r["personName"], r["game_date"][:10], rest_days, rolling7, tov_pct])

    by_player = defaultdict(list)
    for rec in records:
        by_player[rec[0]].append(rec)

    for pid, recs in by_player.items():
        vals = [rec[5] for rec in recs]
        m = sum(vals) / len(vals)
        sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5
        if sd == 0:
            for rec in recs:
                rec.append(None)
            continue
        for rec in recs:
            rec.append((rec[5] - m) / sd)

    records = [rec for rec in records if rec[-1] is not None]

    n = len(records)
    rest = [r[3] for r in records]
    load = [r[4] for r in records]
    z_tov = [r[6] for r in records]

    r_rest = pearson(rest, z_tov)
    r_load = pearson(load, z_tov)

    mx1, mx2, my = sum(rest) / n, sum(load) / n, sum(z_tov) / n
    Sxx1 = sum((x - mx1) ** 2 for x in rest)
    Sxx2 = sum((x - mx2) ** 2 for x in load)
    Sx1x2 = sum((x1 - mx1) * (x2 - mx2) for x1, x2 in zip(rest, load))
    Sx1y = sum((x1 - mx1) * (y - my) for x1, y in zip(rest, z_tov))
    Sx2y = sum((x2 - mx2) * (y - my) for x2, y in zip(load, z_tov))
    Syy = sum((y - my) ** 2 for y in z_tov)

    det = Sxx1 * Sxx2 - Sx1x2 ** 2
    b1 = (Sx1y * Sxx2 - Sx2y * Sx1x2) / det
    b2 = (Sx2y * Sxx1 - Sx1y * Sx1x2) / det
    r2_combined = (b1 * Sx1y + b2 * Sx2y) / Syy

    group_a = [r[6] for r in records if r[4] > LOAD_THRESHOLD and r[3] <= REST_THRESHOLD]
    group_b = [r[6] for r in records if not (r[4] > LOAD_THRESHOLD and r[3] <= REST_THRESHOLD)]

    ma, sa = mean_std(group_a)
    mb, sb = mean_std(group_b)
    na, nb = len(group_a), len(group_b)

    t_stat = (ma - mb) / math.sqrt(sa ** 2 / na + sb ** 2 / nb)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

    return {
        "season": season,
        "qualifying_players": qualifying,
        "n_rows": n,
        "r_rest": r_rest,
        "r_load": r_load,
        "r2_combined": r2_combined,
        "diff_sd": ma - mb,
        "p_value": p_value,
    }


def main():
    results = [analyze_season(season) for season in SEASONS]

    print(f"{'Season':10} {'Players':8} {'Rows':7} {'r(rest)':9} {'r(load)':9} {'R2':8} {'Diff(sd)':10} {'p-value':9}")
    for res in results:
        print(
            f"{res['season']:10} {res['qualifying_players']:<8} {res['n_rows']:<7} "
            f"{res['r_rest']:+.4f}   {res['r_load']:+.4f}   {res['r2_combined']:.5f}  "
            f"{res['diff_sd']:+.4f}    {res['p_value']:.4f}"
        )


if __name__ == "__main__":
    main()
