from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("Successfully connected to PostgreSQL database.")
    except Exception as e:
        print(f"Startup Notice: Database connection check skipped or waiting for DB: {e}")
    
    yield
    
    # Shutdown: Clean up connections
    await engine.dispose()
    print("Database engine connections closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health Check"])
async def root():
    return {
        "message": "Welcome to AUSA - AI University & Scholarship Advisor API",
        "docs": "/docs",
        "status": "online",
    }


@app.get("/health", tags=["Health Check"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
