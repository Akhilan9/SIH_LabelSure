import uuid
import base64
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models import SyncQueue, Inspection, InspectionImage

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

def generate_sample_image_base64() -> str:
    """Creates a synthetic label image in base64 format for testing."""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    cv2.putText(img, "APEX COFFEE ROASTERS", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "NET QTY: 250 g", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs 350.00 (INCL OF ALL TAXES)", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "MFG: 01/2026", (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "COUNTRY OF ORIGIN: INDIA", (30, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    _, buffer = cv2.imencode(".jpg", img)
    return base64.b64encode(buffer).decode("utf-8")

# -----------------------------------------------------------------
# 1. Offline Creation Test
# -----------------------------------------------------------------
def test_offline_creation():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-create-{uuid.uuid4()}"
    client_id = "mobile-device-s24-001"
    
    payload = {
        "commodity_name": "Premium Basmati Rice 1kg",
        "brand_name": "RoyalHeritage",
        "rule_version": "LMPC-2026-RULES",
        "notes": "Offline created inspection at rural mandi",
        "context": {
            "commodity_category": "FOOD",
            "product_type": "Pre-Packaged Grain",
            "is_food": True,
            "is_imported": False,
            "origin_country": "India",
            "package_type": "SINGLE_PRE_PACKAGED",
            "declared_net_quantity": 1000.0,
            "declared_unit": "g"
        }
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    res = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "SYNCED"
    assert "inspection_id" in data
    assert data["inspection_number"].startswith("INSP-")

# -----------------------------------------------------------------
# 2. Offline Image Capture Test
# -----------------------------------------------------------------
def test_offline_image_capture():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-capture-{uuid.uuid4()}"
    client_id = "mobile-device-s24-002"
    
    img_b64 = generate_sample_image_base64()
    
    payload = {
        "commodity_name": "Artisanal Filter Coffee 250g",
        "brand_name": "ApexRoasters",
        "rule_version": "LMPC-2026-RULES",
        "notes": "Multi-panel photo offline capture",
        "context": {
            "commodity_category": "FOOD",
            "is_food": True,
            "is_imported": False,
            "origin_country": "India",
            "declared_net_quantity": 250.0,
            "declared_unit": "g"
        },
        "images": [
            {
                "view_type": "FRONT",
                "image_base64": img_b64,
                "filename": "front_panel.jpg"
            },
            {
                "view_type": "MRP_PANEL",
                "image_base64": img_b64,
                "filename": "mrp_panel.jpg"
            }
        ],
        "auto_analyze": False
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    res = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "REVIEW_REQUIRED"
    assert data["images_count"] == 2
    
    # Verify image cryptographic SHA-256 and records in database
    db = SessionLocal()
    try:
        images = db.query(InspectionImage).filter(InspectionImage.inspection_id == data["inspection_id"]).all()
        assert len(images) == 2
        for img in images:
            assert img.sha256_hash is not None
            assert len(img.sha256_hash) == 64
            assert img.view_type in ["FRONT", "MRP_PANEL"]
            assert img.is_acceptable is True
    finally:
        db.close()

# -----------------------------------------------------------------
# 3. Reconnect & Successful Synchronization Test (with auto analysis)
# -----------------------------------------------------------------
def test_reconnect_and_successful_synchronization():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-reconnect-{uuid.uuid4()}"
    client_id = "mobile-device-s24-003"
    
    img_b64 = generate_sample_image_base64()
    
    # Simulated queued payload that was pending during disconnection
    queued_payload = {
        "commodity_name": "Single-Origin Dark Roast 250g",
        "brand_name": "ApexRoasters",
        "rule_version": "LMPC-2026-RULES",
        "notes": "Synchronized after reconnection to central network",
        "context": {
            "commodity_category": "FOOD",
            "is_food": True,
            "is_imported": False,
            "origin_country": "India",
            "declared_net_quantity": 250.0,
            "declared_unit": "g"
        },
        "images": [
            {
                "view_type": "FRONT",
                "image_base64": img_b64,
                "filename": "front.jpg"
            }
        ],
        "auto_analyze": True
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    # Send sync request (simulating network reconnect)
    res = client.post("/api/sync/inspections", json=queued_payload, headers=sync_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "inspection_id" in data
    assert data["images_count"] >= 1
    assert "findings_summary" in data

# -----------------------------------------------------------------
# 4. Duplicate Prevention (Idempotency Key Deduplication) Test
# -----------------------------------------------------------------
def test_duplicate_prevention():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"idempotency-dedup-{uuid.uuid4()}"
    client_id = "mobile-device-s24-004"
    
    payload = {
        "commodity_name": "Tea Powder 500g",
        "brand_name": "AssamGold",
        "rule_version": "LMPC-2026-RULES",
        "context": {
            "commodity_category": "FOOD",
            "is_food": True,
            "is_imported": False,
            "declared_net_quantity": 500.0,
            "declared_unit": "g"
        }
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    # First sync call
    res1 = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "SYNCED"
    orig_insp_id = data1["inspection_id"]
    
    # Second sync call with exact same idempotency key (simulating re-transmission or retry)
    res2 = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ALREADY_SYNCED"
    assert data2["inspection_id"] == orig_insp_id
    
    # Third sync call
    res3 = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["status"] == "ALREADY_SYNCED"
    assert data3["inspection_id"] == orig_insp_id
    
    # Verify in DB that only 1 inspection was ever created
    db = SessionLocal()
    try:
        sync_entries = db.query(SyncQueue).filter(SyncQueue.idempotency_key == idempotency_key).all()
        assert len(sync_entries) == 1
        inspections = db.query(Inspection).filter(Inspection.id == orig_insp_id).all()
        assert len(inspections) == 1
    finally:
        db.close()

# -----------------------------------------------------------------
# 5. Failed Synchronization & Error Recording Test
# -----------------------------------------------------------------
def test_failed_synchronization():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-fail-{uuid.uuid4()}"
    client_id = "mobile-device-s24-005"
    
    # Corrupt base64 image data to trigger error
    bad_payload = {
        "commodity_name": "Defective Test Item",
        "brand_name": "FaultyBrand",
        "images": [
            {
                "view_type": "FRONT",
                "image_base64": "NOT_A_VALID_BASE64_STRING_%%%!!!"
            }
        ]
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    res = client.post("/api/sync/inspections", json=bad_payload, headers=sync_headers)
    assert res.status_code == 500
    assert "SYNC_FAILED" in res.json().get("error", {}).get("code", "")
    
    # Verify error was logged in SyncQueue table
    db = SessionLocal()
    try:
        entry = db.query(SyncQueue).filter(SyncQueue.idempotency_key == idempotency_key).first()
        assert entry is not None
        assert entry.status == "FAILED"
        assert entry.last_error is not None
        assert entry.attempts == 1
    finally:
        db.close()

# -----------------------------------------------------------------
# 6. Retry Mechanism Test
# -----------------------------------------------------------------
def test_retry_mechanism():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-retry-{uuid.uuid4()}"
    client_id = "mobile-device-s24-006"
    
    # Step A: Fail first
    bad_payload = {
        "commodity_name": "Initially Failing Inspection",
        "images": [{"view_type": "FRONT", "image_base64": "INVALID_B64_DATA"}]
    }
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    res_fail = client.post("/api/sync/inspections", json=bad_payload, headers=sync_headers)
    assert res_fail.status_code == 500
    
    # Step B: Retry with corrected payload
    img_b64 = generate_sample_image_base64()
    repaired_payload = {
        "commodity_name": "Successfully Repaired Inspection",
        "brand_name": "RetryBrand",
        "images": [{"view_type": "FRONT", "image_base64": img_b64}],
        "auto_analyze": False
    }
    res_retry = client.post("/api/sync/inspections", json=repaired_payload, headers=sync_headers)
    assert res_retry.status_code == 200
    data = res_retry.json()
    assert data["success"] is True
    assert data["status"] in ["SYNCED", "REVIEW_REQUIRED"]
    
    # Verify attempt count incremented in SyncQueue
    db = SessionLocal()
    try:
        entry = db.query(SyncQueue).filter(SyncQueue.idempotency_key == idempotency_key).first()
        assert entry is not None
        assert entry.status == "PROCESSED"
        assert entry.attempts >= 2
        assert entry.last_error is None
    finally:
        db.close()

# -----------------------------------------------------------------
# 7. Sync Status & Queue Query Endpoints Test
# -----------------------------------------------------------------
def test_sync_status_and_queue_endpoints():
    headers = get_auth_headers("INSPECTOR")
    idempotency_key = f"offline-status-{uuid.uuid4()}"
    client_id = "mobile-device-s24-007"
    
    payload = {
        "commodity_name": "Ground Spices 100g",
        "brand_name": "SpicesDirect"
    }
    
    sync_headers = {
        **headers,
        "X-Idempotency-Key": idempotency_key,
        "X-Client-ID": client_id
    }
    
    # Submit sync
    res = client.post("/api/sync/inspections", json=payload, headers=sync_headers)
    assert res.status_code == 200
    
    # Query status by key
    res_status = client.get(f"/api/sync/status/{idempotency_key}", headers=headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["idempotency_key"] == idempotency_key
    assert status_data["status"] == "PROCESSED"
    assert status_data["client_id"] == client_id
    
    # Query queue list
    res_queue = client.get(f"/api/sync/queue?client_id={client_id}", headers=headers)
    assert res_queue.status_code == 200
    queue_data = res_queue.json()
    assert len(queue_data) >= 1
    assert any(q["idempotency_key"] == idempotency_key for q in queue_data)
