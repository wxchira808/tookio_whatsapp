# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import json
import requests
import frappe
from datetime import datetime, timedelta
from urllib.parse import quote


def _extract_sheet_id(sheet_url_or_id):
	"""
	Extract just the sheet ID from a full Google Sheets URL or return the ID if already extracted.
	Examples:
	  Input: https://docs.google.com/spreadsheets/d/1ABC123/edit?usp=sharing
	  Output: 1ABC123
	  Input: 1ABC123
	  Output: 1ABC123
	"""
	if not sheet_url_or_id:
		return ""
	if "/d/" in sheet_url_or_id:
		# Extract from URL
		try:
			parts = sheet_url_or_id.split("/d/")
			if len(parts) > 1:
				sheet_id = parts[1].split("/")[0]  # Get ID before the next /
				return sheet_id.strip()
		except Exception:
			pass
	# Return as-is if it looks like just an ID
	return sheet_url_or_id.strip()


def needs_business_selection(conversation):
	"""
	Check if conversation needs to ask for business selection.
	Returns True if:
	- Business not assigned, OR
	- Business assigned > 7 hours ago
	"""
	if not conversation.get("business"):
		return True
	
	assigned_at = conversation.get("business_assigned_at")
	if not assigned_at:
		return True
	
	# Parse datetime if it's a string
	if isinstance(assigned_at, str):
		try:
			assigned_at = datetime.fromisoformat(assigned_at)
		except Exception:
			return True
	
	# Check if > 7 hours old
	hours_elapsed = (datetime.now() - assigned_at).total_seconds() / 3600
	return hours_elapsed > 7


def get_business_context(business_name, integration_name=None, google_sheet_id=None, google_sheet_range=None):
	"""
	Fetch full business context: name, description, support details, and AI behavior settings.
	
	Args:
		business_name (str): Name of Business doctype
		integration_name (str): Optional integration name (for fallback sheet config)
		google_sheet_id (str): Optional sheet ID override
		google_sheet_range (str): Optional sheet range override
		
	Returns:
		dict: Business context including name, description, support_email, owner info, AI settings
	"""
	try:
		# Try to fetch the Business doctype
		business_data = {}
		if business_name:
			# Defensive lookup: only ask the database for fields that exist in the
			# current site's DocType schema. This prevents SQL errors on older sites
			# that have not been migrated yet.
			try:
				meta = frappe.get_meta("Business")
				requested_fields = [
					"business_name",
					"business_description",
					"owner_phone_number",
					"owner_name",
					"handoff_keywords",
					"support_email",
					"support_phone",
					"ai_tone",
					"ai_max_reply_length",
					"ai_custom_instructions",
					"google_sheet_id",
					"google_sheet_range",
					"google_api_key",
				]
				available_fields = [field for field in requested_fields if meta.has_field(field)]
				if available_fields:
					business = frappe.db.get_value(
						"Business",
						business_name,
						available_fields,
						as_dict=True,
					)
					if business:
						business_data = business
			except Exception as e:
				frappe.log_error("Business doctype lookup failed", str(e))
		
		# If no sheet ID provided, try to get the sheet details from integration.
		if integration_name:
			try:
				integration = frappe.db.get_value(
					"WhatsApp Integration",
					integration_name,
					["google_sheet_id", "google_sheet_range"],
					as_dict=True,
				)
				if integration:
					if not google_sheet_id:
						google_sheet_id = integration.get("google_sheet_id")
					if not google_sheet_range:
						google_sheet_range = integration.get("google_sheet_range")
			except Exception:
				pass
		
		# Build context dict (prefer business-scoped sheet/key if present)
		context = {
			"business_name": business_data.get("business_name") or business_name,
			"business_description": business_data.get("business_description", ""),
			"owner_name": business_data.get("owner_name", ""),
			"owner_phone": business_data.get("owner_phone_number", ""),
			"support_email": business_data.get("support_email", ""),
			"support_phone": business_data.get("support_phone", ""),
			"ai_tone": business_data.get("ai_tone", "casual"),  # default: casual
			"ai_max_reply_length": business_data.get("ai_max_reply_length") or 100,  # default: 100 tokens (shorter!)
			"ai_custom_instructions": business_data.get("ai_custom_instructions", ""),
			"handoff_keywords": business_data.get("handoff_keywords", ""),
			"google_sheet_id": business_data.get("google_sheet_id") or google_sheet_id or "",
			"google_sheet_range": business_data.get("google_sheet_range") or google_sheet_range or "Products!A1:E100",
			"google_api_key": business_data.get("google_api_key", ""),
		}
		
		return context
	
	except Exception as e:
		frappe.log_error("Error building business context", str(e))
		return {}


