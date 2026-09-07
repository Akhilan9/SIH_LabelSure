from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import os
import uuid
import base64
import hashlib
import datetime
from PIL import Image as PILImage

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.models import SyncQueue, Inspection, ProductContext, User, AuditLog, InspectionImage, Finding, Declaration
from backend.app.api.deps import get_current_user
from backend.app.ai.quality import assess_image_quality
from backend.app.cv.preprocessing import preprocess_label_image
from backend.app.services.inspection_service import run_full_inspection_analysis

router = APIRouter(prefix="/sync", tags=["Offline Sync"])

@router.post("/inspections")
def sync_offline_inspection(
    payload: Dict[str, Any],
    idempotency_key: str = Header(..., alias="X-Idempotency-Key"),
    client_id: str = Header(..., alias="X-Client-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Idempotent synchronization endpoint for offline mobile inspector client.
    Guarantees zero duplication when network requests are retried.
    Supports inline base64 images and automatic OCR/RuleEngine pipeline triggering.
    """
    existing_sync = db.query(SyncQueue).filter(
        SyncQueue.idempotency_key == idempotency_key
    ).first()
    
    # 1. Duplicate Prevention: Return existing record if already processed
    if existing_sync and existing_sync.status == "PROCESSED" and existing_sync.inspection_id:
        insp = db.query(Inspection).filter(Inspection.id == existing_sync.inspection_id).first()
        if insp:
            summary_counts = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
            for f in insp.findings:
                st = f.final_status.lower()
                if st in summary_counts:
                    summary_counts[st] += 1
            return {
                "success": True,
                "status": "ALREADY_SYNCED",
                "inspection_id": insp.id,
                "inspection_number": insp.inspection_number,
                "compliance_status": insp.compliance_status,
                "images_count": len(insp.images),
                "findings_summary": summary_counts
            }

    # 2. Retry or New Entry Setup
    if existing_sync:
        sync_entry = existing_sync
        sync_entry.attempts += 1
        sync_entry.status = "PENDING"
        sync_entry.payload = payload
        sync_entry.client_id = client_id
    else:
        sync_entry = SyncQueue(
            client_id=client_id,
            idempotency_key=idempotency_key,
            payload=payload,
            status="PENDING",
            attempts=1
        )
        db.add(sync_entry)
    db.commit()
    db.refresh(sync_entry)
    
    try:
        # Create inspection from payload
        year = datetime.datetime.now().year
        count = db.query(Inspection).count() + 1
        insp_num = payload.get("inspection_number") or f"INSP-{year}-{count:05d}"
        
        insp = Inspection(
            inspection_number=insp_num,
            inspector_id=current_user.id,
            status="SYNCED",
            compliance_status=payload.get("compliance_status", "PENDING"),
            commodity_name=payload.get("commodity_name", "Synchronized Packaged Commodity"),
            brand_name=payload.get("brand_name"),
            rule_version=payload.get("rule_version", "LMPC-2026-RULES"),
            notes=payload.get("notes")
        )
        db.add(insp)
        db.flush()
        
        # Add Product Context
        ctx_data = payload.get("context", {})
        context = ProductContext(
            inspection_id=insp.id,
            commodity_category=ctx_data.get("commodity_category", "GENERAL_COMMODITY"),
            product_type=ctx_data.get("product_type", "Pre-Packaged Good"),
            is_food=ctx_data.get("is_food", False),
            is_imported=ctx_data.get("is_imported", False),
            origin_country=ctx_data.get("origin_country"),
            package_type=ctx_data.get("package_type", "SINGLE_PRE_PACKAGED"),
            declared_net_quantity=ctx_data.get("declared_net_quantity"),
            declared_unit=ctx_data.get("declared_unit"),
            is_ecommerce=ctx_data.get("is_ecommerce", False),
            inspection_date=ctx_data.get("inspection_date") or datetime.date.today().isoformat(),
            target_rule_version=insp.rule_version
        )
        db.add(context)
        db.flush()

        # Handle offline stored images if present in payload
        offline_images = payload.get("images", [])
        saved_image_records = []
        for img_item in offline_images:
            view_type = img_item.get("view_type", "FRONT").upper()
            raw_b64 = img_item.get("image_base64") or img_item.get("file_data")
            if not raw_b64:
                continue
                
            # Strip data URI header if present
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
                
            img_bytes = base64.b64decode(raw_b64)
            sha256_hash = hashlib.sha256(img_bytes).hexdigest()
            img_id = str(uuid.uuid4())
            filename = f"{img_id}.jpg"
            storage_path = str(settings.UPLOAD_DIR / filename)
            
            with open(storage_path, "wb") as f:
                f.write(img_bytes)
                
            try:
                with PILImage.open(storage_path) as p_img:
                    w, h = p_img.size
            except Exception:
                w, h = 800, 600

            quality_result = assess_image_quality(storage_path)
            proc_filename = f"proc_{img_id}.jpg"
            proc_path = str(settings.PROCESSED_DIR / proc_filename)
            try:
                preprocess_label_image(storage_path, proc_path)
            except Exception:
                proc_path = storage_path

            img_rec = InspectionImage(
                id=img_id,
                inspection_id=insp.id,
                view_type=view_type,
                original_filename=img_item.get("filename", filename),
                storage_path=storage_path,
                processed_path=proc_path,
                sha256_hash=sha256_hash,
                width=w,
                height=h,
                file_size_bytes=len(img_bytes),
                mime_type="image/jpeg",
                quality_assessment=quality_result,
                is_acceptable=quality_result.get("is_acceptable", True)
            )
            db.add(img_rec)
            saved_image_records.append(img_rec)

        db.flush()

        # Optional automatic analysis trigger if images exist
        if payload.get("auto_analyze", True) and len(saved_image_records) > 0:
            insp.status = "ANALYZING"
            db.commit()
            try:
                run_full_inspection_analysis(inspection_id=insp.id, db=db, user_id=current_user.id)
            except Exception as ae:
                print(f"Sync analysis non-fatal warning: {ae}")
                insp.status = "REVIEW_REQUIRED"
        else:
            insp.status = "REVIEW_REQUIRED" if len(saved_image_records) > 0 else "SYNCED"

        sync_entry = db.query(SyncQueue).filter(SyncQueue.idempotency_key == idempotency_key).first()
        sync_entry.inspection_id = insp.id
        sync_entry.status = "PROCESSED"
        sync_entry.last_error = None
        
        db.add(AuditLog(
            inspection_id=insp.id,
            user_id=current_user.id,
            action="OFFLINE_SYNC",
            entity_type="INSPECTION",
            entity_id=insp.id,
            new_state={"idempotency_key": idempotency_key, "client_id": client_id, "images_synced": len(saved_image_records)}
        ))
        db.commit()
        db.refresh(insp)
        
        summary_counts = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
        for f in insp.findings:
            st = f.final_status.lower()
            if st in summary_counts:
                summary_counts[st] += 1
                
        return {
            "success": True,
            "status": insp.status,
            "inspection_id": insp.id,
            "inspection_number": insp.inspection_number,
            "compliance_status": insp.compliance_status,
            "images_count": len(saved_image_records),
            "findings_summary": summary_counts
        }
        
    except Exception as e:
        db.rollback()
        fail_entry = db.query(SyncQueue).filter(SyncQueue.idempotency_key == idempotency_key).first()
        if fail_entry:
            fail_entry.status = "FAILED"
            fail_entry.last_error = str(e)
            db.commit()
        raise AppException(code="SYNC_FAILED", message=f"Sync error: {str(e)}", status_code=500)

@router.get("/status/{idempotency_key}")
def get_sync_status(
    idempotency_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query status of a specific synchronization request by its idempotency key."""
    sync_entry = db.query(SyncQueue).filter(
        SyncQueue.idempotency_key == idempotency_key
    ).first()
    if not sync_entry:
        raise AppException(code="SYNC_NOT_FOUND", message="No sync request found with this key.", status_code=404)
        
    return {
        "idempotency_key": sync_entry.idempotency_key,
        "client_id": sync_entry.client_id,
        "status": sync_entry.status,
        "attempts": sync_entry.attempts,
        "inspection_id": sync_entry.inspection_id,
        "last_error": sync_entry.last_error,
        "created_at": sync_entry.created_at,
        "updated_at": sync_entry.updated_at
    }

@router.get("/queue")
def list_sync_queue(
    client_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List recent synchronization entries for inspection officers."""
    q = db.query(SyncQueue)
    if client_id:
        q = q.filter(SyncQueue.client_id == client_id)
    if status_filter:
        q = q.filter(SyncQueue.status == status_filter)
    entries = q.order_by(SyncQueue.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": e.id,
            "idempotency_key": e.idempotency_key,
            "client_id": e.client_id,
            "status": e.status,
            "attempts": e.attempts,
            "inspection_id": e.inspection_id,
            "last_error": e.last_error,
            "created_at": e.created_at,
            "updated_at": e.updated_at
        }
        for e in entries
    ]
