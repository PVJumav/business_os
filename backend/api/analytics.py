from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.crm import (
    CRMAccount,
    CRMAccountIssue,
    CRMActivity,
    CRMAutomationRule,
    CRMContact,
    CRMCustomerEngagement,
    CRMDeal,
    CRMDepartmentWorkflow,
    CRMInvoice,
    CRMLead,
    CRMOpportunity,
    CRMPMOProject,
    CRMQuotation,
    CRMSLAAssignment,
    CRMSalesTarget,
    CRMTask,
    CRMTechnicalService,
    CRMTender,
    CRMTenderRepositoryDocument,
    CRMTicket,
)
from backend.models.hrm import (
    HRMAttendance,
    HRMBenefit,
    HRMDepartment,
    HRMDocument,
    HRMEmployee,
    HRMLeave,
    HRMPayroll,
    HRMPerformance,
    HRMRecruitment,
    HRMTraining,
    HRMActivity,
    HRMAssetAssignment,
    HRMCompensation,
    HRMGRCRecord,
    HRMEmployeeRelationCase,
    HRMLifecycleEvent,
    HRMLeaveBalance,
    HRMOnboardingTask,
    HRMPolicyAcknowledgement,
    HRMPosition,
    HRMSurvey,
)
from backend.models.finance import (
    FinanceApproval,
    FinanceAuditTrail,
    FinanceBankAccount,
    FinanceBankTransaction,
    FinanceBill,
    FinanceBudget,
    FinanceChartAccount,
    FinanceCostCenter,
    FinanceCreditNote,
    FinanceDocument as FinanceDocumentModel,
    FinanceExpenseClaim,
    FinanceFixedAsset,
    FinanceIntegrationEvent,
    FinanceInvoice as FinanceInvoiceModel,
    FinanceJournalEntry,
    FinanceJournalLine,
    FinancePayment,
    FinanceProjectFinance,
    FinancePurchaseOrder,
    FinancePurchaseRequest,
    FinanceReceipt,
    FinanceRevenueRecord,
    FinanceTaxRecord,
    FinanceVendor,
)
from backend.models.config import AccessRight, OrganizationPolicy
from backend.models.enterprise import (
    CRMLicence,
    DataImportBatch,
    EntitySequence,
    ERPInventoryItem,
    CommunicationLog,
    FeatureCapability,
    IntegrationConnector,
    KnowledgeBaseArticle,
    NotificationEvent,
    OrganizationGoal,
    PortalRequest,
    ProjectMilestone,
    ProjectRisk,
    ProjectTask,
    ResourceAllocation,
    ScheduleEvent,
    StaffRoleAssignment,
    SupportTicket,
    TerritoryRule,
    WorkflowRule,
    WorkflowRunLog,
)
from backend.models.crm import CRMQuotation


router = APIRouter(prefix="/analytics", tags=["Analytics"])

