"""Boot info extension — adds AI employee config to the desk boot session."""

import frappe


def add_ai_config(bootinfo):
    try:
        bootinfo.ai_employees = frappe.get_all(
            "AI Employee",
            filters={"enabled": 1},
            fields=["name", "nickname", "position", "category", "about", "greeting", "avatar"],
            order_by="creation asc",
        )
    except Exception:
        bootinfo.ai_employees = []
