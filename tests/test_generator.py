import pytest

from flashcards.generator import cloze, from_copula, from_delimited, generate_offline, parse_cards

NOTES = """Photosynthesis: the process plants use to convert light energy into chemical energy.
Chlorophyll is the green pigment in chloroplasts that absorbs light.
Stomata are small pores on leaves that let carbon dioxide in and oxygen out.
The Calvin cycle occurs in the stroma and uses ATP to fix carbon dioxide into sugar."""


def test_delimited_definition():
    card = from_delimited("Mitosis: cell division that produces two identical cells")
    assert card == {"q": "What is Mitosis?", "a": "Cell division that produces two identical cells"}


def test_copula_plural_subject():
    card = from_copula("Stomata are small pores on leaves that let gases through.")
    assert card["q"] == "What are Stomata?"
    assert card["a"].startswith("Small pores")


def test_cloze_prefers_numbers_and_proper_nouns():
    card = cloze("The war ended in 1918 after four long years.")
    assert card["a"] == "1918"
    assert "_____" in card["q"]
    assert cloze("The Treaty of Versailles was signed after the war.")["a"] == "Versailles"


def test_offline_generation_has_no_duplicates_and_respects_count():
    cards = generate_offline(NOTES, 5)
    assert len(cards) == 5
    assert len({c["q"] for c in cards}) == len(cards)
    assert cards[0]["q"] == "What is Photosynthesis?"


def test_offline_generation_rejects_empty_material():
    with pytest.raises(ValueError):
        generate_offline("hi", 5)


def test_parse_cards_tolerates_fences_and_alt_keys():
    raw = '```json\n[{"question": "2+2?", "answer": "4"}, {"q": "", "a": "skip"}]\n```'
    assert parse_cards(raw) == [{"q": "2+2?", "a": "4"}]
