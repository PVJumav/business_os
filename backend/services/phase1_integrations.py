from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.crm import (
    CRMAccount,
    CRMAccountIssue,
    CRMActivity,
    CRMContract,
    CRMCustomerLPO,
    CRMOpportunity,
    CRMQuotation,
    CRMQuoteLineItem,
)
from backend.models.finance import (
    FinanceApproval,
    FinanceBill,
    FinanceBudget,
    FinanceExpense,
    FinanceIntegrationEvent,
    FinanceInvoice,
    FinanceInvoiceLineItem,
    FinancePayrollPosting,
    FinanceProjectFinancialRecord,
    FinancePayment,
    FinancePurchaseOrder,
    FinancePurchaseRequest,
    FinanceReceipt,
    FinanceRevenueRecognitionRecord,
    FinanceRevenueRecord,
    FinanceVendor,
)
from backend.models.hrm import HRMEmployee, HRMPayrollRun
from backend.models.projects import (
    LicenseTracking,
    Project,
    ProjectBudget,
    ProjectExpense,
    ProjectMilestone,
    ProjectPhase,
    ProjectSignoff,
    ProjectStatusUpdate,
    SLA,
    SLATicket,
)
from backend.schemas.auth import UserResponse
from backend.services.iam_enterprise import create_user_for_employee, disable_user_for_employee_termination


IMPLEMENTATION_PHASES = [
    "Initiation",
    "Documentation",
    "Deployment",
    "Testing",
    "Training",
    "Signoff",
    "Closure",
]


def money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def event(
    db: Session,
    source: str,
    target: str,
    event_type: str,
    record_type: str,
    record_id: UUID | None,
    summary: str,
    status: str = "processed",
) -> None:
    db.add(
        FinanceIntegrationEvent(
            source_module=source,
            target_module=target,
            event_type=event_type,
            related_record_type=record_type,
            related_record_id=record_id,
            status=status,
            payload_summary=summary,
            processed_at=datetime.now(timezone.utc),
        )
    )


def next_code(db: Session, model, field_name: str, prefix: str) -> str:
    existing = db.query(model).count() + 1
    candidate = f"{prefix}-{existing:05d}"
    field = getattr(model, field_name)
    while db.query(model).filter(field == candidate).first():
        existing += 1
        candidate = f"{prefix}-{existing:05d}"
    return candidate


