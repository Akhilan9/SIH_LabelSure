export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'INSPECTOR' | 'SUPERVISOR' | 'VIEWER';
  badge_number?: string;
}

export interface InspectionSummary {
  id: string;
  inspection_number: string;
  inspector_id: string;
  inspector_name?: string;
  status: 'DRAFT' | 'CAPTURED' | 'QUEUED' | 'UPLOADING' | 'ANALYZING' | 'REVIEW_REQUIRED' | 'FINALIZED' | 'SYNCED' | 'SYNC_FAILED';
  compliance_status: 'PENDING' | 'COMPLIANT' | 'NON_COMPLIANT' | 'REQUIRES_REVIEW';
  commodity_name: string;
  brand_name?: string;
  rule_version: string;
  total_images: number;
  findings_summary: {
    pass: number;
    fail: number;
    uncertain: number;
    not_applicable: number;
  };
  created_at: string;
  updated_at: string;
  finalized_at?: string;
}

export interface InspectionImage {
  id: string;
  inspection_id: string;
  view_type: string;
  original_filename: string;
  storage_path: string;
  processed_path?: string;
  sha256_hash: string;
  width: number;
  height: number;
  file_size_bytes: number;
  mime_type: string;
  quality_assessment?: {
    quality_score: number;
    blur_score: number;
    brightness_score: number;
    contrast_score: number;
    resolution_score: number;
    is_acceptable: boolean;
    warnings: string[];
  };
  is_acceptable: boolean;
  created_at: string;
}

export interface Declaration {
  id: string;
  inspection_id: string;
  source_image_id?: string;
  category: string;
  raw_text: string;
  normalized_value?: any;
  unit?: string;
  confidence: number;
  bbox: number[]; // [x1, y1, x2, y2]
  extraction_method: string;
  is_inspector_edited: boolean;
  original_ai_value?: string;
}

export interface Finding {
  id: string;
  inspection_id: string;
  rule_id: string;
  rule_version: string;
  clause_reference: string;
  requirement_title: string;
  ai_status: 'PASS' | 'FAIL' | 'UNCERTAIN' | 'NOT_APPLICABLE';
  inspector_status?: 'PASS' | 'FAIL' | 'UNCERTAIN' | 'NOT_APPLICABLE' | null;
  final_status: 'PASS' | 'FAIL' | 'UNCERTAIN' | 'NOT_APPLICABLE';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFORMATIONAL';
  confidence: number;
  explanation: string;
  uncertainty_reason?: string;
  observed_value?: string;
  expected_condition: string;
  evidence_references: Array<{
    image_id: string;
    view_type?: string;
    bbox: number[];
    ocr_snippet?: string;
  }>;
  inspector_comment?: string;
  inspector_id?: string;
  reviewed_at?: string;
}

export interface Rule {
  rule_id: string;
  rule_version: string;
  clause_reference: string;
  requirement: string;
  applicability: any;
  validation_logic: any;
  severity: string;
  effective_from: string;
  effective_to?: string;
  source_document: string;
  source_url: string;
  notes?: string;
  is_active: boolean;
}

export interface DashboardSummary {
  total_inspections: number;
  compliant: number;
  non_compliant: number;
  requires_review: number;
  uncertain: number;
  active_rules_count: number;
  recent_inspections: InspectionSummary[];
  violation_categories: Record<string, number>;
  rule_version_distribution: Record<string, number>;
}

export interface ReportRecord {
  id: string;
  inspection_id: string;
  certificate_number: string;
  generated_by: string;
  compliance_verdict: string;
  pdf_url: string;
  pdf_sha256: string;
  summary: {
    total_rules_evaluated: number;
    passed: number;
    failed: number;
    uncertain: number;
    not_applicable: number;
    critical_violations: number;
    inspector_overrides: number;
  };
  model_versions: Record<string, string>;
  generated_at: string;
}

export interface AnalyticsData {
  total_inspections: number;
  compliant_count: number;
  non_compliant_count: number;
  requires_review_count: number;
  compliance_rate: number;
  total_rules_evaluated: number;
  passed_findings: number;
  failed_findings: number;
  uncertain_findings: number;
  overridden_findings: number;
  top_violations: Array<{
    clause: string;
    title: string;
    count: number;
  }>;
  commodity_distribution: Array<{
    name: string;
    count: number;
  }>;
}

export interface UserCreatePayload {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: 'ADMIN' | 'INSPECTOR' | 'SUPERVISOR' | 'VIEWER';
  badge_number?: string;
}