RESOURCE_MAP: dict[str, dict[str, Any]] = {
    "crm.accounts": {"model": CRMAccount, "status": "account_status", "value": None},
    "crm.contacts": {"model": CRMContact, "status": None, "value": None},
    "crm.leads": {"model": CRMLead, "status": "status", "value": "estimated_value"},
    "crm.opportunities": {"model": CRMOpportunity, "status": "stage", "value": "opportunity_value"},
    "crm.deals": {"model": CRMDeal, "status": "deal_status", "value": "gross_profit"},
    "crm.activities": {"model": CRMActivity, "status": "status", "value": None},
    "crm.engagements": {"model": CRMCustomerEngagement, "status": "engagement_type", "value": None},
    "crm.account-issues": {"model": CRMAccountIssue, "status": "status", "value": None},
    "crm.sales-targets": {"model": CRMSalesTarget, "status": "period_type", "value": "achieved_gp"},
    "crm.invoices": {"model": CRMInvoice, "status": "status", "value": "amount"},
    "crm.department-workflows": {"model": CRMDepartmentWorkflow, "status": "status", "value": None},
    "crm.tenders": {"model": CRMTender, "status": "outcome", "value": "estimated_value"},
    "crm.tender-documents": {"model": CRMTenderRepositoryDocument, "status": "status", "value": None},
    "crm.pmo-projects": {"model": CRMPMOProject, "status": "status", "value": None},
    "crm.sla-assignments": {"model": CRMSLAAssignment, "status": "status", "value": None},
    "crm.technical-services": {"model": CRMTechnicalService, "status": "arena", "value": None},
    "crm.customer-tickets": {"model": CRMTicket, "status": "status", "value": None},
    "crm.tasks": {"model": CRMTask, "status": "status", "value": None},
    "crm.quotes": {"model": CRMQuotation, "status": "status", "value": "total_amount"},
    "crm.automation": {"model": CRMAutomationRule, "status": "status", "value": None},
    "crm.licences": {"model": CRMLicence, "status": "status", "value": None},
    "hrm.employees": {"model": HRMEmployee, "status": "employment_status", "value": None},
    "hrm.departments": {"model": HRMDepartment, "status": "status", "value": None},
    "hrm.attendance": {"model": HRMAttendance, "status": "status", "value": "total_hours"},
    "hrm.leave": {"model": HRMLeave, "status": "status", "value": "total_days"},
    "hrm.payroll": {"model": HRMPayroll, "status": "payment_status", "value": "net_pay"},
    "hrm.recruitment": {"model": HRMRecruitment, "status": "application_status", "value": "expected_salary"},
    "hrm.performance": {"model": HRMPerformance, "status": "status", "value": "performance_score"},
    "hrm.training": {"model": HRMTraining, "status": "completion_status", "value": "cost"},
    "hrm.benefits": {"model": HRMBenefit, "status": "status", "value": "employer_contribution"},
    "hrm.documents": {"model": HRMDocument, "status": "status", "value": None},
    "hrm.activities": {"model": HRMActivity, "status": "status", "value": "actual_cost"},
    "hrm.grc": {"model": HRMGRCRecord, "status": "compliance_status", "value": None},
    "hrm.positions": {"model": HRMPosition, "status": "status", "value": "headcount_budget"},
    "hrm.onboarding": {"model": HRMOnboardingTask, "status": "status", "value": None},
    "hrm.leave-balances": {"model": HRMLeaveBalance, "status": "status", "value": "available_days"},
    "hrm.compensation": {"model": HRMCompensation, "status": "approval_status", "value": "base_salary"},
    "hrm.lifecycle": {"model": HRMLifecycleEvent, "status": "status", "value": None},
    "hrm.policy-acknowledgements": {"model": HRMPolicyAcknowledgement, "status": "status", "value": None},
    "hrm.employee-relations": {"model": HRMEmployeeRelationCase, "status": "status", "value": None},
    "hrm.surveys": {"model": HRMSurvey, "status": "status", "value": "average_score"},
    "hrm.asset-assignments": {"model": HRMAssetAssignment, "status": "status", "value": None},
    "hrm.staff-roles": {"model": StaffRoleAssignment, "status": "status", "value": "target_gp"},
    "finance.chart-accounts": {"model": FinanceChartAccount, "status": "is_active", "value": None},
    "finance.cost-centers": {"model": FinanceCostCenter, "status": "status", "value": None},
    "finance.journal-entries": {"model": FinanceJournalEntry, "status": "status", "value": "total_debit"},
    "finance.journal-lines": {"model": FinanceJournalLine, "status": None, "value": "debit_amount"},
    "finance.vendors": {"model": FinanceVendor, "status": "status", "value": None},
    "finance.bills": {"model": FinanceBill, "status": "status", "value": "amount"},
    "finance.payments": {"model": FinancePayment, "status": "status", "value": "amount"},
    "finance.invoices": {"model": FinanceInvoiceModel, "status": "status", "value": "total_amount"},
    "finance.receipts": {"model": FinanceReceipt, "status": None, "value": "amount"},
    "finance.credit-notes": {"model": FinanceCreditNote, "status": "status", "value": "amount"},
    "finance.expense-claims": {"model": FinanceExpenseClaim, "status": "approval_status", "value": "amount"},
    "finance.budgets": {"model": FinanceBudget, "status": "status", "value": "approved_amount"},
    "finance.purchase-requests": {"model": FinancePurchaseRequest, "status": "status", "value": "estimated_amount"},
    "finance.purchase-orders": {"model": FinancePurchaseOrder, "status": "status", "value": "total_amount"},
    "finance.bank-accounts": {"model": FinanceBankAccount, "status": "status", "value": "current_balance"},
    "finance.bank-transactions": {"model": FinanceBankTransaction, "status": "transaction_type", "value": "amount"},
    "finance.tax-records": {"model": FinanceTaxRecord, "status": "filing_status", "value": "tax_amount"},
    "finance.fixed-assets": {"model": FinanceFixedAsset, "status": "status", "value": "purchase_cost"},
    "finance.project-finance": {"model": FinanceProjectFinance, "status": "status", "value": "profitability"},
    "finance.revenue-records": {"model": FinanceRevenueRecord, "status": "status", "value": "amount"},
    "finance.approvals": {"model": FinanceApproval, "status": "status", "value": None},
    "finance.audit-trails": {"model": FinanceAuditTrail, "status": "action", "value": None},
    "finance.documents": {"model": FinanceDocumentModel, "status": "status", "value": None},
    "finance.integration-events": {"model": FinanceIntegrationEvent, "status": "status", "value": None},
    "admin.policies": {"model": OrganizationPolicy, "status": "status", "value": None},
    "admin.access-rights": {"model": AccessRight, "status": "status", "value": None},
    "enterprise.connectors": {"model": IntegrationConnector, "status": "status", "value": None},
    "enterprise.imports": {"model": DataImportBatch, "status": "status", "value": "imported_rows"},
    "enterprise.sequences": {"model": EntitySequence, "status": "active", "value": "next_number"},
    "enterprise.workflow-rules": {"model": WorkflowRule, "status": "status", "value": None},
    "enterprise.workflow-logs": {"model": WorkflowRunLog, "status": "outcome", "value": None},
    "enterprise.notifications": {"model": NotificationEvent, "status": "status", "value": None},
    "enterprise.knowledge-base": {"model": KnowledgeBaseArticle, "status": "status", "value": None},
    "enterprise.goals": {"model": OrganizationGoal, "status": "status", "value": "actual_value"},
    "crm.support-tickets": {"model": SupportTicket, "status": "status", "value": "csat_score"},
    "crm.project-tasks": {"model": ProjectTask, "status": "status", "value": "actual_hours"},
    "crm.project-milestones": {"model": ProjectMilestone, "status": "status", "value": "billing_amount"},
    "crm.project-risks": {"model": ProjectRisk, "status": "status", "value": None},
    "crm.territories": {"model": TerritoryRule, "status": "status", "value": None},
    "finance.inventory-items": {"model": ERPInventoryItem, "status": "status", "value": "quantity_on_hand"},
    "enterprise.portal-requests": {"model": PortalRequest, "status": "status", "value": None},
    "enterprise.communications": {"model": CommunicationLog, "status": "channel", "value": None},
    "enterprise.schedule-events": {"model": ScheduleEvent, "status": "status", "value": None},
    "enterprise.resource-allocations": {"model": ResourceAllocation, "status": "status", "value": "planned_hours"},
    "enterprise.capabilities": {"model": FeatureCapability, "status": "implementation_status", "value": None},
}


