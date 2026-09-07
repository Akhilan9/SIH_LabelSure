import os
import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Finding, Inspection, InspectionImage, User, AuditLog
from backend.app.schemas import (
    FindingResponse, FindingReviewUpdate, RuleLensFindingResponse, RuleLensInspectionResponse, EvidenceItem, HazardExplanation
)
from backend.app.rule_engine.hazard_engine import generate_hazard_violation_explanation
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(tags=["Findings & RuleLens"])

def build_rulelens_finding(finding: Finding, image_map: Dict[str, InspectionImage], fallback_image_url: Optional[str] = None) -> RuleLensFindingResponse:
    """
    Constructs a complete RuleLens finding representation containing all 13 statutory audit fields:
    1. Requirement
    2. Rule ID
    3. Rule version
    4. Clause/reference
    5. Observed value
    6. Expected condition
    7. Evidence image
    8. Bounding box
    9. OCR text
    10. AI confidence
    11. Decision
    12. Explanation
    13. Inspector status
    """
    enriched_evidences: List[EvidenceItem] = []
    evidence_image: Optional[str] = fallback_image_url
    primary_bbox: List[float] = [0.0, 0.0, 0.0, 0.0]
    primary_ocr_text: Optional[str] = finding.observed_value
    
    raw_evidences = finding.evidence_references or []
    for idx, ev in enumerate(raw_evidences):
        img_id = ev.get("image_id")
        img_obj = image_map.get(img_id) if img_id else None
        
        img_url = None
        proc_url = None
        if img_obj:
            fname = os.path.basename(img_obj.storage_path)
            img_url = f"/storage/uploads/{fname}"
            if img_obj.processed_path:
                proc_url = f"/storage/processed/{os.path.basename(img_obj.processed_path)}"
        elif fallback_image_url:
            img_url = fallback_image_url

        bbox = ev.get("bbox", [0.0, 0.0, 0.0, 0.0])
        snippet = ev.get("ocr_snippet") or ev.get("ocr_text")
        
        if idx == 0:
            if img_url:
                evidence_image = img_url
            if bbox and len(bbox) == 4:
                primary_bbox = bbox
            if snippet:
                primary_ocr_text = snippet
                
        enriched_evidences.append(EvidenceItem(
            image_id=img_id,
            view_type=ev.get("view_type", "LABEL"),
            image_url=img_url,
            processed_image_url=proc_url,
            bbox=bbox,
            ocr_text=snippet
        ))
        
    hazard_dict = generate_hazard_violation_explanation(
        clause_reference=finding.clause_reference,
        requirement_title=finding.requirement_title,
        observed_value=finding.observed_value,
        expected_condition=finding.expected_condition,
        final_status=finding.final_status,
        ocr_snippet=primary_ocr_text
    )
    hazard_exp = HazardExplanation(**hazard_dict) if hazard_dict else None

    return RuleLensFindingResponse(
        id=finding.id,
        inspection_id=finding.inspection_id,
        requirement=finding.requirement_title,
        rule_id=finding.rule_id,
        rule_version=finding.rule_version,
        clause_reference=finding.clause_reference,
        observed_value=finding.observed_value,
        expected_condition=finding.expected_condition,
        evidence_image=evidence_image,
        bounding_box=primary_bbox,
        ocr_text=primary_ocr_text,
        ai_confidence=finding.confidence,
        decision=finding.final_status,
        ai_status=finding.ai_status,
        final_status=finding.final_status,
        explanation=finding.explanation,
        hazard_explanation=hazard_exp,
        uncertainty_reason=finding.uncertainty_reason,
        severity=finding.severity,
        inspector_status=finding.inspector_status,
        inspector_comment=finding.inspector_comment,
        inspector_id=finding.inspector_id,
        reviewed_at=finding.reviewed_at,
        evidence_references=enriched_evidences,
        created_at=finding.created_at
    )

