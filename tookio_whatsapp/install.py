# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import json
import os
import frappe


def after_install():
	"""Load DocTypes from JSON files after app installation"""
	app_path = os.path.dirname(__file__)
	standard_docs = [
		("doctype", "whatsapp_integration", "whatsapp_integration.json"),
		("doctype", "whatsapp_message", "whatsapp_message.json"),
		("doctype", "whatsapp_conversation", "whatsapp_conversation.json"),
		("desktop_icon", "tookio_whatsapp", "tookio_whatsapp.json"),
		("workspace_sidebar", "tookio_whatsapp", "tookio_whatsapp.json"),
	]

	for folder_name, record_folder, file_name in standard_docs:
		json_file = os.path.join(app_path, folder_name, record_folder, file_name)

		if os.path.exists(json_file):
			try:
				with open(json_file, "r") as f:
					doc_data = json.load(f)

				frappe.get_doc(doc_data).insert(ignore_if_duplicate=True)
				frappe.db.commit()
				print(f"✓ Loaded {doc_data['name']}")

			except Exception as e:
				frappe.log_error(f"Failed to load {record_folder}", str(e))
				print(f"✗ Failed to load {record_folder}: {str(e)}")
	
	print("Installation complete!")
