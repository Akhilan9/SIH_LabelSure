# APEX LabelSure — Demonstration & Evaluation Guide

**Target Audience**: Smart India Hackathon (SIH) Evaluators, Department of Consumer Affairs Juries, Legal Metrology Officers, Technical Reviewers  
**Platform**: APEX LabelSure — Legal Metrology Packaged Commodities AI Inspection System  
**System Architecture**: FastAPI Backend + React/TypeScript Admin Web Dashboard + Flutter Mobile App  

---

## 1. Quick Start & Demonstration Environment

Both primary demonstration servers are already running and accessible locally:

| Service | Local URL | Description |
| :--- | :--- | :--- |
| **Admin Web Dashboard** | [http://localhost:5173](http://localhost:5173) | 11-Screen React + TypeScript Inspector & Officer Portal |
| **FastAPI Core Gateway** | [http://localhost:8000](http://localhost:8000) | Regulatory Inspection Engine & AI Inference Services |
| **Interactive API Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI (28 Live REST Endpoints) |

### Demonstration Credentials

The platform comes pre-seeded with 4 distinct administrative and enforcement roles:

| Role | Username | Password | Intended Workflow / Permissions |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin` | `Admin@123` | Full access: user management, rule updates, audit logs |
| **INSPECTOR** | `inspector1` | `Inspector@123` | Field enforcement: capture images, run analysis, review findings |
| **SUPERVISOR** | `supervisor1` | `Super@123` | Senior review: approval of contested findings, regional analytics |
| **VIEWER** | `viewer1` | `Viewer@123` | Read-only compliance auditor: view reports and analytics |

---

## 2. Core Innovation Talking Points for Judges

When introducing APEX LabelSure to evaluators, emphasize these 5 key differentiators:

1. **Deterministic Rule Engine (No Hallucinations)**: Unlike generic LLMs that hallucinate compliance advice, our legal metrology engine is 100% deterministic, version-aware (LMPC 2011, 2017 amendments, 2026 rules), and backed by exact statutory references.
2. **RuleLens Visual Explainability**: Every compliance finding links directly to the physical packaging image with normalized bounding boxes, verbatim OCR text, expected conditions, and statutory clause citations.
3. **Dual AI / Human Adjudication Ledger**: When an inspector overrides an AI finding, the system **never overwrites** the original AI decision. Both `ai_status` and `inspector_status` are preserved forever with officer timestamps and justifications.
4. **Field Offline Resilience**: Inspecting warehouses or rural mandis with zero internet connectivity? The mobile client queues inspections locally in SQLite with UUID v4 idempotency keys, automatically synchronizing and deduplicating when connectivity is restored.
5. **Truth-in-Reporting Guarantee**: If image quality is degraded (blur, flash glare, low resolution), the system refuses to guess. It flags `UNCERTAIN` and enforces `REQUIRES_REVIEW` on the legal certificate.

---

## 3. Step-by-Step Demonstration Script (6 Canonical Scenarios)

### Scenario 1: The Happy Path — Compliant FMCG Package
**Objective**: Show real-time multi-panel ingestion, OCR extraction of all 14 statutory fields, and instant certification.

1. Open [http://localhost:5173](http://localhost:5173) and log in with `inspector1` / `Inspector@123`.
2. Click **New Inspection** in the top navigation.
3. Fill in product details:
   - Commodity Name: `Deluxe Whole Wheat Flour 5kg`
   - Brand Name: `Apex Harvest`
   - Commodity Category: `FOOD`
   - Declared Net Quantity: `5` | Unit: `kg`
   - Rule Version: `LMPC-2026-RULES`
4. Click **Create Inspection**.
5. Upload a front panel image (e.g. from sample assets or captured label).
6. Click **Run Analysis**:
   - Watch the pipeline execute in ~2.5 seconds (Preprocessing $\rightarrow$ RapidOCR $\rightarrow$ Extraction $\rightarrow$ Rule Engine).
7. View the **Compliance Status: COMPLIANT** badge.
8. Click **RuleLens** tab to visually verify green bounding boxes enclosing MRP, Net Qty, and Mfg Date.
9. Click **Generate PDF Report** to view and download the official signed certificate with SHA-256 hash.

---

### Scenario 2: Detecting Missing Mandatory Declarations (Enforcement Flow)
**Objective**: Demonstrate automated violation detection with exact legal citations under the Legal Metrology Act.

1. Create a new inspection: `Sunflower Cooking Oil 1L`.
2. Upload a label image lacking MRP and Date of Packaging declarations.
3. Run **Full Pipeline Analysis**.
4. System immediately displays:
   - **Compliance Status: NON_COMPLIANT** (Red banner).
   - Violation 1: **Missing Retail Sale Price (MRP)** — Cites *Rule 6(1)(e)*.
   - Violation 2: **Missing Month and Year of Manufacture/Packaging** — Cites *Rule 6(1)(d)*.
5. Highlight the **Severity: CRITICAL** and penal notices ready for seizure memo generation.

---

### Scenario 3: Guarding Against False Compliance (Substandard Image Quality)
**Objective**: Demonstrate that degraded packaging images do not result in false compliance passes.

1. Create an inspection: `Generic Household Detergent 1kg`.
2. Upload a blurry or poorly illuminated image.
3. Observe the **Image Quality Assessment Panel**:
   - `Blur Variance: < 50` (Flagged: `IMAGE_TOO_BLURRY`).
   - `Quality Score: < 0.60`.
4. Run Analysis:
   - The system returns **Compliance Status: REQUIRES_REVIEW** with status `UNCERTAIN`.
   - The Explanation explicitly states: *"Insufficient visual evidence to reliably determine declaration presence. Physical re-inspection required."*
5. Demonstrate that the PDF Report warns: *"Provisional Audit: Inconclusive Evidence."*

---

### Scenario 4: Imported Commodities — Dual Origin & Importer Validation
**Objective**: Demonstrate compliance checking for imported packaged goods under Rule 6(1)(a) & (10).

1. Create an inspection with `is_imported: true` and Origin Country `Italy`.
2. Commodity Name: `Tuscan Extra Virgin Olive Oil 500ml`.
3. Upload label declaring foreign manufacturer in Milan and Indian importer in New Delhi.
4. Run Analysis:
   - Rule `LMPC_2026_R06_1_A_IMP` evaluates both conditions simultaneously.
   - Verified: Country of Origin ("Italy") $\rightarrow$ **PASS**.
   - Verified: Name & Address of Indian Importer $\rightarrow$ **PASS**.

---

### Scenario 5: Human Inspector Review & Audit Trail Ledger
**Objective**: Show human-in-the-loop adjudication and immutable audit logging.

1. Navigate to an inspection with a flagged finding (e.g. from Scenario 2 or 3).
2. Click **Inspector Review** tab.
3. Click on the finding:
   - Review the AI observation vs expected condition.
   - Select **Inspector Verdict: PASS (Override)**.
   - Add comment: *"Verified declaration physically stamped on carton neck during warehouse visit."*
   - Click **Save Finding Adjudication**.
4. Observe the **Dual Status Ledger**:
   - `AI Status: FAIL` (Preserved!).
   - `Inspector Status: PASS` (Overridden by `inspector1`).
5. Navigate to **Audit Logs** (`/audit`) as `admin` to show the tamper-evident log capturing the exact before/after JSON diff and officer ID.

---

### Scenario 6: Field Offline Synchronization
**Objective**: Demonstrate offline field inspection capability with deduplication.

1. Open Swagger UI at [http://localhost:8000/docs#/Sync/sync_inspections_api_sync_inspections_post](http://localhost:8000/docs#/Sync/sync_inspections_api_sync_inspections_post).
2. Submit a batch inspection payload with a custom `idempotency_key` (e.g. `FIELD-OFFLINE-UUID-999`).
3. Verify that the inspection is ingested with status `SYNCED`.
4. Resubmit the exact same payload again to simulate network timeout retransmission.
5. Verify response: `status: "EXISTING_RECORD_RETURNED"` — Zero duplicate records created!

---

## 4. Admin Dashboard Tour

Walk evaluators through the 11 integrated dashboard views:

1. **Executive Dashboard (`/`)**: High-level KPIs (Total Audits, Non-Compliance Rate, Active Officers, Weekly Trends).
2. **Inspection Registry (`/inspections`)**: Filter by Status, Commodity Category, Rule Version, or Search by Inspection Number.
3. **Inspection Details (`/inspections/:id`)**: Comprehensive product context, multi-panel thumbnails, and statutory metadata.
4. **Evidence Viewer (`/inspections/:id/evidence`)**: High-resolution image canvas with pan/zoom and image quality score breakdowns.
5. **RuleLens (`/inspections/:id/rulelens`)**: Interactive SVG bounding box overlays mapping OCR text to specific legal clauses.
6. **Regulatory Rule Explorer (`/rules`)**: Search and explore official Legal Metrology rules across 2011, 2017, and 2026 versions.
7. **Official Reports (`/reports`)**: Repository of generated PDF compliance certificates with SHA-256 verification hashes.
8. **Analytics & Heatmaps (`/analytics`)**: Geographical violation distribution and common non-compliance categories.
9. **User Management (`/users`)**: Role-based access control management for field officers and supervisors.
10. **Audit Logs (`/audit`)**: Cryptographic chronological ledger of every inspection creation, edit, override, and finalization.

---

## 5. Technical Q&A Cheat Sheet for Evaluators

**Q: How do you handle regional language declarations (Hindi, Tamil, etc.)?**  
*A: RapidOCR supports multi-lingual ONNX models including Devanagari and regional scripts. Under Rule 9, English or Hindi (Devanagari) is mandatory for consumer products; the system checks for English or Hindi text presence.*

**Q: What happens if an e-commerce platform lists products with digital labels?**  
*A: The platform supports `is_ecommerce: true` context, which activates Rule 6(10) / 2017 amendments requiring Country of Origin and digital declarations before consumer checkout.*

**Q: Can a corrupt officer edit a PDF report after finalization?**  
*A: No. Every PDF report generated by ReportLab embeds a 64-character SHA-256 cryptographic hash calculated over the exact document bytes and recorded in the immutable database audit ledger.*
