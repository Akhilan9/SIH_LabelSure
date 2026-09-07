import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.international_engine import (
    get_available_jurisdictions,
    get_jurisdiction_rules,
    scan_text_for_banned_substances,
    compare_product_with_jurisdiction
)

client = TestClient(app)


def get_auth_headers():
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@LabelSure2026"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_available_jurisdictions():
    jurisdictions = get_available_jurisdictions()
    assert len(jurisdictions) >= 5
    ids = [j["jurisdiction_id"] for j in jurisdictions]
    assert "USA" in ids
    assert "EU" in ids
    assert "GBR" in ids
    assert "AUS" in ids
    assert "GCC" in ids

    # Check flags and acts
    usa = next(j for j in jurisdictions if j["jurisdiction_id"] == "USA")
    assert usa["flag_emoji"] == "🇺🇸"
    assert len(usa["governing_acts"]) >= 1


def test_scan_text_for_banned_substances():
    # Test detecting Titanium Dioxide (E171)
    text_sample = "Ingredients: Refined wheat flour, sugar, vegetable oil, Titanium Dioxide (E171), artificial flavor."
    matches = scan_text_for_banned_substances(text_sample, target_jurisdiction_id="EU")
    assert len(matches) >= 1
    e171 = next((m for m in matches if m["canonical_name"] == "Titanium Dioxide"), None)
    assert e171 is not None
    assert e171["is_banned_in_target"] is True
    assert e171["target_ban_detail"]["legal_citation"] is not None
    assert "DNA" in e171["target_ban_detail"]["health_concern"] or "Genotoxicity" in e171["target_ban_detail"]["health_concern"]

    # Test detecting BVO
    bvo_sample = "Carbonated water, high fructose corn syrup, citric acid, brominated vegetable oil, natural citrus flavor."
    bvo_matches = scan_text_for_banned_substances(bvo_sample, target_jurisdiction_id="USA")
    assert any(m["canonical_name"].startswith("Brominated Vegetable Oil") for m in bvo_matches)


def test_compare_product_with_usa_jurisdiction():
    declarations = [
        {"category": "MRP", "raw_text": "MRP Rs. 150.00 incl. of all taxes", "normalized_value": "150.00"},
        {"category": "NET_QUANTITY", "raw_text": "Net Wt: 400g", "normalized_value": "400", "unit": "g"},
        {"category": "MANUFACTURER", "raw_text": "Manufactured by XYZ Pvt Ltd, Mumbai 400001", "normalized_value": "XYZ"}
    ]
    raw_ocr = "XYZ Premium Cookies Net Wt: 400g MRP Rs. 150.00 incl. of all taxes Contains E171 color"

    res = compare_product_with_jurisdiction(
        jurisdiction_id="USA",
        declarations=declarations,
        context={"commodity_category": "FOOD", "product_type": "Biscuits"},
        raw_ocr_text=raw_ocr
    )

    assert res["jurisdiction"]["jurisdiction_id"] == "USA"
    assert res["blockers_count"] >= 1  # Indian MRP is prohibited in US free market
    assert res["overall_verdict"] in ["EXPORT_BLOCKED", "ACTION_REQUIRED"]

    # Verify MRP rule is flagged as PROHIBITED_IN_TARGET
    mrp_item = next((item for item in res["comparison_matrix"] if item["dimension"] == "PRICING_MRP"), None)
    assert mrp_item is not None
    assert mrp_item["export_status"] == "PROHIBITED_IN_TARGET"

    # Verify Net Quantity dual units flag
    net_item = next((item for item in res["comparison_matrix"] if item["dimension"] == "NET_QUANTITY_UNITS"), None)
    assert net_item is not None
    assert net_item["export_status"] == "ACTION_REQUIRED"


def test_compare_product_with_gcc_jurisdiction():
    # Label without Arabic text
    declarations = [
        {"category": "MRP", "raw_text": "MRP Rs. 50", "normalized_value": "50"},
        {"category": "NET_QUANTITY", "raw_text": "Net Wt: 250g", "normalized_value": "250", "unit": "g"}
    ]
    raw_ocr = "Crispy Namkeen 250g MRP Rs. 50 Best before 6 months from packaging"

    res = compare_product_with_jurisdiction(
        jurisdiction_id="GCC",
        declarations=declarations,
        raw_ocr_text=raw_ocr
    )
    assert res["jurisdiction"]["jurisdiction_id"] == "GCC"
    # Arabic is mandatory under GSO 9/2013
    lang_item = next((item for item in res["comparison_matrix"] if item["dimension"] == "LANGUAGE_REQUIREMENTS"), None)
    assert lang_item is not None
    assert lang_item["export_status"] == "ACTION_REQUIRED"


def test_international_api_endpoints():
    headers = get_auth_headers()

    # 1. GET /api/international/jurisdictions
    res = client.get("/api/international/jurisdictions", headers=headers)
    assert res.status_code == 200
    jurisdictions = res.json()
    assert len(jurisdictions) >= 5

    # 2. GET /api/international/jurisdictions/USA
    res = client.get("/api/international/jurisdictions/USA", headers=headers)
    assert res.status_code == 200
    assert res.json()["country_name"] == "United States of America"

    # 3. GET /api/international/banned-substances
    res = client.get("/api/international/banned-substances?search=Titanium", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 1
    assert any("Titanium" in s["canonical_name"] for s in data["substances"])

    # 4. POST /api/international/scan-text
    scan_res = client.post(
        "/api/international/scan-text",
        headers=headers,
        json={
            "text": "Ingredients: Potassium Bromate (E924), flour, water, yeast, salt.",
            "jurisdiction_id": "EU"
        }
    )
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["total_found"] >= 1
    match = scan_data["matches"][0]
    assert match["canonical_name"] == "Potassium Bromate"
    assert match["is_banned_in_target"] is True
    assert "Carcinogen" in match["target_ban_detail"]["health_concern"]
