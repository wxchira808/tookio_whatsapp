# Copyright (c) 2026, Tookio and contributors
# For license information, please see license.txt

import requests
import time
import frappe
from frappe import logger


class GeminiClient:
	"""Wrapper for Gemini API calls"""

	def __init__(self, api_key, model="gemini-1.5-flash", temperature=0.7):
		self.api_key = api_key
		self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
		self.model = self._normalize_model_name(model)
		self.temperature = temperature

	def _normalize_model_name(self, model):
		if not model:
			return "gemini-1.5-flash"
		if model.startswith("models/"):
			return model.replace("models/", "", 1)
		return model
	
	def generate_response(self, system_instruction, messages, tools=None, max_tokens=500, timeout=30):
		"""
		Call Gemini API and return text response or function call
		"""
		max_attempts = 4
		backoff_base = 1.0
		url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
		
		payload = {
			"systemInstruction": {
				"parts": [{"text": system_instruction}]
			},
			"contents": messages,
			"generationConfig": {
				"maxOutputTokens": max_tokens,
				"temperature": self.temperature
			}
		}
		
		if tools:
			payload["tools"] = tools
		
		headers = {"Content-Type": "application/json"}

		for attempt in range(1, max_attempts + 1):
			try:
				response = requests.post(url, json=payload, headers=headers, timeout=timeout)
				response.raise_for_status()
				result = response.json()
				
				if "candidates" in result and len(result["candidates"]) > 0:
					candidate = result["candidates"][0]
					if "content" in candidate and "parts" in candidate["content"]:
						parts = candidate["content"]["parts"]
						if len(parts) > 0:
							# Look for functionCall inside parts
							has_call = False
							for part in parts:
								if "functionCall" in part:
									return {"type": "functionCall", "call": part["functionCall"], "parts": parts}
							# If no functionCall, return the first text
							if "text" in parts[0]:
								return {"type": "text", "text": parts[0]["text"]}
				
				frappe.log_error("Gemini returned unexpected response format", str(result))
				return None

			except requests.exceptions.RequestException as e:
				# Try to get status code and body if available
				status = None
				body = None
				if hasattr(e, 'response') and e.response is not None:
					status = getattr(e.response, 'status_code', None)
					try:
						body = e.response.text
					except Exception:
						body = None

				# Log detailed info
				frappe.log_error(
					"Gemini API request failed",
					f"attempt={attempt} status={status} error={str(e)} body={body}",
				)

				# Retry on 429 or 5xx server errors
				if status in (429, 500, 502, 503, 504) and attempt < max_attempts:
					sleep = backoff_base * (2 ** (attempt - 1))
					time.sleep(sleep)
					continue
				# No retry, return None
				return None

			except Exception as e:
				frappe.log_error("Gemini API error", str(e))
				return None
	
	def generate_response_with_image(self, text_prompt, image_id, access_token, max_tokens=150, timeout=30):
		"""
		Call Gemini with image (currently simplified - just processes text)
		
		Args:
			text_prompt (str): Text prompt
			image_id (str): Meta's image ID
			access_token (str): WhatsApp access token to fetch image
			max_tokens (int): Max tokens
			timeout (int): Request timeout
		
		Returns:
			str: Generated response
		"""
		# For MVP, just use text. Image vision can be added later
		return self.generate_response(text_prompt, max_tokens, timeout)
