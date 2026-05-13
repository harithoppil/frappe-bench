"""DeepSeek provider (OpenAI-compatible API)."""

from .base import BaseProvider


class DeepSeekProvider(BaseProvider):
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    @property
    def default_model(self) -> str:
        return "deepseek-chat"

    @property
    def available_models(self) -> list[str]:
        return ["deepseek-chat", "deepseek-reasoner"]

    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.default_model,
            api_key=api_key or "placeholder",
            base_url=base_url or self.DEFAULT_BASE_URL,
        )
