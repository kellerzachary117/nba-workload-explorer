import glob
from datetime import timedelta

import pandas as pd
import streamlit as st

SEASON = "2023-24"
AVAILABLE_SEASONS = ["2023-24", "2024-25", "2025-26"]

USECOLS = [
    "season_year", "game_date", "matchup", "teamTricode",
    "personId", "personName", "minutes",
    "fieldGoalsAttempted", "freeThrowsAttempted", "points",
]


def _files_for_season(season: str) -> list:
    if season == "2023-24":
        return sorted(glob.glob("regular_season_box_scores_2010_2024_part_*.csv"))
    return [f"regular_season_box_scores_{season.replace('-', '_')}.csv"]


def _parse_minutes(s):
    if pd.isna(s) or s == "":
        return None
    s = str(s)
    if ":" in s:
        mm, ss = s.split(":")
        return int(mm) + int(ss) / 60.0
    return float(s)


@st.cache_data(show_spinner="Loading season data...")
def load_game_log(season: str = SEASON) -> pd.DataFrame:
    frames = []
    for path in _files_for_season(season):
        df = pd.read_csv(path, usecols=USECOLS, dtype={"personId": str})
        frames.append(df[df["season_year"] == season])
    df = pd.concat(frames, ignore_index=True)

    df = df[df["minutes"].notna() & (df["minutes"] != "")].copy()
    df["minutes_played"] = df["minutes"].apply(_parse_minutes)
    df["game_date"] = pd.to_datetime(df["game_date"])

    df = df.sort_values(["personId", "game_date"]).reset_index(drop=True)

    denom = 2 * (df["fieldGoalsAttempted"] + 0.44 * df["freeThrowsAttempted"])
    df["ts_pct"] = (df["points"] / denom * 100).where(denom > 0)

    rest_days_list = []
    rolling7_list = []
    for _, group in df.groupby("personId", sort=False):
        dates = group["game_date"].tolist()
        minutes = group["minutes_played"].tolist()
        prev_date = None
        for i, d in enumerate(dates):
            rest_days_list.append((d - prev_date).days - 1 if prev_date is not None else None)
            prev_date = d
            rolling7_list.append(sum(
                m for dd, m in zip(dates[:i], minutes[:i])
                if timedelta(0) < (d - dd) <= timedelta(days=7)
            ))
    df["rest_days"] = rest_days_list
    df["rolling7min"] = rolling7_list

    df["rest_category"] = df["rest_days"].apply(
        lambda r: "Back-to-back (0 days rest)" if r == 0
        else ("Rested (1+ days)" if pd.notna(r) else None)
    )

    grouped = df.groupby("personId")["ts_pct"]
    player_mean = grouped.transform("mean")
    player_std = grouped.transform(lambda s: s.std(ddof=1))
    player_n = grouped.transform("count")
    df["z_ts"] = (df["ts_pct"] - player_mean) / player_std
    df.loc[(player_n < 2) | (player_std == 0), "z_ts"] = None

    return df


@st.cache_data(show_spinner=False)
def player_name_to_id(df: pd.DataFrame) -> dict:
    return df.drop_duplicates("personName").set_index("personName")["personId"].to_dict()


@st.cache_data(show_spinner="Loading player list...")
def all_players_across_seasons() -> dict:
    """Name -> personId, merged across every season in AVAILABLE_SEASONS.

    Lets the player search box stay stable when the season selector changes,
    so picking a player who didn't play in the current season is possible
    (and handled as a clear "no data" message rather than an empty dropdown).
    """
    combined = {}
    for season in AVAILABLE_SEASONS:
        for path in _files_for_season(season):
            df = pd.read_csv(path, usecols=["personId", "personName"], dtype={"personId": str})
            combined.update(df.drop_duplicates("personName").set_index("personName")["personId"].to_dict())
    return combined
