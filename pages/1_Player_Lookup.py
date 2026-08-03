import altair as alt
import pandas as pd
import streamlit as st

from data_utils import all_players_across_seasons, load_game_log
from nav import render_player_lookup_nav

st.set_page_config(page_title="Player Lookup", page_icon="🏀", layout="wide")

season = render_player_lookup_nav()

st.title("Player Lookup")
st.caption(f"{season} regular season")

METRICS = {
    "Shooting efficiency (TS%)": {
        "raw_col": "ts_pct",
        "z_col": "z_ts",
        "raw_label": "Avg TS%",
        "chart_label": "TS%",
        "y_title": "TS% z-score (relative to own season avg)",
        "small_sample_note": "TS% swings heavily with limited playing time and shouldn't be "
        "read the same as a rotation/starter's chart.",
        "caption": "Each point is one game. Y-axis is that game's True Shooting % converted "
        "to a z-score against the player's own season average (0 = their normal night). "
        "Color marks whether the game followed a back-to-back or at least one day of rest.",
    },
    "Turnover rate (TOV%)": {
        "raw_col": "tov_pct",
        "z_col": "z_tov",
        "raw_label": "Avg TOV%",
        "chart_label": "TOV%",
        "y_title": "TOV% z-score (relative to own season avg)",
        "small_sample_note": "TOV% swings heavily with limited playing time and shouldn't be "
        "read the same as a rotation/starter's chart.",
        "caption": "Each point is one game. Y-axis is that game's turnover rate (turnovers "
        "per 100 plays) converted to a z-score against the player's own season average "
        "(0 = their normal night). Color marks whether the game followed a back-to-back or "
        "at least one day of rest.",
    },
}

name_to_id = all_players_across_seasons()

col_player, col_metric = st.columns([3, 2])
with col_player:
    player_name = st.selectbox(
        "Search for a player",
        options=sorted(name_to_id.keys()),
        index=None,
        placeholder="Type a player name...",
    )
with col_metric:
    metric_label = st.selectbox("Metric", options=list(METRICS.keys()))

metric = METRICS[metric_label]

if not player_name:
    st.info("Start typing a name above to look up a player's season.")
    st.stop()

person_id = name_to_id[player_name]
game_log = load_game_log(season)
player_df = game_log[game_log["personId"] == person_id].sort_values("game_date").copy()

if player_df.empty:
    st.warning(f"No data for {player_name} in {season}.")
    st.stop()

headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{person_id}.png"

col_img, col_stats = st.columns([1, 3])
with col_img:
    st.image(headshot_url, width=180)
with col_stats:
    st.subheader(player_name)
    games_played = len(player_df)
    avg_minutes = player_df["minutes_played"].mean()
    avg_metric = player_df[metric["raw_col"]].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("Games played", games_played)
    m2.metric("Avg minutes", f"{avg_minutes:.1f}")
    m3.metric(metric["raw_label"], f"{avg_metric:.1f}%" if pd.notna(avg_metric) else "N/A")

st.subheader(f"{metric['chart_label']} (z-score) across the {season} season")

if games_played < 20 or (pd.notna(avg_minutes) and avg_minutes < 10):
    st.markdown(
        f"""
<div style="border-radius:8px; padding:0.75rem 1rem; margin-bottom:1rem;
            background-color:rgba(137,135,129,0.12); border:1px solid rgba(137,135,129,0.3);
            color:#898781; font-size:0.9rem;">
Small sample: {metric["small_sample_note"]}
</div>
""",
        unsafe_allow_html=True,
    )

chart_df = player_df.dropna(subset=[metric["z_col"], "rest_category"]).copy()

if chart_df.empty:
    st.warning(f"Not enough games with valid {metric['chart_label']} data to build a z-score chart.")
else:
    color_scale = alt.Scale(
        domain=["Rested (1+ days)", "Back-to-back (0 days rest)"],
        range=["#2a78d6", "#eb6834"],
    )

    base = alt.Chart(chart_df).encode(
        x=alt.X("game_date:T", title="Game date"),
    )

    line = base.mark_line(color="#c3c2b7", strokeWidth=2).encode(
        y=alt.Y(f"{metric['z_col']}:Q", title=metric["y_title"]),
        order="game_date:T",
    )

    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="#898781", strokeDash=[4, 4]
    ).encode(y="y:Q")

    points = base.mark_circle(size=140, stroke="#fcfcfb", strokeWidth=1.5).encode(
        y=f"{metric['z_col']}:Q",
        color=alt.Color("rest_category:N", title="Rest before game", scale=color_scale),
        tooltip=[
            alt.Tooltip("game_date:T", title="Date"),
            alt.Tooltip("matchup:N", title="Matchup"),
            alt.Tooltip(f"{metric['raw_col']}:Q", title=metric["chart_label"], format=".1f"),
            alt.Tooltip(f"{metric['z_col']}:Q", title=f"{metric['chart_label']} z-score", format=".2f"),
            alt.Tooltip("rest_days:Q", title="Rest days"),
            alt.Tooltip("rolling7min:Q", title="Prior 7-day minutes", format=".0f"),
            alt.Tooltip("minutes_played:Q", title="Minutes this game", format=".1f"),
        ],
    )

    chart = (zero_rule + line + points).properties(width=950, height=560).interactive()
    st.altair_chart(chart, use_container_width=False)

    st.caption(metric["caption"])
