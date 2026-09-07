import os
import pytest
from pathlib import Path
from backend.app.rule_engine.evaluator import evaluate_rule
from backend.app.rule_engine.engine import (
    load_rules_from_file,
    load_all_rule_versions,
    validate_rule_definition,
    filter_rules_by_effective_date,
    run_compliance_evaluation
)
from backend.app.core.config import settings

# -----------------------------------------------------------------
# Sample Statutory Rule Fixtures
# -----------------------------------------------------------------
mrp_rule = {
    "rule_id": "LMPC_2026_R06_1_E_MRP",
    "rule_version": "LMPC-2026-RULES",
    "clause_reference": "Rule 6(1)(e)",
    "requirement": "Maximum Retail Price (MRP) inclusive of all taxes",
    "applicability": {
        "package_type": ["SINGLE_PRE_PACKAGED", "MULTI_PIECE"]
    },
    "validation_logic": {
        "field": "MRP",
        "operator": "EXISTS"
    },
    "severity": "CRITICAL",
    "effective_from": "2011-04-01",
    "effective_to": None,
    "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
    "source_url": "https://consumeraffairs.nic.in"
}

net_qty_rule = {
    "rule_id": "LMPC_2026_R06_1_C_NET_QTY",
    "rule_version": "LMPC-2026-RULES",
    "clause_reference": "Rule 6(1)(c) & Rule 13",
    "requirement": "Net quantity in standard metric units",
    "applicability": {
        "package_type": ["SINGLE_PRE_PACKAGED"]
    },
    "validation_logic": {
        "field": "NET_QUANTITY",
        "operator": "UNIT_VALIDATION"
    },
    "severity": "CRITICAL",
    "effective_from": "2011-04-01",
    "effective_to": None,
    "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
    "source_url": "https://consumeraffairs.nic.in"
}

imported_origin_rule = {
    "rule_id": "LMPC_2026_R06_1_A_IMP",
    "rule_version": "LMPC-2026-RULES",
    "clause_reference": "Rule 6(1)(a)",
    "requirement": "Country of origin and importer details for imported commodity",
    "applicability": {
        "is_imported": True
    },
    "validation_logic": {
        "field": "IMPORTER",
        "operator": "COMPOSITE_AND",
        "composite_conditions": [
            {"field": "IMPORTER", "operator": "EXISTS"},
            {"field": "COUNTRY_OF_ORIGIN", "operator": "EXISTS"}
        ]
    },
    "severity": "CRITICAL",
    "effective_from": "2011-04-01",
    "effective_to": None,
    "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
    "source_url": "https://consumeraffairs.nic.in"
}

usp_amendment_rule = {
    "rule_id": "LMPC_2021_R06_11_USP",
    "rule_version": "LMPC-2021-AMENDMENT",
    "clause_reference": "Rule 6(11)",
    "requirement": "Unit Sale Price (USP) declaration in Rs. per g/ml/piece",
    "applicability": {
        "package_type": ["SINGLE_PRE_PACKAGED"]
    },
    "validation_logic": {
        "field": "UNIT_SALE_PRICE",
        "operator": "EXISTS"
    },
    "severity": "HIGH",
    "effective_from": "2022-12-01",
    "effective_to": None,
    "source_document": "Legal Metrology (Packaged Commodities) Amendment Rules, 2021 (GSR 779(E))",
    "source_url": "https://consumeraffairs.nic.in"
}

ecom_rule = {
    "rule_id": "LMPC_2017_R06_10_ECOM",
    "rule_version": "LMPC-2017-AMENDMENT",
    "clause_reference": "Rule 6(10)",
    "requirement": "E-Commerce entity mandatory display of declarations",
    "applicability": {
        "is_ecommerce": True
    },
    "validation_logic": {
        "field": "COMMON_GENERIC_NAME",
        "operator": "EXISTS"
    },
    "severity": "CRITICAL",
    "effective_from": "2018-01-01",
    "effective_to": None,
    "source_document": "Legal Metrology (Packaged Commodities) Amendment Rules, 2017 (GSR 629(E))",
    "source_url": "https://consumeraffairs.nic.in"
}

# -----------------------------------------------------------------
# 1. Test Case: Valid Declaration (PASS)
# -----------------------------------------------------------------
def test_valid_declaration_pass():
    declarations = [
        {"type": "MRP", "raw_text": "MRP Rs. 299.00 incl. of all taxes", "confidence": 0.98}
    ]
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_imported": False, "inspection_date": "2026-03-15"}
    res = evaluate_rule(mrp_rule, declarations, context)
    assert res["ai_status"] == "PASS"
    assert res["final_status"] == "PASS"
    assert res["severity"] == "CRITICAL"
    assert "Rule 6(1)(e)" in res["clause_reference"]
    assert len(res["evidence_references"]) > 0

# -----------------------------------------------------------------
# 2. Test Case: Missing Declaration on Clear Image (FAIL)
# -----------------------------------------------------------------
def test_missing_declaration_clear_image_fail():
    declarations = [
        {"type": "NET_QUANTITY", "raw_text": "1 kg", "confidence": 0.95}
    ]
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_imported": False, "inspection_date": "2026-03-15"}
    # Image quality is crisp (0.95), no blur -> absence is confirmed FAIL
    res = evaluate_rule(mrp_rule, declarations, context, overall_image_quality=0.95, has_blurry_image=False)
    assert res["ai_status"] == "FAIL"
    assert res["final_status"] == "FAIL"
    assert "Missing mandatory declaration" in res["explanation"]
    assert res["observed_value"] == "[MISSING]"

