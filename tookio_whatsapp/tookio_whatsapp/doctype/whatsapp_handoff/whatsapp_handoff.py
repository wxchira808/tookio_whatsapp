# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WhatsAppHandoff(Document):
	def on_insert(self):
		"""Mark notify time and log the handoff event."""
		self.owner_notified_at = frappe.utils.now()
		self.save(ignore_permissions=True)
		frappe.logger().info(f"Handoff created and owner will be alerted: {self.name}")
