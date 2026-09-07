import uuid
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    global_exception_handler,
    create_error_response
)
from backend.app.api import (
    health, auth, inspections, images, analysis, declarations, findings, rules, reports, dashboard, audit, sync, area_inspections, international
)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-powered Legal Metrology packaged-commodity compliance inspection platform for the Department of Consumer Affairs, Government of India.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.core.logger import logger

# Request ID & Timing Middleware with Structured Logging
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    logger.info(f"Incoming request: {request.method} {request.url.path} (request_id={request_id})")
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    
    logger.info(
        f"Completed request: {request.method} {request.url.path} - status={response.status_code} "
        f"latency={process_time:.4f}s (request_id={request_id})"
    )
    return response

# Static Storage Mount (Serves uploaded images and generated PDF reports)
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

# Standardized Error Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request parameters or body failed schema validation.",
        status_code=422,
        details={"errors": exc.errors()},
        request_id=req_id
    )

app.add_exception_handler(Exception, global_exception_handler)

# Register All API Routers under /api
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(inspections.router, prefix=settings.API_PREFIX)
app.include_router(images.router, prefix=settings.API_PREFIX)
app.include_router(analysis.router, prefix=settings.API_PREFIX)
app.include_router(declarations.router, prefix=settings.API_PREFIX)
app.include_router(findings.router, prefix=settings.API_PREFIX)
app.include_router(rules.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(sync.router, prefix=settings.API_PREFIX)
app.include_router(area_inspections.router, prefix=settings.API_PREFIX)
app.include_router(international.router, prefix=settings.API_PREFIX)
