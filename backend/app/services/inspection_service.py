import os
import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models import (
    Inspection, InspectionImage, OcrResult, Declaration, ProductContext, Finding, AuditLog
)
from backend.app.core.config import settings
from backend.app.cv.preprocessing import preprocess_label_image
from backend.app.ai.quality import assess_image_quality
from backend.app.ocr.engine import run_ocr_on_image
from backend.app.extraction.extractor import extract_declarations_from_ocr
from backend.app.services.context_engine import enrich_context_from_declarations
from backend.app.rule_engine.engine import run_compliance_evaluation, load_rules_from_db

def run_full_inspection_analysis(inspection_id: str, db: Session, user_id: str = None) -> Dict[str, Any]:
    """
    Complete end-to-end pipeline execution:
    Image Quality -> Preprocessing -> PP-OCRv4 -> Declaration Extraction -> Context Enrichment -> Versioned Rule Adjudication.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise ValueError(f"Inspection {inspection_id} not found.")
        
    inspection.status = "ANALYZING"
    db.commit()
    
    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection_id).all()
    if not images:
        inspection.status = "CAPTURED"
        db.commit()
        raise ValueError("Cannot analyze inspection without at least one uploaded photograph.")
        
    all_extracted_decls: List[Dict[str, Any]] = []
    combined_ocr_text_list = []
    quality_scores = []
    has_blurry_image = False
    
    # Process each image
    for img in images:
        orig_path = img.storage_path
        if not os.path.exists(orig_path):
            continue
            
        # 1. Quality Assessment
        q_result = assess_image_quality(orig_path)
        img.quality_assessment = q_result
        img.is_acceptable = q_result.get("is_acceptable", True)
        quality_scores.append(q_result.get("quality_score", 1.0))
        if q_result.get("blur_score", 100.0) < 65.0:
            has_blurry_image = True
            
        # 2. Preprocessing (deskew, CLAHE, bilateral smoothing)
        if not img.processed_path or not os.path.exists(img.processed_path):
            proc_filename = f"proc_{img.id}.jpg"
            proc_path = str(settings.PROCESSED_DIR / proc_filename)
            try:
                preprocess_label_image(orig_path, proc_path)
                img.processed_path = proc_path
            except Exception as e:
                print(f"Warning: preprocessing failed on image {img.id}: {e}")
                img.processed_path = orig_path
                
        # 3. OCR Engine (PP-OCRv4 ONNX)
        ocr_record = db.query(OcrResult).filter(OcrResult.image_id == img.id).first()
        if not ocr_record:
            # Use processed image if available, else original
            run_path = img.processed_path if (img.processed_path and os.path.exists(img.processed_path)) else orig_path
            ocr_data = run_ocr_on_image(run_path)
            ocr_record = OcrResult(
                inspection_id=inspection_id,
                image_id=img.id,
                engine_name=ocr_data["engine_name"],
                engine_version=ocr_data["engine_version"],
                processing_time_ms=ocr_data["processing_time_ms"],
                full_text=ocr_data["full_text"],
                lines=ocr_data["lines"]
            )
            db.add(ocr_record)
            db.flush()
            
        combined_ocr_text_list.append(ocr_record.full_text)
        
        # 4. Declaration Extraction
        raw_decls = extract_declarations_from_ocr(ocr_record.lines, source_image_id=img.id)
        for d in raw_decls:
            d["view_type"] = img.view_type
            all_extracted_decls.append(d)
            
    # Persist or update declarations in database
    # Clear previous AI-extracted declarations (keep inspector edits if any)
    existing_decls = db.query(Declaration).filter(
        Declaration.inspection_id == inspection_id,
        Declaration.is_inspector_edited == False
    ).all()
    for ed in existing_decls:
        db.delete(ed)
    db.flush()
    
    for d in all_extracted_decls:
        decl_obj = Declaration(
            inspection_id=inspection_id,
            source_image_id=d["source_image_id"],
            category=d["category"],
            raw_text=d["raw_text"],
            normalized_value=d["normalized_value"],
            unit=d.get("unit"),
            confidence=d.get("confidence", 0.9),
            bbox=d.get("bbox", [0, 0, 0, 0]),
            extraction_method=d.get("extraction_method", "HYBRID"),
            is_inspector_edited=False
        )
        db.add(decl_obj)
    db.flush()
    
    # 5. Product Context Enrichment
    context = db.query(ProductContext).filter(ProductContext.inspection_id == inspection_id).first()
    if not context:
        context = ProductContext(inspection_id=inspection_id)
        db.add(context)
        db.flush()
        
    full_combined_text = "\n".join(combined_ocr_text_list)
    enrich_context_from_declarations(context, all_extracted_decls, full_combined_text)
    db.flush()
    
    # 6. Version-Aware Rule Evaluation
    overall_quality = float(sum(quality_scores) / max(1, len(quality_scores)))
    rules = load_rules_from_db(db, target_version=inspection.rule_version or context.target_rule_version)
    
    context_dict = {
        "commodity_category": context.commodity_category,
        "package_type": context.package_type,
        "is_food": context.is_food,
        "is_imported": context.is_imported,
        "is_ecommerce": context.is_ecommerce,
        "inspection_date": context.inspection_date
    }
    
    findings_list, compliance_status, summary = run_compliance_evaluation(
        rules=rules,
        declarations=all_extracted_decls,
        context=context_dict,
        overall_image_quality=overall_quality,
        has_blurry_image=has_blurry_image
    )
    
    # Preserve previous inspector decisions
    existing_overrides = {}
    prev_findings = db.query(Finding).filter(Finding.inspection_id == inspection_id).all()
    for pf in prev_findings:
        if pf.inspector_status:
            existing_overrides[pf.rule_id] = {
                "inspector_status": pf.inspector_status,
                "inspector_comment": pf.inspector_comment,
                "inspector_id": pf.inspector_id,
                "reviewed_at": pf.reviewed_at
            }
            
    # Clear previous findings
    db.query(Finding).filter(Finding.inspection_id == inspection_id).delete()
    db.flush()
    
    # Persist findings with overrides preserved
    for f in findings_list:
        override = existing_overrides.get(f["rule_id"])
        final_st = override["inspector_status"] if override else f["final_status"]
        
        finding_obj = Finding(
            inspection_id=inspection_id,
            rule_id=f["rule_id"],
            rule_version=f["rule_version"],
            clause_reference=f["clause_reference"],
            requirement_title=f["requirement_title"],
            ai_status=f["ai_status"],  # Original AI decision preserved
            inspector_status=override["inspector_status"] if override else None,
            final_status=final_st,
            severity=f["severity"],
            confidence=f["confidence"],
            explanation=f["explanation"],
            uncertainty_reason=f.get("uncertainty_reason"),
            observed_value=f.get("observed_value"),
            expected_condition=f["expected_condition"],
            evidence_references=f.get("evidence_references", []),
            inspector_comment=override["inspector_comment"] if override else None,
            inspector_id=override["inspector_id"] if override else None,
            reviewed_at=override["reviewed_at"] if override else None
        )
        db.add(finding_obj)
        
    # Update Inspection Status
    inspection.status = "REVIEW_REQUIRED"
    inspection.compliance_status = compliance_status
    
    # Log Audit Record
    audit = AuditLog(
        inspection_id=inspection_id,
        user_id=user_id,
        action="RUN_ANALYSIS",
        entity_type="INSPECTION",
        entity_id=inspection_id,
        new_state={
            "compliance_status": compliance_status,
            "summary": summary,
            "declarations_count": len(all_extracted_decls),
            "findings_count": len(findings_list)
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "inspection_id": inspection_id,
        "compliance_status": compliance_status,
        "summary": summary,
        "declarations_count": len(all_extracted_decls),
        "findings_count": len(findings_list),
        "overall_image_quality": round(overall_quality, 2),
        "has_blurry_image": has_blurry_image
    }
