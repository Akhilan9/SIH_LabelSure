import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models import Rule
from backend.app.core.config import settings
from backend.app.rule_engine.evaluator import evaluate_rule

VALID_OPERATORS = {
    "EXISTS", "NOT_EXISTS", "EQUALS", "NOT_EQUALS", "GREATER_THAN",
    "LESS_THAN", "BETWEEN", "REGEX", "UNIT_VALIDATION", "DATE_VALIDATION",
    "COMPOSITE_AND", "COMPOSITE_OR"
}

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"}

REQUIRED_RULE_FIELDS = [
    "rule_id", "rule_version", "clause_reference", "requirement",
    "applicability", "validation_logic", "severity", "effective_from",
    "source_document", "source_url"
]

def validate_rule_definition(rule: Dict[str, Any]) -> List[str]:
    """
    Validates that a rule definition strictly adheres to the Legal Metrology rule specification.
    Returns a list of validation errors (empty if valid).
    """
    errors: List[str] = []
    for field in REQUIRED_RULE_FIELDS:
        if field not in rule or rule[field] is None:
            errors.append(f"Missing mandatory field '{field}'.")
            
    v_logic = rule.get("validation_logic", {})
    if not isinstance(v_logic, dict):
        errors.append("validation_logic must be an object.")
    else:
        op = v_logic.get("operator")
        if not op or op not in VALID_OPERATORS:
            errors.append(f"Invalid or missing operator '{op}'. Must be one of: {', '.join(sorted(VALID_OPERATORS))}")
            
    sev = rule.get("severity")
    if sev and sev not in VALID_SEVERITIES:
        errors.append(f"Invalid severity '{sev}'. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}")
        
    return errors

def load_rules_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Loads and validates rule definitions from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        rules = json.load(f)
        
    if not isinstance(rules, list):
        raise ValueError(f"Rules file {file_path} must contain a JSON array of rule objects.")
        
    for idx, r in enumerate(rules):
        errs = validate_rule_definition(r)
        if errs:
            raise ValueError(f"Rule validation error in {file_path} at index {idx} ({r.get('rule_id', 'UNKNOWN')}): {'; '.join(errs)}")
            
    return rules

def load_all_rule_versions(rules_dir: Optional[Path] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Loads all rule version definitions found in rules/versions directory."""
    target_dir = rules_dir or (settings.RULES_DIR / "versions")
    versions: Dict[str, List[Dict[str, Any]]] = {}
    if not target_dir.exists():
        return versions
        
    for json_file in target_dir.glob("*.json"):
        rules = load_rules_from_file(str(json_file))
        if rules:
            ver = rules[0].get("rule_version", json_file.stem.upper())
            versions[ver] = rules
    return versions

def filter_rules_by_effective_date(rules: List[Dict[str, Any]], inspection_date: str) -> List[Dict[str, Any]]:
    """Filters rules that were active and legally enforceable on the specified inspection date (YYYY-MM-DD)."""
    active_rules = []
    for r in rules:
        eff_from = r.get("effective_from")
        eff_to = r.get("effective_to")
        if eff_from and inspection_date < eff_from:
            continue
        if eff_to and inspection_date > eff_to:
            continue
        active_rules.append(r)
    return active_rules

def load_rules_from_db(
    db: Session,
    target_version: Optional[str] = "LMPC-2026-RULES",
    inspection_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Loads active rules matching target version or effective date from database."""
    query = db.query(Rule).filter(Rule.is_active == True)
    if target_version:
        query = query.filter(Rule.rule_version == target_version)
    records = query.all()
    
    # If target version has no records in DB, fallback to any active rules
    if not records:
        records = db.query(Rule).filter(Rule.is_active == True).all()
        
    rules = []
    for r in records:
        rules.append({
            "rule_id": r.rule_id,
            "rule_version": r.rule_version,
            "clause_reference": r.clause_reference,
            "requirement": r.requirement,
            "applicability": r.applicability,
            "validation_logic": r.validation_logic,
            "severity": r.severity,
            "effective_from": r.effective_from,
            "effective_to": r.effective_to,
            "source_document": r.source_document,
            "source_url": r.source_url,
            "notes": r.notes
        })
        
    if inspection_date:
        rules = filter_rules_by_effective_date(rules, inspection_date)
        
    return rules

def run_compliance_evaluation(
    rules: List[Dict[str, Any]],
    declarations: List[Dict[str, Any]],
    context: Dict[str, Any],
    overall_image_quality: float = 1.0,
    has_blurry_image: bool = False
) -> Tuple[List[Dict[str, Any]], str, Dict[str, int]]:
    """
    Orchestrates deterministic rule evaluation over all applicable statutory rules.
    Computes overall compliance status and findings breakdown:
    - COMPLIANT: All applicable rules are PASS.
    - NON_COMPLIANT: At least one applicable rule is FAIL.
    - REQUIRES_REVIEW: At least one applicable rule is UNCERTAIN (and none are FAIL).
    """
    findings: List[Dict[str, Any]] = []
    summary = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
    
    for rule in rules:
        finding = evaluate_rule(
            rule=rule,
            declarations=declarations,
            context=context,
            overall_image_quality=overall_image_quality,
            has_blurry_image=has_blurry_image
        )
        findings.append(finding)
        status_key = finding["ai_status"].lower()
        if status_key in summary:
            summary[status_key] += 1
            
    # Compute overall compliance verdict
    if summary["fail"] > 0:
        compliance_status = "NON_COMPLIANT"
    elif summary["uncertain"] > 0:
        compliance_status = "REQUIRES_REVIEW"
    elif summary["pass"] > 0:
        compliance_status = "COMPLIANT"
    else:
        compliance_status = "REQUIRES_REVIEW"
        
    return findings, compliance_status, summary
