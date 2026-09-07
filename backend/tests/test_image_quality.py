import os
import hashlib
import cv2
import numpy as np
import pytest
from backend.app.ai.quality import assess_image_quality
from backend.app.cv.preprocessing import preprocess_label_image, compute_deskew_angle, rotate_image

# -----------------------------------------------------------------
# Condition 1: Sharp, High-Quality Label Image
# -----------------------------------------------------------------
def test_condition_1_sharp_image(tmp_path):
    img = np.ones((900, 900, 3), dtype=np.uint8) * 230
    cv2.rectangle(img, (50, 50), (850, 850), (30, 30, 30), 4)
    cv2.putText(img, "LEGAL METROLOGY AUDIT", (80, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3)
    cv2.putText(img, "NET QUANTITY: 1.0 kg", (80, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    cv2.putText(img, "MRP Rs. 350.00 incl. of all taxes", (80, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)
    cv2.putText(img, "Mfg: Apex Foods Pvt Ltd", (80, 520), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    path = str(tmp_path / "cond1_sharp.jpg")
    cv2.imwrite(path, img)
    
    res = assess_image_quality(path)
    assert res["is_acceptable"] is True
    assert res["blur_score"] >= 60.0
    assert res["quality_score"] >= 0.50
    assert res["orientation"]["layout"] in ("SQUARE", "PORTRAIT", "LANDSCAPE")
    assert not any("IMAGE_TOO_BLURRY" in w for w in res["warnings"])

# -----------------------------------------------------------------
# Condition 2: Blurry Label Image (Insufficient Evidence)
# -----------------------------------------------------------------
def test_condition_2_blurry_image(tmp_path):
    img = np.ones((800, 800, 3), dtype=np.uint8) * 240
    cv2.putText(img, "BLURRY DECLARATIONS", (80, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    blurred = cv2.GaussianBlur(img, (51, 51), 0)
    
    path = str(tmp_path / "cond2_blurry.jpg")
    cv2.imwrite(path, blurred)
    
    res = assess_image_quality(path)
    assert res["is_acceptable"] is False
    assert res["blur_score"] < 60.0
    assert any("IMAGE_TOO_BLURRY" in w for w in res["warnings"])

# -----------------------------------------------------------------
# Condition 3: Underexposed / Dark Label Image
# -----------------------------------------------------------------
def test_condition_3_underexposed_dark_image(tmp_path):
    # Very dark image with low average intensity (mean brightness < 60)
    img = np.ones((800, 800, 3), dtype=np.uint8) * 25
    cv2.putText(img, "DARK PACKAGING LABEL", (80, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 60, 60), 2)
    
    path = str(tmp_path / "cond3_dark.jpg")
    cv2.imwrite(path, img)
    
    res = assess_image_quality(path)
    assert res["brightness_score"] < 60.0
    assert any("UNDEREXPOSED" in w for w in res["warnings"])

# -----------------------------------------------------------------
# Condition 4: Overexposed / Washed-Out Glare Image
# -----------------------------------------------------------------
def test_condition_4_overexposed_glare_image(tmp_path):
    # Very bright washed-out image (mean brightness > 225)
    img = np.ones((800, 800, 3), dtype=np.uint8) * 245
    cv2.putText(img, "GLARE WASHED LABEL", (80, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (230, 230, 230), 1)
    
    path = str(tmp_path / "cond4_glare.jpg")
    cv2.imwrite(path, img)
    
    res = assess_image_quality(path)
    assert res["brightness_score"] > 225.0
    assert any("OVEREXPOSED" in w for w in res["warnings"])

# -----------------------------------------------------------------
# Condition 5: Low-Resolution Image (< 600px min dimension)
# -----------------------------------------------------------------
def test_condition_5_low_resolution_image(tmp_path):
    # Small image (250 x 200) below legal metrology inspection standard
    img = np.ones((200, 250, 3), dtype=np.uint8) * 200
    cv2.putText(img, "TINY LABEL", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    path = str(tmp_path / "cond5_low_res.jpg")
    cv2.imwrite(path, img)
    
    res = assess_image_quality(path)
    assert res["resolution_score"] < 0.70
    assert any("LOW_RESOLUTION" in w for w in res["warnings"])

# -----------------------------------------------------------------
# Condition 6: Skewed / Rotated Image (Orientation Detection)
# -----------------------------------------------------------------
def test_condition_6_skewed_orientation_image(tmp_path):
    # Create image with horizontal text lines then rotate by 8 degrees
    img = np.ones((800, 1000, 3), dtype=np.uint8) * 240
    for y in range(150, 700, 100):
        cv2.line(img, (100, y), (900, y), (0, 0, 0), 4)
        cv2.putText(img, f"HORIZONTAL DECLARATION LINE AT {y}", (120, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Rotate by 8 degrees
    rotated = rotate_image(img, 8.0)
    path = str(tmp_path / "cond6_skewed.jpg")
    cv2.imwrite(path, rotated)
    
    res = assess_image_quality(path)
    assert "orientation" in res
    assert res["orientation"]["layout"] == "LANDSCAPE"
    assert res["orientation"]["aspect_ratio"] > 1.0

# -----------------------------------------------------------------
# Non-Destructive Preprocessing: Original Preservation Test
# -----------------------------------------------------------------
def test_preprocessing_preserves_original(tmp_path):
    orig_img = np.ones((800, 800, 3), dtype=np.uint8) * 200
    cv2.putText(orig_img, "ORIGINAL PRESERVATION TEST", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    input_path = str(tmp_path / "original.jpg")
    output_path = str(tmp_path / "processed_copy.jpg")
    cv2.imwrite(input_path, orig_img)
    
    # Compute SHA-256 of original prior to preprocessing
    with open(input_path, "rb") as f:
        orig_hash_before = hashlib.sha256(f.read()).hexdigest()
        
    w, h = preprocess_label_image(input_path, output_path)
    
    # Verify processed copy exists and has valid dimensions
    assert os.path.exists(output_path)
    assert w > 0 and h > 0
    
    # Verify original file was NOT modified in any byte
    with open(input_path, "rb") as f:
        orig_hash_after = hashlib.sha256(f.read()).hexdigest()
    assert orig_hash_before == orig_hash_after
