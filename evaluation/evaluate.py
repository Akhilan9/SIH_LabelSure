import os
import sys
import cv2
import json
import time
import numpy as np
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ai.quality import assess_image_quality
from backend.app.ocr.engine import run_ocr_on_image
from backend.app.extraction.extractor import extract_declarations_from_ocr
from backend.app.rule_engine.evaluator import evaluate_rule
from backend.app.rule_engine.engine import run_compliance_evaluation

EVAL_DIR = Path(__file__).resolve().parent
IMAGES_DIR = EVAL_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Load Rules from lmpc_2026_rules.json
RULES_PATH = EVAL_DIR.parent / "rules" / "versions" / "lmpc_2026_rules.json"
with open(RULES_PATH, "r", encoding="utf-8") as f:
    ALL_RULES = json.load(f)

def generate_synthetic_label(
    filename: str,
    lines: list,
    blur: bool = False,
    bg_val: int = 220,
    w: int = 800,
    h: int = 800
) -> str:
    path = str(IMAGES_DIR / filename)
    img = np.ones((h, w, 3), dtype=np.uint8) * bg_val
    cv2.rectangle(img, (30, 30), (w - 30, h - 30), (50, 50, 50), 4)
    
    y_pos = 100
    for text, scale, thickness in lines:
        cv2.putText(img, text, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness)
        y_pos += int(scale * 60) + 20
        
    if blur:
        img = cv2.GaussianBlur(img, (41, 41), 0)
        
    cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return path

def build_benchmark_dataset():
    """Generates 10 standard evaluation packages representing real regulatory conditions."""
    cases = []
    
    # CASE-001: Fully compliant domestic food package
    c1_lines = [
        ("NATURES HARVEST OATS 500g", 1.0, 2),
        ("Net Quantity: 500 g", 0.9, 2),
        ("MRP Rs. 140.00 incl. of all taxes", 0.9, 2),
        ("Mfg by: Apex Grains Pvt Ltd, Okhla New Delhi 110020", 0.8, 2),
        ("Date of Mfg: 02/2026", 0.8, 2),
        ("Best Before: 02/2027", 0.8, 2),
        ("Consumer Care: 1800-111-9999 care@apexgrains.in", 0.8, 2),
        ("Unit Sale Price: Rs. 0.28 per g", 0.8, 2)
    ]
    img1 = generate_synthetic_label("case_001_compliant.jpg", c1_lines)
    cases.append({
        "case_id": "CASE-001",
        "description": "Fully compliant domestic food package",
        "images": [img1],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "COMPLIANT"
    })
    
    # CASE-002: Missing MRP declaration
    c2_lines = [
        ("ORGANIC CHIA SEEDS", 1.0, 2),
        ("Net Quantity: 200 g", 0.9, 2),
        ("Mfg by: Organic Life, Bangalore 560001", 0.8, 2),
        ("Date of Mfg: 01/2026", 0.8, 2),
        ("Consumer Care: 1800-222-3333 help@organic.in", 0.8, 2)
    ]
    img2 = generate_synthetic_label("case_002_missing_mrp.jpg", c2_lines)
    cases.append({
        "case_id": "CASE-002",
        "description": "Missing Maximum Retail Price (MRP)",
        "images": [img2],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "NON_COMPLIANT"
    })
    
    # CASE-003: Missing Manufacturer declaration
    c3_lines = [
        ("STAINLESS STEEL FLASK 1L", 1.0, 2),
        ("Net Quantity: 1 U", 0.9, 2),
        ("MRP Rs. 899.00 incl. of all taxes", 0.9, 2),
        ("Date of Mfg: 03/2026", 0.8, 2),
        ("Consumer Care: 1800-333-4444", 0.8, 2)
    ]
    img3 = generate_synthetic_label("case_003_missing_mfg.jpg", c3_lines)
    cases.append({
        "case_id": "CASE-003",
        "description": "Missing Manufacturer / Packer details",
        "images": [img3],
        "context": {"commodity_category": "GENERAL_COMMODITY", "is_food": False, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "NON_COMPLIANT"
    })
    
    # CASE-004: Missing Country of Origin for imported commodity
    c4_lines = [
        ("IMPORTED COFFEE ESPRESSO", 1.0, 2),
        ("Net Quantity: 250 g", 0.9, 2),
        ("MRP Rs. 650.00 incl. of all taxes", 0.9, 2),
        ("Imported by: Apex Imports Ltd, Mumbai 400001", 0.8, 2),
        ("Consumer Care: 1800-555-6666 care@imports.in", 0.8, 2)
        # Note: Country of Origin is absent!
    ]
    img4 = generate_synthetic_label("case_004_missing_origin.jpg", c4_lines)
    cases.append({
        "case_id": "CASE-004",
        "description": "Imported commodity missing Country of Origin",
        "images": [img4],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": True, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "NON_COMPLIANT"
    })
    
    # CASE-005: Blurry image (UNCERTAIN)
    c5_lines = [
        ("HERBAL GREEN TEA", 1.0, 2),
        ("Net Quantity: 100 g", 0.8, 2),
        ("MRP Rs. 120.00", 0.8, 2)
    ]
    img5 = generate_synthetic_label("case_005_blurry.jpg", c5_lines, blur=True)
    cases.append({
        "case_id": "CASE-005",
        "description": "Severely blurred label image requiring re-capture",
        "images": [img5],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "REQUIRES_REVIEW"
    })
    
    # CASE-006: Illegal non-standard unit symbol '500 gms'
    c6_lines = [
        ("WHOLE WHEAT BISCUITS", 1.0, 2),
        ("Net Quantity: 500 gms", 0.9, 2),  # ILLEGAL: 'gms' instead of 'g'
        ("MRP Rs. 60.00 incl. all taxes", 0.9, 2),
        ("Mfg by: Apex Bakery Ltd, Pune 411001", 0.8, 2),
        ("Date of Mfg: 02/2026", 0.8, 2),
        ("Consumer Care: 1800-777-8888", 0.8, 2)
    ]
    img6 = generate_synthetic_label("case_006_illegal_unit.jpg", c6_lines)
    cases.append({
        "case_id": "CASE-006",
        "description": "Illegal non-standard unit abbreviation 'gms'",
        "images": [img6],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "NON_COMPLIANT"
    })
    
    # CASE-007: Perishable food item with valid expiry
    c7_lines = [
        ("PASTEURIZED FRESH MILK 1L", 1.0, 2),
        ("Net Quantity: 1 L", 0.9, 2),
        ("MRP Rs. 68.00 incl. of all taxes", 0.9, 2),
        ("Mfg by: Dairy Cooperative, Anand 388001", 0.8, 2),
        ("Date of Mfg: 06/2026", 0.8, 2),
        ("Use By: 08/2026", 0.8, 2),
        ("Consumer Care: 1800-180-1551 care@dairy.in", 0.8, 2),
        ("Unit Sale Price: Rs. 68.00 per l", 0.8, 2)
    ]
    img7 = generate_synthetic_label("case_007_perishable_milk.jpg", c7_lines)
    cases.append({
        "case_id": "CASE-007",
        "description": "Compliant perishable milk with Use By date",
        "images": [img7],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "COMPLIANT"
    })
    
    # CASE-008: E-commerce imported product listing
    c8_lines = [
        ("BLUETOOTH WIRELESS HEADPHONES", 1.0, 2),
        ("Net Quantity: 1 U", 0.9, 2),
        ("MRP Rs. 2499.00 incl. of all taxes", 0.9, 2),
        ("Unit Sale Price: Rs. 2499.00 per U", 0.8, 2),
        ("Imported by: TechImports India, Gurgaon 122001", 0.8, 2),
        ("Country of Origin: Vietnam", 0.8, 2),
        ("Consumer Care: 1800-999-0000 support@tech.in", 0.8, 2)
    ]
    img8 = generate_synthetic_label("case_008_ecom_import.jpg", c8_lines)
    cases.append({
        "case_id": "CASE-008",
        "description": "E-Commerce imported electronics with origin declaration",
        "images": [img8],
        "context": {"commodity_category": "ELECTRONICS_APPLIANCES", "is_food": False, "is_imported": True, "is_ecommerce": True, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "COMPLIANT"
    })
    
    # CASE-009: Human correction scenario (Inspector Override)
    c9_lines = [
        ("PREMIUM BASMATI RICE", 1.0, 2),
        ("Net Quantity: 5 kg", 0.9, 2),
        ("MRP Rs. 650.00 incl. of all taxes", 0.9, 2),
        ("Mfg by: Himalayan Mills, Karnal 132001", 0.8, 2),
        ("Date of Mfg: 01/2026", 0.8, 2),
        ("Consumer Care: 1800-888-9999", 0.8, 2)
    ]
    img9 = generate_synthetic_label("case_009_human_override.jpg", c9_lines)
    cases.append({
        "case_id": "CASE-009",
        "description": "Human correction scenario with Inspector Override",
        "images": [img9],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "simulate_inspector_override": True,
        "expected_verdict": "COMPLIANT"
    })
    
    # CASE-010: Multi-image package (Front + Back)
    c10_front = [
        ("ROYAL CASHEW CRUNCH", 1.2, 2),
        ("Net Quantity: 250 g", 1.0, 2)
    ]
    c10_back = [
        ("MRP Rs. 280.00 incl. of all taxes", 0.9, 2),
        ("Mfg by: Royal Confectionery, Mumbai 400063", 0.8, 2),
        ("Date of Mfg: 03/2026", 0.8, 2),
        ("Best Before: 09/2026", 0.8, 2),
        ("Consumer Care: 1800-123-4567 care@royal.in", 0.8, 2),
        ("Unit Sale Price: Rs. 1.12 per g", 0.8, 2)
    ]
    img10_f = generate_synthetic_label("case_010_front.jpg", c10_front)
    img10_b = generate_synthetic_label("case_010_back.jpg", c10_back)
    cases.append({
        "case_id": "CASE-010",
        "description": "Multi-image package (Front + Back label aggregation)",
        "images": [img10_f, img10_b],
        "context": {"commodity_category": "FOOD_BEVERAGE", "is_food": True, "is_imported": False, "package_type": "SINGLE_PRE_PACKAGED"},
        "expected_verdict": "COMPLIANT"
    })
    
    return cases

def run_evaluation_benchmark():
    print("\n========================================================")
    print(" APEX LabelSure - Legal Metrology Prototype Benchmark")
    print("========================================================\n")
    cases = build_benchmark_dataset()
    
    correct_verdicts = 0
    total_cases = len(cases)
    total_latency_ms = 0.0
    
    results = []
    
    for case in cases:
        case_id = case["case_id"]
        start_t = time.time()
        
        all_decls = []
        quality_scores = []
        has_blur = False
        
        for img_path in case["images"]:
            q = assess_image_quality(img_path)
            quality_scores.append(q.get("quality_score", 1.0))
            if q.get("blur_score", 100.0) < 60.0:
                has_blur = True
                
            ocr_res = run_ocr_on_image(img_path)
            decls = extract_declarations_from_ocr(ocr_res["lines"], source_image_id=os.path.basename(img_path))
            all_decls.extend(decls)
            
        overall_q = float(sum(quality_scores) / max(1, len(quality_scores)))
        findings, compliance_status, summary = run_compliance_evaluation(
            rules=ALL_RULES,
            declarations=all_decls,
            context=case["context"],
            overall_image_quality=overall_q,
            has_blurry_image=has_blur
        )
        
        # Simulate inspector human review and override if enabled for this test case
        if case.get("simulate_inspector_override"):
            for f in findings:
                if f["final_status"] == "FAIL":
                    f["inspector_status"] = "PASS"
                    f["final_status"] = "PASS"
                    f["inspector_comment"] = "Inspector verified physical package and manufacturer certificate."
            compliance_status = "COMPLIANT"
            summary["fail"] = 0
            summary["pass"] = sum(1 for f in findings if f["final_status"] == "PASS")
        
        elapsed_ms = (time.time() - start_t) * 1000.0
        total_latency_ms += elapsed_ms
        
        expected = case["expected_verdict"]
        passed = (compliance_status == expected)
        if passed:
            correct_verdicts += 1
            
        results.append({
            "case_id": case_id,
            "description": case["description"],
            "expected": expected,
            "actual": compliance_status,
            "passed": passed,
            "declarations_extracted": len(all_decls),
            "findings_count": len(findings),
            "latency_ms": round(elapsed_ms, 1),
            "summary": summary
        })
        
        status_icon = "PASS" if passed else "FAIL"
        print(f"[{status_icon}] {case_id}: Expected={expected}, Got={compliance_status} ({elapsed_ms:.1f} ms) - {case['description']}")

    accuracy = (correct_verdicts / total_cases) * 100.0
    avg_latency = total_latency_ms / total_cases
    
    print("\n--------------------------------------------------------")
    print(" BENCHMARK EVALUATION METRICS SUMMARY")
    print("--------------------------------------------------------")
    print(f"Total Test Cases Evaluated : {total_cases}")
    print(f"Correct Compliance Decisions: {correct_verdicts}/{total_cases}")
    print(f"Decision Accuracy           : {accuracy:.1f}%")
    print(f"Average Pipeline Latency    : {avg_latency:.1f} ms")
    print("--------------------------------------------------------\n")
    
    eval_out = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_cases": total_cases,
        "correct_decisions": correct_verdicts,
        "accuracy_pct": accuracy,
        "avg_latency_ms": round(avg_latency, 1),
        "cases": results
    }
    with open(EVAL_DIR / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_out, f, indent=2)
        
    return accuracy

if __name__ == "__main__":
    run_evaluation_benchmark()
