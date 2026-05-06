# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

from datetime import datetime
import difflib
import re

import frappe
import requests

from .gemini_client import GeminiClient
from .context_builder import get_business_context, get_product_catalogue, build_ai_system_prompt


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

		# Reset business selection after ~7 hours so one customer can talk to multiple businesses in a day.
		# Use defensive access because the DB schema may not yet include the new field on some installs.
		conversation_has_assignment_field = False
		try:
			conversation_has_assignment_field = conversation.meta.has_field("business_assigned_at")
		except Exception:
			conversation_has_assignment_field = False
		assigned_at = None
		try:
			# Prefer Document-style .get (works for both dict-like and Document objects)
			assigned_at = conversation.get("business_assigned_at")
		except Exception:
			assigned_at = getattr(conversation, "business_assigned_at", None)
		if assigned_at:
			try:
				if isinstance(assigned_at, str):
					assigned_at = datetime.fromisoformat(assigned_at)
			except Exception:
				# If parsing fails, skip reset logic to avoid throwing
				assigned_at = None
		if assigned_at:
			elapsed = (datetime.now() - assigned_at).total_seconds() / 3600
			if elapsed > 7:
				conversation.business = None
				if conversation_has_assignment_field:
					# defensive save: only set attribute if the field exists on this site
					conversation.business_assigned_at = None
				conversation.save(ignore_permissions=True)

		# If no business selected yet:
		if not conversation.business:
			# First ever message in this conversation: ask for business name once.
			if (conversation.message_count or 0) == 0 or _looks_like_greeting(message.text_content):
				response_text = (
					f"Hi {message.customer_name}, thank you for reaching out to us, "
					"kindly assist us with the business name and whatever product you are trying to buy."
				)
				_send_whatsapp_message(
					phone_number_id=integration.phone_number_id,
					to_phone=message.from_phone,
					text=response_text,
					access_token=integration.access_token,
				)
				message.processed = True
				message.response_text = response_text
				message.response_sent_at = datetime.now()
				message.save(ignore_permissions=True)
				_update_conversation(
					conversation_name=conversation.name,
					last_message=message.text_content,
					customer_name=message.customer_name,
				)
				return

			# After the initial ask, treat incoming text as business selection and match fuzzily.
			# Also understand replies like "first one" or "2" from previous suggestions.
			possible_business = _resolve_business_selection_from_previous_prompt(
				conversation_name=conversation.name,
				user_text=message.text_content,
			)
			if not possible_business:
				possible_business = _find_business_by_name(message.text_content)
			if not possible_business:
				if not _has_any_business_records():
					response_text = (
						"I cannot find any Business profiles configured yet. "
						"Please ask the admin to create at least one Business record first."
					)
				else:
					candidates = _get_business_candidates(message.text_content, limit=3)
					if candidates:
						response_text = _build_candidates_message(candidates)
					else:
						response_text = (
							"I couldn't find that business name yet. Please type the business name again "
							"(for example: Tio's Galore or Busy Works Beats)."
						)
				_send_whatsapp_message(
					phone_number_id=integration.phone_number_id,
					to_phone=message.from_phone,
					text=response_text,
					access_token=integration.access_token,
				)
				message.processed = True
				message.response_text = response_text
				message.response_sent_at = datetime.now()
				message.save(ignore_permissions=True)
				_update_conversation(
					conversation_name=conversation.name,
					last_message=message.text_content,
					customer_name=message.customer_name,
				)
				return

			# Business matched: persist and send one-time welcome template.
			conversation.business = possible_business
			if conversation_has_assignment_field:
				conversation.business_assigned_at = datetime.now()
			conversation.save(ignore_permissions=True)

			context = get_business_context(
				business_name=possible_business,
				integration_name=message.integration,
			)
			business_label = context.get("business_name") or possible_business
			business_desc = (context.get("business_description") or "our products and services").strip()
			response_text = (
				f"Welcome to {business_label}. We handle {business_desc}. "
				"What would you like assistance with today?"
			)
			_send_whatsapp_message(
				phone_number_id=integration.phone_number_id,
				to_phone=message.from_phone,
				text=response_text,
				access_token=integration.access_token,
			)
			message.processed = True
			message.response_text = response_text
			message.response_sent_at = datetime.now()
			message.save(ignore_permissions=True)
			_update_conversation(
				conversation_name=conversation.name,
				last_message=message.text_content,
				customer_name=message.customer_name,
			)
			return
		
		# Now we have a business assigned. Proceed with normal AI processing.
		business_name = conversation.business
		
		gemini_config = _get_gemini_config(integration)
		if not gemini_config:
			return

		gemini = GeminiClient(
			api_key=gemini_config["api_key"],
			model=gemini_config["model"],
			temperature=gemini_config["temperature"],
		)

		# Fetch business context using the assigned business name
		business_context = get_business_context(
			business_name=business_name,
			integration_name=message.integration,
		)
		
		# Fetch product catalogue from Google Sheets
		product_info = get_product_catalogue(
			business_context.get("google_sheet_id", ""),
			business_context.get("google_sheet_range", ""),
			integration_name=message.integration,
		)
		
		# Check if this is the first message TO THIS BUSINESS (message_count == 1)
		is_first_msg = conversation.message_count == 0
		
		# Build system prompt with business context
		system_prompt = build_ai_system_prompt(business_context, product_info, is_first_message=is_first_msg)
		
		recent_messages = _get_recent_messages(conversation.name)
		
		# Build the full prompt combining system prompt and user message
		prompt = _build_prompt(
			system_prompt=system_prompt,
			customer_message=message.text_content,
			customer_name=message.customer_name,
			conversation_history=recent_messages,
		)

		# Check if handoff is needed before calling Gemini
		business = frappe.get_doc("Business", business_name) if business_name else None
		handoff_reason = _check_handoff_trigger(message.text_content, business)

		if handoff_reason:
			# Trigger handoff instead of AI response
			_create_handoff(
				business_name=business_name,
				conversation_name=conversation.name,
				message_id=message_id,
				reason=handoff_reason,
				customer_message=message.text_content,
			)
			# Notify customer that we're getting help
			_send_whatsapp_message(
				phone_number_id=integration.phone_number_id,
				to_phone=message.from_phone,
				text="I'm getting the business owner to help with this. Please hold on...",
				access_token=integration.access_token,
			)
			return

		ai_response = gemini.generate_response(
			prompt,
			max_tokens=business_context.get("ai_max_reply_length", 100),
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


def _build_prompt(system_prompt, customer_message, customer_name, conversation_history=""):
	"""Build the full prompt for Gemini using system prompt + customer message + history."""
	prompt = system_prompt
	
	if conversation_history:
		prompt += f"\n\nPrevious Conversation:\n{conversation_history}"
	
	prompt += f"\n\nCustomer Name: {customer_name}"
	prompt += f"\nCustomer Message: {customer_message}"
	prompt += "\n\nRespond in your established tone. Keep it concise and relevant to their question."
	
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


def _find_business_by_name(text):
	"""
	Try to find a Business doctype matching the customer's text.
	Uses exact, substring, and fuzzy matching on normalized names.
	"""
	if not text or len(text.strip()) < 2:
		return None
	
	try:
		businesses = _get_business_records_for_matching(limit=200)

		if not businesses:
			return None

		def normalize(value):
			v = (value or "").lower()
			v = re.sub(r"[^a-z0-9]+", " ", v)
			return " ".join(v.split())

		text_norm = normalize(text)
		if not text_norm:
			return None

		# 1) Exact normalized match
		for b in businesses:
			if normalize(b.get("business_name")) == text_norm:
				return b.get("name")

		# 2) Token overlap / substring style match
		for b in businesses:
			bn = normalize(b.get("business_name"))
			if text_norm in bn or bn in text_norm:
				return b.get("name")

		# 3) Fuzzy match for typos (e.g. "TioGlaore" -> "Tio's Galore")
		norm_to_name = {normalize(b.get("business_name")): b.get("name") for b in businesses}
		matches = difflib.get_close_matches(text_norm, list(norm_to_name.keys()), n=1, cutoff=0.6)
		if matches:
			return norm_to_name[matches[0]]

		return None
	
	except Exception as e:
		frappe.log_error("Error finding business by name", str(e))
		return None


def _get_business_candidates(text, limit=3):
	"""Return top matching enabled business names for suggestion UX."""
	if not text or len(text.strip()) < 2:
		return []

	try:
		businesses = _get_business_records_for_matching(limit=300)
		if not businesses:
			return []

		def normalize(value):
			v = (value or "").lower()
			v = re.sub(r"[^a-z0-9]+", " ", v)
			return " ".join(v.split())

		query = normalize(text)
		if not query:
			return []

		scored = []
		for b in businesses:
			label = b.get("business_name") or b.get("name")
			bn = normalize(label)
			ratio = difflib.SequenceMatcher(None, query, bn).ratio()
			if query in bn or bn in query:
				ratio = max(ratio, 0.9)
			scored.append((ratio, b.get("name"), label))

		scored.sort(key=lambda x: x[0], reverse=True)
		top = [item for item in scored if item[0] >= 0.45][:limit]
		return [{"name": n, "label": lbl} for _, n, lbl in top]
	except Exception as e:
		frappe.log_error("Error generating business candidates", str(e))
		return []


def _get_business_records_for_matching(limit=200):
	"""Return businesses with enabled records first, then any remaining records."""
	enabled = frappe.get_all(
		"Business",
		filters={"enabled": 1},
		fields=["name", "business_name"],
		limit_page_length=limit,
	)
	if enabled:
		return enabled

	# Fallback to all Business records if none are enabled.
	return frappe.get_all(
		"Business",
		fields=["name", "business_name"],
		limit_page_length=limit,
	)


def _has_any_business_records():
	"""Return True if at least one Business record exists."""
	try:
		return bool(frappe.db.exists("Business", {}))
	except Exception:
		return False


def _looks_like_greeting(text):
	"""Detect short greeting-only inputs so we don't treat them as business names."""
	t = (text or "").strip().lower()
	if not t:
		return True

	greetings = {
		"hi", "hey", "hello", "yo", "good morning", "good afternoon", "good evening", "hiya", "hallo",
	}
	# Remove punctuation/noise for robust greeting checks.
	t_clean = re.sub(r"[^a-z0-9\s]+", "", t)
	t_clean = " ".join(t_clean.split())

	if t_clean in greetings:
		return True

	# Handle forms like "hi there", "hello there"
	if t_clean.startswith("hi ") or t_clean.startswith("hello ") or t_clean.startswith("hey "):
		if len(t_clean.split()) <= 3:
			return True

	return False


def _build_candidates_message(candidates):
	"""Build numbered top-3 suggestion text to allow easy user selection."""
	lines = [
		"I found a few close matches — pick the one you meant:",
	]
	for idx, c in enumerate(candidates, start=1):
		lines.append(f"{idx}. {c.get('label')}")
	return "\n".join(lines)


def _resolve_business_selection_from_previous_prompt(conversation_name, user_text):
	"""Resolve replies like 'first one' or '2' based on the previous numbered suggestions."""
	if not conversation_name or not user_text:
		return None

	previous = _get_last_assistant_response(conversation_name)
	if not previous:
		return None

	# Parse previous suggestion list lines: "1. Business Name"
	options = []
	for line in (previous or "").splitlines():
		m = re.match(r"^\s*([1-3])\.\s+(.+?)\s*$", line)
		if m:
			options.append(m.group(2).strip())

	if not options:
		return None

	text = (user_text or "").strip().lower()
	index = None

	# Numeric selection
	if text in {"1", "2", "3"}:
		index = int(text) - 1

	# Word/ordinal selection
	if index is None:
		if any(token in text for token in ["first", "1st", "one", "option 1"]):
			index = 0
		elif any(token in text for token in ["second", "2nd", "two", "option 2"]):
			index = 1
		elif any(token in text for token in ["third", "3rd", "three", "option 3"]):
			index = 2

	if index is not None and 0 <= index < len(options):
		return _find_business_by_name(options[index])

	# If user typed one of the suggested names approximately, resolve that too.
	def normalize(value):
		v = (value or "").lower()
		v = re.sub(r"[^a-z0-9]+", " ", v)
		return " ".join(v.split())

	user_norm = normalize(text)
	for opt in options:
		opt_norm = normalize(opt)
		if user_norm == opt_norm or user_norm in opt_norm or opt_norm in user_norm:
			return _find_business_by_name(opt)

	return None


def _get_last_assistant_response(conversation_name):
	"""Fetch the latest assistant response_text for this conversation."""
	try:
		rows = frappe.db.sql(
			"""
			select response_text
			from `tabWhatsApp Message`
			where conversation = %s
			  and ifnull(response_text, '') != ''
			order by creation desc
			limit 1
			""",
			(conversation_name,),
			as_dict=True,
		)
		if rows:
			return rows[0].get("response_text")
		return None
	except Exception:
		return None


def _check_handoff_trigger(customer_message, business=None):
	"""Check if the customer message triggers a handoff to the business owner."""
	if not customer_message:
		return None

	msg_lower = customer_message.lower()

	# Universal handoff keywords (always trigger handoff)
	universal_keywords = [
		"refund",
		"complaint",
		"angry",
		"help",
		"manager",
		"owner",
		"human",
		"payment",
		"order number",
		"tracking",
		"delivery",
		"urgent",
		"emergency",
	]

	for keyword in universal_keywords:
		if keyword in msg_lower:
			return f"Customer mentioned: {keyword}"

	# Business-specific handoff keywords
	if business and business.handoff_keywords:
		keywords = [k.strip().lower() for k in business.handoff_keywords.split("\n") if k.strip()]
		for keyword in keywords:
			if keyword in msg_lower:
				return f"Business keyword match: {keyword}"

	return None


def _create_handoff(business_name, conversation_name, message_id, reason, customer_message):
	"""Create a WhatsApp Handoff record and trigger owner alert."""
	try:
		handoff = frappe.get_doc(
			{
				"doctype": "WhatsApp Handoff",
				"business": business_name,
				"conversation": conversation_name,
				"latest_message": message_id,
				"reason": reason,
				"status": "owner_notified",
				"customer_summary": f"Customer: {customer_message[:200]}",
				"owner_notified_at": datetime.now(),
			}
		)
		handoff.insert(ignore_permissions=True)
		frappe.logger().info(f"Handoff created: {handoff.name}")

		# Alert the owner via WhatsApp
		_alert_owner_whatsapp(business_name, conversation_name, message_id, reason)

		return handoff.name
	except Exception as e:
		frappe.log_error("Handoff creation failed", str(e))
		return None


def _alert_owner_whatsapp(business_name, conversation_name, message_id, reason):
	"""Send a WhatsApp alert to the business owner about the handoff."""
	try:
		business = frappe.get_doc("Business", business_name)
		if not business.owner_phone_number:
			frappe.log_error("Owner phone missing", f"Business {business_name} has no owner WhatsApp number")
			return

		conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
		msg = frappe.get_doc("WhatsApp Message", message_id)
		integration = frappe.get_doc("WhatsApp Integration", conversation.integration)

		if not integration.enabled:
			frappe.log_error("Integration disabled", f"Integration {conversation.integration} is disabled")
			return

		alert_text = f"""🔔 Handoff Needed

Customer: {conversation.customer_name or conversation.customer_phone}
Request: {msg.text_content[:100]}...

Reason: {reason}

Status: Awaiting your action"""

		_send_whatsapp_message(
			phone_number_id=integration.phone_number_id,
			to_phone=business.owner_phone_number,
			text=alert_text,
			access_token=integration.access_token,
		)
		frappe.logger().info(f"Owner alert sent for handoff in {business_name}")

	except Exception as e:
		frappe.log_error("Owner WhatsApp alert failed", str(e))

