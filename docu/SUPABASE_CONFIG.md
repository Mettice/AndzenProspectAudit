# Your Supabase Configuration

## 📋 Project Details

- **Project Name**: Andzen
- **Project ID**: `vplzphjygfazhsaqxhbt`
- **Project URL**: `https://vplzphjygfazhsaqxhbt.supabase.co`
- **Publishable API Key**: `sb_publishable_weWMSzJ7FLr_jOxd3K6CWQ_Pzg2SYbA`

## 🔑 Database Connection String

To get your database connection string:

1. Go to: https://supabase.com/dashboard/project/vplzphjygfazhsaqxhbt/settings/database
2. Scroll to **Connection string** section
3. Select **URI** tab
4. Copy the connection string (it will look like):
   ```
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   OR
   ```
   postgresql://postgres:[PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
   ```

## ⚙️ Quick Setup

### For Local Development

1. Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
   SECRET_KEY=your-secret-key-here
   ```

2. Generate a secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. Restart your server - tables will be created automatically!

### For Railway Deployment

Add these environment variables in Railway dashboard:

```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.vplzphjygfazhsaqxhbt.supabase.co:5432/postgres
SECRET_KEY=your-generated-secret-key
CORS_ORIGINS=https://your-app.vercel.app
```

## 🔐 Getting Your Database Password

If you don't have the password:

1. Go to: https://supabase.com/dashboard/project/vplzphjygfazhsaqxhbt/settings/database
2. Look for **Database password** section
3. Click **Reset database password** if needed
4. Copy the password (you'll only see it once!)

## ✅ Verification

After setting `DATABASE_URL`, restart your server and check logs:

```
✓ Database initialized (PostgreSQL)
```

Then verify in Supabase dashboard → **Table Editor**:
- `users` table should exist
- `reports` table should exist

## 📚 Full Setup Guide

See `SUPABASE_SETUP.md` for detailed instructions.

