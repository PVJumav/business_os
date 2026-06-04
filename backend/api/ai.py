from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models.crm import (
    CRMAccount,
    CRMDeal,
    CRMInvoice,
    CRMLead,
    CRMOpportunity,
    CRMPMOProject,
    CRMSLAAssignment,
    CRMSalesTarget,
    CRMTender,
    CRMTicket,
)
from backend.models.finance import (
    FinanceApproval,
    FinanceBill,
    FinanceBudget,
    FinanceExpenseClaim,
    FinanceInvoice,
    FinancePayment,
    FinanceRevenueRecord,
)
from backend.models.hrm import (
    HRMActivity,
    HRMEmployee,
    HRMLeave,
    HRMPayroll,
    HRMRecruitment,
    HRMTraining,
)
from backend.schemas.auth import UserResponse


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    evidence: list[dict[str, Any]]
    actions: list[dict[str, str]]
    records: list[dict[str, str]]


def _money(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _count(db: Session, model: Any, *filters: Any) -> int:
    stmt = select(func.count()).select_from(model)
    if filters:
        stmt = stmt.where(*filters)
    return int(db.execute(stmt).scalar() or 0)


def _sum(db: Session, column: Any, *filters: Any) -> float:
    stmt = select(func.coalesce(func.sum(column), 0))
    if filters:
        stmt = stmt.where(*filters)
    return _money(db.execute(stmt).scalar())


def _metric(label: str, value: Any, detail: str = "") -> dict[str, Any]:
    return {"label": label, "value": value, "detail": detail}


def _record(entity: str, title: str, subtitle: str, href: str) -> dict[str, str]:
    return {"entity": entity, "title": title, "subtitle": subtitle, "href": href}


def _action(label: str, href: str, description: str) -> dict[str, str]:
    return {"label": label, "href": href, "description": description}


def _scope_filter(user: UserResponse, owner_columns: list[Any]) -> list[Any]:
    if user.role in {"admin", "manager"}:
        return []
    name = user.full_name or user.email
    return [or_(*[column.ilike(f"%{name}%") for column in owner_columns])]


def _finance_answer(db: Session, message: str) -> AIChatResponse:
    today = date.today()
    overdue_filter = FinanceInvoice.due_date.isnot(None), FinanceInvoice.due_date < today
    outstanding = _sum(db, FinanceInvoice.total_amount - FinanceInvoice.paid_amount, FinanceInvoice.status != "paid")
    overdue = _sum(db, FinanceInvoice.total_amount - FinanceInvoice.paid_amount, *overdue_filter, FinanceInvoice.status != "paid")
    pending_bills = _sum(db, FinanceBill.amount - FinanceBill.paid_amount, FinanceBill.status != "paid")
    paid_revenue = _sum(db, FinanceInvoice.paid_amount)
    recognized_revenue = _sum(db, FinanceRevenueRecord.amount)
    expenses = _sum(db, FinanceExpenseClaim.amount) + _sum(db, FinanceBill.amount)
    approvals = _count(db, FinanceApproval, FinanceApproval.status == "pending")
    budget_overruns = _count(db, FinanceBudget, FinanceBudget.actual_amount > FinanceBudget.approved_amount)

    invoices = (
        db.query(
            FinanceInvoice.invoice_number,
            FinanceInvoice.total_amount,
            FinanceInvoice.paid_amount,
            FinanceInvoice.due_date,
            FinanceInvoice.status,
        )
        .filter(FinanceInvoice.status != "paid")
        .order_by(FinanceInvoice.due_date.asc().nullslast())
        .limit(5)
        .all()
    )

    records = [
        _record(
            "Invoice",
            row.invoice_number,
            f"{row.status or 'open'} | balance {(_money(row.total_amount) - _money(row.paid_amount)):,.0f}",
            "/finance/accounts-receivable",
        )
        for row in invoices
    ]

    answer = (
        f"Finance position: outstanding receivables are {outstanding:,.0f}, overdue receivables are "
        f"{overdue:,.0f}, pending payables are {pending_bills:,.0f}, and paid invoice collections are "
        f"{paid_revenue:,.0f}. Estimated profit from recognized/paid revenue less bills and claims is "
        f"{(paid_revenue + recognized_revenue - expenses):,.0f}."
    )
    if "approval" in message:
        answer += f" There are {approvals} finance approvals waiting for action."
    if "budget" in message:
        answer += f" {budget_overruns} budget lines are currently above approved amount."

    return AIChatResponse(
        answer=answer,
        intent="finance",
        confidence=0.92,
        evidence=[
            _metric("Outstanding receivables", outstanding, "Invoices not fully paid"),
            _metric("Overdue receivables", overdue, "Due date before today"),
            _metric("Pending payables", pending_bills, "Supplier/vendor bills not fully paid"),
            _metric("Pending approvals", approvals, "Finance approval queue"),
            _metric("Budget overruns", budget_overruns, "Actual amount above approved budget"),
        ],
        actions=[
            _action("Open Finance", "/finance", "Review the finance dashboard"),
            _action("Review Approvals", "/finance/approvals", "Approve or reject pending finance items"),
            _action("Download Finance Report", "/reports", "Customize and export a finance report"),
        ],
        records=records,
    )


def _crm_answer(db: Session, message: str, user: UserResponse) -> AIChatResponse:
    deal_scope = _scope_filter(user, [CRMDeal.owner])
    opportunity_scope = _scope_filter(user, [CRMOpportunity.owner])
    lead_scope = _scope_filter(user, [CRMLead.assigned_to])
    open_deals = _count(db, CRMDeal, CRMDeal.deal_status == "open", *deal_scope)
    won_deals = _count(db, CRMDeal, CRMDeal.deal_status.in_(["won", "closed_won", "Closed Won", "closed as won"]))
    open_pipeline = _sum(db, CRMDeal.revenue_amount, CRMDeal.deal_status == "open", *deal_scope)
    weighted_opportunities = _sum(
        db,
        CRMOpportunity.opportunity_value * (CRMOpportunity.probability / 100.0),
        CRMOpportunity.status == "open",
        *opportunity_scope,
    )
    leads = _count(db, CRMLead, CRMLead.converted == False, *lead_scope)  # noqa: E712
    renewals_soon = _count(
        db,
        CRMDeal,
        CRMDeal.renewal_date.isnot(None),
        CRMDeal.renewal_date <= date.today() + timedelta(days=60),
        CRMDeal.deal_status == "open",
        *deal_scope,
    )
    tenders_due = _count(
        db,
        CRMTender,
        CRMTender.close_date.isnot(None),
        CRMTender.close_date <= date.today() + timedelta(days=30),
        CRMTender.outcome == "pending",
    )

    deals = (
        db.query(CRMDeal.deal_name, CRMDeal.owner, CRMDeal.stage, CRMDeal.revenue_amount, CRMDeal.deal_status)
        .filter(CRMDeal.deal_status == "open", *deal_scope)
        .order_by(CRMDeal.revenue_amount.desc().nullslast())
        .limit(5)
        .all()
    )
    records = [
        _record("Deal", row.deal_name, f"{row.owner or 'Unassigned'} | {row.stage or 'No stage'} | {float(row.revenue_amount or 0):,.0f}", "/crm/deals")
        for row in deals
    ]

    answer = (
        f"CRM health: {open_deals} open deals hold {open_pipeline:,.0f} in pipeline value, with "
        f"{weighted_opportunities:,.0f} weighted opportunity value. There are {leads} unconverted leads, "
        f"{renewals_soon} renewals due in the next 60 days, and {tenders_due} tender responses due within 30 days."
    )
    if won_deals:
        answer += f" Closed-won deal count is {won_deals}, which should feed finance revenue recognition."

    return AIChatResponse(
        answer=answer,
        intent="crm",
        confidence=0.91,
        evidence=[
            _metric("Open deals", open_deals, "Active sales pipeline"),
            _metric("Open pipeline value", open_pipeline, "Revenue amount on open deals"),
            _metric("Weighted opportunities", weighted_opportunities, "Opportunity value multiplied by probability"),
            _metric("Unconverted leads", leads, "Leads not yet converted"),
            _metric("Renewals soon", renewals_soon, "Renewal date within 60 days"),
        ],
        actions=[
            _action("Open Deals", "/crm/deals", "Work the current pipeline"),
            _action("Open Leads", "/crm/leads", "Convert qualified leads into accounts and deals"),
            _action("Open Sales Report", "/reports", "Generate a sales report"),
        ],
        records=records,
    )


def _hr_answer(db: Session, message: str) -> AIChatResponse:
    active_staff = _count(db, HRMEmployee, HRMEmployee.employment_status == "active")
    departments = int(db.execute(select(func.count(func.distinct(HRMEmployee.department)))).scalar() or 0)
    pending_leave = _count(db, HRMLeave, HRMLeave.status == "pending")
    recruiting = _count(db, HRMRecruitment, HRMRecruitment.application_status.in_(["pending", "screening", "interview"]))
    training_incomplete = _count(db, HRMTraining, HRMTraining.completion_status != "completed")
    monthly_payroll = _sum(db, HRMPayroll.net_pay, HRMPayroll.payment_status != "cancelled")
    activities = _count(db, HRMActivity, HRMActivity.status.in_(["planned", "active"]))

    staff = (
        db.query(HRMEmployee.first_name, HRMEmployee.last_name, HRMEmployee.department, HRMEmployee.job_title, HRMEmployee.employment_status)
        .filter(HRMEmployee.employment_status == "active")
        .order_by(HRMEmployee.department.asc().nullslast(), HRMEmployee.last_name.asc())
        .limit(5)
        .all()
    )
    records = [
        _record("Staff", f"{row.first_name} {row.last_name}", f"{row.department or 'No department'} | {row.job_title or 'No role'}", "/hrm/staff")
        for row in staff
    ]

    answer = (
        f"HRM snapshot: {active_staff} active employees across {departments} departments. "
        f"There are {pending_leave} leave requests pending, {recruiting} recruitment items in motion, "
        f"{training_incomplete} incomplete training records, and {activities} active HR activities. "
        f"Current payroll records total {monthly_payroll:,.0f} in net pay."
    )

    return AIChatResponse(
        answer=answer,
        intent="hrm",
        confidence=0.9,
        evidence=[
            _metric("Active staff", active_staff, "Employment status is active"),
            _metric("Departments", departments, "Distinct staff departments"),
            _metric("Pending leave", pending_leave, "Leave approvals required"),
            _metric("Recruitment pipeline", recruiting, "Open hiring activity"),
            _metric("Incomplete training", training_incomplete, "Training records not completed"),
        ],
        actions=[
            _action("Open Staff 360", "/hrm/staff", "Search any employee and drill into staff details"),
            _action("Open Recruitment", "/hrm/recruitment", "Review candidates and hiring pipeline"),
            _action("Download HR Report", "/reports", "Customize and export HR reports"),
        ],
        records=records,
    )


def _projects_answer(db: Session) -> AIChatResponse:
    active_projects = _count(db, CRMPMOProject, CRMPMOProject.status == "active")
    planning_projects = _count(db, CRMPMOProject, CRMPMOProject.stage.in_(["planning", "scoping"]))
    active_slas = _count(db, CRMSLAAssignment, CRMSLAAssignment.status == "active")
    open_tickets = _count(db, CRMTicket, CRMTicket.status != "closed")
    high_tickets = _count(db, CRMTicket, CRMTicket.status != "closed", CRMTicket.severity.in_(["high", "critical"]))

    projects = (
        db.query(CRMPMOProject.project_name, CRMPMOProject.project_manager, CRMPMOProject.stage, CRMPMOProject.status)
        .filter(CRMPMOProject.status == "active")
        .limit(5)
        .all()
    )
    records = [
        _record("Project", row.project_name, f"{row.project_manager or 'No PM'} | {row.stage or 'planning'}", "/crm/pmo-projects")
        for row in projects
    ]

    return AIChatResponse(
        answer=(
            f"Delivery view: {active_projects} active projects, {planning_projects} in planning/scoping, "
            f"{active_slas} active SLA assignments, and {open_tickets} open customer tickets. "
            f"{high_tickets} tickets are high or critical severity."
        ),
        intent="projects",
        confidence=0.89,
        evidence=[
            _metric("Active projects", active_projects, "PMO records with active status"),
            _metric("Planning/scoping", planning_projects, "Projects not yet fully in delivery"),
            _metric("Active SLAs", active_slas, "Live SLA assignments"),
            _metric("Open tickets", open_tickets, "Customer tickets not closed"),
            _metric("High severity tickets", high_tickets, "High or critical ticket severity"),
        ],
        actions=[
            _action("Open Projects", "/crm/pmo-projects", "Review implementation delivery"),
            _action("Open SLAs", "/crm/sla-assignments", "Check engineer assignments and support obligations"),
            _action("Download Project Report", "/reports", "Generate a project or SLA report"),
        ],
        records=records,
    )


def _search_answer(db: Session, message: str) -> AIChatResponse:
    term = f"%{message.strip()}%"
    staff = (
        db.query(HRMEmployee.first_name, HRMEmployee.last_name, HRMEmployee.department, HRMEmployee.job_title)
        .filter(or_(HRMEmployee.first_name.ilike(term), HRMEmployee.last_name.ilike(term), HRMEmployee.email.ilike(term)))
        .limit(3)
        .all()
    )
    accounts = (
        db.query(CRMAccount.company_name, CRMAccount.account_manager, CRMAccount.country, CRMAccount.vertical)
        .filter(CRMAccount.company_name.ilike(term))
        .limit(3)
        .all()
    )
    records = [
        _record("Staff", f"{row.first_name} {row.last_name}", f"{row.department or 'No department'} | {row.job_title or 'No role'}", "/hrm/staff")
        for row in staff
    ]
    records += [
        _record("Account", row.company_name, f"{row.account_manager or 'No AM'} | {row.country or 'No country'} | {row.vertical or 'No vertical'}", "/crm/accounts")
        for row in accounts
    ]

    if not records:
        return AIChatResponse(
            answer="I did not find a direct staff or account match. Try asking about finance, CRM pipeline, HR workforce, projects, SLAs, reports, or use a more specific name.",
            intent="search",
            confidence=0.62,
            evidence=[],
            actions=[_action("Open Global Analytics", "/analytics", "Explore company-wide data")],
            records=[],
        )

    return AIChatResponse(
        answer=f"I found {len(records)} likely match{'es' if len(records) != 1 else ''}. Open the linked area to drill down into the full record.",
        intent="search",
        confidence=0.78,
        evidence=[_metric("Matches", len(records), "Staff and account records")],
        actions=[_action("Open Staff 360", "/hrm/staff", "Search deeper by employee name")],
        records=records,
    )


def _restricted_answer(area: str, href: str) -> AIChatResponse:
    return AIChatResponse(
        answer=f"{area} intelligence is restricted by your system role. Ask an admin to update your access rights if this should be available to you.",
        intent="restricted",
        confidence=1.0,
        evidence=[],
        actions=[_action("Open Settings", href, "Admins can review roles, policies, and access rights")],
        records=[],
    )


@router.post("/chat", response_model=AIChatResponse)
def chat_with_assistant(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    user: UserResponse = Depends(get_current_user),
):
    message = payload.message.strip().lower()
    if not message:
        return AIChatResponse(
            answer="Ask me about sales pipeline, HR workforce, finance position, projects, SLAs, reports, approvals, budgets, or any staff/customer record.",
            intent="help",
            confidence=1.0,
            evidence=[],
            actions=[
                _action("Open Dashboard", "/", "Review the company overview"),
                _action("Open Analytics", "/analytics", "Explore live analytics"),
            ],
            records=[],
        )

    if any(word in message for word in ["finance", "invoice", "cash", "budget", "expense", "payment", "payable", "receivable", "tax", "approval"]):
        if user.role != "admin":
            return _restricted_answer("Finance", "/settings/access-rights")
        return _finance_answer(db, message)
    if any(word in message for word in ["crm", "deal", "pipeline", "lead", "opportunity", "sales", "tender", "renewal", "account", "customer"]):
        return _crm_answer(db, message, user)
    if any(word in message for word in ["hr", "hrm", "staff", "employee", "payroll", "leave", "recruit", "training", "benefit", "workforce"]):
        if user.role not in {"admin", "manager"}:
            return _restricted_answer("HRM", "/settings/access-rights")
        return _hr_answer(db, message)
    if any(word in message for word in ["project", "sla", "ticket", "implementation", "delivery", "engineer", "pmo"]):
        return _projects_answer(db)
    if any(word in message for word in ["report", "analytics", "ceo", "summary", "overview"]):
        if user.role not in {"admin", "manager"}:
            return _restricted_answer("Executive analytics", "/settings/access-rights")
        company = _crm_answer(db, message, user)
        finance = _finance_answer(db, message) if user.role == "admin" else None
        hrm = _hr_answer(db, message)
        return AIChatResponse(
            answer=f"CEO summary: {company.answer} {finance.answer if finance else 'Finance details are admin-only.'} {hrm.answer}",
            intent="executive_summary",
            confidence=0.88,
            evidence=company.evidence[:3] + (finance.evidence[:3] if finance else []) + hrm.evidence[:3],
            actions=[
                _action("Open Executive Dashboard", "/", "Review the full company dashboard"),
                _action("Open Analytics", "/analytics", "Filter by company, HR, finance, sales, and projects"),
                _action("Build CEO Report", "/reports", "Preview, customize, and download the CEO report"),
            ],
            records=company.records[:3] + (finance.records[:3] if finance else []) + hrm.records[:3],
        )

    return _search_answer(db, payload.message)
