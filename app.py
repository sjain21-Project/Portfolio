"""Portfolio entry point. Run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Your Name · Portfolio", page_icon="👋", layout="wide")

pages = st.navigation(
    [
        st.Page("views/home.py", title="Portfolio", icon="👋", default=True),
        st.Page("views/flashcard_maker.py", title="AI Flashcard Maker", icon="🧠", url_path="flashcards"),
        st.Page("views/sports_tracker.py", title="Live Sports Tracker", icon="🏟️", url_path="sports"),
    ]
)
pages.run()
