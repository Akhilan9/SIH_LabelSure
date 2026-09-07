from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.models import UserRole

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    full_name: str
    role: str
    badge_number: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str
    role: str
    badge_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = UserRole.INSPECTOR.value
    badge_number: Optional[str] = None

# --- Product Context Schemas ---
class ProductContextBase(BaseModel):
    commodity_category: str = "GENERAL_COMMODITY"
    product_type: str = "Pre-Packaged Good"
    is_food: bool = False
    is_imported: bool = False
    origin_country: Optional[str] = None
    package_type: str = "SINGLE_PRE_PACKAGED"
    declared_net_quantity: Optional[float] = None
    declared_unit: Optional[str] = None
    is_ecommerce: bool = False
    platform_name: Optional[str] = None
    inspection_date: Optional[str] = None
    target_rule_version: str = "LMPC-2026-RULES"
    notes: Optional[str] = None

class ProductContextCreate(ProductContextBase):
    pass

class ProductContextUpdate(BaseModel):
    commodity_category: Optional[str] = None
    product_type: Optional[str] = None
    is_food: Optional[bool] = None
    is_imported: Optional[bool] = None
    origin_country: Optional[str] = None
    package_type: Optional[str] = None
    declared_net_quantity: Optional[float] = None
    declared_unit: Optional[str] = None
    is_ecommerce: Optional[bool] = None
    platform_name: Optional[str] = None
    inspection_date: Optional[str] = None
    target_rule_version: Optional[str] = None
    notes: Optional[str] = None

class ProductContextResponse(ProductContextBase):
    id: str
    inspection_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Inspection Schemas ---
class InspectionCreate(BaseModel):
    commodity_name: str = "Packaged Commodity"
    brand_name: Optional[str] = None
    rule_version: str = "LMPC-2026-RULES"
    notes: Optional[str] = None
    context: Optional[ProductContextCreate] = None

class InspectionUpdate(BaseModel):
    commodity_name: Optional[str] = None
    brand_name: Optional[str] = None
    rule_version: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class InspectionSummary(BaseModel):
    id: str
    inspection_number: str
    inspector_id: str
    inspector_name: Optional[str] = None
    status: str
    compliance_status: str
    commodity_name: str
    brand_name: Optional[str] = None
    rule_version: str
    total_images: int = 0
    findings_summary: Dict[str, int] = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Image Schemas ---
class QualityAssessmentResponse(BaseModel):
    quality_score: float
    blur_score: float
    brightness_score: float
    contrast_score: float
    resolution_score: float
    orientation: Optional[Dict[str, Any]] = None
    is_acceptable: bool
    warnings: List[str]

class ImageResponse(BaseModel):
    id: str
    inspection_id: str
    view_type: str
    original_filename: str
    storage_path: str
    processed_path: Optional[str] = None
    sha256_hash: str
    width: int
    height: int
    file_size_bytes: int
    mime_type: str
    quality_assessment: Optional[Dict[str, Any]] = None
    is_acceptable: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- OCR Schemas ---
class OcrLine(BaseModel):
    line_index: int
    text: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    polygon: Optional[List[List[float]]] = None

class OcrResponse(BaseModel):
    id: str
    image_id: str
    inspection_id: str
    engine_name: str
    engine_version: str
    processing_time_ms: float
    lines: List[OcrLine]
    full_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Declaration Schemas ---
class DeclarationCreate(BaseModel):
    source_image_id: Optional[str] = None
    category: str
    raw_text: str
    normalized_value: Optional[Any] = None
    unit: Optional[str] = None
    confidence: float = 1.0
    bbox: List[float] = [0, 0, 0, 0]
    extraction_method: str = "MANUAL_ENTRY"

class DeclarationUpdate(BaseModel):
    category: Optional[str] = None
    raw_text: Optional[str] = None
    normalized_value: Optional[Any] = None
    unit: Optional[str] = None
    bbox: Optional[List[float]] = None

