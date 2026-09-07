import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from PIL import Image as PILImage

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.ai.quality import assess_image_quality
from backend.app.cv.preprocessing import preprocess_label_image
from backend.app.ocr.engine import run_ocr_on_image
from backend.app.extraction.extractor import extract_declarations_from_ocr
from backend.app.rule_engine.engine import load_rules_from_db, load_all_rule_versions, run_compliance_evaluation
from backend.app.reports.generator import generate_collective_inspection_pdf, generate_inspection_pdf

router = APIRouter(prefix="/area-inspections", tags=["Inspection Area & Centers"])

SESSIONS_DIR: Path = settings.STORAGE_DIR / "area_sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store backed by JSON files
_sessions_cache: Dict[str, Dict[str, Any]] = {}

def _init_sessions_from_disk():
    global _sessions_cache
    if not SESSIONS_DIR.exists():
        return
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, dict) and "id" in data:
                    _sessions_cache[data["id"]] = data
        except Exception as e:
            logger.warning(f"Failed to load area session from {f.name}: {e}")

_init_sessions_from_disk()

def _save_session(session: Dict[str, Any]) -> None:
    session_id = session["id"]
    _sessions_cache[session_id] = session
    file_path = SESSIONS_DIR / f"{session_id}.json"
    with open(file_path, "w", encoding="utf-8") as fp:
        json.dump(session, fp, indent=2, default=str)


class CreateAreaSessionRequest(BaseModel):
    establishment_name: str = Field(..., description="Name of premise, retail mall, hub or market center")
    premise_type: str = Field("RETAIL_SUPERMARKET", description="Category of premise (e.g. RETAIL_SUPERMARKET, WHOLESALE_MANDI, WAREHOUSE_DEPOT, ECOMMERCE_FULFILLMENT)")
    address: str = Field("", description="Premise street address or location")
    district: Optional[str] = Field("Central District", description="Jurisdictional District")
    inspector_name: Optional[str] = Field("Authorized Legal Metrology Inspector", description="Officer Name")
    inspector_badge: Optional[str] = Field("DL-LM-001", description="Officer Badge Number")
    notes: Optional[str] = Field(None, description="Premise inspection remarks")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_area_session(req: CreateAreaSessionRequest):
    """
    Establishes an active premises audit session for an Inspection Center or Area.
    Allows field officers to audit multiple sampled packaged commodities at one location.
    """
    session_id = str(uuid.uuid4())
    year = datetime.now().year
    count = len(_sessions_cache) + 1
    session_number = f"AREA-{year}-{count:04d}"
    now_iso = datetime.now(timezone.utc).isoformat()

    session = {
        "id": session_id,
        "session_number": session_number,
        "establishment_name": req.establishment_name.strip(),
        "premise_type": req.premise_type,
        "address": req.address.strip() or "Jurisdiction Premise",
        "district": req.district or "Central District",
        "inspector_name": req.inspector_name or "Authorized Legal Metrology Inspector",
        "inspector_badge": req.inspector_badge or "DL-LM-001",
        "notes": req.notes or "",
        "created_at": now_iso,
        "inspection_date": datetime.now().strftime("%d-%b-%Y"),
        "status": "ACTIVE",
        "compliance_verdict": "PENDING",
        "total_items": 0,
        "compliant_items": 0,
        "violation_items": 0,
        "review_items": 0,
        "compliance_rate": 0.0,
        "items": [],
        "report": None
    }

    _save_session(session)
    logger.info(f"Created Area Inspection Session {session_number} for '{req.establishment_name}' (ID: {session_id})")
    return session


@router.get("")
def list_area_sessions():
    """Returns all area inspection sessions sorted by latest creation time."""
    sessions = list(_sessions_cache.values())
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


@router.get("/{session_id}")
def get_area_session(session_id: str):
    """Retrieves an area inspection session, its tray of sampled products, and metrics."""
    session = _sessions_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Area inspection session not found")
    return session


