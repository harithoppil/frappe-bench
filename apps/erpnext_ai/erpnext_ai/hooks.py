"""ERPNext AI — Frappe hooks.

Based on NocoBase's plugin-ai architecture, adapted for Frappe/ERPNext.
"""

app_name = "erpnext_ai"
app_title = "ERPNext AI"
app_description = "AI Employees & Agent Loop for ERPNext — NocoBase-inspired"
app_icon = "bot"
app_color = "#00b894"
app_email = "dev@aries.erp"
app_license = "MIT"

# Required apps
required_apps = ["frappe", "erpnext"]

# ─── DocType Events ──────────────────────────────────────
# Auto-classify and enrich using AI when documents are created/updated


# ─── AI Tool Registry ────────────────────────────────────
# Maps tool names → {scope, permission, definition, invoke}
# scope: GENERAL | SPECIFIED | CUSTOM
# permission: ALLOW (auto-execute) | ASK (human-in-the-loop)
# execution: backend | frontend
# definition: JSON schema for the tool
# invoke: dotted path to Python function
ai_tools = {
    "searchDocs": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Search indexed documentation using keyword search",
        "invoke": "erpnext_ai.tools.docs.search_docs",
    },
    "readDocEntry": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Read a specific document entry by path",
        "invoke": "erpnext_ai.tools.docs.read_doc_entry",
    },
    "getCollectionNames": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "List all DocType names in the system",
        "invoke": "erpnext_ai.tools.schema.get_collection_names",
    },
    "getCollectionMetadata": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Get field definitions and relationships for a DocType",
        "invoke": "erpnext_ai.tools.schema.get_collection_metadata",
    },
    "defineCollections": {
        "scope": "SPECIFIED",
        "permission": "ASK",
        "execution": "frontend",
        "description": "Create or update DocTypes from schema JSON (requires confirmation)",
        "invoke": "erpnext_ai.tools.schema.define_collections",
    },
    "formFiller": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "frontend",
        "description": "Fill a Frappe form with key-value data",
        "invoke": "erpnext_ai.tools.form.fill_form",
    },
    "chartGenerator": {
        "scope": "SPECIFIED",
        "permission": "ASK",
        "execution": "frontend",
        "description": "Generate an ECharts chart specification from data",
        "invoke": "erpnext_ai.tools.chart.generate_chart",
    },
    "suggestions": {
        "scope": "GENERAL",
        "permission": "ASK",
        "execution": "backend",
        "description": "Provide suggested prompts for the user",
        "invoke": "erpnext_ai.tools.suggest.provide_suggestions",
    },
    "subAgentWebSearch": {
        "scope": "SPECIFIED",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Search the web using a sub-agent",
        "invoke": "erpnext_ai.tools.search.web_search",
    },
    "queryERPData": {
        "scope": "SPECIFIED",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Query ERPNext data using frappe.get_all with filters",
        "invoke": "erpnext_ai.tools.erp.query_erp_data",
    },
    "getERPRecord": {
        "scope": "SPECIFIED",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Get a single ERPNext record by DocType and name",
        "invoke": "erpnext_ai.tools.erp.get_erp_record",
    },
    "createERPDocument": {
        "scope": "SPECIFIED",
        "permission": "ASK",
        "execution": "backend",
        "description": "Create a new ERPNext document (requires confirmation)",
        "invoke": "erpnext_ai.tools.erp.create_erp_document",
    },
    "wikiSearch": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Search the knowledge base / wiki",
        "invoke": "erpnext_ai.tools.knowledge.search_knowledge",
    },
    "wikiRead": {
        "scope": "GENERAL",
        "permission": "ALLOW",
        "execution": "backend",
        "description": "Read a wiki/knowledge base page",
        "invoke": "erpnext_ai.tools.knowledge.read_knowledge",
    },
}

# ─── LLM Provider Registry ──────────────────────────────
ai_llm_providers = {
    "google-genai": "erpnext_ai.providers.google_genai.GoogleGenAIProvider",
    "openai": "erpnext_ai.providers.openai_provider.OpenAIProvider",
    "anthropic": "erpnext_ai.providers.anthropic_provider.AnthropicProvider",
    "deepseek": "erpnext_ai.providers.deepseek_provider.DeepSeekProvider",
    "ollama": "erpnext_ai.providers.ollama_provider.OllamaProvider",
}

# ─── Scheduler Events ─────────────────────────────────────


# ─── Fixtures ─────────────────────────────────────────────
# Pre-seeded AI Employees (Dex, Viz, Avery) — based on NocoBase's built-in employees
fixtures = [
    {"doctype": "AI Employee", "filters": [["built_in", "=", 1]]},
    {"doctype": "LLM Service", "filters": [["is_default", "=", 1]]},
]

# ─── Website Route Rules ─────────────────────────────────
website_route_rules = [
    {"from_route": "/ai-chat", "to_route": "ai_chat"},
]

# ─── Boot Info ────────────────────────────────────────────
extend_bootinfo = ["erpnext_ai.utils.boot.add_ai_config"]

# ─── App Include JS/CSS ──────────────────────────────────
app_include_js = "erpnext_ai.bundle.js"
app_include_css = "erpnext_ai.bundle.css"
