from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Declaration, Inspection, User, AuditLog
from backend.app.schemas import DeclarationResponse, DeclarationCreate, DeclarationUpdate
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(tags=["Declarations"])

@router.get("/inspections/{id}/declarations", response_model=List[DeclarationResponse])
def get_inspection_declarations(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    decls = db.query(Declaration).filter(Declaration.inspection_id == id).all()
    return decls

@router.post("/inspections/{id}/declarations", response_model=DeclarationResponse, status_code=status.HTTP_201_CREATED)
def add_manual_declaration(
    id: str,
    decl_in: DeclarationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    decl = Declaration(
        inspection_id=id,
        source_image_id=decl_in.source_image_id,
        category=decl_in.category,
        raw_text=decl_in.raw_text,
        normalized_value=decl_in.normalized_value or {"value": decl_in.raw_text},
        unit=decl_in.unit,
        confidence=1.0,
        bbox=decl_in.bbox,
        extraction_method="MANUAL_ENTRY",
        is_inspector_edited=True
    )
    db.add(decl)
    db.add(AuditLog(
        inspection_id=id,
        user_id=current_user.id,
        action="ADD_DECLARATION",
        entity_type="DECLARATION",
        entity_id=decl.id,
        new_state={"category": decl.category, "raw_text": decl.raw_text}
    ))
    db.commit()
    db.refresh(decl)
    return decl

@router.patch("/declarations/{id}", response_model=DeclarationResponse)
def update_declaration(
    id: str,
    decl_up: DeclarationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    decl = db.query(Declaration).filter(Declaration.id == id).first()
    if not decl:
        raise AppException(code="DECLARATION_NOT_FOUND", message="Declaration not found.", status_code=404)
        
    prev_text = decl.raw_text
    if not decl.is_inspector_edited:
        decl.original_ai_value = prev_text
        decl.is_inspector_edited = True
        
    if decl_up.category is not None:
        decl.category = decl_up.category
    if decl_up.raw_text is not None:
        decl.raw_text = decl_up.raw_text
    if decl_up.normalized_value is not None:
        decl.normalized_value = decl_up.normalized_value
    if decl_up.unit is not None:
        decl.unit = decl_up.unit
    if decl_up.bbox is not None:
        decl.bbox = decl_up.bbox
        
    db.add(AuditLog(
        inspection_id=decl.inspection_id,
        user_id=current_user.id,
        action="EDIT_DECLARATION",
        entity_type="DECLARATION",
        entity_id=decl.id,
        previous_state={"raw_text": prev_text},
        new_state={"raw_text": decl.raw_text, "category": decl.category}
    ))
    db.commit()
    db.refresh(decl)
    return decl
