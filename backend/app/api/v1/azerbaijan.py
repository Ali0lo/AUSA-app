from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

router = APIRouter(prefix="/azerbaijan", tags=["Azerbaijan cutoffs"])


class AzerbaijanPrediction(BaseModel):
    status: str
    reason: str | None = None
    program_code: str | None = None
    university_name: str | None = None
    department_name: str | None = None
    score_type: str | None = None
    history_years: int | None = None
    run_id: str | None = None
    prediction_type: str | None = None
    model: str | None = None
    target_year: int | None = None
    predicted_cutoff: float | None = None
    lower_cutoff: float | None = None
    upper_cutoff: float | None = None


class AzerbaijanPredictionList(BaseModel):
    status: str
    items: list[AzerbaijanPrediction]


@router.get("/predictions", response_model=AzerbaijanPredictionList)
async def list_azerbaijan_predictions(
    request: Request,
    university: str | None = Query(None, max_length=300),
    group: str | None = Query(None, max_length=100),
):
    service = request.app.state.az_prediction_service
    items = service.list_predictions(university=university, group=group)
    return AzerbaijanPredictionList(status="listed" if items else "not_available", items=items)


@router.get("/predictions/{program_code}", response_model=AzerbaijanPrediction)
async def get_azerbaijan_prediction(program_code: str, request: Request):
    return request.app.state.az_prediction_service.predict(program_code)