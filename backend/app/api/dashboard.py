from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models import Inspection, Finding, Rule, AuditLog
from backend.app.schemas import DashboardSummaryResponse, InspectionSummary, AuditLogResponse
from backend.app.api.deps import get_current_user
from typing import List

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total = db.query(Inspection).count()
    compliant = db.query(Inspection).filter(Inspection.compliance_status == "COMPLIANT").count()
    non_compliant = db.query(Inspection).filter(Inspection.compliance_status == "NON_COMPLIANT").count()
    requires_review = db.query(Inspection).filter(Inspection.compliance_status == "REQUIRES_REVIEW").count()
    uncertain = db.query(Finding).filter(Finding.final_status == "UNCERTAIN").count()
    active_rules = db.query(Rule).filter(Rule.is_active == True).count()
    
    # Recent inspections
    recents = db.query(Inspection).order_by(Inspection.created_at.desc()).limit(10).all()
    recent_summaries = []
    for insp in recents:
        summary_counts = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
        for f in insp.findings:
            st = f.final_status.lower()
            if st in summary_counts:
                summary_counts[st] += 1
                
        recent_summaries.append(InspectionSummary(
            id=insp.id,
            inspection_number=insp.inspection_number,
            inspector_id=insp.inspector_id,
            inspector_name=insp.inspector.full_name if insp.inspector else "Unknown",
            status=insp.status,
            compliance_status=insp.compliance_status,
            commodity_name=insp.commodity_name,
            brand_name=insp.brand_name,
            rule_version=insp.rule_version,
            total_images=len(insp.images),
            findings_summary=summary_counts,
            created_at=insp.created_at,
            updated_at=insp.updated_at,
            finalized_at=insp.finalized_at
        ))
        
    # Top violation categories
    violations = db.query(Finding.requirement_title, func.count(Finding.id))\
        .filter(Finding.final_status == "FAIL")\
        .group_by(Finding.requirement_title)\
        .order_by(func.count(Finding.id).desc())\
        .limit(6).all()
    violation_dict = {row[0]: row[1] for row in violations}
    if not violation_dict:
        violation_dict = {"MRP Declaration": 0, "Net Quantity": 0, "Country of Origin": 0, "Consumer Care": 0}
        
    # Rule version distribution
    version_counts = db.query(Inspection.rule_version, func.count(Inspection.id))\
        .group_by(Inspection.rule_version).all()
    version_dict = {row[0]: row[1] for row in version_counts}
    if not version_dict:
        version_dict = {"LMPC-2026-RULES": total}
        
    return DashboardSummaryResponse(
        total_inspections=total,
        compliant=compliant,
        non_compliant=non_compliant,
        requires_review=requires_review,
        uncertain=uncertain,
        active_rules_count=active_rules,
        recent_inspections=recent_summaries,
        violation_categories=violation_dict,
        rule_version_distribution=version_dict
    )

@router.get("/analytics")
def get_analytics_data(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total = db.query(Inspection).count()
    compliant = db.query(Inspection).filter(Inspection.compliance_status == "COMPLIANT").count()
    non_compliant = db.query(Inspection).filter(Inspection.compliance_status == "NON_COMPLIANT").count()
    requires_review = db.query(Inspection).filter(Inspection.compliance_status == "REQUIRES_REVIEW").count()
    uncertain_findings = db.query(Finding).filter(Finding.final_status == "UNCERTAIN").count()
    passed_findings = db.query(Finding).filter(Finding.final_status == "PASS").count()
    failed_findings = db.query(Finding).filter(Finding.final_status == "FAIL").count()
    overridden_findings = db.query(Finding).filter(Finding.inspector_status != None).count()
    
    # Violation breakdown by clause & requirement
    violations = db.query(Finding.clause_reference, Finding.requirement_title, func.count(Finding.id))\
        .filter(Finding.final_status == "FAIL")\
        .group_by(Finding.clause_reference, Finding.requirement_title)\
        .order_by(func.count(Finding.id).desc())\
        .limit(10).all()
    violation_list = [
        {"clause": row[0], "title": row[1], "count": row[2]}
        for row in violations
    ]
    if not violation_list:
        violation_list = [
            {"clause": "Rule 6(1)(e)", "title": "MRP Prominent Display", "count": 0},
            {"clause": "Rule 6(1)(b)", "title": "Net Quantity Standard Units", "count": 0},
            {"clause": "Rule 6(1)(a)", "title": "Manufacturer & Packer Identity", "count": 0},
            {"clause": "Rule 6(1)(d)", "title": "Month & Year of Manufacture", "count": 0}
        ]

    # Breakdown by commodity category
    commodity_stats = db.query(Inspection.commodity_name, func.count(Inspection.id))\
        .group_by(Inspection.commodity_name)\
        .order_by(func.count(Inspection.id).desc())\
        .limit(8).all()
    commodity_list = [{"name": row[0], "count": row[1]} for row in commodity_stats]
    
    # Compliance rate
    compliance_rate = round((compliant / total * 100), 1) if total > 0 else 0.0

    return {
        "total_inspections": total,
        "compliant_count": compliant,
        "non_compliant_count": non_compliant,
        "requires_review_count": requires_review,
        "compliance_rate": compliance_rate,
        "total_rules_evaluated": passed_findings + failed_findings + uncertain_findings,
        "passed_findings": passed_findings,
        "failed_findings": failed_findings,
        "uncertain_findings": uncertain_findings,
        "overridden_findings": overridden_findings,
        "top_violations": violation_list,
        "commodity_distribution": commodity_list
    }

