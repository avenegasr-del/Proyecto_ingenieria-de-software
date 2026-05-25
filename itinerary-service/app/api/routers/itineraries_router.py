import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_command_service, get_query_service
from app.api.schemas import ItineraryCreate, ItineraryUpdate, ItineraryResponse, ErrorResponse
from app.application.services.itinerary_command_service import ItineraryCommandService
from app.application.services.itinerary_query_service import ItineraryQueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


@router.post(
    "",
    response_model=ItineraryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a travel itinerary",
    responses={
        201: {"description": "Itinerary created successfully"},
        404: {"model": ErrorResponse, "description": "Airport not found"},
        422: {"description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Airport Service unavailable"},
    },
)
def create_itinerary(
    payload: ItineraryCreate,
    svc: ItineraryCommandService = Depends(get_command_service),
):
    try:
        itinerary = svc.create(
            user_name=payload.user_name,
            departure_airport_id=payload.departure_airport_id,
            arrival_airport_id=payload.arrival_airport_id,
            travel_date=payload.travel_date,
            duration_minutes=payload.duration_minutes,
        )
        return ItineraryResponse.model_validate(itinerary)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Airport Service unavailable: {e}")


@router.get(
    "",
    response_model=List[ItineraryResponse],
    summary="List itineraries",
    responses={200: {"description": "List of itineraries"}},
)
def list_itineraries(
    user_name: Optional[str] = Query(None, description="Filter by user name"),
    svc: ItineraryQueryService = Depends(get_query_service),
):
    items = svc.get_all(user_name=user_name)
    return [ItineraryResponse.model_validate(i) for i in items]


@router.get(
    "/{itinerary_id}",
    response_model=ItineraryResponse,
    summary="Get itinerary by ID",
    responses={
        200: {"description": "Itinerary found"},
        404: {"model": ErrorResponse, "description": "Itinerary not found"},
    },
)
def get_itinerary(
    itinerary_id: int,
    svc: ItineraryQueryService = Depends(get_query_service),
):
    item = svc.get_by_id(itinerary_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Itinerary {itinerary_id} not found")
    return ItineraryResponse.model_validate(item)


@router.put(
    "/{itinerary_id}",
    response_model=ItineraryResponse,
    summary="Update itinerary",
    responses={
        200: {"description": "Itinerary updated"},
        404: {"model": ErrorResponse, "description": "Itinerary or airport not found"},
        503: {"model": ErrorResponse, "description": "Airport Service unavailable"},
    },
)
def update_itinerary(
    itinerary_id: int,
    payload: ItineraryUpdate,
    svc: ItineraryCommandService = Depends(get_command_service),
):
    try:
        update_data = payload.model_dump(exclude_none=True)
        item = svc.update(itinerary_id, **update_data)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Itinerary {itinerary_id} not found")
        return ItineraryResponse.model_validate(item)
    except HTTPException:
        raise
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Airport Service unavailable: {e}")


@router.delete(
    "/{itinerary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete itinerary",
    responses={
        204: {"description": "Itinerary deleted"},
        404: {"model": ErrorResponse, "description": "Itinerary not found"},
    },
)
def delete_itinerary(
    itinerary_id: int,
    svc: ItineraryCommandService = Depends(get_command_service),
):
    if not svc.delete(itinerary_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Itinerary {itinerary_id} not found")
