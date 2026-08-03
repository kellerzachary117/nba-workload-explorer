import streamlit as st

st.set_page_config(page_title="NBA Workload & Efficiency Explorer", page_icon="🏀", layout="wide")

st.title("🏀 NBA Workload & Efficiency Explorer")
st.caption("2023-24 through 2025-26 regular seasons · 40+ games per player-season")

st.markdown(
    """
Does playing heavy minutes on short rest hurt a player's shooting efficiency?
It's a common assumption in load-management debates, so we tested it directly
against the data.
"""
)

st.subheader("The hypothesis")
st.markdown(
    """
More recent playing time and less rest between games should show up as
**lower True Shooting % (TS%)** — the theory being that tired legs shoot worse.
We measured "recent workload" as total minutes played in the 7 days before
a game, and "rest" as days off before that game.
"""
)

st.subheader("What the raw data showed")
st.markdown(
    """
Pooling every qualifying player's games together, rest alone showed no
relationship with TS%. But recent workload did — and it pointed the
**wrong way**: players with a heavier 7-day minutes load shot *better*,
not worse.
"""
)

col1, col2, col3 = st.columns(3)
col1.metric("r (rest vs TS%)", "0.002")
col2.metric("r (workload vs TS%)", "0.040")
col3.metric("High-load group TS%", "+1.73 pts", help="vs. everyone else, p < 0.0001")

st.subheader("Diagnosing the confound")
st.markdown(
    """
A positive workload effect doesn't make basketball sense as fatigue — so
before trusting it, we asked what else high recent workload might be
picking up.

The answer: **who plays heavy minutes**. Sustained 7-day workload mostly
identifies starters and high-usage regulars — players who are already
efficient scorers — while low-workload games are disproportionately bench
and rotation minutes, which are noisier and less efficient on average.
The "workload effect" was really a *player quality* effect in disguise.
"""
)

st.subheader("The corrected test")
st.markdown(
    """
To isolate the actual within-player effect, we converted each game's TS%
into a **z-score relative to that player's own season mean and standard
deviation** — so a star's normal night and a bench player's normal night
both read as 0, and only deviations from a player's own baseline count.
"""
)

st.markdown("**Raw pooled data vs. per-player z-scored data:**")
st.table(
    {
        "Metric": [
            "r (rest vs TS%)",
            "r (workload vs TS%)",
            "Combined R²",
            "High-load + low-rest vs. rest of sample",
        ],
        "Raw (pooled)": ["0.0018", "0.0403", "0.0019", "+1.73 pts, p < 0.0001"],
        "Per-player z-scored": ["0.0078", "0.0040", "0.0001", "+0.014 sd, p = 0.29"],
    }
)

st.info(
    "**Bottom line:** once you control for player identity, the workload effect "
    "disappears. Rest and recent workload show no detectable relationship with "
    "shooting efficiency (p = 0.29) — the raw correlation was just heavy-minutes "
    "players being better shooters, not fatigue.",
    icon="🎯",
)

st.caption(
    "A null result here doesn't prove fatigue isn't real — it means this method "
    "(simple linear correlation on per-game TS%, 7-day rolling minutes) didn't detect "
    "one. A real effect might require a longer workload window, opponent/matchup "
    "adjustment, or a non-linear model to surface."
)

st.subheader("Does this hold up in other seasons?")
st.markdown(
    """
The 2023-24 walkthrough above is one season. Re-running the same per-player
z-scored test independently on 2024-25 and 2025-26 — each season's players,
games, and baselines kept separate, never pooled together — checks whether
the null result was a one-season fluke.
"""
)

st.table(
    {
        "Season": ["2023-24", "2024-25", "2025-26"],
        "Players (40+ games)": ["354", "352", "367"],
        "r (rest vs z-TS%)": ["+0.0078", "-0.0011", "-0.0130"],
        "r (workload vs z-TS%)": ["+0.0040", "+0.0044", "+0.0159"],
        "High-load+low-rest vs. rest, p-value": ["0.29", "0.58", "0.14"],
    }
)

st.caption(
    "No season shows a statistically significant rest/workload effect on "
    "per-player z-scored TS% at conventional thresholds (p < 0.05) — the "
    "null result replicates across all three seasons in this dataset, not "
    "just 2023-24."
)

st.subheader("What about turnovers?")
st.markdown(
    """
Shooting touch is one way fatigue could show up — ball security is another,
and arguably a more physically plausible one. We ran the same test on
**turnover rate** (TOV%, turnovers per 100 plays — not raw turnovers, which
would just track who handles the ball more, the same confound TS% had to be
corrected for). Each player's TOV% is z-scored against their own season
baseline, exactly like TS% was, and tested independently per season.
"""
)

st.table(
    {
        "Season": ["2023-24", "2024-25", "2025-26"],
        "r (rest vs z-TOV%)": ["-0.0013", "-0.0114", "-0.0087"],
        "r (workload vs z-TOV%)": ["-0.0045", "-0.0012", "-0.0081"],
        "High-load+low-rest vs. rest, p-value": ["0.57", "0.51", "0.48"],
    }
)

st.caption(
    "Same result as shooting efficiency: no statistically significant "
    "rest/workload effect on turnover rate in any of the three seasons. "
    "Both metrics tested point the same direction — at least for these "
    "playing-time-based proxies, rest and recent workload don't show up in "
    "shot quality or ball security."
)
