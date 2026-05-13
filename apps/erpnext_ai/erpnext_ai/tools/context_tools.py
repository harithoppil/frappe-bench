"""Context tools — expose Frappe session and system info to the agent."""

from langchain_core.tools import tool


@tool
def get_current_user() -> dict:
    """Get information about the currently logged-in user."""
    import frappe
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    return {
        "user": user,
        "full_name": user_doc.full_name,
        "email": user_doc.email,
        "roles": [r.role for r in user_doc.roles],
    }


@tool
def get_system_settings() -> dict:
    """Get key system settings (company name, currency, fiscal year, etc.)."""
    import frappe
    settings = frappe.get_single("System Settings")
    return {
        "language": settings.language,
        "time_zone": settings.time_zone,
        "date_format": settings.date_format,
        "currency": frappe.db.get_single_value("Global Defaults", "default_currency"),
        "company": frappe.db.get_single_value("Global Defaults", "default_company"),
    }
