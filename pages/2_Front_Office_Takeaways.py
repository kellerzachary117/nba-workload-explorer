import streamlit as st

st.set_page_config(page_title="Front Office Takeaways", page_icon="🏀", layout="wide")

st.title("🏀 Front Office Takeaways")
st.caption("Plain-language summary of the rest/workload vs. shooting efficiency and turnover findings")

st.subheader("What this means for a GM")
st.markdown(
    """
Once you account for who the player actually is, there's no real link between how much a
guy has played lately (or how much rest he's had) and how well he shoots or how often he
turns the ball over. So don't treat a shooting slump or a rash of turnovers as proof someone
needs to be rested more, and don't treat a hot stretch as proof your current workload plan is
working — neither stat is a reliable signal either way for roster or rotation decisions. This
says nothing about injury risk, long-term durability, or wear and tear, which is a separate
question this analysis didn't touch. Keep load management decisions about health and
durability, not about protecting someone's box score.
"""
)

st.subheader("What this means for a Head Coach/Assistant Coach")
st.markdown(
    """
Don't assume a player on a back-to-back or coming off a heavy-minutes stretch is going to
shoot worse or turn the ball over more — once you isolate it to that player's own normal
performance, neither effect is there, it's just night-to-night noise. That means shortening
someone's rotation or game-planning around an opponent's "tired legs" on the second night of
a back-to-back isn't backed up by the shooting or turnover data. This only measured shooting
efficiency and ball security, though — it doesn't tell you anything about whether fatigue
shows up in lateral quickness or defensive effort, which are still worth watching for
yourself. Use rest and workload for pacing guys and managing injury risk, not for predicting
who's going to make or miss shots or cough the ball up.
"""
)
