"""LLM Service DocType — NocoBase llmServices equivalent.

Configures LLM providers (Google GenAI, OpenAI, Anthropic, DeepSeek, Ollama)
with API keys, base URLs, enabled models, and default generation options.
"""

import frappe
from frappe.model.document import Document


class LLMService(Document):
    def validate(self):
        if self.is_default:
            # Only one default service per provider
            existing = frappe.db.exists(
                "LLM Service",
                {"provider": self.provider, "is_default": 1, "name": ["!=", self.name]},
            )
            if existing:
                frappe.throw(f"Default service already set for {self.provider}: {existing}")

    def get_client(self):
        """Instantiate the LLM client for this service.

        Returns a langchain BaseChatModel instance.
        """
        from erpnext_ai.providers import get_provider

        provider = get_provider(self.provider)
        return provider.create_client(
            api_key=self.get_password("api_key") if self.api_key else None,
            base_url=self.base_url or None,
        )

    @staticmethod
    def get_default_service(provider: str | None = None) -> "LLMService | None":
        """Get the default LLM service, optionally filtered by provider."""
        filters = {"is_default": 1, "enabled": 1}
        if provider:
            filters["provider"] = provider

        name = frappe.db.get_value("LLM Service", filters)
        if not name:
            # Fallback to any enabled service
            name = frappe.db.get_value("LLM Service", {"enabled": 1})
        if name:
            return frappe.get_doc("LLM Service", name)
        return None
