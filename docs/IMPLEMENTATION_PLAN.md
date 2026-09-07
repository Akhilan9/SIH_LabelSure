# APEX LabelSure - Implementation Plan & Engineering Roadmap

## Implementation Strategy
This plan follows a strict dependency-ordered methodology for implementing APEX LabelSure:
1. **Contracts & Schemas (`contracts/`):** Freeze common JSON schemas.
2. **Backend Core & Database (`backend/`):** Models, migrations, seeds, JWT auth, RBAC.
3. **Computer Vision & Preprocessing (`backend/app/cv/`, `ai/`):** Blur (Laplacian), brightness, contrast, resolution gating, enhancement.
4. **OCR & Text Localization (`backend/app/ocr/`):** RapidOCR PP-OCRv4 ONNX pipeline, normalized bounding boxes.
5. **Declaration Extraction (`backend/app/extraction/`):** Hybrid regex + anchor + spatial extractor for 14+ Legal Metrology fields.
6. **Product Context Engine (`backend/app/services/context_engine.py`):** Commodity metadata, pack types, e-commerce vs retail, import flags.
7. **Version-Aware Deterministic Rule Engine (`backend/app/rule_engine/`):** LMPC 2011 to 2026 rulesets, boolean/unit/date operators, uncertainty mapping.
8. **RuleLens & Human Review (`backend/app/api/review.py`):** Bidirectional explainability layer, manual override, tamper-evident audit logging.
9. **Official PDF Inspection Certificate (`backend/app/reports/`):** High-resolution ReportLab certificate generation with evidence thumbnails.
10. **Web Admin Dashboard (`apps/admin-web/`):** React 19 + TypeScript + Vite with interactive BBox canvas, RuleLens inspector, and analytics.
11. **Mobile Inspector App (`apps/mobile/`):** Flutter + Dart offline-first client architecture with SQLite sync queue.
12. **Automated Verification & Evaluation (`backend/tests/`, `evaluation/`):** Pytest test suite and 10 benchmark evaluation cases.
