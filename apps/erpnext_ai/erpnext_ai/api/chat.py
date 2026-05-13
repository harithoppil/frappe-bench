"""Chat API — SSE streaming endpoint and conversation management.

Mirrors NocoBase's /api/ai/conversations REST layer.

Key endpoints:
  POST /api/method/erpnext_ai.api.chat.create_conversation
  POST /api/method/erpnext_ai.api.chat.send_message  (SSE stream)
  GET  /api/method/erpnext_ai.api.chat.get_conversations
  GET  /api/method/erpnext_ai.api.chat.get_messages
"""

import json

import frappe
from frappe import _


@frappe.whitelist()
def create_conversation(employee_name: str, title: str | None = None) -> dict:
    """Create a new AI Conversation for the current user + employee."""
    employee = frappe.get_doc("AI Employee", employee_name)

    conv = frappe.get_doc({
        "doctype": "AI Conversation",
        "ai_employee": employee_name,
        "user": frappe.session.user,
        "title": title or f"Chat with {employee.nickname or employee_name}",
        "status": "Active",
    })
    conv.insert(ignore_permissions=True)

    if employee.greeting:
        conv.add_message("assistant", employee.greeting)

    return {
        "conversation": conv.name,
        "session_id": conv.session_id,
        "title": conv.title,
    }


@frappe.whitelist(allow_guest=False)
def send_message(
    conversation_name: str,
    message: str,
    work_context: str | None = None,
) -> str:
    """Stream an agent response via SSE.

    Returns all SSE events concatenated as a single string.
    The frontend JS client parses the `data: {...}` lines.
    """
    import asyncio

    conv = frappe.get_doc("AI Conversation", conversation_name)

    if conv.user != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Not allowed"), frappe.PermissionError)

    employee_name = conv.ai_employee
    ctx = json.loads(work_context) if work_context else None

    from erpnext_ai.agents.loop import stream_agent_turn

    async def _run():
        chunks = []
        async for chunk in stream_agent_turn(employee_name, conversation_name, message, ctx):
            chunks.append(chunk)
        return chunks

    events = asyncio.run(_run())
    return "".join(events)


@frappe.whitelist()
def get_conversations(employee_name: str | None = None, limit: int = 20) -> list[dict]:
    """List conversations for the current user."""
    filters = {"user": frappe.session.user, "status": "Active"}
    if employee_name:
        filters["ai_employee"] = employee_name

    return frappe.get_all(
        "AI Conversation",
        filters=filters,
        fields=["name", "title", "ai_employee", "creation", "modified"],
        limit=min(int(limit), 100),
        order_by="modified desc",
    )


@frappe.whitelist()
def get_messages(conversation_name: str) -> list[dict]:
    """Get all messages in a conversation."""
    conv = frappe.get_doc("AI Conversation", conversation_name)

    if conv.user != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Not allowed"), frappe.PermissionError)

    return [
        {
            "role": m.role,
            "content": m.content,
            "tool_calls": json.loads(m.tool_calls) if m.tool_calls else None,
            "tool_call_id": m.tool_call_id,
            "idx": m.idx,
        }
        for m in conv.messages
    ]


@frappe.whitelist()
def archive_conversation(conversation_name: str) -> dict:
    """Archive a conversation (soft-delete)."""
    conv = frappe.get_doc("AI Conversation", conversation_name)
    if conv.user != frappe.session.user and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Not allowed"), frappe.PermissionError)

    conv.status = "Archived"
    conv.save(ignore_permissions=True)
    return {"status": "archived"}


@frappe.whitelist()
def get_employees() -> list[dict]:
    """List enabled AI Employees."""
    return frappe.get_all(
        "AI Employee",
        filters={"enabled": 1},
        fields=["name", "nickname", "position", "category", "about", "greeting", "avatar"],
        order_by="creation asc",
    )
