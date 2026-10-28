"""Fetch and normalize scoreboards from ESPN's public JSON feed (no API key needed)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

import requests

LEAGUES: dict[str, dict[str, str]] = {
    "NFL": {"icon": "🏈", "path": "football/nfl"},
    "NBA": {"icon": "🏀", "path": "basketball/nba"},
    "MLB": {"icon": "⚾", "path": "baseball/mlb"},
    "NHL": {"icon": "🏒", "path": "hockey/nhl"},
    "WNBA": {"icon": "🏀", "path": "basketball/wnba"},
    "NCAAF": {"icon": "🏈", "path": "football/college-football"},
    "MLS": {"icon": "⚽", "path": "soccer/usa.1"},
    "EPL": {"icon": "⚽", "path": "soccer/eng.1"},
}

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"


@dataclass
class Team:
    id: str
    name: str
    abbr: str
    logo: str
    score: str
    home_away: str
    record: str = ""
    rank: int | None = None
    winner: bool = False


@dataclass
class Game:
    id: str
    start: datetime
    state: str  # "pre" | "in" | "post"
    detail: str
    teams: list[Team] = field(default_factory=list)
    venue: str = ""
    broadcast: str = ""
    possession: str | None = None
    down_distance: str = ""
    last_play: str = ""
    headline: str = ""
    odds: str = ""

    @property
    def is_live(self) -> bool:
        return self.state == "in"


def _parse_date(iso: str) -> datetime:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def normalize(event: dict) -> Game:
    """Flatten ESPN's deeply nested event into a simple Game object."""
    comp = (event.get("competitions") or [{}])[0]
    status_type = (event.get("status") or comp.get("status") or {}).get("type", {})

    teams = []
    for c in comp.get("competitors", []):
        t = c.get("team", {})
        rank = (c.get("curatedRank") or {}).get("current")
        teams.append(
            Team(
                id=str(t.get("id") or c.get("id", "")),
                name=t.get("displayName") or t.get("name") or "TBD",
                abbr=t.get("abbreviation", ""),
                logo=t.get("logo") or ((t.get("logos") or [{}])[0].get("href", "")),
                score=str(c.get("score", "")),
                home_away=c.get("homeAway", ""),
                record=((c.get("records") or [{}])[0]).get("summary", ""),
                rank=rank if isinstance(rank, int) and rank <= 25 else None,
                winner=bool(c.get("winner")),
            )
        )
    teams.sort(key=lambda t: t.home_away != "away")  # away team on top, like a scoreboard

    venue = comp.get("venue") or {}
    city = (venue.get("address") or {}).get("city", "")
    situation = comp.get("situation") or {}

    return Game(
        id=str(event.get("id", "")),
        start=_parse_date(event.get("date", "")),
        state=status_type.get("state", "pre"),
        detail=status_type.get("shortDetail") or status_type.get("detail", ""),
        teams=teams,
        venue=", ".join(x for x in (venue.get("fullName", ""), city) if x),
        broadcast=", ".join(n for b in comp.get("broadcasts", []) for n in b.get("names", [])),
        possession=situation.get("possession"),
        down_distance=situation.get("downDistanceText", ""),
        last_play=(situation.get("lastPlay") or {}).get("text", ""),
        headline=((comp.get("headlines") or [{}])[0]).get("shortLinkText", ""),
        odds=((comp.get("odds") or [{}])[0]).get("details", ""),
    )


def fetch_scoreboard(league: str, day: date, timeout: float = 10) -> list[Game]:
    url = BASE_URL.format(path=LEAGUES[league]["path"])
    resp = requests.get(url, params={"dates": day.strftime("%Y%m%d"), "limit": 200}, timeout=timeout)
    resp.raise_for_status()
    return [normalize(e) for e in resp.json().get("events", [])]


STATE_ORDER = {"in": 0, "pre": 1, "post": 2}


def sort_games(games: list[Game], favorites: set[str]) -> list[Game]:
    """Favorites first, then live, upcoming, final; then by start time."""
    def key(g: Game):
        pinned = any(t.id in favorites for t in g.teams)
        return (not pinned, STATE_ORDER.get(g.state, 3), g.start)
    return sorted(games, key=key)
