"""Main FastAPI application for Astro MVP Backend."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils.errors import (
    AstroException,
    ValidationError,
    CalculationError,
    LLMError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.rate_limit_redis_url if settings.rate_limit_enabled else "memory://"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize services here if needed
    # await init_database()
    # await init_redis()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add timing
    start_time = time.time()
    
    response = await call_next(request)
    
    # Add timing info
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Exception handlers
@app.exception_handler(AstroException)
async def astro_exception_handler(request: Request, exc: AstroException):
    """Handle custom Astro exceptions."""
    logger.error(f"AstroException: {exc.message}", extra={
        "request_id": getattr(request.state, "request_id", None),
        "error_code": exc.error_code,
        "details": exc.details
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTPException: {exc.detail}", extra={
        "request_id": getattr(request.state, "request_id", None),
        "status_code": exc.status_code
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True, extra={
        "request_id": getattr(request.state, "request_id", None)
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoints
@app.get("/healthz")
async def health_check():
    """Liveness probe."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe."""
    # TODO: Check database and Redis connectivity
    return {"status": "ready", "timestamp": time.time()}


# Include API routers
from app.api import auth, profiles, compute, predict, admin, chat
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(compute.router, prefix="/compute", tags=["calculations"])
app.include_router(predict.router, prefix="/predict", tags=["predictions"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
