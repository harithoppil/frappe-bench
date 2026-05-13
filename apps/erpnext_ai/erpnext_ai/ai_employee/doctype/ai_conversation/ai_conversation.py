"""AI Conversation DocType — NocoBase aiConversations equivalent."""

import frappe
from frappe.model.document import Document


class AIConversation(Document):
    def before_save(self):
        if not self.session_id:
            import uuid
            self.session_id = str(uuid.uuid4())

    def add_message(self, role: str, content: str, tool_calls=None, work_context=None):
        """Append a message to this conversation."""
        msg = self.append("messages", {
            "role": role,
            "content": content,
        })
        if tool_calls:
            msg.tool_calls = frappe.as_json(tool_calls)
        if work_context:
            msg.work_context = frappe.as_json(work_context)
        self.save()
        return msg

    def get_recent_messages(self, limit: int = 20) -> list[dict]:
        """Get recent messages for LLM context window."""
        messages = []
        for msg in reversed(self.messages[-limit:]):
            entry = {"role": msg.role, "content": msg.content or ""}
            if msg.role == "assistant" and msg.tool_calls:
                import json
                try:
                    entry["tool_calls"] = json.loads(msg.tool_calls)
                except (json.JSONDecodeError, TypeError):
                    pass
            if msg.role == "tool" and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            messages.append(entry)
        messages.reverse()
        return messages

    def fork(self) -> "AIConversation":
        """Create a forked conversation (increment thread number)."""
        forked = frappe.copy_doc(self)
        forked.session_id = self.session_id
        forked.thread = (self.thread or 0) + 1
        forked.title = f"{self.title} (fork {forked.thread})"
        forked.messages = []  # Start fresh, reference parent via session_id
        forked.insert()
        return forked
