import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Float, Integer, DateTime, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    INSPECTOR = "INSPECTOR"
    SUPERVISOR = "SUPERVISOR"
    VIEWER = "VIEWER"

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default=UserRole.INSPECTOR.value)  # ADMIN, INSPECTOR, SUPERVISOR, VIEWER
    badge_number = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    inspections = relationship("Inspection", back_populates="inspector")

class Inspection(Base):
    __tablename__ = "inspections"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_number = Column(String(64), unique=True, nullable=False, index=True)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="DRAFT", index=True)
    # DRAFT, CAPTURED, QUEUED, UPLOADING, ANALYZING, REVIEW_REQUIRED, FINALIZED, SYNCED, SYNC_FAILED
    compliance_status = Column(String(32), nullable=False, default="PENDING", index=True)
    # PENDING, COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
    commodity_name = Column(String(256), nullable=False, default="Unspecified Packaged Commodity")
    brand_name = Column(String(128), nullable=True)
    rule_version = Column(String(64), nullable=False, default="LMPC-2026-RULES")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    finalized_at = Column(DateTime, nullable=True)
    
    inspector = relationship("User", back_populates="inspections")
    images = relationship("InspectionImage", back_populates="inspection", cascade="all, delete-orphan")
    context = relationship("ProductContext", back_populates="inspection", uselist=False, cascade="all, delete-orphan")
    declarations = relationship("Declaration", back_populates="inspection", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")
    ocr_results = relationship("OcrResult", back_populates="inspection", cascade="all, delete-orphan")

class ProductContext(Base):
    __tablename__ = "product_context"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), unique=True, nullable=False, index=True)
    commodity_category = Column(String(64), nullable=False, default="GENERAL_COMMODITY")
    # FOOD_BEVERAGE, COSMETICS_PERSONAL_CARE, HOUSEHOLD_CLEANING, ELECTRONICS_APPLIANCES, PHARMACEUTICAL_MEDICAL, APPAREL_TEXTILE, GENERAL_COMMODITY
    product_type = Column(String(128), nullable=False, default="Pre-Packaged Good")
    is_food = Column(Boolean, default=False)
    is_imported = Column(Boolean, default=False)
    origin_country = Column(String(64), nullable=True)
    package_type = Column(String(64), nullable=False, default="SINGLE_PRE_PACKAGED")
    # SINGLE_PRE_PACKAGED, MULTI_PIECE, COMBINATION, WHOLESALE, LOOSE_REPACKAGED
    declared_net_quantity = Column(Float, nullable=True)
    declared_unit = Column(String(16), nullable=True)
    is_ecommerce = Column(Boolean, default=False)
    platform_name = Column(String(64), nullable=True)
    inspection_date = Column(String(16), nullable=False, default=lambda: utc_now().strftime("%Y-%m-%d"))
    target_rule_version = Column(String(64), nullable=False, default="LMPC-2026-RULES")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    
    inspection = relationship("Inspection", back_populates="context")

class InspectionImage(Base):
    __tablename__ = "inspection_images"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    view_type = Column(String(32), nullable=False, default="FRONT")
    # FRONT, BACK, SIDE, TOP, BOTTOM, NUTRITION_PANEL, MRP_PANEL, OTHER
    original_filename = Column(String(256), nullable=False)
    storage_path = Column(String(512), nullable=False)
    processed_path = Column(String(512), nullable=True)
    sha256_hash = Column(String(64), nullable=False, index=True)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(64), default="image/jpeg")
    quality_assessment = Column(JSON, nullable=True)
    is_acceptable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    
    inspection = relationship("Inspection", back_populates="images")
    ocr_result = relationship("OcrResult", back_populates="image", uselist=False, cascade="all, delete-orphan")

