"""
FastAPI application for Klaviyo prospect audit automation.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from api.routes import audit, auth, reports, admin
from api.database import init_db

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Klaviyo Prospect Audit API",
    description="Automated audit report generation for Klaviyo prospects",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()
    print("✓ Database initialized")

# CORS middleware - Configure for production
cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
]

# Add Vercel/Custom origins from environment
if os.getenv("CORS_ORIGINS"):
    cors_origins.extend([origin.strip() for origin in os.getenv("CORS_ORIGINS").split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
# This serves all files in the frontend directory under /ui
if FRONTEND_DIR.exists():
    # Mount static files for /ui/ (with trailing slash) and sub-paths
    app.mount("/ui/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    print(f"✓ Frontend mounted at /ui/ from {FRONTEND_DIR}")

# Explicit route for /ui (without trailing slash) to avoid redirect
@app.get("/ui")
async def serve_ui():
    """Serve the frontend index.html at /ui (no redirect)."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found"}

# Explicit route for CSS to ensure it's accessible
@app.get("/ui/style.css")
async def serve_css():
    """Serve the CSS file explicitly."""
    css_path = FRONTEND_DIR / "style.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return {"error": "CSS not found"}

# Basic routes
@app.get("/")
async def root():
    """Root endpoint - redirect to UI or show API info."""
    # Try to serve the UI at root, fallback to API info
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Klaviyo Prospect Audit API", "version": "1.0.0", "ui": "/ui"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/test-ui")
async def test_ui():
    return {"message": "UI test route works", "frontend_path": str(FRONTEND_DIR)}

# Include routers
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])