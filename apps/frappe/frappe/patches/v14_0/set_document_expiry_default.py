from __future__ import annotations
import frappe


def execute():
	frappe.db.set_single_value(
		"System Settings",
		{"document_share_key_expiry": 30},
	)
