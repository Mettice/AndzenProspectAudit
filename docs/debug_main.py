from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

print("=== LOADING DEBUG MAIN ===")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI()

# Add CORS (suspect this might be the issue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "debug server root"}

@app.get("/test")
async def test():
    print("=== TEST ROUTE HIT ===")
    return {"message": "debug test route works"}

# Test the problematic double decorator pattern
@app.get("/ui", include_in_schema=False)
@app.get("/ui/", include_in_schema=False) 
async def serve_ui():
    print("=== UI ROUTE HIT ===")
    return {"message": "UI route works"}

# Test adding the audit router (suspect this is the issue)
try:
    print("=== IMPORTING AUDIT ROUTER ===")
    from api.routes import audit
    print("=== AUDIT IMPORT SUCCESS ===")
    
    print("=== REGISTERING AUDIT ROUTER ===") 
    app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
    print("=== AUDIT ROUTER REGISTERED ===")
except Exception as e:
    print(f"=== AUDIT ROUTER ERROR: {e} ===")

print("=== ROUTES REGISTERED ===")
print(f"Frontend dir: {FRONTEND_DIR}")