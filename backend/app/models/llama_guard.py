"""``Guardrail`` with Llama Guard 4 through the same ``ChatModel`` (AD-009, AD-054)."""

import re

from app.documents.domain.job_errors import TransientFailure
from app.models.chat_model import ChatModel, ChatRequest
from app.models.guardrail import GuardVerdict

GUARD_MAX_TOKENS = 20
VERDICT_ATTEMPTS = 3

# Llama Guard 4 names what it flagged as S1..S14 on the lines after ``unsafe``.
CATEGORY = re.compile(r"\bS\d{1,2}\b", re.IGNORECASE)


class LlamaGuard:
    """Asks the classifier about one text and reads its verdict and the categories it names.

    ``safe`` passes. ``unsafe`` blocks unless every category it names is in ``allowed``: the
    categories a person's own documents trip without being harmful (AD-054), such as S6
    (specialized advice: a lab report, a contract) or S7 (privacy: a name and an ID number).
    ``unsafe`` with no category blocks. A reply that is neither verdict (the model can emit
    noise on long inputs) is asked again, then raised as ``TransientFailure`` - never read as
    a verdict either way. Llama Guard classifies harmful content; it does not detect prompt
    injection, which the prompt delimiters handle.
    """

    def __init__(
        self, chat: ChatModel, model_id: str, allowed: frozenset[str] = frozenset()
    ) -> None:
        self._chat = chat
        self._model_id = model_id
        self._allowed = frozenset(category.upper() for category in allowed)

    async def is_safe(self, text: str) -> bool:
        """True for ``safe``, or ``unsafe`` naming only allowed categories."""
        return (await self.check(text)).safe

    async def check(self, text: str) -> GuardVerdict:
        """The verdict with the categories named, so a rejection can say what was flagged."""
        request = ChatRequest(
            model=self._model_id,
            messages=[{"role": "user", "content": text}],
            max_tokens=GUARD_MAX_TOKENS,
        )

        for _ in range(VERDICT_ATTEMPTS):
            lines = _lines(await self._chat.complete(request))
            verdict = lines[0] if lines else ""

            if verdict == "safe":
                return GuardVerdict(safe=True)
            if verdict.startswith("unsafe"):
                categories = _categories(lines)
                return GuardVerdict(self._only_allowed(categories), frozenset(categories))

        raise TransientFailure("guardrail verdict unreadable")

    def _only_allowed(self, categories: set[str]) -> bool:
        return bool(categories) and categories <= self._allowed


def _lines(reply: str) -> list[str]:
    return [line.strip().lower() for line in reply.strip().splitlines() if line.strip()]


def _categories(lines: list[str]) -> set[str]:
    return {match.upper() for line in lines for match in CATEGORY.findall(line)}
