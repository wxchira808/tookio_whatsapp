# Tookio WhatsApp Frappe App - Complete Build Context

**Last Updated:** May 2026  
**Project:** tookio_whatsapp (Frappe App)  
**Location:** Nairobi, Kenya  
**Use Case:** Multi-tenant WhatsApp AI chatbot for Kenyan online sellers

---

## PROJECT OVERVIEW

### What You're Building

A Frappe app that integrates WhatsApp Business Cloud API with n8n and Gemini AI to create an automated customer service bot for small online retailers.

**Key Features:**
- Accept incoming WhatsApp messages via Meta webhook
- Route to Gemini AI for intelligent responses
- Handle product lookups from Google Sheets
- Process images with Gemini Vision API
- Log conversations to Frappe
- Support human escalation/handoff
- Multi-tenant support (multiple clients)
- Free messaging within 24-hour customer service window

### Architecture

```
Customer WhatsApp → Meta Servers → Your Frappe Webhook → n8n Workflow
                                         ↓
                                   Gemini API
                                         ↓
                                   Google Sheets
                                         ↓
                                   Frappe Logging
                                         ↓
                                   Response → WhatsApp
```

---

## CRITICAL CONTEXT

### Why This Approach (No Twilio)

You're using **Meta's WhatsApp Cloud API directly** instead of Twilio because:

1. **Cost:** No Twilio markup ($0.005/msg gone)
2. **Free 24-hour window:** Customer initiates conversation = free messages
3. **Customer ownership:** Each client owns their own WhatsApp Business Account
4. **Direct control:** You manage webhooks on your own server
5. **Scalability:** One webhook handles all clients (with routing logic)

### Pricing Reality

**Per client, per month (~100 messages/day):**
- WhatsApp number: ~KES 500
- Messages (most free within 24h): ~KES 100-200
- Gemini AI: ~KES 50-100
- Your infrastructure: KES 0 (already on VM)
- **Total cost per client: ~KES 700**
- **You charge: KES 5,000-10,000**
- **Your margin: 70-80%**

### Tech Stack

