"""Google GenAI / Gemini provider — primary LLM for this project.

API key loaded from site_config.google_cloud_api_key (GEMINI_API_KEY).
"""

from .base import BaseProvider


class GoogleGenAIProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @property
    def available_models(self) -> list[str]:
        return [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.1-pro-preview",
            "gemini-3.1-flash-lite-preview",
        ]

    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Fallback to site_config key if none provided
        if not api_key:
            try:
                import frappe
                api_key = frappe.conf.get("google_cloud_api_key")
            except Exception:
                pass

        kwargs: dict = {}
        if api_key:
            kwargs["google_api_key"] = api_key

        return ChatGoogleGenerativeAI(model=self.default_model, **kwargs)
