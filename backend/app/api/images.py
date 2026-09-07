import os
import uuid
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from PIL import Image as PILImage
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, InspectionImage, User, AuditLog
from backend.app.schemas import ImageResponse
from backend.app.api.deps import get_current_user, require_role
from backend.app.ai.quality import assess_image_quality
from backend.app.cv.preprocessing import preprocess_label_image

router = APIRouter(tags=["Images"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

@router.post("/inspections/{id}/images", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_inspection_image(
    id: str,
    view_type: str = Form("FRONT"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise AppException(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"File type {file.content_type} is not supported. Please upload JPEG, PNG, or WebP images.",
            status_code=400
        )
        
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        raise AppException(
            code="FILE_TOO_LARGE",
            message=f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum permitted limit of 25 MB.",
            status_code=400
        )
        
    # Cryptographic SHA-256 Hash
    sha256_hash = hashlib.sha256(contents).hexdigest()
    
    # Secure storage filename
    ext = os.path.splitext(file.filename or "image.jpg")[1].lower() or ".jpg"
    image_id = str(uuid.uuid4())
    stored_filename = f"{image_id}{ext}"
    storage_path = str(settings.UPLOAD_DIR / stored_filename)
    
    with open(storage_path, "wb") as f:
        f.write(contents)
        
    # Read dimensions safely with Pillow
    try:
        with PILImage.open(storage_path) as p_img:
            width, height = p_img.size
    except Exception:
        os.remove(storage_path)
        raise AppException(
            code="CORRUPT_IMAGE",
            message="Uploaded image could not be decoded. File may be corrupt.",
            status_code=400
        )
        
    # Image Quality Assessment
    quality_result = assess_image_quality(storage_path)
    
    # Preprocessing (Non-destructive)
    proc_filename = f"proc_{image_id}.jpg"
    proc_path = str(settings.PROCESSED_DIR / proc_filename)
    try:
        preprocess_label_image(storage_path, proc_path)
    except Exception as e:
        print(f"Non-fatal preprocessing warning: {e}")
        proc_path = storage_path
        
    # Create DB Record
    image_record = InspectionImage(
        id=image_id,
        inspection_id=insp.id,
        view_type=view_type.upper(),
        original_filename=file.filename or stored_filename,
        storage_path=storage_path,
        processed_path=proc_path,
        sha256_hash=sha256_hash,
        width=width,
        height=height,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        quality_assessment=quality_result,
        is_acceptable=quality_result.get("is_acceptable", True)
    )
    db.add(image_record)
    
    # Transition inspection status if it was DRAFT
    if insp.status == "DRAFT":
        insp.status = "CAPTURED"
        
    db.add(AuditLog(
        inspection_id=insp.id,
        user_id=current_user.id,
        action="UPLOAD_IMAGE",
        entity_type="IMAGE",
        entity_id=image_id,
        new_state={"sha256": sha256_hash, "view_type": view_type, "quality_score": quality_result.get("quality_score")}
    ))
    db.commit()
    db.refresh(image_record)
    
    return ImageResponse(
        id=image_record.id,
        inspection_id=image_record.inspection_id,
        view_type=image_record.view_type,
        original_filename=image_record.original_filename,
        storage_path=f"/storage/uploads/{stored_filename}",
        processed_path=f"/storage/processed/{proc_filename}" if proc_path != storage_path else f"/storage/uploads/{stored_filename}",
        sha256_hash=image_record.sha256_hash,
        width=image_record.width,
        height=image_record.height,
        file_size_bytes=image_record.file_size_bytes,
        mime_type=image_record.mime_type,
        quality_assessment=image_record.quality_assessment,
        is_acceptable=image_record.is_acceptable,
        created_at=image_record.created_at
    )

@router.get("/images", response_model=List[ImageResponse])
def list_images(
    view_type: Optional[str] = Query(None),
    is_acceptable: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InspectionImage)
    if view_type:
        query = query.filter(InspectionImage.view_type == view_type.upper())
    if is_acceptable is not None:
        query = query.filter(InspectionImage.is_acceptable == is_acceptable)
        
    images = query.order_by(InspectionImage.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for img in images:
        fname = os.path.basename(img.storage_path)
        pfname = os.path.basename(img.processed_path) if img.processed_path else fname
        results.append(ImageResponse(
            id=img.id,
            inspection_id=img.inspection_id,
            view_type=img.view_type,
            original_filename=img.original_filename,
            storage_path=f"/storage/uploads/{fname}",
            processed_path=f"/storage/processed/{pfname}",
            sha256_hash=img.sha256_hash,
            width=img.width,
            height=img.height,
            file_size_bytes=img.file_size_bytes,
            mime_type=img.mime_type,
            quality_assessment=img.quality_assessment,
            is_acceptable=img.is_acceptable,
            created_at=img.created_at
        ))
    return results

@router.get("/images/{id}", response_model=ImageResponse)
def get_image_details(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    img = db.query(InspectionImage).filter(InspectionImage.id == id).first()
    if not img:
        raise AppException(code="IMAGE_NOT_FOUND", message="Image not found.", status_code=404)
        
    fname = os.path.basename(img.storage_path)
    pfname = os.path.basename(img.processed_path) if img.processed_path else fname
    return ImageResponse(
        id=img.id,
        inspection_id=img.inspection_id,
        view_type=img.view_type,
        original_filename=img.original_filename,
        storage_path=f"/storage/uploads/{fname}",
        processed_path=f"/storage/processed/{pfname}",
        sha256_hash=img.sha256_hash,
        width=img.width,
        height=img.height,
        file_size_bytes=img.file_size_bytes,
        mime_type=img.mime_type,
        quality_assessment=img.quality_assessment,
        is_acceptable=img.is_acceptable,
        created_at=img.created_at
    )

@router.delete("/images/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    img = db.query(InspectionImage).filter(InspectionImage.id == id).first()
    if not img:
        raise AppException(code="IMAGE_NOT_FOUND", message="Image not found.", status_code=404)
        
    if os.path.exists(img.storage_path):
        try:
            os.remove(img.storage_path)
        except Exception:
            pass
    if img.processed_path and os.path.exists(img.processed_path):
        try:
            os.remove(img.processed_path)
        except Exception:
            pass
            
    db.delete(img)
    db.commit()
    return None
