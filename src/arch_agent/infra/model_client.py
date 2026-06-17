"""Real Anthropic model client — a :data:`ModelClient` backed by the Messages API.

Plugs into the agent crew / gatekeeper wherever a ``Callable[[str], str]`` is
expected (the mock is swapped for this in real runs). Credentials come from the
environment (``ANTHROPIC_API_KEY``; load ``.env`` before constructing). Each call
records the response's real token usage for the efficiency study, so the study no
longer has to estimate tokens.

``temperature``/``thinking`` are intentionally omitted so the same call works
across current models (the model id — e.g. ``claude-sonnet-4-6`` — comes from
``config/setup.json``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_MAX_TOKENS = 4096


@dataclass(frozen=True)
class Usage:
    """Token usage reported by a single Messages API call."""

    in_tokens: int
    out_tokens: int


class AnthropicClient:
    """A ``ModelClient`` backed by ``anthropic.Anthropic().messages.create``."""

    def __init__(
        self, model: str, max_tokens: int = DEFAULT_MAX_TOKENS, client: Any = None
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = client if client is not None else self._default_client()
        self.last_usage: Usage | None = None

    @staticmethod
    def _default_client() -> Any:
        import anthropic

        return anthropic.Anthropic()

    def __call__(self, prompt: str) -> str:
        """Send ``prompt`` as a single user turn; return the text, record usage."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        self.last_usage = Usage(response.usage.input_tokens, response.usage.output_tokens)
        return self._text(response)

    @staticmethod
    def _text(response: Any) -> str:
        return "".join(block.text for block in response.content if block.type == "text")
