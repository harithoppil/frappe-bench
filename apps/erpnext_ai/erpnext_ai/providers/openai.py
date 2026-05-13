"""OpenAI provider — defaults to Azure OpenAI endpoint.

Azure endpoint + key loaded from site_config if not passed directly.
"""

from .base import BaseProvider

AZURE_BASE_URL = "https://east-us-neoklis-resource.services.ai.azure.com/openai/v1"


class OpenAIProvider(BaseProvider):
    @property
    def default_model(self) -> str:
        return "gpt-5.5"

    @property
    def available_models(self) -> list[str]:
        return ["gpt-5.5", "gpt-5.4-pro", "gpt-4o", "gpt-4o-mini", "o1", "o3-mini"]

    def create_client(self, api_key: str | None = None, base_url: str | None = None):
        from langchain_openai import ChatOpenAI

        if not api_key:
            try:
                import frappe
                api_key = frappe.conf.get("azure_openai_key")
            except Exception:
                pass

        if not base_url:
            try:
                import frappe
                base_url = frappe.conf.get("azure_openai_endpoint") or AZURE_BASE_URL
            except Exception:
                base_url = AZURE_BASE_URL

        return ChatOpenAI(
            model=self.default_model,
            api_key=api_key or "placeholder",
            base_url=base_url,
        )
