# ✅ Deployment Progress

## ✅ Completed
- [x] Backend deployed to Railway
- [x] Railway URL: `https://web-production-2ce0.up.railway.app`
- [x] Health check passed: `{"status":"healthy"}`

## 🚀 Next Steps: Deploy Frontend to Vercel

### Step 1: Deploy to Vercel (5 minutes)

1. **Go to Vercel**: https://vercel.com
2. **Click "Add New Project"**
3. **Import GitHub Repository**: `Mettice/AndzenProspectAudit`
4. **Configure Project**:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend` ⚠️ **IMPORTANT!**
   - **Build Command**: `node scripts/inject-api-url.js` (auto-filled)
   - **Output Directory**: `frontend` (or leave blank)

5. **Add Environment Variable**:
   - Click "Environment Variables"
   - Add:
     ```
     Name: API_URL
     Value: https://web-production-2ce0.up.railway.app
     ```

6. **Click "Deploy"**
7. **Copy your Vercel URL** (e.g., `https://your-app.vercel.app`)

### Step 2: Update CORS in Railway

After you get your Vercel URL:

1. Go back to **Railway Dashboard**
2. Select your service → **Variables** tab
3. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   ```
   (Replace with your actual Vercel URL)

4. Railway will automatically redeploy with the new CORS setting

### Step 3: Create Admin User

After both are deployed, create your first admin user:

**Option A: Using Railway CLI** (if installed)
```bash
railway run python scripts/create_admin.py
```

**Option B: Run Locally** (with Railway's DATABASE_URL)
```powershell
# Set DATABASE_URL from Railway dashboard
$env:DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"

# Run admin creation
python scripts/create_admin.py
```

### Step 4: Test Everything

1. Visit your Vercel URL
2. Login with admin credentials
3. Test generating an audit report
4. Verify file downloads work

---

## 🔧 Current Configuration

### Railway (Backend)
- **URL**: `https://web-production-2ce0.up.railway.app`
- **Status**: ✅ Healthy
- **Environment Variables Needed**:
  - `DATABASE_URL` (from Supabase)
  - `SECRET_KEY` (generate random 32-char string)
  - `CORS_ORIGINS` (update after Vercel deployment)

### Vercel (Frontend) - To Deploy
- **Repository**: `Mettice/AndzenProspectAudit`
- **Root Directory**: `frontend`
- **Environment Variable Needed**:
  - `API_URL`: `https://web-production-2ce0.up.railway.app`

---

## 🐛 Troubleshooting

**If Vercel deployment fails:**
- Check that Root Directory is set to `frontend`
- Verify build command: `node scripts/inject-api-url.js`
- Check Vercel logs for errors

**If CORS errors after Vercel deployment:**
- Make sure `CORS_ORIGINS` in Railway includes your Vercel URL
- Wait for Railway to redeploy after updating CORS

**If frontend can't reach backend:**
- Verify `API_URL` env var in Vercel matches Railway URL
- Check browser console for errors

---

## 📝 Quick Reference

**Railway Backend URL**: `https://web-production-2ce0.up.railway.app`

**Test Backend**:
```powershell
curl https://web-production-2ce0.up.railway.app/health
```

**Vercel Environment Variable**:
```
API_URL=https://web-production-2ce0.up.railway.app
```

