# N8N WhatsApp Chatbot Template - Analysis & Setup for Tookio

## WHAT THIS TEMPLATE DOES (The Good)

This template is a **WhatsApp AI Sales Bot** that:

1. **Receives WhatsApp messages** via the WhatsApp Trigger node
2. **Filters message types** (only accepts text, rejects images/audio)
3. **Loads a product PDF** (Yamaha loudspeakers brochure in this case)
4. **Creates a vector store** (in-memory database of product knowledge)
5. **Routes through an AI Agent** (OpenAI GPT-4o with memory per customer)
6. **Sends responses back** via WhatsApp

The workflow data shows:
```
Message comes in → Type check (text?) → AI Agent processes 
→ AI queries vector store (product catalog) → Response sent back
```

---

## CRITICAL ISSUES WITH THIS TEMPLATE (The Problems)

### **Problem 1: It Uses OpenAI, Not Gemini** ❌

The template uses:
- `OpenAI Chat Model` (GPT-4o) = **expensive**
- `Embeddings OpenAI` = **paid**

**For your use case:** You wanted Gemini (cheapest). This template is 5-10x more expensive.

**Cost comparison per 1,000 customer interactions:**
- OpenAI GPT-4o: ~$3-5
- Gemini 2.0 Flash: ~$0.03-0.05 ✓

**Fix:** Replace all OpenAI nodes with Gemini equivalents (we'll do this)

---

### **Problem 2: It Uses In-Memory Vector Store** ❌

The template uses:
```
Create Product Catalogue → Vector Store In Memory → Product knowledge
```

**Why this sucks for your use case:**
- In-memory means the product catalog **resets every time the workflow runs**
- You have to re-upload the PDF every single time
- **Can't handle multiple clients** (each client's product list is separate)
- Doesn't scale beyond ~100MB of data

**For Mary's phone case shop:** Every restart = lose all products. Bad.

**Fix:** Replace with Google Sheets (which you already use) or Supabase

---

### **Problem 3: It Can't Multi-Tenant** ❌

This template is hardcoded for **one business**:
```
"phoneNumberId": "477115632141067",  ← This is hardcoded
"memoryKey": "whatsapp-75"           ← This is hardcoded
Vector Store: "whatsapp-75"          ← This is hardcoded
```

**For your 10-client business model:** You need to handle multiple phone numbers and separate product catalogs.

This template would require **duplicating the entire workflow 10 times**. Not scalable.

**Fix:** Add dynamic lookup based on incoming `phone_number_id`

---

### **Problem 4: Message History Is Per-Customer But Stored In-Memory** ⚠️

The template uses:
```
"sessionKey": "=whatsapp-75-{{ $json.messages[0].from }}"
```

This keeps conversation history per customer, which is good. BUT:
- It's lost when n8n restarts
- No persistent database

**Fix:** Use Frappe as your persistent storage (you have it!)

---

### **Problem 5: It Doesn't Handle Image Recognition** ❌

The template explicitly rejects non-text messages:
```
Reply To User1: "I'm unable to process non-text messages..."
```

But **your use case needs image handling.** Mary's customers send photos of items!

**Fix:** Add image processing with Gemini Vision API

---

### **Problem 6: No Human Escalation** ❌

The template can't hand off to a human if the AI is unsure. For your business, you need:
- Detect when AI confidence is low
- Alert the business owner
- Let them take over the conversation

**Fix:** Add a switch/condition for escalation

---

## WHAT WORKS IN THIS TEMPLATE ✅

1. **WhatsApp Trigger node** ✅ - Perfect, no changes needed
2. **Switch node for message type filtering** ✅ - Reusable
3. **AI Agent pattern** ✅ - The general architecture is sound
4. **Memory per customer** ✅ - Good approach (just needs persistence)
5. **Reply To User node** ✅ - Works perfectly

---

## YOUR ACTUAL WORKFLOW (What We'll Build)

Here's what we need instead:

```
WhatsApp Message Arrives
    ↓
Extract: phone_number_id, sender_phone, message_text, (if image: image data)
    ↓
Lookup client by phone_number_id
    ├─ Get client's Google Sheet (product list)
    ├─ Get client's context (business name, industry, tone)
    └─ Get conversation history from Frappe
    ↓
IF image:
    └─ Call Gemini Vision API → identify product
    ↓
Build prompt with:
    - Client context
    - Product data from sheet
    - Conversation history
    - User message
    ↓
Call Gemini Flash API (with vision if needed)
    ↓
Check AI confidence:
    ├─ HIGH (>0.8) → Send response directly
    └─ LOW (<0.8) → Escalate + notify owner + send "hold on" message
    ↓
Log interaction to Frappe
    ↓
Send response back to WhatsApp
```

---

## STEP-BY-STEP: FIX THIS TEMPLATE FOR YOUR USE CASE

### **Option A: Minimal Changes (Quick Start)**

Keep 70% of template, change:
1. Replace OpenAI nodes with Gemini
2. Replace in-memory vector store with Google Sheets lookup
3. Add image handling
4. Hardcode for ONE client first (Mary)
5. Test it works

**Timeline:** 2-3 hours
**Scalability:** Works for 1 client, messy for 10

---

### **Option B: Proper Build (What You Should Do)**

Start fresh with your own workflow:
1. Frappe API trigger (webhook)
2. Client lookup logic
3. Google Sheets fetch
4. Gemini API calls (text + vision)
5. Conversation logging to Frappe
6. Multi-client routing

**Timeline:** 8-10 hours (one-time)
**Scalability:** Works for 100+ clients cleanly

---

## BREAKDOWN OF EACH NODE IN THIS TEMPLATE

### **Nodes That Work For You:**

```
1. WhatsApp Trigger
   - Listens for incoming messages ✅
   - Gives you: phone_number_id, sender phone, message type, text body
   - Keep as-is

2. Handle Message Types (Switch Node)
   - Checks if message is text or not
   - Separates the two flows
   - Keep this logic, adapt for Gemini Vision

3. AI Sales Agent
   - This is n8n's LangChain agent node
   - Connects to LLM + memory + tools
   - We'll replace OpenAI with Gemini

4. Window Buffer Memory
   - Keeps last N messages per customer
   - Perfect for context
   - Keep this but add persistence

5. Reply To User (WhatsApp Node)
   - Sends response back ✅
   - Keep as-is
```

### **Nodes That DON'T Work For You:**

```
1. get Product Brochure (HTTP Request)
   - Downloads Yamaha PDF
   - Replace with: Google Sheets fetch

2. Extract from File
   - Pulls text from PDF
   - Replace with: Google Sheets API → product list

3. Default Data Loader
   - Prepares PDF text for embedding
   - Not needed if using Sheets

4. Embeddings OpenAI
   - Creates vector embeddings
   - Replace with: Gemini Embeddings (if using embeddings at all)
   - OR: Skip embeddings entirely, just search Sheets directly

5. Recursive Character Text Splitter
   - Breaks PDF into chunks
   - Not needed with Sheets approach

6. Product Catalogue (Vector Store In Memory)
   - Stores embeddings in RAM
   - Replace with: Direct Sheets lookup + Gemini context

7. Vector Store Tool
   - Queries the vector store
   - Replace with: Sheets lookup function
```

---

## THE REAL ISSUE: This Template Is For a DIFFERENT Use Case

This template is designed for:
- **1 business** (Yamaha)
- **Static catalog** (PDF that doesn't change much)
- **Rich product knowledge** (detailed specs)
- **Sales education** (not transaction-heavy)

Your use case is:
- **Multiple businesses** (Mary, her friends, 10-100 clients)
- **Dynamic catalogs** (Google Sheets they update)
- **Quick lookups** (price, stock, availability)
- **Transaction-heavy** (orders, delivery, payment)

**Conclusion:** This template is 60% useful. 40% needs rebuilding.

---

## RECOMMENDED APPROACH FOR YOU

**Phase 1: Get This Template Working (1 week)**
- Replace OpenAI → Gemini
- Hardcode for Mary's shop
- Replace PDF → Google Sheet
- Verify messages send/receive

**Phase 2: Scale It (1 week)**
- Add multi-client routing
- Add persistent storage (Frappe)
- Add image handling
- Add escalation logic

**Phase 3: Polish (ongoing)**
- Add handoff flows
- Add analytics
- Add template messages
- White-label UI for clients

---

## WHAT YOU NEED RIGHT NOW

1. **n8n credentials:** Gemini API key + WhatsApp API credentials
2. **Google Sheet:** Mary's product list (columns: name, price, stock, image)
3. **Frappe custom doctype:** To store conversations (optional but good)
4. **Meta App access:** You already have this ✓

---

## NEXT STEPS

I can help you with either:

**Option A:** Fix this template for Mary (quick)
```
- Replace OpenAI with Gemini
- Connect to Google Sheet
- Test with Mary
- Time: 2-3 hours
```

**Option B:** Build from scratch (better long-term)
```
- Start with WhatsApp Trigger only
- Build client lookup logic
- Add Gemini calls
- Build persistence
- Time: 8-10 hours but scales to 100 clients
```

Which way do you want to go?

Also, I noticed in your Meta dashboard, you have a phone number ID. What's your current setup:
- Do you have Mary's test number ready?
- Do you have her product list in a Google Sheet already?
- Do you have n8n running on your VM?

Once I know these details, I can give you the exact steps to get running.
