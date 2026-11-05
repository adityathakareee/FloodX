"""Main entry point for FLOOD-X FastAPI Backend Application.

PCCOE International Grand Challenge 2026.
Predict | Prioritize | Protect
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import check_db_connection
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: verifies subsystems during startup."""
    setup_logging()
    logger.info("==================================================")
    logger.info("Initializing %s v%s", settings.PROJECT_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Pilot Region: %s", settings.PILOT_REGION)
    logger.info("==================================================")

    # Verify PostgreSQL/PostGIS connection at startup
    is_connected, latency, error = check_db_connection()
    if is_connected:
        logger.info("Database connection established successfully (latency: %.2f ms)", latency)
    else:
        logger.warning(
            "Database connection could not be established at startup: %s. "
            "Backend will continue in DEGRADED mode to support client health discovery.",
            error,
        )

    yield

    logger.info("Shutting down %s", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "AI-Powered Flood Intelligence & Emergency Decision-Support Platform "
            "for the PCCOE International Grand Challenge 2026.\n\n"
            "**Pilot Geography**: Pune / Mula-Mutha River Basin, Maharashtra, India.\n"
            "**Architecture**: Modular Monorepo — Phase 0 Foundation."
        ),
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized exception handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP %d error at %s: %s", exc.status_code, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "path": request.url.path,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error at %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "path": request.url.path,
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception at %s: %s", request.url.path, str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "Internal server error occurred",
                    "path": request.url.path,
                }
            },
        )

    # Mount API v1 router
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root discovery redirect / metadata endpoint
    @app.get(
        "/",
        tags=["Root"],
        summary="API Root Information",
        description="Root entry point providing discovery links to Swagger docs and Health endpoints.",
    )
    def root():
        return {
            "project": settings.PROJECT_NAME,
            "tagline": settings.PROJECT_TAGLINE,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": f"{settings.API_V1_PREFIX}/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
            "system_info": f"{settings.API_V1_PREFIX}/system/info",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )

