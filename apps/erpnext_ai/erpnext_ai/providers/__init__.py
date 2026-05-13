"""LLM provider registry — NocoBase llmProviders equivalent."""

from .base import BaseProvider
from .google import GoogleGenAIProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .deepseek import DeepSeekProvider
from .ollama import OllamaProvider

_REGISTRY: dict[str, type[BaseProvider]] = {
    "Google GenAI": GoogleGenAIProvider,
    "OpenAI": OpenAIProvider,
    "Anthropic": AnthropicProvider,
    "DeepSeek": DeepSeekProvider,
    "Ollama": OllamaProvider,
}


def get_provider(name: str) -> BaseProvider:
    cls = _REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown LLM provider: {name}. Available: {list(_REGISTRY)}")
    return cls()


def list_providers() -> list[str]:
    return list(_REGISTRY.keys())
