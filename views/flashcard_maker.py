"""AI Flashcard Maker page."""
import os
import random
import re
from html import escape

import pandas as pd
import streamlit as st

from flashcards import storage
from flashcards.generator import DEFAULT_MODEL, generate_offline, generate_with_ai

SAMPLE = """Photosynthesis: the process plants use to convert light energy into chemical energy stored in glucose.
Chlorophyll is the green pigment in chloroplasts that absorbs light, mostly red and blue wavelengths.
The light-dependent reactions take place in the thylakoid membranes and produce ATP and NADPH.
The Calvin cycle occurs in the stroma and uses ATP and NADPH to fix carbon dioxide into sugar.
Stomata are small pores on leaves that let carbon dioxide in and oxygen out.
Oxygen released during photosynthesis comes from splitting water molecules.
The overall equation turns 6 molecules of carbon dioxide and 6 molecules of water into one glucose molecule.
Cellular respiration is the reverse process, in which cells break down glucose to release usable energy."""

CARD_CSS = """
<style>
.flashcard { border-radius: 20px; min-height: 280px; padding: 40px 32px; display: flex; flex-direction: column;
  justify-content: center; align-items: center; text-align: center; box-shadow: 0 18px 40px rgba(0,0,0,.35); position: relative; }
.flashcard.front { background: #f8fafc; color: #0b1020; }
.flashcard.back { background: linear-gradient(135deg, #312e81, #4338ca); color: #fff; }
.flashcard .label { position: absolute; top: 14px; left: 20px; font-size: .72rem; letter-spacing: .1em;
  text-transform: uppercase; opacity: .55; font-weight: 700; }
.flashcard p { font-size: 1.45rem; font-weight: 600; white-space: pre-wrap; margin: 0; }
</style>
"""

# ------------------------------------------------------------------ State
ss = st.session_state
ss.setdefault("decks", storage.load_decks())
ss.setdefault("mode", "create")  # create | edit | study
ss.setdefault("deck_id", None)
ss.setdefault("source_text", "")
ss.setdefault("deck_name", "")


def persist() -> None:
    storage.save_decks(ss.decks)


def current_deck() -> dict | None:
    return next((d for d in ss.decks if d["id"] == ss.deck_id), None)


def go(mode: str, deck_id: str | None = None) -> None:
    ss.mode = mode
    if deck_id:
        ss.deck_id = deck_id


def start_study(deck_id: str, only_ids: list[str] | None = None) -> None:
    deck = next(d for d in ss.decks if d["id"] == deck_id)
    ss.deck_id = deck_id
    ss.queue = [c["id"] for c in deck["cards"] if only_ids is None or c["id"] in only_ids]
    ss.pos, ss.flipped, ss.missed, ss.round_done, ss.celebrated = 0, False, set(), False, False
    ss.mode = "study"


def load_sample() -> None:
    ss.source_text = SAMPLE
    if not ss.deck_name:
        ss.deck_name = "Biology – Photosynthesis"


# ---------------------------------------------------------------- Sidebar
with st.sidebar:
    st.subheader("⚙️ AI settings")
    default_key = ""
    try:
        default_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:  # no secrets file
        pass
    default_key = default_key or os.environ.get("ANTHROPIC_API_KEY", "")
    api_key = st.text_input(
        "Anthropic API key",
        value=default_key,
        type="password",
        help="Used only for this session. Leave blank to use offline mode.",
    )
    model = st.text_input("Model", value=DEFAULT_MODEL)
    if api_key:
        st.success("🤖 AI mode: Claude writes your cards.")
    else:
        st.info("⚡ Offline mode: cards are extracted from your notes. Add a key for AI-written cards and topic-only generation.")

st.title("🧠 AI Flashcard Maker")


