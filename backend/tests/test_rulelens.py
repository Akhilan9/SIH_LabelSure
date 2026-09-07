import os
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_header():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "Admin@LabelSure2026"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_rulelens_inspection_and_finding_lifecycle():
    headers = get_auth_header()
    
    # 1. Create an inspection
    create_res = client.post(
        "/api/inspections",
        headers=headers,
        json={
            "commodity_name": "Premium Almond Butter 200g",
            "brand_name": "ApexNuts",
            "rule_version": "LMPC-2026-RULES",
            "context": {
                "commodity_category": "FOOD_BEVERAGE",
                "product_type": "Pre-Packaged Food",
                "is_food": True,
                "is_imported": False,
                "package_type": "SINGLE_PRE_PACKAGED"
            }
        }
    )
    assert create_res.status_code == 201
    insp_id = create_res.json()["id"]
    
    # 2. Upload a synthesized image with clear statutory declarations
    img = np.ones((800, 900, 3), dtype=np.uint8) * 240
    cv2.putText(img, "APEX ALMOND BUTTER", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
    cv2.putText(img, "Net Quantity: 200 g", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs. 320.00 incl. of all taxes", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "Mfg by: Apex Nutri Foods, Plot 5, Manesar 122050", (50, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Date of Mfg: 02/2026", (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Best Before: 02/2027", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Consumer Care: 1800-333-4444 support@apexnuts.com", (50, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    
    _, buffer = cv2.imencode(".jpg", img)
    files = {"file": ("almond_butter.jpg", io.BytesIO(buffer.tobytes()), "image/jpeg")}
    upload_res = client.post(f"/api/inspections/{insp_id}/images", data={"view_type": "FRONT"}, files=files, headers=headers)
    assert upload_res.status_code == 201
    
    # 3. Trigger pipeline analysis
    analyze_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res.status_code == 200
    
    # 4. Invoke RuleLens endpoint: GET /api/inspections/{id}/rulelens
    rulelens_res = client.get(f"/api/inspections/{insp_id}/rulelens", headers=headers)
    assert rulelens_res.status_code == 200
    rl_data = rulelens_res.json()
    
    assert rl_data["inspection_id"] == insp_id
    assert rl_data["total_findings"] > 0
    assert "summary" in rl_data
    assert len(rl_data["findings"]) > 0
    
    # Verify all 13 required fields for every finding in RuleLens
    for f in rl_data["findings"]:
        # 1. Requirement
        assert "requirement" in f and f["requirement"]
        # 2. Rule ID
        assert "rule_id" in f and f["rule_id"]
        # 3. Rule version
        assert "rule_version" in f and f["rule_version"]
        # 4. Clause/reference
        assert "clause_reference" in f and f["clause_reference"]
        # 5. Observed value
        assert "observed_value" in f
        # 6. Expected condition
        assert "expected_condition" in f and f["expected_condition"]
        # 7. Evidence image
        assert "evidence_image" in f
        # 8. Bounding box
        assert "bounding_box" in f and len(f["bounding_box"]) == 4
        # 9. OCR text
        assert "ocr_text" in f
        # 10. AI confidence
        assert "ai_confidence" in f and (0.0 <= f["ai_confidence"] <= 1.0)
        # 11. Decision
        assert f["decision"] in ("PASS", "FAIL", "UNCERTAIN", "NOT_APPLICABLE")
        # 12. Explanation
        assert "explanation" in f and len(f["explanation"]) > 0
        # 13. Inspector status
        assert "inspector_status" in f
        
        # Verify explanation connects to actual rule & evidence data
        assert f["clause_reference"] in f["explanation"] or f["rule_id"] in f["explanation"] or "declaration" in f["explanation"].lower() or "applicable" in f["explanation"].lower()
        
    # 5. Invoke single finding RuleLens endpoint: GET /api/findings/{id}/rulelens
    first_finding = rl_data["findings"][0]
    single_res = client.get(f"/api/findings/{first_finding['id']}/rulelens", headers=headers)
    assert single_res.status_code == 200
    single_f = single_res.json()
    assert single_f["id"] == first_finding["id"]
    assert single_f["rule_id"] == first_finding["rule_id"]
    assert single_f["requirement"] == first_finding["requirement"]
    assert single_f["decision"] == first_finding["decision"]
    assert single_f["explanation"] == first_finding["explanation"]

    # 6. Test Inspector Status Override
    override_res = client.patch(
        f"/api/findings/{first_finding['id']}",
        headers=headers,
        json={
            "inspector_status": "PASS",
            "inspector_comment": "Inspector verified physical container label on shelf."
        }
    )
    assert override_res.status_code == 200
    
    # Verify RuleLens reflects the updated inspector status and decision
    updated_rl_res = client.get(f"/api/findings/{first_finding['id']}/rulelens", headers=headers)
    assert updated_rl_res.status_code == 200
    updated_f = updated_rl_res.json()
    assert updated_f["inspector_status"] == "PASS"
    assert updated_f["decision"] == "PASS"
    assert updated_f["inspector_comment"] == "Inspector verified physical container label on shelf."