@router.get("/inspections/{id}/findings", response_model=List[FindingResponse])
def get_inspection_findings(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    findings = db.query(Finding).filter(Finding.inspection_id == id).all()
    return findings

@router.get("/inspections/{id}/rulelens", response_model=RuleLensInspectionResponse)
def get_inspection_rulelens_view(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dedicated RuleLens inspector endpoint providing comprehensive statutory findings,
    clause references, bounding box overlays, and image evidence links.
    """
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message=f"Inspection {id} not found.", status_code=404)
        
    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == id).all()
    image_map = {img.id: img for img in images}
    
    fallback_image_url = None
    if images:
        fallback_image_url = f"/storage/uploads/{os.path.basename(images[0].storage_path)}"
        
    findings = db.query(Finding).filter(Finding.inspection_id == id).all()
    rulelens_findings = [build_rulelens_finding(f, image_map, fallback_image_url) for f in findings]
    
    summary = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
    for f in findings:
        st = f.final_status.lower()
        if st in summary:
            summary[st] += 1

    return RuleLensInspectionResponse(
        inspection_id=insp.id,
        inspection_number=insp.inspection_number,
        commodity_name=insp.commodity_name,
        rule_version=insp.rule_version,
        overall_status=insp.status,
        compliance_status=insp.compliance_status,
        total_findings=len(rulelens_findings),
        summary=summary,
        findings=rulelens_findings
    )

@router.get("/findings/{id}/rulelens", response_model=RuleLensFindingResponse)
def get_single_finding_rulelens(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    finding = db.query(Finding).filter(Finding.id == id).first()
    if not finding:
        raise AppException(code="FINDING_NOT_FOUND", message=f"Finding {id} not found.", status_code=404)
        
    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == finding.inspection_id).all()
    image_map = {img.id: img for img in images}
    fallback_url = f"/storage/uploads/{os.path.basename(images[0].storage_path)}" if images else None
    
    return build_rulelens_finding(finding, image_map, fallback_url)

@router.patch("/findings/{id}", response_model=FindingResponse)
def review_finding_override(
    id: str,
    review_in: FindingReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    finding = db.query(Finding).filter(Finding.id == id).first()
    if not finding:
        raise AppException(code="FINDING_NOT_FOUND", message="Finding not found.", status_code=404)
        
    prev_state = {
        "ai_status": finding.ai_status,
        "inspector_status": finding.inspector_status,
        "final_status": finding.final_status,
        "inspector_comment": finding.inspector_comment
    }
    
    # Store human decision separately from AI decision
    finding.inspector_status = review_in.inspector_status
    finding.final_status = review_in.inspector_status  # Human override prevails in final determination
    finding.inspector_comment = review_in.inspector_comment
    finding.inspector_id = current_user.id
    finding.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
    
    # Recalculate inspection compliance verdict
    insp = db.query(Inspection).filter(Inspection.id == finding.inspection_id).first()
    if insp:
        all_findings = db.query(Finding).filter(Finding.inspection_id == insp.id).all()
        has_fail = any(f.final_status == "FAIL" or (f.id == id and review_in.inspector_status == "FAIL") for f in all_findings)
        has_uncertain = any(f.final_status == "UNCERTAIN" or (f.id == id and review_in.inspector_status == "UNCERTAIN") for f in all_findings)
        
        if has_fail:
            insp.compliance_status = "NON_COMPLIANT"
        elif has_uncertain:
            insp.compliance_status = "REQUIRES_REVIEW"
        else:
            insp.compliance_status = "COMPLIANT"
            
    db.add(AuditLog(
        inspection_id=finding.inspection_id,
        user_id=current_user.id,
        action="OVERRIDE_FINDING",
        entity_type="FINDING",
        entity_id=finding.id,
        previous_state=prev_state,
        new_state={
            "ai_status": finding.ai_status,
            "inspector_status": finding.inspector_status,
            "final_status": finding.final_status,
            "comment": review_in.inspector_comment
        }
    ))
    db.commit()
    db.refresh(finding)
    return finding
