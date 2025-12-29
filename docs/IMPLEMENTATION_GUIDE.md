# Authentication & Report Management - Implementation Guide

## ✅ What Has Been Implemented

### 1. Database Models
- **User Model**: Stores user accounts with roles (admin, user, viewer)
- **Report Model**: Stores audit report metadata and file paths

### 2. Authentication System
- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Protected routes with dependencies

### 3. API Endpoints

#### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT token)
- `GET /api/auth/me` - Get current user info

#### Reports (`/api/reports`)
- `GET /api/reports` - List reports (with pagination & filters)
- `GET /api/reports/{id}` - Get report details
- `GET /api/reports/{id}/download` - Download report file
- `DELETE /api/reports/{id}` - Delete report (admin only)

#### Admin (`/api/admin`)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Delete user

### 4. Report Generation Integration
- Reports are automatically saved to database when generated
- Links report to the user who created it
- Stores file paths for HTML, PDF, and Word formats

## 🚀 Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
Create or update `.env` file:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./data/audit.db
```

### Step 3: Create First Admin User
```bash
python scripts/create_admin.py
```

### Step 4: Start the Server
```bash
uvicorn api.main:app --reload
```

## 📝 Usage Examples

### 1. Register a New User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123",
    "role": "user"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true
  }
}
```

### 3. Generate Report (Protected)
```bash
curl -X POST "http://localhost:8000/api/audit/generate-morrison" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your_klaviyo_key",
    "client_name": "Acme Co",
    "days": 90
  }'
```

### 4. List Reports
```bash
curl -X GET "http://localhost:8000/api/reports?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Delete Report (Admin Only)
```bash
curl -X DELETE "http://localhost:8000/api/reports/1" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## 🔐 Role Permissions

### Admin
- ✅ Full access to all reports
- ✅ Create, update, delete users
- ✅ Delete any report
- ✅ Generate reports

### User
- ✅ Generate reports
- ✅ View own reports only
- ✅ Download own reports
- ❌ Cannot delete reports
- ❌ Cannot view other users' reports

### Viewer
- ✅ View own reports only
- ✅ Download own reports
- ❌ Cannot generate reports
- ❌ Cannot delete reports

## 🎨 Next Steps: Frontend Integration

### 1. Create Login Page
- Add login form to frontend
- Store JWT token in localStorage
- Redirect to dashboard after login

### 2. Create Dashboard
- Display list of reports
- Filter and search functionality
- Download buttons
- Delete button (admin only)

### 3. Update Report Generation
- Include authentication token in requests
- Show success message with report ID
- Link to view report in dashboard

### 4. Add User Management (Admin)
- User list page
- Create/edit user forms
- Role assignment

## 🔒 Security Notes

1. **SECRET_KEY**: Must be changed in production! Use a strong random string.
2. **Password Hashing**: Uses bcrypt with automatic salt generation.
3. **JWT Tokens**: 24-hour expiration (configurable).
4. **API Keys**: Klaviyo API keys are hashed before storage.
5. **Role-Based Access**: All routes check user permissions.

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email
- `hashed_password`: Bcrypt hashed password
- `role`: Enum (admin, user, viewer)
- `is_active`: Boolean flag
- `created_at`: Timestamp
- `updated_at`: Timestamp

### Reports Table
- `id`: Primary key
- `filename`: Report filename
- `client_name`: Client name
- `auditor_name`: Auditor name
- `client_code`: Client code
- `industry`: Industry type
- `analysis_period_days`: Analysis period
- `file_path_html`: Path to HTML file
- `file_path_pdf`: Path to PDF file
- `file_path_word`: Path to Word file
- `status`: Enum (processing, completed, failed)
- `klaviyo_api_key_hash`: Hashed API key
- `llm_provider`: LLM provider used
- `llm_model`: LLM model used
- `created_by_id`: Foreign key to Users
- `created_at`: Timestamp
- `updated_at`: Timestamp

## 🐛 Troubleshooting

### Database Not Found
- Ensure `data/` directory exists
- Run `python scripts/create_admin.py` to initialize database

### Authentication Fails
- Check SECRET_KEY is set in .env
- Verify password is correct
- Check user is_active status

### Permission Denied
- Verify user role has required permissions
- Check JWT token is valid and not expired
- Ensure Authorization header is included

