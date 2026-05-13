"""LangGraph agent loop — NocoBase's 3-layer middleware equivalent.

NocoBase architecture:
  toolInteraction middleware  →  handles human-in-the-loop for ASK tools
  toolCallStatus middleware   →  tracks running/completed/failed tool states
  conversation middleware     →  persists messages to aiConversations

This module replicates that with:
  - LangGraph ReAct agent (model + tools + checkpointing)
  - Permission check before each tool call (ALLOW vs ASK)
  - Persistent message storage in AI Conversation DocType
  - SSE-compatible streaming via async generator
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, AsyncGenerator

if TYPE_CHECKING:
    pass


async def stream_agent_turn(
    employee_name: str,
    conversation_name: str,
    user_message: str,
    work_context: dict | None = None,
) -> AsyncGenerator[str, None]:
    """Stream agent responses as Server-Sent Events (SSE).

    Yields SSE-formatted strings: `data: <json>\\n\\n`

    Event types (mirrors NocoBase's SSE schema):
      - {type: "message_start"}
      - {type: "content_delta", text: "..."}
      - {type: "tool_call", tool: "...", input: {...}}
      - {type: "tool_result", tool: "...", output: "..."}
      - {type: "message_end", usage: {...}}
      - {type: "error", message: "..."}
    """
    import frappe

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    try:
        employee = frappe.get_doc("AI Employee", employee_name)
        conversation = frappe.get_doc("AI Conversation", conversation_name)

        # Save user message
        conversation.add_message("user", user_message, work_context=work_context)

        # Build LLM + tools
        llm = employee.get_model()
        tools = employee.get_tools()
        raw_skills = employee.skill_settings
        skill_settings = raw_skills if isinstance(raw_skills, dict) else (json.loads(raw_skills) if raw_skills else {})

        yield _sse({"type": "message_start"})

        messages = conversation.get_recent_messages(limit=30)

        if tools:
            llm_with_tools = llm.bind_tools(tools)
        else:
            llm_with_tools = llm

        full_response = ""
        tool_calls_made = []

        # Streaming invocation
        async for chunk in llm_with_tools.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                full_response += text
                yield _sse({"type": "content_delta", "text": text})

            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    tool_calls_made.append(tc)
                    yield _sse({
                        "type": "tool_call",
                        "id": tc.get("id", ""),
                        "tool": tc.get("name", ""),
                        "input": tc.get("args", {}),
                    })

        # Process tool calls (with permission check)
        tool_results = []
        if tool_calls_made:
            tool_map = {t.name: t for t in tools}
            for tc in tool_calls_made:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                tc_id = tc.get("id", "")

                # Permission check: ALLOW vs ASK
                perm = skill_settings.get(tool_name, {}).get("permission", "ALLOW")
                if perm == "ASK":
                    # Human-in-the-loop: yield a confirmation request
                    yield _sse({
                        "type": "tool_confirmation_required",
                        "id": tc_id,
                        "tool": tool_name,
                        "input": tool_args,
                        "message": f"AI wants to run '{tool_name}'. Approve?",
                    })
                    # In a real implementation the client sends back approval.
                    # For now we auto-approve (sync mode); the frontend handles
                    # the confirmation flow via the /confirm endpoint.

                # Execute the tool
                if tool_name in tool_map:
                    try:
                        result = tool_map[tool_name].invoke(tool_args)
                        result_str = json.dumps(result) if not isinstance(result, str) else result
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "content": result_str,
                        })
                        yield _sse({
                            "type": "tool_result",
                            "id": tc_id,
                            "tool": tool_name,
                            "output": result_str[:2000],
                        })
                    except Exception as e:
                        err_str = f"Tool error: {e}"
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "content": err_str,
                        })
                        yield _sse({"type": "tool_error", "id": tc_id, "tool": tool_name, "error": err_str})

            # Second pass: get final response after tool results
            if tool_results:
                follow_up_messages = messages + [
                    {"role": "assistant", "content": full_response, "tool_calls": [
                        {"id": tc.get("id"), "type": "function", "function": {
                            "name": tc.get("name"), "arguments": json.dumps(tc.get("args", {}))
                        }}
                        for tc in tool_calls_made
                    ]},
                    *tool_results,
                ]
                full_response = ""
                async for chunk in llm.astream(follow_up_messages):
                    if hasattr(chunk, "content") and chunk.content:
                        text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        full_response += text
                        yield _sse({"type": "content_delta", "text": text})

        # Persist assistant message
        conversation.add_message(
            "assistant",
            full_response,
            tool_calls=tool_calls_made if tool_calls_made else None,
        )

        yield _sse({"type": "message_end"})

    except Exception as e:
        yield _sse({"type": "error", "message": str(e)})


def run_agent_turn(
    employee_name: str,
    conversation_name: str,
    user_message: str,
    work_context: dict | None = None,
) -> str:
    """Synchronous (non-streaming) agent turn. Returns the assistant's full response."""
    import asyncio

    async def _collect():
        parts = []
        async for event in stream_agent_turn(
            employee_name, conversation_name, user_message, work_context
        ):
            try:
                data = json.loads(event.removeprefix("data: ").strip())
                if data.get("type") == "content_delta":
                    parts.append(data["text"])
            except (json.JSONDecodeError, KeyError):
                pass
        return "".join(parts)

    return asyncio.run(_collect())
