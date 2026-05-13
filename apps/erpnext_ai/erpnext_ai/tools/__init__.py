"""AI tool registry — NocoBase aiTools equivalent.

Tools are langchain StructuredTool instances. The registry maps tool_name →
callable so the AI Employee can bind whichever tools it has permission for.
"""

from .erp_tools import (
    get_doctype_schema,
    get_records,
    create_record,
    update_record,
    delete_record,
    run_report,
    submit_document,
    cancel_document,
    get_linked_documents,
    search_records,
)
from .context_tools import (
    get_current_user,
    get_system_settings,
)
from .analytics_tools import (
    run_sql_query,
    generate_chart_data,
)

TOOL_REGISTRY: dict[str, object] = {
    "get_doctype_schema": get_doctype_schema,
    "get_records": get_records,
    "create_record": create_record,
    "update_record": update_record,
    "delete_record": delete_record,
    "run_report": run_report,
    "submit_document": submit_document,
    "cancel_document": cancel_document,
    "get_linked_documents": get_linked_documents,
    "search_records": search_records,
    "get_current_user": get_current_user,
    "get_system_settings": get_system_settings,
    "run_sql_query": run_sql_query,
    "generate_chart_data": generate_chart_data,
}


def get_tool(name: str):
    tool = TOOL_REGISTRY.get(name)
    if not tool:
        raise ValueError(f"Unknown tool: {name}. Available: {list(TOOL_REGISTRY)}")
    return tool
