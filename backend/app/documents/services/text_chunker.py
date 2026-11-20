"""Split long text into pieces a single model call can take."""

SUMMARY_PIECE_CHARS = 300_000


def split_text(text: str, max_chars: int = SUMMARY_PIECE_CHARS) -> list[str]:
    """Cut ``text`` into consecutive pieces of at most ``max_chars`` characters.

    Text that fits is returned whole. A cut prefers the last line break of the window's final
    tenth, so a paragraph is rarely split; joined back, the pieces equal the input.
    """
    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            newline = text.rfind("\n", end - max_chars // 10, end)
            end = newline + 1 if newline > start else end
        pieces.append(text[start:end])
        start = end
    return pieces
