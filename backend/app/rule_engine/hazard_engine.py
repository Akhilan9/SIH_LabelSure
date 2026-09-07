import re
from typing import Dict, Any, List, Optional

def generate_hazard_violation_explanation(
    clause_reference: str,
    requirement_title: str,
    observed_value: Optional[str],
    expected_condition: str,
    final_status: str,
    context: Optional[Dict[str, Any]] = None,
    ocr_snippet: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a deterministic 5-step statutory explanation chain expanding RuleLens:
    1. Detected Issue
    2. Applicable Rule
    3. Reason for Non-Compliance
    4. Potential Consumer & Regulatory Risk (Consumer Harm + Regulatory Risk)
    5. Evidence from Package
    """
    context = context or {}
    status_upper = (final_status or "UNCERTAIN").upper()
    clause_clean = clause_reference or "Rule 6"
    title_lower = (requirement_title or "").lower()
    obs = observed_value or "[Not Detected]"

    # If the finding passed, provide compliant validation explanation
    if status_upper == "PASS":
        return {
            "detected_issue": f"No violation detected. The statutory requirement for {requirement_title} is satisfied.",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011/2026.",
            "reason_for_non_compliance": "Fully compliant. The package displays the mandatory declaration in accordance with prescribed format, font height, and placement.",
            "consumer_regulatory_risk": {
                "consumer_harm": "None. Consumer rights to fair transparency and accurate commodity information are preserved.",
                "regulatory_risk": "None. Package conforms to statutory metrological standards."
            },
            "evidence_from_package": f"Verified declaration on packaging: '{obs}'. Bounding box confirmed on label face."
        }

    # 1. Maximum Retail Price (MRP) & Unit Sale Price (USP)
    if "mrp" in title_lower or "retail price" in title_lower:
        return {
            "detected_issue": f"Maximum Retail Price declaration is {obs.lower() if obs else 'missing or defective'} without statutory 'inclusive of all taxes' mandatory text.",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011 read with Section 18 of the Legal Metrology Act, 2009.",
            "reason_for_non_compliance": "Rule 6(1)(e) strictly mandates that the retail sale price must be unambiguously declared in Indian currency (₹ or Rs.) followed by 'inclusive of all taxes'. Sale price cannot be left ambiguous, omitted, or smudged.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Consumers are exposed to arbitrary price gouging and illicit overcharging at point of sale. Deprives buyers of understanding the legal price ceiling and embedded taxation.",
                "regulatory_risk": "Punishable under Section 36(1) of the Legal Metrology Act, 2009 with fines up to ₹25,000 (1st offence), ₹50,000 (2nd offence), and up to ₹1,00,000 or imprisonment for subsequent contraventions."
            },
            "evidence_from_package": f"Observed package text: '{obs}'. Search across all captured faces confirmed absence of compliant MRP declaration."
        }

    if "unit sale price" in title_lower or "usp" in title_lower:
        return {
            "detected_issue": "Unit Sale Price (USP per gram / kg / ml / litre) is absent on a package exceeding 1 unit / 100g.",
            "applicable_rule": f"{clause_clean} (amendment 2022/2026) of Legal Metrology (Packaged Commodities) Rules.",
            "reason_for_non_compliance": "When pre-packaged commodities are sold in non-standard or fractional quantities, declaration of unit cost (e.g., ₹/g or ₹/kg) is mandatory to enable transparent price-per-quantity comparison.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Consumers fall victim to 'shrinkflation' and mathematical confusion where reduced pack weights conceal price hikes compared to competitor brands.",
                "regulatory_risk": "Non-compliance with Department of Consumer Affairs anti-shrinkflation mandate; triggers compounding notices under Section 48."
            },
            "evidence_from_package": f"Package declares total price '{obs}', but no accompanying Unit Sale Price (USP) rate was detected."
        }

    # 2. Net Quantity & Non-Standard Units
    if "net quantity" in title_lower or "units" in title_lower or "weight" in title_lower:
        has_illegal_symbol = any(sym in obs.lower() for sym in ["gms", "gm", "kgs", "ltrs", "ltr", "ml."])
        if has_illegal_symbol:
            return {
                "detected_issue": f"Prohibited unit symbol used in net quantity declaration ('{obs}'). Non-SI metric abbreviation detected.",
                "applicable_rule": f"{clause_clean} & Rule 13(1) read with Schedule II of Legal Metrology (Packaged Commodities) Rules, 2011.",
                "reason_for_non_compliance": "Rule 13 strictly prohibits non-standard abbreviations such as 'gms', 'gm', 'kgs', 'ltrs'. Only certified SI metric unit symbols ('g', 'kg', 'ml', 'l') without pluralization 's' or trailing periods are legally permissible.",
                "consumer_regulatory_risk": {
                    "consumer_harm": "Causes confusion in weight denominations and violates standard metric literacy. Informal notations facilitate deceptive fractional packaging.",
                    "regulatory_risk": "Direct breach of the National Measurement System established under Section 8 of the Legal Metrology Act, 2009."
                },
                "evidence_from_package": f"OCR extraction detected unlawful unit symbol '{obs}' in primary quantity statement."
            }
        return {
            "detected_issue": f"Net quantity declaration is absent or fails minimum numeral height specifications ('{obs}').",
            "applicable_rule": f"{clause_clean} & Rule 7 Table I (Minimum Height of Numerals) of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "Net quantity must appear conspicuously on the Principal Display Panel satisfying font height thresholds (minimum 2mm to 6mm depending on pack weight bracket).",
            "consumer_regulatory_risk": {
                "consumer_harm": "Purchaser cannot discern the true volume or weight of commodity being bought; visual deception regarding physical package volume.",
                "regulatory_risk": "Misleading trade declaration punishable under Section 36 of Legal Metrology Act, 2009."
            },
            "evidence_from_package": f"Extracted value: '{obs}'. Numeral height does not satisfy mandatory Rule 7 schedule."
        }

    # 3. Manufacturer, Packer & Importer Identification
    if "manufacturer" in title_lower or "packer" in title_lower or "importer" in title_lower or "address" in title_lower:
        return {
            "detected_issue": f"Manufacturer / Packer / Importer premises address is incomplete or missing ('{obs}').",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "Rule 6(1)(a) mandates the complete physical address of the manufacturing or packaging premises, including building/plot number, street name, city, state, and valid postal PIN code. Generic names or PO Box numbers alone are legally invalid.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Deprives consumers of the legal capacity to serve statutory grievance notices, seek refunds, or initiate complaints in District Consumer Disputes Redressal Commissions.",
                "regulatory_risk": "Untraceable entities evade GST, metrological inspection, product recall directives, and statutory audit."
            },
            "evidence_from_package": f"Observed text snippet: '{obs}'. Lacks mandatory complete premise details or postal PIN code."
        }

    # 4. Country of Origin
    if "country of origin" in title_lower or "origin" in title_lower:
        return {
            "detected_issue": "Country of Origin declaration is missing on an imported or pre-packaged commodity.",
            "applicable_rule": f"{clause_clean} and proviso to Rule 6(1)(a) of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "Mandatory requirement to prominently declare the country where the commodity was manufactured, packed, or assembled for trade transparency.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Violates the consumer's right to information regarding provenance, source quality, and trade origin.",
                "regulatory_risk": "Circumvention of customs verification, Free Trade Agreement (FTA) rules of origin, and Department for Promotion of Industry and Internal Trade (DPIIT) trade compliance."
            },
            "evidence_from_package": f"Observed text: '{obs}'. No conspicuous Country of Origin statement detected across package panels."
        }

    # 5. Consumer Care Details
    if "consumer care" in title_lower or "grievance" in title_lower or "complaint" in title_lower:
        return {
            "detected_issue": f"Consumer Care contact details (email / telephone / address) are absent or incomplete ('{obs}').",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "Every pre-packaged commodity must prominently mention the name, address, telephone number, and email address of the person or office to be contacted in case of consumer complaints.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Directly disenfranchises consumers when encountering adulterated, spoiled, defective, or underweight packaged commodities.",
                "regulatory_risk": "Contravention of consumer grievance accessibility under the Consumer Protection Act, 2019 and LMPC enforcement mandates."
            },
            "evidence_from_package": f"Extracted value: '{obs}'. Lacks mandatory functioning consumer care helpline or email."
        }

    # 6. Month & Year of Manufacture / Packing / Expiry
    if "date" in title_lower or "month" in title_lower or "year" in title_lower or "expiry" in title_lower or "manufacture" in title_lower:
        return {
            "detected_issue": f"Month and year of manufacture, packaging, or import is absent or unreadable ('{obs}').",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "Rule 6(1)(d) mandates clear declaration of month and year in numerical (e.g. 03/2026) or alphabetical (e.g. March 2026) format so consumers can evaluate commodity freshness and shelf-life.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Exposes consumers to the health hazard of unknowingly purchasing expired, rancid, or degraded products.",
                "regulatory_risk": "Enables illicit relabelling and re-drumming of aged or expired stock by unethical distributors."
            },
            "evidence_from_package": f"Observed package marking: '{obs}'. No clear manufacturing/packing date was deciphered."
        }

    # 7. Common or Generic Commodity Name
    if "generic" in title_lower or "commodity" in title_lower or "name" in title_lower:
        return {
            "detected_issue": f"Generic or common commodity identity is absent or obscured by brand imagery ('{obs}').",
            "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011.",
            "reason_for_non_compliance": "The true identity of the packaged commodity must appear conspicuously on the Principal Display Panel so the nature of the product is immediately clear.",
            "consumer_regulatory_risk": {
                "consumer_harm": "Consumers are misled into purchasing synthetic, blended, or imitation substitutes masquerading as pure goods.",
                "regulatory_risk": "Deceptive marketing and misbranding under Section 18 of the Legal Metrology Act, 2009."
            },
            "evidence_from_package": f"Extracted text: '{obs}'. Brand trademark is present but common commodity name is omitted."
        }

    # Generic Fallback
    return {
        "detected_issue": f"Statutory requirement '{requirement_title}' evaluated to {status_upper} ('{obs}').",
        "applicable_rule": f"{clause_clean} of Legal Metrology (Packaged Commodities) Rules, 2011/2026.",
        "reason_for_non_compliance": f"Package condition does not satisfy statutory benchmark: expected '{expected_condition}'. Observed value '{obs}' is legally defective.",
        "consumer_regulatory_risk": {
            "consumer_harm": "Lack of statutory clarity compromises consumer transparency and fair market transaction standards.",
            "regulatory_risk": "Technical contravention under Section 18 of the Legal Metrology Act, 2009."
        },
        "evidence_from_package": f"Package observation: '{obs}'. Evaluated against expected condition: '{expected_condition}'."
    }


def generate_recommended_follow_up_actions(
    compliance_verdict: str,
    violations: List[Dict[str, Any]],
    product_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generates deterministic legal follow-up actions and statutory enforcement advisories
    based on the Legal Metrology Act, 2009.
    """
    actions: List[Dict[str, Any]] = []
    verdict = (compliance_verdict or "PENDING").upper()

    if verdict == "COMPLIANT" or not violations:
        actions.append({
            "action_type": "CERTIFICATE_ISSUED",
            "statutory_section": "Rule 6 & Section 18 (Compliant Verification)",
            "title": "Issue Clean Statutory Compliance Certificate",
            "description": "Package satisfies all mandatory legal metrology declarations. Commodity cleared for open retail and commercial sale.",
            "penalty_estimate": "NIL (Full Compliance)",
            "deadline_days": 0,
            "priority": "LOW"
        })
        actions.append({
            "action_type": "PERIODIC_AUDIT",
            "statutory_section": "Routine Market Surveillance",
            "title": "Schedule Routine Surveillance Audit",
            "description": "Re-sample from manufacturing lot during standard quarterly market inspection cycles.",
            "penalty_estimate": "NIL",
            "deadline_days": 90,
            "priority": "LOW"
        })
        return actions

    # Count violations by severity
    critical_violations = [v for v in violations if v.get("severity") == "CRITICAL" or v.get("final_status") == "FAIL"]
    mrp_violation = any("mrp" in (v.get("requirement_title") or "").lower() for v in critical_violations)
    net_qty_violation = any("net quantity" in (v.get("requirement_title") or "").lower() for v in critical_violations)
    mfg_violation = any("manufacturer" in (v.get("requirement_title") or "").lower() for v in critical_violations)

    # 1. Statutory Notice under Section 18
    actions.append({
        "action_type": "STATUTORY_NOTICE",
        "statutory_section": "Section 18 & Section 36(1) of Legal Metrology Act, 2009",
        "title": "Issue Show-Cause Notice to Manufacturer / Packer",
        "description": f"Serve formal statutory notice detailing {len(critical_violations)} detected declaration defect(s). Mandate submission of explanation within 15 calendar days.",
        "penalty_estimate": "Show-Cause Notice (Pre-Compounding)",
        "deadline_days": 15,
        "priority": "HIGH"
    })

    # 2. Compounding Assessment under Section 48
    if len(critical_violations) >= 2 or mrp_violation or net_qty_violation:
        compounding_range = "₹25,000 (First Offence) to ₹50,000 (Second Offence)"
        actions.append({
            "action_type": "COMPOUNDING_OFFENSE",
            "statutory_section": "Section 48 (Compounding of Offences)",
            "title": "Compounding Assessment & Fine Recovery",
            "description": "Offer compounding option under Section 48 to avoid court litigation, subject to formal written admission of defect and payment of statutory fine to the State Legal Metrology treasury.",
            "penalty_estimate": compounding_range,
            "deadline_days": 30,
            "priority": "HIGH"
        })
    else:
        actions.append({
            "action_type": "COMPOUNDING_OFFENSE",
            "statutory_section": "Section 48 (Compounding of Offences)",
            "title": "Administrative Rectification & Minor Compounding",
            "description": "Issue compounding assessment for minor label deficiency with statutory fine of ₹10,000.",
            "penalty_estimate": "₹10,000 to ₹25,000",
            "deadline_days": 30,
            "priority": "MEDIUM"
        })

    # 3. Seizure / Shelf Withdrawal Advisory under Section 15
    if net_qty_violation or (mrp_violation and len(critical_violations) >= 3):
        actions.append({
            "action_type": "SEIZURE_ADVISORY",
            "statutory_section": "Section 15 (Power of Search, Seizure and Forfeiture)",
            "title": "Shelf Seizure and Commercial Stop-Sale Order",
            "description": "Issue Form 1 Seizure Order impounding non-compliant packaging lots from the retail establishment to protect consumers from deceptive quantity or price manipulation.",
            "penalty_estimate": "Seizure of Entire In-Store Lot",
            "deadline_days": 1,
            "priority": "CRITICAL"
        })
    else:
        actions.append({
            "action_type": "RECTIFICATION_DIRECTIVE",
            "statutory_section": "Rule 33 (Adjudication & Correction)",
            "title": "Over-Sticker Rectification Clearance Order",
            "description": "Permit manufacturer/retailer to apply certified corrective over-stickers rectifying the missing declarations before goods can be returned to active retail shelves.",
            "penalty_estimate": "Pre-Sale Rectification Required",
            "deadline_days": 15,
            "priority": "MEDIUM"
        })

    # 4. Mandatory Re-Inspection Timeline
    actions.append({
        "action_type": "RE_INSPECTION",
        "statutory_section": "Section 16 (Inspector Audit Verification)",
        "title": "Mandatory On-Site Re-Inspection",
        "description": "Schedule physical re-inspection by designated Legal Metrology Officer to verify complete rectification of the defect or impoundment compliance.",
        "penalty_estimate": "NIL (Follow-up Audit)",
        "deadline_days": 21,
        "priority": "MEDIUM"
    })

    return actions
