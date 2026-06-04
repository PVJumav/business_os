import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
import os

from backend.api.auth import router as auth_router
from backend.api.auth import _decode_token
from backend.api.analytics import router as analytics_router
from backend.api.health import router as health_router
from backend.api.staff import router as staff_router
from backend.api.search import router as search_router
from backend.api.system import router as system_router
from backend.api.finance import router as finance_router
from backend.api.finance_bucs import router as finance_bucs_router
from backend.api.finance_enterprise import router as finance_enterprise_router
from backend.api.reports import router as reports_router
from backend.api.admin_config import router as admin_config_router
from backend.api.ai import router as ai_router
from backend.api.automation import router as automation_enterprise_router
from backend.api.enterprise import router as enterprise_router
from backend.api.phase1_integrations import router as phase1_integrations_router
from backend.api.iam.enterprise import router as iam_enterprise_router
from backend.api.projects.enterprise import router as projects_enterprise_router
from backend.api.crm.activities import router as activities_router
from backend.api.crm.automation import router as automation_router
from backend.api.crm.enterprise import router as crm_enterprise_router
from backend.api.crm.v6_workflows import router as crm_v6_workflows_router
from backend.api.crm.leads import router as leads_router
from backend.api.crm.lpos import router as lpos_router
from backend.api.crm.accounts import router as accounts_router
from backend.api.crm.contacts import router as contacts_router
from backend.api.crm.opportunities import router as opportunities_router
from backend.api.crm.tasks import router as tasks_router
from backend.api.crm.quotations import router as quotations_router
from backend.api.crm.quotes import router as quotes_router
from backend.api.crm.commercial import (
    deals_router,
    engagements_router,
    invoices_router,
    issues_router,
    targets_router,
    workflows_router,
)
from backend.api.crm.operations import (
    customer_tickets_router,
    pmo_projects_router,
    sla_assignments_router,
    technical_services_router,
    tender_documents_router,
    tenders_router,
)
from backend.api.hrm import (
    attendance,
    benefits,
    departments,
    documents,
    employees,
    employee_capabilities,
    employment_info,
    enterprise as hrm_enterprise,
    leave,
    payroll,
    performance,
    probation,
    recruitment,
    overview,
    training,
    extras,
)
from backend.core.database import SessionLocal
from backend.core.create_tables import create_tables
from backend.core.storage import get_upload_root

app = FastAPI(
    title="BusinessOS API",
    description="Backend API for BusinessOS",
    version="1.0.0"
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://business-os-edf.pages.dev",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROTECTED_PREFIXES = (
    "/api/crm",
    "/api/hrm",
    "/api/finance",
    "/api/projects",
    "/api/project-resources",
    "/api/slas",
    "/api/sla-tickets",
    "/api/licenses",
    "/api/invoicing",
    "/api/analytics",
    "/api/reports",
    "/api/approvals",
    "/api/audit",
    "/crm",
    "/hrm",
    "/finance",
    "/projects",
    "/project-resources",
    "/slas",
    "/sla-tickets",
    "/licenses",
    "/invoicing",
)

PUBLIC_PREFIXES = (
    "/api/auth",
    "/auth",
    "/api/health",
    "/health",
    "/uploads",
    "/docs",
    "/openapi.json",
)


@app.middleware("http")
async def require_auth_for_business_modules(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)
    if path.startswith(PROTECTED_PREFIXES):
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return JSONResponse({"detail": "Missing authorization header"}, status_code=401)
        try:
            _decode_token(token)
        except Exception:
            return JSONResponse({"detail": "Invalid authentication token"}, status_code=401)
    return await call_next(request)

upload_root = get_upload_root()
app.mount("/uploads", StaticFiles(directory=str(upload_root)), name="uploads")


frontend_routers = [
    health_router,
    staff_router,
    search_router,
    system_router,
    finance_bucs_router,
    finance_router,
    finance_enterprise_router,
    reports_router,
    admin_config_router,
    ai_router,
    automation_enterprise_router,
    enterprise_router,
    iam_enterprise_router,
    projects_enterprise_router,
    phase1_integrations_router,
    leads_router,
    lpos_router,
    accounts_router,
    contacts_router,
    opportunities_router,
    activities_router,
    tasks_router,
    quotations_router,
    quotes_router,
    deals_router,
    engagements_router,
    issues_router,
    targets_router,
    invoices_router,
    workflows_router,
    tenders_router,
    tender_documents_router,
    pmo_projects_router,
    sla_assignments_router,
    technical_services_router,
    customer_tickets_router,
    automation_router,
    crm_enterprise_router,
    crm_v6_workflows_router,
    attendance.router,
    employees.router,
    employee_capabilities.router,
    employment_info.router,
    departments.router,
    leave.router,
    payroll.router,
    overview.router,
    recruitment.router,
    performance.router,
    probation.router,
    training.router,
    benefits.router,
    documents.router,
    extras.router,
    hrm_enterprise.router,
]

app.include_router(auth_router, prefix="/api")
app.include_router(analytics_router)
app.include_router(analytics_router, prefix="/api")

for router in frontend_routers:
    app.include_router(router)
    app.include_router(router, prefix="/api")


async def employment_expiry_monitor():
    while True:
        await asyncio.sleep(24 * 60 * 60)
        db = SessionLocal()
        try:
            employees.process_expired_employment_engagements(db)
            employees.process_probation_reviews(db)
        finally:
            db.close()


@app.on_event("startup")
async def start_employment_expiry_monitor():
    create_tables()
    asyncio.create_task(employment_expiry_monitor())

@app.get("/")
def root():
    return {
        "message": "BusinessOS API is running"
    }
