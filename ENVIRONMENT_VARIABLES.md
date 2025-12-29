# Environment Variables Guide

## 🚂 Railway (Backend) - Required Variables

### Essential Variables

```env
# Database Connection (from Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres

# JWT Secret Key (for authentication)
SECRET_KEY=your-generated-secret-key-here

# CORS Origins (your Vercel frontend URL)
CORS_ORIGINS=https://your-app.vercel.app
```

### Optional Variables (Fallback LLM API Keys)

These are **optional** because users can provide API keys via the UI. Only set these if you want fallback defaults:

```env
# Optional: LLM API Keys (fallback if user doesn't provide in UI)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

**Note**: Since users provide API keys in the UI, these are only needed as fallbacks.

---

## 🌐 Vercel (Frontend) - Required Variables

### Essential Variables

```env
# Backend API URL (your Railway URL)
API_URL=https://web-production-2ce0.up.railway.app
```

**Note**: The frontend uses `window.API_URL` which is injected during build. This environment variable is used by the build script.

---

## 🗄️ Supabase (Database) - No Environment Variables Needed

Supabase doesn't require separate environment variables. The database connection is handled through the `DATABASE_URL` in Railway.

**To get your Supabase connection string:**
1. Go to: https://supabase.com/dashboard/project/vplzphjygfazhsaqxhbt/settings/database
2. Scroll down to find **Connection string** section
3. You'll see tabs: **URI**, **JDBC**, **Golang**, etc.
4. Click on the **URI** tab
5. Copy the connection string (it will look like: `postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`)
6. Replace `[YOUR-PASSWORD]` with your actual database password

**If direct connection (port 5432) fails with "Network is unreachable":**
- This is often an IPv6 connectivity issue with Railway
- **Solution**: Use Connection Pooling instead (port 6543)
- Go to Supabase → Settings → Database → Connection string
- Look for "Connection pooling" section (may be in a different tab or section)
- Use the connection pooling URL (port 6543) instead of direct (port 5432)
- **For Oceania (Sydney) region**: Format: `postgresql://postgres.vplzphjygfazhsaqxhbt:[PASSWORD]@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres`
- **Note**: The region (`ap-southeast-2` for Sydney) must match your Supabase project region

**If you don't see Connection pooling:**
- Check if your Supabase project is **paused** (common cause of connection failures)
- Go to Supabase dashboard and ensure project is active
- Try the direct connection: `postgresql://postgres:[PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres`
- Ensure Network Restrictions allow all IPs (0.0.0.0/0)

---

## 📋 Quick Setup Checklist

### Step 1: Generate SECRET_KEY

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Linux/Mac:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or use OpenSSL:
```bash
openssl rand -hex 32
```

### Step 2: Get Supabase Connection String

1. Visit: https://supabase.com/dashboard/project/vplzphjygfazhsaqxhbt/settings/database
2. Find **Connection string** → **URI** tab
3. Copy the full connection string
4. Replace `[YOUR-PASSWORD]` with your actual password

### Step 3: Configure Railway

In Railway dashboard → **Variables**, add:

```env
# Option 1: Connection Pooling (RECOMMENDED for Railway - port 6543)
# For Oceania (Sydney) region - adjust region if your project is in a different region
DATABASE_URL=postgresql://postgres.vplzphjygfazhsaqxhbt:YOUR_PASSWORD@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres

# Option 2: Direct Connection (port 5432) - may have IPv6 issues on Railway
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres

SECRET_KEY=your-generated-secret-key
CORS_ORIGINS=https://your-app.vercel.app
```

**Important for Railway**: If you get "Network is unreachable" errors, try connection pooling (Option 1) instead of direct connection (Option 2). Connection pooling often resolves IPv6 connectivity issues.

### Step 4: Configure Vercel

In Vercel dashboard → **Settings** → **Environment Variables**, add:

```env
API_URL=https://web-production-2ce0.up.railway.app
```

**Note**: Replace with your actual Railway URL if different.

---

## 🔍 Variable Details

### DATABASE_URL
- **Required**: Yes
- **Format**: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`
- **Example**: `postgresql://postgres:mypassword123@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres`
- **Used by**: Backend database connection
- **Where**: Railway only

### SECRET_KEY
- **Required**: Yes
- **Format**: Random string (32+ characters recommended)
- **Used by**: JWT token signing for authentication
- **Where**: Railway only
- **Security**: Keep this secret! Never commit to Git.

### CORS_ORIGINS
- **Required**: Yes (for production)
- **Format**: Comma-separated URLs
- **Example**: `https://your-app.vercel.app,https://www.your-app.vercel.app`
- **Used by**: Backend CORS middleware
- **Where**: Railway only

### API_URL
- **Required**: Yes
- **Format**: Full URL with protocol
- **Example**: `https://web-production-2ce0.up.railway.app`
- **Used by**: Frontend to connect to backend
- **Where**: Vercel only

### LLM API Keys (Optional)
- **Required**: No (users provide via UI)
- **Used by**: Fallback if user doesn't provide keys
- **Where**: Railway only
- **Note**: Since the UI allows users to input their own API keys, these are optional fallbacks.

---

## ✅ Verification

### After Setting Railway Variables

1. Check Railway logs for:
   ```
   ✓ Database initialized (PostgreSQL)
   ```

2. Test health endpoint:
   ```bash
   curl https://your-app.railway.app/health
   ```

### After Setting Vercel Variables

1. Check Vercel build logs for:
   ```
   ✓ Injected API URL: https://your-app.railway.app
   ```

2. Visit your Vercel URL and check browser console:
   ```javascript
   console.log(window.API_URL) // Should show your Railway URL
   ```

---

## 🔐 Security Notes

1. **Never commit** `.env` files or environment variables to Git
2. **SECRET_KEY** should be unique and random
3. **DATABASE_URL** contains sensitive credentials - keep it secure
4. **CORS_ORIGINS** should only include trusted domains
5. LLM API keys in Railway are optional since users provide them via UI

---

## 📝 Summary Table

| Variable | Required | Platform | Purpose |
|----------|----------|----------|---------|
| `DATABASE_URL` | ✅ Yes | Railway | PostgreSQL connection |
| `SECRET_KEY` | ✅ Yes | Railway | JWT authentication |
| `CORS_ORIGINS` | ✅ Yes | Railway | Allow frontend requests |
| `API_URL` | ✅ Yes | Vercel | Backend API endpoint |
| `ANTHROPIC_API_KEY` | ⚠️ Optional | Railway | LLM fallback |
| `OPENAI_API_KEY` | ⚠️ Optional | Railway | LLM fallback |
| `GOOGLE_API_KEY` | ⚠️ Optional | Railway | LLM fallback |

---

## 🆘 Troubleshooting

### Database Connection Fails
- Check `DATABASE_URL` format
- Verify password is correct
- Ensure Supabase database is running
- Check if IP is whitelisted (if required)

### CORS Errors
- Verify `CORS_ORIGINS` includes your Vercel URL
- Check for trailing slashes
- Ensure Railway has redeployed after adding variable

### Frontend Can't Connect to Backend
- Verify `API_URL` in Vercel matches Railway URL
- Check Railway is running and accessible
- Verify CORS is configured correctly

