import os
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, Finding, Declaration, Report, User, AuditLog, InspectionImage, Rule
from backend.app.schemas import ReportResponse, ComprehensiveStructuredReportResponse, FollowUpAction
from backend.app.reports.generator import generate_inspection_pdf
from backend.app.api.deps import get_current_user, require_role
from backend.app.api.findings import build_rulelens_finding
from backend.app.rule_engine.hazard_engine import generate_recommended_follow_up_actions

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


def build_comprehensive_structured_report(
    insp: Inspection,
    db: Session,
    rep: Optional[Report] = None
) -> ComprehensiveStructuredReportResponse:
    """Compiles all 9 statutory pillars into a structured audit report."""
    # Pillar 1: Product Details
    ctx = insp.context
    product_details = {
        "commodity_name": getattr(insp, "commodity_name", "Packaged Commodity"),
        "commodity_category": ctx.commodity_category if ctx else "GENERAL_COMMODITY",
        "product_type": ctx.product_type if ctx else "Pre-Packaged Good",
        "is_food": ctx.is_food if ctx else False,
        "is_imported": ctx.is_imported if ctx else False,
        "origin_country": ctx.origin_country if ctx else "India",
        "package_type": ctx.package_type if ctx else "SINGLE_PRE_PACKAGED",
        "declared_net_quantity": ctx.declared_net_quantity if ctx else None,
        "declared_unit": ctx.declared_unit if ctx else "",
        "retail_establishment": getattr(insp, "retail_establishment", None),
        "batch_number": getattr(insp, "batch_number", None),
        "target_rule_version": getattr(insp, "rule_version", "LMPC-2026-RULES")
    }

    # Pillar 2: Extracted Declarations
    decls = db.query(Declaration).filter(Declaration.inspection_id == insp.id).all()

    # Pillar 3: Applicable Rules
    rule_records = db.query(Rule).filter(Rule.rule_version == insp.rule_version).all()
    applicable_rules = [
        {
            "rule_id": r.rule_id,
            "rule_version": r.rule_version,
            "clause_reference": r.clause_reference,
            "requirement": r.requirement,
            "severity": r.severity
        }
        for r in rule_records
    ] if rule_records else [
        {"rule_id": "R-MRP-01", "clause_reference": "Rule 6(1)(e)", "requirement": "MRP Declaration"},
        {"rule_id": "R-QTY-01", "clause_reference": "Rule 6(1)(f)", "requirement": "Net Quantity & Units"},
        {"rule_id": "R-MFG-01", "clause_reference": "Rule 6(1)(a)", "requirement": "Manufacturer / Packer Address"},
        {"rule_id": "R-CARE-01", "clause_reference": "Rule 6(1)(g)", "requirement": "Consumer Grievance Care"},
        {"rule_id": "R-DATE-01", "clause_reference": "Rule 6(1)(d)", "requirement": "Month & Year of Manufacture"},
        {"rule_id": "R-NAME-01", "clause_reference": "Rule 6(1)(b)", "requirement": "Generic / Common Commodity Name"}
    ]

    # Pillar 4: Compliance Status & Scorecard
    findings = db.query(Finding).filter(Finding.inspection_id == insp.id).all()
    total_findings = len(findings)
    pass_count = sum(1 for f in findings if f.final_status == "PASS")
    fail_count = sum(1 for f in findings if f.final_status == "FAIL")
    uncertain_count = sum(1 for f in findings if f.final_status == "UNCERTAIN")
    rate = round((pass_count / total_findings * 100), 1) if total_findings > 0 else 0.0

    verdict = getattr(insp, "compliance_status", "PENDING")
    insp_status = getattr(insp, "status", "DRAFT")

    compliance_status = {
        "overall_status": insp_status,
        "compliance_verdict": verdict,
        "compliance_rate": rate,
        "total_rules": total_findings,
        "passed_count": pass_count,
        "failed_count": fail_count,
        "uncertain_count": uncertain_count
    }

    # Pillar 5: Detected Violations with 5-Step Hazard Chain
    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == insp.id).all()
    image_map = {img.id: img for img in images}
    fallback_url = f"/storage/uploads/{os.path.basename(images[0].storage_path)}" if images else None

    rulelens_findings = [build_rulelens_finding(f, image_map, fallback_url) for f in findings]
    detected_violations = [rf for rf in rulelens_findings if rf.final_status != "PASS"]

    # Pillar 6: Visual Evidence (images query above)

    # Pillar 7: Inspector Verification
    inspector_obj = getattr(insp, "inspector", None)
    inspector_name = inspector_obj.full_name if inspector_obj else "Authorized Legal Metrology Officer"
    badge_number = (inspector_obj.badge_number if inspector_obj and inspector_obj.badge_number else "DL-LM-2026")

    inspector_verification = {
        "inspector_id": insp.inspector_id or "usr_inspector_01",
        "inspector_name": inspector_name,
        "badge_number": badge_number,
        "verification_status": "VERIFIED" if insp_status in ["FINALIZED", "COMPLETED"] else "REVIEWED",
        "overrides_count": sum(1 for f in findings if f.inspector_status is not None),
        "digital_seal_sha256": rep.pdf_sha256 if rep else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }

    # Pillar 8: Timestamps
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    timestamps = {
        "created_at": insp.created_at.isoformat() if insp.created_at else now_utc.isoformat(),
        "analyzed_at": getattr(insp, "updated_at", now_utc).isoformat(),
        "reviewed_at": insp.finalized_at.isoformat() if getattr(insp, "finalized_at", None) else None,
        "certified_at": rep.generated_at.isoformat() if rep else now_utc.isoformat()
    }

    # Pillar 9: Recommended Follow-up Actions
    findings_dicts = [{"final_status": f.final_status, "severity": f.severity, "requirement_title": f.requirement_title} for f in findings]
    follow_up_dicts = generate_recommended_follow_up_actions(verdict, findings_dicts, product_details)
    follow_up_actions = [FollowUpAction(**a) for a in follow_up_dicts]

    cert_num = rep.certificate_number if rep else f"LMPC-CERT-{insp.inspection_number.replace('INSP-', '')}"
    pdf_url = rep.pdf_url if rep else f"/storage/reports/report_{insp.id}.pdf"
    pdf_sha256 = rep.pdf_sha256 if rep else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    return ComprehensiveStructuredReportResponse(
        certificate_number=cert_num,
        inspection_id=insp.id,
        inspection_number=insp.inspection_number,
        compliance_verdict=verdict,
        generated_at=rep.generated_at if rep else now_utc,
        generated_by=rep.generated_by if rep else inspector_name,
        pdf_url=pdf_url,
        pdf_sha256=pdf_sha256,
        product_details=product_details,
        extracted_declarations=decls,
        applicable_rules=applicable_rules,
        compliance_status=compliance_status,
        detected_violations=detected_violations,
        visual_evidence=images,
        inspector_verification=inspector_verification,
        timestamps=timestamps,
        recommended_follow_up_actions=follow_up_actions
    )


@router.get("/inspections/{id}/structured-report", response_model=ComprehensiveStructuredReportResponse)
def get_structured_inspection_report(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a comprehensive structured inspection report containing all 9 statutory pillars:
    product details, extracted declarations, applicable rules, compliance status, detected violations,
    visual evidence, inspector verification, certified timestamps, and recommended follow-up actions.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)

    rep = db.query(Report).filter(Report.inspection_id == id).order_by(Report.generated_at.desc()).first()
    return build_comprehensive_structured_report(insp, db, rep)


@router.get("/reports/{id}/structured", response_model=ComprehensiveStructuredReportResponse)
def get_structured_report_by_id(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve comprehensive 9-pillar structured report by report ID."""
    rep = db.query(Report).filter(Report.id == id).first()
    if not rep:
        raise AppException(code="REPORT_NOT_FOUND", message="Report not found.", status_code=404)

    insp = db.query(Inspection).filter(Inspection.id == rep.inspection_id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Associated inspection not found.", status_code=404)

    return build_comprehensive_structured_report(insp, db, rep)

