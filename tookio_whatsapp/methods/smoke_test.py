# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import frappe

from .message_processor import _build_prompt, _get_recent_messages


@frappe.whitelist()
def run_smoke_test():
	"""Return a small set of checks for the WhatsApp integration flow."""
	message_conversation_field = frappe.db.exists(
		"DocField",
		{
			"parent": "WhatsApp Message",
			"fieldname": "conversation",
		},
	)

	integration_api_key_field = frappe.db.exists(
		"DocField",
		{
			"parent": "WhatsApp Integration",
			"fieldname": "erpnext_api_key",
		},
	)

	integration_api_secret_field = frappe.db.exists(
		"DocField",
		{
			"parent": "WhatsApp Integration",
			"fieldname": "erpnext_api_secret",
		},
	)

	prompt = _build_prompt(
		customer_message="Do you have phone cases?",
		customer_name="Mary",
		business_name="Mary Shop",
		product_info="",
		conversation_history="Customer: Hi",
	)

	empty_history = _get_recent_messages("NON_EXISTENT_CONVERSATION")

	return {
		"message_conversation_field": bool(message_conversation_field),
		"integration_api_key_field": bool(integration_api_key_field),
		"integration_api_secret_field": bool(integration_api_secret_field),
		"prompt_has_history": "Conversation History:" in prompt,
		"prompt_mentions_business": "Mary Shop" in prompt,
		"empty_history_is_blank": empty_history == "",
	}
