# Tookio WhatsApp Frappe App - Master Context Index

**Your complete guide to building the webhook system. Start here.**

---

## WHAT YOU'RE BUILDING

A Frappe app (`tookio_whatsapp`) that integrates WhatsApp Business Cloud API with Gemini AI to create an automated customer service bot for Kenyan online sellers (Mary, her friends, etc.).

**Key fact:** Messages within the 24-hour customer service window are FREE on WhatsApp. You're building the automation to handle them at scale.

---

## YOUR DOCUMENTS (5 FILES)

### 1. **tookio_whatsapp_complete_context.md** ⭐ START HERE
- **Length:** 33 KB (comprehensive)
- **Purpose:** Complete technical reference for building the webhook
- **Contains:**
  - Full architecture explanation
  - All Python code (webhook, processor, Gemini client)
  - All three Frappe DocTypes (definition + fields)
  - Environment setup
  - Testing instructions
  - Common issues & solutions
  - Deployment checklist

**When to use:** When you need exact code to copy or need deep understanding of how something works.

**How to use:** Load this into VS Code, reference sections as you code.

---

### 2. **tookio_whatsapp_quick_reference.md** 🚀 QUICK LOOKUP
- **Length:** 6.5 KB (cheat sheet)
- **Purpose:** One-page reference while coding
- **Contains:**
  - Webhook flow diagram
  - Copy-paste code snippets (signature verification, send message, Gemini call)
  - File structure
  - Testing commands
  - DocType field checklist
  - Common errors & fixes
  - Key concepts summary

**When to use:** When you need a quick code snippet or can't remember how to do something.

**How to use:** Print this out or keep it in a VS Code tab.

---

### 3. **how_to_use_claude_in_vscode.md** 🤖 VS CODE GUIDE
- **Length:** 12 KB (practical guidance)
- **Purpose:** How to effectively use Claude AI in VS Code for development
- **Contains:**
  - Installation & setup of Claude in VS Code
  - 5 prompt patterns (Create, Explain, Debug, Test, Implement)
  - Step-by-step workflow for building (1-5)
  - Testing strategies with Claude
  - Best practices
  - VS Code extensions recommendations
  - Prompt templates (copy-paste)
  - Workflow checklist
  - Common mistakes to avoid

**When to use:** Before you start coding, and whenever you get stuck.

**How to use:** Follow the workflow 1-5. Use the prompt templates. Ask Claude using the patterns.

---

### 4. **n8n_whatsapp_template_analysis.md** 📊 (OPTIONAL - For Reference)
- **Length:** 8.8 KB
- **Purpose:** Analysis of the n8n WhatsApp template you found
- **Contains:**
  - What the template does (good parts)
  - Critical issues (problems for your use case)
  - What works vs what doesn't
  - Cost comparison (OpenAI vs Gemini)
  - Why this template won't scale
  - Recommended approaches

**When to use:** If you're curious about the template or want to understand why we're not using it.

**When NOT to use:** For building your Frappe app (this is about n8n, which is separate).

---

### 5. **n8n_whatsapp_setup_checklist.md** 📋 (OPTIONAL - For n8n Later)
- **Length:** 7.5 KB
- **Purpose:** Setup guide for n8n integration (if you want to use it later)
- **Contains:**
  - Prerequisites checklist
  - n8n credentials setup
  - Cost comparison
  - Field checklists for n8n
  - Modification guide for the template
  - Timeline estimates (quick path vs proper path)

**When to use:** AFTER you've built the Frappe webhook (later phase).

**When NOT to use:** Right now - focus on the Frappe webhook first.

---

## RECOMMENDED READING ORDER

### **If you want to start coding NOW (Go Fast):**

