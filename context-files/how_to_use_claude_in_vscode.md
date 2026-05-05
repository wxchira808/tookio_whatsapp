# Using Claude in VS Code for Tookio WhatsApp Webhook Development

**How to make the most of AI-assisted coding in VS Code**

---

## SETUP: Claude in VS Code

### 1. Install Claude for VS Code Extension

In VS Code:
1. Open Extensions (Ctrl+Shift+X)
2. Search: "Claude"
3. Install "GitHub Copilot" OR "Claude for VS Code" (if available)
4. Sign in with your Claude account

### 2. Open Your Project

```bash
# On your local machine
cd your-local-path/tookio_whatsapp
code .
```

### 3. Load the Context Files

In VS Code:
1. Create a folder: `.claude` (hidden folder for context)
2. Copy all `.md` files there:
   - `tookio_whatsapp_complete_context.md`
   - `tookio_whatsapp_quick_reference.md`

3. Open VS Code Command Palette (Ctrl+Shift+P)
4. Type: "Claude: Load Context"
5. Select the complete context file

---

## HOW TO USE CLAUDE EFFECTIVELY

### Prompt Pattern 1: "Create This File"

```
@Claude I need to create the file whatsapp_webhook.py in methods/
Here's the structure needed: [paste relevant section from context]

Generate the complete file with:
- Proper error handling
- Logging
- Comments explaining each function
- Type hints

File path: tookio_whatsapp/methods/whatsapp_webhook.py
```

**Claude will:**
- Generate the complete file
- Add helpful comments
- Include error handling
- Follow your patterns

### Prompt Pattern 2: "Explain This Part"

```
@Claude I'm confused about signature verification in the context docs.
Can you explain:
1. Why we need HMAC-SHA256?
2. How the comparison works?
3. Why use hmac.compare_digest()?

Use simple language and examples.
```

### Prompt Pattern 3: "Debug This Issue"

```
@Claude The webhook verification is failing.

Here's what I did:
1. Set VERIFY_TOKEN to "abc123"
2. Created the webhook endpoint
3. Tested with curl

Error: "Verification failed"

What's wrong? Check the context docs and suggest fixes.
```

### Prompt Pattern 4: "Write Tests"

```
@Claude Write unit tests for the signature verification function.

Include:
- Test with valid signature
- Test with invalid signature
- Test with missing header
- Test with wrong app secret

Use pytest framework.
File: tookio_whatsapp/tests/test_webhook.py
```

### Prompt Pattern 5: "Implement This Feature"

```
@Claude I need to add image handling to the message processor.

From the context:
- process_image function exists
- It should call Gemini Vision API
- Return product matches

But it's incomplete. Please:
1. Complete the function
2. Handle errors gracefully
3. Add logging
4. Test the JSON format

Reference: [paste relevant section]
```

---

## WORKFLOW: Start to Finish

### Step 1: Create the DocTypes First

**Prompt:**
```
@Claude Based on the context, I need to create WhatsApp Integration DocType.

Generate:
1. The JSON structure (whatsapp_integration.json)
2. The Python class (whatsapp_integration.py)
3. Include all fields from the checklist

Requirements:
- Access token should be Password type (hidden)
- phone_number_id should be Text
- Include creation metadata

Output as two separate code blocks, one for each file.
```

**Claude generates → Copy to VS Code → Test in Frappe**

### Step 2: Create the Webhook Handler

**Prompt:**
```
@Claude I'm ready to implement the webhook handler.

From context, whatsapp_webhook.py needs:
1. GET handler for verification
2. POST handler for messages
3. Signature verification
4. Message extraction

Implement these functions:
- verify_webhook()
- handle_message()
- verify_signature()
- create_message_record()

Use @frappe.whitelist(allow_guest=True) for public access.
Include proper error logging.
```

### Step 3: Create the Message Processor

