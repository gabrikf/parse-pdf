"""``Guardrail`` with Llama Guard 4 through the same ``ChatModel`` (AD-009)."""

from app.documents.domain.job_errors import TransientFailure
from app.models.chat_model import ChatModel, ChatRequest

GUARD_MAX_TOKENS = 20
VERDICT_ATTEMPTS = 3


class LlamaGuard:
    """Asks the classifier about one text and reads its first line: ``safe`` or ``unsafe``.

    A reply that is neither (the model can emit noise on long inputs) is asked again, then
    raised as ``TransientFailure`` - never read as a verdict either way. Llama Guard classifies
    harmful content; it does not detect prompt injection, which the prompt delimiters handle.
    """

    def __init__(self, chat: ChatModel, model_id: str) -> None:
        self._chat = chat
        self._model_id = model_id

    async def is_safe(self, text: str) -> bool:
        """True for ``safe``, False for ``unsafe``."""
        request = ChatRequest(
            model=self._model_id,
            messages=[{"role": "user", "content": text}],
            max_tokens=GUARD_MAX_TOKENS,
        )
        for _ in range(VERDICT_ATTEMPTS):
            verdict = _first_line(await self._chat.complete(request))
            if verdict == "safe":
                return True
            if verdict.startswith("unsafe"):
                return False
        raise TransientFailure("guardrail verdict unreadable")


def _first_line(reply: str) -> str:
    lines = [line.strip().lower() for line in reply.strip().splitlines() if line.strip()]
    return lines[0] if lines else ""
