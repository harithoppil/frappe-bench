"""AI Employee DocType — NocoBase aiEmployees equivalent.

Each AI Employee is a configurable persona with:
- System prompt (about) defining personality and capabilities
- Tool/skill bindings with permission levels (ALLOW vs ASK)
- Data source access (which DocTypes it can read/query)
- Model settings (LLM provider, temperature, etc.)
- Knowledge base configuration for RAG retrieval
"""

import json

import frappe
from frappe.model.document import Document


def _as_dict(val, default=None):
    """Parse Frappe JSON field — handles both str and already-parsed dict/list."""
    if default is None:
        default = {}
    if isinstance(val, (dict, list)):
        return val
    if val:
        return json.loads(val)
    return default


class AIEmployee(Document):
    def validate(self):
        if self.skill_settings and isinstance(self.skill_settings, str):
            try:
                json.loads(self.skill_settings)
            except json.JSONDecodeError:
                frappe.throw("Skill Settings must be valid JSON")

        if self.model_settings and isinstance(self.model_settings, str):
            try:
                json.loads(self.model_settings)
            except json.JSONDecodeError:
                frappe.throw("Model Settings must be valid JSON")

    def get_system_prompt(self, user_context: dict | None = None) -> str:
        """Build the full system prompt using NocoBase's prompt template.

        Structure (from NocoBase):
        - Global instructions (security, integrity, communication)
        - Employee-specific prompt (about field)
        - Personal customization
        - Task background (data source schema context)
        - Environment info (database, locale)
        - Knowledge base context (RAG-retrieved data)
        """
        parts = [
            f"You are **{self.nickname}**, an AI employee working in **ERPNext**.",
            "",
            "<<instructions>",
            "<<global>",
            "1. Data Source Integrity — Only access data via bound tools (queryERPData, getERPRecord)",
            "2. Information Security — NEVER expose raw database schema or internal IDs to users",
            "3. Database Operations — Always use parameterized queries via frappe API",
            "4. Communication Standards — Be professional, concise, and helpful",
            "5. Tool Integration — NEVER refer to tool names directly in responses",
            "</global>",
            f"<<ai_employee>",
            self.about or "",
            "</ai_employee>",
        ]

        if user_context and user_context.get("personal"):
            parts.append(f"<personal>{user_context['personal']}</personal>")

        parts.append("</instructions>")

        # Task context: inject DocType schema from data_source_settings
        data_source_context = self._get_data_source_context()
        if data_source_context:
            parts.append(f"<<task>")
            parts.append(f"<background>{data_source_context}</background>")
            if user_context and user_context.get("context"):
                parts.append(f"<context>{user_context['context']}</context>")
            parts.append("</task>")

        # Environment
        parts.append(f"<<environment>")
        parts.append(f"<main_database>PostgreSQL / MariaDB via Frappe ORM</main_database>")
        parts.append(f"<locale>en-US</locale>")
        parts.append("</environment>")

        # Knowledge base
        if self.enable_knowledge_base and self.knowledge_base_prompt:
            kb_context = self._retrieve_knowledge_base()
            if kb_context:
                prompt = self.knowledge_base_prompt.replace("{context}", kb_context)
                parts.append(f"<<knowledgeBase>{prompt}</knowledgeBase>")

        return "\n".join(parts)

    def _get_data_source_context(self) -> str:
        """Inject DocType field metadata into the system prompt.

        NocoBase equivalent: getEmployeeDataSourceContext()
        Reads employee.dataSourceSettings.collections[] and dumps
        field names, types, and labels for each DocType.
        """
        import json

        if not self.data_source_settings:
            return ""

        settings = _as_dict(self.data_source_settings)

        collections = settings.get("collections", [])
        if not collections:
            return ""

        lines = []
        for doctype_name in collections:
            try:
                meta = frappe.get_meta(doctype_name)
                lines.append(f"\nDocType: {doctype_name}")
                for field in meta.fields:
                    if field.fieldtype in ["Section Break", "Column Break", "Tab Break"]:
                        continue
                    lines.append(
                        f"  Field: {field.fieldname}, "
                        f"Label: {field.label}, "
                        f"Type: {field.fieldtype}"
                        + (f", Options: {field.options}" if field.options else "")
                        + (", Required" if field.reqd else "")
                    )
            except frappe.DoesNotExistError:
                lines.append(f"\nDocType: {doctype_name} (NOT FOUND)")

        return "\n".join(lines)

    def _retrieve_knowledge_base(self) -> str:
        """Retrieve relevant knowledge base documents for RAG context.

        NocoBase equivalent: retrieveKnowledgeBase()
        Uses vector store to search knowledge base documents.
        """
        # TODO: Implement RAG retrieval via Frappe full-text search or vector DB
        return ""

    def get_tools(self) -> list:
        """Get langchain tool instances bound to this employee.

        skill_settings format: {"tool_name": {"permission": "ALLOW" | "ASK"}, ...}
        Returns only the tools listed in skill_settings.
        """
        from erpnext_ai.tools import TOOL_REGISTRY

        if not self.skill_settings:
            return []

        settings = _as_dict(self.skill_settings)

        tools = []
        for tool_name, config in settings.items():
            tool = TOOL_REGISTRY.get(tool_name)
            if tool:
                tools.append(tool)

        return tools

    @frappe.whitelist()
    def get_model(self):
        """Get the LLM client instance for this employee.

        model_settings format: {"model": "gemini-2.5-flash", "temperature": 0.3, ...}
        Provider is inferred from the model name; defaults to Google GenAI.
        """
        from erpnext_ai.providers import get_provider

        settings = _as_dict(self.model_settings)
        model_name = settings.get("model", "gemini-2.5-flash")
        temperature = settings.get("temperature", 0.3)

        # Infer provider from model name
        if model_name.startswith("gemini"):
            provider_name = "Google GenAI"
        elif model_name.startswith("gpt") or model_name.startswith("o1") or model_name.startswith("o3"):
            provider_name = "OpenAI"
        elif model_name.startswith("claude"):
            provider_name = "Anthropic"
        elif model_name.startswith("deepseek"):
            provider_name = "DeepSeek"
        else:
            provider_name = settings.get("provider", "Google GenAI")

        # Get the LLM service for API key / base URL
        llm_service = None
        try:
            svc_name = frappe.db.get_value(
                "LLM Service", {"provider": provider_name, "is_default": 1, "enabled": 1}
            ) or frappe.db.get_value("LLM Service", {"provider": provider_name, "enabled": 1})
            if svc_name:
                llm_service = frappe.get_doc("LLM Service", svc_name)
        except Exception:
            pass

        provider = get_provider(provider_name)
        api_key = llm_service.get_password("api_key") if llm_service and llm_service.api_key else None
        base_url = llm_service.base_url if llm_service else None

        client = provider.create_client(api_key=api_key, base_url=base_url or None)

        # Bind temperature if supported
        try:
            client = client.bind(temperature=temperature)
        except Exception:
            pass

        return client
