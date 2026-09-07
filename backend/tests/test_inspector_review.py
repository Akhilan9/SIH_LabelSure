import os
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_auth_header(role: str = "INSPECTOR"):
    creds = {
        "ADMIN": ("admin", "Admin@LabelSure2026"),
        "INSPECTOR": ("inspector1", "Inspector@2026"),
        "SUPERVISOR": ("supervisor1", "Supervisor@2026")
    }
    username, password = creds[role]
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_full_inspector_review_workflow():
    headers = get_auth_header("INSPECTOR")
    
    # -------------------------------------------------------------
    # 1. Create Inspection
    # -------------------------------------------------------------
    create_res = client.post(
        "/api/inspections",
        headers=headers,
        json={
            "commodity_name": "Artisanal Olive Oil 500ml",
            "brand_name": "ApexOils",
            "rule_version": "LMPC-2026-RULES",
            "context": {
                "commodity_category": "FOOD_BEVERAGE",
                "product_type": "Pre-Packaged Food",
                "is_food": True,
                "is_imported": True,
                "origin_country": "Spain",
                "package_type": "SINGLE_PRE_PACKAGED"
            }
        }
    )
    assert create_res.status_code == 201
    insp_id = create_res.json()["id"]

    # -------------------------------------------------------------
    # 2. Upload Initial Evidence (Front Label)
    # -------------------------------------------------------------
    front_img = np.ones((800, 900, 3), dtype=np.uint8) * 240
    cv2.putText(front_img, "APEX ARTISANAL OLIVE OIL", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(front_img, "Net Quantity: 500 ml", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(front_img, "Country of Origin: Spain", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    
    _, buffer1 = cv2.imencode(".jpg", front_img)
    files1 = {"file": ("front_label.jpg", io.BytesIO(buffer1.tobytes()), "image/jpeg")}
    up_res1 = client.post(f"/api/inspections/{insp_id}/images", data={"view_type": "FRONT"}, files=files1, headers=headers)
    assert up_res1.status_code == 201
    img1_id = up_res1.json()["id"]

    # -------------------------------------------------------------
    # 3. Trigger Initial AI Analysis
    # -------------------------------------------------------------
    analyze_res1 = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert analyze_res1.status_code == 200

    # -------------------------------------------------------------
    # 4. Inspector Views Original Image & OCR Bounding Boxes
    # -------------------------------------------------------------
    img_detail_res = client.get(f"/api/images/{img1_id}", headers=headers)
    assert img_detail_res.status_code == 200
    img_detail = img_detail_res.json()
    assert img_detail["storage_path"].startswith("/storage/uploads/")
    assert img_detail["width"] == 900
    assert img_detail["height"] == 800

    # RuleLens inspection view contains bounding box coordinates
    rulelens_res = client.get(f"/api/inspections/{insp_id}/rulelens", headers=headers)
    assert rulelens_res.status_code == 200
    findings = rulelens_res.json()["findings"]
    assert len(findings) > 0

    # -------------------------------------------------------------
    # 5. Inspector Views & Edits Declarations
    # -------------------------------------------------------------
    decls_res = client.get(f"/api/inspections/{insp_id}/declarations", headers=headers)
    assert decls_res.status_code == 200
    decls = decls_res.json()
    assert len(decls) > 0
    first_decl = decls[0]
    
    # Inspector edits declaration text
    edit_decl_res = client.patch(
        f"/api/declarations/{first_decl['id']}",
        headers=headers,
        json={
            "raw_text": first_decl["raw_text"] + " [Inspector Verified]",
            "normalized_value": {"verified": True}
        }
    )
    assert edit_decl_res.status_code == 200
    edited_decl = edit_decl_res.json()
    assert edited_decl["is_inspector_edited"] is True
    assert edited_decl["original_ai_value"] == first_decl["raw_text"]

    # -------------------------------------------------------------
    # 6. Inspector Edits Product Context
    # -------------------------------------------------------------
    ctx_patch_res = client.patch(
        f"/api/inspections/{insp_id}/context",
        headers=headers,
        json={
            "declared_net_quantity": 500.0,
            "declared_unit": "ml",
            "notes": "Inspector verified importer credentials on site"
        }
    )
    assert ctx_patch_res.status_code == 200
    updated_ctx = ctx_patch_res.json()
    assert updated_ctx["declared_net_quantity"] == 500.0
    assert updated_ctx["declared_unit"] == "ml"

    # -------------------------------------------------------------
    # 7. Inspector Overrides Findings: Accept, Reject, Mark Uncertain
    # -------------------------------------------------------------
    # A. Accept finding with comment (e.g. first finding)
    f0 = findings[0]
    orig_ai_status_0 = f0["ai_status"]
    accept_res = client.patch(
        f"/api/findings/{f0['id']}",
        headers=headers,
        json={
            "inspector_status": "PASS",
            "inspector_comment": "Inspector confirmed presence of physical imprint."
        }
    )
    assert accept_res.status_code == 200
    f0_updated = accept_res.json()
    # CRITICAL: AI status is NEVER overwritten
    assert f0_updated["ai_status"] == orig_ai_status_0
    assert f0_updated["inspector_status"] == "PASS"
    assert f0_updated["final_status"] == "PASS"
    assert f0_updated["inspector_comment"] == "Inspector confirmed presence of physical imprint."
    assert f0_updated["reviewed_at"] is not None

    # B. Reject finding with comment
    if len(findings) > 1:
        f1 = findings[1]
        orig_ai_status_1 = f1["ai_status"]
        reject_res = client.patch(
            f"/api/findings/{f1['id']}",
            headers=headers,
            json={
                "inspector_status": "FAIL",
                "inspector_comment": "Missing statutory font contrast."
            }
        )
        assert reject_res.status_code == 200
        f1_updated = reject_res.json()
        assert f1_updated["ai_status"] == orig_ai_status_1
        assert f1_updated["inspector_status"] == "FAIL"
        assert f1_updated["final_status"] == "FAIL"

    # C. Mark finding UNCERTAIN with comment
    if len(findings) > 2:
        f2 = findings[2]
        orig_ai_status_2 = f2["ai_status"]
        unc_res = client.patch(
            f"/api/findings/{f2['id']}",
            headers=headers,
            json={
                "inspector_status": "UNCERTAIN",
                "inspector_comment": "Torn label corner requires warehouse re-audit."
            }
        )
        assert unc_res.status_code == 200
        f2_updated = unc_res.json()
        assert f2_updated["ai_status"] == orig_ai_status_2
        assert f2_updated["inspector_status"] == "UNCERTAIN"
        assert f2_updated["final_status"] == "UNCERTAIN"

    # -------------------------------------------------------------
    # 8. Inspector Uploads Additional Evidence (Back Panel)
    # -------------------------------------------------------------
    back_img = np.ones((800, 900, 3), dtype=np.uint8) * 240
    cv2.putText(back_img, "MRP Rs. 750.00 incl. of all taxes", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(back_img, "Imported by: Apex Gourmet Imports, Mumbai 400001", (50, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(back_img, "Date of Mfg: 01/2026", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(back_img, "Best Before: 01/2028", (50, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(back_img, "Customer Care: 1800-777-8888 care@apexoils.in", (50, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    
    _, buffer2 = cv2.imencode(".jpg", back_img)
    files2 = {"file": ("back_panel.jpg", io.BytesIO(buffer2.tobytes()), "image/jpeg")}
    up_res2 = client.post(f"/api/inspections/{insp_id}/images", data={"view_type": "BACK"}, files=files2, headers=headers)
    assert up_res2.status_code == 201
    
    # -------------------------------------------------------------
    # 9. Inspector Reruns Analysis
    # -------------------------------------------------------------
    rerun_res = client.post(f"/api/inspections/{insp_id}/analyze", headers=headers)
    assert rerun_res.status_code == 200
    
    # Verify inspector manual overrides were preserved across rerun
    rerun_findings_res = client.get(f"/api/inspections/{insp_id}/rulelens", headers=headers)
    assert rerun_findings_res.status_code == 200
    rerun_findings = rerun_findings_res.json()["findings"]
    f0_rechecked = next((f for f in rerun_findings if f["rule_id"] == f0["rule_id"]), None)
    assert f0_rechecked is not None
    assert f0_rechecked["inspector_status"] == "PASS"
    assert f0_rechecked["decision"] == "PASS"
    assert f0_rechecked["inspector_comment"] == "Inspector confirmed presence of physical imprint."

    # -------------------------------------------------------------
    # 10. Inspector Finalizes Inspection
    # -------------------------------------------------------------
    finalize_res = client.post(f"/api/inspections/{insp_id}/finalize", headers=headers)
    assert finalize_res.status_code == 200
    finalized = finalize_res.json()
    assert finalized["status"] == "FINALIZED"
    assert finalized["finalized_at"] is not None

    # -------------------------------------------------------------
    # 11. Audit Trail Verification
    # -------------------------------------------------------------
    audit_res = client.get(f"/api/audit-logs?inspection_id={insp_id}", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    actions = [log["action"] for log in logs]
    
    assert "CREATE_INSPECTION" in actions
    assert "UPLOAD_IMAGE" in actions
    assert "EDIT_DECLARATION" in actions
    assert "EDIT_PRODUCT_CONTEXT" in actions
    assert "OVERRIDE_FINDING" in actions
    assert "FINALIZE_INSPECTION" in actions
