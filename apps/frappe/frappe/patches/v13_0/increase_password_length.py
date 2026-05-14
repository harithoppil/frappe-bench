from __future__ import annotations
import frappe


def execute():
	frappe.db.change_column_type("__Auth", column="password", type="TEXT")
