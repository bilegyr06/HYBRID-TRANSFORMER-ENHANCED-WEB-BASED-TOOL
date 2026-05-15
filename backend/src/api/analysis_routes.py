from fastapi import APIRouter

from src.schemas.analysis import AnalysisRequest, AnalysisResponse
from src.services.analysis_service import generate_analysis_results


router = APIRouter(tags=["Analysis"])


@router.post("/analysis/results", response_model=AnalysisResponse)
async def analysis_results(request: AnalysisRequest):
    return generate_analysis_results(request)
