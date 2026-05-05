# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import hmac
import hashlib
import json
from datetime import datetime
import frappe
from frappe import logger

from .message_processor import process_whatsapp_message, _get_or_create_conversation


def verify_webhook_token(verify_token, hub_challenge):
	"""
	Verify webhook verification request from Meta
	
	Args:
		verify_token (str): Token from query params
		hub_challenge (str): Challenge from Meta
	
	Returns:
		str: Challenge if valid, None otherwise
	"""
	# First, try a global token from site config
	stored_token = frappe.conf.get("whatsapp_verify_token")
	if stored_token and verify_token == stored_token:
		return hub_challenge

	# Fallback: check any configured WhatsApp Integration records
	try:
		integrations = frappe.get_all("WhatsApp Integration", fields=["name", "verify_token"]) or []
		for it in integrations:
			it_token = it.get("verify_token")
			if it_token and verify_token == it_token:
				return hub_challenge
	except Exception as e:
		frappe.log_error(f"Error checking WhatsApp Integration tokens: {e}", "whatsapp_webhook.verify")

	# No matching token found
	frappe.log_error("WhatsApp verify token not configured or invalid", "Set whatsapp_verify_token in site config or add a Verify Token on the WhatsApp Integration")
	return None


def verify_signature(signature_header, payload, app_secret):
	"""
	Verify the X-Hub-Signature-256 header
	
	Args:
		signature_header (str): Value of X-Hub-Signature-256 header
		payload (bytes): Raw request body
		app_secret (str): WhatsApp app secret
	
	Returns:
		bool: True if signature is valid
	"""
	if not signature_header or not signature_header.startswith("sha256="):
		return False
	
	provided_signature = signature_header.split("=")[1]
	
	expected_signature = hmac.new(
		app_secret.encode(),
		payload,
		hashlib.sha256
	).hexdigest()
	
	return hmac.compare_digest(provided_signature, expected_signature)


@frappe.whitelist(allow_guest=True)
def webhook():
	"""
	Main webhook endpoint
	- GET: Verification handshake from Meta
	- POST: Incoming messages from Meta
	"""
	request = frappe.request
	method = request.method
	
	if method == "GET":
		# Verification handshake
		hub_mode = request.args.get("hub.mode")
		hub_verify_token = request.args.get("hub.verify_token")
		hub_challenge = request.args.get("hub.challenge")
		
		challenge = verify_webhook_token(hub_verify_token, hub_challenge)
		
		if challenge:
			frappe.logger().info("Webhook verification successful")
			frappe.local.response.type = "txt"
			frappe.local.response.doctype = "whatsapp_webhook"
			frappe.local.response.result = challenge
			return
		else:
			frappe.logger().warning("Webhook verification failed - invalid token")
			return "Unauthorized", 403
	
	elif method == "POST":
		# Message reception
		signature = request.headers.get("X-Hub-Signature-256", "")
		
		# Get raw payload for signature verification
		payload = request.get_data()
		
		# Get app secret - try global config first. If not present, attempt
		# to locate the correct integration's app_secret using the payload
		# metadata (phone_number_id) or by trying enabled integrations.
		app_secret = frappe.conf.get("whatsapp_app_secret")
		verified = False
		integration_used = None

		if app_secret:
			try:
				if verify_signature(signature, payload, app_secret):
					verified = True
			except Exception as e:
				frappe.log_error("Error verifying signature with global app secret", str(e))

		# If global secret not available or didn't verify, try to extract
		# phone_number_id from the payload to find the matching integration.
		if not verified:
			try:
				parsed = json.loads(payload.decode() if isinstance(payload, (bytes, bytearray)) else payload)
				phone_number_id = None
				for entry in parsed.get("entry", []) or []:
					for change in entry.get("changes", []) or []:
						value = change.get("value", {})
						meta = value.get("metadata", {})
						if meta.get("phone_number_id"):
							phone_number_id = meta.get("phone_number_id")
							break
					if phone_number_id:
						break

				if phone_number_id:
					integrations = frappe.get_list(
						"WhatsApp Integration",
						filters={"phone_number_id": phone_number_id, "enabled": 1},
						fields=["name"],
						limit=1,
					) or []

					if integrations:
						try:
							it_doc = frappe.get_doc("WhatsApp Integration", integrations[0].name)
							it_secret = it_doc.get("app_secret")
							if it_secret and verify_signature(signature, payload, it_secret):
								verified = True
								integration_used = it_doc.name
						except Exception as e:
							frappe.log_error("Error loading WhatsApp Integration for signature check", str(e))

			except Exception as e:
				# Parsing failed; continue to broader fallback below
				frappe.log_error("Failed to parse webhook JSON for app_secret lookup", str(e))

		# As a last resort, try all enabled integrations that have an app_secret
		if not verified:
			try:
				integrations = frappe.get_all("WhatsApp Integration", filters={"enabled": 1}, fields=["name", "app_secret"]) or []
				for it in integrations:
					it_secret = it.get("app_secret")
					if not it_secret:
						continue
					try:
						if verify_signature(signature, payload, it_secret):
							verified = True
							integration_used = it.get("name")
							break
					except Exception:
						# ignore and continue trying others
						continue
			except Exception as e:
				frappe.log_error("Error checking integration app_secrets for signature", str(e))

		if not verified:
			frappe.logger().warning("Invalid signature received or app secret not configured")
			return {"status": "unauthorized"}, 401
		
		# Parse JSON
		try:
			data = request.get_json()
		except Exception as e:
			frappe.log_error("Failed to parse webhook JSON", str(e))
			return {"status": "error"}, 400
		
		# Process asynchronously (return 200 immediately)
		try:
			_queue_messages(data)
			frappe.db.commit()
			return {"status": "ok"}, 200
		except Exception as e:
			frappe.log_error("Webhook processing error", str(e))
			return {"status": "error"}, 500
	
	else:
		return {"status": "method_not_allowed"}, 405