# -----------------------------------------------------------------
# 3. Test Case: Invalid Declaration (Illegal Unit Symbol -> FAIL)
# -----------------------------------------------------------------
def test_invalid_declaration_illegal_unit_fail():
    declarations = [
        {
            "type": "NET_QUANTITY",
            "raw_text": "Net Weight: 500 gms",
            "unit": "gms",
            "normalized_value": {"value": 500.0, "unit": "gms"},
            "confidence": 0.96
        }
    ]
    context = {"package_type": "SINGLE_PRE_PACKAGED", "inspection_date": "2026-03-15"}
    res = evaluate_rule(net_qty_rule, declarations, context)
    assert res["ai_status"] == "FAIL"
    assert res["final_status"] == "FAIL"
    assert "Illegal unit symbol 'gms'" in res["explanation"]
    assert "Rule 13" in res["clause_reference"] or "Rule 13" in res["explanation"]

# -----------------------------------------------------------------
# 4. Test Case: Non-Applicable Declaration (NOT_APPLICABLE)
# -----------------------------------------------------------------
def test_non_applicable_declaration_domestic_product():
    declarations = [
        {"type": "MANUFACTURER", "raw_text": "Mfg by Apex Agro, Delhi", "confidence": 0.95}
    ]
    # Domestic product context (is_imported: False)
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_imported": False, "inspection_date": "2026-03-15"}
    res = evaluate_rule(imported_origin_rule, declarations, context)
    assert res["ai_status"] == "NOT_APPLICABLE"
    assert res["final_status"] == "NOT_APPLICABLE"
    assert "not applicable" in res["explanation"].lower()

def test_non_applicable_ecommerce_rule_on_physical_package():
    declarations = []
    # Physical retail context (is_ecommerce: False)
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_ecommerce": False, "inspection_date": "2026-03-15"}
    res = evaluate_rule(ecom_rule, declarations, context)
    assert res["ai_status"] == "NOT_APPLICABLE"
    assert res["final_status"] == "NOT_APPLICABLE"

# -----------------------------------------------------------------
# 5. Test Case: Insufficient Evidence / Degraded Image (UNCERTAIN)
# -----------------------------------------------------------------
def test_insufficient_evidence_blurry_image_yields_uncertain():
    declarations = []
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_imported": False, "inspection_date": "2026-03-15"}
    # Degraded image quality: has_blurry_image=True and low quality score
    res = evaluate_rule(mrp_rule, declarations, context, overall_image_quality=0.40, has_blurry_image=True)
    assert res["ai_status"] == "UNCERTAIN"
    assert res["final_status"] == "UNCERTAIN"
    assert res["uncertainty_reason"] is not None
    assert "Image quality is insufficient" in res["uncertainty_reason"]
    assert res["observed_value"] == "[Not Detected - Evidence Degradation]"

# -----------------------------------------------------------------
# 6. Test Case: Different Effective Dates (Date Temporal Selection)
# -----------------------------------------------------------------
def test_different_effective_dates_usp_rule():
    declarations = []
    
    # Scenario A: Inspection conducted on 2021-06-15 (BEFORE 2021 amendment took effect on 2022-12-01)
    context_old = {"package_type": "SINGLE_PRE_PACKAGED", "inspection_date": "2021-06-15"}
    res_old = evaluate_rule(usp_amendment_rule, declarations, context_old, overall_image_quality=0.95)
    assert res_old["final_status"] == "NOT_APPLICABLE"
    assert "not yet in force" in res_old["explanation"]

    # Scenario B: Inspection conducted on 2026-02-20 (AFTER USP became mandatory)
    context_new = {"package_type": "SINGLE_PRE_PACKAGED", "inspection_date": "2026-02-20"}
    res_new = evaluate_rule(usp_amendment_rule, declarations, context_new, overall_image_quality=0.95)
    assert res_new["final_status"] == "FAIL"
    assert "Missing mandatory declaration" in res_new["explanation"]

# -----------------------------------------------------------------
# 7. Test Case: Schema Validation & Rule Loading from Files
# -----------------------------------------------------------------
def test_rule_schema_validation_and_loading():
    rules_dir = Path("rules/versions")
    assert rules_dir.exists(), "rules/versions directory must exist"
    
    loaded_versions = load_all_rule_versions(rules_dir)
    assert len(loaded_versions) >= 4, f"Expected at least 4 rule version sets, got {len(loaded_versions)}"
    
    # Validate each loaded rule has zero schema errors
    total_rules = 0
    for ver_name, rule_list in loaded_versions.items():
        assert len(rule_list) > 0
        for r in rule_list:
            total_rules += 1
            errs = validate_rule_definition(r)
            assert len(errs) == 0, f"Rule {r.get('rule_id')} has schema errors: {errs}"
            assert r["effective_from"] is not None
            assert r["source_document"] is not None
            assert r["source_url"] is not None
            
    assert total_rules >= 15

# -----------------------------------------------------------------
# 8. Test Case: Compliance Evaluation Orchestration
# -----------------------------------------------------------------
def test_full_compliance_evaluation_orchestration():
    rules = [mrp_rule, net_qty_rule, imported_origin_rule]
    declarations = [
        {"type": "MRP", "raw_text": "MRP Rs. 100.00 incl. of all taxes", "confidence": 0.98},
        {"type": "NET_QUANTITY", "raw_text": "100 g", "unit": "g", "normalized_value": {"unit": "g"}, "confidence": 0.97}
    ]
    context = {"package_type": "SINGLE_PRE_PACKAGED", "is_imported": False, "inspection_date": "2026-03-15"}
    
    findings, status, summary = run_compliance_evaluation(
        rules=rules,
        declarations=declarations,
        context=context,
        overall_image_quality=0.95
    )
    
    assert status == "COMPLIANT"
    assert summary["pass"] == 2
    assert summary["fail"] == 0
    assert summary["not_applicable"] == 1
    assert len(findings) == 3