**Prompt:**
```
@Claude Now I need the async message processor.

Implement message_processor.py with:
1. process_message() - triggered on WhatsApp Message insert
2. build_context() - gather conversation history
3. process_text() - handle text with Gemini
4. process_image() - handle images with Gemini Vision
5. send_whatsapp_message() - send response back

Use the GeminiClient class for API calls.
Include detailed error handling and logging.
```

### Step 4: Create Gemini Client

**Prompt:**
```
@Claude Create the GeminiClient wrapper class.

The class should:
1. Initialize with API key from env
2. generate_text() - call Gemini with system prompt
3. analyze_image() - vision API for images
4. Handle timeouts and errors gracefully
5. Return clean text responses

Use requests library.
Add retry logic for network failures.
```

### Step 5: Wire Everything in hooks.py

**Prompt:**
```
@Claude Update hooks.py to register:
1. The three DocTypes (fixtures)
2. Webhook routes (GET and POST)
3. After-insert hook for message processing

From the context, I need:
- fixtures list
- api_routes list  
- webhooks dict

Make sure the paths are correct:
- GET /api/resource/whatsapp/webhook
- POST /api/resource/whatsapp/webhook
```

---

## TESTING WITH CLAUDE

### Test Generation

**Prompt:**
```
@Claude Generate comprehensive tests for the webhook.

I need:
1. Test verification handshake
2. Test signature validation (valid and invalid)
3. Test message extraction
4. Test different message types (text, image, unsupported)
5. Test error cases (missing fields, wrong signatures)

Use pytest.
File: tookio_whatsapp/tests/test_webhook.py

Also generate test fixtures with sample Meta webhook payloads.
```

### Debugging Help

**When something breaks:**

```
@Claude My webhook verification is failing.

Error in logs: "Verification failed: token=abc123"

My setup:
- VERIFY_TOKEN=abc123 (set in .env)
- Endpoint: http://localhost:8000/api/resource/whatsapp/webhook
- Testing with: curl "http://localhost:8000/api/resource/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=abc123&hub.challenge=test"

Expected: returns "test"
Actual: returns 403

From the context, what could be wrong? Check:
1. How I'm reading the verify token
2. How I'm comparing it
3. How I'm returning the challenge

Here's my code: [paste your code]

What's the bug?
```

---

## BEST PRACTICES FOR CLAUDE IN VS CODE

### 1. Use @context References

```
@Claude Using the @tookio_whatsapp_complete_context.md file you loaded,
the signature verification should use hmac.compare_digest().

In my current code [paste], I'm using == for comparison.
Is this a security issue? What should I change?
```

### 2. Ask for Specific File Outputs

Always specify the file path:
```
@Claude Create the file: tookio_whatsapp/methods/gemini_client.py

Include:
- Class definition
- All methods from context
- Docstrings for each method
- Error handling
```

### 3. Ask Claude to Review Your Code

```
@Claude Review this code for issues:

[paste your webhook handler]

Check against the context for:
1. Correct error handling
2. Proper async handling (return 200 immediately)
3. Correct signature verification
4. Proper logging

What should I fix?
```

### 4. Build Incrementally

Don't ask for everything at once. Build step-by-step:
1. Webhook verification first (just GET)
2. Then POST handler
3. Then message creation
4. Then AI integration

This helps you test as you go.

### 5. Use Context References

When confused, ask Claude to point you to the relevant section:

```
@Claude I need to understand how conversation history is built.

From the complete context, point me to:
1. The relevant section
2. The exact code pattern I should follow
3. An example of how it's used
```

---

## VS CODE TIPS FOR WEBHOOK DEVELOPMENT

### Extension: REST Client

Install "REST Client" extension in VS Code.

Create `test.http`:
```
@api = http://localhost:8000
@token = your-verify-token
@secret = your-app-secret

### Test Verification
GET {{api}}/api/resource/whatsapp/webhook?hub.mode=subscribe&hub.verify_token={{token}}&hub.challenge=test_challenge

### Test Message
POST {{api}}/api/resource/whatsapp/webhook
Content-Type: application/json
X-Hub-Signature-256: sha256=...

{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "254712345678",
          "id": "wamid.test",
          "type": "text",
          "text": {"body": "Hello!"}
        }],
        "metadata": {
          "phone_number_id": "123456789"
        },
        "contacts": [{
          "profile": {"name": "Test"}
        }]
      }
    }]
  }]
}
```

