# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import frappe
import requests
from urllib.parse import quote


def _extract_sheet_id(sheet_url_or_id):
	"""
	Extract just the sheet ID from a full Google Sheets URL or return the ID if already extracted.
	"""
	if not sheet_url_or_id:
		return ""
	if "/d/" in sheet_url_or_id:
		try:
			parts = sheet_url_or_id.split("/d/")
			if len(parts) > 1:
				sheet_id = parts[1].split("/")[0]
				return sheet_id.strip()
		except Exception:
			pass
	return sheet_url_or_id.strip()


class GoogleSheetsClient:
	"""Handles fetching data from Google Sheets using Sheets API v4"""
	
	def __init__(self, sheet_id, api_key=None):
		"""
		Initialize Google Sheets client
		
		Args:
			sheet_id (str): Google Sheet ID or full URL
			api_key (str): Optional Google API key (uses frappe.conf if not provided)
		"""
		# Extract just the ID in case user pasted a full URL
		self.sheet_id = _extract_sheet_id(sheet_id)
		self.api_key = api_key or self._get_api_key()
		self.base_url = "https://sheets.googleapis.com/v4/spreadsheets"
	
	def _get_api_key(self):
		"""Get Google API key from Frappe config"""
		return frappe.conf.get("google_api_key") or frappe.conf.get("google_sheets_api_key")
	
	def fetch_products(self, sheet_range="Products!A1:J500"):
		"""
		Fetch product data from Google Sheet.
		Automatically extracts sheet ID if user provided a full URL.
		
		Args:
			sheet_range (str): Range to fetch (e.g., 'Sheet1!A1:J100')
		
		Returns:
			list: List of dicts with product data, or empty list if error
		"""
		try:
			if not self.api_key:
				frappe.logger().info("Skipping Google Sheets fetch because no API key is configured")
				return []
			
				url = f"{self.base_url}/{self.sheet_id}/values/{quote(sheet_range, safe='')}"
			params = {"key": self.api_key}
			
			response = requests.get(url, params=params, timeout=10)
			response.raise_for_status()
			
			data = response.json()
			
			# Parse values into product dicts
			if "values" not in data or len(data["values"]) == 0:
				frappe.log_error("Google Sheets", f"No data found in range {sheet_range}")
				return []
			
			rows = data["values"]
			headers = rows[0]  # First row is headers
			products = []
			
			# Typical columns: SKU, Product Name, Category, Price, Currency, Stock, Description, Variants, Image URL, Product URL
			for row in rows[1:]:
				# Pad row if it's shorter than headers
				while len(row) < len(headers):
					row.append("")
				
				product = {}
				for i, header in enumerate(headers):
					product[header.strip()] = row[i].strip() if i < len(row) else ""
				
				products.append(product)
			
			frappe.logger().info(f"Fetched {len(products)} products from Google Sheet {self.sheet_id}")
			return products
		
		except requests.exceptions.RequestException as e:
			error_msg = str(e)
			if "INVALID_ARGUMENT" in error_msg or "Unable to parse range" in error_msg:
				frappe.logger().warning(
					f"Google Sheets range error (likely wrong sheet name): {sheet_range}. "
					f"Check that your Google Sheet has a tab/sheet named '{sheet_range.split('!')[0]}'"
				)
			else:
				frappe.log_error("Google Sheets API Error", error_msg)
			return []
		except Exception as e:
			frappe.log_error("Google Sheets parsing error", str(e))
			return []
	
	def format_products_for_prompt(self, products, max_products=5):
		"""
		Format product list into a concise string for Gemini prompt
		
		Args:
			products (list): List of product dicts
			max_products (int): Max products to include in prompt
		
		Returns:
			str: Formatted product summary
		"""
		if not products:
			return ""
		
		# Limit to most relevant products for context
		summary_products = products[:max_products]
		
		lines = ["AVAILABLE PRODUCTS:"]
		for product in summary_products:
			# Try common column names
			sku = product.get("SKU", "")
			name = product.get("Product Name", product.get("Name", ""))
			price = product.get("Price", "")
			currency = product.get("Currency", "USD")
			stock = product.get("Stock", product.get("Stock Level", ""))
			category = product.get("Category", "")
			description = product.get("Description", "")
			
			# Build product line
			product_line = f"- {name}"
			if sku:
				product_line += f" (SKU: {sku})"
			if category:
				product_line += f" [{category}]"
			if price:
				product_line += f" - {currency} {price}"
			if stock:
				product_line += f" (In Stock: {stock})"
			
			if description and len(description) > 100:
				product_line += f" - {description[:100]}..."
			elif description:
				product_line += f" - {description}"
			
			lines.append(product_line)
		
		return "\n".join(lines)


def fetch_products_for_integration(integration_name):
	"""
	Fetch products from Google Sheet configured for an integration
	
	Args:
		integration_name (str): Name of WhatsApp Integration document
	
	Returns:
		str: Formatted product summary for prompt, or empty string if error
	"""
	try:
		integration = frappe.get_doc("WhatsApp Integration", integration_name)
		
		if not integration.google_sheet_id:
			return ""
		
		client = GoogleSheetsClient(
			sheet_id=integration.google_sheet_id,
			api_key=integration.get("google_api_key") or frappe.conf.get("google_api_key") or frappe.conf.get("google_sheets_api_key")
		)
		
		products = client.fetch_products(
			sheet_range=integration.google_sheet_range or "Products!A1:J500"
		)
		
		return client.format_products_for_prompt(products, max_products=5)
	
	except Exception as e:
		frappe.log_error("Integration products fetch failed", str(e))
		return ""
