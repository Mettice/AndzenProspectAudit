# Supabase Database Setup Guide

## 📋 Prerequisites

You have:
- **Project URL**: `https://vplzphjygfazhsaqxhbt.supabase.co`
- **Publishable API Key**: `sb_publishable_weWMSzJ7FLr_jOxd3K6CWQ_Pzg2SYbA`

## 🔑 Step 1: Get Your Database Password

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: **Andzen**
3. Go to **Settings** → **Database**
4. Scroll down to **Connection string** section
5. Look for **Connection pooling** or **Direct connection**
6. You'll see a connection string like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
   ```
7. **Copy the password** from the connection string, or reset it if needed

## 🔧 Step 2: Create Connection String

The connection string format is:
```
postgresql://postgres:[PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
```

Replace `[PASSWORD]` with your actual database password.

**Example:**
```
postgresql://postgres:MySecurePassword123@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
```

## 📝 Step 3: Configure Environment Variables

### Option A: Create `.env` file (for local development)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your database connection string:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
   SECRET_KEY=your-random-secret-key-here
   ```

3. Generate a secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### Option B: Railway Environment Variables (for production)

When deploying to Railway, add these environment variables in the Railway dashboard:

- `DATABASE_URL`: Your full PostgreSQL connection string
- `SECRET_KEY`: A random secret key (use the command above)
- `CORS_ORIGINS`: Your frontend URL (e.g., `https://your-app.vercel.app`)

## 🗄️ Step 4: Initialize Database Tables

Once the `DATABASE_URL` is set, the application will automatically create tables on startup.

To verify:
1. Restart your FastAPI server
2. Check the logs for: `✓ Database initialized (PostgreSQL)`
3. Go to Supabase dashboard → **Table Editor** to see your tables:
   - `users`
   - `reports`

## 🔐 Step 5: Enable Row Level Security (RLS) in Supabase

For production security:

1. Go to Supabase dashboard → **Authentication** → **Policies**
2. For the `users` table, create policies:
   - **Select**: Users can read their own data
   - **Insert**: Users can create their own records
   - **Update**: Users can update their own data

3. For the `reports` table:
   - **Select**: Users can read their own reports
   - **Insert**: Users can create reports
   - **Update**: Users can update their own reports
   - **Delete**: Only admins can delete reports

## ✅ Step 6: Create First Admin User

After the database is connected, create your first admin user:

```bash
python scripts/create_admin.py
```

This will prompt you for:
- Username
- Email
- Password

The user will be created with `admin` role.

## 🧪 Step 7: Test the Connection

1. Start your server:
   ```bash
   uvicorn api.main:app --reload
   ```

2. Check the startup logs:
   ```
   ✓ Database initialized (PostgreSQL)
   ```

3. Test the API:
   ```bash
   curl http://localhost:8000/health
   ```

## 📊 Step 8: Verify in Supabase Dashboard

1. Go to **Table Editor** in Supabase
2. You should see:
   - `users` table (empty initially)
   - `reports` table (empty initially)

3. After creating a user via the API, refresh to see the data.

## 🔍 Troubleshooting

### Connection Refused
- Check that your IP is allowed in Supabase → **Settings** → **Database** → **Connection pooling**
- Verify the password is correct
- Ensure the connection string format is correct

### Authentication Failed
- Double-check the password
- Make sure you're using the `postgres` user (default)

### Tables Not Created
- Check server logs for errors
- Verify `DATABASE_URL` is set correctly
- Ensure `psycopg2-binary` is installed: `pip install psycopg2-binary`

## 🚀 Next Steps

1. ✅ Database connected
2. ✅ Tables created
3. ✅ Admin user created
4. 🔄 Deploy to Railway with environment variables
5. 🔄 Set up frontend on Vercel
6. 🔄 Configure CORS for production

