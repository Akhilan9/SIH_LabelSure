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
from backend.app.models import Inspection, ProductContext, Finding, Declaration, Report, InspectionImage, User

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

# -----------------------------------------------------------------
# 1. Test PDF Report Generation: Compliant Inspection
# -----------------------------------------------------------------
def test_generate_report_compliant_inspection():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    db = SessionLocal()
    try:
        # Create Compliant Inspection
        insp = Inspection(
            inspection_number=f"INSP-COMPLIANT-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Fortified Wheat Flour 5kg",
            brand_name="AnnapurnaPure",
            rule_version="LMPC-2026-RULES",
            status="FINALIZED",
            compliance_status="COMPLIANT"
        )
        db.add(insp)
        db.flush()
        
        ctx = ProductContext(
            inspection_id=insp.id,
            commodity_category="FOOD",
            product_type="Pre-Packaged Grain",
            is_food=True,
            is_imported=False,
            origin_country="India",
            declared_net_quantity=5.0,
            declared_unit="kg"
        )
        db.add(ctx)
        
        # Add Passing Findings
        f1 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-A",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(a)",
            requirement_title="Manufacturer Name and Complete Address",
            expected_condition="Must specify complete physical address with PIN code",
            observed_value="Annapurna Mills Pvt Ltd, Sector 62, Noida 201301",
            severity="CRITICAL",
            ai_status="PASS",
            final_status="PASS",
            confidence=0.96,
            explanation="Manufacturer declaration is fully compliant with complete address and PIN."
        )
        f2 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-E",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(e)",
            requirement_title="Maximum Retail Price (MRP)",
            expected_condition="Inclusive of all taxes",
            observed_value="MRP Rs 240.00 (INCL. OF ALL TAXES)",
            severity="CRITICAL",
            ai_status="PASS",
            final_status="PASS",
            confidence=0.98,
            explanation="Statutory MRP declaration is present with tax inclusion statement."
        )
        db.add_all([f1, f2])
        
        # Add Declarations with required bbox
        d1 = Declaration(
            inspection_id=insp.id,
            category="MANUFACTURER",
            raw_text="Annapurna Mills Pvt Ltd, Sector 62, Noida 201301",
            normalized_value="Annapurna Mills Pvt Ltd",
            confidence=0.96,
            bbox=[0.1, 0.1, 0.2, 0.8],
            extraction_method="OCR+Regex"
        )
        d2 = Declaration(
            inspection_id=insp.id,
            category="MRP",
            raw_text="MRP Rs 240.00 (INCL. OF ALL TAXES)",
            normalized_value="240.00 INR",
            confidence=0.98,
            bbox=[0.7, 0.1, 0.8, 0.5],
            extraction_method="OCR+Regex"
        )
        db.add_all([d1, d2])
        db.commit()
        insp_id = insp.id
    finally:
        db.close()

    # Generate Report via API
    res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["compliance_verdict"] == "COMPLIANT"
    assert data["certificate_number"].startswith("LMPC-CERT-")
    assert data["pdf_sha256"] is not None
    assert len(data["pdf_sha256"]) == 64
    assert data["summary"]["passed"] == 2
    assert data["summary"]["failed"] == 0
    assert data["summary"]["uncertain"] == 0

    # Verify PDF file existence on disk
    pdf_filename = data["pdf_url"].replace("/storage/reports/", "")
    from backend.app.core.config import settings
    disk_path = settings.REPORTS_DIR / pdf_filename
    assert disk_path.exists()
    assert disk_path.stat().st_size > 1000

