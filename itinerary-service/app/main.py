import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import itineraries_router, health_router
from app.core.config import settings
from app.infrastructure.database.session import create_tables

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="""
## Itinerary Service

Manages travel itineraries with full CRUD operations.

### Architecture
- **Pattern**: Hexagonal Architecture (Ports & Adapters)
- **Persistence**: SQLAlchemy + SQLite/PostgreSQL via `IItineraryRepository`
- **Validation**: Airports validated via HTTP call to Airport Service through `IAirportValidationPort`

### Airport Validation Flow
Before saving any itinerary, this service calls Airport Service to verify
both departure and arrival airports exist. If either is invalid, a 404 is returned.
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

@app.on_event("startup")
def on_startup():
    create_tables()
    logging.getLogger(__name__).info("Database tables created/verified")

app.include_router(itineraries_router.router)
app.include_router(health_router.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "itinerary-service",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": [
            "POST /itineraries",
            "GET /itineraries",
            "GET /itineraries/{id}",
            "PUT /itineraries/{id}",
            "DELETE /itineraries/{id}",
            "GET /health",
        ],
    }