- **Backend Framework:** Frappe (Python)
- **App Name:** tookio_whatsapp
- **Webhook Server:** Built into Frappe
- **AI Model:** Gemini 2.0 Flash (text + vision)
- **Product Storage:** Google Sheets (via client's account)
- **Message Storage:** Frappe DocTypes
- **Orchestration:** n8n (on your VM, separate from Frappe)
- **Hosting:** Your Contabo VM (62.171.168.124)

---

## WEBHOOK MECHANICS (Critical Understanding)

### How Meta Sends You Messages

**1. Verification Handshake (Setup)**

Meta does a GET request:
```
GET https://your-domain.com/api/resource/whatsapp/webhook?
    hub.mode=subscribe&
    hub.verify_token=YOUR_VERIFY_TOKEN&
    hub.challenge=RANDOM_CHALLENGE
```

Your webhook must:
1. Extract `hub.verify_token` from query params
2. Compare with your stored `VERIFY_TOKEN`
3. If match: return `hub.challenge` value
4. If no match: return 403

```python
# Pseudo-code
if request.method == "GET":
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Unauthorized", 403
```

**2. Message Reception (Ongoing)**

Meta does a POST request with message data:
```
POST https://your-domain.com/api/resource/whatsapp/webhook
Headers:
    X-Hub-Signature-256: sha256=<HMAC_SIGNATURE>
    Content-Type: application/json

Body: {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "254712345678",
                    "id": "wamid.XXX",
                    "timestamp": "1234567890",
                    "type": "text",
                    "text": {
                        "body": "Do you have iPhone cases?"
                    }
                }],
                "contacts": [{
                    "profile": {
                        "name": "Mary"
                    },
                    "wa_id": "254712345678"
                }],
                "metadata": {
                    "display_phone_number": "254123456789",
                    "phone_number_id": "123456789",
                    "business_account_id": "abc123"
                }
            }
        }]
    }]
}
```

Your webhook must:
1. Verify signature (security)
2. Extract customer data
3. Route to AI/logic
4. Store in Frappe
5. Return 200 OK immediately (within 30 seconds)

```python
# Pseudo-code
if request.method == "POST":
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(signature, request.data, APP_SECRET):
        return "Unauthorized", 401
    
    # Process message
    data = request.json
    messages = data["entry"][0]["changes"][0]["value"]["messages"]
    
    # Handle async (don't block response)
    process_message_async(messages)
    
    return {"status": "ok"}, 200
```

### Why Async Matters

Meta expects a 200 response **within 30 seconds**. Your AI processing might take 5-10 seconds. Solution:

1. Accept webhook → return 200 immediately
2. Queue the message processing (Celery/background job)
3. Process in background
4. Send response when ready

---

## FRAPPE APP STRUCTURE

### What You Need to Create

```
tookio_whatsapp/
├── tookio_whatsapp/
│   ├── __init__.py
│   ├── hooks.py (register webhook, routes)
│   ├── methods/
│   │   ├── __init__.py
│   │   ├── whatsapp_webhook.py (main webhook logic)
│   │   ├── message_processor.py (AI/response logic)
│   │   └── gemini_client.py (Gemini API wrapper)
│   ├── doctype/
│   │   ├── whatsapp_integration/
│   │   │   ├── whatsapp_integration.json (DocType definition)
│   │   │   ├── whatsapp_integration.py (DocType class)
│   │   │   └── whatsapp_integration.js (Frontend)
│   │   ├── whatsapp_message/
│   │   │   ├── whatsapp_message.json
│   │   │   ├── whatsapp_message.py
│   │   │   └── whatsapp_message.js
│   │   └── whatsapp_conversation/
│   │       ├── whatsapp_conversation.json
│   │       ├── whatsapp_conversation.py
│   │       └── whatsapp_conversation.js
│   ├── config/
│   │   ├── __init__.py
│   │   └── desktop.py (sidebar menu)
│   ├── public/
│   │   ├── css/
│   │   └── js/
│   └── templates/
│       └── (any HTML templates)
```

---

## CRITICAL DOCTYPES YOU NEED

### 1. WhatsApp Integration (Client Setup)

```python
# DocType Fields:
- name: Integration Name (e.g., "Mary's Phone Cases")
- phone_number_id: Phone Number ID from Meta
- access_token: WhatsApp API token
- verify_token: Your webhook verify token (secret)
- app_secret: WhatsApp app secret (for signature verification)
- business_name: The business name for AI context
- google_sheet_id: Their product sheet ID
- google_sheet_range: e.g., "Products!A1:E100"
- enabled: Boolean toggle
- created_on: Auto
- modified_on: Auto
- owner: User
```

### 2. WhatsApp Message (Log Each Message)

```python
# DocType Fields:
- name: Auto (message_id)
- integration: Link to WhatsApp Integration
- from_phone: Customer phone number
- message_type: "text" / "image" / "document" / "unsupported"
- text_content: The actual message text
- image_id: Meta's image ID (if image)
- timestamp: When customer sent it
- processed: Boolean (did we respond?)
- response_text: What we sent back
- response_sent_at: When response was sent
- created_on: Auto
```

### 3. WhatsApp Conversation (Thread Per Customer)

```python
# DocType Fields:
- name: Integration + Phone combination
- integration: Link to WhatsApp Integration
- customer_phone: The customer's phone number
- customer_name: Their WhatsApp profile name
- message_count: Total messages in thread
- last_message: Last message text
- last_message_at: Timestamp
- conversation_state: "active" / "escalated" / "resolved"
- escalated_to_user: (if human took over)
- created_on: Auto
```

---

## WEBHOOK ENDPOINT SETUP

### Register in hooks.py

```python
# tookio_whatsapp/hooks.py

app_name = "tookio_whatsapp"
app_title = "Tookio WhatsApp"
app_publisher = "Tookio"
app_description = "WhatsApp Business API integration for Frappe"
app_email = "brian@tookio.co.ke"
app_license = "GPL-3.0"
app_version = "0.0.1"

# Fixtures (DocTypes)
fixtures = [
    {
        "doctype": "DocType",
        "filters": [
            ["name", "in", [
                "WhatsApp Integration",
                "WhatsApp Message",
                "WhatsApp Conversation"
            ]]
        ]
    }
]

# Webhooks
webhooks = {
    "after_insert": {
        "WhatsApp Message": "tookio_whatsapp.methods.message_processor.process_message"
    }
}

# API Routes
api_routes = [
    {
        "method": "POST",
        "path": "/api/resource/whatsapp/webhook",
        "controller": "tookio_whatsapp.methods.whatsapp_webhook"
    },
    {
        "method": "GET",
        "path": "/api/resource/whatsapp/webhook",
        "controller": "tookio_whatsapp.methods.whatsapp_webhook"
    }
]
```

### Webhook Handler (whatsapp_webhook.py)

```python
# tookio_whatsapp/methods/whatsapp_webhook.py

import frappe
import hmac
import hashlib
import json
from frappe import request
from frappe.client import get_list

VERIFY_TOKEN = frappe.get_env("WHATSAPP_VERIFY_TOKEN")
APP_SECRET = frappe.get_env("WHATSAPP_APP_SECRET")


@frappe.whitelist(allow_guest=True)
def webhook():
    """
    Main webhook endpoint for WhatsApp messages
    Handles both GET (verification) and POST (messages)
    """
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return handle_message()
    
    return {"error": "Invalid method"}, 405


def verify_webhook():
    """
    Meta's verification handshake
    GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        frappe.logger().info(f"Webhook verified: {challenge}")
        return challenge  # Return challenge as-is
    
    frappe.logger().error(f"Webhook verification failed: token={token}")
    return {"error": "Verification failed"}, 403


def handle_message():
    """
    Process incoming WhatsApp messages
    Verify signature, extract data, create DocType, return 200 immediately
    """
    
    payload = request.data
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Verify signature
    if not verify_signature(signature, payload):
        frappe.logger().error("Signature verification failed")
        return {"error": "Unauthorized"}, 401
    
    try:
        data = json.loads(payload)
        
        # Extract message details from nested JSON
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        messages = value.get("messages", [])
        metadata = value.get("metadata", {})
        contacts = value.get("contacts", [])
        
        if not messages:
            return {"status": "ok"}, 200
        
        message_data = messages[0]
        phone_number_id = metadata.get("phone_number_id")
        from_phone = message_data.get("from")
        message_id = message_data.get("id")
        timestamp = message_data.get("timestamp")
        message_type = message_data.get("type")
        
        # Get contact name
        contact_name = contacts[0].get("profile", {}).get("name") if contacts else "Unknown"
        
        # Find the integration by phone_number_id
        integration = frappe.get_value(
            "WhatsApp Integration",
            filters={"phone_number_id": phone_number_id, "enabled": 1},
            fieldname=["name", "access_token", "business_name"]
        )
        
        if not integration:
            frappe.logger().warning(f"No integration found for phone_number_id: {phone_number_id}")
            return {"status": "ok"}, 200
        
        # Process based on message type
        if message_type == "text":
            text_body = message_data.get("text", {}).get("body", "")
            create_message_record(
                integration=integration[0],
                from_phone=from_phone,
                contact_name=contact_name,
                message_type="text",
                text_content=text_body,
                message_id=message_id,
                timestamp=timestamp
            )
        
        elif message_type == "image":
            image_id = message_data.get("image", {}).get("id")
            caption = message_data.get("image", {}).get("caption", "")
            create_message_record(
                integration=integration[0],
                from_phone=from_phone,
                contact_name=contact_name,
                message_type="image",
                text_content=caption,
                image_id=image_id,
                message_id=message_id,
                timestamp=timestamp
            )
        
        else:
            # Unsupported message type
            create_message_record(
                integration=integration[0],
                from_phone=from_phone,
                contact_name=contact_name,
                message_type="unsupported",
                text_content=f"[{message_type.upper()} MESSAGE]",
                message_id=message_id,
                timestamp=timestamp
            )
        
        # Return 200 immediately - processing happens async
        return {"status": "ok"}, 200
    
    except Exception as e:
        frappe.logger().error(f"Webhook error: {str(e)}")
        frappe.log_error(message=frappe.get_traceback(), title="WhatsApp Webhook Error")
        return {"status": "error"}, 200  # Return 200 even on error (Meta doesn't care about errors)


def verify_signature(signature, payload):
    """
    Verify the X-Hub-Signature-256 header
    Signature format: sha256=<HMAC_SHA256_HEX>
    """
    if not signature or not signature.startswith("sha256="):
        return False
    
    provided_signature = signature.split("=")[1]
    
    expected_signature = hmac.new(
        APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(provided_signature, expected_signature)


def create_message_record(integration, from_phone, contact_name, message_type, 
                         text_content, image_id=None, message_id=None, timestamp=None):
    """
    Create a WhatsApp Message DocType record
    This triggers async processing via after_insert hook
    """
    doc = frappe.get_doc({
        "doctype": "WhatsApp Message",
        "integration": integration,
        "from_phone": from_phone,
        "customer_name": contact_name,
        "message_type": message_type,
        "text_content": text_content,
        "image_id": image_id,
        "message_id": message_id,
        "timestamp": int(timestamp) if timestamp else None,
        "processed": 0
    })
    doc.insert(ignore_permissions=True)
```

---

## MESSAGE PROCESSING (The AI Part)

### message_processor.py

```python
# tookio_whatsapp/methods/message_processor.py

import frappe
import json
import requests
from .gemini_client import GeminiClient
from frappe.client import get_value, get_list
from datetime import datetime, timedelta


def process_message(doc, method=None):
    """
    Async message processor - called after WhatsApp Message is created
    Handles: AI response, image analysis, sheet lookup, response sending
    """
    
    if doc.processed:
        return
    
    try:
        # Get integration details
        integration = frappe.get_doc("WhatsApp Integration", doc.integration)
        
        if not integration.enabled:
            return
        
        # Build context
        context = build_context(integration, doc.from_phone, doc.customer_name)
        
        # Handle image if present
        if doc.message_type == "image":
            response_text = process_image(
                integration,
                doc.image_id,
                doc.text_content,  # caption
                context
            )
        elif doc.message_type == "text":
            response_text = process_text(
                integration,
                doc.text_content,
                context
            )
        else:
            response_text = f"Sorry, I can't process {doc.message_type} messages. Please send text or images."
        
        # Send response via WhatsApp
        send_whatsapp_message(
            integration,
            doc.from_phone,
            response_text
        )
        
        # Update message record
        doc.processed = 1
        doc.response_text = response_text
        doc.response_sent_at = datetime.now()
        doc.db_update()
        
        # Update conversation
        update_conversation(integration, doc.from_phone, doc.customer_name, response_text)
        
        frappe.logger().info(f"Message {doc.name} processed successfully")
    
    except Exception as e:
        frappe.logger().error(f"Error processing message {doc.name}: {str(e)}")
        frappe.log_error(message=frappe.get_traceback(), title=f"WhatsApp Message Processing Error")


def build_context(integration, customer_phone, customer_name):
    """
    Build the context for the AI agent
    Includes: business context, conversation history, product data
    """
    
    # Get recent conversation history
    recent_messages = frappe.get_list(
        "WhatsApp Message",
        filters={
            "integration": integration.name,
            "from_phone": customer_phone
        },
        fields=["text_content", "response_text", "created_on"],
        order_by="created_on desc",
        limit_page_length=5
    )
    
    # Format history for prompt
    conversation_history = "\n".join([
        f"Customer: {msg.get('text_content', '')}\nYou: {msg.get('response_text', '')}"
        for msg in reversed(recent_messages)
    ])
    
    # Get product data from Google Sheet
    products_text = fetch_google_sheet_data(integration.google_sheet_id, integration.google_sheet_range)
    
    context = {
        "business_name": integration.business_name,
        "conversation_history": conversation_history,
        "products": products_text,
        "customer_name": customer_name,
        "customer_phone": customer_phone
    }
    
    return context


def process_text(integration, message_text, context):
    """
    Process text message with Gemini
    """
    
    gemini = GeminiClient()
    
    system_prompt = f"""You are a customer service assistant for {context['business_name']}.
Your role is to help customers with questions about our products and services.

Business Name: {context['business_name']}
Customer Name: {context['customer_name']}

Our Products:
{context['products']}

Recent Conversation:
{context['conversation_history']}

Guidelines:
1. Be friendly and helpful
2. Use the customer's name when appropriate
3. Reference our products from the inventory
4. If you don't know something, say so and offer to escalate
5. Keep responses concise (under 200 characters for WhatsApp)
6. Use Swahili if customer uses Swahili, English if customer uses English
7. For orders, collect: product name, quantity, delivery address, phone number
"""
    
    response = gemini.generate_text(
        prompt=message_text,
        system_prompt=system_prompt,
        max_tokens=150
    )
    
    return response


def process_image(integration, image_id, caption, context):
    """
    Process image with Gemini Vision API
    """
    
    # Download image from Meta
    image_url = get_image_url(integration.access_token, image_id)
    
    gemini = GeminiClient()
    
    # Analyze image
    image_analysis = gemini.analyze_image(
        image_url=image_url,
        prompt=f"What product is this? Customer said: {caption}"
    )
    
    # Now use the analysis as context for response
    system_prompt = f"""You are a customer service assistant for {context['business_name']}.

The customer sent an image. Here's what the image shows:
{image_analysis}

Our Products:
{context['products']}

Help the customer by identifying if we have similar products and provide recommendations.
Keep response under 200 characters.
"""
    
    response = gemini.generate_text(
        prompt=f"Customer image: {image_analysis}. They said: {caption}",
        system_prompt=system_prompt,
        max_tokens=150
    )
    
    return response


def send_whatsapp_message(integration, recipient_phone, message_text):
    """
    Send message back to customer via WhatsApp API
    """
    
    url = f"https://graph.instagram.com/v18.0/{integration.phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }
    
    headers = {
        "Authorization": f"Bearer {integration.access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        frappe.logger().info(f"Message sent to {recipient_phone}: {message_text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        frappe.logger().error(f"Failed to send WhatsApp message: {str(e)}")
        raise


def get_image_url(access_token, image_id):
    """
    Get download URL for image from Meta
    """
    url = f"https://graph.instagram.com/v18.0/{image_id}"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json().get("url")


def fetch_google_sheet_data(sheet_id, sheet_range):
    """
    Fetch product list from Google Sheets
    Format: Product Name | Price | Stock | Description
    """
    
    try:
        # This would use Google Sheets API
        # For now, placeholder
        # In practice, you'd use google-auth and google-api-client libraries
        
        # Fetch from integration's stored sheet
        # Return formatted string like:
        # "1. iPhone 15 Case - KES 1,500 (In stock)\n2. Screen Protector - KES 800 (In stock)"
        
        pass
    except Exception as e:
        frappe.logger().error(f"Error fetching sheet: {str(e)}")
        return "Product list unavailable"


def update_conversation(integration, customer_phone, customer_name, last_message):
    """
    Update or create WhatsApp Conversation record
    """
    
    conversation_name = f"{integration}-{customer_phone}"
    
    try:
        conversation = frappe.get_doc("WhatsApp Conversation", conversation_name)
        conversation.last_message = last_message
        conversation.last_message_at = datetime.now()
        conversation.message_count += 1
        conversation.save(ignore_permissions=True)
    except frappe.DoesNotExistError:
        conversation = frappe.get_doc({
            "doctype": "WhatsApp Conversation",
            "name": conversation_name,
            "integration": integration,
            "customer_phone": customer_phone,
            "customer_name": customer_name,
            "last_message": last_message,
            "last_message_at": datetime.now(),
            "message_count": 1,
            "conversation_state": "active"
        })
        conversation.insert(ignore_permissions=True)
```

---

## GEMINI CLIENT WRAPPER

### gemini_client.py

```python
# tookio_whatsapp/methods/gemini_client.py

import requests
import frappe
import base64
from io import BytesIO


class GeminiClient:
    """
    Wrapper for Google Gemini API
    Handles text generation and vision analysis
    """
    
    def __init__(self):
        self.api_key = frappe.get_env("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.text_model = "gemini-2.0-flash"
        self.vision_model = "gemini-2.0-flash"
    
    def generate_text(self, prompt, system_prompt=None, max_tokens=150):
        """
        Generate text response using Gemini
        """
        
        url = f"{self.base_url}/{self.text_model}:generateContent?key={self.api_key}"
        
        # Build message with system prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract text from response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return text.strip()
            
            return "I couldn't generate a response. Please try again."
        
        except requests.exceptions.RequestException as e:
            frappe.logger().error(f"Gemini API error: {str(e)}")
            return "I'm having trouble processing your request. Please try again."
    
    def analyze_image(self, image_url, prompt):
        """
        Analyze image using Gemini Vision API
        """
        
        url = f"{self.base_url}/{self.vision_model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": prompt
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": self._fetch_image_as_base64(image_url)
                        }
                    }
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 200
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    return text.strip()
            
            return "Could not analyze image"
        
        except requests.exceptions.RequestException as e:
            frappe.logger().error(f"Gemini Vision API error: {str(e)}")
            return "Could not analyze image"
    
    @staticmethod
    def _fetch_image_as_base64(image_url):
        """
        Fetch image from URL and convert to base64
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            frappe.logger().error(f"Error fetching image: {str(e)}")
            return None
```

---

## ENVIRONMENT VARIABLES

### Required .env Setup

```bash
# .env or in your Frappe instance

# WhatsApp Configuration
WHATSAPP_VERIFY_TOKEN=your-random-verify-token-here
WHATSAPP_APP_SECRET=your-app-secret-from-meta
WHATSAPP_ACCESS_TOKEN=your-access-token-from-meta
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

# Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key

# Google Sheets (optional, if using direct API)
GOOGLE_SHEETS_API_KEY=your-google-sheets-api-key
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json
```

---

## TESTING THE WEBHOOKS LOCALLY

### 1. Using ngrok (For Development)

```bash
# Terminal 1: Start ngrok to expose local Frappe
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io

# Use this URL in Meta Dashboard:
# Webhook URL: https://abc123.ngrok.io/api/resource/whatsapp/webhook
# Verify Token: your-verify-token
```

### 2. Using curl to Test

```bash
# Test GET (verification)
curl -X GET "http://localhost:8000/api/resource/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test_challenge"

# Expected response: test_challenge

# Test POST (message)
curl -X POST http://localhost:8000/api/resource/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=your_signature" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "254712345678",
            "id": "wamid.test",
            "timestamp": "1234567890",
            "type": "text",
            "text": {
              "body": "Hello!"
            }
          }],
          "metadata": {
            "phone_number_id": "123456789"
          },
          "contacts": [{
            "profile": {
              "name": "Test User"
            }
          }]
        }
      }]
    }]
  }'
```

### 3. Generate Correct Signature

```python
import hmac
import hashlib
import json

APP_SECRET = "your-app-secret"
payload = json.dumps({...}).encode()

signature = "sha256=" + hmac.new(
    APP_SECRET.encode(),
    payload,
    hashlib.sha256
).hexdigest()

print(signature)  # Use in X-Hub-Signature-256 header
```

---

## DEPLOYMENT CHECKLIST

- [ ] Create all three DocTypes (WhatsApp Integration, Message, Conversation)
- [ ] Register webhook routes in hooks.py
- [ ] Set up environment variables on your VM
- [ ] Test GET endpoint (verification) with Meta
- [ ] Test POST endpoint (message) with curl
- [ ] Set webhook URL in Meta Dashboard
- [ ] Test with real WhatsApp message
- [ ] Check logs in Frappe for any errors
- [ ] Test image handling
- [ ] Test Gemini API integration
- [ ] Create first WhatsApp Integration for Mary
- [ ] Send test message from her WhatsApp

---

## COMMON ISSUES & SOLUTIONS

### Issue 1: Webhook Verification Fails

**Symptom:** Meta says "Webhook couldn't be verified"

**Solutions:**
1. Check `VERIFY_TOKEN` matches what you set in Meta Dashboard
2. Return the `challenge` value exactly as received
3. Make sure endpoint is HTTPS (ngrok handles this)
4. Check Frappe logs for errors

### Issue 2: Signature Verification Fails

**Symptom:** POST requests return 401

**Solutions:**
1. Verify `APP_SECRET` is correct
2. Check you're using request.data (raw bytes), not request.json
3. Compare signature with `hmac.compare_digest()` (timing-safe comparison)

### Issue 3: Messages Not Being Processed

**Symptom:** Webhook returns 200 but no message is created

**Solutions:**
1. Check if integration exists for that phone_number_id
2. Check if integration is enabled
3. Look in Frappe error logs
4. Verify message JSON structure is correct

### Issue 4: Images Not Loading

**Symptom:** Image analysis returns empty

**Solutions:**
1. Verify access token is still valid
2. Check image_id is correct
3. Try downloading image in separate request
4. Verify Gemini API has vision enabled

### Issue 5: Gemini API Errors

**Symptom:** AI responses not generating

**Solutions:**
1. Verify API key is correct
2. Check API key has access to Gemini models
3. Verify model name is correct (`gemini-2.0-flash`)
4. Check request format matches API spec

---

## PERFORMANCE CONSIDERATIONS

### Rate Limiting

- Meta allows ~1000 messages per second per business account
- Gemini has free tier limits (15 requests/min, paid is higher)
- Google Sheets: 500 read requests per 100 seconds
- **For 100 clients doing 100 msgs/day each:** Comfortably within limits

### Async Processing

- Always return 200 within 30 seconds
- Use Frappe's background jobs (Celery) for heavy processing
- Don't block webhook response on Gemini API calls

### Caching

- Cache Google Sheet data for 5-10 minutes
- Cache conversation history in memory (per session)
- Cache embeddings if using vector search

---

## NEXT STEPS

1. **Create the DocTypes** in Frappe
2. **Copy webhook code** into tookio_whatsapp/methods/
3. **Set environment variables** on your VM
4. **Test webhook verification** with Meta
5. **Test message receipt** with curl
6. **Connect to Gemini** and test
7. **Create integration** for Mary
8. **Send real message** and debug

---

## REFERENCE LINKS

- Meta WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api/
- Gemini API: https://ai.google.dev/
- Frappe Webhooks: https://frappeframework.com/docs/user/en/setup/automation/webhooks
- Frappe Custom App: https://frappeframework.com/docs/user/en/guide/app-development/

---

**Document Version:** 1.0  
**Last Updated:** May 2026  
**Author:** Claude (AI)  
**Status:** Ready for Implementation
