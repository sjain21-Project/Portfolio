"""Save and load decks as a JSON file, plus CSV/JSON export helpers."""
from __future__ import annotations

import csv
import io
import json
import time
import uuid
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "decks.json"


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def make_deck(name: str, cards: list[dict], source: str) -> dict:
    return {
        "id": new_id(),
        "name": name,
        "source": source,
        "created": time.time(),
        "cards": [{"id": new_id(), "q": c["q"], "a": c["a"], "known": False} for c in cards],
    }


def load_decks(path: Path = DATA_FILE) -> list[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_decks(decks: list[dict], path: Path = DATA_FILE) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(decks, indent=2), encoding="utf-8")
    except OSError:
        pass  # read-only hosting: decks still live in the session


def to_json(deck: dict) -> str:
    return json.dumps({"name": deck["name"], "cards": [{"q": c["q"], "a": c["a"]} for c in deck["cards"]]}, indent=2)


def to_csv(deck: dict) -> str:
    """Two-column CSV that imports straight into Anki or Quizlet."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    for c in deck["cards"]:
        writer.writerow([c["q"], c["a"]])
    return buf.getvalue()


def from_json(raw: str, fallback_name: str) -> dict:
    data = json.loads(raw)
    items = data if isinstance(data, list) else data.get("cards", [])
    cards = [c for c in items if isinstance(c, dict) and c.get("q") and c.get("a")]
    if not cards:
        raise ValueError("No cards found in that file.")
    name = data.get("name", fallback_name) if isinstance(data, dict) else fallback_name
    return make_deck(name, cards, "import")
