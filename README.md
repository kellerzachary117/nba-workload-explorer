# 🏀 NBA Workload & Efficiency Explorer

**Live app:** https://nba-workload-explorer-mxycqjgdjlmkgixzznfpvw.streamlit.app/

A Streamlit analytics project testing a common load-management assumption against
NBA play-by-play data: **does playing heavy recent minutes on short rest hurt a
player's shooting efficiency?**

## The finding

Pooling every qualifying player's games together, recent 7-day workload showed a
*positive* relationship with True Shooting % — heavier-minutes players shot
better, not worse. That's backwards for a fatigue effect, which was the signal
this was supposed to catch.

The reason: raw pooled correlation was confounding **workload with player
identity**. Sustained heavy minutes mostly identifies starters and high-usage
regulars, who are already efficient scorers; low-workload games are
disproportionately bench minutes, which are noisier and less efficient on
average. The "workload effect" was a player-quality effect in disguise.

Converting each game's TS% into a **z-score against that player's own season
mean** (so a star's normal night and a bench player's normal night both read as
0) removes that confound. Once player identity is controlled for, rest and
recent workload show **no detectable relationship with shooting efficiency**
(p = 0.29).

| Metric | Raw (pooled) | Per-player z-scored |
|---|---|---|
| r (rest vs TS%) | 0.0018 | 0.0078 |
| r (workload vs TS%) | 0.0403 | 0.0040 |
| Combined R² | 0.0019 | 0.0001 |
| High-load + low-rest vs. rest of sample | +1.73 pts, p < 0.0001 | +0.014 sd, p = 0.29 |

A null result doesn't prove fatigue isn't real — it means this method (linear
correlation on per-game TS%, 7-day rolling minutes) didn't detect one in the
2023-24 regular season. A real effect might need a longer workload window,
opponent/matchup adjustment, or a non-linear model to surface.

## The app

Three pages, built in Streamlit:

- **Home** — the analysis above: hypothesis, raw vs. corrected results, the
  confound diagnosis.
- **Player Lookup** — search any player across the 2023-24 through 2025-26
  seasons; headshot, season averages, and a TS%-z-score-by-game chart
  color-coded by rest status (with a small-sample warning for low-minute
  players).
- **Front Office Takeaways** — the same finding translated into plain-language
  implications for a GM (don't use shooting slumps/streaks as a load-management
  signal) versus a Head Coach/Assistant Coach (don't game-plan around "tired
  legs" shooting worse on a back-to-back).

## Methodology / how the numbers were produced

`data_utils.py` is what the live app runs on. The headline stats on the Home
page were derived by the analysis scripts in [`analysis/`](analysis/), which
document the exploratory path from a single-player sanity check up through the
full pooled-vs-z-scored comparison:

1. `lebron_2023_24_workload.py` — single-player sanity check of the rest/TS%
   pipeline.
2. `all_players_2023_24_rest_vs_ts.py` — pooled rest-days-vs-TS% correlation
   across all qualifying players (40+ games).
3. `rest_load_vs_ts.py` — adds rolling 7-day workload as a second variable;
   surfaces the backwards-looking workload correlation.
4. `rest_load_vs_ts_zscore.py` — per-player z-score normalization; the version
   whose output is quoted in the app and this README.

True Shooting % is computed as `points / (2 * (FGA + 0.44 * FTA)) * 100`.
Rest days and rolling 7-day minutes are computed per player from their own
game log, not league-wide.

## Data source

Box score and totals CSVs (2010-2024) are from
[NocturneBear/NBA-Data-2010-2024](https://github.com/NocturneBear/NBA-Data-2010-2024).
2024-25 and 2025-26 season data was pulled directly from `stats.nba.com` via
[`nba_api`](https://github.com/swar/nba_api) using `fetch_2025_26_box_scores.py`,
matching the same schema.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Requires the CSV data files in the repo root (already included). Python 3.12
is pinned via `runtime.txt` — Streamlit Cloud's default Python 3.14 has an
`altair` compatibility issue as of this writing.

## Tech stack

Python, Streamlit, pandas, Altair, [`nba_api`](https://github.com/swar/nba_api).

## Why this project

Built as a portfolio piece for an Analytics Intern application — the point
isn't the Streamlit app itself, it's the analysis underneath it: catching a
Simpson's-paradox-style confound in a plausible-looking correlation before
trusting it, and being honest about a null result instead of reaching for a
model that would manufacture a signal that isn't there.
