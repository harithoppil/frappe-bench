import os
import sys

sites_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(sites_path, "..", "apps", "frappe"))
sys.path.insert(0, os.path.join(sites_path, "..", "apps", "erpnext"))

os.chdir(sites_path)

import frappe
from frappe.app import application_with_statics

application = application_with_statics()
