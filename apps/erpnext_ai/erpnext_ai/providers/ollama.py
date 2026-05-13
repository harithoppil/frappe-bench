"""Ollama local provider."""

from .base import BaseProvider


class OllamaProvider(BaseProvider):
    DEFAULT_BASE_URL = "http://localhost:11434"

    @property
    def default_model(self) -> str:
        return "llama3.1"

    @property
    def available_models(self) -> list[str]:
        return ["llama3.1", "llama3.2", "mistral", "qwen2.5", "phi4", "gemma3"]

    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=self.default_model,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )
