# Quick Setup Checklist for Your WhatsApp + Gemini + n8n Integration

## BEFORE YOU START: Prerequisites

- [ ] n8n running on your Frappe VM (running version 1.x or higher)
- [ ] Gemini API key (from Google Cloud Console - FREE tier available)
- [ ] WhatsApp Business Account set up in Meta Dashboard
- [ ] Phone Number ID from your Meta WhatsApp Business Account
- [ ] Access Token from your WhatsApp Business Account
- [ ] Google Sheet with product data (or ready to create one)
- [ ] One test client (Mary) with test WhatsApp number

---

## CREDENTIALS YOU NEED IN N8N

### 1. Gemini API Credential
```
Name: Gemini API
Type: HTTP
Base URL: https://generativelanguage.googleapis.com/v1beta
API Key: [Your Gemini API key from Google Cloud]
```

### 2. WhatsApp API Credential
```
Name: WhatsApp API
Type: WhatsApp Business Cloud
Access Token: [From Meta Dashboard → Settings → Access Tokens]
Phone Number ID: [From Meta Dashboard → Phone Numbers]
Business Account ID: [From Meta Dashboard → WhatsApp Business Accounts]
```

### 3. Google Sheets Credential (if using Sheets)
```
Name: Google Sheets
Type: OAuth2
Authenticate with: Your Google Account
Required scope: https://www.googleapis.com/auth/spreadsheets
```

---

## COST COMPARISON: This Template vs Your Needs

### Current Template (OpenAI GPT-4o)
```
Per message:
- Input tokens (~500 avg):    500 × $0.003/1k    = $0.0015
- Output tokens (~200 avg):   200 × $0.006/1k    = $0.0012
- Vector embeddings:          ~$0.00005
                Total per msg = $0.0027 (≈KES 0.35)

For 100 msgs/day × 30 days = 3,000 msgs/month
Cost = 3,000 × $0.0027 = $8.10 per month per client
```

### Your Version (Gemini Flash)
```
Per message:
- Input tokens (~500 avg):    500 × $0.0375/1k   = $0.0000188 ✓
- Output tokens (~200 avg):   200 × $0.15/1k     = $0.00003
- Image (if needed):          ~$0.00013 per image
                Total per msg = $0.000068 (≈KES 0.009)

For 100 msgs/day × 30 days = 3,000 msgs/month
Cost = 3,000 × $0.000068 = $0.20 per month per client ✓ (40x cheaper)
```

---

## THE PROBLEM VISUALIZATION

### This Template's Data Flow
```
┌─────────────────────────────────────┐
│     1 Business (Yamaha)             │
│     1 PDF Document (Static)         │
│     1 Vector Store (In-Memory)      │
│     1 WhatsApp Number               │
└─────────────────────────────────────┘
           ↓
        [Workflow]
           ↓
      ✓ Works for 1 business
      ✗ Catalog lost on restart
      ✗ Can't handle 10 clients
      ✗ Data not persistent
```

### Your Business's Data Flow
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Mary's Shop │  │ John's Salon │  │ Lucy's Shoes │
│  Google Sheet│  │  Google Sheet│  │ Google Sheet │
│ Phone: 254X │  │ Phone: 254Y  │  │ Phone: 254Z  │
└──────────────┘  └──────────────┘  └──────────────┘
      ↓                ↓                   ↓
      └────────────────┴───────────────────┘
              ↓
      [ONE n8n Workflow]
              ↓
    Dynamic client lookup
    Dynamic product data
    Dynamic business context
              ↓
    ✓ Scales to 100+ clients
    ✓ Data persistent (Sheets)
    ✓ Each client independent
    ✓ Cost predictable per client
