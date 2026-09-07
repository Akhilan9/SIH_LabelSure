# APEX LabelSure - System Architecture & Regulatory Specification

## 1. Executive Summary
**APEX LabelSure** is an enterprise-grade, research-oriented regulatory compliance inspection platform designed for the **Department of Consumer Affairs, Government of India**, to enforce the **Legal Metrology (Packaged Commodities) Rules, 2011** (LMPC Rules, 2011) and subsequent amendments (2017, 2021, 2022, 2024, 2025, 2026).

The platform solves the critical challenge of AI hallucination in legal adjudication by strictly separating:
1. **Perceptual AI & Computer Vision Pipeline:** Text detection, optical character recognition (OCR), image quality gating, spatial layout localization, and entity extraction.
2. **Deterministic, Version-Aware Legal Rule Engine:** Auditing observed declarations against statutory requirements, applicable rule versions, commodity context, and threshold conditions.
3. **RuleLens Explainability & Inspector Review:** Providing bidirectional traceability from statutory clause to raw bounding boxes with cryptographic hash protection and immutable human review logs.

---

## 2. Statutory Regulatory Framework & Rule Corpus

### 2.1 Department of Consumer Affairs Regulatory Basis
Primary statutory references:
- **Legal Metrology Act, 2009 (Act No. 1 of 2010)**: Sections 18, 36 (Offences and penalties for non-standard packages).
- **Legal Metrology (Packaged Commodities) Rules, 2011 (LMPC Rules 2011)**:
  - **Rule 6(1)(a)**: Name and complete address of the manufacturer / packer / importer.
  - **Rule 6(1)(b)**: Common or generic name of the commodity contained in the package.
  - **Rule 6(1)(c)**: Net quantity in standard units of weight, measure, or number (strict metric symbols: `g`, `kg`, `ml`, `l`, `m`, `cm`, `mm`, `N`, `U`; non-standard abbreviations like `gms`, `kgs`, `ltrs` violate the Act).
  - **Rule 6(1)(d)**: Month and year of manufacture or packing or import.
  - **Rule 6(1)(da)**: Mandatory Unit Sale Price (USP) for packages where net quantity exceeds 1 kg/1 litre or contains multiple discrete items.
  - **Rule 6(1)(e)**: Maximum Retail Price (MRP) in format `"MRP ₹ xx.xx incl. of all taxes"`.
  - **Rule 6(1)(f)**: Consumer grievance redressal: Name, address, telephone number, and email address of person/office to contact.
  - **Rule 6(10) (E-Commerce Amendments 2017)**: E-commerce marketplace display of mandatory declarations prior to purchase.
  - **Rule 7 & Rule 8**: Principal Display Panel (PDP) dimensions and minimum numeral/font height based on net quantity brackets.

### 2.2 Versioned Regulatory Corpus Architecture
The rule engine does not hardcode static rules. Rules are maintained in versioned declarations (`LMPC-2011-BASE`, `LMPC-2017-AMENDMENT`, `LMPC-2021-AMENDMENT`, `LMPC-2026-RULES`):
```json
{
  "rule_id": "LMPC_MRP_001",
  "rule_version": "2026.1",
  "clause_reference": "Rule 6(1)(e)",
  "requirement": "Declaration of Maximum Retail Price (MRP) inclusive of all taxes",
  "applicability": {
    "package_type": "pre_packaged",
    "is_exempt": false
  },
  "validation_logic": {
    "field": "MRP",
    "operator": "EXISTS",
    "composite_and": [
      { "field": "MRP.value", "operator": "GREATER_THAN", "value": 0 },
      { "field": "MRP.inclusive_of_taxes", "operator": "EQUALS", "value": true }
    ]
  },
  "severity": "CRITICAL",
  "effective_from": "2011-04-01",
  "effective_to": null,
  "source_document": "Legal Metrology (Packaged Commodities) Rules, 2011",
  "source_url": "https://consumeraffairs.gov.in/pages/legal-metrology-act"
}
```

---

## 3. System Architecture & Component Interactions

```
+---------------------------------------------------------------------------------+
|                                PRESENTATION TIER                                |
|                                                                                 |
|   +------------------------------------+   +--------------------------------+   |
|   |  Flutter Mobile Field Client       |   |  React 19 Web Admin Dashboard  |   |
|   |  (Offline SQLite / Camera / Sync)  |   |  (RuleLens, Analytics, Review) |   |
|   +-----------------+------------------+   +---------------+----------------+   |
+---------------------|--------------------------------------|--------------------+
                      | REST API / JSON                      | REST API / JSON
                      v                                      v
+---------------------------------------------------------------------------------+
|                               APPLICATION TIER                                  |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                     FastAPI Compliance Backend Engine                   |   |
|   |  - Auth & RBAC (JWT, Bcrypt)          - Inspection Orchestrator         |   |
|   |  - Idempotent Sync Manager            - Evidence Immutability Ledger    |   |
|   +----+--------------------+--------------------+---------------------+----+   |
|        |                    |                    |                     |        |
|        v                    v                    v                     v        |
|  +------------+       +------------+       +------------+        +------------+ |
|  | Image CV   |       | ONNX OCR   |       | Context    |        | RuleLens   | |
|  | & Quality  |       | PP-OCRv4   |       | Engine     |        | & ReportLab| |
|  +------------+       +------------+       +------------+        +------------+ |
+---------------------------------------------------------------------------------+
|                                 DATA TIER                                       |
|                                                                                 |
|   +------------------------------------+   +--------------------------------+   |
|   | PostgreSQL 16 (Audited Relational) |   | MinIO / Local Evidence Store   |   |
|   | Inspections, Rules, Audit Logs     |   | Original Images, Preprocessed  |   |
|   +------------------------------------+   +--------------------------------+   |
+---------------------------------------------------------------------------------+
```

