from datetime import date

from sports import espn


def make_event(event_id, state, home_score, away_score, winner_home=False):
    return {
        "id": event_id,
        "date": "2026-10-27T23:15Z",
        "status": {"type": {"state": state, "shortDetail": "Q3 4:12" if state == "in" else "Final"}},
        "competitions": [{
            "competitors": [
                {"homeAway": "home", "score": home_score, "winner": winner_home,
                 "team": {"id": "1", "displayName": "Kansas City Chiefs", "abbreviation": "KC", "logo": "kc.png"},
                 "records": [{"summary": "6-1"}]},
                {"homeAway": "away", "score": away_score,
                 "team": {"id": "2", "displayName": "Buffalo Bills", "abbreviation": "BUF"}},
            ],
            "venue": {"fullName": "Arrowhead Stadium", "address": {"city": "Kansas City"}},
            "broadcasts": [{"names": ["CBS"]}],
            "situation": {"possession": "1", "downDistanceText": "2nd & 7 at BUF 34"},
        }],
    }


def test_normalize_flattens_event():
    game = espn.normalize(make_event("a", "in", "24", "17"))
    assert game.is_live
    assert [t.abbr for t in game.teams] == ["BUF", "KC"]  # away team first
    assert game.teams[1].record == "6-1"
    assert game.venue == "Arrowhead Stadium, Kansas City"
    assert game.broadcast == "CBS"
    assert game.down_distance == "2nd & 7 at BUF 34"


def test_normalize_survives_missing_fields():
    game = espn.normalize({"id": "x"})
    assert game.state == "pre"
    assert game.teams == []


def test_sort_puts_favorites_then_live_first():
    live = espn.normalize(make_event("live", "in", "7", "3"))
    final = espn.normalize(make_event("final", "post", "21", "17", winner_home=True))
    upcoming = espn.normalize(make_event("pre", "pre", "0", "0"))
    assert [g.id for g in espn.sort_games([final, upcoming, live], set())] == ["live", "pre", "final"]
    final.teams[0].id = "fav"
    assert espn.sort_games([final, upcoming, live], {"fav"})[0].id == "final"


def test_fetch_scoreboard_builds_request(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"events": [make_event("a", "post", "21", "17", True)]}

    def fake_get(url, params, timeout):
        captured.update(url=url, params=params)
        return FakeResponse()

    monkeypatch.setattr(espn.requests, "get", fake_get)
    games = espn.fetch_scoreboard("NBA", date(2026, 10, 27))
    assert "basketball/nba" in captured["url"]
    assert captured["params"]["dates"] == "20261027"
    assert games[0].teams[1].winner
