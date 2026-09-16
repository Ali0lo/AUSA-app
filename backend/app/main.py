from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.services.prediction import AzerbaijanPredictionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the Azerbaijan data and artifacts once. Requests must never refit or
    # reload a model, and an absent artifact remains an explicit absence.
    app.state.az_prediction_service = AzerbaijanPredictionService.load()
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

# CORS: exact origins from settings only.
#
# There was an allow_origin_regex=r"https?://.*" here, which matched every origin
# and made the allowlist decorative. Combined with allow_credentials=True that lets
# any site a logged-in user visits issue credentialed requests and read the replies.
# Add deployed frontend origins to BACKEND_CORS_ORIGINS instead.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(ConnectionError)
async def _database_unreachable_handler(request: Request, exc: ConnectionError) -> JSONResponse:
    """Report a lost database connection as an outage.

    asyncpg raises a bare ConnectionRefusedError (an OSError) when Postgres is
    unreachable, so SQLAlchemy never wraps it and endpoint-level SQLAlchemyError
    handlers do not see it. Without this it surfaces as an opaque 500 -- and the
    code this replaced answered it by fabricating data instead.
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "A required service is temporarily unavailable."},
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