---

## 4. Multi-Stage Pipeline Specification

### 4.1 Stage 1: Quality Assessment Gate
Before invoking OCR, images are evaluated by computer vision metrics:
- **Blur Assessment:** Laplacian operator variance $\text{Var}(\nabla^2 I)$. If $\text{Var} < 100.0$, image is tagged as blurry.
- **Exposure Analysis:** Mean and standard deviation of luminance channel (HSV/YUV). Underexposed ($< 45$) or overexposed ($> 220$) images generate evidence warnings.
- **Resolution Verification:** Minimum threshold of 800px on the shortest dimension for legibility.
- **Uncertainty Rule:** When image quality fails the threshold, the system **never** marks missing declarations as `FAIL`. It strictly classifies them as `UNCERTAIN` (`NEEDS_BETTER_EVIDENCE`) and notifies the inspector.

### 4.2 Stage 2: Computer Vision Preprocessing
- Deskewing & orientation correction via Hough line transform and projection profiles.
- Contrast-Limited Adaptive Histogram Equalization (CLAHE) for low-contrast metallic or transparent packaging.
- Bilateral filtering to preserve text edges while attenuating print dot matrix noise.
- Storage of both original unprocessed image (with SHA-256 hash) and preprocessed image.

### 4.3 Stage 3: High-Precision OCR Engine
- Driven by `rapidocr-onnxruntime` executing PaddleOCR PP-OCRv4 models (DBNet text detection + SVTR text recognition).
- Extracts precise 4-point bounding polygons, confidence scores, line texts, and reading order.

### 4.4 Stage 4: Structured Declaration Extractor
Extracts 14+ Legal Metrology fields:
- `PRODUCT_NAME`, `COMMON_GENERIC_NAME`
- `MANUFACTURER`, `PACKER`, `IMPORTER`
- `COUNTRY_OF_ORIGIN`
- `NET_QUANTITY` (value, unit, verification of legal metric units)
- `MRP` (currency symbol, value, tax inclusion declaration)
- `MANUFACTURE_DATE`, `PACK_DATE`, `BEST_BEFORE`, `USE_BY`
- `CONSUMER_CARE` (toll-free number, email, nodal officer address)
- `UNIT_SALE_PRICE` (calculated per unit price)
- `DIMENSIONS`

### 4.5 Stage 5: Product Context Engine
Aggregates inspection conditions:
- Commodity Category (Food, Beverage, Cosmetics, Electronics, Commodity)
- Package Type (Pre-packaged single, multi-piece, combination, wholesale)
- Origin Type (Domestic manufactured vs Imported)
- Channel (Physical retail vs E-commerce listing)
- Inspection Date (determines effective rule version)

### 4.6 Stage 6: Deterministic Rule Engine
Evaluates statutory rules based on product context and extracted declarations:
- Operators: `EXISTS`, `NOT_EXISTS`, `EQUALS`, `NOT_EQUALS`, `GREATER_THAN`, `LESS_THAN`, `BETWEEN`, `REGEX`, `UNIT_VALIDATION`, `DATE_VALIDATION`, `CONTEXT_CONDITION`, `COMPOSITE_AND`, `COMPOSITE_OR`.
- Outcomes:
  - `PASS`: Requirement met with high confidence.
  - `FAIL`: Requirement legally absent or violated with satisfactory image quality.
  - `UNCERTAIN`: Low confidence or insufficient image quality.
  - `NOT_APPLICABLE`: Requirement not mandated for this commodity context.

### 4.7 Stage 7: RuleLens Explanation Layer
Constructs transparent legal adjudication cards containing:
- Clause citation and requirement title.
- Observed declaration text, bounding box coordinates, and source image id.
- Statutory expectation and delta reason.
- AI confidence vs diagnostic uncertainty metrics.

### 4.8 Stage 8: Inspector Review & Immutable Audit Ledger
- Allows inspectors to correct extracted text, override AI conclusions, add explanatory comments, and sign off.
- Preserves original AI outputs alongside human decisions in append-only `audit_logs` table.

---

## 5. Security & RBAC Model
Role permissions:
- **ADMIN:** System configuration, user management, rule corpus management, full audit log access.
- **SUPERVISOR:** Case review, inspection sign-off, analytics reporting.
- **INSPECTOR:** Create inspections, upload images, execute analysis, review and override findings, generate reports.
- **VIEWER:** Read-only access to finalized inspection cases and compliance reports.
