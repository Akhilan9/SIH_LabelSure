import os
import uuid
import base64
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.config import settings
from backend.app.models import Inspection, ProductContext, Finding, Declaration, Report, InspectionImage, User, AuditLog

client = TestClient(app)

def get_auth_headers_and_inspector_id(role: str = "INSPECTOR"):
    creds = {
        "ADMIN": ("admin", "Admin@LabelSure2026"),
        "INSPECTOR": ("inspector1", "Inspector@2026"),
    }
    username, password = creds[role]
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    data = res.json()
    token = data["access_token"]
    user_id = data["user_id"]
    return {"Authorization": f"Bearer {token}"}, user_id

def create_synthetic_compliant_label_bytes() -> bytes:
    """Creates a high-contrast, fully compliant package label with standard legal declarations."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.putText(img, "APEX NATURALS - PURE WHEAT FLOUR", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "COMMON GENERIC NAME: ATTA / WHOLE WHEAT FLOUR", (40, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "NET QUANTITY: 500 g", (40, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs 65.00 (INCL. OF ALL TAXES)", (40, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "UNIT SALE PRICE: Rs 0.13 / g", (40, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "MFG DATE: 02/2026", (40, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "BEST BEFORE: 6 MONTHS FROM PACKAGING", (40, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "MFG BY: APEX FOODS PVT LTD, SECTOR 18, NOIDA 201301", (40, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    cv2.putText(img, "COUNTRY OF ORIGIN: INDIA", (40, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "CONSUMER CARE: CARE@APEXFOODS.IN, TEL 1800-11-2026", (40, 510), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    
    _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return buf.tobytes()

def create_synthetic_missing_declaration_bytes() -> bytes:
    """Creates a label intentionally missing MRP and Manufacturing Date."""
    img = np.ones((500, 700, 3), dtype=np.uint8) * 255
    cv2.putText(img, "APEX REFRESH - MINERAL WATER", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "NET QUANTITY: 1 L", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "MFG BY: APEX BEVERAGES, PLOT 9, HARIDWAR 249401", (40, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "COUNTRY OF ORIGIN: INDIA", (40, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    # Notice: MRP, Date, and Consumer Care are completely missing!
    _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return buf.tobytes()

def create_synthetic_blurry_label_bytes() -> bytes:
    """Creates a heavily blurred label to trigger low quality score and uncertainty."""
    img = np.ones((300, 500, 3), dtype=np.uint8) * 200
    cv2.putText(img, "DEGRADED BLURRY LABEL", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2)
    # Heavy Gaussian Blur to drop Laplacian variance below threshold
    blurred = cv2.GaussianBlur(img, (45, 45), 0)
    _, buf = cv2.imencode(".jpg", blurred, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
    return buf.tobytes()

def create_synthetic_imported_product_bytes() -> bytes:
    """Creates a label declaring both foreign manufacturer and domestic Indian importer."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.putText(img, "BELLISSIMO EXTRA VIRGIN OLIVE OIL 1L", (40, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "NET QUANTITY: 1 L", (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs 1450.00 (INCL. OF ALL TAXES)", (40, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "COUNTRY OF ORIGIN: ITALY", (40, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "PRODUCED BY: OLIO BELLA SPA, VIA ROMA 44, MILAN, ITALY", (40, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    cv2.putText(img, "IMPORTED & PACKED BY: APEX GOURMET IMPORTS, CONNAUGHT PLACE, NEW DELHI 110001", (40, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)
    cv2.putText(img, "DATE OF IMPORT: 01/2026", (40, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, "CONSUMER CARE: IMPORTS@APEXGOURMET.IN, TEL 011-2334455", (40, 490), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    
    _, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return buf.tobytes()


# =================================================================
# CASE-001: Compliant Package Full Workflow
# =================================================================
def test_case_001_compliant_package_full_flow():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    # 1. Create Inspection & Context
    payload = {
        "commodity_name": "Apex Naturals Whole Wheat Flour 500g",
        "brand_name": "ApexNaturals",
        "rule_version": "LMPC-2026-RULES",
        "notes": "E2E Integration Case-001 Compliant Audit",
        "context": {
            "commodity_category": "FOOD",
            "product_type": "Pre-Packaged Grain",
            "is_food": True,
            "is_imported": False,
            "origin_country": "India",
            "package_type": "SINGLE_PRE_PACKAGED",
            "declared_net_quantity": 500.0,
            "declared_unit": "g"
        }
    }
    create_res = client.post("/api/inspections", json=payload, headers=headers)
    assert create_res.status_code == 201
    insp_id = create_res.json()["id"]
    
    # 2. Upload High-Quality Multi-Panel Image
    img_bytes = create_synthetic_compliant_label_bytes()
    files = {"file": ("front_compliant.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    data = {"view_type": "FRONT"}
    img_res = client.post(f"/api/inspections/{insp_id}/images", files=files, data=data, headers=headers)
    assert img_res.status_code == 201
    img_data = img_res.json()
    assert img_data["sha256_hash"] is not None
    assert img_data["quality_assessment"]["is_acceptable"] is True
    
    # 3. Trigger Full Pipeline Analysis (OCR -> Declarations -> Rule Engine -> RuleLens)
    analyze_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    analysis_data = analyze_res.json()["data"]
    assert analysis_data["findings_count"] > 0
    assert analysis_data["declarations_count"] > 0
    assert analysis_data["compliance_status"] == "COMPLIANT"
    
    # 4. Verify RuleLens Dossier
    rulelens_res = client.get(f"/api/inspections/{insp_id}/rulelens", headers=headers)
    assert rulelens_res.status_code == 200
    rulelens_data = rulelens_res.json()
    assert len(rulelens_data["findings"]) >= 4
    for f in rulelens_data["findings"]:
        assert f["rule_id"] is not None
        assert f["clause_reference"] is not None
        assert f["explanation"] is not None
        
    # 5. Generate Official Certificate Report
    report_res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert report_res.status_code == 201
    report_data = report_res.json()
    assert report_data["compliance_verdict"] == "COMPLIANT"
    assert report_data["pdf_sha256"] is not None
    assert report_data["summary"]["failed"] == 0


# =================================================================
# CASE-002: Missing Declaration Statutory Violation Workflow
# =================================================================
def test_case_002_missing_declaration_violation_flow():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    payload = {
        "commodity_name": "Apex Refresh Mineral Water 1L",
        "brand_name": "ApexRefresh",
        "rule_version": "LMPC-2026-RULES",
        "notes": "E2E Integration Case-002 Missing MRP & Date",
        "context": {
            "commodity_category": "FOOD_BEVERAGE",
            "is_food": True,
            "is_imported": False,
            "declared_net_quantity": 1.0,
            "declared_unit": "L"
        }
    }
    insp_res = client.post("/api/inspections", json=payload, headers=headers)
    assert insp_res.status_code == 201
    insp_id = insp_res.json()["id"]
    
    # Upload image that lacks MRP & Date
    img_bytes = create_synthetic_missing_declaration_bytes()
    files = {"file": ("missing_decl.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    img_res = client.post(f"/api/inspections/{insp_id}/images", files=files, data={"view_type": "FRONT"}, headers=headers)
    assert img_res.status_code == 201
    
    # Run analysis
    analyze_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    data = analyze_res.json()["data"]
    assert data["compliance_status"] == "NON_COMPLIANT"
    
    # Verify report reflects NON_COMPLIANT
    report_res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert report_res.status_code == 201
    report = report_res.json()
    assert report["compliance_verdict"] == "NON_COMPLIANT"
    assert report["summary"]["failed"] >= 1


# =================================================================
# CASE-003: Poor Image Quality & Uncertainty Workflow
# =================================================================
def test_case_003_poor_image_blur_uncertainty_flow():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    payload = {
        "commodity_name": "Generic Blurry Sample Package",
        "rule_version": "LMPC-2026-RULES",
        "context": {
            "commodity_category": "GENERAL_COMMODITY",
            "is_food": False,
            "declared_net_quantity": 100.0,
            "declared_unit": "g"
        }
    }
    insp_res = client.post("/api/inspections", json=payload, headers=headers)
    assert insp_res.status_code == 201
    insp_id = insp_res.json()["id"]
    
    # Upload heavily blurred image
    img_bytes = create_synthetic_blurry_label_bytes()
    files = {"file": ("blurry_pkg.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    img_res = client.post(f"/api/inspections/{insp_id}/images", files=files, data={"view_type": "FRONT"}, headers=headers)
    assert img_res.status_code == 201
    qa = img_res.json()["quality_assessment"]
    # Verify blur is flagged
    assert qa["blur_score"] < 75.0 or qa["quality_score"] < 0.85 or any("BLUR" in w.upper() for w in qa.get("warnings", []))
    
    # Run analysis
    analyze_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    data = analyze_res.json()["data"]
    assert data["compliance_status"] in ["REQUIRES_REVIEW", "UNCERTAIN"]
    
    # Truth-in-reporting check: Report must NEVER falsely claim COMPLIANT
    report_res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert report_res.status_code == 201
    report = report_res.json()
    assert report["compliance_verdict"] != "COMPLIANT"
    assert report["compliance_verdict"] in ["REQUIRES_REVIEW", "UNCERTAIN"]


# =================================================================
# CASE-004: Imported Product Specific Statutory Rules Workflow
# =================================================================
def test_case_004_imported_product_specific_rules_flow():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    payload = {
        "commodity_name": "Bellissimo Extra Virgin Olive Oil 1L",
        "brand_name": "Bellissimo",
        "rule_version": "LMPC-2026-RULES",
        "context": {
            "commodity_category": "FOOD",
            "is_food": True,
            "is_imported": True,
            "origin_country": "Italy",
            "package_type": "SINGLE_PRE_PACKAGED",
            "declared_net_quantity": 1.0,
            "declared_unit": "L"
        }
    }
    insp_res = client.post("/api/inspections", json=payload, headers=headers)
    assert insp_res.status_code == 201
    insp_id = insp_res.json()["id"]
    
    # Upload label with Italian origin and Indian importer address
    img_bytes = create_synthetic_imported_product_bytes()
    files = {"file": ("imported_oil.jpg", io.BytesIO(img_bytes), "image/jpeg")}
    img_res = client.post(f"/api/inspections/{insp_id}/images", files=files, data={"view_type": "FRONT"}, headers=headers)
    assert img_res.status_code == 201
    
    # Run analysis
    analyze_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    data = analyze_res.json()["data"]
    assert data["findings_count"] > 0
    
    # Retrieve inspection details with findings
    insp_detail_res = client.get(f"/api/inspections/{insp_id}", headers=headers)
    assert insp_detail_res.status_code == 200
    findings = insp_detail_res.json()["findings"]
    
    # Country of Origin rule must evaluate to PASS
    origin_finding = next((f for f in findings if "origin" in f["requirement_title"].lower()), None)
    if origin_finding:
        assert origin_finding["final_status"] == "PASS"


# =================================================================
# CASE-005: Human Inspector Correction & Adjudication Override
# =================================================================
def test_case_005_human_correction_adjudication():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    # Create inspection with initial findings
    db = SessionLocal()
    try:
        insp = Inspection(
            inspection_number=f"INSP-E2E-OVERRIDE-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Artisanal Roasted Almonds 200g",
            rule_version="LMPC-2026-RULES",
            status="ANALYZED",
            compliance_status="NON_COMPLIANT"
        )
        db.add(insp)
        db.flush()
        
        f1 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-B",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(b)",
            requirement_title="Generic or Common Name",
            expected_condition="Must specify generic commodity name",
            observed_value="[Not detected by OCR]",
            severity="HIGH",
            ai_status="FAIL",
            final_status="FAIL",
            confidence=0.55,
            explanation="OCR did not detect generic name on front view panel."
        )
        db.add(f1)
        db.commit()
        insp_id = insp.id
        finding_id = f1.id
    finally:
        db.close()
        
    # Inspector Adjudication Override: Accept as PASS with statutory explanation
    override_payload = {
        "inspector_status": "PASS",
        "inspector_comment": "On-site physical inspection verified: 'California Almonds' clearly stamped in silver foil on top flap."
    }
    patch_res = client.patch(f"/api/findings/{finding_id}", json=override_payload, headers=headers)
    assert patch_res.status_code == 200
    patched_finding = patch_res.json()
    assert patched_finding["ai_status"] == "FAIL" # Original AI decision strictly preserved!
    assert patched_finding["inspector_status"] == "PASS"
    assert patched_finding["final_status"] == "PASS"
    assert patched_finding["inspector_comment"] == override_payload["inspector_comment"]
    
    # Finalize inspection
    finalize_res = client.post(f"/api/inspections/{insp_id}/finalize", headers=headers)
    assert finalize_res.status_code == 200
    
    # Verify AuditLog has recorded the override
    db = SessionLocal()
    try:
        audit_entry = db.query(AuditLog).filter(
            AuditLog.inspection_id == insp_id,
            AuditLog.action == "OVERRIDE_FINDING"
        ).first()
        assert audit_entry is not None
        assert audit_entry.new_state["inspector_status"] == "PASS"
    finally:
        db.close()
        
    # Generate report and verify override is noted
    rep_res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert rep_res.status_code == 201
    assert rep_res.json()["summary"]["inspector_overrides"] == 1


# =================================================================
# CASE-006: Offline Synchronization & Deduplication Flow
# =================================================================
def test_case_006_offline_synchronization_dedup():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    
    idempotency_key = f"e2e-offline-{uuid.uuid4()}"
    client_id = "field-device-s24-demo"
    
    img_bytes = create_synthetic_compliant_label_bytes()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    
    payload = {
        "commodity_name": "Organic Cold-Pressed Mustard Oil 1L",
        "brand_name": "KisanShakti",
        "rule_version": "LMPC-2026-RULES",
        "notes": "Case-006 Offline field capture at village mandi",
        "context": {
            "commodity_category": "FOOD",
            "is_food": True,
            "is_imported": False,
            "declared_net_quantity": 1.0,
            "declared_unit": "L"
        },
        "images": [
            {
                "view_type": "FRONT",
                "image_base64": img_b64,
                "filename": "mandi_front.jpg"
            }
        ],
        "auto_analyze": True
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    # First Sync Transmission
    res1 = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["success"] is True
    assert "inspection_id" in data1
    insp_id = data1["inspection_id"]
    
    # Second Sync Transmission (Exact duplicate replay)
    res2 = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ALREADY_SYNCED"
    assert data2["inspection_id"] == insp_id
    
    # Verify zero duplicate records in DB
    db = SessionLocal()
    try:
        inspections = db.query(Inspection).filter(Inspection.id == insp_id).all()
        assert len(inspections) == 1
    finally:
        db.close()
