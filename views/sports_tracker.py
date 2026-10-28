"""Live Sports Tracker page."""
from datetime import date, datetime, timedelta
from html import escape

import streamlit as st

from sports.espn import LEAGUES, Game, fetch_scoreboard, sort_games

REFRESH_SECONDS = 30

ss = st.session_state
ss.setdefault("league", "NFL")
ss.setdefault("day", date.today())
ss.setdefault("favorites", set())     # "LEAGUE:teamId"
ss.setdefault("prev_scores", {})      # "gameId:teamId" -> score


@st.cache_data(ttl=REFRESH_SECONDS - 5, show_spinner=False)
def get_games(league: str, day: date) -> list[Game]:
    """Cached so many viewers / reruns don't hammer the API."""
    return fetch_scoreboard(league, day)


st.markdown(
    """
    <style>
      .live-badge { background:#f43f5e; color:#fff; border-radius:6px; padding:1px 8px; font-size:.75rem;
                    font-weight:700; font-family:monospace; animation: blink 2s infinite; }
      .final-badge { background:#334155; color:#e2e8f0; border-radius:6px; padding:1px 8px; font-size:.75rem; font-family:monospace; }
      .pre-badge { background:#1a2340; color:#cbd5e1; border-radius:6px; padding:1px 8px; font-size:.75rem; font-family:monospace; }
      .score { font-family:monospace; font-size:1.6rem; font-weight:700; text-align:right; line-height:1.9; }
      .score.win { color:#6ee7b7; }
      .score.changed { color:#fbbf24; }
      .team-name { font-weight:600; line-height:1.15; padding-top:4px; }
      .team-name small { color:#8b94b3; font-weight:500; }
      .loser { opacity:.55; }
      @keyframes blink { 50% { opacity:.65; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏟️ Live Sports Tracker")

# ------------------------------------------------------------- Controls
league = st.segmented_control(
    "League",
    options=list(LEAGUES),
    format_func=lambda k: f"{LEAGUES[k]['icon']} {k}",
    key="league",
    label_visibility="collapsed",
)
if league is None:  # user clicked the selected pill again to deselect it
    league = "NFL"


def shift_day(days: int) -> None:
    ss.day = ss.day + timedelta(days=days)


def reset_day() -> None:
    ss.day = date.today()


c_prev, c_date, c_next, c_today, c_filter, c_search = st.columns([0.5, 1.4, 0.5, 0.8, 2.6, 2])
c_prev.button("‹", on_click=shift_day, args=(-1,), width="stretch", help="Previous day")
c_date.date_input("Date", key="day", label_visibility="collapsed")
c_next.button("›", on_click=shift_day, args=(1,), width="stretch", help="Next day")
c_today.button("Today", on_click=reset_day, width="stretch")
status_filter = c_filter.radio(
    "Show", ["All", "Live", "Upcoming", "Final"], horizontal=True, label_visibility="collapsed"
)
query = c_search.text_input("Search", placeholder="Search teams…", label_visibility="collapsed").strip().lower()

auto = st.toggle(f"Auto-refresh every {REFRESH_SECONDS}s", value=ss.day == date.today())

FILTER_STATE = {"Live": "in", "Upcoming": "pre", "Final": "post"}


# ------------------------------------------------------------ Rendering
def toggle_favorite(fav_key: str) -> None:
    ss.favorites.symmetric_difference_update({fav_key})


def badge(game: Game) -> str:
    if game.state == "in":
        return '<span class="live-badge">● LIVE</span>'
    if game.state == "post":
        return f'<span class="final-badge">{escape(game.detail or "Final")}</span>'
    return f'<span class="pre-badge">{game.start.astimezone().strftime("%I:%M %p").lstrip("0")}</span>'


def render_game(game: Game, changed: set[str]) -> None:
    pinned = any(f"{league}:{t.id}" in ss.favorites for t in game.teams)
    with st.container(border=True):
        left = "⭐ " if pinned else ""
        left += escape(game.detail) if game.state == "in" else ("Scheduled" if game.state == "pre" else "")
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;font-size:.8rem;color:#8b94b3;font-weight:600">'
            f"<span>{left}</span>{badge(game)}</div>",
            unsafe_allow_html=True,
        )
        has_winner = game.state == "post" and any(t.winner for t in game.teams)
        for team in game.teams:
            fav_key = f"{league}:{team.id}"
            dim = " loser" if has_winner and not team.winner else ""
            logo_col, name_col, score_col, star_col = st.columns([0.6, 3.2, 1.2, 0.6], vertical_alignment="center")
            if team.logo.startswith("http"):
                logo_col.image(team.logo, width=34)
            else:
                logo_col.markdown(f"**{escape(team.abbr[:3])}**")
            rank = f"<small>#{team.rank}</small> " if team.rank else ""
            poss = " 🏈" if game.is_live and game.possession == team.id else ""
            name_col.markdown(
                f'<div class="team-name{dim}">{rank}{escape(team.name)}{poss}<br><small>{escape(team.record)}</small></div>',
                unsafe_allow_html=True,
            )
            if game.state != "pre":
                cls = "changed" if f"{game.id}:{team.id}" in changed else ("win" if has_winner and team.winner else "")
                score_col.markdown(f'<div class="score {cls}{dim}">{escape(team.score)}</div>', unsafe_allow_html=True)
            star_col.button(
                "★" if fav_key in ss.favorites else "☆",
                key=f"fav_{game.id}_{team.id}",
                on_click=toggle_favorite,
                args=(fav_key,),
                help=f"{'Unpin' if fav_key in ss.favorites else 'Pin'} {team.name}",
            )

        if game.is_live and (game.down_distance or game.last_play):
            st.caption(" · ".join(x for x in (game.down_distance, game.last_play) if x))
        if game.state == "post" and game.headline:
            st.caption(f"*{game.headline}*")
        meta = [
            f"📍 {game.venue}" if game.venue else "",
            f"📺 {game.broadcast}" if game.broadcast else "",
            f"📊 {game.odds}" if game.state == "pre" and game.odds else "",
        ]
        if any(meta):
            st.caption(" · ".join(m for m in meta if m))


@st.fragment(run_every=REFRESH_SECONDS if auto else None)
def scoreboard() -> None:
    """Only this part reruns on the timer, so the controls above stay put."""
    try:
        games = get_games(league, ss.day)
    except Exception as err:
        st.error(f"📡 Couldn't load scores: {err}")
        if st.button("Retry"):
            get_games.clear()
            st.rerun(scope="fragment")
        return

    # Detect score changes since the last refresh
    changed = set()
    for g in games:
        for t in g.teams:
            key = f"{g.id}:{t.id}"
            prev = ss.prev_scores.get(key)
            if g.is_live and prev is not None and prev != t.score:
                changed.add(key)
            ss.prev_scores[key] = t.score

    live = sum(g.state == "in" for g in games)
    final = sum(g.state == "post" for g in games)
    upcoming = len(games) - live - final
    day_label = "Today" if ss.day == date.today() else f"{ss.day:%a, %b} {ss.day.day}"
    st.caption(
        f"**{day_label}:** {len(games)} games · 🔴 {live} live · {upcoming} upcoming · {final} final "
        f"· updated {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}"
    )
    if changed:
        st.toast(f"🔔 Score update in {len({k.split(':')[0] for k in changed})} game(s)!")

    shown = [
        g for g in games
        if (status_filter == "All" or g.state == FILTER_STATE[status_filter])
        and (not query or any(query in f"{t.name} {t.abbr}".lower() for t in g.teams))
    ]
    favs = {k.split(":", 1)[1] for k in ss.favorites if k.startswith(f"{league}:")}
    shown = sort_games(shown, favs)

    if not shown:
        if games:
            st.info("No games match this filter.")
        else:
            st.info(f"🗓️ No {league} games on {day_label}. The league may be in its off-season, so try another date or league.")
        return

    cols_per_row = 3
    for i in range(0, len(shown), cols_per_row):
        for col, game in zip(st.columns(cols_per_row), shown[i : i + cols_per_row]):
            with col:
                render_game(game, changed)


scoreboard()
st.caption("Data from ESPN's public scoreboard feed · ☆ a team to pin its games to the top")
