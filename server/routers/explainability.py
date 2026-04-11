"""Explainability endpoint used by dashboard views."""

from fastapi import APIRouter, HTTPException, status

from server.explainability.contracts import validate_request_payload
from server.explainability.service import generate_explanation
from server.models.schemas import ExplainabilityRequest, ExplainabilityResponse

router = APIRouter(prefix="/explainability", tags=["explainability"])


@router.post("/generate", response_model=ExplainabilityResponse, status_code=status.HTTP_200_OK)
async def generate_explanation_route(payload: ExplainabilityRequest) -> ExplainabilityResponse:
    payload_dict = payload.model_dump(exclude_none=True)

    validation_error = validate_request_payload(payload_dict)
    if validation_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation_error)

    try:
        response = generate_explanation(payload_dict)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ExplainabilityResponse(**response)
