# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
import requests

from .gemini_client import GeminiClient


@frappe.whitelist()
def process_whatsapp_message(message_id):
	"""Process one stored WhatsApp message and send a reply."""
	try:
		message = frappe.get_doc("WhatsApp Message", message_id)
		integration = frappe.get_doc("WhatsApp Integration", message.integration)

		if not integration.enabled:
			frappe.log_error("Integration disabled", f"Integration {message.integration} is disabled")
			return

		if message.message_type != "text":
			frappe.log_error("Unsupported message type", f"Message {message_id}: {message.message_type}")
			return

		conversation = _get_or_create_conversation(
			integration=message.integration,
			customer_phone=message.from_phone,
			customer_name=message.customer_name,
		)

		if message.conversation != conversation.name:
			message.conversation = conversation.name
			message.save(ignore_permissions=True)

		gemini_config = _get_gemini_config(integration)
		if not gemini_config:
			return

		gemini = GeminiClient(
			api_key=gemini_config["api_key"],
			model=gemini_config["model"],
			temperature=gemini_config["temperature"],
		)

		recent_messages = _get_recent_messages(conversation.name)
		prompt = _build_prompt(
			customer_message=message.text_content,
			customer_name=message.customer_name,
			business_name=integration.business_name,
			product_info="",
			conversation_history=recent_messages,
		)

		ai_response = gemini.generate_response(
			prompt,
			max_tokens=gemini_config["max_output_tokens"],
			timeout=gemini_config["timeout_seconds"],
		)
		if not ai_response:
			frappe.log_error("Gemini failed to generate response", f"Message {message_id}")
			return

		success = _send_whatsapp_message(
			phone_number_id=integration.phone_number_id,
			to_phone=message.from_phone,
			text=ai_response,
			access_token=integration.access_token,
		)

		if success:
			message.processed = True
			message.response_text = ai_response
			message.response_sent_at = datetime.now()
			message.save(ignore_permissions=True)

			_update_conversation(
				conversation_name=conversation.name,
				last_message=message.text_content,
				customer_name=message.customer_name,
			)

			frappe.logger().info(f"Message {message_id} processed successfully")
		else:
			frappe.log_error("Failed to send WhatsApp response", f"Message {message_id}")

	except Exception as e:
		frappe.log_error("Message processing error", str(e))


def _get_or_create_conversation(integration, customer_phone, customer_name=None):
	"""Return the active conversation row for this customer, or create it."""
	conversation_name = frappe.db.get_value(
		"WhatsApp Conversation",
		{
			"integration": integration,
			"customer_phone": customer_phone,
		},
		"name",
	)

	if conversation_name:
		return frappe.get_doc("WhatsApp Conversation", conversation_name)

	conversation = frappe.get_doc(
		{
			"doctype": "WhatsApp Conversation",
			"integration": integration,
			"customer_phone": customer_phone,
			"customer_name": customer_name,
			"message_count": 0,
			"conversation_state": "active",
		}
	)
	conversation.insert(ignore_permissions=True)
	return conversation


def _get_gemini_config(integration):
	"""Return Gemini credentials and generation settings."""
	profile_name = integration.get("gemini_profile")
	if profile_name:
		try:
			profile = frappe.get_doc("Gemini Profile", profile_name)
			if not profile.enabled:
				frappe.log_error(
					"Gemini profile disabled",
					f"Gemini Profile {profile_name} is disabled",
				)
				return None

			return {
				"api_key": profile.api_key,
				"model": profile.model or "gemini-1.5-flash",
				"temperature": profile.temperature if profile.temperature is not None else 0.7,
				"max_output_tokens": profile.max_output_tokens or 150,
				"timeout_seconds": profile.timeout_seconds or 30,
			}
		except Exception as e:
			frappe.log_error("Gemini profile lookup failed", str(e))
			return None

	default_profile = frappe.get_all(
		"Gemini Profile",
		filters={"enabled": 1, "is_default": 1},
		fields=["name"],
		order_by="modified desc",
		limit_page_length=1,
	)
	if default_profile:
		try:
			profile = frappe.get_doc("Gemini Profile", default_profile[0]["name"])
			return {
				"api_key": profile.api_key,
				"model": profile.model or "gemini-1.5-flash",
				"temperature": profile.temperature if profile.temperature is not None else 0.7,
				"max_output_tokens": profile.max_output_tokens or 150,
				"timeout_seconds": profile.timeout_seconds or 30,
			}
		except Exception as e:
			frappe.log_error("Default Gemini profile lookup failed", str(e))
			return None

	api_key = integration.get("gemini_api_key") or frappe.conf.get("gemini_api_key")
	if not api_key:
		frappe.log_error("Gemini API key missing", "Set a Gemini Profile or gemini_api_key on the integration")
		return None

	return {
		"api_key": api_key,
		"model": "gemini-1.5-flash",
		"temperature": 0.7,
		"max_output_tokens": 150,
		"timeout_seconds": 30,
	}


def _get_recent_messages(conversation_name, limit=4):
	"""Return a compact summary of the latest message thread for context."""
	try:
		messages = frappe.get_list(
			"WhatsApp Message",
			filters={"conversation": conversation_name},
			fields=["text_content", "response_text", "creation"],
			order_by="creation desc",
			limit_page_length=limit,
		)

		if not messages:
			return ""

		lines = []
		for record in reversed(messages):
			incoming = record.get("text_content") or ""
			response = record.get("response_text") or ""
			if incoming:
				lines.append(f"Customer: {incoming}")
			if response:
				lines.append(f"Assistant: {response}")

		return "\n".join(lines)
	except Exception:
		return ""


def _build_prompt(customer_message, customer_name, business_name, product_info, conversation_history=""):
	"""Build the prompt for Gemini."""
	prompt = f"""You are a customer service representative for {business_name}.

Customer Name: {customer_name}
Customer Message: {customer_message}

{f'Conversation History:\n{conversation_history}\n' if conversation_history else ''}
{f'Available Products: {product_info}' if product_info else ''}

Respond helpfully and professionally. Keep response under 150 words.
If you can't help, politely suggest they contact support."""

	return prompt


def _send_whatsapp_message(phone_number_id, to_phone, text, access_token):
	"""Send a message back to the customer via WhatsApp API."""
	try:
		url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
		payload = {
			"messaging_product": "whatsapp",
			"to": to_phone,
			"type": "text",
			"text": {
				"preview_url": False,
				"body": text,
			},
		}
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json",
		}

		response = requests.post(url, json=payload, headers=headers, timeout=10)
		response.raise_for_status()
		result = response.json()

		if "messages" in result and len(result["messages"]) > 0:
			frappe.logger().info(f"WhatsApp message sent to {to_phone}")
			return True

		frappe.log_error("WhatsApp API unexpected response", str(result))
		return False

	except Exception as e:
		frappe.log_error("WhatsApp send failed", str(e))
		return False


def _update_conversation(conversation_name, last_message, customer_name=None):
	"""Update the conversation summary fields."""
	try:
		conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
		conversation.message_count = (conversation.message_count or 0) + 1
		conversation.last_message = last_message
		conversation.last_message_at = datetime.now()
		if customer_name and not conversation.customer_name:
			conversation.customer_name = customer_name
		conversation.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error("Conversation update failed", str(e))
