from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppException
from backend.app.models import Inspection, User, Finding, Declaration
from backend.app.services.inspection_service import run_full_inspection_analysis
from backend.app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/inspections", tags=["Analysis"])

@router.post("/{id}/analyze")
def trigger_inspection_analysis(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "INSPECTOR", "SUPERVISOR"]))
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    try:
        result = run_full_inspection_analysis(inspection_id=id, db=db, user_id=current_user.id)
        return {
            "success": True,
            "data": result
        }
    except ValueError as ve:
        raise AppException(code="ANALYSIS_PRECONDITION_FAILED", message=str(ve), status_code=400)
    except Exception as e:
        import traceback
        print(f"Analysis error: {e}\n{traceback.format_exc()}")
        raise AppException(code="ANALYSIS_EXECUTION_FAILED", message=f"Analysis pipeline error: {str(e)}", status_code=500)

@router.get("/{id}/analysis")
def get_inspection_analysis(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    insp = db.query(Inspection).filter(Inspection.id == id).first()
    if not insp:
        raise AppException(code="INSPECTION_NOT_FOUND", message="Inspection not found.", status_code=404)
        
    findings = db.query(Finding).filter(Finding.inspection_id == id).all()
    declarations = db.query(Declaration).filter(Declaration.inspection_id == id).all()
    
    summary = {"pass": 0, "fail": 0, "uncertain": 0, "not_applicable": 0}
    for f in findings:
        st = f.final_status.lower()
        if st in summary:
            summary[st] += 1
            
    return {
        "inspection_id": id,
        "status": insp.status,
        "compliance_status": insp.compliance_status,
        "summary": summary,
        "declarations_count": len(declarations),
        "findings_count": len(findings)
    }
