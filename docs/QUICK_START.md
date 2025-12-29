# Quick Start: Supabase + Railway + Vercel

## 🚀 Quick Deployment Steps

### 1. Supabase Setup (5 minutes)
1. Create project at [supabase.com](https://supabase.com)
2. Go to **Settings** → **Database** → Copy connection string
3. Format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

### 2. Railway Backend (10 minutes)
1. Go to [railway.app](https://railway.app) → **New Project**
2. Connect GitHub repo or upload code
3. Add environment variables:
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   SECRET_KEY=<generate-with-openssl-rand-hex-32>
   CORS_ORIGINS=https://your-app.vercel.app
   ```
4. Railway auto-deploys! Get your URL: `https://your-app.railway.app`

### 3. Vercel Frontend (5 minutes)
1. Go to [vercel.com](https://vercel.com) → **Import Project**
2. Connect GitHub repo
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Other
4. Add environment variable:
   ```env
   API_URL=https://your-app.railway.app
   ```
5. Update `frontend/index.html` line ~155: Replace `'https://your-app.railway.app'` with your Railway URL

### 4. Create Admin User
```bash
# Set DATABASE_URL
export DATABASE_URL="your-supabase-connection-string"

# Run script
python scripts/create_admin.py
```

## ✅ Done!
- Backend: `https://your-app.railway.app`
- Frontend: `https://your-app.vercel.app`
- Database: Supabase (managed)

## 🔧 Update Frontend API URL
In `frontend/index.html`, find line ~155 and update:
```javascript
return window.API_URL || 'https://your-actual-railway-url.railway.app';
```

Or set `API_URL` environment variable in Vercel dashboard.

