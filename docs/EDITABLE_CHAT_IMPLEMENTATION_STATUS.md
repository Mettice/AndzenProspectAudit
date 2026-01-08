# Editable Report + Chat Interface - Implementation Status

## ✅ What's Been Built

### **Backend (Complete)**

1. **Database Models** ✅
   - `ChatMessage` model (`api/models/chat.py`)
   - `ReportEdit` model (`api/models/chat.py`)
   - Updated `Report` model to store:
     - `html_content` (for editing)
     - `llm_config` (for chat)

2. **Chat API Endpoints** ✅ (`api/routes/chat.py`)
   - `POST /api/audit/{report_id}/chat` - Chat with AI about report
   - `POST /api/audit/{report_id}/edit` - Edit a section
   - `GET /api/audit/{report_id}/chat/history` - Get chat history
   - `GET /api/audit/{report_id}/edits/history` - Get edit history

3. **Report Storage** ✅
   - Updated `api/routes/audit.py` to save `html_content` to database
   - LLM config stored for chat functionality

4. **Router Registration** ✅
   - Chat router registered in `api/main.py`

---

## 🚧 What's Next (Frontend)

### **Step 1: Replace iframe with Editable Report Display**

**Current:** Report displays in `<iframe srcdoc="...">`

**New:** Replace with contentEditable div

```html
<div class="report-editor-container">
  <div class="editor-toolbar">
    <button id="edit-mode-toggle">Edit Mode</button>
    <button id="save-btn">Save Changes</button>
    <button id="download-btn">Download</button>
  </div>
  
  <div class="report-content" id="report-content" contenteditable="true">
    <!-- Report HTML here -->
  </div>
</div>
```

**Location:** `frontend/index.html` (around line 1119)

---

### **Step 2: Add Chat Interface Panel**

Add a split-view layout:

```html
<div class="report-chat-layout">
  <!-- Left: Report Editor -->
  <div class="report-editor-panel">
    <!-- Editable report content -->
  </div>
  
  <!-- Right: Chat Interface -->
  <div class="chat-panel">
    <div class="chat-header">
      <h3>💬 Chat with AI</h3>
      <button id="clear-chat">Clear</button>
    </div>
    
    <div class="chat-messages" id="chat-messages">
      <!-- Messages appear here -->
    </div>
    
    <div class="chat-input-container">
      <input 
        type="text" 
        id="chat-input" 
        placeholder="Ask about the report... (e.g., 'Why is KAV low?')"
      />
      <button id="send-chat-btn">Send</button>
    </div>
  </div>
</div>
```

**Location:** `frontend/index.html` (replace report preview section)

---

### **Step 3: JavaScript Functions**

Add to `frontend/index.html` `<script>` section:

```javascript
// Chat functionality
let currentReportId = null;
let chatHistory = [];

async function sendChatMessage(message, sectionId = null) {
  if (!currentReportId) return;
  
  // Add user message to UI
  addChatMessage('user', message);
  
  // Send to API
  const response = await fetch(`${API_BASE_URL}/api/audit/${currentReportId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify({
      message: message,
      section_id: sectionId,
      report_id: currentReportId
    })
  });
  
  const data = await response.json();
  
  // Add AI response to UI
  addChatMessage('assistant', data.response, data.suggested_edits);
  
  // If AI suggested edits, show preview buttons
  if (data.suggested_edits && data.suggested_edits.length > 0) {
    showSuggestedEdits(data.suggested_edits);
  }
}

function addChatMessage(role, message, suggestedEdits = null) {
  const chatMessages = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message chat-message-${role}`;
  
  let content = `<div class="message-content">${message}</div>`;
  
  if (suggestedEdits) {
    content += '<div class="suggested-edits">';
    suggestedEdits.forEach(edit => {
      content += `
        <div class="suggested-edit">
          <p><strong>Suggested edit to ${edit.section_id}:</strong></p>
          <div class="edit-preview">${edit.new_content.substring(0, 200)}...</div>
          <button onclick="applyEdit('${edit.section_id}', ${JSON.stringify(edit.new_content).replace(/"/g, '&quot;')})">Apply</button>
        </div>
      `;
    });
    content += '</div>';
  }
  
  messageDiv.innerHTML = content;
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function applyEdit(sectionId, newContent) {
  if (!currentReportId) return;
  
  const response = await fetch(`${API_BASE_URL}/api/audit/${currentReportId}/edit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify({
      report_id: currentReportId,
      section_id: sectionId,
      new_content: newContent,
      edit_source: 'chat'
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Reload report content
    loadReportContent(currentReportId);
    addChatMessage('assistant', `✅ Changes applied to ${sectionId}!`);
  }
}

