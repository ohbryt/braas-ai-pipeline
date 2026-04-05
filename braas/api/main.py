"""FastAPI application for BRaaS AI Pipeline."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from braas.api.routes import experiments_router, equipment_router, inventory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: initialize resources
    yield
    # Shutdown: cleanup resources
    pass


app = FastAPI(
    title="BRaaS AI Pipeline",
    description="Biotechnology Research as a Service AI Pipeline",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(experiments_router, prefix="/experiments", tags=["experiments"])
app.include_router(equipment_router, prefix="/equipment", tags=["equipment"])
app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])


@app.get("/", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "braas-ai-pipeline"}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Alternative health check endpoint."""
    return {"status": "healthy"}
