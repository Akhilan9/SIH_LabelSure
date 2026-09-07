# APEX LabelSure: Current Architecture

**System**: APEX LabelSure  
**Authority**: Department of Consumer Affairs, Government of India  
**Statutory Framework**: Legal Metrology (Packaged Commodities) Rules, 2011 (with 2017, 2021, and 2026 Amendments)  
**Document Version**: 2.0.0  

---

## 1. High-Level System Architecture

```
                          APEX LABELSURE
                                │
               ┌────────────────┴────────────────┐
               │                                 │
               ▼                                 ▼
      Flutter Mobile App                 React Admin Web
     (Field Enforcement)               (Command & Control)
               │                                 │
               └────────────────┬────────────────┘
                                ▼
                       FastAPI Backend
                  (Port 8000 / HTTPS Tunnel)
                                │
                        Inspection API
                                │
               ┌────────────────┴────────────────┐
               │                                 │
               ▼                                 ▼
          AI Pipeline                      Context Engine
               │                                 │
        ┌──────┼────────┐                        │
        │      │        │                        │
        ▼      ▼        ▼                        │
     Quality  OCR     CV/NLP                     │
     (Blur,  (PP-OCR  (Spatial                   │
     Light)   v4)     Parsing)                   │
        │      │        │                        │
        └──────┴────────┘                        │
               │                                 │
               ▼                                 │
        Structured Declarations ◄────────────────┘
               │
               ▼
       Version-Aware Rule Engine
     (LMPC 2011, 2017, 2021, 2026)
               │
               ▼
     PASS / FAIL / UNCERTAIN / N/A
               │
               ▼
       Hazard / RuleLens Engine
   (5-Step Why Is It Wrong Matrix)
               │
               ▼
      Human Inspector Verification
   (Accept, Reject, Edit, Override)
               │
               ▼
        Final Inspection
          /          \
         /            \
        ▼              ▼
     ReportLab       Audit Trail
     Official PDF   (Immutable Logs)
        │              │
        └───────┬──────┘
                ▼
      PostgreSQL + Storage
   (Relational Data + Evidence)
```

---

## 2. Core Components & Technical Stack

### 2.1 Mobile Application (`apps/mobile`)
- **Framework**: Flutter 3.33 / Dart 3.x
- **Key Modules**:
  - `InspectionAreaScreen`: Setup inspection area and target jurisdictions.
  - `CameraScreen` & `GalleryScreen`: Multi-panel image acquisition with flash and grid controls.
  - `ImageReviewScreen`: Pre-upload crop and preview before queue ingestion.
  - `AnalysisScreen`: Real-time pipeline tracking and statutory breakdown matrix.
  - `RuleLensScreen`: Visual evidence viewfinder displaying overlaid bounding boxes and the 5-step hazard explanation card.
  - `ComprehensiveReportScreen`: 9-pillar official statutory report viewer with PDF export.
  - `SyncManager`: 8-state offline synchronization lifecycle (`DRAFT`, `QUEUED`, `UPLOADING`, `ANALYZING`, `REVIEW_REQUIRED`, `FINALIZED`, `SYNCED`, `SYNC_FAILED`).

### 2.2 Admin Web Dashboard (`apps/admin-web`)
- **Framework**: React 19, TypeScript 5.7, Vite 6
- **Styling**: Modern dark/light glassmorphic UI with CSS tokens and Lucide React icons.
- **Views**:
  - `DashboardView`: High-level metrics, compliance rates, and recent inspection activity.
  - `InspectionsView`: Filterable list of all field inspections with status badges.
  - `InspectionDetailView`: Full inspection dossier including product context and timeline.
  - `EvidenceView`: Interactive image viewer displaying bounding box overlays.
  - `RuleLensView`: Comprehensive RuleLens adjudicator with human override buttons.
  - `RuleExplorerView`: Legal Metrology corpus browser with effective date filters.
  - `ReportsView`: Certificate downloads and digital verification seals.
  - `AnalyticsView`: Geographic compliance distributions and risk hot-spots.
  - `AuditLogsView`: Immutable log stream of all inspector actions.
  - `UsersView`: Role-based user management (Admin, Inspector, Supervisor, Viewer).

### 2.3 Backend API (`backend/app`)
- **Framework**: FastAPI (Python 3.13), Uvicorn ASGI
- **Authentication**: OAuth2 Password Bearer with JWT + Field Session Token support.
- **Database ORM**: SQLAlchemy 2.0 with Alembic database migrations.
- **Database**: PostgreSQL 16 (production) / SQLite (testing & local dev).

---

## 3. The AI & Perception Pipeline

### 3.1 Image Quality Assessment (`backend/app/cv/preprocessing.py`)
- Evaluates image quality prior to OCR:
  - **Laplacian Variance**: Assesses blurriness (threshold < 100.0 flags blur).
  - **Mean Luminance**: Detects under-exposure (< 40.0) or over-exposure (> 220.0).
  - **Resolution & Aspect Ratio**: Ensures package label details are legible.
- **Critical Policy**: Poor image quality does NOT generate a legal violation (`FAIL`). Instead, it issues a quality warning and produces `UNCERTAIN` to request clearer evidence.

### 3.2 OCR Engine (`backend/app/ocr/engine.py`)
- **Engine**: RapidOCR with PP-OCRv4 ONNX weights.
- **Capabilities**:
  - Extracts text, confidence scores, and bounding polygon coordinates `[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]`.
  - Normalizes coordinates to rectangular bounding boxes `[x1, y1, x2, y2]`.
  - Supports English, Devanagari numerals, currency symbols (`₹`, `Rs.`), dates, and metric units.

