from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models import AuditLog
from backend.app.schemas import AuditLogResponse
from backend.app.api.deps import require_role

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse], dependencies=[Depends(require_role(["ADMIN", "SUPERVISOR", "INSPECTOR"]))])
def list_audit_logs(
    inspection_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if inspection_id:
        query = query.filter(AuditLog.inspection_id == inspection_id)
    if action:
        query = query.filter(AuditLog.action == action)
        
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs
