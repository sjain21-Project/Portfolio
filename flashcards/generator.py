"""Flashcard generation.

- generate_with_ai(): asks Claude to write cards and parses its JSON reply.
- generate_offline(): a heuristic generator that needs no API key or network.
"""
from __future__ import annotations

import json
import re

DEFAULT_MODEL = "claude-haiku-5-5"

Card = dict[str, str]  # {"q": "...", "a": "..."}


# --------------------------------------------------------------------------- AI


def build_prompt(text: str, count: int, difficulty: str) -> str:
    is_topic = len(text.split()) < 12
    task = (
        f'Create {count} flashcards that teach the topic: "{text.strip()}".'
        if is_topic
        else f"Create {count} flashcards from the study material below."
    )
    material = "" if is_topic else f"\n<material>\n{text.strip()}\n</material>"
    return f"""You are an expert teacher who writes excellent study flashcards.

{task}

Rules:
- Difficulty level: {difficulty}.
- Each card tests exactly ONE idea. Questions must be specific and unambiguous.
- Answers are short (ideally under 25 words) but complete.
- Mix question styles: definitions, "why/how", cause and effect, comparisons, examples.
- Respond with ONLY a JSON array, no markdown fences, in this exact shape:
[{{"q": "question text", "a": "answer text"}}]
{material}"""


def parse_cards(raw: str) -> list[Card]:
    """Pull the JSON array out of the model's reply, tolerating stray fences or text."""
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("The AI response did not contain a card list.")
    items = json.loads(raw[start : end + 1])
    cards = []
    for item in items:
        if not isinstance(item, dict):
            continue
        q = item.get("q") or item.get("question")
        a = item.get("a") or item.get("answer")
        if q and a:
            cards.append({"q": str(q).strip(), "a": str(a).strip()})
    return cards


def generate_with_ai(text: str, count: int, difficulty: str, api_key: str, model: str = DEFAULT_MODEL) -> list[Card]:
    import anthropic  # imported lazily so offline mode works without the package

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": build_prompt(text, count, difficulty)}],
    )
    raw = "".join(block.text for block in message.content if block.type == "text")
    cards = parse_cards(raw)
    if not cards:
        raise ValueError("The AI returned no usable cards.")
    return cards[:count]


# ---------------------------------------------------------------------- Offline

STOP_WORDS = set(
    """the a an and or but of to in on for with by as at from is are was were be been being this that
    these those it its into than then there their which who whom whose what when where why how also such
    can may might will would should could has have had do does did not no very more most other some any
    each all both""".split()
)

_BULLET = re.compile(r"^[\s\-•*\d.)]+")
_DELIMITED = re.compile(r"^([A-Z][\w\s'()/-]{1,50}?)\s*(?::|—|–|\s-\s)\s*(.{8,})$")
_COPULA = re.compile(
    r"^(.{3,70}?)\s+(is defined as|is known as|refers to|consists of|means|is|are|was|were)\s+(.{8,})$",
    re.IGNORECASE,
)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.replace("\r", ""))
    cleaned = (_BULLET.sub("", p).strip() for p in parts)
    return [s for s in cleaned if len(s) > 15 and len(s.split()) >= 4]


def from_delimited(line: str) -> Card | None:
    """'Term: definition' or 'Term - definition'."""
    m = _DELIMITED.match(line)
    if not m:
        return None
    return {"q": f"What is {m.group(1).strip()}?", "a": _cap(m.group(2).strip())}


def from_copula(sentence: str) -> Card | None:
    """'X is/are/means/refers to Y'."""
    m = _COPULA.match(sentence)
    if not m:
        return None
    subject = re.sub(r"^(the|a|an)\s+", "", m.group(1), flags=re.IGNORECASE).strip()
    if len(subject.split()) > 8:
        return None
    verb = m.group(2).lower()
    if verb == "consists of":
        q = f"What does {subject} consist of?"
    elif verb in ("are", "were"):
        q = f"What are {subject}?"
    elif verb == "was":
        q = f"What was {subject}?"
    else:
        q = f"What is {subject}?"
    return {"q": q, "a": _cap(m.group(3).rstrip(".;"))}


def cloze(sentence: str) -> Card | None:
    """Fill-in-the-blank: hide the most important-looking word."""
    words = sentence.split()
    best_idx, best_score = -1, 0
    for i, word in enumerate(words):
        clean = re.sub(r"[^\w'-]", "", word)
        if not clean or clean.lower() in STOP_WORDS:
            continue
        score = len(clean)
        if re.fullmatch(r"\d[\d,.%]*", clean):
            score += 8  # numbers and dates make good blanks
        if i > 0 and clean[0].isupper():
            score += 6  # proper nouns mid-sentence
        if score > best_score:
            best_idx, best_score = i, score
    if best_idx == -1 or best_score < 5:
        return None
    answer = re.sub(r"[^\w'-]", "", words[best_idx])
    words[best_idx] = words[best_idx].replace(answer, "_____", 1)
    return {"q": "Fill in the blank:\n" + " ".join(words), "a": answer}


def generate_offline(text: str, count: int) -> list[Card]:
    cards: list[Card] = []
    seen: set[str] = set()
    used: set[str] = set()

    def push(card: Card | None) -> bool:
        if card and card["q"].lower() not in seen:
            seen.add(card["q"].lower())
            cards.append(card)
            return True
        return False

    for raw_line in text.splitlines():
        line = _BULLET.sub("", raw_line).strip()
        if line and push(from_delimited(line)):
            used.add(line)

    sentences = split_sentences(text)
    for s in sentences:
        if s not in used and push(from_copula(s)):
            used.add(s)

    # Prefer cloze cards from sentences that didn't already become a definition
    ordered = [s for s in sentences if s not in used] + [s for s in sentences if s in used]
    for s in ordered:
        if len(cards) >= count:
            break
        push(cloze(s))

    if not cards:
        raise ValueError(
            "Not enough material for offline mode. Paste a few sentences of notes, "
            "or add an API key to generate from a topic."
        )
    return cards[:count]
