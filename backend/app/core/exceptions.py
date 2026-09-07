from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import uuid
import datetime

class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    req_id = request_id or str(uuid.uuid4())
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": req_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        }
    )

async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=req_id
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR"
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return create_error_response(
        code=code,
        message=msg,
        status_code=exc.status_code,
        details={},
        request_id=req_id
    )

async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    import traceback
    # Server-side logging only - never leak stack trace to caller
    print(f"Unhandled Exception [req_id={req_id}]: {exc}\n{traceback.format_exc()}")
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please contact the administrator.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={},
        request_id=req_id
    )
