import re
from typing import List, Dict, Any, Optional

# Standard legal metric symbols under Legal Metrology Act (Rule 13)
LEGAL_METRIC_UNITS = {
    "g": "gram",
    "kg": "kilogram",
    "mg": "milligram",
    "ml": "millilitre",
    "l": "litre",
    "m": "metre",
    "cm": "centimetre",
    "mm": "millimetre",
    "n": "number",
    "u": "unit"
}

NON_STANDARD_UNIT_SYMBOLS = {
    "gms": "g",
    "gm": "g",
    "kgs": "kg",
    "ltrs": "l",
    "ltr": "l",
    "ml.": "ml",
    "g.": "g",
    "kg.": "kg"
}

def are_spatially_adjacent(box_a: List[float], box_b: List[float], y_thresh: float = 0.04, x_thresh: float = 0.25) -> bool:
    """Checks if box_b is immediately to the right or on the immediate next line under box_a."""
    # box format: [x1, y1, x2, y2]
    vert_aligned = abs(box_a[1] - box_b[1]) < y_thresh
    to_right = (box_b[0] >= box_a[0]) and ((box_b[0] - box_a[2]) < x_thresh)
    next_line = (box_b[1] >= box_a[1]) and ((box_b[1] - box_a[3]) < y_thresh)
    return (vert_aligned and to_right) or next_line