def employee_created(db: Session, employee_id: UUID, user: UserResponse | None = None):
    employee = db.query(HRMEmployee).filter(HRMEmployee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    account = create_user_for_employee(db, employee, user)
    event(db, "hrms", "iam", "employee.created", "hrm_employees", employee.id, f"Provisioned user account {account.email}")
    db.commit()
    return {"user_id": str(account.id), "email": account.email}


def employee_terminated(db: Session, employee_id: UUID, user: UserResponse | None = None):
    disable_user_for_employee_termination(db, employee_id, user)
    event(db, "hrms", "iam", "employee.terminated", "hrm_employees", employee_id, "Disabled linked IAM user if present")
    db.commit()
    return {"status": "processed"}


def validate_lpo_against_quote(lpo: CRMCustomerLPO, quote: CRMQuotation | None) -> dict[str, Any]:
    if not quote:
        lpo.validation_status = "quote_missing"
        lpo.approval_status = "pending"
        lpo.variance_reason = "No quotation was linked to the LPO."
        return {"valid": False, "variance": float(lpo.total_amount or 0), "reason": lpo.variance_reason}

    quote_total = money(quote.total_amount)
    lpo_total = money(lpo.total_amount)
    variance = lpo_total - quote_total
    lpo.variance_amount = variance
    if variance == 0:
        lpo.validation_status = "matched"
        lpo.approval_status = "not_required"
        lpo.variance_reason = None
        return {"valid": True, "variance": 0, "reason": None}

    lpo.validation_status = "variance"
    lpo.approval_status = "pending"
    lpo.variance_reason = f"LPO total {lpo_total} differs from quote total {quote_total}."
    return {"valid": False, "variance": float(variance), "reason": lpo.variance_reason}


def lpo_uploaded(db: Session, payload: dict[str, Any], user: UserResponse | None = None):
    quotation_id = payload.get("quotation_id")
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first() if quotation_id else None
    if quotation_id and not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    account_id = payload.get("account_id") or (str(quote.opportunity.account_id) if quote and quote.opportunity else None)
    opportunity_id = payload.get("opportunity_id") or (str(quote.opportunity_id) if quote else None)
    if not account_id:
        raise HTTPException(status_code=422, detail="LPO must link to a CRM account or quotation with an account")

    lpo = CRMCustomerLPO(
        lpo_number=payload.get("lpo_number") or next_code(db, CRMCustomerLPO, "lpo_number", "IS-LPO"),
        account_id=account_id,
        opportunity_id=opportunity_id,
        quotation_id=quotation_id,
        lpo_date=payload.get("lpo_date") or date.today(),
        currency=payload.get("currency") or "KES",
        subtotal=payload.get("subtotal") or (quote.subtotal if quote else 0),
        tax_amount=payload.get("tax_amount") or (quote.tax_amount if quote else 0),
        discount_amount=payload.get("discount_amount") or (quote.discount_amount if quote else 0),
        total_amount=payload.get("total_amount") or (quote.total_amount if quote else 0),
        document_url=payload.get("document_url"),
        uploaded_by=getattr(user, "full_name", None) or getattr(user, "email", None),
        notes=payload.get("notes"),
    )
    db.add(lpo)
    db.flush()
    validation = validate_lpo_against_quote(lpo, quote)
    if not validation["valid"]:
        db.add(
            FinanceApproval(
                approval_type="lpo_variance",
                related_record_type="crm.customer_lpos",
                related_record_id=lpo.id,
                requested_by=getattr(user, "email", None),
                approver="finance_manager",
                status="pending",
                comments=validation["reason"],
            )
        )
    event(db, "crm", "finance", "crm_lpo_uploaded", "crm.customer_lpos", lpo.id, validation["reason"] or "LPO matched quotation")
    db.commit()
    db.refresh(lpo)
    return {"lpo_id": str(lpo.id), "validation": validation}


def quote_approved(db: Session, quotation_id: UUID, user: UserResponse | None = None):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    quote.approval_status = "approved"
    quote.status = "approved"
    quote.approved_by = getattr(user, "full_name", None) or getattr(user, "email", None)
    if quote.opportunity_id:
        opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == quote.opportunity_id).first()
        if opportunity:
            opportunity.stage = "Stage 1.d Commit/Award"
            opportunity.approval_status = "approved"
    event(db, "crm", "crm", "crm_quote_approved", "crm.quotations", quote.id, "Quote approved and opportunity moved to commit/award")
    db.commit()
    return {"quote_id": str(quote.id), "status": quote.status}


def quote_accepted(db: Session, quotation_id: UUID, user: UserResponse | None = None):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quote.valid_until and quote.valid_until < date.today():
        raise HTTPException(status_code=422, detail="Expired quotes cannot be accepted")
    quote.status = "accepted"
    quote.approval_status = "approved"
    event(db, "crm", "crm", "crm_quote_accepted", "crm.quotations", quote.id, "Quote accepted by customer")
    db.commit()
    return {"quote_id": str(quote.id), "status": "accepted"}


def contract_from_quote_lpo(db: Session, quotation_id: UUID, lpo_id: UUID | None = None, user: UserResponse | None = None):
    quote = db.query(CRMQuotation).filter(CRMQuotation.id == quotation_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quote.status not in {"accepted", "approved"}:
        raise HTTPException(status_code=422, detail="Only approved or accepted quotes can generate contracts")

    lpo = db.query(CRMCustomerLPO).filter(CRMCustomerLPO.id == lpo_id).first() if lpo_id else None
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == quote.opportunity_id).first() if quote.opportunity_id else None
    account_id = lpo.account_id if lpo else (opportunity.account_id if opportunity else None)
    if not account_id:
        raise HTTPException(status_code=422, detail="Contract requires an account")

    contract = CRMContract(
        contract_number=next_code(db, CRMContract, "contract_number", "IS-CON"),
        account_id=account_id,
        opportunity_id=quote.opportunity_id,
        deal_id=quote.deal_id,
        contract_title=quote.title,
        contract_type="customer_award",
        start_date=date.today(),
        end_date=quote.valid_until or (date.today() + timedelta(days=365)),
        renewal_date=(quote.valid_until or (date.today() + timedelta(days=365))) - timedelta(days=30),
        contract_value=lpo.total_amount if lpo else quote.total_amount,
        status="draft",
        notes=f"Generated from quote {quote.quote_number}" + (f" and LPO {lpo.lpo_number}" if lpo else ""),
    )
    db.add(contract)
    db.flush()
    if lpo:
        lpo.contract_id = contract.id
    event(db, "crm", "crm", "crm_contract_generated", "crm.contracts", contract.id, "Contract draft generated from quote/LPO")
    db.commit()
    db.refresh(contract)
    return {"contract_id": str(contract.id), "contract_number": contract.contract_number}


