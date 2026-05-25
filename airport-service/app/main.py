import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import airports_router, health_router
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="""
## Airport Service

Microservice responsible for exposing Colombian airport data.

### Architecture
- **Pattern**: Hexagonal Architecture (Ports & Adapters)
- **Adapter**: `ApiColombiaAdapter` implements `IAirportExternalPort`
- **Data source**: [API Colombia](https://api-colombia.com)

### Key Design Decision
The frontend and other microservices **never** call API Colombia directly.
All external data is mediated through this service via the Adapter pattern.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(airports_router.router)
app.include_router(health_router.router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "airport-service",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": ["/airports", "/airports/plotly", "/airports/{id}", "/health"],
    }