@router.post("/{session_id}/items", status_code=status.HTTP_201_CREATED)
async def add_product_item_to_area(
    session_id: str,
    commodity_name: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    mrp: Optional[str] = Form(None),
    net_quantity: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Rapid Product Shutter: Audits a sampled packaged commodity at the premise.
    Extracts label text via OCR, maps mandatory declarations under LMPC Rules 2011/2026,
    evaluates statutory rule compliance, and appends the item to the session tray.
    """
    session = _sessions_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Area inspection session not found")

    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Product image exceeds 25 MB limit")

    ext = os.path.splitext(file.filename or "product.jpg")[1].lower() or ".jpg"
    item_id = str(uuid.uuid4())
    stored_filename = f"area_{session_id[:8]}_{item_id[:8]}{ext}"
    storage_path = str(settings.UPLOAD_DIR / stored_filename)

    with open(storage_path, "wb") as fp:
        fp.write(contents)

    # Validate image decoding
    try:
        with PILImage.open(storage_path) as p_img:
            img_w, img_h = p_img.size
    except Exception:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        raise HTTPException(status_code=400, detail="Corrupted product photograph")

    # Assess Quality
    q_result = assess_image_quality(storage_path)

    # Non-destructive preprocessing
    proc_filename = f"proc_area_{item_id[:8]}.jpg"
    proc_path = str(settings.PROCESSED_DIR / proc_filename)
    try:
        preprocess_label_image(storage_path, proc_path)
        ocr_target_path = proc_path
    except Exception:
        ocr_target_path = storage_path

    # Execute PP-OCRv4
    ocr_result = run_ocr_on_image(ocr_target_path)
    lines = ocr_result.get("lines", [])
    full_text = ocr_result.get("full_text", "")

    # Extract Declarations
    declarations = extract_declarations_from_ocr(lines, source_image_id=item_id)

    # Automatically extract key fields if not manually provided
    detected_mrp = mrp
    detected_net_qty = net_quantity
    detected_brand = brand_name
    detected_commodity = commodity_name

    for decl in declarations:
        cat = decl.get("category")
        raw = decl.get("raw_text", "").strip()
        norm = decl.get("normalized_value")
        if cat == "MRP" and not detected_mrp:
            if isinstance(norm, dict) and "mrp" in norm:
                detected_mrp = f"₹{norm['mrp']}"
            else:
                detected_mrp = raw
        elif cat == "NET_QUANTITY" and not detected_net_qty:
            if isinstance(norm, dict) and "value" in norm:
                detected_net_qty = f"{norm['value']} {norm.get('unit', '')}".strip()
            else:
                detected_net_qty = raw
        elif cat == "MANUFACTURER" and not detected_brand:
            detected_brand = raw[:30]
        elif cat == "PRODUCT_NAME" and not detected_commodity:
            detected_commodity = raw[:50]

    # Fallbacks
    if not detected_commodity:
        # Check first line of OCR text as product hint
        first_line = lines[0]["text"] if lines else "Packaged Commodity"
        detected_commodity = first_line[:40]
    if not detected_brand:
        detected_brand = "Local / Commercial Pack"
    if not detected_mrp:
        detected_mrp = "Not Declared"
    if not detected_net_qty:
        detected_net_qty = "Not Specified"

    # Evaluate Rules
    try:
        rules = load_rules_from_db(db, target_version="LMPC-2026-RULES")
    except Exception:
        rules = []

    if not rules:
        all_versions = load_all_rule_versions()
        rules = all_versions.get("LMPC-2026-RULES", [])
        if not rules and all_versions:
            rules = next(iter(all_versions.values()))

    # Build evaluation context
    eval_context = {
        "is_food": any(kw in full_text.lower() for kw in ["food", "fssai", "edible", "snack", "flour", "spice", "milk", "tea"]),
        "is_imported": any(kw in full_text.lower() for kw in ["imported", "origin: china", "country of origin"]),
        "package_type": "SINGLE_PRE_PACKAGED",
        "commodity_category": "FOOD_BEVERAGE" if any(kw in full_text.lower() for kw in ["food", "fssai"]) else "GENERAL_COMMODITY",
        "declared_net_quantity": None,
        "declared_unit": None
    }

    findings, item_compliance, findings_summary = run_compliance_evaluation(
        rules=rules,
        declarations=declarations,
        context=eval_context,
        overall_image_quality=q_result.get("quality_score", 1.0),
        has_blurry_image=(q_result.get("blur_score", 100.0) < 65.0)
    )

    # Collect list of violations
    violations_list = []
    for f in findings:
        if f.get("final_status") == "FAIL":
            clause = f.get("clause_reference", "Rule")
            req = f.get("requirement_title", "Statutory requirement missing")
            violations_list.append(f"{clause} - {req}")

    item_record = {
        "id": item_id,
        "session_id": session_id,
        "item_index": len(session.get("items", [])) + 1,
        "commodity_name": detected_commodity,
        "brand_name": detected_brand,
        "mrp": detected_mrp,
        "net_quantity": detected_net_qty,
        "compliance_status": item_compliance,
        "violations_list": violations_list,
        "findings_summary": findings_summary,
        "declarations_count": len(declarations),
        "findings": findings,
        "declarations": declarations,
        "eval_context": eval_context,
        "image_path": storage_path,
        "image_url": f"/storage/uploads/{stored_filename}",
        "quality_score": q_result.get("quality_score", 1.0),
        "ocr_snippet": full_text[:180] if full_text else "No text detected",
        "report": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    session.setdefault("items", []).append(item_record)

    # Re-aggregate premise totals
    items = session["items"]
    total = len(items)
    compliant = sum(1 for i in items if i.get("compliance_status") == "COMPLIANT")
    violations = sum(1 for i in items if i.get("compliance_status") == "NON_COMPLIANT")
    reviews = sum(1 for i in items if i.get("compliance_status") == "REQUIRES_REVIEW")
    rate = round((compliant / total * 100.0), 1) if total > 0 else 0.0

    session["total_items"] = total
    session["compliant_items"] = compliant
    session["violation_items"] = violations
    session["review_items"] = reviews
    session["compliance_rate"] = rate
    session["compliance_verdict"] = (
        "NON_COMPLIANT" if violations > 0 else (
            "REQUIRES_REVIEW" if reviews > 0 else "COMPLIANT"
        )
    )

    _save_session(session)
    logger.info(f"Added product #{item_record['item_index']} '{detected_commodity}' ({item_compliance}) to session {session['session_number']}")

    return {
        "item": item_record,
        "session_summary": {
            "session_id": session_id,
            "session_number": session["session_number"],
            "total_items": total,
            "compliant_items": compliant,
            "violation_items": violations,
            "review_items": reviews,
            "compliance_rate": rate,
            "compliance_verdict": session["compliance_verdict"]
        }
    }


@router.delete("/{session_id}/items/{item_id}")
def delete_product_item(session_id: str, item_id: str):
    """Removes a sampled product from the session tray (e.g. accidental shutter)."""
    session = _sessions_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Area inspection session not found")

    items = session.get("items", [])
    orig_len = len(items)
    items = [i for i in items if i.get("id") != item_id]

    if len(items) == orig_len:
        raise HTTPException(status_code=404, detail="Item not found in session")

    # Re-index remaining items
    for idx, item in enumerate(items, 1):
        item["item_index"] = idx

    session["items"] = items
    total = len(items)
    compliant = sum(1 for i in items if i.get("compliance_status") == "COMPLIANT")
    violations = sum(1 for i in items if i.get("compliance_status") == "NON_COMPLIANT")
    reviews = sum(1 for i in items if i.get("compliance_status") == "REQUIRES_REVIEW")
    rate = round((compliant / total * 100.0), 1) if total > 0 else 0.0

    session["total_items"] = total
    session["compliant_items"] = compliant
    session["violation_items"] = violations
    session["review_items"] = reviews
    session["compliance_rate"] = rate
    session["compliance_verdict"] = (
        "NON_COMPLIANT" if violations > 0 else (
            "REQUIRES_REVIEW" if reviews > 0 else ("PENDING" if total == 0 else "COMPLIANT")
        )
    )

    _save_session(session)
    return {"message": "Product item removed", "total_remaining": total}


@router.post("/{session_id}/collective-report")
def create_collective_report(session_id: str):
    """
    Compiles and cryptographically seals an Official Consolidated Statutory Inspection Report (PDF)
    covering all sampled commodities at the premise or center under Legal Metrology Rules 2011/2026.
    """
    session = _sessions_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Area inspection session not found")

    items = session.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="Cannot generate collective report without at least one sampled product")

    report_result = generate_collective_inspection_pdf(
        area_session=session,
        items=items,
        output_filename=f"collective_report_{session_id}.pdf"
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    session["report"] = {
        "certificate_number": report_result["certificate_number"],
        "pdf_url": report_result["pdf_url"],
        "pdf_sha256": report_result["pdf_sha256"],
        "pdf_filename": report_result["pdf_filename"],
        "generated_at": now_iso
    }
    session["status"] = "FINALIZED"
    _save_session(session)

    logger.info(f"Generated collective report {report_result['certificate_number']} for session {session['session_number']}")
    return session["report"]


@router.post("/{session_id}/items/{item_id}/report")
def create_individual_item_report(session_id: str, item_id: str):
    """
    Generates an Individual Statutory Compliance Inspection Certificate (PDF)
    for a specific sampled commodity from an area session.
    """
    session = _sessions_cache.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Area inspection session not found")

    items = session.get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in session")

    insp_data = {
        "id": item["id"],
        "inspection_number": f"{session['session_number']}-ITM{item['item_index']:02d}",
        "commodity_name": item["commodity_name"],
        "brand_name": item["brand_name"],
        "status": "FINALIZED",
        "compliance_status": item["compliance_status"],
        "rule_version": "LMPC-2026-RULES",
        "inspector_name": session.get("inspector_name", "Authorized Legal Metrology Inspector"),
        "notes": f"Sampled at premise: {session.get('establishment_name')}"
    }

    images_data = [{
        "view_type": "FRONT_PANEL",
        "original_filename": os.path.basename(item.get("image_path", "image.jpg")),
        "storage_path": item.get("image_path", ""),
        "sha256_hash": hashlib.sha256(item.get("id", "").encode()).hexdigest(),
        "is_acceptable": True,
        "quality_assessment": {"quality_score": item.get("quality_score", 1.0), "warnings": []}
    }]

    output_filename = f"report_{session_id[:8]}_{item_id[:8]}.pdf"
    report_res = generate_inspection_pdf(
        inspection_data=insp_data,
        findings=item.get("findings", []),
        declarations=item.get("declarations", []),
        product_context=item.get("eval_context", {}),
        images_data=images_data,
        output_filename=output_filename
    )

    item["report"] = {
        "certificate_number": report_res["certificate_number"],
        "pdf_url": report_res["pdf_url"],
        "pdf_sha256": report_res["pdf_sha256"],
        "pdf_filename": report_res["pdf_filename"],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    _save_session(session)
    logger.info(f"Generated individual report {report_res['certificate_number']} for item #{item['item_index']} in session {session['session_number']}")
    return item["report"]
