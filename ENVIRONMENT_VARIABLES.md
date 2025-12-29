# Environment Variables Guide

## 🚂 Railway (Backend) - Required Variables

### Essential Variables

```env
# Database Connection (from Railway PostgreSQL)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway

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

## 🗄️ Railway PostgreSQL (Database) - Connection String

Railway PostgreSQL provides connection strings, but you need the **PUBLIC** one for local development.

### ⚠️ Important: Internal vs Public Connection Strings

Railway provides two connection strings:
- **Internal** (`postgres.railway.internal`) - Only works inside Railway's network
- **Public** - Works from your local machine and external services

### To get your PUBLIC Railway PostgreSQL connection string:

1. Go to your Railway project dashboard
2. Click on your **PostgreSQL** service
3. Go to the **Variables** tab
4. Look for `DATABASE_URL` or `POSTGRES_URL`
5. **If it contains `postgres.railway.internal`**, you need the public connection string instead:
   - Go to **Connect** tab (or **Settings** → **Networking**)
   - Look for **Public Networking** or **Connection String (Public)**
   - Copy the public connection string (it will have a public hostname, not `railway.internal`)

**Public connection string format:**
```
postgresql://postgres:[PASSWORD]@[PUBLIC-HOST]:[PORT]/railway
```

**Example:**
```
postgresql://postgres:password123@containers-us-west-123.railway.app:5432/railway
```

**Note**: For Railway services (backend), you can use the internal connection string. For local development or external services, use the public one.

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

### Step 2: Get Railway PostgreSQL Connection String

1. Go to your Railway project dashboard
2. Click on your **PostgreSQL** service
3. Go to the **Variables** or **Connect** tab
4. Copy the `DATABASE_URL` or `POSTGRES_URL` connection string
5. It will look like: `postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway`
6. **That's it!** Railway PostgreSQL is much simpler - no connection pooling or region configuration needed

### Step 3: Configure Railway

In Railway dashboard → **Variables**, add:

```env
# Railway PostgreSQL connection string (from Railway dashboard)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@HOST:PORT/railway

SECRET_KEY=your-generated-secret-key
CORS_ORIGINS=https://your-app.vercel.app
```

**Note**: Railway PostgreSQL doesn't have the connection issues that Supabase had - it's much simpler and more reliable!

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

