import os
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.rule_engine.evaluator import evaluate_rule

client = TestClient(app)

def get_auth_headers(role: str = "INSPECTOR"):
    creds = {
        "ADMIN": ("admin", "Admin@LabelSure2026"),
        "INSPECTOR": ("inspector1", "Inspector@2026"),
    }
    username, password = creds[role]
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# -----------------------------------------------------------------
# 1. Inspection Creation Test
# -----------------------------------------------------------------
def test_inspection_creation():
    headers = get_auth_headers("INSPECTOR")
    payload = {
        "commodity_name": "Organic Honey 500g",
        "brand_name": "ApexNaturals",
        "rule_version": "LMPC-2026-RULES",
        "notes": "Retail audit at Connaught Place supermarket",
        "context": {
            "commodity_category": "FOOD_BEVERAGE",
            "product_type": "Pre-Packaged Food",
            "is_food": True,
            "is_imported": False,
            "package_type": "SINGLE_PRE_PACKAGED",
            "declared_net_quantity": 500.0,
            "declared_unit": "g"
        }
    }
    res = client.post("/api/inspections", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["inspection_number"].startswith("INSP-")
    assert data["status"] == "DRAFT"
    assert data["compliance_status"] == "PENDING"
    assert data["commodity_name"] == "Organic Honey 500g"
    assert data["brand_name"] == "ApexNaturals"

# -----------------------------------------------------------------
# 2. Inspection Retrieval Tests (List & Detail)
# -----------------------------------------------------------------
def test_inspection_retrieval_and_filtering():
    headers = get_auth_headers("INSPECTOR")
    # Retrieve list
    list_res = client.get("/api/inspections", headers=headers)
    assert list_res.status_code == 200
    inspections = list_res.json()
    assert isinstance(inspections, list)
    assert len(inspections) > 0
    
    first_id = inspections[0]["id"]
    
    # Retrieve single inspection detail
    detail_res = client.get(f"/api/inspections/{first_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == first_id
    assert "context" in detail
    assert "images" in detail
    assert "declarations" in detail
    assert "findings" in detail

    # Test search query
    search_res = client.get(f"/api/inspections?search={detail['commodity_name'][:4]}", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

# -----------------------------------------------------------------
# 3. Inspection Update Test
# -----------------------------------------------------------------
def test_inspection_update():
    headers = get_auth_headers("INSPECTOR")
    # Create inspection
    create_res = client.post(
        "/api/inspections",
        json={"commodity_name": "Initial Commodity Name", "brand_name": "BrandA"},
        headers=headers
    )
    insp_id = create_res.json()["id"]

    # Update inspection
    update_payload = {
        "commodity_name": "Updated Premium Commodity 1kg",
        "brand_name": "ApexBrandUpdated",
        "notes": "Updated remarks during physical inspection"
    }
    patch_res = client.patch(f"/api/inspections/{insp_id}", json=update_payload, headers=headers)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["commodity_name"] == "Updated Premium Commodity 1kg"
    assert updated["brand_name"] == "ApexBrandUpdated"

# -----------------------------------------------------------------
# 4. Image Upload, Storage, Metadata, Hashing, & Preprocessing Test
# -----------------------------------------------------------------
def test_image_upload_pipeline():
    headers = get_auth_headers("INSPECTOR")
    
    # 1. Create target inspection
    create_res = client.post(
        "/api/inspections",
        json={"commodity_name": "Packaged Wheat Flour 5kg", "brand_name": "ApexGrains"},
        headers=headers
    )
    insp_id = create_res.json()["id"]
    
    # 2. Synthesize test image with legal declarations
    img = np.ones((850, 850, 3), dtype=np.uint8) * 235
    cv2.putText(img, "APEX WHEAT FLOUR", (60, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    cv2.putText(img, "Net Quantity: 5 kg", (60, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs. 260.00 incl. taxes", (60, 370), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    _, buffer = cv2.imencode(".jpg", img)
    image_bytes = buffer.tobytes()
    
    # 3. Upload image
    files = {"file": ("package_front.jpg", io.BytesIO(image_bytes), "image/jpeg")}
    data = {"view_type": "FRONT"}
    
    upload_res = client.post(f"/api/inspections/{insp_id}/images", data=data, files=files, headers=headers)
    assert upload_res.status_code == 201
    img_data = upload_res.json()
    
    # Validate image metadata
    assert img_data["inspection_id"] == insp_id
    assert img_data["view_type"] == "FRONT"
    assert img_data["width"] == 850
    assert img_data["height"] == 850
    assert img_data["file_size_bytes"] == len(image_bytes)
    assert img_data["mime_type"] == "image/jpeg"
    assert len(img_data["sha256_hash"]) == 64
    
    # Validate storage paths
    assert img_data["storage_path"].startswith("/storage/uploads/")
    assert img_data["processed_path"].startswith("/storage/processed/")
    
    # Validate Quality Assessment
    assert "quality_assessment" in img_data
    qa = img_data["quality_assessment"]
    assert "quality_score" in qa
    assert "blur_score" in qa
    assert "brightness_score" in qa
    assert "resolution_score" in qa
    assert "orientation" in qa
    assert qa["is_acceptable"] is True
    
    # 4. Fetch Image Details via API
    image_id = img_data["id"]
    get_img_res = client.get(f"/api/images/{image_id}", headers=headers)
    assert get_img_res.status_code == 200
    assert get_img_res.json()["id"] == image_id

    # 5. Inspection status should have transitioned to CAPTURED
    insp_res = client.get(f"/api/inspections/{insp_id}", headers=headers)
    assert insp_res.json()["status"] == "CAPTURED"
    assert len(insp_res.json()["images"]) == 1

# -----------------------------------------------------------------
# 5. Unsupported MIME Type Rejection
# -----------------------------------------------------------------
def test_unsupported_file_type_rejection():
    headers = get_auth_headers("INSPECTOR")
    create_res = client.post("/api/inspections", json={"commodity_name": "Test Item"}, headers=headers)
    insp_id = create_res.json()["id"]
    
    # Upload text file pretending to be an image
    files = {"file": ("malicious.txt", io.BytesIO(b"Hello world"), "text/plain")}
    res = client.post(f"/api/inspections/{insp_id}/images", files=files, headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

# -----------------------------------------------------------------
# 6. UNCERTAIN Verdict Support on Insufficient Image Quality
# -----------------------------------------------------------------
def test_uncertain_supported_on_insufficient_evidence():
    """
    Verifies that when photographic evidence has quality degradation (e.g. blur or low resolution),
    the rule evaluation yields UNCERTAIN instead of false NON_COMPLIANT / FAIL.
    """
    rule = {
        "rule_id": "LMPC-2026-R01",
        "rule_version": "LMPC-2026-RULES",
        "clause_reference": "Rule 6(1)(e)",
        "requirement": "Maximum Retail Price (MRP) Declaration",
        "applicability": {},
        "validation_logic": {"field": "MAXIMUM_RETAIL_PRICE", "operator": "EXISTS"},
        "severity": "CRITICAL"
    }
    
    # Scenario A: Good image quality (sharp) and MRP declaration is missing -> Result: FAIL
    finding_sharp = evaluate_rule(
        rule=rule,
        declarations=[],  # No declarations detected
        context={"commodity_category": "GENERAL_COMMODITY"},
        overall_image_quality=0.92,
        has_blurry_image=False
    )
    assert finding_sharp["ai_status"] == "FAIL"
    assert finding_sharp["final_status"] == "FAIL"

    # Scenario B: Blurry image / insufficient evidence -> Result MUST BE UNCERTAIN!
    finding_blurry = evaluate_rule(
        rule=rule,
        declarations=[],  # No declarations detected due to blur
        context={"commodity_category": "GENERAL_COMMODITY"},
        overall_image_quality=0.45,
        has_blurry_image=True
    )
    assert finding_blurry["ai_status"] == "UNCERTAIN"
    assert finding_blurry["final_status"] == "UNCERTAIN"
    assert finding_blurry["uncertainty_reason"] is not None
    assert "insufficient" in finding_blurry["uncertainty_reason"].lower()