def _queue_messages(data):
	"""
	Extract messages from webhook data and queue for processing
	
	Args:
		data (dict): Parsed webhook JSON from Meta
	"""
	try:
		# Navigate the Meta webhook structure
		entries = data.get("entry", [])
		
		for entry in entries:
			changes = entry.get("changes", [])
			
			for change in changes:
				value = change.get("value", {})
				messages = value.get("messages", [])
				metadata = value.get("metadata", {})
				contacts = value.get("contacts", [])
				
				phone_number_id = metadata.get("phone_number_id")
				
				# Find the integration by phone_number_id
				integrations = frappe.get_list(
					"WhatsApp Integration",
					filters={"phone_number_id": phone_number_id, "enabled": 1},
					limit=1
				)
				
				if not integrations:
					frappe.logger().warning(f"No integration found for phone_number_id: {phone_number_id}")
					continue
				
				integration_name = integrations[0].name
				
				# Get customer name from contacts
				customer_name = "Unknown"
				if contacts:
					customer_name = contacts[0].get("profile", {}).get("name", "Unknown")
				
				# Process each message
				for message in messages:
					try:
						message_id = message.get("id")
						from_phone = message.get("from")
						timestamp = int(message.get("timestamp", 0))
						message_type = message.get("type", "unknown")
						
						# Extract message content based on type
						text_content = ""
						image_id = None
						
						if message_type == "text":
							text_content = message.get("text", {}).get("body", "")
						elif message_type == "image":
							image_id = message.get("image", {}).get("id")
							text_content = message.get("image", {}).get("caption", "")
						else:
							# Unsupported type, but still log it
							text_content = f"Unsupported message type: {message_type}"

						conversation = _get_or_create_conversation(
							integration=integration_name,
							customer_phone=from_phone,
							customer_name=customer_name,
						)
						
						# Create WhatsApp Message record
						msg_doc = frappe.get_doc({
							"doctype": "WhatsApp Message",
							"conversation": conversation.name,
							"integration": integration_name,
							"from_phone": from_phone,
							"customer_name": customer_name,
							"message_id": message_id,
							"timestamp": timestamp,
							"message_type": message_type if message_type in ["text", "image", "document"] else "unsupported",
							"text_content": text_content,
							"image_id": image_id,
							"processed": False
						})
						msg_doc.insert()

						conversation.message_count = (conversation.message_count or 0) + 1
						conversation.last_message = text_content
						conversation.last_message_at = datetime.now()
						if customer_name and not conversation.customer_name:
							conversation.customer_name = customer_name
						conversation.save(ignore_permissions=True)
						
						# Queue async processing
						frappe.enqueue(
							process_whatsapp_message,
							message_id=message_id,
							queue="default"
						)
						
						frappe.logger().info(f"Message {message_id} queued for processing")
					
					except Exception as e:
						frappe.log_error("Error processing individual message", str(e))
						continue
	
	except Exception as e:
		frappe.log_error("Error queuing messages", str(e))
		raise