def get_product_catalogue(sheet_id, sheet_range, oauth_token=None, integration_name=None, api_key=None):
	"""
	Fetch product catalogue from Google Sheets.
	
	Args:
		sheet_id (str): Google Sheet ID or full URL
		sheet_range (str): Range like "Products!A1:E100"
		oauth_token (str): Optional OAuth token for private sheets
		
	Returns:
		str: Formatted product list for AI prompt, or empty string if fetch fails
	"""
	# Extract just the sheet ID in case user pasted a full URL
	sheet_id = _extract_sheet_id(sheet_id)
	if not sheet_id or not sheet_range:
		return ""
	
	try:
		# Use Google Sheets public API (no auth needed if sheet is public)
		# URL-encode the range to handle special characters like !
		encoded_range = quote(sheet_range, safe='')
		url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_range}"
		
		# Note: This requires the sheet to be public or we need a proper API key.
		# For now, use a simple public read (no authentication).
		# If you have a Gemini API key, you can reuse it as a Google API key if it's multi-service.
		# Better approach: store a separate Google API key in site_config or integration config.
		
		# Prefer an explicit api_key passed in from business context. Otherwise
		# fall back to integration-level or site_config keys.
		if not api_key:
			api_key = frappe.conf.get("google_sheets_api_key") or frappe.conf.get("google_api_key")
			if not api_key and integration_name:
				try:
					integration = frappe.db.get_value(
						"WhatsApp Integration",
						integration_name,
						["google_api_key"],
						as_dict=True,
					)
					if integration:
						api_key = integration.get("google_api_key") or ""
				except Exception:
					pass
		if not api_key:
			frappe.logger().info("Skipping Google Sheets catalogue fetch because no Google API key is configured")
			return ""
		
		params = {"key": api_key}
		response = requests.get(url, params=params, timeout=10)
		response.raise_for_status()
		
		data = response.json()
		values = data.get("values", [])
		
		if not values:
			return ""
		
		# Format rows into readable product list
		lines = []
		
		# First row is usually headers
		if len(values) > 0:
			headers = values[0]
			lines.append("Product Catalogue:")
			lines.append("---")
			
			# Remaining rows are products
			for row in values[1:]:
				if row:
					# Simple format: join columns with " | "
					formatted_row = " | ".join(str(cell).strip() for cell in row)
					lines.append(formatted_row)
		
		return "\n".join(lines)
	
	except Exception as e:
		error_msg = str(e)
		# Provide helpful error message for common issues
		if "INVALID_ARGUMENT" in error_msg or "Unable to parse range" in error_msg:
			frappe.logger().warning(
				f"Google Sheets range error (likely wrong sheet name): {sheet_range}. "
				f"Check that your Google Sheet has a tab/sheet named '{sheet_range.split('!')[0]}'"
			)
		elif "404" in error_msg or "Not Found" in error_msg:
			frappe.logger().warning(f"Google Sheet not found: {sheet_id}. Check the sheet ID.")
		elif "401" in error_msg or "Unauthorized" in error_msg:
			frappe.logger().warning(f"Google Sheets API unauthorized. Check your API key.")
		else:
			frappe.log_error("Failed to fetch product catalogue from Google Sheets", error_msg)
		return ""


def build_ai_system_prompt(business_context, product_info="", is_first_message=False):
	"""
	Build the system prompt for AI with business context and personality.
	
	Args:
		business_context (dict): From get_business_context()
		product_info (str): From get_product_catalogue()
		is_first_message (bool): True if this is the first message in conversation
		
	Returns:
		str: System prompt for Gemini
	"""
	business_name = business_context.get("business_name", "Customer Service")
	business_desc = business_context.get("business_description", "")
	support_email = business_context.get("support_email", "")
	support_phone = business_context.get("support_phone", "")
	ai_tone = business_context.get("ai_tone", "casual")
	custom_instructions = business_context.get("ai_custom_instructions", "")
	
	prompt_lines = []
	
	# Core identity
	prompt_lines.append(f"You are a customer service rep for {business_name}.")
	
	# Business description (short context only)
	if business_desc:
		prompt_lines.append(f"{business_desc}")
	
	# Tone/personality - simplified
	if ai_tone == "casual":
		prompt_lines.append("Be casual, friendly, and conversational. Keep it short and human. No formal stuff unless asked.")
	elif ai_tone == "formal":
		prompt_lines.append("Be professional and formal. Use proper grammar and courteous language.")
	elif ai_tone == "concise":
		prompt_lines.append("Keep replies super short (1-2 sentences max). No fluff.")
	else:  # professional (default)
		prompt_lines.append("Be helpful and professional. Keep it concise.")
	
	# IMPORTANT: Only greet on first message
	if is_first_message:
		prompt_lines.append("Since this is the first message, greet them warmly but briefly.")
	else:
		prompt_lines.append("This is NOT the first message. Do NOT greet them or say 'thank you for reaching out' or 'regards' or any formal closing. Just answer their question directly.")
	
	# Support details (if available)
	if support_email or support_phone:
		support_line = "For urgent issues, customers can reach support at:"
		if support_email:
			support_line += f" {support_email}"
		if support_phone:
			support_line += f" or {support_phone}"
		prompt_lines.append(support_line)
	
	# Product info
	if product_info:
		prompt_lines.append("\n" + product_info)
	
	# Custom instructions (can override everything)
	if custom_instructions:
		prompt_lines.append("\nSpecial instructions for this business:")
		prompt_lines.append(custom_instructions)
	
	# Closing instruction
	prompt_lines.append("\nStay in character and be helpful. Keep replies short and natural.")
	
	return "\n".join(prompt_lines)
