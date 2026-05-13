"""ERPNext AI — NocoBase-inspired AI Employees for ERPNext/Frappe.

Provides:
- AI Employee DocType (configurable personas with system prompts, tools, data sources)
- LLM Service DocType (multi-provider: Google GenAI, OpenAI, Anthropic, DeepSeek, Ollama)
- AI Conversation & Message DocTypes (persistent chat with tool call tracking)
- AI Context Datasource DocType (inject DocType schema + records into system prompt)
- LangGraph agent loop with Frappe checkpoint persistence
- Human-in-the-loop tool confirmation (ASK vs ALLOW permissions)
- SSE streaming for real-time chat
- RAG knowledge base integration
- Text-to-App: AI generates DocTypes from natural language
"""

__version__ = "0.0.1"
