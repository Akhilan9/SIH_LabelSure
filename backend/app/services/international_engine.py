import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.logger import logger

# Base directories
BASE_DIR = Path(__file__).resolve().parents[3]
INTERNATIONAL_RULES_DIR = BASE_DIR / "rules" / "international"
BANNED_SUBSTANCES_FILE = BASE_DIR / "rules" / "banned_substances" / "global_bans.json"

# In-memory caches
_JURISDICTIONS_CACHE: Dict[str, Dict[str, Any]] = {}
_GLOBAL_BANS_CACHE: Optional[Dict[str, Any]] = None


def get_global_bans_database() -> Dict[str, Any]:
    """Load and cache the global bans database from JSON."""
    global _GLOBAL_BANS_CACHE
    if _GLOBAL_BANS_CACHE is None:
        if not BANNED_SUBSTANCES_FILE.exists():
            logger.error(f"Global bans file not found at {BANNED_SUBSTANCES_FILE}")
            return {"version": "1.0", "substances": []}
        try:
            with open(BANNED_SUBSTANCES_FILE, "r", encoding="utf-8") as f:
                _GLOBAL_BANS_CACHE = json.load(f)
        except Exception as e:
            logger.error(f"Error loading global bans database: {e}")
            return {"version": "1.0", "substances": []}
    return _GLOBAL_BANS_CACHE


def get_available_jurisdictions() -> List[Dict[str, Any]]:
    """Retrieve metadata of all available international jurisdictions."""
    jurisdictions = []
    if not INTERNATIONAL_RULES_DIR.exists():
        return jurisdictions

    for file_path in INTERNATIONAL_RULES_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                jurisdictions.append({
                    "jurisdiction_id": data.get("jurisdiction_id"),
                    "country_name": data.get("country_name"),
                    "flag_emoji": data.get("flag_emoji", "🌐"),
                    "regulatory_bodies": data.get("regulatory_bodies", []),
                    "governing_acts": data.get("governing_acts", []),
                    "rules_count": len(data.get("requirements", []))
                })
        except Exception as e:
            logger.error(f"Failed to read jurisdiction file {file_path}: {e}")

    # Sort predictably: USA, EU, GBR, AUS, GCC
    order = {"USA": 1, "EU": 2, "GBR": 3, "AUS": 4, "GCC": 5}
    jurisdictions.sort(key=lambda x: order.get(x["jurisdiction_id"], 99))
    return jurisdictions


def get_jurisdiction_rules(jurisdiction_id: str) -> Optional[Dict[str, Any]]:
    """Get full requirements specification for a given jurisdiction."""
    global _JURISDICTIONS_CACHE
    jid = jurisdiction_id.upper().strip()
    if jid in _JURISDICTIONS_CACHE:
        return _JURISDICTIONS_CACHE[jid]

    if not INTERNATIONAL_RULES_DIR.exists():
        return None

    for file_path in INTERNATIONAL_RULES_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("jurisdiction_id", "").upper() == jid:
                    _JURISDICTIONS_CACHE[jid] = data
                    return data
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
    return None