def _status_breakdown(db: Session, model, status_field: str | None):
    if not status_field:
        return []
    column = getattr(model, status_field)
    rows = (
        db.query(column.label("name"), func.count(model.id).label("count"))
        .group_by(column)
        .order_by(func.count(model.id).desc())
        .all()
    )
    return [{"name": row.name or "Unspecified", "count": row.count} for row in rows]


def _sum(db: Session, model, field: str):
    return float(db.query(func.coalesce(func.sum(getattr(model, field)), 0)).scalar() or 0)


def _count(db: Session, model, *criteria):
    query = db.query(func.count(model.id))
    if criteria:
        query = query.filter(*criteria)
    return int(query.scalar() or 0)


def department_detail(db: Session, department: str):
    employees = _count(db, HRMEmployee, HRMEmployee.department == department)
    activities = _count(db, HRMActivity, HRMActivity.department == department)
    activity_spend = _sum(db, HRMActivity, "actual_cost")
    certifications = _count(db, HRMTraining, HRMTraining.certification_awarded == True)  # noqa: E712
    training_spend = _sum(db, HRMTraining, "cost")
    budget = _sum(db, FinanceBudget, "approved_amount")
    actual = _sum(db, FinanceBudget, "actual_amount")
    if department == "Sales":
        performance = [
            f"Pipeline value: {_sum(db, CRMOpportunity, 'opportunity_value'):,.0f}",
            f"Won deals: {_count(db, CRMDeal, CRMDeal.deal_status == 'closed_won')}",
            f"Revenue: {_sum(db, CRMDeal, 'revenue_amount'):,.0f}",
        ]
    elif department == "Finance":
        performance = [
            f"Outstanding invoices: {max(_sum(db, FinanceInvoiceModel, 'total_amount') - _sum(db, FinanceInvoiceModel, 'paid_amount'), 0):,.0f}",
            f"Vendor bills: {_sum(db, FinanceBill, 'amount'):,.0f}",
            f"Budget actual: {actual:,.0f}",
        ]
    elif department == "HR":
        performance = [
            f"Pending leave: {_count(db, HRMLeave, HRMLeave.status == 'pending')}",
            f"Recruitment records: {_count(db, HRMRecruitment)}",
            f"HR activities: {activities}",
        ]
    elif department in ["PMO", "Technical"]:
        performance = [
            f"Open projects: {_count(db, CRMPMOProject, CRMPMOProject.status != 'completed')}",
            f"Active SLAs: {_count(db, CRMSLAAssignment, CRMSLAAssignment.status == 'active')}",
            f"Open tickets: {_count(db, CRMTicket, CRMTicket.status.in_(['open', 'in_progress']))}",
        ]
    else:
        performance = [
            f"Open work items: {_count(db, CRMDepartmentWorkflow, CRMDepartmentWorkflow.department == department, CRMDepartmentWorkflow.status != 'completed')}",
            f"GRC items: {_count(db, HRMGRCRecord, HRMGRCRecord.department == department)}",
        ]
    return {
        "name": department,
        "employees": employees,
        "activities": activities,
        "activity_spend": activity_spend,
        "certifications": certifications,
        "training_spend": training_spend,
        "budget": budget,
        "actual_spend": actual,
        "performance": performance,
    }


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return {
        key: db.query(config["model"]).count()
        for key, config in RESOURCE_MAP.items()
    }