# -----------------------------------------------------------------
# 2. Test PDF Report Generation: Non-Compliant Inspection
# -----------------------------------------------------------------
def test_generate_report_non_compliant_inspection():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    db = SessionLocal()
    try:
        insp = Inspection(
            inspection_number=f"INSP-FAIL-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Instant Energy Drink 250ml",
            brand_name="TurboVolt",
            rule_version="LMPC-2026-RULES",
            status="FINALIZED",
            compliance_status="NON_COMPLIANT"
        )
        db.add(insp)
        db.flush()
        
        f1 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-E",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(e)",
            requirement_title="Maximum Retail Price (MRP)",
            expected_condition="Must state inclusive of all taxes",
            observed_value="MRP Rs 60 (PLUS TAXES EXTRA)",
            severity="CRITICAL",
            ai_status="FAIL",
            final_status="FAIL",
            confidence=0.94,
            explanation="Unlawful MRP declaration: charging extra taxes is prohibited under LMPC Rule 6(1)(e)."
        )
        f2 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-C",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(c)",
            requirement_title="Country of Origin",
            expected_condition="Mandatory for all packaged goods",
            observed_value=None,
            severity="CRITICAL",
            ai_status="FAIL",
            final_status="FAIL",
            confidence=0.91,
            explanation="Country of origin declaration is entirely missing from all packaging panels."
        )
        db.add_all([f1, f2])
        db.commit()
        insp_id = insp.id
    finally:
        db.close()

    res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["compliance_verdict"] == "NON_COMPLIANT"
    assert data["summary"]["failed"] == 2
    assert data["summary"]["critical_violations"] == 2

# -----------------------------------------------------------------
# 3. CRITICAL: Uncertain Inspection Truth-in-Reporting Check
# -----------------------------------------------------------------
def test_generate_report_uncertain_inspection_truth_check():
    """
    CRITICAL STATUTORY REQUIREMENT:
    Do not generate a report that falsely says an uncertain inspection is compliant/non-compliant.
    If any finding is UNCERTAIN, the report MUST state REQUIRES_REVIEW or UNCERTAIN.
    """
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    db = SessionLocal()
    try:
        # Even if someone erroneously sets compliance_status to COMPLIANT on an inspection with uncertain findings
        insp = Inspection(
            inspection_number=f"INSP-UNCERTAIN-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Ayurvedic Cough Syrup 100ml",
            brand_name="VedikaCare",
            rule_version="LMPC-2026-RULES",
            status="REVIEW_REQUIRED",
            compliance_status="COMPLIANT" # Erroneous status that must be caught by truth-in-reporting
        )
        db.add(insp)
        db.flush()
        
        f1 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-D",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(d)",
            requirement_title="Date of Manufacture / Packaging",
            expected_condition="Clear month and year declaration",
            observed_value="[Occluded / Blurry text]",
            severity="CRITICAL",
            ai_status="UNCERTAIN",
            final_status="UNCERTAIN",
            confidence=0.42,
            explanation="Image blur prevents definitive OCR extraction of manufacturing date panel."
        )
        db.add(f1)
        db.commit()
        insp_id = insp.id
    finally:
        db.close()

    res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert res.status_code == 201
    data = res.json()
    
    # Assert report STRICTLY refrains from falsely claiming COMPLIANT!
    assert data["compliance_verdict"] != "COMPLIANT"
    assert data["compliance_verdict"] in ["REQUIRES_REVIEW", "UNCERTAIN"]
    assert data["summary"]["uncertain"] >= 1

    # Verify the generated PDF exists on disk with valid sha256
    from backend.app.core.config import settings
    pdf_filename = data["pdf_url"].replace("/storage/reports/", "")
    disk_path = settings.REPORTS_DIR / pdf_filename
    assert disk_path.exists()
    assert disk_path.stat().st_size > 1000
    assert len(data["pdf_sha256"]) == 64