```

---

## QUICK MODIFICATION GUIDE

If you want to **quickly adapt the template**:

### Step 1: Replace These Nodes

**Remove:**
- "get Product Brochure" (HTTP → PDF)
- "Extract from File"
- "Default Data Loader"
- "Recursive Character Text Splitter"
- "Embeddings OpenAI"
- "Embeddings OpenAI1"
- "Create Product Catalogue"
- "Product Catalogue" (Vector Store)

**Replace with:**
- ONE "Google Sheets" node that fetches the product list

### Step 2: Simplify Product Lookup

Instead of vector search, do direct lookup:
```
Customer: "Do you have iPhone cases?"
↓
Google Sheets search: Contains "iPhone"
↓
Return matching rows: [iPhone 15 case, iPhone 14 case, ...]
↓
Pass to AI: "Here are our products: [list]. Customer asked about..."
↓
AI responds naturally
```

### Step 3: Replace OpenAI with Gemini

In the "AI Sales Agent" node:
```
OLD: "OpenAI Chat Model" (GPT-4o)
NEW: Gemini node (use HTTP request to Gemini API)

OR: Use n8n's native Gemini node if available
```

### Step 4: Add Multi-Client Routing

After WhatsApp Trigger:
```
1. Extract phone_number_id from message
2. Lookup client in Frappe DocType: "WhatsApp Integration"
3. Get their Google Sheet ID
4. Get their business context
5. Route to rest of workflow
```

---

## ESTIMATED TIMELINE

### Quick Path (Adapt Template)
```
1. Replace OpenAI → Gemini:           30 min
2. Remove vector store logic:         30 min
3. Add Google Sheets lookup:          45 min
4. Configure for Mary:                30 min
5. Test end-to-end:                   30 min
                            Total: ~2.5 hours
```

### Proper Path (Build for Scale)
```
1. Create Frappe DocType:             1 hour
2. Build client lookup flow:          2 hours
3. Google Sheets integration:         1 hour
4. Gemini API setup:                  1 hour
5. Message logging:                   1 hour
6. Testing + error handling:          2 hours
                            Total: ~8 hours
```

---

## RED FLAGS IN THE TEMPLATE (Watch Out For)

1. **Hardcoded Phone Number ID**
   ```json
   "phoneNumberId": "477115632141067"
   ```
   This won't work for your clients. Make it dynamic.

2. **In-Memory Vector Store Clears on Restart**
   ```
   Every n8n restart = lose all product data
   Use Google Sheets instead
   ```

3. **No Multi-Tenancy**
   ```
   Can't distinguish between different clients
   Need to add phone_number_id → client mapping
   ```

4. **No Image Handling**
   ```
   Explicitly rejects: "I'm unable to process non-text messages"
   Your clients need image recognition
   Add Gemini Vision for this
   ```

5. **No Persistence**
   ```
   Conversation history only in memory
   If n8n restarts, lose all context
   Store in Frappe instead
   ```

---

## DECISION TIME

### Choose One:

**Path A: "I want it working in 2-3 hours"**
- Adapt this template
- Hardcode for Mary
- Get proof of concept
- Then scale later

**Path B: "I want to build it right the first time"**
- Ignore this template
- Build from scratch
- Proper multi-tenant architecture
- Takes longer but scales cleanly

---

## YOUR SETUP STATUS

**You have:**
- ✅ Meta App created (tookio-app-1)
- ✅ WhatsApp Business Account approved
- ✅ Test message sent successfully
- ✅ n8n running on your VM
- ✅ Frappe + Google Workspace

**You still need:**
- [ ] Gemini API key
- [ ] n8n credentials configured
- [ ] Test client (Mary) ready with product list
- [ ] Google Sheet with product data
- [ ] Frappe DocType for storing integrations

---

## NEXT IMMEDIATE ACTION

1. **Get your credentials ready** (WhatsApp access token + Gemini API key)
2. **Ask Mary:** "What's your product list?" (get it in a Google Sheet)
3. **Test message:** Confirm WhatsApp messages work in n8n
4. **Pick a path:** Quick hack (2h) or proper build (8h)?

Once you have these, I can walk you through the exact node-by-node setup.

What's your call?
