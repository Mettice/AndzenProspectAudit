# Architecture Overview

## Current Status: Using `api/main.py` ✅

**Active File**: `api/main.py` (with authentication, database, all routes)
**Old File**: `api/main_new.py` (legacy, only audit routes - should be removed)

Both `Procfile` and `railway.json` reference `api.main:app`, confirming `main.py` is active.

---

## 📁 Project Structure

```
AndzenProspectsAudit/
├── api/                          # Backend (FastAPI)
│   ├── main.py                   # ✅ ACTIVE - Main FastAPI app
│   ├── main_new.py               # ❌ OLD - Should be removed
│   ├── database.py               # Database configuration (SQLite/PostgreSQL)
│   ├── models/                   # Database models
│   │   ├── user.py               # User model (auth)
│   │   ├── report.py             # Report model
│   │   └── schemas.py            # Pydantic schemas
│   ├── routes/                   # API routes
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── audit.py              # Audit generation endpoints
│   │   ├── reports.py            # Report management endpoints
│   │   └── admin.py              # Admin endpoints
│   ├── services/                 # Business logic
│   │   ├── auth.py               # Authentication service
│   │   ├── klaviyo/              # Klaviyo API integration
│   │   │   ├── orchestrator.py   # Data extraction orchestrator
│   │   │   ├── extraction/        # Data extractors
│   │   │   ├── formatters/       # Data formatters
│   │   │   └── ...
│   │   ├── llm/                  # LLM service (Claude/OpenAI/Gemini)
│   │   │   ├── __init__.py       # LLM service
│   │   │   └── prompts/          # Prompt templates
│   │   └── report/               # Report generation
│   │       ├── __init__.py       # Report service
│   │       ├── preparers/        # Data preparers for sections
│   │       └── pdf_generator.py  # PDF generation
│   └── data/
│       └── reports/              # Generated reports (HTML/PDF/Word)
│
├── frontend/                     # Frontend (Static HTML/CSS/JS)
│   ├── index.html                # Main UI page
│   └── style.css                 # Styles
│
├── templates/                    # Jinja2 templates for reports
│   ├── base.html                 # Base template
│   ├── sections/                 # Section templates
│   └── assets/                   # Report assets
│
├── scripts/                      # Utility scripts
│   └── create_admin.py           # Create admin user
│
├── Procfile                      # Railway/Heroku deployment
├── railway.json                  # Railway configuration
└── vercel.json                   # Vercel configuration
```

---

## 🔄 Backend Architecture

### FastAPI Application (`api/main.py`)
- **Entry Point**: `api.main:app`
- **Server**: Uvicorn ASGI server
- **Database**: SQLAlchemy ORM (SQLite dev / PostgreSQL prod)

### API Routes Structure
```
/api/auth/*          - Authentication (login, register, me)
/api/reports/*       - Report management (list, get, delete, download)
/api/admin/*         - Admin operations (user management)
/api/audit/*         - Audit generation endpoints
/ui                  - Frontend serving (development)
```

### Services Layer
1. **Klaviyo Service**: Extracts data from Klaviyo API
2. **LLM Service**: Generates insights using Claude/OpenAI/Gemini
3. **Report Service**: Generates HTML/PDF/Word reports
4. **Auth Service**: Handles authentication & authorization

---

## 🎨 Frontend Architecture

### Structure
- **Single Page Application**: `frontend/index.html`
- **Static Assets**: CSS, fonts loaded via CDN
- **No Build Step**: Pure HTML/CSS/JavaScript
- **API Communication**: Fetch API to backend

### Frontend Flow
```
User Input → Form Submit → Fetch API → Backend Processing → Display Results
```

### Current Implementation
- Form-based UI for audit inputs
- Inline report preview (iframe)
- Download buttons (HTML/PDF/Word)
- Status indicators
- Log display

---

## 🔌 Backend ↔ Frontend Communication

### Current Setup
1. **Development**: Frontend served by FastAPI at `/ui`
2. **Production**: 
   - Frontend: Vercel (static hosting)
   - Backend: Railway (API server)
   - Communication: CORS-enabled API calls

### API Endpoints Used by Frontend
```javascript
POST /api/audit/generate-morrison  // Generate audit report
```

### Frontend API Configuration
```javascript
// In frontend/index.html
const API_BASE_URL = 
  window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://your-app.railway.app';
```

---

## 🗄️ Database Schema

### Users Table
- Authentication & authorization
- Roles: admin, user, viewer

### Reports Table
- Audit report metadata
- File paths (HTML/PDF/Word)
- Links to creator user

---

## 🚀 Deployment Architecture

### Development
```
Frontend: http://localhost:8000/ui (served by FastAPI)
Backend:  http://localhost:8000/api/* (FastAPI)
Database: SQLite (./data/audit.db)
```

### Production
```
Frontend: Vercel (https://your-app.vercel.app)
Backend:  Railway (https://your-app.railway.app)
Database: Supabase PostgreSQL
```

---

## ⚠️ Issues Found

1. **Duplicate Main Files**: 
   - `api/main.py` ✅ (ACTIVE - has auth, database, all routes)
   - `api/main_new.py` ❌ (OLD - only audit routes, no auth)

2. **Recommendation**: Delete `api/main_new.py` to avoid confusion

---

## 📝 Next Steps

1. ✅ Remove `api/main_new.py` (legacy file)
2. ✅ Verify all routes are in `api/main.py`
3. ✅ Ensure frontend API URL is configurable
4. ✅ Test end-to-end flow

