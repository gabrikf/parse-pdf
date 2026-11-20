"""One summary per document: guarded, map-reduced when long, counted in the budget."""

from app.documents.domain.job_errors import PermanentFailure
from app.documents.domain.page import Page
from app.documents.services.guardrail_hint import GuardedText, guardrail_hint
from app.documents.services.prompt_builder import combine_messages, summary_messages
from app.documents.services.text_chunker import SUMMARY_PIECE_CHARS, split_text
from app.models.chat_model import ChatModel, ChatRequest
from app.models.guardrail import Guardrail
from app.rate_limit.model_budget import ModelBudget

GUARDRAIL_REJECTED = "guardrail_rejected"
# Llama Guard answers noise on very long inputs (seen live at 70k tokens); 20,000 characters
# (about 5k tokens) per check is read reliably.
GUARD_PIECE_CHARS = 20_000
SUMMARY_MAX_TOKENS = 1500


class SummaryService:
    """Writes the summary with the summary model (always Gemini, AD-003).

    Each input piece is checked by the guardrail before any summary call, and the summary is
    checked before it is returned; an ``unsafe`` verdict is permanent and never retried.
    """

    def __init__(
        self,
        chat: ChatModel,
        guardrail: Guardrail,
        budget: ModelBudget,
        model_id: str,
        piece_chars: int = SUMMARY_PIECE_CHARS,
    ) -> None:
        self._chat = chat
        self._guardrail = guardrail
        self._budget = budget
        self._model_id = model_id
        self._piece_chars = piece_chars

    async def summarize(self, pages: list[Page]) -> str:
        """Return the markdown summary of the pages' text."""
        text = "\n\n".join(page.content for page in pages)
        pieces = split_text(text, self._piece_chars)

        for piece in split_text(text, GUARD_PIECE_CHARS):
            await self._require_safe(piece, GuardedText.DOCUMENT)

        if len(pieces) == 1:
            summary = await self._ask(summary_messages(pieces[0]))
        else:
            partials = [await self._ask(summary_messages(piece)) for piece in pieces]
            summary = await self._ask(combine_messages(partials))

        await self._require_safe(summary, GuardedText.SUMMARY)
        await self._budget.add(1)
        return summary.strip()

    async def _ask(self, messages: list[dict[str, object]]) -> str:
        request = ChatRequest(
            model=self._model_id, messages=messages, max_tokens=SUMMARY_MAX_TOKENS
        )
        return await self._chat.complete(request)

    async def _require_safe(self, text: str, where: GuardedText) -> None:
        verdict = await self._guardrail.check(text)
        if not verdict.safe:
            raise PermanentFailure(
                GUARDRAIL_REJECTED, hint=guardrail_hint(verdict.categories, where)
            )
