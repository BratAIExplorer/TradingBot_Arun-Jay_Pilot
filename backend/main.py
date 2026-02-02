from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routes import router as api_router
from backend.bot_manager import bot_manager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import os

# Rate Limiter Configuration
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="ARUN Titan V2 API",
    description="Headless Trading Bot Control API with JWT Authentication",
    version="2.1.0",
    docs_url="/docs",  # Swagger UI enabled
    redoc_url="/redoc"
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# Read allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.environ.get("ARUN_CORS_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    # Default origins for development
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

# Add any VPS origin from environment
VPS_ORIGIN = os.environ.get("ARUN_VPS_ORIGIN")
if VPS_ORIGIN:
    ALLOWED_ORIGINS.append(VPS_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes
app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "message": "ARUN Titan V2 Headless API Online 🚀",
        "version": "2.1.0",
        "docs": "/docs",
        "auth_required": True,
        "endpoints": {
            "login": "POST /api/auth/login",
            "status": "GET /api/status",
            "positions": "GET /api/positions",
            "pnl": "GET /api/pnl",
            "capital": "GET /api/capital",
            "start": "POST /api/control/start",
            "stop": "POST /api/control/stop",
            "logs": "GET /api/logs"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Application startup handler"""
    print("=" * 50)
    print("🚀 ARUN Titan V2 API Server Starting...")
    print("=" * 50)
    print(f"📖 API Docs: http://localhost:8000/docs")
    print(f"🔐 Authentication: JWT Bearer Token Required")
    print(f"🌐 CORS Origins: {ALLOWED_ORIGINS}")
    print("=" * 50)
    print("")
    print("⚠️  SECURITY REMINDER:")
    print("   Set these environment variables for production:")
    print("   - ARUN_JWT_SECRET=<random-secret-key>")
    print("   - ARUN_ADMIN_USER=<your-username>")
    print("   - ARUN_ADMIN_PASSWORD=<strong-password>")
    print("   - ARUN_CORS_ORIGINS=https://your-domain.com")
    print("")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler"""
    print("🛑 API Server Shutting Down...")
    if bot_manager.running:
        bot_manager.stop_bot()


# Rate limiting for critical endpoints
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Apply rate limiting:
    - General endpoints: 60 requests/minute
    - Control endpoints: 5 requests/minute
    """
    response = await call_next(request)
    return response


if __name__ == "__main__":
    # Get host/port from environment or use defaults
    HOST = os.environ.get("ARUN_API_HOST", "0.0.0.0")
    PORT = int(os.environ.get("ARUN_API_PORT", "8000"))
    
    # Check for SSL certificates
    SSL_KEYFILE = os.environ.get("ARUN_SSL_KEYFILE")
    SSL_CERTFILE = os.environ.get("ARUN_SSL_CERTFILE")
    
    if SSL_KEYFILE and SSL_CERTFILE:
        print("🔒 HTTPS Enabled")
        uvicorn.run(
            "backend.main:app", 
            host=HOST, 
            port=PORT, 
            reload=True,
            ssl_keyfile=SSL_KEYFILE,
            ssl_certfile=SSL_CERTFILE
        )
    else:
        print("⚠️  Running in HTTP mode (not recommended for production)")
        uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
