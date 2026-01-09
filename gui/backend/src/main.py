"""Maicrosoft GUI - FastAPI Backend.

Auto-generated from meta-plan.yaml
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base

from routers.auth import router as auth_router
from routers.plans import router as plans_router
from routers.validation import router as validation_router
from routers.execution import router as execution_router
from routers.primitives import router as primitives_router
from routers.secrets import router as secrets_router
from routers.templates import router as templates_router
from routers.github import router as github_router
from routers.compile import router as compile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Maicrosoft GUI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(plans_router, prefix="/api/plans", tags=["plans"])
app.include_router(validation_router, prefix="/api/validation", tags=["validation"])
app.include_router(execution_router, prefix="/api/execution", tags=["execution"])
app.include_router(primitives_router, prefix="/api/primitives", tags=["primitives"])
app.include_router(secrets_router, prefix="/api/secrets", tags=["secrets"])
app.include_router(templates_router, prefix="/api/templates", tags=["templates"])
app.include_router(github_router, prefix="/api/github", tags=["github"])
app.include_router(compile_router, prefix="/api/compile", tags=["compile"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