class DeclarationResponse(BaseModel):
    id: str
    inspection_id: str
    source_image_id: Optional[str] = None
    category: str
    type: Optional[str] = None
    raw_text: str
    normalized_value: Optional[Any] = None
    unit: Optional[str] = None
    confidence: float
    bbox: List[float]
    extraction_method: str
    is_inspector_edited: bool
    original_ai_value: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Rule Schemas ---
class RuleResponse(BaseModel):
    rule_id: str
    rule_version: str
    clause_reference: str
    requirement: str
    applicability: Dict[str, Any]
    validation_logic: Dict[str, Any]
    severity: str
    effective_from: str
    effective_to: Optional[str] = None
    source_document: str
    source_url: str
    notes: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class RuleCreate(BaseModel):
    rule_id: str
    rule_version: str
    clause_reference: str
    requirement: str
    applicability: Dict[str, Any]
    validation_logic: Dict[str, Any]
    severity: str = "HIGH"
    effective_from: str
    effective_to: Optional[str] = None
    source_document: str
    source_url: str
    notes: Optional[str] = None

# --- Finding & Review Schemas ---
class FindingReviewUpdate(BaseModel):
    inspector_status: str  # PASS, FAIL, UNCERTAIN, NOT_APPLICABLE
    inspector_comment: Optional[str] = None

class FindingResponse(BaseModel):
    id: str
    inspection_id: str
    rule_id: str
    rule_version: str
    clause_reference: str
    requirement_title: str
    ai_status: str
    inspector_status: Optional[str] = None
    final_status: str
    severity: str
    confidence: float
    explanation: str
    uncertainty_reason: Optional[str] = None
    observed_value: Optional[str] = None
    expected_condition: str
    evidence_references: List[Dict[str, Any]] = []
    inspector_comment: Optional[str] = None
    inspector_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EvidenceItem(BaseModel):
    image_id: Optional[str] = None
    view_type: Optional[str] = None
    image_url: Optional[str] = None
    processed_image_url: Optional[str] = None
    bbox: List[float] = [0.0, 0.0, 0.0, 0.0]
    ocr_text: Optional[str] = None

class RuleLensFindingResponse(BaseModel):
    id: str
    inspection_id: str
    requirement: str
    rule_id: str
    rule_version: str
    clause_reference: str
    observed_value: Optional[str] = None
    expected_condition: str
    evidence_image: Optional[str] = None
    bounding_box: List[float] = [0.0, 0.0, 0.0, 0.0]
    ocr_text: Optional[str] = None
    ai_confidence: float
    decision: str
    ai_status: str
    final_status: str
    explanation: str
    uncertainty_reason: Optional[str] = None
    severity: str
    inspector_status: Optional[str] = None
    inspector_comment: Optional[str] = None
    inspector_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    evidence_references: List[EvidenceItem] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RuleLensInspectionResponse(BaseModel):
    inspection_id: str
    inspection_number: str
    commodity_name: str
    rule_version: str
    overall_status: str
    compliance_status: str
    total_findings: int
    summary: Dict[str, int]
    findings: List[RuleLensFindingResponse]

# --- Inspection Detail Schema ---
class InspectionDetailResponse(InspectionSummary):
    context: Optional[ProductContextResponse] = None
    images: List[ImageResponse] = []
    declarations: List[DeclarationResponse] = []
    findings: List[FindingResponse] = []

# --- Report Schema ---
class ReportResponse(BaseModel):
    id: str
    inspection_id: str
    certificate_number: str
    generated_at: datetime
    generated_by: str
    compliance_verdict: str
    pdf_url: str
    pdf_sha256: str
    summary: Dict[str, Any]
    model_versions: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

# --- Audit & Dashboard Schemas ---
class AuditLogResponse(BaseModel):
    id: str
    inspection_id: Optional[str] = None
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardSummaryResponse(BaseModel):
    total_inspections: int
    compliant: int
    non_compliant: int
    requires_review: int
    uncertain: int
    active_rules_count: int
    recent_inspections: List[InspectionSummary]
    violation_categories: Dict[str, int]
    rule_version_distribution: Dict[str, int]
