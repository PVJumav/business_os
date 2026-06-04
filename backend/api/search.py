from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.crm import (
    CRMAccount,
    CRMActivity,
    CRMContact,
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
from backend.models.hrm import (
    HRMBenefit,
    HRMDepartment,
    HRMDocument,
    HRMEmployee,
    HRMLeave,
    HRMPayroll,
    HRMRecruitment,
    HRMTraining,
)


router = APIRouter(prefix="/search", tags=["Global Search"])


def make_result(entity: str, title: str, subtitle: str, href: str, record: Any):
    return {
        "entity": entity,
        "title": title,
        "subtitle": subtitle,
        "href": href,
        "id": str(record.id),
    }


def entity_href(entity_type: str, record: Any):
    return f"/entities?type={entity_type}&id={record.id}"


@router.get("")
def global_search(
    query: str = Query(..., min_length=2),
    scope: str = Query(default="Company"),
    db: Session = Depends(get_db),
):
    term = f"%{query.strip()}%"
    results = []

    for item in (
        db.query(HRMEmployee)
        .filter(
            or_(
                HRMEmployee.first_name.ilike(term),
                HRMEmployee.last_name.ilike(term),
                HRMEmployee.email.ilike(term),
                HRMEmployee.employee_code.ilike(term),
                HRMEmployee.department.ilike(term),
                HRMEmployee.job_title.ilike(term),
                HRMEmployee.role_category.ilike(term),
            )
        )
        .limit(8)
        .all()
    ):
        results.append(
            make_result(
                "Staff",
                f"{item.first_name} {item.last_name}",
                f"{item.department or 'No department'} | {item.job_title or 'No role'}",
                f"/hrm/employees?mode=intelligence&employee={item.id}",
                item,
            )
        )

    for item in db.query(CRMAccount).filter(CRMAccount.company_name.ilike(term)).limit(6).all():
        results.append(
            make_result(
                "Account",
                item.company_name,
                f"{item.account_manager or 'No AM'} | {item.country or 'No country'} | {item.vertical or 'No vertical'}",
                entity_href("accounts", item),
                item,
            )
        )

    for item in (
        db.query(CRMOpportunity)
        .filter(or_(CRMOpportunity.title.ilike(term), CRMOpportunity.owner.ilike(term), CRMOpportunity.stage.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(
            make_result(
                "Opportunity",
                item.title,
                f"{item.stage or 'No stage'} | GP {float(item.gross_profit or 0):,.0f}",
                entity_href("opportunities", item),
                item,
            )
        )

    for item in (
        db.query(CRMDeal)
        .filter(or_(CRMDeal.deal_name.ilike(term), CRMDeal.owner.ilike(term), CRMDeal.deal_status.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(
            make_result("Deal", item.deal_name, f"{item.deal_status or 'open'} | GP {float(item.gross_profit or 0):,.0f}", entity_href("deals", item), item)
        )

    for item in (
        db.query(CRMInvoice)
        .filter(or_(CRMInvoice.invoice_number.ilike(term), CRMInvoice.debt_owner.ilike(term), CRMInvoice.status.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(
            make_result(
                "Invoice",
                item.invoice_number,
                f"{item.status or 'draft'} | Amount {float(item.amount or 0):,.0f}",
                "/crm/invoices",
                item,
            )
        )

    for item in (
        db.query(CRMPMOProject)
        .filter(or_(CRMPMOProject.project_name.ilike(term), CRMPMOProject.project_manager.ilike(term), CRMPMOProject.status.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(make_result("Project", item.project_name, f"{item.stage or 'planning'} | {item.status or 'active'}", entity_href("projects", item), item))

    for item in (
        db.query(CRMSLAAssignment)
        .filter(or_(CRMSLAAssignment.solution.ilike(term), CRMSLAAssignment.assigned_engineer.ilike(term), CRMSLAAssignment.status.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(make_result("SLA", item.solution, f"{item.assigned_engineer or 'Unassigned'} | {item.status or 'active'}", entity_href("slas", item), item))

    for item in (
        db.query(CRMTender)
        .filter(or_(CRMTender.tender_title.ilike(term), CRMTender.tender_number.ilike(term), CRMTender.bid_manager.ilike(term), CRMTender.outcome.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(make_result("Tender", item.tender_title, f"{item.stage or 'prequalification'} | {item.outcome or 'pending'}", "/crm/tenders", item))

    for item in (
        db.query(CRMTicket)
        .filter(or_(CRMTicket.ticket_number.ilike(term), CRMTicket.issue_title.ilike(term), CRMTicket.assigned_engineer.ilike(term), CRMTicket.status.ilike(term)))
        .limit(6)
        .all()
    ):
        results.append(make_result("Ticket", item.issue_title, f"{item.severity or 'medium'} | {item.status or 'open'}", entity_href("support-tickets", item), item))

    for item in db.query(CRMContact).filter(or_(CRMContact.first_name.ilike(term), CRMContact.last_name.ilike(term), CRMContact.email.ilike(term))).limit(4).all():
        results.append(make_result("Contact", f"{item.first_name} {item.last_name}", item.email or item.job_title or "Contact", entity_href("contacts", item), item))

    for item in db.query(CRMLead).filter(or_(CRMLead.contact_name.ilike(term), CRMLead.company_name.ilike(term), CRMLead.assigned_to.ilike(term))).limit(4).all():
        results.append(make_result("Lead", item.contact_name, item.company_name or item.status or "Lead", entity_href("leads", item), item))

    for item in db.query(HRMDepartment).filter(or_(HRMDepartment.name.ilike(term), HRMDepartment.description.ilike(term))).limit(4).all():
        results.append(make_result("Department", item.name, item.status or "active", entity_href("departments", item), item))

    for item in db.query(HRMPayroll).filter(or_(HRMPayroll.payroll_month.ilike(term), HRMPayroll.payment_status.ilike(term))).limit(4).all():
        results.append(make_result("Payroll", item.payroll_month, f"{item.payment_status or 'pending'} | Net {float(item.net_pay or 0):,.0f}", "/hrm/payroll", item))

    for item in db.query(HRMBenefit).filter(or_(HRMBenefit.benefit_name.ilike(term), HRMBenefit.provider.ilike(term), HRMBenefit.status.ilike(term))).limit(4).all():
        results.append(make_result("Benefit", item.benefit_name, item.provider or item.status or "Benefit", "/hrm/benefits", item))

    for item in db.query(HRMLeave).filter(or_(HRMLeave.leave_type.ilike(term), HRMLeave.status.ilike(term), HRMLeave.reason.ilike(term))).limit(4).all():
        results.append(make_result("Leave", item.leave_type, item.status or "pending", "/hrm/leave", item))

    for item in db.query(HRMRecruitment).filter(or_(HRMRecruitment.job_title.ilike(term), HRMRecruitment.candidate_name.ilike(term), HRMRecruitment.application_status.ilike(term))).limit(4).all():
        results.append(make_result("Recruitment", item.candidate_name, f"{item.job_title} | {item.application_status or 'pending'}", "/hrm/recruitment", item))

    for item in db.query(HRMTraining).filter(or_(HRMTraining.training_title.ilike(term), HRMTraining.training_provider.ilike(term), HRMTraining.completion_status.ilike(term))).limit(4).all():
        results.append(make_result("Training", item.training_title, item.completion_status or "not_started", "/hrm/training", item))

    for item in db.query(HRMDocument).filter(or_(HRMDocument.document_title.ilike(term), HRMDocument.document_type.ilike(term), HRMDocument.status.ilike(term))).limit(4).all():
        results.append(make_result("Document", item.document_title, item.document_type, "/hrm/documents", item))

    for item in db.query(CRMActivity).filter(or_(CRMActivity.subject.ilike(term), CRMActivity.description.ilike(term), CRMActivity.created_by.ilike(term))).limit(4).all():
        results.append(make_result("Activity", item.subject, item.status or item.activity_type or "Activity", "/crm/activities", item))

    for item in db.query(CRMSalesTarget).filter(or_(CRMSalesTarget.target_owner.ilike(term), CRMSalesTarget.arena.ilike(term), CRMSalesTarget.period_label.ilike(term))).limit(4).all():
        results.append(make_result("Target", item.target_owner, f"{item.period_label} | Target GP {float(item.target_gp or 0):,.0f}", "/crm/sales-targets", item))

    priorities = {
        "HRM": {"Staff", "Department", "Payroll", "Benefit", "Leave", "Recruitment", "Training", "Document"},
        "CRM": {"Account", "Opportunity", "Deal", "Invoice", "Project", "SLA", "Tender", "Ticket", "Contact", "Lead", "Activity", "Target"},
        "Finance": {"Invoice", "Payroll"},
        "Projects": {"Project", "SLA", "Ticket", "Tender"},
    }
    preferred = priorities.get(scope, set())
    results.sort(key=lambda item: 0 if item["entity"] in preferred else 1)
    return results[:40]
