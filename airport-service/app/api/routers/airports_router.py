import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_airport_service
from app.api.schemas import AirportResponse, PlotlyAirportResponse
from app.application.services.airport_query_service import AirportQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/airports", tags=["Airports"])


@router.get(
    "",
    response_model=List[AirportResponse],
    summary="List all Colombian airports",
    response_description="List of airports from API Colombia, adapted to internal domain model",
    responses={
        200: {"description": "Airports retrieved successfully"},
        502: {"description": "API Colombia unreachable"},
    },
)
async def list_airports(
    service: AirportQueryService = Depends(get_airport_service),
):
    """
    Returns all Colombian airports.
    Data is fetched from API Colombia via the Adapter pattern and transformed
    to the internal domain model before being returned.
    """
    try:
        airports = service.list_all()
        return [
            AirportResponse(
                id=a.id,
                name=a.name,
                city=a.city,
                latitude=a.latitude,
                longitude=a.longitude,
                iata_code=a.iata_code,
            )
            for a in airports
        ]
    except ConnectionError as e:
        logger.error(f"Upstream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Airport data source unavailable: {e}",
        )


@router.get(
    "/plotly",
    response_model=List[PlotlyAirportResponse],
    summary="Get airports in Plotly-ready format",
    response_description="Airport data formatted for Plotly JS scatter geo map",
    responses={
        200: {"description": "Plotly data retrieved successfully"},
        502: {"description": "API Colombia unreachable"},
    },
)
async def get_plotly_data(
    service: AirportQueryService = Depends(get_airport_service),
):
    """
    Returns airports formatted for Plotly JS visualization.
    Includes nombre, ciudad, latitud, longitud, codigo.
    """
    try:
        data = service.get_plotly_data()
        return data
    except ConnectionError as e:
        logger.error(f"Upstream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Airport data source unavailable: {e}",
        )


@router.get(
    "/{airport_id}",
    response_model=AirportResponse,
    summary="Get airport by ID",
    responses={
        200: {"description": "Airport found"},
        404: {"description": "Airport not found"},
        502: {"description": "API Colombia unreachable"},
    },
)
async def get_airport(
    airport_id: str,
    service: AirportQueryService = Depends(get_airport_service),
):
    """
    Returns a single airport by its numeric ID from API Colombia.
    """
    try:
        airport = service.get_by_id(airport_id)
        if airport is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Airport with id '{airport_id}' not found",
            )
        return AirportResponse(
            id=airport.id,
            name=airport.name,
            city=airport.city,
            latitude=airport.latitude,
            longitude=airport.longitude,
            iata_code=airport.iata_code,
        )
    except HTTPException:
        raise
    except ConnectionError as e:
        logger.error(f"Upstream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Airport data source unavailable: {e}",
        )
