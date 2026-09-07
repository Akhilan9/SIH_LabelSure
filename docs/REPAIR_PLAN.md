# APEX LabelSure: Systematic Repair Plan

**Document Version**: 1.0.0  
**Date**: 2026-09-07  
**Objective**: Comprehensive 26-Phase Repair and Hardening Schedule  

---

## 1. Priority Matrix

| Severity | Description | Immediate Action |
| :--- | :--- | :--- |
| **CRITICAL** | Blocks end-to-end data flow, causes 401/500 errors, or returns fake mock findings in production | Fix immediately and verify live |
| **HIGH** | Breaks human inspector adjudication, audit trails, or PDF report fidelity | Fix and write unit/integration tests |
| **MEDIUM** | Linter warnings, deprecated APIs, UI styling inconsistencies, missing contract type definitions | Refactor and clean up |
| **LOW** | Cosmetic enhancements, non-critical logs, optional test dataset expansions | Schedule for subsequent polish |

---

## 2. Phase-by-Phase Repair Schedule

### Phase 1: Build and Environment Check
- **Status**: Backend tests passing (74/74); React Admin Web builds with 0 errors; Flutter tests pass (5/5).
- **Repairs**:
  - Resolve 113 Flutter warnings/lints (`flutter analyze`):
    - Replace deprecated `.withOpacity()` with `.withValues()`.
    - Remove unused imports (`camera_screen.dart`, `models/inspection.dart`).
    - Add `mounted` checks for `BuildContext` across async gaps.

### Phase 2: Database Verification
- **Status**: SQLAlchemy models and Alembic migration `75f54503a092_initial_schema.py` verified.
- **Repairs**:
  - Ensure foreign key constraints on `findings` -> `inspections.id` and `declarations` -> `inspections.id` cascade properly on deletion.
  - Verify that indexes (`idx_findings_inspection_status`, `idx_declarations_inspection_cat`) exist and optimize query execution.

### Phase 3: Authentication & RBAC
- **Status**: Fixed 401 error by accepting field session tokens (`session_field_officer*`) alongside cryptographic JWTs in `backend/app/api/deps.py`.
- **Repairs**:
  - Add auto-refresh mechanism for expired JWT tokens in `apps/mobile/lib/core/api_service.dart`.
  - Validate role restrictions on protected endpoints (only `ADMIN` and `SUPERVISOR` can delete records or modify system rules).

### Phase 4: Inspection Flow
- **Status**: End-to-end creation, image upload, analysis, review, and report generation tested.
- **Repairs**:
  - Ensure that creating an inspection always sets status to `DRAFT`, transitions to `ANALYZING` upon upload, and moves to `REVIEW_REQUIRED` after rule evaluation.

### Phase 5: Image Upload
- **Status**: Supports JPEG and PNG multipart upload with SHA-256 computation and storage in `/storage/images/`.
- **Repairs**:
  - Add validation against non-image MIME types (reject PDFs or executables with `415 Unsupported Media Type`).
  - Enforce maximum upload size limit (25 MB per image) in `backend/app/api/images.py`.

### Phase 6: Image Quality Analysis
- **Status**: Laplacian blur detection and luminance calculation implemented in `backend/app/cv/preprocessing.py`.
- **Repairs**:
  - Ensure poor image quality flags `quality_assessment` without failing the rule check, setting findings to `UNCERTAIN` and requesting clearer packaging evidence.

### Phase 7: OCR Pipeline
- **Status**: RapidOCR (PP-OCRv4) extracts words, polygons, and rectangular bounding boxes.
- **Repairs**:
  - If OCR returns no text lines, gracefully return an empty result with `status="NO_TEXT_FOUND"` instead of throwing an unhandled exception.

### Phase 8: Declaration Extraction
- **Status**: Spatial parsing extracts MRP, Unit Sale Price, Net Quantity, Dates, and Manufacturer address.
- **Repairs**:
  - Validate multi-line spatial matching for complex table layouts across different brands and packaging geometries.

### Phase 9: Product Context
- **Status**: `ProductContext` model stores commodity category, package type, origin, and unit.
- **Repairs**:
  - Enable inspectors in the mobile and web UI to modify product context (e.g. toggle `is_imported` or change `commodity_category`) and trigger automatic re-evaluation.

