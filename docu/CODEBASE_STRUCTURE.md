# Codebase Structure Analysis

## ✅ Active Main File

**`api/main.py`** is the ACTIVE file (confirmed by `Procfile` and `railway.json`)
- ✅ Has authentication routes
- ✅ Has database initialization
- ✅ Has all routes (auth, reports, admin, audit)
- ✅ Has CORS configuration for production

**`api/main_new.py`** - ❌ DELETED (was old version with only audit routes)

---

## 🏗️ Backend Structure

### Entry Point
- **File**: `api/main.py`
- **App Variable**: `app = FastAPI(...)`
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### Route Organization
```
api/routes/
├── auth.py       → /api/auth/* (login, register, me)
├── audit.py      → /api/audit/* (generate-morrison)
├── reports.py    → /api/reports/* (list, get, delete, download)
└── admin.py      → /api/admin/* (user management)
```

### Service Layer
```
api/services/
├── auth.py              → Authentication & authorization
├── klaviyo/             → Klaviyo API integration
│   ├── orchestrator.py  → Main data extraction orchestrator
│   ├── extraction/      → Data extractors (campaign, flow, etc.)
│   ├── formatters/     → Data formatters
│   └── ...
├── llm/                 → LLM service (Claude/OpenAI/Gemini)
│   ├── __init__.py      → LLM service implementation
│   └── prompts/         → Prompt templates
└── report/              → Report generation
    ├── __init__.py      → Report service
    ├── preparers/       → Section data preparers
    └── pdf_generator.py → PDF generation
```

### Database Models
```
api/models/
├── user.py      → User model (authentication)
├── report.py    → Report model (metadata)
└── schemas.py   → Pydantic request/response schemas
```

---

## 🎨 Frontend Structure

### Single Page Application
- **File**: `frontend/index.html`
- **Style**: `frontend/style.css`
- **Type**: Pure HTML/CSS/JavaScript (no build step)

### Frontend Architecture
```
frontend/
├── index.html   → Main UI (form + results display)
└── style.css    → Styling
```

### Frontend Features
- ✅ Form-based input (Klaviyo API key, client info, LLM config)
- ✅ Dynamic API URL detection (localhost vs production)
- ✅ Inline report preview (iframe)
- ✅ Download buttons (HTML/PDF/Word)
- ✅ Status indicators
- ✅ Log display

### API Communication
```javascript
// Frontend → Backend
POST ${API_BASE_URL}/api/audit/generate-morrison
```

**API URL Detection:**
- Local: `http://localhost:8000`
- Production: `window.API_URL` or `https://your-app.railway.app`

---

## 🔄 Request Flow

### Audit Generation Flow
```
1. User fills form (frontend/index.html)
   ↓
2. Form submit → fetch(`${API_BASE_URL}/api/audit/generate-morrison`)
   ↓
3. Backend: api/routes/audit.py → generate_morrison_audit()
   ↓
4. Backend: api/services/klaviyo/orchestrator.py → Extract data
   ↓
5. Backend: api/services/llm/__init__.py → Generate insights
   ↓
6. Backend: api/services/report/__init__.py → Generate report
   ↓
7. Backend: Save to database (api/models/report.py)
   ↓
8. Response: HTML content + file URLs
   ↓
9. Frontend: Display in iframe + download buttons
```

---

## 📁 File Serving

### Development (FastAPI serves frontend)
```
GET /ui          → frontend/index.html
GET /ui/style.css → frontend/style.css
GET /api/*       → API endpoints
```

### Production (Vercel + Railway)
```
Frontend (Vercel):
  - Serves static files (index.html, style.css)
  - Makes API calls to Railway backend

Backend (Railway):
  - Only serves API endpoints (/api/*)
  - Does NOT serve frontend files
```

---

## 🗄️ Database

### Configuration
- **File**: `api/database.py`
- **Dev**: SQLite (`sqlite:///./data/audit.db`)
- **Prod**: PostgreSQL/Supabase (`postgresql://...`)

### Models
- **Users**: Authentication & roles
- **Reports**: Audit report metadata

---

## 🚀 Deployment Files

### Railway (Backend)
- `Procfile`: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- `railway.json`: Deployment configuration

### Vercel (Frontend)
- `vercel.json`: Routing configuration

---

## ✅ Summary

1. **Main File**: `api/main.py` ✅ (ACTIVE)
2. **Old File**: `api/main_new.py` ❌ (DELETED)
3. **Frontend**: Single-page app in `frontend/`
4. **Backend**: FastAPI with modular routes/services
5. **Database**: SQLAlchemy (SQLite/PostgreSQL)
6. **Deployment**: Railway (backend) + Vercel (frontend)

---

## 🔍 Key Findings

### ✅ What's Working
- Clear separation: Frontend (static) ↔ Backend (API)
- Modular backend structure
- Database integration ready
- Authentication system in place
- Report management endpoints

### ⚠️ Notes
- Frontend is currently a single HTML file (could be enhanced with a framework later)
- Backend serves frontend in development (`/ui` routes)
- Production uses separate hosting (Vercel + Railway)
- API URL needs to be updated in `frontend/index.html` line 167 for production

