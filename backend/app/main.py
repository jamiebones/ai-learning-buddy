import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.core.config import settings
from app.api.api import api_router
from app.core.db import create_tables, close_db_connections
from app.core.logging import setup_logging
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


# Setup logging
logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up application")
    try:
        await create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.exception("Failed to create database tables: %s", str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    try:
        await close_db_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.exception("Error closing database connections: %s", str(e))


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app_instance = FastAPI(
        title=settings.PROJECT_NAME,
        description="Production API with FastAPI",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        debug=settings.ENVIRONMENT == "development",
        lifespan=lifespan,
    )

    # Add middleware - order matters!
    _configure_middleware(app_instance)
    
    # Add routes
    app_instance.include_router(api_router, prefix=settings.API_PREFIX)
    
    # Add exception handlers
    _configure_exception_handlers(app_instance)
    
    return app_instance


def _configure_middleware(app_instance: FastAPI) -> None:
    """Configure all middleware for the application."""
    # HTTPS redirect in production
    if settings.ENVIRONMENT == "production" and settings.ENFORCE_HTTPS:
        app_instance.add_middleware(HTTPSRedirectMiddleware)

    # Security middleware
    app_instance.add_middleware(SecurityHeadersMiddleware)
    
    # Trusted hosts
    if settings.ALLOWED_HOSTS:
        app_instance.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # CORS configuration
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Process-Time", "X-Request-ID"],
        max_age=600,
    )
    
    # Compression middleware
    app_instance.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting
    if settings.ENABLE_RATE_LIMIT:
        app_instance.add_middleware(
            RateLimitMiddleware,
            limit=settings.RATE_LIMIT_REQUESTS,
            timeframe=settings.RATE_LIMIT_TIMEFRAME,
        )
    
    # Process time middleware
    @app_instance.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return response
        except Exception as e:
            logger.exception("Unhandled exception during request processing: %s", str(e))
            process_time = time.time() - start_time
            error_response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )
            error_response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return error_response


def _configure_exception_handlers(app_instance: FastAPI) -> None:
    """Configure exception handlers for the application."""
    @app_instance.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "Validation error: %s",
            str(exc.errors()),
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )


# Health check endpoint
@api_router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns a 200 OK response if the service is healthy.
    """
    # In a production app, this would check database connection, external services, etc.
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server")
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=settings.ENVIRONMENT == "development",
        access_log=settings.ENVIRONMENT != "production",
        log_level="info" if settings.ENVIRONMENT != "production" else "error",
        workers=settings.WORKERS,
    ) 