def extract_declarations_from_ocr(
    lines: List[Dict[str, Any]],
    source_image_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Hybrid declaration extraction pipeline utilizing:
    - Regex pattern matching
    - Anchor keyword recognition
    - Spatial relationship tracking (horizontal adjacency & line proximity)
    - Normalized metric validation
    
    Supports all 14 statutory declaration categories:
    1. MANUFACTURER
    2. PACKER
    3. IMPORTER
    4. COUNTRY_OF_ORIGIN
    5. COMMON_GENERIC_NAME
    6. NET_QUANTITY
    7. MRP
    8. MANUFACTURE_DATE
    9. PACK_DATE
    10. BEST_BEFORE
    11. USE_BY
    12. CONSUMER_CARE
    13. UNIT_SALE_PRICE
    14. DIMENSIONS
    """
    declarations: List[Dict[str, Any]] = []
    
    # Pre-parse lines
    cleaned_lines = []
    for line in lines:
        t = line.get("text", "").strip()
        if t:
            cleaned_lines.append({
                "text": t,
                "bbox": line.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                "confidence": line.get("confidence", 0.8),
                "line_index": line.get("line_index", 0)
            })
            
    def add_declaration(
        category: str,
        raw_text: str,
        normalized_value: Any,
        confidence: float,
        bbox: List[float],
        unit: Optional[str] = None,
        extraction_method: str = "HYBRID"
    ):
        declarations.append({
            "type": category,
            "category": category,
            "raw_text": raw_text,
            "normalized_value": normalized_value,
            "unit": unit,
            "confidence": round(confidence, 3),
            "bbox": bbox,
            "source_image_id": source_image_id,
            "extraction_method": extraction_method
        })

    # 1. MRP Extraction
    mrp_pattern = re.compile(
        r'(?:M\.?R\.?P\.?|MAXIMUM\s*RETAIL\s*PRICE)\s*[:\.\-]?\s*(?:Rs\.?|₹|INR)?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(.*)',
        re.IGNORECASE
    )
    for idx, item in enumerate(cleaned_lines):
        match = mrp_pattern.search(item["text"])
        if match:
            val_str = match.group(1)
            rest = match.group(2)
            # Spatial lookahead: check immediate right or next line for "incl. of all taxes"
            next_text = cleaned_lines[idx+1]["text"] if idx+1 < len(cleaned_lines) else ""
            combined_context = rest + " " + next_text
            tax_incl = bool(re.search(r'incl|inclusive|all\s*tax', combined_context, re.IGNORECASE))
            add_declaration(
                category="MRP",
                raw_text=item["text"] + (f" ({next_text})" if (tax_incl and "tax" in next_text.lower()) else ""),
                normalized_value={
                    "value": float(val_str),
                    "currency": "INR",
                    "inclusive_of_taxes": tax_incl
                },
                unit="INR",
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="REGEX_PATTERN"
            )
            break

    # 2. Net Quantity Extraction
    qty_pattern = re.compile(
        r'(?:Net\s*(?:Qty|Quantity|Wt|Weight|Contents?)|Quantity|Net\s*Volume)\s*[:\.\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\.\/]+)',
        re.IGNORECASE
    )
    qty_found = False
    for item in cleaned_lines:
        match = qty_pattern.search(item["text"])
        if match:
            val = float(match.group(1))
            unit_raw = match.group(2).strip().lower()
            is_legal = unit_raw in LEGAL_METRIC_UNITS
            add_declaration(
                category="NET_QUANTITY",
                raw_text=item["text"],
                normalized_value={
                    "value": val,
                    "unit": unit_raw,
                    "is_legal_metric_unit": is_legal,
                    "canonical_unit": LEGAL_METRIC_UNITS.get(unit_raw, NON_STANDARD_UNIT_SYMBOLS.get(unit_raw, unit_raw))
                },
                unit=unit_raw,
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="REGEX_PATTERN"
            )
            qty_found = True
            break
            
    if not qty_found:
        # Standalone net quantity heuristic: e.g. "500 g" or "1 kg" or "250 ml" or "10 N"
        standalone_qty = re.compile(r'\b([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gms|gm|ml|l|ltrs|N|U)\b', re.IGNORECASE)
        for item in cleaned_lines:
            match = standalone_qty.search(item["text"])
            if match and not any(kw in item["text"].lower() for kw in ["rs", "mrp", "₹", "usp", "price"]):
                val = float(match.group(1))
                unit_raw = match.group(2).strip().lower()
                is_legal = unit_raw in LEGAL_METRIC_UNITS
                add_declaration(
                    category="NET_QUANTITY",
                    raw_text=item["text"],
                    normalized_value={
                        "value": val,
                        "unit": unit_raw,
                        "is_legal_metric_unit": is_legal,
                        "canonical_unit": LEGAL_METRIC_UNITS.get(unit_raw, NON_STANDARD_UNIT_SYMBOLS.get(unit_raw, unit_raw))
                    },
                    unit=unit_raw,
                    confidence=item["confidence"] * 0.88,
                    bbox=item["bbox"],
                    extraction_method="KEYWORD_ANCHOR"
                )
                break

    # 3. Manufacturer Extraction
    mfg_pattern = re.compile(r'(?:Mfd\.?\s*by|Mfg\.?\s*by|Manufactured\s*by|Produced\s*by|Factory\s*[:\-])\s*[:\.\-]?\s*(.*)', re.IGNORECASE)
    for idx, item in enumerate(cleaned_lines):
        mfg_match = mfg_pattern.search(item["text"])
        if mfg_match:
            entity_text = mfg_match.group(1).strip()
            full_mfg_text = item["text"]
            # Spatial grouping: if subsequent line is an address, combine it
            if idx + 1 < len(cleaned_lines) and are_spatially_adjacent(item["bbox"], cleaned_lines[idx+1]["bbox"]):
                full_mfg_text += " " + cleaned_lines[idx+1]["text"]
            add_declaration(
                category="MANUFACTURER",
                raw_text=full_mfg_text,
                normalized_value={
                    "declared_name": entity_text or full_mfg_text,
                    "has_pincode": bool(re.search(r'\b[1-9][0-9]{5}\b', full_mfg_text))
                },
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="KEYWORD_ANCHOR"
            )
            break

    # 4. Packer Extraction
    packer_pattern = re.compile(r'(?:Packed\s*by|Pkd\.?\s*by|Packer\s*[:\-])\s*[:\.\-]?\s*(.*)', re.IGNORECASE)
    for idx, item in enumerate(cleaned_lines):
        p_match = packer_pattern.search(item["text"])
        if p_match:
            full_packer_text = item["text"]
            if idx + 1 < len(cleaned_lines) and are_spatially_adjacent(item["bbox"], cleaned_lines[idx+1]["bbox"]):
                full_packer_text += " " + cleaned_lines[idx+1]["text"]
            add_declaration(
                category="PACKER",
                raw_text=full_packer_text,
                normalized_value={"declared_name": p_match.group(1).strip() or full_packer_text},
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="KEYWORD_ANCHOR"
            )
            break

    # 5. Importer Extraction
    importer_pattern = re.compile(
        r'(?:Imported\s*(?:&|and)?\s*(?:(?:Packed|Marketed|Distributed)\s*)?by|Importer\s*[:\-]|Marketed\s*in\s*India\s*by)\s*[:\.\-]?\s*(.*)',
        re.IGNORECASE
    )
    for idx, item in enumerate(cleaned_lines):
        match = importer_pattern.search(item["text"])
        if match:
            full_imp_text = item["text"]
            if idx + 1 < len(cleaned_lines) and are_spatially_adjacent(item["bbox"], cleaned_lines[idx+1]["bbox"]):
                full_imp_text += " " + cleaned_lines[idx+1]["text"]
            add_declaration(
                category="IMPORTER",
                raw_text=full_imp_text,
                normalized_value=match.group(1).strip() or full_imp_text,
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="KEYWORD_ANCHOR"
            )
            break

    # 6. Country of Origin Extraction
    origin_pattern = re.compile(r'(?:Country\s*of\s*Origin|Made\s*in|Product\s*of|Origin\s*[:\-])\s*[:\.\-]?\s*([A-Za-z\s]+)', re.IGNORECASE)
    for item in cleaned_lines:
        match = origin_pattern.search(item["text"])
        if match:
            country = match.group(1).strip()
            add_declaration(
                category="COUNTRY_OF_ORIGIN",
                raw_text=item["text"],
                normalized_value=country,
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="REGEX_PATTERN"
            )
            break

    # 7. Manufacture Date & Pack Date
    mfg_date_pattern = re.compile(r'(?:Mfg\.?\s*Date|Date\s*of\s*Mfg|Date\s*of\s*Manufacture|Month\s*and\s*Year\s*of\s*Mfg|DOM\s*[:\-])\s*[:\.\-]?\s*([0-9A-Za-z\/\-\.\s]+)', re.IGNORECASE)
    pack_date_pattern = re.compile(r'(?:Date\s*of\s*Pack(?:aging)?|Pkd\s*on|Packed\s*on|Packaging\s*Date|Month\s*and\s*Year\s*of\s*Pack(?:ing)?|DOP\s*[:\-])\s*[:\.\-]?\s*([0-9A-Za-z\/\-\.\s]+)', re.IGNORECASE)
    
    for item in cleaned_lines:
        if not any(d["category"] == "MANUFACTURE_DATE" for d in declarations):
            m_date = mfg_date_pattern.search(item["text"])
            if m_date:
                add_declaration(
                    category="MANUFACTURE_DATE",
                    raw_text=item["text"],
                    normalized_value=m_date.group(1).strip(),
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    extraction_method="REGEX_PATTERN"
                )

        if not any(d["category"] == "PACK_DATE" for d in declarations):
            p_date = pack_date_pattern.search(item["text"])
            if p_date:
                add_declaration(
                    category="PACK_DATE",
                    raw_text=item["text"],
                    normalized_value=p_date.group(1).strip(),
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    extraction_method="REGEX_PATTERN"
                )

    # 8. Best Before & Use By (Expiry)
    best_before_pattern = re.compile(r'(?:Best\s*Before|BB\s*[:\-])\s*[:\.\-]?\s*(.*)', re.IGNORECASE)
    use_by_pattern = re.compile(r'(?:Use\s*By|Expiry\s*Date|Exp\.?\s*Date|Expiry|Exp\s*[:\-])\s*[:\.\-]?\s*(.*)', re.IGNORECASE)
    
    for item in cleaned_lines:
        if not any(d["category"] == "BEST_BEFORE" for d in declarations):
            bb_match = best_before_pattern.search(item["text"])
            if bb_match:
                add_declaration(
                    category="BEST_BEFORE",
                    raw_text=item["text"],
                    normalized_value=bb_match.group(1).strip(),
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    extraction_method="REGEX_PATTERN"
                )
                
        if not any(d["category"] == "USE_BY" for d in declarations):
            ub_match = use_by_pattern.search(item["text"])
            if ub_match:
                add_declaration(
                    category="USE_BY",
                    raw_text=item["text"],
                    normalized_value=ub_match.group(1).strip(),
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    extraction_method="REGEX_PATTERN"
                )

    # 9. Consumer Care Details
    cc_phone_pattern = re.compile(r'(?:Consumer\s*Care|Customer\s*Care|Helpline|Toll\s*Free|Phone|Tel)\s*[:\.\-]?\s*([0-9\+\-\s]{8,15})', re.IGNORECASE)
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    for item in cleaned_lines:
        match_phone = cc_phone_pattern.search(item["text"])
        match_email = email_pattern.search(item["text"])
        if match_phone or match_email or any(kw in item["text"].lower() for kw in ["consumercare", "customercare", "toll-free", "helpline"]):
            add_declaration(
                category="CONSUMER_CARE",
                raw_text=item["text"],
                normalized_value={
                    "phone": match_phone.group(1).strip() if match_phone else None,
                    "email": match_email.group(0) if match_email else None
                },
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="KEYWORD_ANCHOR"
            )
            break

    # 10. Unit Sale Price (USP)
    usp_pattern = re.compile(r'(?:Unit\s*Sale\s*Price|USP)\s*[:\.\-]?\s*(?:Rs\.?|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/|\s*per\s*)\s*([a-zA-Z]+)', re.IGNORECASE)
    for item in cleaned_lines:
        match = usp_pattern.search(item["text"])
        if match:
            add_declaration(
                category="UNIT_SALE_PRICE",
                raw_text=item["text"],
                normalized_value={
                    "price_per_unit": float(match.group(1)),
                    "unit": match.group(2).strip().lower()
                },
                unit=match.group(2).strip().lower(),
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="REGEX_PATTERN"
            )
            break

    # 11. Dimensions
    dim_pattern = re.compile(
        r'(?:Dimensions?|Size|Dim\.?)\s*[:\.\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)?\s*[xX*×]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)?(?:\s*[xX*×]\s*([0-9]+(?:\.[0-9]+)?))?\s*([a-zA-Z]+)',
        re.IGNORECASE
    )
    for item in cleaned_lines:
        dim_match = dim_pattern.search(item["text"])
        if dim_match:
            d1 = float(dim_match.group(1))
            d2 = float(dim_match.group(2))
            d3 = float(dim_match.group(3)) if dim_match.group(3) else None
            unit_d = dim_match.group(4).strip().lower()
            add_declaration(
                category="DIMENSIONS",
                raw_text=item["text"],
                normalized_value={
                    "length": d1,
                    "width": d2,
                    "height": d3,
                    "unit": unit_d
                },
                unit=unit_d,
                confidence=item["confidence"],
                bbox=item["bbox"],
                extraction_method="REGEX_PATTERN"
            )
            break

    # 12. Common / Generic Name
    generic_name_pattern = re.compile(r'(?:Common\s*Name|Generic\s*Name|Name\s*of\s*(?:the\s*)?Commodity|Commodity)\s*[:\.\-]?\s*(.*)', re.IGNORECASE)
    generic_found = False
    for item in cleaned_lines:
        g_match = generic_name_pattern.search(item["text"])
        if g_match:
            g_name = g_match.group(1).strip()
            if g_name:
                add_declaration(
                    category="COMMON_GENERIC_NAME",
                    raw_text=item["text"],
                    normalized_value=g_name,
                    confidence=item["confidence"],
                    bbox=item["bbox"],
                    extraction_method="KEYWORD_ANCHOR"
                )
                generic_found = True
                break
                
    if not generic_found and cleaned_lines:
        # Spatial heuristic: The uppermost prominent non-numeric title line is the product/generic name
        for line in cleaned_lines[:3]:
            txt = line["text"]
            if len(txt) > 3 and not any(kw in txt.lower() for kw in ["mrp", "rs", "net", "qty", "mfg", "date", "batch", "lot"]):
                add_declaration(
                    category="COMMON_GENERIC_NAME",
                    raw_text=txt,
                    normalized_value=txt,
                    confidence=line["confidence"] * 0.90,
                    bbox=line["bbox"],
                    extraction_method="SPATIAL_PROXIMITY"
                )
                break

    return declarations