@router.get("/executive")
def get_executive_dashboard(db: Session = Depends(get_db)):
    pipeline_value = _sum(db, CRMOpportunity, "opportunity_value")
    opportunity_gp = _sum(db, CRMOpportunity, "gross_profit")
    deal_revenue = _sum(db, CRMDeal, "revenue_amount")
    deal_gp = _sum(db, CRMDeal, "gross_profit")
    invoice_amount = _sum(db, CRMInvoice, "amount")
    paid_amount = _sum(db, CRMInvoice, "paid_amount")
    finance_invoice_amount = _sum(db, FinanceInvoiceModel, "total_amount")
    finance_receipts = _sum(db, FinanceReceipt, "amount")
    finance_revenue = _sum(db, FinanceRevenueRecord, "amount") or finance_invoice_amount
    finance_bills = _sum(db, FinanceBill, "amount")
    finance_expenses = _sum(db, FinanceExpenseClaim, "amount")
    bank_cash = _sum(db, FinanceBankAccount, "current_balance")
    payroll_cost = _sum(db, HRMPayroll, "net_pay")
    benefits_cost = _sum(db, HRMBenefit, "employer_contribution")
    training_cost = _sum(db, HRMTraining, "cost")
    target_gp = _sum(db, CRMSalesTarget, "target_gp")
    achieved_gp = _sum(db, CRMSalesTarget, "achieved_gp") or deal_gp or opportunity_gp

    departments = []
    department_names = [
        "Sales",
        "Bids",
        "Technical",
        "PMO",
        "Finance",
        "HR",
        "Operations",
        "Legal",
        "Marketing",
    ]
    for department in department_names:
        departments.append(
            {
                **department_detail(db, department),
                "open_work": (
                    _count(db, CRMOpportunity, CRMOpportunity.owner.ilike(f"%{department}%"))
                    + _count(db, CRMPMOProject, CRMPMOProject.status != "completed")
                    if department in ["Sales", "PMO", "Technical"]
                    else _count(db, CRMDepartmentWorkflow, CRMDepartmentWorkflow.department == department, CRMDepartmentWorkflow.status != "completed")
                ),
                "href": f"/analytics?department={department}",
            }
        )

    pipeline_by_stage = _status_breakdown(db, CRMOpportunity, "stage")
    revenue_by_status = _status_breakdown(db, CRMInvoice, "status")

    return {
        "kpis": {
            "accounts": _count(db, CRMAccount),
            "contacts": _count(db, CRMContact),
            "leads": _count(db, CRMLead),
            "opportunities": _count(db, CRMOpportunity),
            "open_deals": _count(db, CRMDeal, CRMDeal.deal_status == "open"),
            "closed_won": _count(db, CRMDeal, CRMDeal.deal_status == "closed_won"),
            "employees": _count(db, HRMEmployee, HRMEmployee.employment_status == "active"),
            "departments": _count(db, HRMDepartment),
            "projects": _count(db, CRMPMOProject),
            "active_slas": _count(db, CRMSLAAssignment, CRMSLAAssignment.status == "active"),
            "tickets_open": _count(db, CRMTicket, CRMTicket.status.in_(["open", "in_progress"])),
            "tenders_pending": _count(db, CRMTender, CRMTender.outcome == "pending"),
            "payroll_records": _count(db, HRMPayroll),
            "leave_pending": _count(db, HRMLeave, HRMLeave.status == "pending"),
        },
        "finance": {
            "pipeline_value": pipeline_value,
            "opportunity_gp": opportunity_gp,
            "deal_revenue": deal_revenue,
            "deal_gp": deal_gp,
            "invoice_amount": invoice_amount + finance_invoice_amount,
            "paid_amount": paid_amount + finance_receipts,
            "outstanding_debt": max((invoice_amount + finance_invoice_amount) - (paid_amount + finance_receipts), 0),
            "payroll_cost": payroll_cost,
            "benefits_cost": benefits_cost,
            "training_cost": training_cost,
            "vendor_bills": finance_bills,
            "expense_claims": finance_expenses,
            "cash_position": bank_cash,
            "recognized_revenue": finance_revenue,
            "people_cost": payroll_cost + benefits_cost + training_cost,
            "target_gp": target_gp,
            "achieved_gp": achieved_gp,
            "target_attainment": round((achieved_gp / target_gp) * 100, 2) if target_gp else 0,
        },
        "workload": {
            "open_projects": _count(db, CRMPMOProject, CRMPMOProject.status != "completed"),
            "active_slas": _count(db, CRMSLAAssignment, CRMSLAAssignment.status == "active"),
            "open_tickets": _count(db, CRMTicket, CRMTicket.status.in_(["open", "in_progress"])),
            "pending_tenders": _count(db, CRMTender, CRMTender.outcome == "pending"),
            "pending_leave": _count(db, HRMLeave, HRMLeave.status == "pending"),
            "pending_payroll": _count(db, HRMPayroll, HRMPayroll.payment_status == "pending"),
            "automation_rules": _count(db, CRMAutomationRule, CRMAutomationRule.status == "active"),
        },
        "departments": departments,
        "pipeline_by_stage": pipeline_by_stage,
        "revenue_by_status": revenue_by_status,
        "drilldowns": [
            {"label": "Sales Pipeline", "href": "/crm/opportunities", "value": _count(db, CRMOpportunity)},
            {"label": "Customer Accounts", "href": "/crm/accounts", "value": _count(db, CRMAccount)},
            {"label": "Projects", "href": "/crm/pmo-projects", "value": _count(db, CRMPMOProject)},
            {"label": "SLAs", "href": "/crm/sla-assignments", "value": _count(db, CRMSLAAssignment)},
            {"label": "HRM", "href": "/hrm", "value": _count(db, HRMEmployee)},
            {"label": "Payroll", "href": "/hrm/payroll", "value": payroll_cost},
            {"label": "Benefits", "href": "/hrm/benefits", "value": benefits_cost},
            {"label": "Reports", "href": "/analytics", "value": _count(db, CRMInvoice)},
        ],
    }


@router.get("/{domain}/{resource}")
def get_resource_analytics(domain: str, resource: str, db: Session = Depends(get_db)):
    key = f"{domain}.{resource}"
    config = RESOURCE_MAP.get(key)
    if not config:
        raise HTTPException(status_code=404, detail="Analytics resource not found")

    model = config["model"]
    value_field = config["value"]
    total_value = 0
    if value_field:
        total_value = db.query(func.coalesce(func.sum(getattr(model, value_field)), 0)).scalar()

    return {
        "resource": key,
        "total": db.query(model).count(),
        "total_value": float(total_value or 0),
        "by_status": _status_breakdown(db, model, config["status"]),
    }
