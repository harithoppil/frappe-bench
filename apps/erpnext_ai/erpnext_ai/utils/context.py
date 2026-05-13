"""Context building utilities — inject DocType schemas into system prompts.

This mirrors NocoBase's datasource context injection where the AI Employee
receives schema + sample records to understand what data exists.
"""

import frappe


def build_doctype_context(doctype: str, record_name: str | None = None) -> dict:
    """Build context dict for a specific DocType, optionally including a record.

    Used when the user is viewing a specific form — the AI receives the
    full field schema and (if viewing a record) the current values.
    """
    meta = frappe.get_meta(doctype)
    fields = [
        {
            "fieldname": f.fieldname,
            "label": f.label,
            "fieldtype": f.fieldtype,
            "reqd": bool(f.reqd),
            "options": f.options,
        }
        for f in meta.fields
        if f.fieldtype not in ("Section Break", "Column Break", "Tab Break", "HTML", "Heading")
    ]

    ctx = {"doctype": doctype, "fields": fields}

    if record_name:
        try:
            doc = frappe.get_doc(doctype, record_name)
            ctx["current_record"] = {
                f["fieldname"]: doc.get(f["fieldname"])
                for f in fields
                if doc.get(f["fieldname"]) is not None
            }
        except frappe.DoesNotExistError:
            pass

    return ctx


def build_page_context(page_route: str, filters: dict | None = None) -> dict:
    """Build context for a list view page.

    Returns a summary of the records visible to the user on their current page.
    """
    return {
        "page_route": page_route,
        "filters": filters or {},
    }
