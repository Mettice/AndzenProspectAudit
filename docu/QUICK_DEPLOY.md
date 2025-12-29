# 🚀 Quick Deployment Checklist

## ✅ Pre-Deployment
- [x] Code pushed to GitHub: https://github.com/Mettice/AndzenProspectAudit
- [ ] Supabase database ready (connection string available)
- [ ] Railway account created
- [ ] Vercel account created

---

## 🚂 Step 1: Deploy Backend to Railway (5-10 minutes)

### 1. Create Railway Project
1. Go to https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Select: `Mettice/AndzenProspectAudit`
3. Railway auto-detects Python

### 2. Add Environment Variables
In Railway → **Variables** tab:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SECRET_KEY=[GENERATE_BELOW]
CORS_ORIGINS=https://your-app.vercel.app
```

**Generate SECRET_KEY (PowerShell):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 3. Deploy
- Railway auto-deploys
- **Copy your Railway URL** (e.g., `https://your-app.railway.app`)

### 4. Create Admin User
```bash
# Set DATABASE_URL from Railway
export DATABASE_URL="postgresql://..."

# Run script
python scripts/create_admin.py
```

### 5. Test
```bash
curl https://your-app.railway.app/health
```

---

## 🌐 Step 2: Deploy Frontend to Vercel (5 minutes)

### 1. Import Repository
1. Go to https://vercel.com → **Add New Project**
2. Import: `Mettice/AndzenProspectAudit`

### 2. Configure Settings
- **Framework Preset**: Other
- **Root Directory**: `frontend` ⚠️ IMPORTANT!
- **Build Command**: (leave blank)
- **Output Directory**: `frontend` (or blank)

### 3. Add Environment Variable
**Environment Variables** tab:
```
API_URL = https://your-app.railway.app
```
(Use your Railway URL from Step 1)

### 4. Deploy
- Click **Deploy**
- **Copy your Vercel URL** (e.g., `https://your-app.vercel.app`)

### 5. Update Railway CORS
Go back to Railway → **Variables**:
```
CORS_ORIGINS=https://your-app.vercel.app
```
Railway auto-redeploys.

---

## ✅ Step 3: Test Everything

1. Visit: `https://your-app.vercel.app`
2. Login with admin credentials
3. Generate an audit report
4. Verify downloads work

---

## 🔧 Environment Variables Summary

### Railway (Backend)
```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
SECRET_KEY=[32_CHAR_RANDOM_STRING]
CORS_ORIGINS=https://your-app.vercel.app
```

### Vercel (Frontend)
```env
API_URL=https://your-app.railway.app
```

---

## 🐛 Common Issues

**CORS Errors?**
- Check `CORS_ORIGINS` in Railway includes Vercel URL
- Verify frontend `API_URL` env var is set

**Database Connection Fails?**
- Verify `DATABASE_URL` format
- Check Supabase connection string

**Frontend Can't Reach Backend?**
- Verify `API_URL` in Vercel matches Railway URL
- Check browser console for errors

---

## 📞 Need Help?

- Railway Logs: Railway dashboard → Service → Logs
- Vercel Logs: Vercel dashboard → Project → Deployments → View Function Logs
- Check both platforms' documentation

