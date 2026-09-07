import cv2
import numpy as np
from pathlib import Path
from typing import Tuple

def load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image at path: {image_path}")
    return image

def compute_deskew_angle(image: np.ndarray) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    # Probabilistic Hough line transform
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 == 0:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        # Keep near-horizontal lines within +/- 45 degrees
        if abs(angle) < 45.0:
            angles.append(angle)
            
    if not angles:
        return 0.0
    
    # Return median angle to reject outliers
    median_angle = float(np.median(angles))
    # Ignore negligible angles
    if abs(median_angle) < 0.5:
        return 0.0
    return median_angle

def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    if abs(angle) < 0.1:
        return image
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new bounding dimensions
    cos = np.abs(rot_mat[0, 0])
    sin = np.abs(rot_mat[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    rot_mat[0, 2] += (new_w / 2) - center[0]
    rot_mat[1, 2] += (new_h / 2) - center[1]
    
    rotated = cv2.warpAffine(
        image, rot_mat, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated

def enhance_text_regions(image: np.ndarray) -> np.ndarray:
    """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) and mild denoising."""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # CLAHE on luminance channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l)
    
    # Merge and convert back to BGR
    enhanced_lab = cv2.merge((enhanced_l, a, b))
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # Bilateral filter to smooth texture while keeping text edges crisp
    denoised = cv2.bilateralFilter(enhanced_bgr, d=5, sigmaColor=35, sigmaSpace=35)
    return denoised

def preprocess_label_image(input_path: str, output_path: str) -> Tuple[int, int]:
    """
    Complete non-destructive preprocessing pipeline:
    1. Loads original image
    2. Corrects skew/rotation
    3. Enhances text regions (CLAHE + bilateral smoothing)
    4. Writes processed version to output_path while leaving original intact
    Returns: (width, height) of preprocessed image
    """
    img = load_image(input_path)
    angle = compute_deskew_angle(img)
    if abs(angle) > 0.5:
        img = rotate_image(img, angle)
    enhanced = enhance_text_regions(img)
    cv2.imwrite(output_path, enhanced, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    h, w = enhanced.shape[:2]
    return (w, h)
