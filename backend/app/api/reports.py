from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, Finding, Declaration, Report, User, AuditLog, InspectionImage
from backend.app.schemas import ReportResponse
from backend.app.reports.generator import generate_inspection_pdf
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(tags=["Reports"])

@router.get("/reports", response_model=List[ReportResponse])
def list_reports(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Report)
    if search:
        query = query.filter(
            (Report.certificate_number.ilike(f"%{search}%")) |
            (Report.generated_by.ilike(f"%{search}%")) |
            (Report.compliance_verdict.ilike(f"%{search}%"))
        )
    return query.order_by(Report.generated_at.desc()).all()

@router.post("/inspections/{id}/report", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_inspection_report(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    findings = db.query(Finding).filter(Finding.inspection_id == id).all()
    declarations = db.query(Declaration).filter(Declaration.inspection_id == id).all()
    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.inspection_id == id).order_by(AuditLog.timestamp.desc()).limit(10).all()
    ctx = insp.context
    
    findings_data = [
        {
            "clause_reference": f.clause_reference,
            "requirement_title": f.requirement_title,
            "ai_status": f.ai_status,
            "final_status": f.final_status,
            "severity": f.severity,
            "observed_value": f.observed_value,
            "expected_condition": f.expected_condition,
            "explanation": f.explanation,
            "bbox": f.evidence_references[0].get("bbox") if f.evidence_references and len(f.evidence_references) > 0 and isinstance(f.evidence_references[0], dict) else None,
            "ai_confidence": f.confidence,
            "inspector_status": f.inspector_status,
            "inspector_comment": f.inspector_comment,
            "inspector_id": f.inspector_id
        }
        for f in findings
    ]
    
    decls_data = [
        {
            "category": d.category,
            "raw_text": d.raw_text,
            "normalized_value": d.normalized_value,
            "confidence": d.confidence,
            "extraction_method": d.extraction_method,
            "bbox": d.bbox
        }
        for d in declarations
    ]

    images_data = [
        {
            "id": img.id,
            "view_type": img.view_type,
            "storage_path": img.storage_path,
            "sha256_hash": img.sha256_hash,
            "width": img.width,
            "height": img.height,
            "quality_score": (img.quality_assessment or {}).get("quality_score", 0.95)
        }
        for img in images
    ]

    product_context = {
        "commodity_category": ctx.commodity_category if ctx else "GENERAL_COMMODITY",
        "product_type": ctx.product_type if ctx else "Pre-Packaged Good",
        "is_food": ctx.is_food if ctx else False,
        "is_imported": ctx.is_imported if ctx else False,
        "origin_country": ctx.origin_country if ctx else "India",
        "package_type": ctx.package_type if ctx else "SINGLE_PRE_PACKAGED",
        "declared_net_quantity": ctx.declared_net_quantity if ctx else None,
        "declared_unit": ctx.declared_unit if ctx else "",
        "retail_establishment": getattr(insp, "retail_establishment", None),
        "batch_number": getattr(insp, "batch_number", None)
    }

    audit_data = [
        {
            "action": a.action,
            "user_id": a.user_id,
            "timestamp": a.timestamp.isoformat() if a.timestamp else "",
            "new_state": a.new_state
        }
        for a in audit_logs
    ]
    
    inspection_meta = {
        "id": insp.id,
        "inspection_number": insp.inspection_number,
        "commodity_name": insp.commodity_name,
        "brand_name": insp.brand_name,
        "rule_version": insp.rule_version,
        "compliance_status": insp.compliance_status,
        "status": insp.status,
        "inspector_name": current_user.full_name,
        "retail_establishment": getattr(insp, "retail_establishment", None),
        "batch_number": getattr(insp, "batch_number", None)
    }
    
    pdf_info = generate_inspection_pdf(
        inspection_data=inspection_meta,
        findings=findings_data,
        declarations=decls_data,
        product_context=product_context,
        images_data=images_data,
        audit_logs=audit_data
    )
    
    summary = {
        "total_rules_evaluated": len(findings),
        "passed": sum(1 for f in findings if f.final_status == "PASS"),
        "failed": sum(1 for f in findings if f.final_status == "FAIL"),
        "uncertain": sum(1 for f in findings if f.final_status == "UNCERTAIN"),
        "not_applicable": sum(1 for f in findings if f.final_status == "NOT_APPLICABLE"),
        "critical_violations": sum(1 for f in findings if f.final_status == "FAIL" and f.severity == "CRITICAL"),
        "inspector_overrides": sum(1 for f in findings if f.inspector_status is not None)
    }

    # Strict compliance truth check: If any finding is UNCERTAIN and not resolved,
    # compliance verdict cannot be falsely recorded as COMPLIANT
    has_uncertain = any(f.final_status == "UNCERTAIN" for f in findings)
    if has_uncertain and insp.compliance_status == "COMPLIANT":
        verdict_recorded = "REQUIRES_REVIEW"
    else:
        verdict_recorded = insp.compliance_status
    
    import uuid
    report_id = str(uuid.uuid4())
    report_record = Report(
        id=report_id,
        inspection_id=insp.id,
        certificate_number=pdf_info["certificate_number"],
        generated_by=current_user.full_name,
        compliance_verdict=verdict_recorded,
        pdf_url=pdf_info["pdf_url"],
        pdf_sha256=pdf_info["pdf_sha256"],
        summary=summary,
        model_versions={
            "ocr_engine": "RapidOCR/PaddleOCR-PP-OCRv4",
            "rule_version": insp.rule_version,
            "cv_evaluator": "Laplacian Blur & Variance v1.0",
            "platform_version": "APEX LabelSure v1.0.0"
        }
    )
    db.add(report_record)
    
    db.add(AuditLog(
        inspection_id=insp.id,
        user_id=current_user.id,
        action="GENERATE_REPORT",
        entity_type="REPORT",
        entity_id=report_id,
        new_state={"certificate_number": report_record.certificate_number, "pdf_sha256": report_record.pdf_sha256}
    ))
    db.commit()
    db.refresh(report_record)
    
    return report_record

@router.get("/inspections/{id}/report", response_model=ReportResponse)
def get_inspection_report(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rep = db.query(Report).filter(Report.inspection_id == id).order_by(Report.generated_at.desc()).first()
    if not rep:
        raise AppException(code="REPORT_NOT_FOUND", message="No report has been generated for this inspection yet.", status_code=404)
    return rep
