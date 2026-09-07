from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Rule, User
from backend.app.schemas import RuleResponse, RuleCreate
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/rules", tags=["Regulatory Rules"])

@router.get("", response_model=List[RuleResponse])
def list_rules(
    version: Optional[str] = Query(None, description="Filter by version e.g. LMPC-2026-RULES"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Rule)
    if active_only:
        query = query.filter(Rule.is_active == True)
    if version:
        query = query.filter(Rule.rule_version == version)
    if severity:
        query = query.filter(Rule.severity == severity)
        
    return query.all()

@router.get("/{id}", response_model=RuleResponse)
def get_rule_detail(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = db.query(Rule).filter(Rule.rule_id == id).first()
    if not rule:
        raise AppException(code="RULE_NOT_FOUND", message=f"Rule {id} not found.", status_code=404)
    return rule

@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    rule_in: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN"]))
):
    existing = db.query(Rule).filter(
        Rule.rule_id == rule_in.rule_id,
        Rule.rule_version == rule_in.rule_version
    ).first()
    if existing:
        raise AppException(code="RULE_ALREADY_EXISTS", message="Rule with this ID and version already exists.", status_code=409)
        
    rule = Rule(
        rule_id=rule_in.rule_id,
        rule_version=rule_in.rule_version,
        clause_reference=rule_in.clause_reference,
        requirement=rule_in.requirement,
        applicability=rule_in.applicability,
        validation_logic=rule_in.validation_logic,
        severity=rule_in.severity,
        effective_from=rule_in.effective_from,
        effective_to=rule_in.effective_to,
        source_document=rule_in.source_document,
        source_url=rule_in.source_url,
        notes=rule_in.notes
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
