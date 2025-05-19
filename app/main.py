"""
Main application module for the AI Agent API.
"""
import logging
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router as api_router
from app.config import settings
from app.utils.logging import setup_logging
from app.utils.monitoring import setup_metrics

# Setup logging
logger = logging.getLogger(__name__)
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="AI Agent API",
    description="Enterprise-grade API for speech-to-text, language model, and text-to-speech processing",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup metrics if enabled
if settings.ENABLE_METRICS:
    setup_metrics(app)

# Include API router
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "1.0.0"}

# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )

if __name__ == "__main__":
    logger.info(f"Starting AI Agent API on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        log_level=settings.API_LOG_LEVEL,
    )