def activate_contract(db: Session, contract_id: UUID, user: UserResponse | None = None):
    contract = db.query(CRMContract).filter(CRMContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.status = "active"
    sla = db.query(SLA).filter(SLA.contract_id == contract.id).first()
    if not sla:
        sla = SLA(
            sla_number=next_code(db, SLA, "sla_number", "IS-SLA"),
            account_id=contract.account_id,
            contract_id=contract.id,
            sla_name=f"SLA for {contract.contract_title}",
            tier="standard",
            start_date=contract.start_date,
            end_date=contract.end_date,
            status="active",
        )
        db.add(sla)
    event(db, "crm", "projects", "crm_contract_activated", "crm.contracts", contract.id, "Contract activated and SLA created/confirmed")
    db.commit()
    db.refresh(contract)
    return {"contract_id": str(contract.id), "sla_id": str(sla.id)}


def create_invoice_from_quote_lpo(db: Session, quote: CRMQuotation, lpo: CRMCustomerLPO | None, project: Project | None, user: UserResponse | None):
    number_source = lpo.lpo_number if lpo else quote.quote_number
    invoice_number = f"INV-{number_source}"
    invoice = db.query(FinanceInvoice).filter(FinanceInvoice.invoice_number == invoice_number).first()
    if invoice:
        return invoice
    invoice = FinanceInvoice(
        invoice_number=invoice_number,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        account_id=(lpo.account_id if lpo else (quote.opportunity.account_id if quote.opportunity else None)),
        deal_id=quote.deal_id,
        project_id=project.id if project else None,
        subtotal=(lpo.subtotal if lpo else quote.subtotal) or 0,
        tax_amount=(lpo.tax_amount if lpo else quote.tax_amount) or 0,
        discount_amount=(lpo.discount_amount if lpo else quote.discount_amount) or 0,
        total_amount=(lpo.total_amount if lpo else quote.total_amount) or 0,
        approval_status="draft",
        status="draft",
        notes="Created from CRM quote/LPO workflow",
    )
    db.add(invoice)
    db.flush()
    for line in db.query(CRMQuoteLineItem).filter(CRMQuoteLineItem.quotation_id == quote.id).all():
        db.add(
            FinanceInvoiceLineItem(
                invoice_id=invoice.id,
                product_service_id=line.product_service_id,
                description=line.line_description or "CRM quoted item",
                quantity=line.quantity or 1,
                unit_price=line.unit_price or 0,
                discount_amount=0,
                tax_rate=line.tax_percent or 0,
                tax_amount=0,
                line_total=line.line_total or 0,
            )
        )
    return invoice


def create_project_from_opportunity(db: Session, opportunity: CRMOpportunity, quote: CRMQuotation | None, contract: CRMContract | None, user: UserResponse | None):
    project = db.query(Project).filter(Project.crm_opportunity_id == opportunity.id).first()
    if project:
        return project
    project = Project(
        project_code=next_code(db, Project, "project_code", "IS-PRJ"),
        project_name=opportunity.title,
        project_type="customer_implementation",
        lifecycle_status="draft",
        implementation_stage="Initiation",
        owner_user_id=getattr(user, "id", None),
        crm_account_id=opportunity.account_id,
        crm_opportunity_id=opportunity.id,
        crm_quotation_id=quote.id if quote else None,
        crm_contract_id=contract.id if contract else None,
        approved_budget=(quote.total_amount if quote else opportunity.opportunity_value) or 0,
        invoiced_amount=0,
        notes="Created from closed-won CRM opportunity",
    )
    db.add(project)
    db.flush()
    for index, phase_name in enumerate(IMPLEMENTATION_PHASES, start=1):
        db.add(ProjectPhase(project_id=project.id, phase_name=phase_name, sequence=index, status="not_started"))
    db.add(ProjectBudget(project_id=project.id, budget_name=f"Budget for {project.project_name}", approved_amount=project.approved_budget or 0, approval_status="draft"))
    db.add(
        FinanceBudget(
            budget_name=f"Project budget - {project.project_name}",
            budget_type="project",
            project_id=project.id,
            fiscal_year=str(date.today().year),
            approved_amount=project.approved_budget or 0,
            approval_status="draft",
            status="active",
        )
    )
    return project


def create_license_and_procurement_requirements(db: Session, quote: CRMQuotation | None, project: Project | None, opportunity: CRMOpportunity, user: UserResponse | None):
    if not quote:
        return []
    created: list[str] = []
    lines = db.query(CRMQuoteLineItem).filter(CRMQuoteLineItem.quotation_id == quote.id).all()
    for line in lines:
        description = (line.line_description or "").lower()
        if "license" not in description and "licence" not in description:
            continue
        license_record = LicenseTracking(
            license_number=next_code(db, LicenseTracking, "license_number", "IS-LIC"),
            account_id=opportunity.account_id,
            project_id=project.id if project else None,
            opportunity_id=opportunity.id,
            product_service_id=line.product_service_id,
            license_name=line.line_description or f"License for {opportunity.title}",
            activation_date=None,
            expiry_date=(date.today() + timedelta(days=365)),
            renewal_date=(date.today() + timedelta(days=335)),
            renewal_owner=opportunity.owner,
            notification_status="pending",
            status="active",
        )
        db.add(license_record)
        db.flush()
        request = FinancePurchaseRequest(
            request_number=next_code(db, FinancePurchaseRequest, "request_number", "IS-PR"),
            requested_by=getattr(user, "email", None) or opportunity.owner,
            department="Projects",
            request_date=date.today(),
            required_date=date.today() + timedelta(days=14),
            description=f"License procurement for {license_record.license_name}",
            estimated_amount=line.line_total or 0,
            approval_status="submitted",
            status="open",
        )
        db.add(request)
        db.flush()
        created.append(str(license_record.id))
    return created


def opportunity_closed_won(db: Session, opportunity_id: UUID, user: UserResponse | None = None, payload: dict[str, Any] | None = None):
    payload = payload or {}
    opportunity = db.query(CRMOpportunity).filter(CRMOpportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    quote = None
    if payload.get("quotation_id"):
        quote = db.query(CRMQuotation).filter(CRMQuotation.id == payload["quotation_id"]).first()
    quote = quote or db.query(CRMQuotation).filter(CRMQuotation.opportunity_id == opportunity.id, CRMQuotation.status.in_(["accepted", "approved"])).order_by(CRMQuotation.created_at.desc()).first()
    lpo = None
    if payload.get("lpo_id"):
        lpo = db.query(CRMCustomerLPO).filter(CRMCustomerLPO.id == payload["lpo_id"]).first()
    lpo = lpo or db.query(CRMCustomerLPO).filter(CRMCustomerLPO.opportunity_id == opportunity.id).order_by(CRMCustomerLPO.created_at.desc()).first()
    contract = None
    if payload.get("contract_id"):
        contract = db.query(CRMContract).filter(CRMContract.id == payload["contract_id"]).first()
    contract = contract or db.query(CRMContract).filter(CRMContract.opportunity_id == opportunity.id).order_by(CRMContract.created_at.desc()).first()

    opportunity.status = "closed_won"
    opportunity.stage = "Stage 6.a Closed as Won"
    opportunity.actual_close_date = date.today()
    opportunity.closed_at = datetime.now(timezone.utc)
    project = create_project_from_opportunity(db, opportunity, quote, contract, user)
    invoice = create_invoice_from_quote_lpo(db, quote, lpo, project, user) if quote else None
    licenses = create_license_and_procurement_requirements(db, quote, project, opportunity, user)
    if contract:
        activate_contract(db, contract.id, user)
    db.add(
        FinanceRevenueRecord(
            revenue_source="closed_won_opportunity",
            account_id=opportunity.account_id,
            deal_id=None,
            invoice_id=invoice.id if invoice else None,
            source_module="crm",
            source_record_id=opportunity.id,
            revenue_type="forecast",
            recognition_date=date.today(),
            amount=opportunity.opportunity_value or 0,
            status="forecast",
        )
    )
    event(db, "crm", "phase1", "crm_opportunity_closed_won", "crm.opportunities", opportunity.id, "Closed-won deal created project, invoice draft, budget, revenue forecast, and license procurement requirements")
    db.commit()
    return {
        "opportunity_id": str(opportunity.id),
        "project_id": str(project.id),
        "invoice_id": str(invoice.id) if invoice else None,
        "license_ids": licenses,
    }


def finance_invoice_paid(db: Session, invoice_id: UUID, payload: dict[str, Any] | None = None, user: UserResponse | None = None):
    payload = payload or {}
    invoice = db.query(FinanceInvoice).filter(FinanceInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    payment_amount = money(payload.get("amount") or invoice.total_amount)
    invoice.paid_amount = min(money(invoice.total_amount), money(invoice.paid_amount) + payment_amount)
    invoice.status = "paid" if money(invoice.paid_amount) >= money(invoice.total_amount) else "partially_paid"
    receipt = FinanceReceipt(
        receipt_number=next_code(db, FinanceReceipt, "receipt_number", "IS-RCT"),
        invoice_id=invoice.id,
        receipt_date=date.today(),
        amount=payment_amount,
        payment_method=payload.get("payment_method") or "bank_transfer",
        received_from=payload.get("received_from"),
        notes="Receipt generated from invoice payment workflow",
    )
    db.add(receipt)
    db.add(
        FinanceRevenueRecognitionRecord(
            invoice_id=invoice.id,
            project_id=invoice.project_id,
            account_id=invoice.account_id,
            recognition_method=payload.get("recognition_method") or "payment",
            recognition_date=date.today(),
            amount=payment_amount,
            status="recognized",
        )
    )
    if invoice.account_id:
        db.add(
            CRMActivity(
                related_type="account",
                related_id=invoice.account_id,
                activity_type="payment",
                subject=f"Payment received for {invoice.invoice_number}",
                description=f"Received {payment_amount} against invoice {invoice.invoice_number}",
                created_by=getattr(user, "email", None),
                status="completed",
            )
        )
    event(db, "finance", "crm", "finance_invoice_paid", "finance.invoices", invoice.id, "Payment recorded, receipt generated, revenue recognized, and CRM account timeline updated")
    db.commit()
    return {"invoice_id": str(invoice.id), "status": invoice.status, "receipt_id": str(receipt.id)}


def purchase_order_from_request(db: Session, request_id: UUID, payload: dict[str, Any] | None = None, user: UserResponse | None = None):
    payload = payload or {}
    request = db.query(FinancePurchaseRequest).filter(FinancePurchaseRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    if request.approval_status not in {"approved", "submitted"}:
        raise HTTPException(status_code=422, detail="Purchase request must be submitted or approved before PO creation")
    vendor_name = payload.get("vendor_name") or "Unassigned Vendor"
    vendor = db.query(FinanceVendor).filter(FinanceVendor.vendor_name.ilike(vendor_name)).first()
    if not vendor:
        vendor = FinanceVendor(vendor_name=vendor_name, vendor_type=payload.get("vendor_type") or "license_supplier", email=payload.get("vendor_email"), status="active")
        db.add(vendor)
        db.flush()
    po = FinancePurchaseOrder(
        po_number=next_code(db, FinancePurchaseOrder, "po_number", "IS-PO"),
        purchase_request_id=request.id,
        vendor_id=vendor.id,
        po_date=date.today(),
        expected_delivery_date=payload.get("expected_delivery_date"),
        total_amount=payload.get("total_amount") or request.estimated_amount or 0,
        approval_status="draft",
        goods_received_status="pending",
        status="open",
        notes="Created from approved project/license procurement request",
    )
    request.status = "po_created"
    db.add(po)
    event(db, "finance", "projects", "purchase_order_created", "finance.purchase_requests", request.id, "Purchase order created for project/license procurement")
    db.commit()
    db.refresh(po)
    return {"purchase_order_id": str(po.id), "po_number": po.po_number, "vendor_id": str(vendor.id)}


def vendor_invoice_received(db: Session, po_id: UUID, payload: dict[str, Any] | None = None, user: UserResponse | None = None):
    payload = payload or {}
    po = db.query(FinancePurchaseOrder).filter(FinancePurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    bill = FinanceBill(
        vendor_id=po.vendor_id,
        bill_number=payload.get("bill_number") or next_code(db, FinanceBill, "bill_number", "IS-BILL"),
        bill_date=payload.get("bill_date") or date.today(),
        due_date=payload.get("due_date") or (date.today() + timedelta(days=30)),
        amount=payload.get("amount") or po.total_amount or 0,
        paid_amount=0,
        tax_amount=payload.get("tax_amount") or 0,
        status="pending",
        approval_status="submitted",
        project_id=payload.get("project_id"),
        notes="Vendor invoice matched to purchase order",
    )
    db.add(bill)
    db.flush()
    po.bill_id = bill.id
    event(db, "finance", "finance", "vendor_invoice_received", "finance.purchase_orders", po.id, "Vendor invoice received and matched to PO")
    db.commit()
    return {"bill_id": str(bill.id), "bill_number": bill.bill_number}


def vendor_invoice_paid(db: Session, bill_id: UUID, payload: dict[str, Any] | None = None, user: UserResponse | None = None):
    payload = payload or {}
    bill = db.query(FinanceBill).filter(FinanceBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Vendor invoice not found")
    payment_amount = money(payload.get("amount") or bill.amount)
    bill.paid_amount = min(money(bill.amount), money(bill.paid_amount) + payment_amount)
    bill.status = "paid" if money(bill.paid_amount) >= money(bill.amount) else "partially_paid"
    payment = FinancePayment(
        payment_number=next_code(db, FinancePayment, "payment_number", "IS-PMT"),
        payment_type="vendor",
        vendor_id=bill.vendor_id,
        bill_id=bill.id,
        payment_date=date.today(),
        amount=payment_amount,
        payment_method=payload.get("payment_method") or "bank_transfer",
        status="paid",
        approved_by=getattr(user, "email", None),
        notes="Vendor payment generated from procurement workflow",
    )
    db.add(payment)
    if bill.project_id:
        db.add(
            FinanceProjectFinancialRecord(
                project_id=bill.project_id,
                actual_cost=payment_amount,
                status="open",
            )
        )
    event(db, "finance", "projects", "vendor_invoice_paid", "finance.bills", bill.id, "Vendor payment recorded and project cost updated where applicable")
    db.commit()
    return {"bill_id": str(bill.id), "status": bill.status, "payment_id": str(payment.id)}


def project_expense_approved(db: Session, expense_id: UUID, user: UserResponse | None = None):
    expense = db.query(ProjectExpense).filter(ProjectExpense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Project expense not found")
    expense.approval_status = "approved"
    finance_expense = FinanceExpense(
        expense_number=next_code(db, FinanceExpense, "expense_number", "IS-EXP"),
        expense_date=expense.expense_date or date.today(),
        category=expense.expense_category,
        claimant_employee_id=expense.incurred_by_employee_id,
        project_id=expense.project_id,
        source_module="projects",
        source_record_id=expense.id,
        source_label="Approved project expense",
        amount=expense.amount or 0,
        approval_status="approved",
        payment_status="unpaid",
        status="approved",
        notes=expense.notes,
    )
    db.add(finance_expense)
    db.flush()
    expense.finance_expense_id = finance_expense.id
    record = FinanceProjectFinancialRecord(project_id=expense.project_id, actual_cost=expense.amount or 0, status="open")
    db.add(record)
    event(db, "projects", "finance", "expense.approved", "projects.expenses", expense.id, "Posted approved project expense to Finance")
    db.commit()
    return {"finance_expense_id": str(finance_expense.id), "project_financial_record_id": str(record.id)}


def project_signed_off(db: Session, project_id: UUID, payload: dict[str, Any] | None = None, user: UserResponse | None = None):
    payload = payload or {}
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.lifecycle_status = "signed_off"
    project.signoff_status = "signed_off"
    project.progress_percent = 100
    project.locked = True
    signoff = ProjectSignoff(
        project_id=project.id,
        signoff_type=payload.get("signoff_type") or "customer_acceptance",
        signed_by=payload.get("signed_by") or getattr(user, "full_name", None),
        signed_at=datetime.now(timezone.utc),
        status="signed_off",
        notes=payload.get("notes"),
    )
    db.add(signoff)
    db.add(ProjectStatusUpdate(project_id=project.id, status_date=date.today(), progress_percent=100, summary="Project signed off and locked.", created_by=getattr(user, "email", None)))
    db.add(
        FinanceProjectFinancialRecord(
            project_id=project.id,
            budget_amount=project.approved_budget or 0,
            actual_cost=project.actual_cost or 0,
            invoiced_amount=project.invoiced_amount or 0,
            profitability_amount=money(project.invoiced_amount) - money(project.actual_cost),
            status="final_review",
        )
    )
    if project.crm_account_id:
        db.add(
            CRMActivity(
                related_type="account",
                related_id=project.crm_account_id,
                activity_type="project_signoff",
                subject=f"Project signed off: {project.project_name}",
                description="Project completion and customer signoff recorded by Projects.",
                created_by=getattr(user, "email", None),
                status="completed",
            )
        )
    event(db, "projects", "finance", "project_signed_off", "projects.projects", project.id, "Project locked and final financial review created")
    db.commit()
    return {"project_id": str(project.id), "signoff_id": str(signoff.id), "locked": project.locked}


def sla_breached(db: Session, ticket_id: UUID, user: UserResponse | None = None):
    ticket = db.query(SLATicket).filter(SLATicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="SLA ticket not found")
    ticket.sla_status = "breached"
    ticket.escalation_level = (ticket.escalation_level or 0) + 1
    if ticket.account_id:
        db.add(
            CRMAccountIssue(
                account_id=ticket.account_id,
                issue_title=f"SLA breach: {ticket.subject}",
                issue_type="sla_breach",
                severity=ticket.priority,
                status="open",
                owner=getattr(user, "email", None),
                feedback=ticket.resolution_notes,
                due_date=date.today() + timedelta(days=2),
            )
        )
        db.add(
            CRMActivity(
                related_type="account",
                related_id=ticket.account_id,
                activity_type="sla_breach",
                subject=f"SLA breach escalated: {ticket.subject}",
                description="Projects SLA ticket breached and was pushed to CRM customer success history.",
                created_by=getattr(user, "email", None),
                status="pending",
            )
        )
    event(db, "projects", "crm", "sla_breached", "projects.sla_tickets", ticket.id, "SLA breach escalated to CRM account issue/activity")
    db.commit()
    return {"ticket_id": str(ticket.id), "sla_status": ticket.sla_status, "escalation_level": ticket.escalation_level}


def renewal_opportunities(db: Session, days: int = 60, user: UserResponse | None = None):
    cutoff = date.today() + timedelta(days=days)
    created: list[str] = []
    expiring = db.query(LicenseTracking).filter(LicenseTracking.renewal_date <= cutoff, LicenseTracking.status == "active").all()
    for license_record in expiring:
        existing = db.query(CRMOpportunity).filter(
            CRMOpportunity.account_id == license_record.account_id,
            CRMOpportunity.service_scope == "renewal",
            CRMOpportunity.renewal_date == license_record.renewal_date,
        ).first()
        if existing:
            continue
        opportunity = CRMOpportunity(
            account_id=license_record.account_id,
            title=f"Renewal - {license_record.license_name}",
            stage="Stage 5 Renewal or Exit",
            opportunity_value=0,
            probability=60,
            expected_close_date=license_record.renewal_date,
            renewal_date=license_record.renewal_date,
            licence_expiry_date=license_record.expiry_date,
            owner=license_record.renewal_owner,
            pipeline_type="Renewal/Exit",
            service_scope="renewal",
            status="open",
        )
        db.add(opportunity)
        db.flush()
        created.append(str(opportunity.id))
    event(db, "projects", "crm", "license_renewal_scan", "projects.licenses", None, f"Created {len(created)} renewal opportunities")
    db.commit()
    return {"created_opportunity_ids": created}


def payroll_approved(db: Session, payroll_run_id: UUID, user: UserResponse | None = None):
    payroll = db.query(HRMPayrollRun).filter(HRMPayrollRun.id == payroll_run_id).first()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    posting = FinancePayrollPosting(
        payroll_run_id=payroll.id,
        posting_number=next_code(db, FinancePayrollPosting, "posting_number", "IS-PAY"),
        total_gross=getattr(payroll, "gross_pay_total", 0) or 0,
        total_deductions=getattr(payroll, "deductions_total", 0) or 0,
        total_net=getattr(payroll, "net_pay_total", 0) or 0,
        status="draft",
    )
    db.add(posting)
    event(db, "hrms", "finance", "payroll.approved", "hrm_payroll_runs", payroll.id, "Created finance payroll posting summary")
    db.commit()
    return {"payroll_posting_id": str(posting.id)}


def account_history(db: Session, account_id: UUID):
    account = db.query(CRMAccount).filter(CRMAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account": {"id": str(account.id), "company_name": account.company_name, "status": account.account_status},
        "opportunities": db.query(CRMOpportunity).filter(CRMOpportunity.account_id == account_id).count(),
        "quotes": db.query(CRMQuotation).join(CRMOpportunity, CRMQuotation.opportunity_id == CRMOpportunity.id).filter(CRMOpportunity.account_id == account_id).count(),
        "lpos": db.query(CRMCustomerLPO).filter(CRMCustomerLPO.account_id == account_id).count(),
        "contracts": db.query(CRMContract).filter(CRMContract.account_id == account_id).count(),
        "invoices": db.query(FinanceInvoice).filter(FinanceInvoice.account_id == account_id).count(),
        "payments": float(db.query(func.coalesce(func.sum(FinanceInvoice.paid_amount), 0)).filter(FinanceInvoice.account_id == account_id).scalar() or 0),
        "projects": db.query(Project).filter(Project.crm_account_id == account_id).count(),
        "slas": db.query(SLA).filter(SLA.account_id == account_id).count(),
        "sla_tickets": db.query(SLATicket).filter(SLATicket.account_id == account_id).count(),
        "licenses": db.query(LicenseTracking).filter(LicenseTracking.account_id == account_id).count(),
        "events": [
            {
                "event_type": row.event_type,
                "source": row.source_module,
                "target": row.target_module,
                "summary": row.payload_summary,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in db.query(FinanceIntegrationEvent)
            .filter(FinanceIntegrationEvent.related_record_id.in_([account_id]))
            .order_by(FinanceIntegrationEvent.created_at.desc())
            .limit(25)
            .all()
        ],
    }


def operational_dashboard(db: Session):
    revenue = db.query(func.coalesce(func.sum(FinanceInvoice.paid_amount), 0)).scalar() or 0
    outstanding = db.query(func.coalesce(func.sum(FinanceInvoice.total_amount - FinanceInvoice.paid_amount), 0)).scalar() or 0
    expenses = db.query(func.coalesce(func.sum(FinanceExpense.amount), 0)).scalar() or 0
    return {
        "crm": {
            "open_opportunities": db.query(CRMOpportunity).filter(CRMOpportunity.status == "open").count(),
            "closed_won": db.query(CRMOpportunity).filter(CRMOpportunity.status == "closed_won").count(),
            "accepted_quotes": db.query(CRMQuotation).filter(CRMQuotation.status == "accepted").count(),
            "lpos": db.query(CRMCustomerLPO).count(),
        },
        "projects": {
            "active": db.query(Project).filter(Project.lifecycle_status.in_(["approved", "planning", "in_progress"])).count(),
            "signed_off": db.query(Project).filter(Project.lifecycle_status == "signed_off").count(),
            "sla_breaches": db.query(SLATicket).filter(SLATicket.sla_status == "breached").count(),
        },
        "finance": {
            "recognized_revenue": float(revenue),
            "outstanding_invoices": float(outstanding),
            "expenses": float(expenses),
            "profitability": float(money(revenue) - money(expenses)),
        },
        "iam_hrms": {
            "active_employees": db.query(HRMEmployee).filter(HRMEmployee.employment_status == "active").count(),
        },
    }


def central_policy_check(user: UserResponse, module: str, action: str, record_owner: str | None = None) -> dict[str, Any]:
    role = str(getattr(user, "role", "user") or "user").lower()
    email = getattr(user, "email", None)
    elevated = {"admin", "manager", "hr_admin", "finance_admin", "payroll_admin", "cfo"}
    module_roles = {
        "crm": {"admin", "manager", "user", "finance_admin", "cfo"},
        "hrms": {"admin", "hr", "hr_admin", "hr_manager", "payroll", "payroll_admin"},
        "projects": {"admin", "manager", "hr", "hr_admin", "hr_manager"},
        "finance": {"admin", "finance_admin", "accountant", "cfo", "payroll", "payroll_admin"},
        "iam": {"admin"},
    }
    sensitive_actions = {"approve", "reject", "lock", "unlock", "post", "mark-paid", "assign-role", "revoke-role", "payment"}
    allowed = role in module_roles.get(module, set()) or role in elevated
    if action in sensitive_actions and role not in elevated and role not in module_roles.get(module, set()):
        allowed = False
    if record_owner and email and record_owner == email and action in {"approve", "reject", "post", "mark-paid"}:
        allowed = False
    return {
        "allowed": allowed,
        "module": module,
        "action": action,
        "role": role,
        "reason": "allowed by Phase 1 centralized policy" if allowed else "blocked by Phase 1 centralized policy",
    }
