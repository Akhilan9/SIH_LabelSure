import cv2
import numpy as np
from typing import Dict, Any, List

def compute_skew_angle(img: np.ndarray) -> float:
    """Computes median line skew angle using probabilistic Hough transform."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 == 0:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 45.0:
            angles.append(angle)
            
    if not angles:
        return 0.0
    median_angle = float(np.median(angles))
    return median_angle if abs(median_angle) >= 0.5 else 0.0

def assess_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Evaluates image suitability for Legal Metrology OCR compliance auditing:
    - Blur score (Variance of Laplacian)
    - Brightness score (Mean intensity in grayscale)
    - Contrast score (Standard deviation of intensity)
    - Resolution score (Normalized against minimum 800x600 standard)
    - Orientation detection (Aspect ratio, layout classification, Hough line skew angle)
    """
    img = cv2.imread(image_path)
    if img is None:
        return {
            "quality_score": 0.0,
            "blur_score": 0.0,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "resolution_score": 0.0,
            "orientation": {
                "aspect_ratio": 1.0,
                "layout": "UNKNOWN",
                "estimated_skew_angle": 0.0,
                "needs_rotation": False
            },
            "is_acceptable": False,
            "warnings": ["IMAGE_READ_FAILED: The uploaded file could not be decoded as a valid image."]
        }
    
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur evaluation via Laplacian variance
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    blur_variance = float(laplacian.var())
    # Normalization heuristic: >= 150 is sharp, < 75 is blurry
    blur_norm = min(1.0, max(0.0, blur_variance / 200.0))
    
    # 2. Brightness evaluation (0-255)
    mean_brightness = float(np.mean(gray))
    # Ideal range is 90 - 180
    if mean_brightness < 60:
        brightness_score = max(0.1, mean_brightness / 60.0)
    elif mean_brightness > 220:
        brightness_score = max(0.1, (255.0 - mean_brightness) / 35.0)
    else:
        brightness_score = 1.0
        
    # 3. Contrast evaluation (standard deviation of gray values)
    contrast_std = float(np.std(gray))
    # Ideal std > 45
    contrast_score = min(1.0, max(0.1, contrast_std / 55.0))
    
    # 4. Resolution score
    min_dim = min(h, w)
    if min_dim >= 800:
        resolution_score = 1.0
    elif min_dim >= 500:
        resolution_score = 0.75
    elif min_dim >= 300:
        resolution_score = 0.50
    else:
        resolution_score = 0.25

    # 5. Orientation & Skew detection
    skew_angle = compute_skew_angle(img)
    aspect_ratio = round(w / h, 2) if h > 0 else 1.0
    if w > h:
        layout = "LANDSCAPE" if (w / h) > 1.05 else "SQUARE"
    elif h > w:
        layout = "PORTRAIT" if (h / w) > 1.05 else "SQUARE"
    else:
        layout = "SQUARE"
        
    orientation_info = {
        "aspect_ratio": aspect_ratio,
        "layout": layout,
        "estimated_skew_angle": round(skew_angle, 1),
        "needs_rotation": abs(skew_angle) > 1.0
    }
        
    warnings: List[str] = []
    
    if blur_variance < 75.0:
        warnings.append(
            f"IMAGE_TOO_BLURRY: Blur variance is {blur_variance:.1f} (minimum recommended is 75.0). Small text declarations (e.g. MRP, Net Quantity) may be unreadable."
        )
    if mean_brightness < 60.0:
        warnings.append(
            f"UNDEREXPOSED: Average brightness is {mean_brightness:.1f}/255. The package label is poorly lit or in shadow."
        )
    elif mean_brightness > 225.0:
        warnings.append(
            f"OVEREXPOSED: Average brightness is {mean_brightness:.1f}/255. High glare or camera flash is washing out text declarations."
        )
    if contrast_std < 25.0:
        warnings.append(
            f"LOW_CONTRAST: Intensity standard deviation is {contrast_std:.1f}. Low contrast between text and background detected."
        )
    if min_dim < 600:
        warnings.append(
            f"LOW_RESOLUTION: Image resolution is {w}x{h} px. Minimum recommended resolution for Legal Metrology auditing is 800px on smallest dimension."
        )
    if abs(skew_angle) > 5.0:
        warnings.append(
            f"IMAGE_SKEWED: Label is tilted by {skew_angle:.1f} degrees. Automated deskewing will be applied."
        )
        
    # Composite quality score (weighted sum)
    # Blur is heavily weighted because legal metrology requires legible font numerals
    quality_score = float(
        (0.40 * blur_norm) +
        (0.25 * brightness_score) +
        (0.15 * contrast_score) +
        (0.20 * resolution_score)
    )
    
    # Acceptable if quality score >= 0.50 and no severe blur (< 60)
    is_acceptable = (quality_score >= 0.50) and (blur_variance >= 60.0)
    
    return {
        "quality_score": round(quality_score, 3),
        "blur_score": round(blur_variance, 1),
        "brightness_score": round(mean_brightness, 1),
        "contrast_score": round(contrast_std, 1),
        "resolution_score": round(resolution_score, 2),
        "orientation": orientation_info,
        "is_acceptable": is_acceptable,
        "warnings": warnings
    }
