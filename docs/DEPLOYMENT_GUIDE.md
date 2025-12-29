# Deployment Guide: Railway + Supabase + Vercel

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Vercel    │─────▶│    Railway    │─────▶│   Supabase  │
│  (Frontend) │      │   (Backend)   │      │ (PostgreSQL)│
└─────────────┘      └──────────────┘      └─────────────┘
```

## 🗄️ Step 1: Setup Supabase Database

### 1.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and API keys

### 1.2 Get Database Connection String
1. Go to **Project Settings** → **Database**
2. Find **Connection String** → **URI**
3. Copy the connection string (format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`)

### 1.3 Run Database Migrations
The database will auto-create tables on first startup, but you can also run migrations manually:

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"

# Run the initialization script
python -c "from api.database import init_db; init_db()"
```

### 1.4 Create First Admin User
```bash
# Set DATABASE_URL first
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"

# Run admin creation script
python scripts/create_admin.py
```

## 🚂 Step 2: Deploy Backend to Railway

### 2.1 Prepare for Railway

Create `railway.json` (optional, for Railway-specific config):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2.2 Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo** (or upload code)

### 2.3 Configure Environment Variables
In Railway dashboard, add these environment variables:

```env
# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres

# Security
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-hex-32

# Optional: LLM API Keys (if not using user-provided keys)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# CORS (for Vercel frontend)
CORS_ORIGINS=https://your-app.vercel.app
```

**Generate SECRET_KEY:**
```bash
# On Linux/Mac
openssl rand -hex 32

# On Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 2.4 Deploy
1. Railway will auto-detect Python
2. It will run `pip install -r requirements.txt`
3. Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
4. Railway provides a URL (e.g., `https://your-app.railway.app`)

### 2.5 Verify Deployment
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"healthy"}
```

## 🌐 Step 3: Deploy Frontend to Vercel

### 3.1 Prepare Frontend for Vercel

Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/ui/(.*)",
      "dest": "/frontend/$1"
    },
    {
      "src": "/ui",
      "dest": "/frontend/index.html"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/index.html"
    }
  ],
  "env": {
    "VITE_API_URL": "https://your-app.railway.app"
  }
}
```

### 3.2 Update Frontend API URL

Update `frontend/index.html` to use environment variable or Railway URL:

```javascript
// Add at the top of the script section
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000' 
  : 'https://your-app.railway.app';
```

Then update fetch calls:
```javascript
const res = await fetch(`${API_BASE_URL}/api/audit/generate-morrison`, {
  // ...
});
```

### 3.3 Deploy to Vercel

**Option A: Via Vercel CLI**
```bash
npm i -g vercel
vercel login
vercel --prod
```

**Option B: Via GitHub Integration**
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend` (or leave blank)
   - **Build Command**: (leave blank for static)
   - **Output Directory**: `frontend`
4. Add environment variable:
   - `VITE_API_URL`: `https://your-app.railway.app`

### 3.4 Configure CORS in Backend

Update `api/main.py` to allow Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-app.vercel.app",  # Add your Vercel URL
        os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔧 Step 4: Environment Variables Summary

### Railway (Backend)
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SECRET_KEY=your-generated-secret-key
CORS_ORIGINS=https://your-app.vercel.app
ANTHROPIC_API_KEY=optional
OPENAI_API_KEY=optional
GOOGLE_API_KEY=optional
```

### Vercel (Frontend)
```env
VITE_API_URL=https://your-app.railway.app
```

### Supabase
- Connection string from Supabase dashboard
- No additional env vars needed (connection string contains credentials)

## 📝 Step 5: Post-Deployment Checklist

### Backend (Railway)
- [ ] Database connection working
- [ ] Health endpoint responding
- [ ] CORS configured for Vercel domain
- [ ] Admin user created
- [ ] API endpoints accessible

### Frontend (Vercel)
- [ ] API URL configured correctly
- [ ] Login page working
- [ ] Can generate reports
- [ ] Can view reports list
- [ ] File downloads working

### Database (Supabase)
- [ ] Tables created (users, reports)
- [ ] Admin user exists
- [ ] Can query reports
- [ ] Connection pooling configured (Supabase handles this)

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Test connection locally first
export DATABASE_URL="your-supabase-connection-string"
python -c "from api.database import SessionLocal; db = SessionLocal(); print('Connected!')"
```

### CORS Errors
- Check `CORS_ORIGINS` in Railway includes Vercel URL
- Verify frontend is using correct API URL
- Check browser console for specific CORS error

### Railway Deployment Fails
- Check build logs in Railway dashboard
- Ensure `requirements.txt` is up to date
- Verify Python version (Railway auto-detects, but can specify in `runtime.txt`)

### Vercel Deployment Issues
- Check if `vercel.json` is correct
- Verify file paths in routes
- Check build logs in Vercel dashboard

## 🔐 Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
3. **Enable Supabase Row Level Security** (optional, for extra security)
4. **Use HTTPS only** - Both Railway and Vercel provide this
5. **Rotate secrets regularly** - Especially SECRET_KEY

## 📊 Monitoring

### Railway
- View logs in Railway dashboard
- Set up alerts for errors
- Monitor resource usage

### Vercel
- View analytics in Vercel dashboard
- Check function logs
- Monitor bandwidth usage

### Supabase
- View database logs in Supabase dashboard
- Monitor connection pool usage
- Set up database backups

## 🚀 Alternative: Railway for Both Frontend and Backend

If you prefer to keep everything on Railway:

1. **Backend**: Deploy as Python service (current setup)
2. **Frontend**: Deploy as static site service
   - Build command: `npm run build` (if using build step)
   - Output directory: `frontend` or `dist`
   - Serve static files from Railway

This simplifies deployment but Vercel is optimized for frontend.

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

