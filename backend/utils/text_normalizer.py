"""
Utility functions to normalize free-text medicine names before fuzzy matching.

Whisper output and CSV entries can differ in case, spacing, and punctuation
("Panadol", "panadol ", "PANADOL,"). Normalizing both sides before comparison
gives RapidFuzz a fair, consistent input.
"""

import re
from typing import Optional

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCTUATION_RE = re.compile(r"[^\w\s%./-]")


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation noise, and collapse whitespace."""
    if not text:
        return ""
    text = text.strip().lower()
    text = _PUNCTUATION_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def is_empty(text: str) -> bool:
    """True if, after normalization, there is no usable content."""
    return len(normalize_text(text)) == 0


# Words a doctor commonly says alongside a medicine name that carry NO
# disambiguating value (frequency, timing/instructions, filler). Stripping
# ONLY these before fuzzy-matching keeps the search focused, without
# discarding strength/form words.
#
# NOTE: unit words (mg, ml, ...) and form words (tablet, capsule, ...) are
# deliberately NOT in this set. They're what distinguish "Panadol 500 mg
# Tablets" from "Panadol 15 ml Drops" or "Panadol 500 mg Injections" — a
# catalog commonly has several products that share a brand name but differ
# only in strength/form. Stripping them collapses all of those into one
# bare word (e.g. "panadol"), which then scores a false near-100% match
# against every variant and makes genuinely different products look tied,
# even when the doctor explicitly said which one they meant.
_FREQUENCY_INSTRUCTION_WORDS = {
    "once", "twice", "thrice", "daily", "day", "days", "week", "weeks",
    "month", "months", "hour", "hours",
    "morning", "evening", "night", "noon", "afternoon", "bedtime",
    "before", "after", "meal", "meals", "food", "eating", "empty", "stomach",
    "water", "sleep",
    "time", "times", "dose", "doses", "please", "give", "prescribe",
    "take", "a", "an", "the", "of", "per", "for", "with", "and", "to",
    "in", "on", "at", "as", "needed", "every",
}


_QUANTITY_RE = re.compile(
    r"\b(\d+(?:[./]\d+)?)\s*"
    r"(mg|mcg|ml|g|gram|grams|milligram|milligrams|iu|units?)\b",
    re.IGNORECASE,
)


def extract_quantity(text: str) -> str:
    """
    Pull out a spoken dosage quantity, e.g. "500 mg" from
    "Panadol 500 mg twice daily". Returns "" if none is found.
    Preserves the unit as spoken (not lowercased) for display purposes.
    """
    if not text:
        return ""
    match = _QUANTITY_RE.search(text)
    if not match:
        return ""
    number, unit = match.group(1), match.group(2)
    return f"{number}{unit.lower()}" if len(unit) <= 2 else f"{number} {unit.lower()}"


# Ordered (specific-first) mapping from words found in a medicine's name/form
# to the everyday unit a doctor would prescribe it in. Order matters: more
# specific words are checked before generic ones.
_FORM_UNIT_RULES = [
    (("injection", "injections", "infusion"), "injection"),
    (("drop", "drops", "suspension", "syrup", "lotion", "lotions", "liquid", "liquids"), "bottle"),
    (("cream", "ointment", "gel"), "tube"),
    (("spray",), "bottle"),
    (("capsule", "capsules"), "capsule"),
    (("tablet", "tablets"), "tablet"),
]


def guess_quantity_unit(medicine_name: str) -> str:
    """
    Infer a sensible default quantity for a medicine from its name/form,
    e.g. "Panadol 15 ml Drops" -> "1 bottle", "... Injections" -> "1 injection".
    Falls back to "1 unit" when the form can't be determined.
    """
    words = set(normalize_text(medicine_name).split())
    for form_words, unit in _FORM_UNIT_RULES:
        if words & set(form_words):
            return f"1 {unit}"
    return "1 unit"


_STRENGTH_RE = re.compile(
    r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu|%)"
    r"(?:\s*/\s*\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|iu))?)\b",
    re.IGNORECASE,
)

_FORM_WORDS = [
    "capsules", "capsule", "tablets", "tablet", "injections", "injection",
    "suspension", "syrup", "drops", "drop", "lotions", "lotion", "cream",
    "ointment", "gel", "spray", "infusion", "powder", "sachet", "sachets",
    "inhaler", "solution",
]


def parse_strength_and_form(item_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Best-effort extraction of strength and dosage form from a combined
    catalog name like "A-Flox 250 mg Capsules", used as a fallback when the
    source CSV doesn't provide separate strength/form columns.
    Returns (strength, form), either of which may be None.
    """
    if not item_name:
        return None, None

    strength_match = _STRENGTH_RE.search(item_name)
    strength = strength_match.group(1).strip() if strength_match else None
    if strength:
        strength = re.sub(r"\s+", " ", strength)
        strength = re.sub(r"\s*/\s*", "/", strength)

    form = None
    lower = item_name.lower()
    for word in _FORM_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            form = word.capitalize()
            break

    return strength, form


def extract_medicine_name_candidate(text: str) -> str:
    """
    Best-effort extraction of the medicine-name (+ strength/form) portion of
    a spoken phrase, e.g. "Panadol 500 mg twice daily" -> "panadol 500 mg".
    Strength and form words are kept (see _FREQUENCY_INSTRUCTION_WORDS
    comment) so this still lets voice input match the exact strength/form,
    just without frequency/instruction words diluting the score. Falls back
    to the full normalized text if stripping would remove everything.
    """
    normalized = normalize_text(text)
    if not normalized:
        return ""

    kept = [
        word
        for word in normalized.split()
        if word not in _FREQUENCY_INSTRUCTION_WORDS
    ]

    candidate = " ".join(kept).strip()
    return candidate if candidate else normalized
