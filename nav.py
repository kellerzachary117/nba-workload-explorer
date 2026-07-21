import streamlit as st

from data_utils import AVAILABLE_SEASONS

TOOLBAR_CSS = """
<style>
/* Trim Streamlit's large default top inset down to just enough to clear
   its own fixed header bar (60px) — dropping it to 0 put our content
   underneath that header instead of below it. */
[data-testid="stMainBlockContainer"] {
    padding-top: 60px !important;
}
.st-key-top_nav {
    /* The bar's own box keeps Streamlit's normal flex-item sizing (fighting
       that with negative margins/calc widths made the selectbox occupy
       space but stop painting — a real rendering bug, not just a layout
       quirk). The full-bleed look instead comes from an absolutely
       positioned ::before that paints past the edges without touching
       layout at all. */
    position: relative;
    padding: 0.9rem 0;
    margin: 0 0 2rem 0;
}
.st-key-top_nav::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: -80px;
    right: -80px;
    border-bottom: 1px solid rgba(137, 135, 129, 0.25);
    z-index: -1;
}
.st-key-top_nav [data-testid="stSelectbox"] label {
    display: none;
}
.st-key-top_nav [data-testid="stMarkdownContainer"] p {
    font-size: 1.2rem;
    font-weight: 700;
    margin: 0;
}
</style>
"""


def render_player_lookup_nav() -> str:
    """Renders the Player Lookup page's toolbar (icon/title + season selector)
    and returns the currently selected season. Player-Lookup-only: the season
    selector doesn't appear on Home."""
    st.session_state.setdefault("season", AVAILABLE_SEASONS[0])

    st.markdown(TOOLBAR_CSS, unsafe_allow_html=True)

    with st.container(key="top_nav"):
        col_brand, col_season = st.columns([5, 2], vertical_alignment="center")
        with col_brand:
            st.markdown("🏀 NBA Workload Explorer")
        with col_season:
            st.selectbox(
                "Season",
                options=AVAILABLE_SEASONS,
                key="season",
            )

    return st.session_state["season"]
