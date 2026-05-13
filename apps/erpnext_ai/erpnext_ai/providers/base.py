"""Abstract base for LLM providers."""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        """Return a langchain BaseChatModel instance."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...

    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        ...
