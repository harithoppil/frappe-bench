from __future__ import annotations
import frappe


def execute():
	for name in ("desktop", "space"):
		frappe.delete_doc("Page", name)
