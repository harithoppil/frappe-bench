"""Core ERP tools — read/write DocType records via Frappe ORM.

These mirror NocoBase's data-access tools but use frappe.db and
frappe.get_doc instead of HTTP calls to NocoBase's REST layer.
"""

from langchain_core.tools import tool


@tool
def get_doctype_schema(doctype: str) -> dict:
    """Return the field schema for a Frappe DocType.

    Useful for the agent to understand what fields exist before querying records.
    """
    import frappe
    meta = frappe.get_meta(doctype)
    return {
        "doctype": doctype,
        "fields": [
            {
                "fieldname": f.fieldname,
                "fieldtype": f.fieldtype,
                "label": f.label,
                "reqd": bool(f.reqd),
                "options": f.options,
            }
            for f in meta.fields
            if f.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML")
        ],
    }


@tool
def get_records(
    doctype: str,
    filters: dict | None = None,
    fields: list[str] | None = None,
    limit: int = 20,
    order_by: str = "modified desc",
) -> list[dict]:
    """Fetch records from any Frappe DocType.

    Args:
        doctype: The DocType name (e.g. "Sales Order", "Customer")
        filters: Dict of field:value pairs to filter records
        fields: List of fields to return (default: name + standard fields)
        limit: Max records to return (default 20, max 100)
        order_by: Sort order (default: modified desc)
    """
    import frappe
    limit = min(limit, 100)
    return frappe.get_all(
        doctype,
        filters=filters or {},
        fields=fields or ["name", "modified", "owner"],
        limit=limit,
        order_by=order_by,
    )


@tool
def create_record(doctype: str, values: dict) -> dict:
    """Create a new document in a Frappe DocType.

    Args:
        doctype: Target DocType
        values: Field values for the new document
    Returns:
        The created document as a dict including its `name` (ID)
    """
    import frappe
    doc = frappe.get_doc({"doctype": doctype, **values})
    doc.insert(ignore_permissions=False)
    frappe.db.commit()
    return doc.as_dict()


@tool
def update_record(doctype: str, name: str, values: dict) -> dict:
    """Update an existing document.

    Args:
        doctype: Target DocType
        name: Document name/ID
        values: Fields to update
    Returns:
        Updated document as a dict
    """
    import frappe
    doc = frappe.get_doc(doctype, name)
    doc.update(values)
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return doc.as_dict()


@tool
def delete_record(doctype: str, name: str) -> str:
    """Delete a document. Use with caution — prefer cancellation for submitted docs.

    Args:
        doctype: Target DocType
        name: Document name/ID
    Returns:
        Confirmation message
    """
    import frappe
    frappe.delete_doc(doctype, name, ignore_permissions=False)
    frappe.db.commit()
    return f"Deleted {doctype} '{name}'"


@tool
def run_report(report_name: str, filters: dict | None = None) -> dict:
    """Run a Frappe Report and return its data.

    Args:
        report_name: Name of the Frappe Report
        filters: Report filter values
    Returns:
        Report result with columns and data rows
    """
    import frappe
    from frappe.desk.query_report import run
    result = run(report_name, filters or {})
    return {"columns": result.get("columns", []), "data": result.get("result", [])}


@tool
def submit_document(doctype: str, name: str) -> str:
    """Submit a draft document (e.g. Sales Order → Submitted).

    Args:
        doctype: Target DocType
        name: Document name/ID
    Returns:
        Confirmation message
    """
    import frappe
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    frappe.db.commit()
    return f"Submitted {doctype} '{name}'"


@tool
def cancel_document(doctype: str, name: str) -> str:
    """Cancel a submitted document.

    Args:
        doctype: Target DocType
        name: Document name/ID
    Returns:
        Confirmation message
    """
    import frappe
    doc = frappe.get_doc(doctype, name)
    doc.cancel()
    frappe.db.commit()
    return f"Cancelled {doctype} '{name}'"


@tool
def get_linked_documents(doctype: str, name: str) -> list[dict]:
    """Get all documents linked to (referencing) a given document.

    Useful to trace related documents (e.g. Invoices linked to a Sales Order).

    Args:
        doctype: Source DocType
        name: Source document name/ID
    Returns:
        List of linked documents with their doctype and name
    """
    import frappe
    links = frappe.get_all_linked_documents(doctype, name)
    return links


@tool
def search_records(
    doctype: str,
    query: str,
    fields: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Full-text search across a DocType's records.

    Args:
        doctype: Target DocType
        query: Search query string
        fields: Fields to search in (default: title/name fields)
        limit: Max results (default 10)
    Returns:
        Matching records
    """
    import frappe
    return frappe.get_all(
        doctype,
        filters=[["name", "like", f"%{query}%"]],
        fields=fields or ["name", "modified"],
        limit=min(limit, 50),
    )
