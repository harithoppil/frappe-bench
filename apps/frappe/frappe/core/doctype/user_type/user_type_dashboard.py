from __future__ import annotations
from frappe import _


def get_data():
	return {"fieldname": "user_type", "transactions": [{"label": _("Reference"), "items": ["User"]}]}