### 3.3 Spatial & Multi-Column Declaration Extraction (`backend/app/extraction/extractor.py`)
- Employs spatial line association and domain regex patterns to extract:
  - `PRODUCT_NAME`: Commodity identity and generic naming.
  - `MANUFACTURER`: Manufacturer / packer / importer address and pin code.
  - `NET_QUANTITY`: Numeric quantity and metric units (`g`, `kg`, `ml`, `L`, `pcs`). Excludes nutritional serving sizes.
  - `MRP`: Maximum Retail Price, verifying statutory phrase *"inclusive of all taxes"*.
  - `UNIT_SALE_PRICE`: Unit sale price statement (`₹ / g`, `₹ / kg`, `₹ / ml`).
  - `DATES`: Date of manufacture, packaging, expiry, or best before.
  - `CONSUMER_CARE`: Email, telephone helpline, and physical consumer care address.

---

## 4. Deterministic Rule Engine & Explainability

### 4.1 Legal Rule Corpus (`rules/versions/`)
- Versioned rule definitions corresponding to official Department of Consumer Affairs notifications:
  - `lmpc_2011_base.json`: Base Legal Metrology Rules, 2011.
  - `lmpc_2017_amendments.json`: Mandatory consumer care & e-commerce provisions.
  - `lmpc_2021_amendments.json`: Mandatory Unit Sale Price provisions.
  - `lmpc_2026_rules.json`: Current active enforcement rule set.

### 4.2 Adjudication Logic (`backend/app/rule_engine/evaluator.py`)
- Deterministic evaluation of applicability conditions:
  - Checks inspection date against rule `effective_from` and `effective_to`.
  - Verifies commodity category (`FOOD_BEVERAGE`, `GENERAL_COMMODITY`, etc.).
  - Evaluates package type (`SINGLE_PRE_PACKAGED`, `MULTI_PIECE`, `E_COMMERCE`).
- Produces unambiguous statutory findings:
  - `PASS`: Requirement fully satisfied by observed package declaration.
  - `FAIL`: Mandatory declaration missing or legally defective.
  - `UNCERTAIN`: Declaration partially obscured, confidence low, or image degraded.
  - `NOT_APPLICABLE`: Rule not applicable to this commodity category or date.

### 4.3 Hazard & Violation Explanation Engine (`backend/app/rule_engine/hazard_engine.py`)
- Maps every non-compliance finding to a 5-step hazard explanation:
  1. `Detected Issue`: Specific defect detected on package label.
  2. `Applicable Rule`: Exact statutory section and rule citation.
  3. `Reason for Non-Compliance`: Legal basis why the packaging fails compliance.
  4. `Consumer / Regulatory Risk`: Consumer harm (price gouging, allergen risk) and regulatory liability (Section 36(1) compounding fines up to ₹25,000).
  5. `Evidence from Package`: The exact OCR text snippet and visual evidence reference.

---

## 5. Official Inspection Reports & Evidence Management

### 5.1 9-Pillar Inspection Report (`backend/app/reports/generator.py`)
The system compiles a comprehensive statutory report containing:
1. **Header & Digital Seal**: Certificate number, QR validation, SHA-256 digital fingerprint.
2. **Product Context**: Commodity name, brand, category, origin, package type.
3. **Extracted Declarations**: Complete table of all observed declarations with confidence scores.
4. **Applicable Legal Rules**: List of all rules evaluated with clause citations.
5. **Compliance Status Breakdown**: Overall verdict, pass/fail counts, compliance rate.
6. **Detected Violations**: Itemized non-compliances with legal risk assessments.
7. **Visual Evidence Crops**: High-resolution cropped image sections highlighting defects.
8. **Inspector Adjudication**: Digital signature, officer badge number, and remarks.
9. **Recommended Follow-up Actions**: Statutory notices (Section 18, 36(1)) and compounding assessments (Section 48).

---

## 6. Database Entity Relationships

```
┌──────────────┐       1:N       ┌──────────────────┐       1:N       ┌─────────────────────┐
│    User      ├────────────────►│    Inspection    ├────────────────►│   InspectionImage   │
│ (Inspectors, │                 │ (Status, Verdict,│                 │ (Path, Hash, Quality│
│    Admins)   │                 │  Commodity)      │                 │  Dimensions)        │
└──────────────┘                 └────────┬─────────┘                 └──────────┬──────────┘
                                          │                                      │
                                          │ 1:1                                  │ 1:1
                                          ▼                                      ▼
                                 ┌──────────────────┐                 ┌─────────────────────┐
                                 │  ProductContext  │                 │      OcrResult      │
                                 │ (Category, Units,│                 │ (Text, Bounding     │
                                 │  Origin, Dates)  │                 │  Boxes, Polygons)   │
                                 └──────────────────┘                 └─────────────────────┘
                                          │
                                          │ 1:N
                        ┌─────────────────┼─────────────────┐
                        │                 │                 │
                        ▼                 ▼                 ▼
             ┌──────────────────┐ ┌────────────────┐ ┌────────────────┐
             │   Declaration    │ │    Finding     │ │     Report     │
             │ (MRP, Qty, Dates,│ │ (RuleId, AI    │ │ (Certificate,  │
             │  Manufacturer)   │ │  Status, Final │ │  PDF URL, Hash)│
             └──────────────────┘ │  Review)       │ └────────────────┘
                                  └────────────────┘
```