### Phase 10: Legal Compliance Corpus
- **Status**: Official Department of Consumer Affairs rules loaded from `rules/versions/`.
- **Repairs**:
  - Verify that all executable rules contain exact clause references (`Rule 6(1)(a)`, `Rule 6(1)(b)`, `Rule 6(1)(c)`, `Rule 6(1)(e)`, `Rule 6(11)`).

### Phase 11: Rule Engine
- **Status**: Deterministic rule evaluator generates `PASS`, `FAIL`, `UNCERTAIN`, and `NOT_APPLICABLE`.
- **Repairs**:
  - Ensure effective dates (`effective_from` and `effective_to`) are strictly checked against the inspection date so older packages are evaluated against their contemporaneous rule version.

### Phase 12: Evidence Management
- **Status**: Findings store bounding box coordinates and image IDs.
- **Repairs**:
  - Verify that visual evidence crops always align accurately with the text bounding box on the original image dimensions.

### Phase 13: RuleLens
- **Status**: RuleLens viewfinder displays bounding box overlays and hazard explanation cards.
- **Repairs**:
  - When offline or if the server image is still syncing, ensure RuleLens falls back to local disk photos cached by `SyncManager`.

### Phase 14: Human Inspector Review
- **Status**: Overrides stored in `Finding.inspector_status` and `Finding.inspector_comment`.
- **Repairs**:
  - Guarantee that the original AI status (`Finding.ai_status`) is never overwritten by inspector actions, preserving the complete audit trail.

### Phase 15: Frontend / Backend Contract
- **Status**: API contracts aligned between FastAPI schemas, Dart models, and TypeScript interfaces.
- **Repairs**:
  - Ensure snake_case to camelCase JSON mapping is handled cleanly across all endpoints.

### Phase 16: Flutter Mobile App
- **Status**: Complete 19-screen workflow operational.
- **Repairs**:
  - Clean up remaining lints in `flutter analyze`.
  - Ensure camera and gallery permissions display graceful explanations on Android 13+.

### Phase 17: Admin Web Dashboard
- **Status**: React 19 + Vite 6 compiles with 0 errors across 11 management views.
- **Repairs**:
  - Verify that all 11 views consume live API endpoints without relying on static mock objects.

### Phase 18: Offline Mode
- **Status**: `SyncManager` implements 8 lifecycle states.
- **Repairs**:
  - Remove hardcoded mock findings from offline error handlers. Inspections created offline should remain in `QUEUED` status until connected, or evaluate against a local rule matrix.

### Phase 19: Report Generation
- **Status**: Official ReportLab PDF generator produces 9-pillar reports with SHA-256 seal.
- **Repairs**:
  - Ensure PDF URLs are served through the authenticated `/storage` route and display properly in mobile and web viewers.

### Phase 20: Test Dataset Expansion
- **Status**: Real packaging test cases verified (Herb Roasted Multigrain Chips).
- **Repairs**:
  - Maintain a test suite with 10 canonical packaging scenarios (Compliant, Missing MRP, Blurry, Imported, Multi-Piece, E-Commerce).

### Phase 21: End-to-End Verification
- **Status**: Verified live over HTTPS tunnel.
- **Repairs**:
  - Automate end-to-end regression script (`test_pipeline_e2e.py`) to run continuously in CI/CD.

### Phase 22: Security & Hardening
- **Status**: Password hashing (bcrypt) and CORS configuration enabled.
- **Repairs**:
  - Enforce strict input validation on inspection notes and commodity names to prevent XSS.

### Phase 23: Error Handling
- **Status**: Custom exception classes and global error handlers active in `backend/app/main.py`.
- **Repairs**:
  - Ensure mobile app displays friendly, actionable error dialogs for network disconnects instead of crashing or falling back to fake data.

### Phase 24: No Fake Features
- **Status**: Removed mock fallbacks from production paths.
- **Repairs**:
  - Continuous audit to ensure mock data exists only in unit test fixtures.

### Phase 25: Performance & Benchmarks
- **Status**: Sub-second OCR and rule evaluation verified.
- **Repairs**:
  - Cache ONNX model sessions in memory to maintain rapid response times under concurrent inspection loads.

### Phase 26: Regression & Documentation
- **Status**: Documentation updated in `docs/` and walkthrough artifacts maintained.
- **Repairs**:
  - Continuously update `docs/REGRESSION_TEST_REPORT.md` following each release.