async function loadReportContent(reportId) {
  // Get report HTML from status endpoint
  const response = await fetch(`${API_BASE_URL}/api/audit/status/${reportId}`, {
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  });
  
  const data = await response.json();
  
  if (data.html_content) {
    const reportContent = document.getElementById('report-content');
    reportContent.innerHTML = data.html_content;
  }
}

// Update the report completion handler
// In the existing pollStatus function, when status === 'completed':
if (statusJson.status === 'completed') {
  currentReportId = reportId;  // Store for chat
  
  // ... existing code ...
  
  // Replace iframe with editable div
  resultBox.innerHTML = `
    <div class="success-box">
      <p class="label">Report Generated Successfully</p>
      <p class="value">${reportFilename}</p>
      ${downloadButtons}
    </div>
    <div class="report-chat-layout">
      <div class="report-editor-panel">
        <div class="editor-toolbar">
          <button id="edit-mode-toggle" onclick="toggleEditMode()">Edit Mode</button>
          <button id="save-btn" onclick="saveReport()">Save Changes</button>
        </div>
        <div class="report-content" id="report-content" contenteditable="false">
          ${htmlContent}
        </div>
      </div>
      <div class="chat-panel">
        <div class="chat-header">
          <h3>💬 Chat with AI</h3>
          <button onclick="clearChat()">Clear</button>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input-container">
          <input type="text" id="chat-input" placeholder="Ask about the report..." />
          <button id="send-chat-btn" onclick="sendChatMessage(document.getElementById('chat-input').value)">Send</button>
        </div>
      </div>
    </div>
  `;
  
  // Load chat history
  loadChatHistory(reportId);
}
```

---

### **Step 4: Add CSS Styling**

Add to `frontend/style.css`:

```css
/* Report + Chat Layout */
.report-chat-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
  height: 80vh;
}

.report-editor-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--brand-bg);
  border-bottom: 1px solid var(--brand-border);
}

.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: white;
}

.report-content[contenteditable="true"] {
  outline: 2px solid var(--brand-green);
  outline-offset: -2px;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--brand-border);
  border-radius: 8px;
  background: white;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--brand-border);
  background: var(--brand-bg);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-message {
  padding: 0.75rem;
  border-radius: 8px;
  max-width: 85%;
}

.chat-message-user {
  background: var(--brand-green);
  color: white;
  align-self: flex-end;
}

.chat-message-assistant {
  background: #f0f0f0;
  align-self: flex-start;
}

.chat-input-container {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--brand-border);
}

.chat-input-container input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--brand-border);
  border-radius: 4px;
}

.suggested-edits {
  margin-top: 1rem;
  padding: 1rem;
  background: #fff3cd;
  border-radius: 4px;
}

.suggested-edit {
  margin-bottom: 1rem;
}

.edit-preview {
  background: white;
  padding: 0.5rem;
  border-radius: 4px;
  margin: 0.5rem 0;
  font-size: 0.9rem;
}
```

---

## 🎯 User Workflow (After Implementation)

1. **Fill Form → Generate Audit** (10-15 min)
   - Current form-based system ✅

2. **Report Displays in Editable UI**
   - Left: Editable report content
   - Right: Chat interface

3. **User Can:**
   - **Edit directly:** Click sections, edit text
   - **Chat with AI:** "Why is KAV low?" → Get explanation
   - **Request edits:** "Make executive summary shorter" → AI suggests edit → Apply
   - **Ask questions:** "What's the biggest opportunity?" → Get answer
   - **Generate quotes:** "Create quote for top 3 priorities" → Get quote

4. **Save & Download**
   - Save changes to database
   - Download final version (HTML/PDF/Word)

---

## 📊 Implementation Checklist

- [x] Database models (ChatMessage, ReportEdit)
- [x] Report model updated (html_content, llm_config)
- [x] Chat API endpoints
- [x] Edit API endpoints
- [x] Router registration
- [ ] Frontend: Replace iframe with editable div
- [ ] Frontend: Add chat panel UI
- [ ] Frontend: JavaScript chat functions
- [ ] Frontend: JavaScript edit functions
- [ ] Frontend: CSS styling
- [ ] Testing: Chat functionality
- [ ] Testing: Edit functionality
- [ ] Testing: Save/load edited reports

---

## 🚀 Next Steps

1. **Update frontend/index.html** to replace iframe with editable report + chat
2. **Add CSS** for the new layout
3. **Add JavaScript** for chat and edit functionality
4. **Test** the complete flow

This will give you the **best of both worlds**: fast automated generation + interactive editing and exploration!


