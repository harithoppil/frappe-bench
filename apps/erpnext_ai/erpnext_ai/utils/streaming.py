"""SSE formatting utilities."""

import json


def sse_event(data: dict, event: str | None = None) -> str:
    """Format a dict as a Server-Sent Event string."""
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)
