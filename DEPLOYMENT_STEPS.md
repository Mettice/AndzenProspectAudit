# 🚀 Quick Deployment Guide

## Prerequisites
- ✅ GitHub repository pushed (already done: https://github.com/Mettice/AndzenProspectAudit)
- ✅ Supabase project created (you mentioned you have one)
- ✅ Railway account
- ✅ Vercel account

---

## Step 1: Deploy Backend to Railway 🚂

### 1.1 Create Railway Project
1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository: `Mettice/AndzenProspectAudit`
5. Railway will auto-detect it's a Python project

### 1.2 Configure Environment Variables
In Railway dashboard, go to your service → **Variables** tab, add:

```env
# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@[YOUR_HOST]:5432/postgres

# Security (generate a random key)
SECRET_KEY=[GENERATE_WITH_COMMAND_BELOW]

# CORS - Add your Vercel URL after deployment
CORS_ORIGINS=https://your-app.vercel.app
```

**Generate SECRET_KEY (Windows PowerShell):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Or use online generator: https://randomkeygen.com/

### 1.3 Deploy
- Railway will automatically:
  - Install Python dependencies from `requirements.txt`
  - Run `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  - Provide you with a URL like: `https://your-app.railway.app`

### 1.4 Create Admin User
After deployment, SSH into Railway or run locally with Railway's DATABASE_URL:

```bash
# Set the DATABASE_URL from Railway
export DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"

# Run admin creation script
python scripts/create_admin.py
```

### 1.5 Test Backend
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"healthy"}
```

**Note your Railway URL** - you'll need it for Vercel!

---

## Step 2: Deploy Frontend to Vercel 🌐

### 2.1 Connect GitHub Repository
1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New Project"**
3. Import your GitHub repository: `Mettice/AndzenProspectAudit`
4. Vercel will auto-detect settings

### 2.2 Configure Project Settings
- **Framework Preset**: Other
- **Root Directory**: `frontend` (IMPORTANT!)
- **Build Command**: (leave blank - static files)
- **Output Directory**: `frontend` (or leave blank)

### 2.3 Add Environment Variable
In Vercel project settings → **Environment Variables**, add:

```
API_URL = https://your-app.railway.app
```
(Replace with your actual Railway URL from Step 1.3)

### 2.4 Deploy
Click **"Deploy"** - Vercel will:
- Deploy your frontend
- Provide you with a URL like: `https://your-app.vercel.app`

### 2.5 Update CORS in Railway
Go back to Railway → **Variables** and update:

```env
CORS_ORIGINS=https://your-app.vercel.app
```

Railway will automatically redeploy with the new CORS setting.

---

## Step 3: Final Configuration ✅

### 3.1 Update Frontend API URL (if needed)
The frontend already has logic to detect production, but verify:
- Vercel environment variable `API_URL` is set to your Railway URL
- Frontend code will use `window.API_URL` in production

### 3.2 Test Full Flow
1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Login with admin credentials
3. Test generating an audit report
4. Verify file downloads work

---

## Environment Variables Summary

### Railway (Backend)
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SECRET_KEY=[GENERATED_SECRET_KEY]
CORS_ORIGINS=https://your-app.vercel.app
```

### Vercel (Frontend)
```env
API_URL=https://your-app.railway.app
```

### Supabase
- Connection string is in `DATABASE_URL` above
- No additional env vars needed

---

## Troubleshooting

### Backend Issues
- **Database connection fails**: Check `DATABASE_URL` format
- **CORS errors**: Verify `CORS_ORIGINS` includes Vercel URL
- **500 errors**: Check Railway logs for Python errors

### Frontend Issues
- **API calls fail**: Verify `API_URL` env var in Vercel
- **404 on routes**: Check `vercel.json` routing
- **CORS errors**: Backend CORS not configured correctly

### Quick Checks
```bash
# Test backend health
curl https://your-app.railway.app/health

# Test backend API
curl https://your-app.railway.app/api/auth/me

# Check Vercel deployment
# Visit: https://your-app.vercel.app
```

---

## Post-Deployment Checklist

- [ ] Railway backend deployed and healthy
- [ ] Vercel frontend deployed
- [ ] Environment variables set in both platforms
- [ ] CORS configured in Railway
- [ ] Admin user created
- [ ] Can login via Vercel frontend
- [ ] Can generate audit reports
- [ ] File downloads work
- [ ] Database connection working

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Check logs in both platforms' dashboards

