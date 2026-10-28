import re

# Stock phrases that make food captions read as generic. Drafters are told to
# avoid them, and the draft guardrail sends a draft back if one slips through.
BANNED_PHRASES: tuple[str, ...] = (
    "mouthwatering",
    "mouth-watering",
    "indulge",
    "treat yourself",
    "taste buds",
    "tantalizing",
    "delectable",
    "look no further",
    "elevate your",
    "culinary journey",
    "culinary delight",
    "feast your eyes",
    "who's hungry",
    "craving something",
    "nothing beats",
    "perfect for any occasion",
    "a symphony of",
    "burst of flavor",
    "flavor explosion",
    "you won't want to miss",
    "game changer",
    "next level",
    "sure to please",
)


# Phrases that describe the photo instead of the food ("our kind of close-up",
# "the plate fills the frame"). Checked by the draft guardrail.
PHOTO_PHRASES: tuple[str, ...] = (
    "close-up",
    "closeup",
    "this photo",
    "this picture",
    "this shot",
    "this image",
    "the frame",
    "in frame",
    "pictured",
    "composition",
)


def _find(phrases: tuple[str, ...], text: str) -> list[str]:
    lowered = text.lower().replace("’", "'")
    return [
        phrase
        for phrase in phrases
        if re.search(rf"\b{re.escape(phrase)}\b", lowered)
    ]


def find_banned_phrases(text: str) -> list[str]:
    """Return the banned phrases that appear in text (case-insensitive)."""
    return _find(BANNED_PHRASES, text)


def find_photo_phrases(text: str) -> list[str]:
    """Return phrases that talk about the photo itself rather than the food."""
    return _find(PHOTO_PHRASES, text)
