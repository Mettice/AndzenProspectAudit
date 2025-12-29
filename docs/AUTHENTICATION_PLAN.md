# Authentication & Report Management System

## Architecture Overview

### Components:
1. **Database**: SQLAlchemy with SQLite (can upgrade to PostgreSQL)
2. **Authentication**: JWT tokens with FastAPI OAuth2
3. **Roles**: Admin, User, Viewer
4. **Report Management**: CRUD operations with file storage

## Database Schema

### Users Table
- id (PK)
- username (unique)
- email (unique)
- hashed_password
- role (enum: admin, user, viewer)
- created_at
- is_active

### Reports Table
- id (PK)
- filename
- client_name
- auditor_name
- client_code
- industry
- analysis_period_days
- file_path_html
- file_path_pdf
- file_path_word
- created_by (FK to Users)
- created_at
- updated_at
- status (enum: completed, failed, processing)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns JWT)
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user info

### Reports (Protected)
- `GET /api/reports` - List all reports (with filters)
- `GET /api/reports/{id}` - Get report details
- `DELETE /api/reports/{id}` - Delete report (admin only)
- `GET /api/reports/{id}/download` - Download report file

### Admin (Admin only)
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}` - Update user role
- `DELETE /api/admin/users/{id}` - Delete user

## Implementation Steps

1. ✅ Add database dependencies (SQLAlchemy, passlib, python-jose)
2. ✅ Create database models
3. ✅ Create authentication service
4. ✅ Create protected route dependencies
5. ✅ Update report generation to save to DB
6. ✅ Create report management routes
7. ✅ Create admin routes
8. ✅ Update frontend with login UI