# -----------------------------------------------------------------
# 4. Test PDF Report Generation with Inspector Review / Overrides
# -----------------------------------------------------------------
def test_generate_report_with_inspector_overrides():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    db = SessionLocal()
    try:
        insp = Inspection(
            inspection_number=f"INSP-OVERRIDE-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Organic Green Tea 25 Bags",
            brand_name="HimalayanHerbs",
            rule_version="LMPC-2026-RULES",
            status="FINALIZED",
            compliance_status="COMPLIANT"
        )
        db.add(insp)
        db.flush()
        
        f1 = Finding(
            inspection_id=insp.id,
            rule_id="RULE-6-1-B",
            rule_version="LMPC-2026-RULES",
            clause_reference="Rule 6(1)(b)",
            requirement_title="Generic or Common Name",
            expected_condition="Must state generic commodity name prominently",
            observed_value="GREEN TEA",
            severity="HIGH",
            ai_status="FAIL", # Original AI Decision was FAIL
            inspector_status="PASS", # Human Inspector Adjudication OVERRIDE
            final_status="PASS",
            inspector_comment="Physical container inspected on-site: 'Green Tea' clearly embossed on bottom foil panel.",
            confidence=0.65,
            explanation="AI could not detect generic name on front panel; verified by inspector on secondary panel."
        )
        db.add(f1)
        db.commit()
        insp_id = insp.id
    finally:
        db.close()

    res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["summary"]["inspector_overrides"] == 1
    assert data["summary"]["passed"] == 1

    # Verify generated PDF file
    from backend.app.core.config import settings
    pdf_filename = data["pdf_url"].replace("/storage/reports/", "")
    disk_path = settings.REPORTS_DIR / pdf_filename
    assert disk_path.exists()
    assert disk_path.stat().st_size > 1000

# -----------------------------------------------------------------
# 5. Test PDF Report Generation with Photographic Evidence
# -----------------------------------------------------------------
def test_generate_report_with_submitted_packaging_images():
    headers, inspector_id = get_auth_headers_and_inspector_id("INSPECTOR")
    from backend.app.core.config import settings
    
    # Create synthetic test image file on disk
    img_name = f"test_panel_{uuid.uuid4().hex[:6]}.jpg"
    img_path = str(settings.UPLOAD_DIR / img_name)
    dummy_img = np.ones((300, 400, 3), dtype=np.uint8) * 240
    cv2.putText(dummy_img, "EVIDENCE PANEL", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2)
    cv2.imwrite(img_path, dummy_img)
    
    db = SessionLocal()
    try:
        insp = Inspection(
            inspection_number=f"INSP-EVIDENCE-{uuid.uuid4().hex[:6]}",
            inspector_id=inspector_id,
            commodity_name="Multigrain Bread 400g",
            brand_name="DailyFresh",
            status="FINALIZED",
            compliance_status="COMPLIANT"
        )
        db.add(insp)
        db.flush()
        
        img_rec = InspectionImage(
            id=str(uuid.uuid4()),
            inspection_id=insp.id,
            view_type="FRONT",
            original_filename=img_name,
            storage_path=img_path,
            processed_path=img_path,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            width=400,
            height=300,
            file_size_bytes=os.path.getsize(img_path),
            mime_type="image/jpeg",
            quality_assessment={"quality_score": 0.94, "is_acceptable": True}
        )
        db.add(img_rec)
        db.commit()
        insp_id = insp.id
    finally:
        db.close()

    res = client.post(f"/api/inspections/{insp_id}/report", headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["pdf_sha256"] is not None

# -----------------------------------------------------------------
# 6. Test Report Retrieval & Query API Endpoints
# -----------------------------------------------------------------
def test_report_query_endpoints():
    headers, _ = get_auth_headers_and_inspector_id("INSPECTOR")
    
    # 1. GET /api/reports list
    list_res = client.get("/api/reports", headers=headers)
    assert list_res.status_code == 200
    reports = list_res.json()
    assert isinstance(reports, list)
    assert len(reports) >= 1
    
    # 2. GET /api/inspections/{id}/report
    first_report = reports[0]
    insp_id = first_report["inspection_id"]
    detail_res = client.get(f"/api/inspections/{insp_id}/report", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["certificate_number"] == first_report["certificate_number"]
    assert detail_data["pdf_sha256"] == first_report["pdf_sha256"]
