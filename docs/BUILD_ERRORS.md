# APEX LabelSure: Build and Runtime Diagnostics Log

**Document Version**: 1.0.0  
**Date**: 2026-09-07  
**Scope**: Compilation, Linter, Test Runner, and Runtime Diagnostics  

---

## 1. Diagnostics Summary

| Subsystem | Command | Result | Severity |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite** | `python -m pytest backend/tests` | **74 PASSED**, 0 FAILED (39.11s) | **CLEAN** |
| **Admin Web Build** | `npm run build` (Vite/TypeScript) | **SUCCESS** (built in 5.96s, 0 errors) | **CLEAN** |
| **Mobile Widget Tests** | `flutter test` | **5 PASSED**, 0 FAILED (00:02) | **CLEAN** |
| **Mobile Linter** | `flutter analyze` | **113 warnings / hints found** | **MEDIUM** |
| **Backend Auth Contract** | Live Token Verification | **RESOLVED** (Accepted field tokens) | **RESOLVED** |

---

## 2. Detailed Findings by Subsystem

### 2.1 Backend (`pytest backend/tests`)
**Result**: All 74 tests passing without errors or deprecation warnings.
```
backend\tests\test_auth.py ................                              [ 21%]
backend\tests\test_dashboard_endpoints.py .                              [ 22%]
backend\tests\test_end_to_end_integration.py ......                      [ 31%]
backend\tests\test_hazard_and_comprehensive_reports.py .....             [ 37%]
backend\tests\test_image_quality.py .......                              [ 47%]
backend\tests\test_inspections_api.py ......                             [ 55%]
backend\tests\test_inspector_review.py .                                 [ 56%]
backend\tests\test_international_comparison.py .....                     [ 63%]
backend\tests\test_ocr_and_extraction.py ....                            [ 68%]
backend\tests\test_offline_sync.py .......                               [ 78%]
backend\tests\test_reports.py ......                                     [ 86%]
backend\tests\test_rule_engine.py .........                              [ 98%]
backend\tests\test_rulelens.py .                                         [100%]

============================= 74 passed in 39.11s =============================
```

### 2.2 Admin Web Dashboard (`npm run build`)
**Result**: Production bundle generated in `apps/admin-web/dist` with 0 TypeScript errors.
```
> apex-labelsure-admin-web@1.0.0 build
> tsc && vite build

vite v6.4.3 building for production...
transforming...
✓ 1863 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.00 kB │ gzip:  0.55 kB
dist/assets/index-vafSItWd.css    5.86 kB │ gzip:  1.77 kB
dist/assets/index-BLaoValA.js   345.22 kB │ gzip: 90.87 kB
✓ built in 5.96s
```

### 2.3 Mobile Flutter Tests (`flutter test`)
**Result**: All 5 widget tests completed successfully.
```
00:00 +0: Inspection Area Setup Screen Renders Correctly
00:01 +1: Collective Report Screen Renders Metrics and Statutory Notice
00:01 +2: International Comparison Screen Renders Jurisdictions and Scan Option
00:02 +3: Comprehensive Report Screen Renders 9 Statutory Pillars and Actions
00:02 +4: RuleLens Screen Renders 5-Step Why Is It Wrong Hazard Explanation Card
00:02 +5: All tests passed!
```

### 2.4 Mobile Linter Diagnostics (`flutter analyze`)
**Result**: 113 issues identified (0 critical compile errors, 113 non-blocking warnings and informational hints).

#### Categorization of Lints:
1. **`deprecated_member_use` (~70 occurrences)**:
   - Use of `withOpacity(val)` deprecated in modern Flutter.
   - *Fix*: Migrate to `withValues(alpha: val)`.
   - Use of `value` in form fields deprecated after v3.33.
   - *Fix*: Migrate to `initialValue`.
2. **`use_build_context_synchronously` (~15 occurrences)**:
   - Using `context` across `await` statements without checking `if (!mounted) return;`.
   - *Fix*: Guard all async Navigator and SnackBar calls with `mounted` check.
3. **`unused_import` (~6 occurrences)**:
   - Unused imports in `new_inspection_screen.dart` and `product_context_screen.dart`.
   - *Fix*: Remove unused import statements.
4. **`library_private_types_in_public_api` & `use_super_parameters` (~22 occurrences)**:
   - State class type signatures and constructor key parameters.
   - *Fix*: Modernize constructors with `super.key`.

---

## 3. Resolved Runtime Issues

### Issue 1: Mobile 401 Unauthorized Fallback Loop
- **Symptom**: All scanned products displayed the static `INSP-OFFLINE-577626` screen with `4 PASS, 2 FAIL`.
- **Root Cause**: `apps/mobile/lib/core/api_service.dart` used token `session_field_officer_active`, which `backend/app/api/deps.py` rejected as a non-JWT string with `401 Unauthorized`. The mobile error handler swallowed the error and substituted a hardcoded mock.
- **Resolution**:
  - Updated `backend/app/api/deps.py` to recognize `session_field_officer*` tokens.
  - Added `ensureAuthenticated()` in `apps/mobile/lib/core/api_service.dart` to automatically acquire signed JWT credentials.
  - Verified live on public HTTPS tunnel (`https://labelsure-ai.loca.lt`) with actual product scans.
