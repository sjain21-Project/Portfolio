# Samyak Jain

Python developer building AI-powered tools and real-time data apps. This repo is my portfolio: a multi-page **Streamlit** app containing the portfolio site and two working projects, written entirely in Python.

**🌐 [View the live portfolio](https://YOUR_APP_NAME.streamlit.app/)**

## Projects

| Project | What it does | Highlights |
| --- | --- | --- |
| 🧠 **AI Flashcard Maker** | Turns notes, textbook passages, or a single topic into a study deck. | Claude API integration with an offline regex-based fallback, editable card table, flip-card study mode, mastery tracking, JSON/CSV (Anki & Quizlet) export |
| 🏟️ **Live Sports Tracker** | Real-time scoreboard for NFL, NBA, MLB, NHL, WNBA, NCAAF, MLS and EPL. | Auto-refresh every 30s, score-change alerts, favorite teams pinned to top, date browsing, filters and search |

## Repo structure

```
portfolio-python/
├── app.py                     # Entry point: page navigation
├── views/
│   ├── home.py                # Portfolio landing page
│   ├── flashcard_maker.py     # Flashcard app UI (create / edit / study)
│   └── sports_tracker.py      # Scoreboard UI with auto-refresh
├── flashcards/
│   ├── generator.py           # AI prompt + parsing, offline card generator
│   └── storage.py             # Deck persistence, JSON/CSV import & export
├── sports/
│   └── espn.py                # API client, data normalization, sorting
├── tests/                     # pytest unit tests for the logic modules
├── .streamlit/config.toml     # Dark theme
├── requirements.txt
└── LICENSE
```

The UI (`views/`) is kept separate from the logic (`flashcards/`, `sports/`), so the core code is plain Python that's easy to test without a browser.

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/portfolio.git
cd portfolio
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

### Optional: AI mode for flashcards

The flashcard maker works without any key (offline mode). For AI-written cards and topic-only generation, get a key from the [Anthropic Console](https://console.anthropic.com/) and either paste it in the app's sidebar or create `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

`secrets.toml` is in `.gitignore`, so it never gets committed.

## Run the tests

```bash
pip install pytest
pytest
```

## Deploy for free (Streamlit Community Cloud)

GitHub Pages only hosts static HTML, so the live app runs on Streamlit's free hosting while the code lives here on GitHub.

1. Push this repo to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
3. Click **Create app**, pick this repo, branch `main`, and main file `app.py`.
4. *(Optional)* Under **Advanced settings → Secrets**, add `ANTHROPIC_API_KEY = "sk-ant-..."` if you want AI mode on by default. Note that every visitor would then use your key, so leave it blank to have visitors bring their own.
5. Deploy, then paste the `*.streamlit.app` link at the top of this README and into your GitHub profile.

## Data sources

- **Scores:** ESPN's public scoreboard JSON (`site.api.espn.com`). It's unofficial and undocumented, so it may change; only `sports/espn.py` would need updating.
- **AI:** Anthropic Claude via the official `anthropic` Python SDK.

## Built with

Python · Streamlit · pandas · requests · Anthropic API · pytest

## Contact

📧 you@example.com · [LinkedIn](https://linkedin.com/in/YOUR_USERNAME)