class OcrResult(Base):
    __tablename__ = "ocr_results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    image_id = Column(String(36), ForeignKey("inspection_images.id"), nullable=False, index=True)
    engine_name = Column(String(64), default="PaddleOCR/RapidOCR-PP-OCRv4")
    engine_version = Column(String(32), default="v4")
    processing_time_ms = Column(Float, default=0.0)
    full_text = Column(Text, nullable=False)
    lines = Column(JSON, nullable=False)  # List of {text, confidence, bbox: [x1,y1,x2,y2], polygon}
    created_at = Column(DateTime, default=utc_now)
    
    inspection = relationship("Inspection", back_populates="ocr_results")
    image = relationship("InspectionImage", back_populates="ocr_result")

class Declaration(Base):
    __tablename__ = "declarations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    source_image_id = Column(String(36), ForeignKey("inspection_images.id"), nullable=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    # PRODUCT_NAME, COMMON_GENERIC_NAME, MANUFACTURER, PACKER, IMPORTER, COUNTRY_OF_ORIGIN,
    # NET_QUANTITY, MRP, MANUFACTURE_DATE, PACK_DATE, BEST_BEFORE, USE_BY, CONSUMER_CARE,
    # UNIT_SALE_PRICE, DIMENSIONS, OTHER_DECLARATION
    raw_text = Column(Text, nullable=False)
    normalized_value = Column(JSON, nullable=True)
    unit = Column(String(32), nullable=True)
    confidence = Column(Float, default=0.0)
    bbox = Column(JSON, nullable=False)  # [x1, y1, x2, y2]
    extraction_method = Column(String(64), default="HYBRID")
    is_inspector_edited = Column(Boolean, default=False)
    original_ai_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    @property
    def type(self) -> str:
        return self.category
        
    inspection = relationship("Inspection", back_populates="declarations")

class Rule(Base):
    __tablename__ = "rules"
    
    rule_id = Column(String(64), primary_key=True)
    rule_version = Column(String(32), primary_key=True)
    clause_reference = Column(String(64), nullable=False)
    requirement = Column(String(256), nullable=False)
    applicability = Column(JSON, nullable=False)
    validation_logic = Column(JSON, nullable=False)
    severity = Column(String(32), nullable=False, default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL
    effective_from = Column(String(16), nullable=False)
    effective_to = Column(String(16), nullable=True)
    source_document = Column(String(256), nullable=False)
    source_url = Column(String(512), nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False, index=True)
    rule_version = Column(String(32), nullable=False)
    clause_reference = Column(String(64), nullable=False)
    requirement_title = Column(String(256), nullable=False)
    ai_status = Column(String(32), nullable=False)  # PASS, FAIL, UNCERTAIN, NOT_APPLICABLE
    inspector_status = Column(String(32), nullable=True)  # PASS, FAIL, UNCERTAIN, NOT_APPLICABLE, null
    final_status = Column(String(32), nullable=False, index=True)
    severity = Column(String(32), nullable=False, default="HIGH")
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, nullable=False)
    uncertainty_reason = Column(Text, nullable=True)
    observed_value = Column(Text, nullable=True)
    expected_condition = Column(Text, nullable=False)
    evidence_references = Column(JSON, default=list)  # [{image_id, view_type, bbox, ocr_snippet}]
    inspector_comment = Column(Text, nullable=True)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    inspection = relationship("Inspection", back_populates="findings")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), ForeignKey("inspections.id"), nullable=False, index=True)
    certificate_number = Column(String(64), unique=True, nullable=False, index=True)
    generated_at = Column(DateTime, default=utc_now)
    generated_by = Column(String(128), nullable=False)
    compliance_verdict = Column(String(32), nullable=False)  # COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
    pdf_url = Column(String(512), nullable=False)
    pdf_sha256 = Column(String(64), nullable=False)
    summary = Column(JSON, nullable=False)
    model_versions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    
    inspection = relationship("Inspection", back_populates="reports")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    inspection_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(64), nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    inspection_id = Column(String(36), nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), default="PENDING", index=True)  # PENDING, PROCESSED, FAILED
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

Index("idx_findings_inspection_status", Finding.inspection_id, Finding.final_status)
Index("idx_declarations_inspection_cat", Declaration.inspection_id, Declaration.category)
