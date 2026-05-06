# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import json
import requests
import frappe


def get_business_context(integration_name):
	"""
	Fetch full business context: name, description, support details, and AI behavior settings.
	
	Args:
		integration_name (str): Name of WhatsApp Integration
		
	Returns:
		dict: Business context including name, description, support_email, owner info, AI settings
	"""
	try:
		# Get the integration
		integration = frappe.db.get_value(
			"WhatsApp Integration",
			integration_name,
			["business_name", "google_sheet_id", "google_sheet_range"],
			as_dict=True,
		)
		
		if not integration:
			frappe.log_error("Integration not found", f"WhatsApp Integration {integration_name}")
			return {}
		
		business_name = integration.get("business_name", "")
		
		# Try to fetch the Business doctype if it exists and is linked
		business_data = {}
		if business_name:
			try:
				business = frappe.db.get_value(
					"Business",
					business_name,
					[
						"business_name",
						"business_description",
						"owner_phone_number",
						"owner_name",
						"support_email",
						"support_phone",
						"ai_tone",
						"ai_max_reply_length",
						"ai_custom_instructions",
						"handoff_keywords",
					],
					as_dict=True,
				)
				if business:
					business_data = business
			except Exception as e:
				frappe.log_error("Business doctype lookup failed (may not exist)", str(e))
		
		# Build context dict
		context = {
			"business_name": business_data.get("business_name") or integration.get("business_name"),
			"business_description": business_data.get("business_description", ""),
			"owner_name": business_data.get("owner_name", ""),
			"owner_phone": business_data.get("owner_phone_number", ""),
			"support_email": business_data.get("support_email", ""),
			"support_phone": business_data.get("support_phone", ""),
			"ai_tone": business_data.get("ai_tone", "professional"),  # default: professional
			"ai_max_reply_length": business_data.get("ai_max_reply_length") or 150,  # default: 150 tokens
			"ai_custom_instructions": business_data.get("ai_custom_instructions", ""),
			"handoff_keywords": business_data.get("handoff_keywords", ""),
			"google_sheet_id": integration.get("google_sheet_id", ""),
			"google_sheet_range": integration.get("google_sheet_range", "Products!A1:E100"),
		}
		
		return context
	
	except Exception as e:
		frappe.log_error("Error building business context", str(e))
		return {}


def get_product_catalogue(sheet_id, sheet_range, oauth_token=None):
	"""
	Fetch product catalogue from Google Sheets.
	
	Args:
		sheet_id (str): Google Sheet ID
		sheet_range (str): Range like "Products!A1:E100"
		oauth_token (str): Optional OAuth token for private sheets
		
	Returns:
		str: Formatted product list for AI prompt, or empty string if fetch fails
	"""
	if not sheet_id or not sheet_range:
		return ""
	
	try:
		# Use Google Sheets public API (no auth needed if sheet is public)
		url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{sheet_range}"
		
		# Note: This requires the sheet to be public or we need a proper API key.
		# For now, use a simple public read (no authentication).
		# If you have a Gemini API key, you can reuse it as a Google API key if it's multi-service.
		# Better approach: store a separate Google API key in site_config or integration config.
		
		# Try to get API key from site config
		api_key = frappe.conf.get("google_sheets_api_key")
		if not api_key:
			# Fallback: try Gemini API key (if it's a Google API key, it may work for Sheets too)
			# But this is not reliable - better to have a dedicated key.
			frappe.log_error(
				"Google Sheets API key missing",
				"Set google_sheets_api_key in site_config.json or integration config"
			)
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
		frappe.log_error("Failed to fetch product catalogue from Google Sheets", str(e))
		return ""


def build_ai_system_prompt(business_context, product_info=""):
	"""
	Build the system prompt for AI with business context and personality.
	
	Args:
		business_context (dict): From get_business_context()
		product_info (str): From get_product_catalogue()
		
	Returns:
		str: System prompt for Gemini
	"""
	business_name = business_context.get("business_name", "Customer Service")
	business_desc = business_context.get("business_description", "")
	owner_name = business_context.get("owner_name", "")
	support_email = business_context.get("support_email", "")
	support_phone = business_context.get("support_phone", "")
	ai_tone = business_context.get("ai_tone", "professional")
	custom_instructions = business_context.get("ai_custom_instructions", "")
	
	prompt_lines = []
	
	# Core identity
	prompt_lines.append(f"You are a customer service representative for {business_name}.")
	
	# Business description
	if business_desc:
		prompt_lines.append(f"About us: {business_desc}")
	
	# Tone/personality
	if ai_tone == "casual":
		prompt_lines.append("Your tone is friendly, casual, and conversational. Use simple language and emojis sparingly. Keep it human and warm.")
	elif ai_tone == "formal":
		prompt_lines.append("Your tone is professional, formal, and courteous. Use proper grammar and maintain a business-like demeanor.")
	elif ai_tone == "concise":
		prompt_lines.append("Your responses are very brief and to the point. 1-2 sentences max. No fluff.")
	else:  # professional (default)
		prompt_lines.append("Your tone is professional and helpful. Be clear and concise.")
	
	# Support details
	if support_email or support_phone:
		support_line = "For additional support, customers can contact:"
		if support_email:
			support_line += f" email: {support_email}"
		if support_phone:
			support_line += f" phone: {support_phone}"
		prompt_lines.append(support_line)
	
	# Product info
	if product_info:
		prompt_lines.append("\n" + product_info)
	
	# Custom instructions (override everything)
	if custom_instructions:
		prompt_lines.append("\nSpecial Instructions:")
		prompt_lines.append(custom_instructions)
	
	# Closing instruction
	prompt_lines.append("\nRespond helpfully and stay in character. If you cannot help, suggest the customer contact support.")
	
	return "\n".join(prompt_lines)