def scan_text_for_banned_substances(text: str, target_jurisdiction_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans free text (ingredients, OCR transcript, product name) for globally banned/restricted substances.
    Returns matches with full country-specific citations, health hazards, and ban statuses.
    """
    if not text or not text.strip():
        return []

    db = get_global_bans_database()
    substances = db.get("substances", [])
    detected_items: List[Dict[str, Any]] = []

    clean_text = text.lower()

    for item in substances:
        canonical = item.get("canonical_name", "")
        aliases = item.get("aliases", [])
        
        # Build comprehensive search terms
        search_terms = set()
        for t in [canonical] + aliases:
            if not t or len(t.strip()) < 2:
                continue
            search_terms.add(t.strip())
            # If term has parenthetical (e.g. "Brominated Vegetable Oil (BVO)"), add both parts
            if "(" in t and ")" in t:
                base_part = re.sub(r'\(.*?\)', '', t).strip()
                if len(base_part) >= 2:
                    search_terms.add(base_part)
                for inner in re.findall(r'\((.*?)\)', t):
                    if len(inner.strip()) >= 2:
                        search_terms.add(inner.strip())

        matched_term = None
        for term in sorted(search_terms, key=len, reverse=True):
            pattern = r'\b' + re.escape(term.lower()) + r'\b'
            if re.search(pattern, clean_text):
                matched_term = term
                break

        if matched_term:
            all_bans = item.get("bans", [])
            # Filter bans by target jurisdiction if specified, but include others for context
            target_ban = None
            if target_jurisdiction_id:
                for b in all_bans:
                    if b.get("jurisdiction_id", "").upper() == target_jurisdiction_id.upper():
                        target_ban = b
                        break

            detected_items.append({
                "substance_id": item.get("substance_id"),
                "canonical_name": canonical,
                "matched_term": matched_term,
                "category": item.get("category"),
                "description": item.get("description"),
                "allowed_in_india": item.get("allowed_in_india", False),
                "indian_status_note": item.get("indian_status_note", ""),
                "is_banned_in_target": (target_ban is not None),
                "target_ban_detail": target_ban,
                "all_bans": all_bans,
                "total_countries_banned": len(all_bans)
            })

    return detected_items


def compare_product_with_jurisdiction(
    jurisdiction_id: str,
    declarations: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
    raw_ocr_text: str = ""
) -> Dict[str, Any]:
    """
    Compares Indian Legal Metrology label declarations against the chosen international jurisdiction.
    Returns:
    - Compliance Matrix with rule-by-rule diff
    - Export readiness score (0 - 100)
    - Actionable modifications required for export
    - Banned substance warnings with legal citations and health risks
    """
    jurisdiction_data = get_jurisdiction_rules(jurisdiction_id)
    if not jurisdiction_data:
        raise ValueError(f"Unsupported jurisdiction ID: '{jurisdiction_id}'")

    jid = jurisdiction_data.get("jurisdiction_id", "UNKNOWN")
    country_name = jurisdiction_data.get("country_name", "International")
    requirements = jurisdiction_data.get("requirements", [])

    # Index Indian declarations by category
    decl_by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for d in declarations:
        cat = d.get("category", "OTHER")
        decl_by_cat.setdefault(cat, []).append(d)

    # Combine all searchable text
    combined_text = raw_ocr_text + " " + " ".join([d.get("raw_text", "") for d in declarations])
    if context:
        combined_text += f" {context.get('commodity_category', '')} {context.get('product_type', '')}"

    # 1. Global bans analysis
    banned_substances = scan_text_for_banned_substances(combined_text, target_jurisdiction_id=jid)

    # 2. Rule-by-rule comparison
    comparison_matrix: List[Dict[str, Any]] = []
    penalties = 0
    blocker_count = 0
    warning_count = 0

    # If banned substances exist for this jurisdiction, that's an immediate critical export blocker
    target_bans = [s for s in banned_substances if s.get("is_banned_in_target")]
    if target_bans:
        blocker_count += len(target_bans)
        penalties += 40

    for req in requirements:
        dimension = req.get("dimension")
        comp_type = req.get("comparison_type")
        title = req.get("title")
        target_rule = req.get("target_rule")
        indian_rule = req.get("indian_rule")
        action = req.get("action_required_for_export")

        status = "COMPLIANT"
        severity = "INFO"
        indian_finding = "Not declared or standard compliant"
        notes = ""

        if dimension == "PRICING_MRP":
            mrp_decls = decl_by_cat.get("MRP", [])
            if mrp_decls:
                mrp_val = mrp_decls[0].get("normalized_value") or mrp_decls[0].get("raw_text")
                indian_finding = f"Indian MRP declared: ₹{mrp_val} (mandatory in India)"
                if comp_type == "PROHIBITED_IN_TARGET":
                    status = "PROHIBITED_IN_TARGET"
                    severity = "CRITICAL"
                    notes = f"MRP is illegal or invalid in {country_name}. Must be replaced with retailer unit pricing."
                    penalties += 20
                    blocker_count += 1
            else:
                indian_finding = "No Indian MRP declared."
                status = "COMPLIANT"

        elif dimension == "NET_QUANTITY_UNITS":
            net_decls = decl_by_cat.get("NET_QUANTITY", [])
            if net_decls:
                unit = net_decls[0].get("unit", "")
                val = net_decls[0].get("normalized_value", "")
                indian_finding = f"Declared Metric Quantity: {val} {unit}"
                if jid == "USA":
                    # Check if US customary units (oz, fl oz, lb) are present in text
                    has_us_units = bool(re.search(r'\b(oz|fl\s*oz|ounce|pound|lb|lbs)\b', combined_text, re.I))
                    if not has_us_units:
                        status = "ACTION_REQUIRED"
                        severity = "HIGH"
                        notes = "U.S. FPLA mandates dual units (avoirdupois oz/lb alongside metric)."
                        penalties += 15
                        warning_count += 1
                    else:
                        status = "COMPLIANT"
                        notes = "Dual metric and U.S. Customary units detected."
                else:
                    status = "COMPLIANT"
                    notes = f"Metric unit '{unit}' is standard in {country_name}."
            else:
                indian_finding = "Net quantity not extracted from label."
                status = "ACTION_REQUIRED"
                severity = "HIGH"
                penalties += 10
                warning_count += 1

        elif dimension == "NET_QUANTITY_PLACEMENT":
            if jid == "USA":
                status = "ACTION_REQUIRED"
                severity = "MEDIUM"
                indian_finding = "Standard Indian placement anywhere on PDP."
                notes = "Must verify net quantity is in bottom 30% of the Principal Display Panel."
                penalties += 5
                warning_count += 1
            elif jid == "AUS":
                status = "ACTION_REQUIRED"
                severity = "MEDIUM"
                indian_finding = "Standard Indian numeral height table."
                notes = "Must verify character height meets NTMR Schedule 4 package dimension rules."
                penalties += 5
                warning_count += 1
            else:
                status = "COMPLIANT"
                indian_finding = "Standard placement meets baseline requirements."

        elif dimension == "STATISTICAL_SYSTEM":
            indian_finding = "Indian LMPC uses individual package Maximum Permissible Error (MPE)."
            status = "DIFFERENT_SPECIFICATION"
            severity = "MEDIUM"
            if jid in ["EU", "GBR", "AUS"]:
                notes = f"{country_name} enforces the Average Quantity System (AQS / Three Packers' Rules). Optional e-mark ℮ requires certification."
            penalties += 5
            warning_count += 1

        elif dimension == "LANGUAGE_REQUIREMENTS":
            if jid == "GCC":
                # Check for Arabic script characters
                has_arabic = bool(re.search(r'[\u0600-\u06FF]', combined_text))
                if not has_arabic:
                    status = "ACTION_REQUIRED"
                    severity = "CRITICAL"
                    indian_finding = "English/Hindi label detected. No Arabic text detected."
                    notes = "GSO 9/2013 strictly mandates Arabic text for all mandatory declarations."
                    penalties += 20
                    blocker_count += 1
                else:
                    status = "COMPLIANT"
                    indian_finding = "Bilingual Arabic text detected."
            else:
                status = "COMPLIANT"
                indian_finding = "English language declarations accepted."

        elif dimension == "BEST_BEFORE_EXPIRY":
            date_decls = decl_by_cat.get("EXPIRY_DATE", []) or decl_by_cat.get("MANUFACTURE_DATE", [])
            if jid == "GCC":
                status = "DIFFERENT_SPECIFICATION"
                severity = "HIGH"
                indian_finding = "Indian format often uses 'Best Before X months from packaging'."
                notes = "GSO 150-1 requires explicit Gregorian Production AND Expiry dates (DD/MM/YYYY)."
                penalties += 10
                warning_count += 1
            else:
                status = "COMPLIANT"
                indian_finding = "Expiry/Manufacture date declared."

        elif dimension == "ALLERGEN_DECLARATION":
            if jid in ["EU", "GBR"]:
                status = "ACTION_REQUIRED"
                severity = "HIGH"
                indian_finding = "FSSAI allergen declaration style."
                notes = "Must emphasize 14 EU/UK allergens in BOLD typography directly within ingredient list."
                penalties += 10
                warning_count += 1
            elif jid == "AUS":
                status = "ACTION_REQUIRED"
                severity = "HIGH"
                indian_finding = "FSSAI allergen declaration style."
                notes = "FSANZ PEAL standard requires bold allergen names AND a separate 'Contains: ...' summary box."
                penalties += 10
                warning_count += 1
            else:
                status = "COMPLIANT"
                indian_finding = "General allergen declaration requirements apply."

        elif dimension == "MANUFACTURER_PACKER":
            status = "ACTION_REQUIRED"
            severity = "MEDIUM"
            indian_finding = "Indian manufacturer premises address declared."
            notes = f"Must declare local {country_name} importer / responsible business entity name and address."
            penalties += 5
            warning_count += 1

        elif dimension == "COUNTRY_OF_ORIGIN":
            status = "COMPLIANT"
            indian_finding = "Mandatory Indian origin declaration."
            notes = f"Add prominent 'Product of India' or 'Made in India' for customs compliance in {country_name}."

        else:
            status = "COMPLIANT"
            indian_finding = "Standard compliance."

        comparison_matrix.append({
            "dimension": dimension,
            "title": title,
            "comparison_type": comp_type,
            "target_rule": target_rule,
            "indian_rule": indian_rule,
            "indian_label_status": indian_finding,
            "export_status": status,
            "severity": severity,
            "notes": notes,
            "action_required": action
        })

    # Calculate export readiness score
    export_readiness_score = max(0, min(100, 100 - penalties))

    if blocker_count > 0:
        verdict = "EXPORT_BLOCKED"
        verdict_summary = f"Cannot export to {country_name} in current packaging: {blocker_count} critical blocker(s) detected."
    elif warning_count > 0:
        verdict = "ACTION_REQUIRED"
        verdict_summary = f"Modifications required for {country_name}: {warning_count} label difference(s) to address before export."
    else:
        verdict = "APPROVED_FOR_EXPORT"
        verdict_summary = f"Fully compliant with {country_name} packaging regulations."

    # Build executive summary
    exec_summary_lines = [
        f"Export Assessment for {country_name} ({jurisdiction_data.get('flag_emoji', '')}): {verdict} ({export_readiness_score}/100 readiness)."
    ]
    if target_bans:
        exec_summary_lines.append(
            f"CRITICAL WARNING: Product text contains {len(target_bans)} ingredient(s) that are BANNED or restricted in {country_name}: " +
            ", ".join([f"{b['canonical_name']} ({b['target_ban_detail']['health_concern']})" for b in target_bans]) + "."
        )
    if blocker_count > len(target_bans):
        exec_summary_lines.append(
            f"Mandatory metrological changes required, including removal of Indian MRP or addition of target-specific declarations."
        )

    return {
        "jurisdiction": {
            "jurisdiction_id": jid,
            "country_name": country_name,
            "flag_emoji": jurisdiction_data.get("flag_emoji", "🌐"),
            "regulatory_bodies": jurisdiction_data.get("regulatory_bodies", []),
            "governing_acts": jurisdiction_data.get("governing_acts", [])
        },
        "export_readiness_score": export_readiness_score,
        "overall_verdict": verdict,
        "verdict_summary": verdict_summary,
        "executive_summary": " ".join(exec_summary_lines),
        "total_requirements": len(requirements),
        "blockers_count": blocker_count,
        "warnings_count": warning_count,
        "banned_substances_detected": banned_substances,
        "comparison_matrix": comparison_matrix
    }
