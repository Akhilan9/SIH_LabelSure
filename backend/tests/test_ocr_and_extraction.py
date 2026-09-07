import os
import cv2
import numpy as np
import pytest
from backend.app.ocr.engine import run_ocr_on_image
from backend.app.cv.preprocessing import preprocess_label_image
from backend.app.extraction.extractor import extract_declarations_from_ocr

# -----------------------------------------------------------------
# 1. Real OCR Pipeline Test: Image -> Preprocessing -> OCR -> Extraction
# -----------------------------------------------------------------
def test_real_ocr_pipeline_on_sample_label(tmp_path):
    # 1. Synthesize realistic packaged food label
    img = np.ones((800, 1000, 3), dtype=np.uint8) * 240
    cv2.putText(img, "APEX ORGANIC BASMATI RICE", (60, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
    cv2.putText(img, "Generic Name: Basmati Rice", (60, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "Net Quantity: 5 kg", (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "MRP Rs. 650.00 incl. of all taxes", (60, 310), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "Unit Sale Price: Rs. 130.00 per kg", (60, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(img, "Mfg by: Apex Agro Industries Ltd, Karnal 132001", (60, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Packed by: Apex Packaging Hub, Sonipat 131001", (60, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Mfg Date: 03/2026", (60, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Best Before: 03/2028", (60, 660), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    cv2.putText(img, "Consumer Care: 1800-222-3333 help@apexrice.com", (60, 730), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 2)
    
    raw_path = str(tmp_path / "rice_sample_label.jpg")
    proc_path = str(tmp_path / "rice_sample_processed.jpg")
    cv2.imwrite(raw_path, img)
    
    # 2. Preprocessing
    w, h = preprocess_label_image(raw_path, proc_path)
    assert os.path.exists(proc_path)
    assert w > 0 and h > 0
    
    # 3. RapidOCR / PP-OCRv4 execution
    ocr_result = run_ocr_on_image(proc_path)
    assert ocr_result["engine_name"].startswith("PaddleOCR / RapidOCR")
    assert len(ocr_result["lines"]) > 0
    assert "full_text" in ocr_result
    
    # Verify bounding boxes & confidence format
    for line in ocr_result["lines"]:
        assert "bbox" in line
        assert len(line["bbox"]) == 4  # [x1, y1, x2, y2]
        assert "confidence" in line
        assert 0.0 <= line["confidence"] <= 1.0
        
    # 4. Declaration Extraction
    decls = extract_declarations_from_ocr(ocr_result["lines"], source_image_id="img_sample_rice")
    assert len(decls) > 0
    
    # Verify contract requirements on every extracted declaration
    for d in decls:
        assert "type" in d
        assert "raw_text" in d and len(d["raw_text"]) > 0
        assert "normalized_value" in d
        assert "confidence" in d and (0.0 <= d["confidence"] <= 1.0)
        assert "bbox" in d and len(d["bbox"]) == 4
        assert d["source_image_id"] == "img_sample_rice"

# -----------------------------------------------------------------
# 2. Comprehensive 14-Category Extraction Test
# -----------------------------------------------------------------
def test_all_14_statutory_declarations_extraction():
    lines = [
        {"text": "APEX ULTRA SMARTPHONE", "bbox": [0.05, 0.05, 0.9, 0.10], "confidence": 0.99},
        {"text": "Generic Name: Mobile Phone", "bbox": [0.05, 0.12, 0.8, 0.16], "confidence": 0.97},
        {"text": "Net Quantity: 1 U", "bbox": [0.05, 0.18, 0.4, 0.22], "confidence": 0.98},
        {"text": "MRP Rs. 24999.00 incl. of all taxes", "bbox": [0.05, 0.24, 0.7, 0.28], "confidence": 0.98},
        {"text": "Unit Sale Price: Rs. 24999.00 per unit", "bbox": [0.05, 0.30, 0.6, 0.34], "confidence": 0.96},
        {"text": "Manufactured by: Apex Electronics Ltd, Sector 62, Noida 201301", "bbox": [0.05, 0.36, 0.95, 0.40], "confidence": 0.95},
        {"text": "Packed by: Apex Tech Packaging Facility, Manesar 122051", "bbox": [0.05, 0.42, 0.95, 0.46], "confidence": 0.94},
        {"text": "Imported by: Apex Global Trade India Pvt Ltd, Mumbai 400001", "bbox": [0.05, 0.48, 0.95, 0.52], "confidence": 0.94},
        {"text": "Country of Origin: India", "bbox": [0.05, 0.54, 0.5, 0.58], "confidence": 0.97},
        {"text": "Date of Manufacture: 01/2026", "bbox": [0.05, 0.60, 0.5, 0.64], "confidence": 0.95},
        {"text": "Date of Packaging: 02/2026", "bbox": [0.05, 0.66, 0.5, 0.70], "confidence": 0.95},
        {"text": "Best Before: 24 months from packaging", "bbox": [0.05, 0.72, 0.6, 0.76], "confidence": 0.93},
        {"text": "Use By: 02/2028", "bbox": [0.05, 0.78, 0.4, 0.82], "confidence": 0.94},
        {"text": "Customer Care: 1800-999-8888 support@apextech.com", "bbox": [0.05, 0.84, 0.85, 0.88], "confidence": 0.96},
        {"text": "Dimensions: 16.5 cm x 7.8 cm x 0.8 cm", "bbox": [0.05, 0.90, 0.7, 0.94], "confidence": 0.95},
    ]

    decls = extract_declarations_from_ocr(lines, source_image_id="img_all_14")
    cat_map = {d["type"]: d for d in decls}

    expected_categories = [
        "COMMON_GENERIC_NAME",
        "NET_QUANTITY",
        "MRP",
        "UNIT_SALE_PRICE",
        "MANUFACTURER",
        "PACKER",
        "IMPORTER",
        "COUNTRY_OF_ORIGIN",
        "MANUFACTURE_DATE",
        "PACK_DATE",
        "BEST_BEFORE",
        "USE_BY",
        "CONSUMER_CARE",
        "DIMENSIONS"
    ]

    for category in expected_categories:
        assert category in cat_map, f"Missing declaration category: {category}"
        decl = cat_map[category]
        assert decl["type"] == category
        assert decl["category"] == category
        assert decl["raw_text"] is not None
        assert decl["normalized_value"] is not None
        assert decl["source_image_id"] == "img_all_14"
        assert len(decl["bbox"]) == 4

    # Validate detailed normalized values
    assert cat_map["MRP"]["normalized_value"]["value"] == 24999.0
    assert cat_map["MRP"]["normalized_value"]["inclusive_of_taxes"] is True
    assert cat_map["NET_QUANTITY"]["normalized_value"]["value"] == 1.0
    assert cat_map["NET_QUANTITY"]["normalized_value"]["unit"] == "u"
    assert cat_map["NET_QUANTITY"]["normalized_value"]["is_legal_metric_unit"] is True
    assert cat_map["UNIT_SALE_PRICE"]["normalized_value"]["price_per_unit"] == 24999.0
    assert cat_map["MANUFACTURER"]["normalized_value"]["has_pincode"] is True
    assert cat_map["COUNTRY_OF_ORIGIN"]["normalized_value"] == "India"
    assert cat_map["DIMENSIONS"]["normalized_value"]["length"] == 16.5
    assert cat_map["DIMENSIONS"]["normalized_value"]["width"] == 7.8
    assert cat_map["DIMENSIONS"]["normalized_value"]["height"] == 0.8
    assert cat_map["DIMENSIONS"]["normalized_value"]["unit"] == "cm"

# -----------------------------------------------------------------
# 3. Non-Standard Metric Unit Validation Test
# -----------------------------------------------------------------
def test_illegal_non_standard_unit_extraction():
    lines = [
        {"text": "Net Weight: 500 gms", "bbox": [0.1, 0.2, 0.5, 0.3], "confidence": 0.95}
    ]
    decls = extract_declarations_from_ocr(lines)
    cat_map = {d["type"]: d for d in decls}
    
    assert "NET_QUANTITY" in cat_map
    # Under Legal Metrology Rule 13, 'gms' is illegal; canonical is 'g'
    assert cat_map["NET_QUANTITY"]["normalized_value"]["unit"] == "gms"
    assert cat_map["NET_QUANTITY"]["normalized_value"]["canonical_unit"] == "g"
    assert cat_map["NET_QUANTITY"]["normalized_value"]["is_legal_metric_unit"] is False

# -----------------------------------------------------------------
# 4. Spatial Grouping Test: Multi-Line Manufacturer Address
# -----------------------------------------------------------------
def test_spatial_grouping_multiline_manufacturer():
    lines = [
        {"text": "Mfg by: Apex Confectionery", "bbox": [0.1, 0.40, 0.6, 0.44], "confidence": 0.95, "line_index": 0},
        {"text": "Plot 42, Sector 18, Gurugram 122015", "bbox": [0.1, 0.45, 0.7, 0.49], "confidence": 0.94, "line_index": 1}
    ]
    decls = extract_declarations_from_ocr(lines)
    cat_map = {d["type"]: d for d in decls}
    
    assert "MANUFACTURER" in cat_map
    mfg_decl = cat_map["MANUFACTURER"]
    # Verify spatial grouping combined both lines into address
    assert "Plot 42" in mfg_decl["raw_text"]
    assert "122015" in mfg_decl["raw_text"]
    assert mfg_decl["normalized_value"]["has_pincode"] is True
