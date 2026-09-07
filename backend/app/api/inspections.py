import uuid
import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, ProductContext, User, Finding, AuditLog
from backend.app.schemas import (
    InspectionCreate, InspectionUpdate, InspectionSummary, InspectionDetailResponse,
    ProductContextResponse, ProductContextUpdate
)
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/inspections", tags=["Inspections"])

def generate_inspection_number(db: Session) -> str:
    count = db.query(Inspection).count() + 1
    year = datetime.datetime.now().year
    return f"INSP-{year}-{count:05d}"

@router.post("", response_model=InspectionSummary, status_code=status.HTTP_201_CREATED)
def create_inspection(
    insp_in: InspectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp_number = generate_inspection_number(db)
    inspection = Inspection(
        inspection_number=insp_number,
        inspector_id=current_user.id,
        status="DRAFT",
        compliance_status="PENDING",
        commodity_name=insp_in.commodity_name,
        brand_name=insp_in.brand_name,
        rule_version=insp_in.rule_version,
        notes=insp_in.notes
    )
    db.add(inspection)
    db.flush()
    
    # Create associated ProductContext
    context_in = insp_in.context
    context = ProductContext(
        inspection_id=inspection.id,
        commodity_category=context_in.commodity_category if context_in else "GENERAL_COMMODITY",
        product_type=context_in.product_type if context_in else "Pre-Packaged Good",
        is_food=context_in.is_food if context_in else False,
        is_imported=context_in.is_imported if context_in else False,
        origin_country=context_in.origin_country if context_in else None,
        package_type=context_in.package_type if context_in else "SINGLE_PRE_PACKAGED",
        declared_net_quantity=context_in.declared_net_quantity if context_in else None,
        declared_unit=context_in.declared_unit if context_in else None,
        is_ecommerce=context_in.is_ecommerce if context_in else False,
        platform_name=context_in.platform_name if context_in else None,
        inspection_date=context_in.inspection_date if (context_in and context_in.inspection_date) else datetime.date.today().isoformat(),
        target_rule_version=insp_in.rule_version
    )
    db.add(context)
    
    # Audit log
    audit = AuditLog(
        inspection_id=inspection.id,
        user_id=current_user.id,
        action="CREATE_INSPECTION",
        entity_type="INSPECTION",
        entity_id=inspection.id,
        new_state={"inspection_number": insp_number, "commodity_name": insp_in.commodity_name}
    )
    db.add(audit)
    db.commit()
    db.refresh(inspection)
    
    return InspectionSummary(
        id=inspection.id,
        inspection_number=inspection.inspection_number,
        inspector_id=inspection.inspector_id,
        inspector_name=current_user.full_name,
        status=inspection.status,
        compliance_status=inspection.compliance_status,
        commodity_name=inspection.commodity_name,
        brand_name=inspection.brand_name,
        rule_version=inspection.rule_version,
        total_images=0,
        findings_summary={"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0},
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
        finalized_at=inspection.finalized_at
    )

@router.get("", response_model=List[InspectionSummary])
def list_inspections(
    search: Optional[str] = Query(None, description="Search by inspection number, commodity, or brand"),
    status: Optional[str] = Query(None, description="Filter by status"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inspection)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Inspection.inspection_number.ilike(s)) |
            (Inspection.commodity_name.ilike(s)) |
            (Inspection.brand_name.ilike(s))
        )
    if status:
        query = query.filter(Inspection.status == status)
    if compliance_status:
        query = query.filter(Inspection.compliance_status == compliance_status)
        
    inspections = query.order_by(Inspection.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for insp in inspections:
        summary_counts = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
        for f in insp.findings:
            st = f.final_status.lower()
            if st in summary_counts:
                summary_counts[st] += 1
                
        results.append(InspectionSummary(
            id=insp.id,
            inspection_number=insp.inspection_number,
            inspector_id=insp.inspector_id,
            inspector_name=insp.inspector.full_name if insp.inspector else "Unknown",
            status=insp.status,
            compliance_status=insp.compliance_status,
            commodity_name=insp.commodity_name,
            brand_name=insp.brand_name,
            rule_version=insp.rule_version,
            total_images=len(insp.images),
            findings_summary=summary_counts,
            created_at=insp.created_at,
            updated_at=insp.updated_at,
            finalized_at=insp.finalized_at
        ))
    return results

@router.get("/{id}", response_model=InspectionDetailResponse)
def get_inspection_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(
            code="INSPECTION_NOT_FOUND",
            message=f"Inspection with ID {id} does not exist.",
            status_code=status.HTTP_404_NOT_FOUND
        )
        
    summary_counts = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
    for f in insp.findings:
        st = f.final_status.lower()
        if st in summary_counts:
            summary_counts[st] += 1
            
    return InspectionDetailResponse(
        id=insp.id,
        inspection_number=insp.inspection_number,
        inspector_id=insp.inspector_id,
        inspector_name=insp.inspector.full_name if insp.inspector else "Unknown",
        status=insp.status,
        compliance_status=insp.compliance_status,
        commodity_name=insp.commodity_name,
        brand_name=insp.brand_name,
        rule_version=insp.rule_version,
        total_images=len(insp.images),
        findings_summary=summary_counts,
        created_at=insp.created_at,
        updated_at=insp.updated_at,
        finalized_at=insp.finalized_at,
        context=insp.context,
        images=insp.images,
        declarations=insp.declarations,
        findings=insp.findings
    )

@router.patch("/{id}", response_model=InspectionSummary)
def update_inspection(
    id: str,
    insp_up: InspectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    prev_state = {"status": insp.status, "commodity_name": insp.commodity_name}
    
    if insp_up.commodity_name is not None:
        insp.commodity_name = insp_up.commodity_name
    if insp_up.brand_name is not None:
        insp.brand_name = insp_up.brand_name
    if insp_up.rule_version is not None:
        insp.rule_version = insp_up.rule_version
    if insp_up.notes is not None:
        insp.notes = insp_up.notes
    if insp_up.status is not None:
        insp.status = insp_up.status
        
    db.add(AuditLog(
        inspection_id=insp.id,
        user_id=current_user.id,
        action="UPDATE_INSPECTION",
        entity_type="INSPECTION",
        entity_id=insp.id,
        previous_state=prev_state,
        new_state={"status": insp.status, "commodity_name": insp.commodity_name}
    ))
    db.commit()
    db.refresh(insp)
    
    return InspectionSummary(
        id=insp.id,
        inspection_number=insp.inspection_number,
        inspector_id=insp.inspector_id,
        inspector_name=insp.inspector.full_name if insp.inspector else "Unknown",
        status=insp.status,
        compliance_status=insp.compliance_status,
        commodity_name=insp.commodity_name,
        brand_name=insp.brand_name,
        rule_version=insp.rule_version,
        total_images=len(insp.images),
        findings_summary={"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0},
        created_at=insp.created_at,
        updated_at=insp.updated_at,
        finalized_at=insp.finalized_at
    )

@router.get("/{id}/context", response_model=ProductContextResponse)
def get_inspection_context(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ctx = db.query(ProductContext).filter(ProductContext.inspection_id == id).first()
    if not ctx:
        raise AppException(code="CONTEXT_NOT_FOUND", message="Product context not found.", status_code=404)
    return ctx

@router.patch("/{id}/context", response_model=ProductContextResponse)
def update_inspection_context(
    id: str,
    ctx_up: ProductContextUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    ctx = db.query(ProductContext).filter(ProductContext.inspection_id == id).first()
    if not ctx:
        raise AppException(code="CONTEXT_NOT_FOUND", message="Product context not found.", status_code=404)
        
    prev_state = {
        "commodity_category": ctx.commodity_category,
        "is_food": ctx.is_food,
        "is_imported": ctx.is_imported,
        "origin_country": ctx.origin_country,
        "package_type": ctx.package_type,
        "declared_net_quantity": ctx.declared_net_quantity,
        "declared_unit": ctx.declared_unit,
        "is_ecommerce": ctx.is_ecommerce
    }
    
    update_data = ctx_up.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(ctx, field, val)
        
    db.add(AuditLog(
        inspection_id=id,
        user_id=current_user.id,
        action="EDIT_PRODUCT_CONTEXT",
        entity_type="PRODUCT_CONTEXT",
        entity_id=ctx.id,
        previous_state=prev_state,
        new_state=update_data
    ))
    db.commit()
    db.refresh(ctx)
    return ctx

@router.post("/{id}/finalize", response_model=InspectionSummary)
def finalize_inspection(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    # Check if there are unresolved findings
    fail_count = db.query(Finding).filter(Finding.inspection_id == id, Finding.final_status == "FAIL").count()
    uncertain_count = db.query(Finding).filter(Finding.inspection_id == id, Finding.final_status == "UNCERTAIN").count()
    
    if fail_count > 0:
        verdict = "NON_COMPLIANT"
    elif uncertain_count > 0:
        verdict = "REQUIRES_REVIEW"
    else:
        verdict = "COMPLIANT"
        
    insp.status = "FINALIZED"
    insp.compliance_status = verdict
    insp.finalized_at = datetime.datetime.now(datetime.timezone.utc)
    
    db.add(AuditLog(
        inspection_id=insp.id,
        user_id=current_user.id,
        action="FINALIZE_INSPECTION",
        entity_type="INSPECTION",
        entity_id=insp.id,
        new_state={"compliance_status": verdict, "finalized_at": insp.finalized_at.isoformat()}
    ))
    db.commit()
    db.refresh(insp)
    
    return InspectionSummary(
        id=insp.id,
        inspection_number=insp.inspection_number,
        inspector_id=insp.inspector_id,
        inspector_name=insp.inspector.full_name if insp.inspector else "Unknown",
        status=insp.status,
        compliance_status=insp.compliance_status,
        commodity_name=insp.commodity_name,
        brand_name=insp.brand_name,
        rule_version=insp.rule_version,
        total_images=len(insp.images),
        findings_summary={"pass": 0, "fail": fail_count, "uncertain": uncertain_count, "not_applicable": 0},
        created_at=insp.created_at,
        updated_at=insp.updated_at,
        finalized_at=insp.finalized_at
    )
