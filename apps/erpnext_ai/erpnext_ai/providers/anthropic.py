"""Anthropic / Claude provider."""

from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-6"

    @property
    def available_models(self) -> list[str]:
        return [
            "claude-opus-4-7",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]

    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        from langchain_anthropic import ChatAnthropic

        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(model=self.default_model, **kwargs)