# ================================================================= CREATE
def create_view() -> None:
    with st.container(border=True):
        st.subheader("Create a deck")
        st.text_input("Deck name", key="deck_name", placeholder="e.g. Biology – Cell Structure")
        st.text_area(
            "Paste your notes or type a topic",
            key="source_text",
            height=220,
            placeholder="Paste lecture notes, a textbook passage, or just a topic like 'The French Revolution'…",
        )
        c1, c2 = st.columns(2)
        count = c1.number_input("Number of cards", min_value=3, max_value=40, value=10)
        difficulty = c2.select_slider("Difficulty", ["beginner", "intermediate", "advanced"], value="intermediate")

        b1, b2, _ = st.columns([1.3, 1, 3])
        generate = b1.button("✨ Generate flashcards", type="primary", width="stretch")
        b2.button("Try sample notes", on_click=load_sample, width="stretch")

        if generate:
            text = ss.source_text.strip()
            if not text:
                st.error("Paste some notes or type a topic first.")
            else:
                cards, source = None, "offline"
                if api_key:
                    with st.spinner("Claude is writing your flashcards…"):
                        try:
                            cards = generate_with_ai(text, int(count), difficulty, api_key, model)
                            source = "ai"
                        except Exception as err:  # bad key, rate limit, network…
                            st.warning(f"AI failed ({err}). Falling back to offline mode.")
                if cards is None:
                    try:
                        cards = generate_offline(text, int(count))
                    except ValueError as err:
                        st.error(str(err))
                if cards:
                    first = re.split(r"[\n.:]", text)[0].strip()
                    name = ss.deck_name.strip() or (first if 3 < len(first) < 50 else f"Deck {len(ss.decks) + 1}")
                    deck = storage.make_deck(name, cards, source)
                    ss.decks.append(deck)
                    persist()
                    go("edit", deck["id"])
                    st.rerun()

    with st.container(border=True):
        head, upload = st.columns([3, 2])
        head.subheader("My decks")
        file = upload.file_uploader("Import a JSON deck", type="json", label_visibility="collapsed")
        if file is not None and ss.get("last_import") != file.file_id:
            ss.last_import = file.file_id
            try:
                deck = storage.from_json(file.getvalue().decode("utf-8"), file.name.removesuffix(".json"))
                ss.decks.append(deck)
                persist()
                st.success(f"Imported “{deck['name']}” ({len(deck['cards'])} cards).")
            except Exception as err:
                st.error(f"Import failed: {err}")

        if not ss.decks:
            st.caption("No decks yet. Generate your first one above!")
        for deck in sorted(ss.decks, key=lambda d: d["created"], reverse=True):
            total = len(deck["cards"])
            known = sum(c["known"] for c in deck["cards"])
            badge = {"ai": "🤖 AI", "offline": "⚡ Offline", "import": "📥 Imported"}.get(deck["source"], "")
            with st.container(border=True):
                info, b1, b2, b3 = st.columns([4, 1, 1, 1])
                info.markdown(f"**{escape(deck['name'])}**  \n{total} cards · {badge}")
                info.progress(known / total if total else 0, text=f"{known}/{total} mastered")
                b1.button("Study", key=f"s{deck['id']}", type="primary", width="stretch",
                          on_click=start_study, args=(deck["id"],), disabled=not total)
                b2.button("Edit", key=f"e{deck['id']}", width="stretch", on_click=go, args=("edit", deck["id"]))
                if b3.button("Delete", key=f"d{deck['id']}", width="stretch"):
                    ss.decks = [d for d in ss.decks if d["id"] != deck["id"]]
                    persist()
                    st.rerun()


# =================================================================== EDIT
def edit_view(deck: dict) -> None:
    st.subheader(f"✏️ {deck['name']}")
    st.caption("Edit any cell, add rows at the bottom, or select rows and press Delete. Then save.")

    df = pd.DataFrame([{"Question": c["q"], "Answer": c["a"]} for c in deck["cards"]], columns=["Question", "Answer"])
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key=f"editor_{deck['id']}_{ss.get('editor_version', 0)}",
        column_config={
            "Question": st.column_config.TextColumn(width="large", required=True),
            "Answer": st.column_config.TextColumn(width="large", required=True),
        },
    )

    def save_edits() -> None:
        old = {(c["q"], c["a"]): c for c in deck["cards"]}
        new_cards = []
        for row in edited.fillna("").itertuples(index=False):
            q, a = str(row.Question).strip(), str(row.Answer).strip()
            if q and a:
                prev = old.get((q, a))
                new_cards.append(prev or {"id": storage.new_id(), "q": q, "a": a, "known": False})
        deck["cards"] = new_cards
        persist()
        ss.editor_version = ss.get("editor_version", 0) + 1  # fresh editor so saved rows aren't re-applied

    c1, c2, c3, c4, c5 = st.columns(5)
    if c1.button("💾 Save", type="primary", width="stretch"):
        save_edits()
        st.toast("Deck saved")
        st.rerun()
    if c2.button("Save & study ▶", width="stretch"):
        save_edits()
        if deck["cards"]:
            start_study(deck["id"])
            st.rerun()
    slug = re.sub(r"[^a-z0-9]+", "-", deck["name"].lower()).strip("-") or "deck"
    c3.download_button("Export JSON", storage.to_json(deck), f"{slug}.json", "application/json", width="stretch")
    c4.download_button("Export CSV", storage.to_csv(deck), f"{slug}.csv", "text/csv", width="stretch",
                       help="Imports straight into Anki or Quizlet")
    c5.button("← All decks", on_click=go, args=("create",), width="stretch")


