from __future__ import annotations
import frappe


def execute():
	frappe.db.delete("DocType", {"name": "Feedback Request"})
