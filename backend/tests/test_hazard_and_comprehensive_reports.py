import pytest
import os
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.rule_engine.hazard_engine import (
    generate_hazard_violation_explanation,
    generate_recommended_follow_up_actions
)
from backend.app.reports.generator import generate_inspection_pdf

client = TestClient(app)

def get_auth_headers():
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@LabelSure2026"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_hazard_engine_five_step_chain():
    # 1. MRP Violation
    mrp_hazard = generate_hazard_violation_explanation(
        clause_reference="Rule 6(1)(e)",
        requirement_title="Maximum Retail Price (MRP) Declaration",
        observed_value="[MISSING]",
        expected_condition="Must declare MRP inclusive of all taxes in Rs/₹ format",
        final_status="FAIL"
    )
    assert "MRP" in mrp_hazard["detected_issue"] or "Maximum Retail Price" in mrp_hazard["detected_issue"]
    assert "Rule 6(1)(e)" in mrp_hazard["applicable_rule"]
    assert "Section 18" in mrp_hazard["applicable_rule"]
    assert "Section 36(1)" in mrp_hazard["consumer_regulatory_risk"]["regulatory_risk"]
    assert "price gouging" in mrp_hazard["consumer_regulatory_risk"]["consumer_harm"].lower()
    assert mrp_hazard["evidence_from_package"] is not None

    # 2. Non-standard unit symbol (gms instead of g)
    unit_hazard = generate_hazard_violation_explanation(
        clause_reference="Rule 6(1)(f)",
        requirement_title="Net Quantity & SI Units",
        observed_value="Net Wt. 500 gms",
        expected_condition="Standard SI metric symbol 'g' or 'kg'",
        final_status="FAIL"
    )
    assert "Prohibited unit symbol" in unit_hazard["detected_issue"] or "Non-SI" in unit_hazard["detected_issue"]
    assert "Rule 13(1)" in unit_hazard["applicable_rule"]
    assert "Section 8" in unit_hazard["consumer_regulatory_risk"]["regulatory_risk"]

    # 3. Manufacturer Premise Address Missing
    mfg_hazard = generate_hazard_violation_explanation(
        clause_reference="Rule 6(1)(a)",
        requirement_title="Manufacturer / Packer Address",
        observed_value="Manufactured in Mumbai",
        expected_condition="Complete physical address with street and PIN code",
        final_status="FAIL"
    )
    assert "Rule 6(1)(a)" in mfg_hazard["applicable_rule"]
    assert "PIN code" in mfg_hazard["reason_for_non_compliance"]
    assert "District Consumer Disputes Redressal" in mfg_hazard["consumer_regulatory_risk"]["consumer_harm"]


def test_statutory_follow_up_actions_generation():
    # Test for non-compliant inspection with critical violations
    violations = [
        {"requirement_title": "Maximum Retail Price (MRP)", "severity": "CRITICAL", "final_status": "FAIL"},
        {"requirement_title": "Net Quantity & Units", "severity": "CRITICAL", "final_status": "FAIL"}
    ]
    actions = generate_recommended_follow_up_actions(
        compliance_verdict="NON_COMPLIANT",
        violations=violations
    )
    assert len(actions) >= 3
    types = [a["action_type"] for a in actions]
    assert "STATUTORY_NOTICE" in types
    assert "COMPOUNDING_OFFENSE" in types
    assert "SEIZURE_ADVISORY" in types

    # Verify statutory sections
    notice = next(a for a in actions if a["action_type"] == "STATUTORY_NOTICE")
    assert "Section 18" in notice["statutory_section"]
    assert notice["deadline_days"] == 15

    # Test for compliant inspection
    comp_actions = generate_recommended_follow_up_actions(
        compliance_verdict="COMPLIANT",
        violations=[]
    )
    assert any(a["action_type"] == "CERTIFICATE_ISSUED" for a in comp_actions)


def test_rulelens_api_includes_hazard_explanation():
    headers = get_auth_headers()
    
    # Get or create an inspection
    create_res = client.post(
        "/api/inspections",
        headers=headers,
        json={"commodity_name": "Test Atta Pack 5kg", "product_type": "Wheat Flour"}
    )
    assert create_res.status_code == 201
    insp_id = create_res.json()["id"]

    # Add a dummy finding or trigger RuleLens view
    rulelens_res = client.get(f"/api/inspections/{insp_id}/rulelens", headers=headers)
    assert rulelens_res.status_code == 200
    data = rulelens_res.json()
    assert "findings" in data


def test_structured_report_api_endpoint():
    headers = get_auth_headers()
    
    # Create inspection
    create_res = client.post(
        "/api/inspections",
        headers=headers,
        json={"commodity_name": "Premium Tea 250g", "product_type": "Tea"}
    )
    assert create_res.status_code == 201
    insp_id = create_res.json()["id"]

    # Request 9-pillar structured report
    report_res = client.get(f"/api/inspections/{insp_id}/structured-report", headers=headers)
    assert report_res.status_code == 200
    structured = report_res.json()

    # Verify all 9 pillars are present
    assert "product_details" in structured
    assert "extracted_declarations" in structured
    assert "applicable_rules" in structured
    assert "compliance_status" in structured
    assert "detected_violations" in structured
    assert "visual_evidence" in structured
    assert "inspector_verification" in structured
    assert "timestamps" in structured
    assert "recommended_follow_up_actions" in structured

    # Verify specific pillar contents
    assert structured["product_details"]["commodity_name"] == "Premium Tea 250g"
    assert "compliance_rate" in structured["compliance_status"]
    assert len(structured["recommended_follow_up_actions"]) >= 1


def test_pdf_generation_with_hazard_and_followup_sections():
    insp_data = {
        "id": "test_hazard_pdf_01",
        "inspection_number": "INSP-TEST-HAZARD",
        "compliance_verdict": "NON_COMPLIANT",
        "rule_version": "LMPC-2026-RULES",
        "inspector_name": "Officer Test"
    }
    findings = [
        {
            "clause_reference": "Rule 6(1)(e)",
            "requirement_title": "Maximum Retail Price (MRP)",
            "final_status": "FAIL",
            "ai_status": "FAIL",
            "observed_value": "[MISSING]",
            "expected_condition": "MRP in Rs inclusive of all taxes",
            "severity": "CRITICAL"
        }
    ]
    declarations = [
        {"category": "NET_QUANTITY", "raw_text": "Net Wt: 500g", "normalized_value": "500g", "confidence": 0.95}
    ]
    
    pdf_res = generate_inspection_pdf(
        inspection_data=insp_data,
        findings=findings,
        declarations=declarations,
        output_filename="test_hazard_report.pdf"
    )
    
    assert pdf_res["pdf_path"] is not None
    assert os.path.exists(pdf_res["pdf_path"])
    assert len(pdf_res["pdf_sha256"]) == 64
    assert pdf_res["certificate_number"] == "LMPC-CERT-TEST-HAZARD"
