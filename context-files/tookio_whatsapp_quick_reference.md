# Tookio WhatsApp Webhook - Quick Reference Card

**Print this and keep it visible while coding!**

---

## WEBHOOK FLOW AT A GLANCE

```
Meta Servers
     ↓
GET /webhook?hub.verify_token=X&hub.challenge=Y
     ↓ (first time only)
Return Y to verify
     ↓
POST /webhook with message JSON
     ↓
Verify signature (X-Hub-Signature-256)
     ↓
Create WhatsApp Message DocType
     ↓ (async, don't block)
AI processing (Gemini)
     ↓
Send response via WhatsApp API
     ↓
Update conversation tracking
```

---

## CRITICAL CODE SNIPPETS

### Signature Verification (Copy-Paste)
```python
import hmac, hashlib

def verify_signature(signature, payload, app_secret):
    if not signature or not signature.startswith("sha256="):
        return False
    provided = signature.split("=")[1]
    expected = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, expected)
```

### Extract Message from JSON (Copy-Paste)
```python
data = request.json
messages = data["entry"][0]["changes"][0]["value"]["messages"]
metadata = data["entry"][0]["changes"][0]["value"]["metadata"]

message = messages[0]
from_phone = message.get("from")
message_type = message.get("type")  # "text", "image", etc.
phone_number_id = metadata.get("phone_number_id")

if message_type == "text":
    text = message["text"]["body"]
elif message_type == "image":
    image_id = message["image"]["id"]
```

### Send WhatsApp Reply (Copy-Paste)
```python
url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
payload = {
    "messaging_product": "whatsapp",
    "to": from_phone,
    "type": "text",
    "text": {"preview_url": False, "body": response_text}
}
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
requests.post(url, json=payload, headers=headers)
```

### Call Gemini (Copy-Paste)
```python
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"maxOutputTokens": 150}
}
response = requests.post(url, json=payload, timeout=30)
text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
```

---

## FILE STRUCTURE

```
tookio_whatsapp/
├── hooks.py ← Register webhook routes here
├── methods/
│   ├── whatsapp_webhook.py ← GET/POST handler
│   ├── message_processor.py ← AI logic
│   └── gemini_client.py ← Gemini wrapper
└── doctype/
    ├── whatsapp_integration/
    ├── whatsapp_message/
    └── whatsapp_conversation/
```

---

## ENVIRONMENT VARIABLES

```bash
WHATSAPP_VERIFY_TOKEN=abc123xyz
WHATSAPP_APP_SECRET=your-secret-key
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=123456789
GEMINI_API_KEY=your-gemini-key
```

---

## TESTING COMMANDS

### Test Verification
```bash
curl "http://localhost:8000/api/resource/whatsapp/webhook?\
hub.mode=subscribe&\
hub.verify_token=abc123xyz&\
hub.challenge=test_challenge"
```

Should return: `test_challenge`

### Test Message Receipt
```bash
# First generate signature
python3 -c "
import hmac, hashlib, json
payload = json.dumps({...}).encode()
secret = 'your-app-secret'
sig = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(sig)
"

# Then send
curl -X POST http://localhost:8000/api/resource/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=SIGNATURE_HERE" \
  -d '{...message json...}'
```

Should return: `{"status": "ok"}`

---

## DOCTYPE FIELD CHECKLIST

### WhatsApp Integration
- [ ] phone_number_id (Text)
- [ ] access_token (Password)
- [ ] verify_token (Password)
- [ ] app_secret (Password)
- [ ] business_name (Text)
- [ ] google_sheet_id (Text)
- [ ] google_sheet_range (Text, default "Products!A1:E100")
- [ ] enabled (Checkbox)

### WhatsApp Message
- [ ] integration (Link → WhatsApp Integration)
- [ ] from_phone (Text)
- [ ] customer_name (Text)
- [ ] message_type (Select: text, image, document, unsupported)
- [ ] text_content (Long Text)
- [ ] image_id (Text)
- [ ] message_id (Text)
- [ ] timestamp (Int)
- [ ] processed (Checkbox)
- [ ] response_text (Long Text)
- [ ] response_sent_at (Datetime)

### WhatsApp Conversation
- [ ] integration (Link → WhatsApp Integration)
- [ ] customer_phone (Text)
- [ ] customer_name (Text)
- [ ] message_count (Int)
- [ ] last_message (Text)
- [ ] last_message_at (Datetime)
- [ ] conversation_state (Select: active, escalated, resolved)

---

## COMMON ERRORS & FIXES

| Error | Fix |
|-------|-----|
| "Verification failed" | Check VERIFY_TOKEN matches Meta Dashboard |
| "Unauthorized" 401 | Verify signature calculation is correct |
| Message not created | Integration not found for phone_number_id |
| Gemini returns empty | Check API key and model name |
| Image not processing | Verify access_token is valid |
| No response sent | Check `process_message` is being called |

---

## DEBUGGING CHECKLIST

- [ ] Check Frappe error logs: `bench log -f`
- [ ] Check webhook is being called (add log at top of handler)
- [ ] Check signature verification passes
- [ ] Check integration exists for phone_number_id
- [ ] Check integration is enabled
- [ ] Check Gemini API key works
- [ ] Check WhatsApp access token is valid
- [ ] Verify JSON structure matches Meta's spec
- [ ] Check request.data (raw bytes) not request.json for signature

---

## KEY CONCEPTS

**Webhook Verification:** Meta confirms you own the endpoint (one-time)
**Signature:** Proves message came from Meta (every message)
**Async Processing:** Return 200 immediately, process in background
**Multi-tenant:** One webhook handles multiple clients (via phone_number_id lookup)
**24-hour window:** Customer-initiated messages are FREE
**Escalation:** When AI can't help, alert human via Slack/email

---

## USEFUL LINKS

```
Meta API Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/
Gemini API: https://ai.google.dev/
Frappe Webhook: https://frappeframework.com/docs/user/en/setup/automation/webhooks
Message JSON: https://developers.facebook.com/docs/whatsapp/webhooks/payload
```

---

## BEFORE YOU START CODING

1. [ ] Have GEMINI_API_KEY ready
2. [ ] Have WHATSAPP_APP_SECRET and ACCESS_TOKEN
3. [ ] Have WHATSAPP_VERIFY_TOKEN (generate random: `openssl rand -hex 32`)
4. [ ] Have your WHATSAPP_PHONE_NUMBER_ID
5. [ ] Have Mary's test WhatsApp number
6. [ ] Have ngrok or exposed URL
7. [ ] Have created all three DocTypes

---

**Version:** 1.0 | **Status:** Ready | **Updated:** May 2026