# ================================================================== STUDY
def study_view(deck: dict) -> None:
    cards = {c["id"]: c for c in deck["cards"]}
    ss.queue = [cid for cid in ss.queue if cid in cards]
    if not ss.queue:
        go("create")
        st.rerun()

    top_l, top_m, top_r = st.columns([1, 3, 1])
    top_l.button("← Done", on_click=go, args=("create",), width="stretch")
    top_m.markdown(f"<h3 style='text-align:center;margin:0'>{escape(deck['name'])}</h3>", unsafe_allow_html=True)
    if top_r.button("🔀 Shuffle", width="stretch"):
        random.shuffle(ss.queue)
        ss.pos, ss.flipped = 0, False
        st.rerun()

    known_total = sum(c["known"] for c in deck["cards"])

    if ss.round_done:
        st.progress(1.0)
        if not ss.missed and not ss.get("celebrated"):
            ss.celebrated = True
            st.balloons()
        with st.container(border=True):
            st.subheader("🎉 Round complete!")
            if ss.missed:
                st.write(f"You marked **{len(ss.missed)}** card(s) as still learning. Deck mastery: {known_total}/{len(cards)}.")
            else:
                st.write(f"Perfect round! Deck mastery: {known_total}/{len(cards)}.")
            a, b, _ = st.columns([1, 1, 2])
            if ss.missed:
                a.button("Review missed cards", type="primary", on_click=start_study,
                         args=(deck["id"], list(ss.missed)), width="stretch")
            b.button("Restart full deck", on_click=start_study, args=(deck["id"],), width="stretch")
        return

    card = cards[ss.queue[ss.pos]]
    st.progress(ss.pos / len(ss.queue), text=f"Card {ss.pos + 1} of {len(ss.queue)} · {known_total}/{len(cards)} mastered")

    st.markdown(CARD_CSS, unsafe_allow_html=True)
    side, label, text = ("back", "Answer", card["a"]) if ss.flipped else ("front", "Question", card["q"])
    st.markdown(
        f'<div class="flashcard {side}"><span class="label">{label}</span><p>{escape(text)}</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    def move(delta: int) -> None:
        nxt = ss.pos + delta
        if nxt < 0:
            return
        if nxt >= len(ss.queue):
            ss.round_done = True
        else:
            ss.pos, ss.flipped = nxt, False

    def mark(known: bool) -> None:
        card["known"] = known
        (ss.missed.discard if known else ss.missed.add)(card["id"])
        persist()
        move(1)

    def flip() -> None:
        ss.flipped = not ss.flipped

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.button("← Prev", on_click=move, args=(-1,), width="stretch", disabled=ss.pos == 0)
    c2.button("✗ Still learning", on_click=mark, args=(False,), width="stretch")
    c3.button("🔄 Flip", on_click=flip, type="primary", width="stretch")
    c4.button("✓ Got it", on_click=mark, args=(True,), width="stretch")
    c5.button("Next →", on_click=move, args=(1,), width="stretch")


# ================================================================ ROUTER
deck = current_deck()
if ss.mode == "edit" and deck:
    edit_view(deck)
elif ss.mode == "study" and deck and "queue" in ss:
    study_view(deck)
else:
    create_view()
