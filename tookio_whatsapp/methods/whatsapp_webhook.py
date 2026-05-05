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
	# Get stored verify token (you set this in WhatsApp Integration)
	stored_token = frappe.conf.get("whatsapp_verify_token")
	
	if not stored_token:
		frappe.log_error("WhatsApp verify token not configured", "Set whatsapp_verify_token in site config")
		return None
	
	if verify_token == stored_token:
		return hub_challenge
	
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
		
		# Get app secret - try from config first, then from WhatsApp Integration
		app_secret = frappe.conf.get("whatsapp_app_secret")
		
		if not app_secret:
			frappe.log_error("WhatsApp app secret not configured", "Set whatsapp_app_secret in site config")
			return {"status": "error"}, 500
		
		if not verify_signature(signature, payload, app_secret):
			frappe.logger().warning("Invalid signature received")
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
