"""Portfolio landing page."""
import streamlit as st

GITHUB = "https://github.com/YOUR_USERNAME"
LINKEDIN = "https://linkedin.com/in/YOUR_USERNAME"
EMAIL = "you@example.com"

st.markdown(
    """
    <style>
      .hero-eyebrow { color: #6ee7b7; font-family: monospace; font-size: 1.05rem; margin-bottom: 0; }
      .hero-name { font-size: clamp(2.6rem, 6vw, 4.4rem); font-weight: 800; line-height: 1.05; margin: 0; }
      .hero-sub { font-size: clamp(1.6rem, 4vw, 2.8rem); font-weight: 700; color: #98a2c3; line-height: 1.1; margin: 4px 0 18px; }
      .hero-lead { color: #98a2c3; max-width: 620px; font-size: 1.08rem; }
      .tag { display: inline-block; font-family: monospace; font-size: .8rem; color: #98a2c3;
             border: 1px solid #26305a; border-radius: 6px; padding: 2px 8px; margin: 0 6px 6px 0; }
      .stat { font-size: 2rem; font-weight: 800; color: #6ee7b7; line-height: 1; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Hero
st.markdown(
    """
    <p class="hero-eyebrow">Hi, I'm</p>
    <p class="hero-name">Your Name.</p>
    <p class="hero-sub">I build useful things with Python.</p>
    <p class="hero-lead">Developer focused on AI-powered tools and real-time data apps.
    I like turning messy problems into fast, clean, friendly software.</p>
    """,
    unsafe_allow_html=True,
)
c1, c2, _ = st.columns([1, 1, 4])
c1.link_button("GitHub", GITHUB, width="stretch")
c2.link_button("Email me", f"mailto:{EMAIL}", width="stretch")

st.divider()

# ------------------------------------------------------------ Projects
st.header("Projects")


def tags(*names: str) -> None:
    st.markdown("".join(f'<span class="tag">{n}</span>' for n in names), unsafe_allow_html=True)


col1, col2 = st.columns(2, gap="large")

with col1, st.container(border=True):
    st.subheader("🧠 AI Flashcard Maker")
    st.write(
        "Paste notes, a textbook passage, or just a topic and get a study-ready deck in seconds. "
        "Uses Claude to write question/answer pairs, with an offline fallback that extracts "
        "definitions and fill-in-the-blank cards without an API key. Includes a flip-card study "
        "mode, mastery tracking, an in-place card editor, and Anki/Quizlet CSV export."
    )
    tags("Python", "Streamlit", "Anthropic API", "Regex NLP", "pandas")
    a, b = st.columns(2)
    a.page_link("views/flashcard_maker.py", label="Open the app", icon="▶️")
    b.link_button("View code", f"{GITHUB}/portfolio/tree/main/flashcards", width="stretch")

with col2, st.container(border=True):
    st.subheader("🏟️ Live Sports Tracker")
    st.write(
        "Real-time scoreboard for the NFL, NBA, MLB, NHL, WNBA, college football, MLS and the "
        "Premier League. Auto-refreshes every 30 seconds, shows score changes as they happen, "
        "pins your favorite teams to the top, and lets you browse any date."
    )
    tags("Python", "Streamlit", "requests", "REST API", "dataclasses")
    a, b = st.columns(2)
    a.page_link("views/sports_tracker.py", label="Open the app", icon="▶️")
    b.link_button("View code", f"{GITHUB}/portfolio/tree/main/sports", width="stretch")

st.divider()

# --------------------------------------------------------------- About
st.header("About me")
left, right = st.columns([2, 1], gap="large")
with left:
    st.write(
        "I'm a developer who enjoys building tools people actually open every day. My recent work "
        "focuses on bringing large language models into practical apps and on making live data "
        "feel instant and readable."
    )
    st.write(
        "When I'm not coding, I'm probably watching a game, which is how the sports tracker started. "
        "*Edit this paragraph to tell your own story: where you study or work, what you're learning, "
        "and what kind of role you're looking for.*"
    )
with right:
    s1, s2, s3 = st.columns(3)
    s1.markdown('<div class="stat">2</div>apps shipped', unsafe_allow_html=True)
    s2.markdown('<div class="stat">8</div>leagues', unsafe_allow_html=True)
    s3.markdown('<div class="stat">100%</div>Python', unsafe_allow_html=True)

st.divider()

# -------------------------------------------------------------- Skills
st.header("Skills")
skills = {
    "Languages": "Python, SQL, JavaScript",
    "Python": "Streamlit, pandas, requests, pytest, dataclasses",
    "AI": "Prompt design, LLM APIs, structured JSON output",
    "Tools": "Git, GitHub, VS Code, REST APIs",
}
for col, (title, body) in zip(st.columns(4), skills.items()):
    with col, st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(body)

st.divider()

# ------------------------------------------------------------- Contact
st.header("Get in touch")
st.write("I'm open to internships, freelance work, and collaborations. My inbox is always open.")
st.markdown(f"📧 [{EMAIL}](mailto:{EMAIL}) · [GitHub]({GITHUB}) · [LinkedIn]({LINKEDIN})")