Right-click → "Send Request" to test without curl.

### Extension: Python

Install "Python" and "Pylance" for better code completion and type checking.

### Extension: Bracket Pair Colorizer

Makes nested JSON easier to read.

---

## PROMPT TEMPLATES (Copy & Paste)

### Template 1: File Generation

```
@Claude Generate the file: [PATH]

From the context, this file should:
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

Include:
- Comments explaining each section
- Proper error handling
- Logging statements
- Type hints (if Python)

Output only the code, no explanation.
```

### Template 2: Debugging

```
@Claude Help me debug this issue.

Symptom: [What's happening]
Expected: [What should happen]

My code: [paste relevant section]

From the context, the correct pattern is [reference section].

Where's the bug? Suggest fixes.
```

### Template 3: Code Review

```
@Claude Review this code against the context documentation.

File: [filename]
Code: [paste your code]

Check for:
1. Compliance with the context specification
2. Error handling completeness
3. Logging adequacy
4. Security issues

What needs fixing?
```

### Template 4: Implementation Help

```
@Claude I need to implement [feature name].

From the context, here's what I understand:
1. [Your understanding]
2. [Your understanding]

But I'm stuck on:
1. [Question]
2. [Question]

The relevant context section is [reference].

Help me implement this correctly.
```

---

## WORKFLOW CHECKLIST

- [ ] Load complete context file into VS Code
- [ ] Create .claude folder for easy reference
- [ ] Install Python extension for type checking
- [ ] Install REST Client for webhook testing
- [ ] Set up .env with required variables
- [ ] Create each DocType (ask Claude to generate)
- [ ] Create webhook handler (ask Claude)
- [ ] Create message processor (ask Claude)
- [ ] Create Gemini client (ask Claude)
- [ ] Update hooks.py (ask Claude)
- [ ] Test verification with REST Client
- [ ] Test message receipt with curl
- [ ] Test with real WhatsApp message
- [ ] Debug any errors (ask Claude for help)

---

## COMMON CLAUDE MISTAKES TO AVOID

### ❌ Don't:

1. **Ask for entire app at once** - Too much at once leads to missed details
2. **Not provide context** - Always reference the context docs
3. **Skip testing between steps** - Build and test incrementally
4. **Copy code without understanding** - Read what Claude generates
5. **Ignore error messages** - Share exact errors with Claude

### ✅ Do:

1. **Ask for one file at a time**
2. **Reference the context docs in prompts**
3. **Test after each file creation**
4. **Read through generated code**
5. **Share full error messages for debugging**

---

## EMERGENCY DEBUGGING

If something breaks completely:

**Prompt:**
```
@Claude I need emergency help debugging.

The webhook is completely broken.
Error: [exact error message]

Here's my complete code:
[paste whatsapp_webhook.py]
[paste hooks.py]
[paste .env variables used]

From the context docs, here's what should happen:
[describe the flow]

What's wrong? Walk me through fixing it step-by-step.
```

Claude will:
1. Identify the issue
2. Show you the fix
3. Explain why it was wrong
4. Prevent future issues

---

## FINAL TIPS

1. **Keep the context files open in VS Code** - Ctrl+K to search them
2. **Use comments in your prompts** - "From the context, section X says..."
3. **Test as you go** - Don't wait until the end
4. **Use REST Client** - Much faster than curl for testing
5. **Ask Claude to explain** - If you don't understand generated code
6. **Keep error messages** - Paste them to Claude for help
7. **Build incrementally** - Verification → Messages → AI → Logging

---

**Version:** 1.0 | **Status:** Ready | **Updated:** May 2026
