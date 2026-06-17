"""Tests for :mod:`arch_agent.infra.model_client` (mocked SDK — no network, no spend)."""

from __future__ import annotations

import pytest

from arch_agent.infra.model_client import AnthropicClient, Usage


class FakeBlock:
    def __init__(self, block_type: str, text: str = "") -> None:
        self.type = block_type
        self.text = text


class FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class FakeResponse:
    def __init__(self, content: list[FakeBlock], usage: FakeUsage) -> None:
        self.content = content
        self.usage = usage


class FakeMessages:
    def __init__(self, response: FakeResponse) -> None:
        self._response = response
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> FakeResponse:
        self.calls.append(kwargs)
        return self._response


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.messages = FakeMessages(response)


def test_returns_joined_text_and_records_usage() -> None:
    response = FakeResponse(
        [FakeBlock("text", "hello "), FakeBlock("thinking", "..."), FakeBlock("text", "world")],
        FakeUsage(120, 8),
    )
    client = AnthropicClient("claude-sonnet-4-6", max_tokens=1000, client=FakeClient(response))
    assert client("hi") == "hello world"  # only text blocks, concatenated
    assert client.last_usage == Usage(in_tokens=120, out_tokens=8)


def test_passes_model_max_tokens_and_prompt() -> None:
    fake = FakeClient(FakeResponse([FakeBlock("text", "ok")], FakeUsage(1, 1)))
    AnthropicClient("claude-sonnet-4-6", max_tokens=512, client=fake)("PROMPT")
    kwargs = fake.messages.calls[0]
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == 512
    assert kwargs["messages"] == [{"role": "user", "content": "PROMPT"}]


def test_no_text_blocks_returns_empty() -> None:
    fake = FakeClient(FakeResponse([FakeBlock("thinking", "x")], FakeUsage(1, 1)))
    assert AnthropicClient("m", client=fake)("hi") == ""


def test_default_client_built_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # constructing anthropic.Anthropic() is offline; it only needs a key present
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    client = AnthropicClient("claude-sonnet-4-6")  # no injected client
    assert hasattr(client._client, "messages")