1. Read: `tookio_whatsapp_quick_reference.md` (5 min)
2. Open: `tookio_whatsapp_complete_context.md` in VS Code
3. Install: Claude in VS Code (follow guide #3)
4. Use: Prompt templates from guide #3
5. Follow: Workflow steps 1-5 from guide #3
6. Reference: `quick_reference.md` for copy-paste code
7. Debug: Using the debugging section of guide #3

---

### **If you want deep understanding first (Go Right):**

1. Read: `tookio_whatsapp_complete_context.md` (30 min)
   - Understand the architecture
   - Read all the code
   - Understand the DocTypes
2. Read: `tookio_whatsapp_quick_reference.md` (5 min)
   - Get the cliff notes version
3. Read: `how_to_use_claude_in_vscode.md` (10 min)
   - Understand how to use AI for coding
4. Then start coding with step-by-step workflow

---

## QUICK START (30 MINUTE OVERVIEW)

If you have limited time right now, here's the essence:

### What Gets Built

```
Customer sends WhatsApp message
       ↓
Meta sends to your webhook (on your Frappe server)
       ↓
Webhook verifies it's really from Meta (signature check)
       ↓
Webhook creates a WhatsApp Message record in Frappe
       ↓
Frappe triggers message_processor (async background job)
       ↓
Processor calls Gemini AI with:
  - Customer's message
  - Business context
  - Product list (from their Google Sheet)
  - Conversation history
       ↓
Gemini returns response
       ↓
Response gets sent back to customer via WhatsApp API
       ↓
Everything logged in Frappe
```

### 5 Files You Create

1. **whatsapp_webhook.py** - Receives messages from Meta
2. **message_processor.py** - AI logic & response generation
3. **gemini_client.py** - Wrapper for Gemini API
4. **hooks.py** - Register routes & setup
5. **DocTypes** (3 of them) - Store data in Frappe

### Key Credentials You Need

```
WHATSAPP_VERIFY_TOKEN = Random string you create
WHATSAPP_APP_SECRET = From Meta Dashboard
WHATSAPP_ACCESS_TOKEN = From Meta Dashboard  
WHATSAPP_PHONE_NUMBER_ID = From Meta Dashboard
GEMINI_API_KEY = From Google Cloud
```

### Cost Per Client Per Month

- WhatsApp: ~KES 500
- API calls (Gemini + messages): ~KES 100
- Infrastructure: KES 0 (your VM)
- **Total: ~KES 600 cost, sell for KES 5,000-10,000**

---

## WHICH DOCUMENT FOR WHICH QUESTION

| Your Question | Go To |
|---|---|
| "How does the webhook work?" | Complete Context (Architecture section) |
| "What's the code for signature verification?" | Quick Reference (Code Snippets) |
| "How do I test this?" | Complete Context (Testing section) or Quick Reference (Testing Commands) |
| "I'm stuck, how do I ask Claude for help?" | How to Use Claude (Debugging section) |
| "What are the exact DocType fields?" | Quick Reference (DOCTYPE Field Checklist) |
| "How should I structure my project?" | Complete Context (App Structure section) |
| "I need a code snippet, fast" | Quick Reference (Snippets) |
| "I want to understand the AI part" | Complete Context (Message Processing section) |
| "Should I use that n8n template?" | n8n Template Analysis |
| "My webhook is broken, help!" | How to Use Claude (Emergency Debugging) |
| "I need to set up n8n" | n8n Setup Checklist |

---

## YOUR DEVELOPMENT TIMELINE

### Phase 1: Setup (1 day)
- [ ] Create Frappe app structure
- [ ] Create the three DocTypes
- [ ] Set environment variables
- [ ] Copy code from context

### Phase 2: Webhooks (2 days)
- [ ] Build webhook handler (GET + POST)
- [ ] Test verification with Meta
- [ ] Test message receipt
- [ ] Debug any signature issues

### Phase 3: AI Integration (2 days)
- [ ] Build Gemini client
- [ ] Build message processor
- [ ] Connect to Google Sheets
- [ ] Test end-to-end with real messages

### Phase 4: Polish (1 day)
- [ ] Error handling refinements
- [ ] Logging improvements
- [ ] Performance optimization
- [ ] Documentation

**Total: ~1 week from zero to production**

---

## CRITICAL SUCCESS FACTORS

### You Must Have:
- ✅ Gemini API key (get it free from ai.google.dev)
- ✅ WhatsApp Business Account set up in Meta
- ✅ Your Meta App verified and approved
- ✅ Phone Number ID from your WhatsApp account
- ✅ Access Token from Meta
- ✅ App Secret from Meta
- ✅ Frappe running on your VM
- ✅ n8n running on your VM (for async processing, optional but good)

### You Must Understand:
- ✅ How webhooks work (request → process → response)
- ✅ Signature verification (HMAC-SHA256)
- ✅ Async processing (return 200 immediately, process later)
- ✅ Multi-tenancy (one webhook, multiple clients)
- ✅ The 24-hour free window (critical for cost)

### You Must Remember:
- ✅ Always return 200 from webhook within 30 seconds
- ✅ Always verify the signature (security)
- ✅ Always log errors (for debugging)
- ✅ Always handle None/missing values gracefully
- ✅ Always test with curl before using real client

---

## USING WITH CLAUDE IN VS CODE

### Load the Context

1. Create `.claude/` folder in your project
2. Copy `tookio_whatsapp_complete_context.md` into it
3. In VS Code: Ctrl+Shift+P → "Claude: Load Context"
4. Select the context file

### Build Step-by-Step

Use the 5-step workflow from `how_to_use_claude_in_vscode.md`:
1. Create DocTypes (5 min)
2. Create webhook handler (15 min)
3. Create message processor (20 min)
4. Create Gemini client (15 min)
5. Wire it in hooks.py (10 min)

### Test After Each Step

Don't wait until the end. Test:
- After step 1: DocTypes exist in Frappe ✓
- After step 2: Webhook verification works ✓
- After step 2: Message receipt works ✓
- After step 3: Messages are processed ✓
- After step 4: Gemini calls work ✓
- After step 5: End-to-end flow works ✓

---

## COMMON GOTCHAS

### 🚨 Gotcha 1: Signature Verification Fails
- **Why:** Using `==` instead of `hmac.compare_digest()`
- **Fix:** Use timing-safe comparison (in context code)

### 🚨 Gotcha 2: Webhook Blocks on Gemini Call
- **Why:** Processing message in webhook handler (returns after Gemini responds)
- **Fix:** Create WhatsApp Message → return 200 → process async

### 🚨 Gotcha 3: Conversation History Lost on Restart
- **Why:** Storing in-memory only
- **Fix:** Frappe persists everything to DB automatically

### 🚨 Gotcha 4: Can't Handle Multiple Clients
- **Why:** Hardcoded phone_number_id
- **Fix:** Look up integration by phone_number_id (in context code)

### 🚨 Gotcha 5: Gemini API Key Not Working
- **Why:** Using wrong model name or API format
- **Fix:** Use exact code from context

---

## SUPPORT RESOURCES

### If You Get Stuck:

1. **Check:** Quick Reference for copy-paste code
2. **Search:** Context file for the section (Ctrl+F)
3. **Ask:** Claude in VS Code using prompt templates
4. **Debug:** Share error message with Claude (Emergency Debugging section)

### If Claude Can't Help:

1. Check Frappe logs: `bench log -f`
2. Check n8n logs (if using n8n)
3. Check your .env variables are set
4. Check Meta Dashboard for API status

---

## YOUR NEXT STEP

**RIGHT NOW:**

1. Open `tookio_whatsapp_quick_reference.md` - spend 5 minutes
2. Open `how_to_use_claude_in_vscode.md` - spend 10 minutes
3. Install Claude in VS Code
4. Load `tookio_whatsapp_complete_context.md` as context
5. Follow workflow step 1: "Create the DocTypes"
6. Use the prompt template from `how_to_use_claude_in_vscode.md`

**You'll have your first DocType in 10 minutes.**

---

## DOCUMENTS AT A GLANCE

```
tookio_whatsapp_complete_context.md
├─ Full technical reference
├─ All code snippets
├─ DocType definitions
├─ Environment setup
├─ Testing guide
└─ Troubleshooting

tookio_whatsapp_quick_reference.md
├─ Copy-paste code snippets
├─ Testing commands
├─ DocType field lists
├─ Error solutions
└─ Key concepts (fits on one page)

how_to_use_claude_in_vscode.md
├─ Setup Claude in VS Code
├─ 5 prompt patterns
├─ Step-by-step workflow (1-5)
├─ Best practices
├─ Debugging strategies
└─ Prompt templates

n8n_whatsapp_template_analysis.md (optional, reference only)
├─ Analysis of template you found
├─ Why it won't work for you
└─ Better approaches

n8n_whatsapp_setup_checklist.md (optional, use later)
├─ For n8n setup
├─ Use after Frappe webhook is done
└─ Not needed for MVP
```

---

## FINAL CHECKLIST BEFORE YOU START

- [ ] All 5 documents downloaded
- [ ] Claude in VS Code installed
- [ ] Gemini API key obtained
- [ ] Meta app verified
- [ ] Phone Number ID from Meta
- [ ] Access token from Meta
- [ ] App secret from Meta
- [ ] Frappe running on your VM
- [ ] Understand why 24-hour window matters
- [ ] Ready to follow the 5-step workflow

---

**Version:** 1.0 | **Status:** Ready for Development | **Updated:** May 2026

**Start with:** `tookio_whatsapp_quick_reference.md` (5 min read)  
**Then read:** `how_to_use_claude_in_vscode.md` (10 min read)  
**Then code:** Follow the 5-step workflow

Good luck! You've got this. 🚀
