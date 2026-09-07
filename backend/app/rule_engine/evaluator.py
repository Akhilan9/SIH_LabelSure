import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

LEGAL_METRIC_UNITS = {"g", "kg", "mg", "ml", "l", "m", "cm", "mm", "n", "u"}
ILLEGAL_UNIT_SYMBOLS = {
    "gms": "g",
    "gm": "g",
    "kgs": "kg",
    "ltrs": "l",
    "ltr": "l",
    "ml.": "ml",
    "g.": "g",
    "kg.": "kg"
}

def check_applicability(applicability: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Checks whether a rule is applicable to the given product context."""
    if not applicability:
        return True
        
    # Check commodity categories
    allowed_cats = applicability.get("commodity_categories")
    if allowed_cats and context.get("commodity_category") not in allowed_cats:
        return False
        
    # Check package types
    allowed_packs = applicability.get("package_type")
    if allowed_packs:
        if isinstance(allowed_packs, list):
            if context.get("package_type") not in allowed_packs:
                return False
        elif context.get("package_type") != allowed_packs:
            return False
            
    # Check import status
    req_imported = applicability.get("is_imported")
    if req_imported is not None and bool(context.get("is_imported")) != req_imported:
        return False
        
    # Check food status
    req_food = applicability.get("is_food")
    if req_food is not None and bool(context.get("is_food")) != req_food:
        return False
        
    # Check ecommerce status
    req_ecom = applicability.get("is_ecommerce")
    if req_ecom is not None and bool(context.get("is_ecommerce")) != req_ecom:
        return False
        
    return True

def find_declaration_by_category(
    declarations: List[Dict[str, Any]],
    category: str
) -> Optional[Dict[str, Any]]:
    for d in declarations:
        cat = d.get("category") or d.get("type")
        if cat == category:
            return d
        # Common / Generic name alias
        if category in ("PRODUCT_NAME", "COMMON_GENERIC_NAME") and cat in ("PRODUCT_NAME", "COMMON_GENERIC_NAME"):
            return d
    return None

def evaluate_rule(
    rule: Dict[str, Any],
    declarations: List[Dict[str, Any]],
    context: Dict[str, Any],
    overall_image_quality: float = 1.0,
    has_blurry_image: bool = False
) -> Dict[str, Any]:
    """
    Evaluates a single regulatory rule against extracted declarations and product context.
    Strictly separates AI observation from legal decisions.
    Applies uncertainty model: degraded evidence -> UNCERTAIN, never false FAIL.
    
    Supported Outcomes:
    - PASS: Requirement verified and fulfilled.
    - FAIL: Clear evidence of non-compliance.
    - UNCERTAIN: Image evidence degraded, unreadable, or insufficient.
    - NOT_APPLICABLE: Out of scope for this commodity, context, or effective date.
    """
    rule_id = rule.get("rule_id", "UNKNOWN_RULE")
    rule_version = rule.get("rule_version", "LMPC-2026-RULES")
    clause_ref = rule.get("clause_reference", "General Rule")
    req_title = rule.get("requirement", "Statutory Declaration")
    severity = rule.get("severity", "HIGH")
    
    # 1. Effective Date Check
    inspection_date = context.get("inspection_date")
    effective_from = rule.get("effective_from")
    effective_to = rule.get("effective_to")
    
    if inspection_date:
        if effective_from and inspection_date < effective_from:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "NOT_APPLICABLE",
                "final_status": "NOT_APPLICABLE",
                "severity": severity,
                "confidence": 1.0,
                "explanation": f"Rule {rule_id} was not yet in force on inspection date ({inspection_date}); effective from {effective_from}.",
                "uncertainty_reason": None,
                "observed_value": None,
                "expected_condition": f"Effective from {effective_from}.",
                "evidence_references": []
            }
        if effective_to and inspection_date > effective_to:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "NOT_APPLICABLE",
                "final_status": "NOT_APPLICABLE",
                "severity": severity,
                "confidence": 1.0,
                "explanation": f"Rule {rule_id} expired on {effective_to}; inspection date was {inspection_date}.",
                "uncertainty_reason": None,
                "observed_value": None,
                "expected_condition": f"Effective until {effective_to}.",
                "evidence_references": []
            }
    
    # 2. Applicability Check
    if not check_applicability(rule.get("applicability", {}), context):
        return {
            "rule_id": rule_id,
            "rule_version": rule_version,
            "clause_reference": clause_ref,
            "requirement_title": req_title,
            "ai_status": "NOT_APPLICABLE",
            "final_status": "NOT_APPLICABLE",
            "severity": severity,
            "confidence": 1.0,
            "explanation": f"This requirement ({clause_ref}) is not applicable to {context.get('commodity_category', 'this package')} in the current context.",
            "uncertainty_reason": None,
            "observed_value": None,
            "expected_condition": "Applicable only to specified commodity/package conditions.",
            "evidence_references": []
        }
        
    validation = rule.get("validation_logic", {})
    operator = validation.get("operator", "EXISTS")
    target_field = validation.get("field", "")
    
    # Helper to collect evidence
    def make_evidence(decl: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "image_id": decl.get("source_image_id"),
            "view_type": decl.get("view_type", "LABEL"),
            "bbox": decl.get("bbox", [0, 0, 0, 0]),
            "ocr_snippet": decl.get("raw_text", "")
        }]

    # 3. Operator Evaluation
    if operator == "EXISTS":
        decl = find_declaration_by_category(declarations, target_field)
        # Check composite conditions if any
        if not decl and validation.get("composite_conditions"):
            for cond in validation["composite_conditions"]:
                alt_field = cond.get("field")
                decl = find_declaration_by_category(declarations, alt_field)
                if decl:
                    break
                    
        if decl:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "PASS",
                "final_status": "PASS",
                "severity": severity,
                "confidence": decl.get("confidence", 0.95),
                "explanation": f"Mandatory declaration found on package under {clause_ref}.",
                "uncertainty_reason": None,
                "observed_value": decl.get("raw_text"),
                "expected_condition": f"Declaration of {target_field} must be prominently displayed.",
                "evidence_references": make_evidence(decl)
            }
        else:
            # Declaration missing: Check image quality before concluding FAIL!
            if has_blurry_image or overall_image_quality < 0.55:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "UNCERTAIN",
                    "final_status": "UNCERTAIN",
                    "severity": severity,
                    "confidence": round(overall_image_quality, 2),
                    "explanation": f"Declaration '{target_field}' was not detected. However, photographic evidence has quality warnings (blur or low resolution).",
                    "uncertainty_reason": "Image quality is insufficient for definitive absence determination. Better evidence is required.",
                    "observed_value": "[Not Detected - Evidence Degradation]",
                    "expected_condition": f"Clear evidence showing presence or absence of {target_field}.",
                    "evidence_references": []
                }
            else:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "FAIL",
                    "final_status": "FAIL",
                    "severity": severity,
                    "confidence": 0.95,
                    "explanation": f"Missing mandatory declaration: No '{target_field}' was detected across satisfactory quality label photographs.",
                    "uncertainty_reason": None,
                    "observed_value": "[MISSING]",
                    "expected_condition": f"Mandatory display of {target_field} as per {clause_ref}.",
                    "evidence_references": []
                }

    elif operator == "UNIT_VALIDATION":
        decl = find_declaration_by_category(declarations, "NET_QUANTITY")
        if not decl:
            if has_blurry_image or overall_image_quality < 0.55:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "UNCERTAIN",
                    "final_status": "UNCERTAIN",
                    "severity": severity,
                    "confidence": round(overall_image_quality, 2),
                    "explanation": "Net quantity declaration could not be detected due to insufficient image clarity.",
                    "uncertainty_reason": "Image quality is insufficient for unit validation.",
                    "observed_value": "[Not Detected]",
                    "expected_condition": "Standard metric net quantity declaration.",
                    "evidence_references": []
                }
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": severity,
                "confidence": 0.95,
                "explanation": "Net quantity declaration is missing from package.",
                "uncertainty_reason": None,
                "observed_value": "[MISSING]",
                "expected_condition": "Net quantity must be declared in metric units.",
                "evidence_references": []
            }
            
        norm = decl.get("normalized_value", {})
        unit = (norm.get("unit") or decl.get("unit") or "").lower()
        
        if unit in ILLEGAL_UNIT_SYMBOLS:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": "CRITICAL",
                "confidence": decl.get("confidence", 0.95),
                "explanation": f"Illegal unit symbol '{unit}' used. Section 18 of the Legal Metrology Act and Rule 13 prohibit non-standard abbreviations like '{unit}'. Standard symbol is '{ILLEGAL_UNIT_SYMBOLS.get(unit, 'standard metric symbol')}'.",
                "uncertainty_reason": None,
                "observed_value": decl.get("raw_text"),
                "expected_condition": "Standard legal metric symbol (e.g. 'g', 'kg', 'ml', 'l').",
                "evidence_references": make_evidence(decl)
            }
        elif unit in LEGAL_METRIC_UNITS:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "PASS",
                "final_status": "PASS",
                "severity": severity,
                "confidence": decl.get("confidence", 0.95),
                "explanation": f"Net quantity declaration conforms to standard Legal Metrology metric unit '{unit}' under {clause_ref}.",
                "uncertainty_reason": None,
                "observed_value": decl.get("raw_text"),
                "expected_condition": "Standard legal metric units.",
                "evidence_references": make_evidence(decl)
            }
        else:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": severity,
                "confidence": decl.get("confidence", 0.90),
                "explanation": f"Unrecognized unit of measurement: '{unit}'. Must conform to Legal Metrology Act.",
                "uncertainty_reason": None,
                "observed_value": decl.get("raw_text"),
                "expected_condition": "Legal standard units.",
                "evidence_references": make_evidence(decl)
            }

    elif operator == "DATE_VALIDATION":
        decl = find_declaration_by_category(declarations, target_field)
        if not decl and validation.get("composite_conditions"):
            for cond in validation["composite_conditions"]:
                alt_field = cond.get("field")
                decl = find_declaration_by_category(declarations, alt_field)
                if decl:
                    break
                    
        if decl:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "PASS",
                "final_status": "PASS",
                "severity": severity,
                "confidence": decl.get("confidence", 0.92),
                "explanation": f"Mandatory date declaration '{decl.get('category')}' is declared ({decl.get('raw_text')}).",
                "uncertainty_reason": None,
                "observed_value": decl.get("raw_text"),
                "expected_condition": "Declaration of month and year or expiry.",
                "evidence_references": make_evidence(decl)
            }
        else:
            if has_blurry_image or overall_image_quality < 0.55:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "UNCERTAIN",
                    "final_status": "UNCERTAIN",
                    "severity": severity,
                    "confidence": round(overall_image_quality, 2),
                    "explanation": f"Date declaration '{target_field}' was not detected in degraded images.",
                    "uncertainty_reason": "Image quality is insufficient for date extraction.",
                    "observed_value": "[Not Detected]",
                    "expected_condition": f"Declaration of {target_field}.",
                    "evidence_references": []
                }
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": severity,
                "confidence": 0.95,
                "explanation": f"Missing mandatory date declaration under {clause_ref}.",
                "uncertainty_reason": None,
                "observed_value": "[MISSING]",
                "expected_condition": f"Month/Year of packing or manufacture must be declared.",
                "evidence_references": []
            }

    elif operator == "COMPOSITE_AND":
        conditions = validation.get("composite_conditions", [])
        passed_conditions = []
        failed_conditions = []
        evidences = []
        
        for cond in conditions:
            f = cond.get("field")
            d = find_declaration_by_category(declarations, f)
            if d:
                passed_conditions.append(f)
                evidences.extend(make_evidence(d))
            else:
                failed_conditions.append(f)
                
        if not failed_conditions:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "PASS",
                "final_status": "PASS",
                "severity": severity,
                "confidence": 0.95,
                "explanation": f"All composite requirements ({', '.join(passed_conditions)}) satisfied under {clause_ref}.",
                "uncertainty_reason": None,
                "observed_value": f"Declarations present: {', '.join(passed_conditions)}",
                "expected_condition": f"All required fields ({', '.join([c.get('field') for c in conditions])}) must be present.",
                "evidence_references": evidences
            }
        else:
            if has_blurry_image or overall_image_quality < 0.55:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "UNCERTAIN",
                    "final_status": "UNCERTAIN",
                    "severity": severity,
                    "confidence": round(overall_image_quality, 2),
                    "explanation": f"Could not verify fields ({', '.join(failed_conditions)}) due to image quality limitations.",
                    "uncertainty_reason": "Low image resolution or blur prevented OCR verification.",
                    "observed_value": f"Missing or unverified: {', '.join(failed_conditions)}",
                    "expected_condition": "Clear visibility of all mandatory declarations.",
                    "evidence_references": evidences
                }
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": severity,
                "confidence": 0.95,
                "explanation": f"Composite requirement failure under {clause_ref}: Missing mandatory fields ({', '.join(failed_conditions)}).",
                "uncertainty_reason": None,
                "observed_value": f"Missing: {', '.join(failed_conditions)}",
                "expected_condition": f"All of ({', '.join([c.get('field') for c in conditions])}) must be declared.",
                "evidence_references": evidences
            }

    elif operator == "COMPOSITE_OR":
        conditions = validation.get("composite_conditions", [])
        for cond in conditions:
            f = cond.get("field")
            d = find_declaration_by_category(declarations, f)
            if d:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "PASS",
                    "final_status": "PASS",
                    "severity": severity,
                    "confidence": d.get("confidence", 0.95),
                    "explanation": f"At least one required alternative ({f}) was declared under {clause_ref}.",
                    "uncertainty_reason": None,
                    "observed_value": d.get("raw_text"),
                    "expected_condition": f"At least one of ({', '.join([c.get('field') for c in conditions])}) must be declared.",
                    "evidence_references": make_evidence(d)
                }
                
        if has_blurry_image or overall_image_quality < 0.55:
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "UNCERTAIN",
                "final_status": "UNCERTAIN",
                "severity": severity,
                "confidence": round(overall_image_quality, 2),
                "explanation": "Alternative declarations could not be determined due to image degradation.",
                "uncertainty_reason": "Image quality insufficient.",
                "observed_value": "[Not Detected]",
                "expected_condition": "Clear image showing at least one alternative.",
                "evidence_references": []
            }
        return {
            "rule_id": rule_id,
            "rule_version": rule_version,
            "clause_reference": clause_ref,
            "requirement_title": req_title,
            "ai_status": "FAIL",
            "final_status": "FAIL",
            "severity": severity,
            "confidence": 0.95,
            "explanation": f"None of the required alternative declarations ({', '.join([c.get('field') for c in conditions])}) were found.",
            "uncertainty_reason": None,
            "observed_value": "[MISSING]",
            "expected_condition": f"At least one of ({', '.join([c.get('field') for c in conditions])}) must be present.",
            "evidence_references": []
        }

    elif operator == "REGEX":
        pattern = validation.get("pattern", ".*")
        decl = find_declaration_by_category(declarations, target_field)
        if decl:
            text = decl.get("raw_text", "")
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "PASS",
                    "final_status": "PASS",
                    "severity": severity,
                    "confidence": decl.get("confidence", 0.95),
                    "explanation": f"Pattern matched for '{target_field}'.",
                    "uncertainty_reason": None,
                    "observed_value": text,
                    "expected_condition": f"Must match pattern '{pattern}'.",
                    "evidence_references": make_evidence(decl)
                }
            else:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "FAIL",
                    "final_status": "FAIL",
                    "severity": severity,
                    "confidence": decl.get("confidence", 0.90),
                    "explanation": f"Pattern mismatch for '{target_field}'. Observed: '{text}'.",
                    "uncertainty_reason": None,
                    "observed_value": text,
                    "expected_condition": f"Must match pattern '{pattern}'.",
                    "evidence_references": make_evidence(decl)
                }
        else:
            if has_blurry_image or overall_image_quality < 0.55:
                return {
                    "rule_id": rule_id,
                    "rule_version": rule_version,
                    "clause_reference": clause_ref,
                    "requirement_title": req_title,
                    "ai_status": "UNCERTAIN",
                    "final_status": "UNCERTAIN",
                    "severity": severity,
                    "confidence": round(overall_image_quality, 2),
                    "explanation": f"Declaration '{target_field}' could not be verified due to image blur.",
                    "uncertainty_reason": "Insufficient image quality for regex pattern evaluation.",
                    "observed_value": "[Not Detected]",
                    "expected_condition": f"Clear declaration matching '{pattern}'.",
                    "evidence_references": []
                }
            return {
                "rule_id": rule_id,
                "rule_version": rule_version,
                "clause_reference": clause_ref,
                "requirement_title": req_title,
                "ai_status": "FAIL",
                "final_status": "FAIL",
                "severity": severity,
                "confidence": 0.95,
                "explanation": f"Missing declaration '{target_field}'.",
                "uncertainty_reason": None,
                "observed_value": "[MISSING]",
                "expected_condition": f"Must match pattern '{pattern}'.",
                "evidence_references": []
            }

    # Fallback for unhandled operators
    return {
        "rule_id": rule_id,
        "rule_version": rule_version,
        "clause_reference": clause_ref,
        "requirement_title": req_title,
        "ai_status": "UNCERTAIN",
        "final_status": "UNCERTAIN",
        "severity": severity,
        "confidence": 0.5,
        "explanation": f"Rule logic for operator '{operator}' marked as unverified.",
        "uncertainty_reason": "UNVERIFIED_RULE: Complex legal condition requires human inspector adjudication.",
        "observed_value": None,
        "expected_condition": "Inspector discretion.",
        "evidence_references": []
    }
