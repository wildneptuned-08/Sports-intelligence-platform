from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert arbitrary text to a URL-safe slug.

    Examples:
        "Real Madrid" → "real-madrid"
        "FC Barcelona" → "fc-barcelona"
        "Atlético de Madrid" → "atletico-de-madrid"
    """
    # Normalize unicode (decompose accented chars → base + combining)
    text = unicodedata.normalize("NFKD", text)
    # Drop non-ASCII characters (removes combining diacritics)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Remove characters that are not alphanumeric, whitespace, or hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    # Replace whitespace / underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Collapse consecutive hyphens
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
