from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, Declaration, ProductContext, OcrResult, User
from backend.app.schemas import (
    JurisdictionSummary,
    InternationalComparisonResponse,
    ScanTextRequest,
    ScanTextResponse,
    BannedSubstanceMatch
)
from backend.app.api.deps import get_current_user
from backend.app.services.international_engine import (
    get_available_jurisdictions,
    get_jurisdiction_rules,
    get_global_bans_database,
    scan_text_for_banned_substances,
    compare_product_with_jurisdiction
)

router = APIRouter(prefix="/international", tags=["International Metrology & Global Bans"])


@router.get("/jurisdictions", response_model=List[JurisdictionSummary])
def list_jurisdictions(
    current_user: User = Depends(get_current_user)
):
    """List all available international metrological jurisdictions and regulatory frameworks."""
    return get_available_jurisdictions()


@router.get("/jurisdictions/{jurisdiction_id}")
def get_jurisdiction_detail(
    jurisdiction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get complete ruleset and metrological requirements for a specific jurisdiction."""
    data = get_jurisdiction_rules(jurisdiction_id)
    if not data:
        raise AppException(
            code="JURISDICTION_NOT_FOUND",
            message=f"Jurisdiction '{jurisdiction_id}' not found.",
            status_code=404
        )
    return data


@router.get("/banned-substances")
def list_banned_substances(
    category: Optional[str] = Query(None, description="Filter by category (e.g. FOOD_ADDITIVE, COSMETIC_INGREDIENT)"),
    search: Optional[str] = Query(None, description="Search by name, E-number, or alias"),
    current_user: User = Depends(get_current_user)
):
    """Retrieve database of globally banned/restricted substances, health risks, and legal citations."""
    db_data = get_global_bans_database()
    substances = db_data.get("substances", [])

    if category:
        substances = [s for s in substances if s.get("category", "").upper() == category.upper()]

    if search:
        s_lower = search.lower()
        substances = [
            s for s in substances
            if s_lower in s.get("canonical_name", "").lower() or
            any(s_lower in alias.lower() for alias in s.get("aliases", []))
        ]

    return {
        "version": db_data.get("version"),
        "total_count": len(substances),
        "substances": substances
    }


@router.get("/inspections/{inspection_id}/compare", response_model=InternationalComparisonResponse)
def compare_inspection(
    inspection_id: str,
    jurisdiction: str = Query("USA", description="Target jurisdiction ID (USA, EU, GBR, AUS, GCC)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare an Indian Legal Metrology inspection against an international jurisdiction.
    Identifies mandatory declaration differences, legal prohibitions (e.g. MRP), and flags
    any product ingredients/substances banned in the destination or other global markets.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise AppException(
            code="INSPECTION_NOT_FOUND",
            message=f"Inspection {inspection_id} not found.",
            status_code=404
        )

    # Fetch declarations
    declarations = db.query(Declaration).filter(Declaration.inspection_id == inspection_id).all()
    decl_dicts = [
        {
            "category": d.category,
            "raw_text": d.raw_text,
            "normalized_value": d.normalized_value,
            "unit": d.unit,
            "confidence": d.confidence
        }
        for d in declarations
    ]

    # Fetch product context
    context = db.query(ProductContext).filter(ProductContext.inspection_id == inspection_id).first()
    ctx_dict = None
    if context:
        ctx_dict = {
            "commodity_category": context.commodity_category,
            "product_type": context.product_type,
            "is_food": context.is_food,
            "is_imported": context.is_imported,
            "origin_country": context.origin_country
        }

    # Fetch OCR text
    ocr_results = db.query(OcrResult).filter(OcrResult.inspection_id == inspection_id).all()
    raw_ocr = " ".join([o.full_text for o in ocr_results if o.full_text])

    try:
        comparison = compare_product_with_jurisdiction(
            jurisdiction_id=jurisdiction,
            declarations=decl_dicts,
            context=ctx_dict,
            raw_ocr_text=raw_ocr
        )
        return comparison
    except ValueError as e:
        raise AppException(
            code="COMPARISON_ERROR",
            message=str(e),
            status_code=400
        )


@router.post("/scan-text", response_model=ScanTextResponse)
def scan_text(
    payload: ScanTextRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Directly scans arbitrary label or ingredients text for substances banned internationally.
    Returns matched chemical/additive names, banning countries, statutory citations, and health hazards.
    """
    matches = scan_text_for_banned_substances(
        text=payload.text,
        target_jurisdiction_id=payload.jurisdiction_id
    )
    return {
        "matches": matches,
        "total_found": len(matches)
    }
