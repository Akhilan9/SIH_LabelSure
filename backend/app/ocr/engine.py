import time
import numpy as np
import cv2
from typing import Dict, Any, List, Optional
from rapidocr_onnxruntime import RapidOCR

_ocr_engine_instance: Optional[RapidOCR] = None

def get_ocr_engine() -> RapidOCR:
    global _ocr_engine_instance
    if _ocr_engine_instance is None:
        # RapidOCR initializes the DBNet detector, direction classifier, and SVTR recognizer
        _ocr_engine_instance = RapidOCR()
    return _ocr_engine_instance

def run_ocr_on_image(image_path: str) -> Dict[str, Any]:
    """
    Executes PP-OCRv4 text detection and recognition on the image.
    Extracts lines with bounding polygons, rectangular bboxes, and confidence.
    """
    engine = get_ocr_engine()
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image at path: {image_path}")
    
    h, w = img.shape[:2]
    start_time = time.time()
    
    # RapidOCR returns: results (list of [box, text, score]), elapse_list
    results, elapse = engine(img)
    processing_time_ms = round((time.time() - start_time) * 1000.0, 2)
    
    lines: List[Dict[str, Any]] = []
    text_pieces: List[str] = []
    
    if results:
        for idx, item in enumerate(results):
            # item is: [dt_boxes, text, score]
            poly = item[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            text = str(item[1]).strip()
            conf = float(item[2])
            
            # Compute axis-aligned bounding box [x_min, y_min, x_max, y_max]
            poly_np = np.array(poly)
            x_min = float(np.min(poly_np[:, 0]))
            y_min = float(np.min(poly_np[:, 1]))
            x_max = float(np.max(poly_np[:, 0]))
            y_max = float(np.max(poly_np[:, 1]))
            
            # Normalize bounding box coordinates relative to image width/height (0.0 to 1.0)
            norm_bbox = [
                round(max(0.0, min(1.0, x_min / w)), 4),
                round(max(0.0, min(1.0, y_min / h)), 4),
                round(max(0.0, min(1.0, x_max / w)), 4),
                round(max(0.0, min(1.0, y_max / h)), 4)
            ]
            
            lines.append({
                "line_index": idx,
                "text": text,
                "confidence": round(conf, 4),
                "bbox": norm_bbox,
                "pixel_bbox": [int(x_min), int(y_min), int(x_max), int(y_max)],
                "polygon": [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in poly]
            })
            text_pieces.append(text)
            
    full_text = "\n".join(text_pieces)
    
    return {
        "engine_name": "PaddleOCR / RapidOCR (PP-OCRv4)",
        "engine_version": "v4.0.0-ONNX",
        "processing_time_ms": processing_time_ms,
        "image_width": w,
        "image_height": h,
        "lines": lines,
        "full_text": full_text
    }
