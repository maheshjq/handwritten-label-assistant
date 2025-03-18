"""
Main FastAPI application for Handwritten Label AI Assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os

from app.api.routes import recognition, validate, models
from app.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the application
app = FastAPI(
    title="Handwritten Label AI Assistant",
    description="An API for recognizing handwritten text in images using LLMs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recognition.router, prefix="/api/recognition", tags=["Recognition"])
app.include_router(validate.router, prefix="/api/validate", tags=["Validation"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])

# Create required directories
@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    if settings.ENABLE_STORAGE:
        os.makedirs(os.path.join(settings.STORAGE_PATH, "images"), exist_ok=True)
        os.makedirs(os.path.join(settings.STORAGE_PATH, "results"), exist_ok=True)
        os.makedirs(os.path.join(settings.STORAGE_PATH, "cache"), exist_ok=True)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def read_root():
    """Welcome message for the root URL."""
    return {
        "message": "Welcome to the Handwritten Label AI Assistant!",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )