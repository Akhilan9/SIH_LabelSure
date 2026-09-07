from fastapi import APIRouter
import datetime
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ocr_engine": settings.OCR_ENGINE
    }
