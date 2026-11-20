"""Make an uploaded filename safe to display; it never becomes a storage key."""

import unicodedata

MAX_FILENAME_CHARS = 255
FALLBACK_NAME = "document.pdf"


def clean_filename(raw: str | None) -> str:
    """Drop path parts and control characters, then cut to 255 characters.

    ``../../etc/passwd.pdf`` becomes ``passwd.pdf``; an empty result becomes ``document.pdf``.
    """
    name = (raw or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(char for char in name if unicodedata.category(char)[0] != "C")
    name = name.strip()[:MAX_FILENAME_CHARS]
    return name if name not in {"", ".", ".."} else FALLBACK_NAME
