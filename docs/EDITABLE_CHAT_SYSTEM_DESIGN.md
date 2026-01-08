# Editable Report + Chat Interface Design

## 🎯 User Workflow

```
1. Fill Form → Generate Audit (10-15 min)
   ↓
2. Report Displays in Editable UI
   ↓
3. User can:
   - Edit sections directly
   - Chat with AI about the report
   - Ask questions: "Why is KAV low?"
   - Request edits: "Make the executive summary more concise"
   - Generate quotes: "Create a quote for top 3 priorities"
   ↓
4. Save edited report
   ↓
5. Download final version (HTML/PDF/Word)
```

---

## 🏗️ Architecture

### **Frontend Components**

1. **Report Editor View**
   - ContentEditable sections
   - Side-by-side: Report | Chat
   - Save button
   - Undo/Redo

2. **Chat Interface**
   - Message history
   - Input field
   - Can reference specific sections
   - Can request edits

3. **Section Navigation**
   - Jump to sections
   - Edit mode toggle
   - Preview mode

### **Backend Endpoints**

1. **Chat API** (`/api/audit/chat`)
   - Takes: report_id, message, section_context
   - Returns: AI response + suggested edits

2. **Edit API** (`/api/audit/edit`)
   - Takes: report_id, section, new_content
   - Returns: updated report

3. **Save API** (`/api/audit/save`)
   - Takes: report_id, edited_content
   - Returns: saved report URL

---

## 📋 Implementation Plan

### **Phase 1: Editable Report Display**

**Frontend:**
- Replace iframe with contentEditable div
- Add edit mode toggle
- Add section navigation
- Add save button

**Backend:**
- Endpoint to get report HTML
- Endpoint to save edited report

### **Phase 2: Chat Interface**

**Frontend:**
- Add chat panel (right side)
- Message input
- Chat history
- "Edit this section" buttons

**Backend:**
- Chat endpoint with LLM
- Context: full report + chat history
- Can reference sections by ID

### **Phase 3: AI-Powered Edits**

**Backend:**
- Parse chat requests: "Make executive summary shorter"
- Identify target section
- Generate edited content
- Apply changes

---

## 💡 Example User Flow

```
User: "Why is their KAV only 16.5%?"
Bot: "Based on the audit, their KAV is below the 30% benchmark because:
      - Campaigns only contribute 35.6% of attributed revenue
      - They're sending campaigns infrequently (1-2x per month)
      - Missing critical flows like winback and back-in-stock.
      
      Would you like me to update the Executive Summary to emphasize this?"

User: "Yes, and make it more actionable"
Bot: "I've updated the Executive Summary section. The new version:
      - Highlights the campaign frequency issue
      - Adds specific action items
      - Quantifies the revenue opportunity
      
      [Preview of changes] [Apply] [Cancel]"

User: [Clicks Apply]
Bot: "Changes applied! The Executive Summary has been updated."
```

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Edit Mode] [Preview] [Save] [Download]               │
├──────────────────────────┬──────────────────────────────┤
│                          │                               │
│   REPORT CONTENT         │    CHAT INTERFACE            │
│   (Editable)             │                               │
│                          │  💬 Chat with AI              │
│  [Section Navigation]    │  ┌─────────────────────────┐│
│  - Cover                 │  │ Why is KAV low?          ││
│  - Why Andzen?           │  └─────────────────────────┘│
│  - Executive Summary     │  ┌─────────────────────────┐│
│  - KAV Analysis          │  │ Based on the audit...    ││
│  - List Growth           │  └─────────────────────────┘│
│  ...                     │  [Type message...]          │
│                          │  [Send]                     │
│                          │                               │
└──────────────────────────┴──────────────────────────────┘
```

---

## 🔧 Technical Implementation

### **1. Editable Report Display**

```html
<div class="report-editor">
  <div class="editor-toolbar">
    <button id="edit-mode-toggle">Edit Mode</button>
    <button id="save-btn">Save Changes</button>
    <button id="download-btn">Download</button>
  </div>
  
  <div class="report-content" contenteditable="true">
    <!-- Report HTML here -->
  </div>
</div>
```

### **2. Chat Interface**

```html
<div class="chat-panel">
  <div class="chat-header">
    <h3>Chat with AI</h3>
    <button id="clear-chat">Clear</button>
  </div>
  
  <div class="chat-messages" id="chat-messages">
    <!-- Messages appear here -->
  </div>
  
  <div class="chat-input">
    <input type="text" id="chat-input" placeholder="Ask about the report...">
    <button id="send-chat">Send</button>
  </div>
</div>
```

### **3. Backend Chat Endpoint**

```python
@router.post("/api/audit/{report_id}/chat")
async def chat_about_report(
    report_id: int,
    message: str,
    section_context: Optional[str] = None
):
    # Get report data
    report = get_report(report_id)
    
    # Get chat history
    chat_history = get_chat_history(report_id)
    
    # Call LLM with:
    # - Full report content
    # - Chat history
    # - Current message
    # - Section context (if user clicked on a section)
    
    response = await llm_service.chat(
        report_content=report.html_content,
        chat_history=chat_history,
        user_message=message,
        section_context=section_context
    )
    
    # Save chat message
    save_chat_message(report_id, message, response)
    
    return {
        "response": response.text,
        "suggested_edits": response.suggested_edits,  # Optional
        "section_references": response.sections  # Which sections were referenced
    }
```

### **4. Backend Edit Endpoint**

```python
@router.post("/api/audit/{report_id}/edit")
async def edit_report_section(
    report_id: int,
    section_id: str,
    new_content: str,
    edit_source: str = "manual"  # "manual" or "chat"
):
    # Get current report
    report = get_report(report_id)
    
    # Parse HTML and update section
    updated_html = update_section(report.html_content, section_id, new_content)
    
    # Save updated report
    save_report(report_id, updated_html)
    
    return {
        "success": True,
        "updated_section": section_id,
        "preview": get_section_preview(updated_html, section_id)
    }
```

---

## 🚀 Implementation Steps

### **Step 1: Make Report Editable (2-3 hours)**
- Replace iframe with contentEditable div
- Add edit mode toggle
- Add section navigation
- Add save functionality

### **Step 2: Add Chat Interface (3-4 hours)**
- Create chat panel UI
- Add message input
- Connect to chat API
- Display chat history

### **Step 3: Connect Chat to Edits (4-5 hours)**
- Parse chat requests for edit commands
- Generate edited content via LLM
- Show preview before applying
- Apply changes to report

### **Step 4: Section References (2-3 hours)**
- Allow clicking sections to reference in chat
- Highlight referenced sections
- Show "Edit this section" buttons

---

## 💾 Data Model

### **Chat Messages Table**
```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    role TEXT,  -- 'user' or 'assistant'
    message TEXT,
    section_references TEXT[],  -- Array of section IDs
    suggested_edits JSONB,  -- Optional edits suggested by AI
    created_at TIMESTAMP
);
```

### **Report Edits Table**
```sql
CREATE TABLE report_edits (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    section_id TEXT,
    old_content TEXT,
    new_content TEXT,
    edit_source TEXT,  -- 'manual' or 'chat'
    chat_message_id INTEGER REFERENCES chat_messages(id),
    created_at TIMESTAMP
);
```

---

## 🎯 Benefits

1. **Speed:** Form-based generation (10-15 min)
2. **Flexibility:** Edit sections as needed
3. **Interactivity:** Chat to understand findings
4. **Customization:** AI can suggest improvements
5. **Quote Generation:** Chat can generate quotes from audit

---

## 📝 Next Steps

1. **Create editable report viewer** (replace iframe)
2. **Add chat panel** to frontend
3. **Build chat API endpoint** (backend)
4. **Build edit API endpoint** (backend)
5. **Connect chat to edits** (AI-powered editing)

This gives you the best of both worlds: **fast automated generation** + **interactive editing and exploration**!


