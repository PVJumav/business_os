from datetime import datetime
from io import BytesIO
from textwrap import wrap

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.crm import CRMAccount, CRMDeal, CRMInvoice, CRMOpportunity, CRMPMOProject, CRMSLAAssignment, CRMTender, CRMTicket
from backend.models.finance import FinanceBankAccount, FinanceBill, FinanceBudget, FinanceExpenseClaim, FinanceInvoice, FinanceRevenueRecord
from backend.models.hrm import HRMAttendance, HRMDepartment, HRMEmployee, HRMLeave, HRMPayroll, HRMPerformance, HRMRecruitment


router = APIRouter(prefix="/reports", tags=["Reports"])


REPORTS = {
    "ceo": "CEO Executive Report",
    "finance": "Finance Report",
    "sales": "Sales Report",
    "hr": "HR Report",
    "sla": "SLA Report",
    "projects": "Project Report",
}


def count(db: Session, model, *criteria):
    query = db.query(func.count(model.id))
    if criteria:
        query = query.filter(*criteria)
    return int(query.scalar() or 0)


def total(db: Session, model, column_name: str, *criteria):
    query = db.query(func.coalesce(func.sum(getattr(model, column_name)), 0))
    if criteria:
        query = query.filter(*criteria)
    return float(query.scalar() or 0)


def money(value: float):
    return f"{value:,.2f}"


def pdf_escape(text: str):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(title: str, sections: list[tuple[str, list[str]]]):
    lines = [title, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for heading, items in sections:
        lines.append(heading)
        lines.extend([f"- {item}" for item in items])
        lines.append("")

    wrapped_lines: list[tuple[str, bool]] = []
    for line in lines:
        is_heading = bool(line and not line.startswith("-") and line != title and not line.startswith("Generated:"))
        if not line:
            wrapped_lines.append(("", False))
            continue
        for chunk in wrap(line, width=92) or [""]:
            wrapped_lines.append((chunk, is_heading))

    pages = [wrapped_lines[index : index + 44] for index in range(0, len(wrapped_lines), 44)] or [[("", False)]]
    objects: list[str] = []
    pages_refs = []

    def add_object(content: str):
        objects.append(content)
        return len(objects)

    font_regular = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    for page in pages:
        commands = ["BT", "/F2 18 Tf", "50 790 Td", f"({pdf_escape(title)}) Tj"]
        y_started = True
        for index, (line, is_heading) in enumerate(page):
            if index == 0 and line == title:
                continue
            size = 12 if not is_heading else 14
            font = "F2" if is_heading else "F1"
            leading = 17 if not is_heading else 20
            commands.append(f"/{font} {size} Tf")
            commands.append(f"0 -{leading} Td" if y_started else "50 760 Td")
            commands.append(f"({pdf_escape(line)}) Tj")
            y_started = True
        commands.append("ET")
        stream = "\n".join(commands)
        content_ref = add_object(f"<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream")
        page_ref = add_object(
            f"<< /Type /Page /Parent PAGES_PLACEHOLDER 0 R /MediaBox [0 0 612 842] "
            f"/Resources << /Font << /F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> /Contents {content_ref} 0 R >>"
        )
        pages_refs.append(page_ref)

    pages_ref = add_object(
        f"<< /Type /Pages /Kids [{' '.join(f'{ref} 0 R' for ref in pages_refs)}] /Count {len(pages_refs)} >>"
    )
    catalog_ref = add_object(f"<< /Type /Catalog /Pages {pages_ref} 0 R >>")
    objects = [obj.replace("PAGES_PLACEHOLDER", str(pages_ref)) for obj in objects]

    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{idx} 0 obj\n{obj}\nendobj\n".encode("utf-8"))
    xref_start = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("utf-8"))
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("utf-8"))
    output.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_ref} 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("utf-8")
    )
    return output.getvalue()


def report_sections(report_type: str, db: Session):
    if report_type == "ceo":
        finance_revenue = total(db, FinanceRevenueRecord, "amount") + total(db, FinanceInvoice, "total_amount")
        finance_expenses = total(db, FinanceBill, "amount") + total(db, FinanceExpenseClaim, "amount") + total(db, HRMPayroll, "net_pay")
        return [
            ("Executive Summary", [
                f"Total accounts: {count(db, CRMAccount)}",
                f"Active employees: {count(db, HRMEmployee, HRMEmployee.employment_status == 'active')}",
                f"Open opportunities: {count(db, CRMOpportunity)}",
                f"Open projects: {count(db, CRMPMOProject, CRMPMOProject.status != 'completed')}",
                f"Active SLAs: {count(db, CRMSLAAssignment, CRMSLAAssignment.status == 'active')}",
            ]),
            ("Financial Position", [
                f"Revenue: {money(finance_revenue)}",
                f"Expenses: {money(finance_expenses)}",
                f"Profit/Loss: {money(finance_revenue - finance_expenses)}",
                f"Cash position: {money(total(db, FinanceBankAccount, 'current_balance'))}",
                f"Outstanding customer invoices: {money(total(db, FinanceInvoice, 'total_amount') - total(db, FinanceInvoice, 'paid_amount'))}",
            ]),
            ("Operational Risks", [
                f"Open tickets: {count(db, CRMTicket, CRMTicket.status.in_(['open', 'in_progress']))}",
                f"Pending tenders: {count(db, CRMTender, CRMTender.outcome == 'pending')}",
                f"Pending leave requests: {count(db, HRMLeave, HRMLeave.status == 'pending')}",
            ]),
        ]
    if report_type == "finance":
        return [
            ("Finance Overview", [
                f"Finance invoices: {count(db, FinanceInvoice)}",
                f"Invoice value: {money(total(db, FinanceInvoice, 'total_amount'))}",
                f"Paid amount: {money(total(db, FinanceInvoice, 'paid_amount'))}",
                f"Outstanding invoices: {money(total(db, FinanceInvoice, 'total_amount') - total(db, FinanceInvoice, 'paid_amount'))}",
                f"Vendor bills: {money(total(db, FinanceBill, 'amount'))}",
                f"Expense claims: {money(total(db, FinanceExpenseClaim, 'amount'))}",
                f"Bank/cash balance: {money(total(db, FinanceBankAccount, 'current_balance'))}",
            ]),
            ("Budgets", [
                f"Budgets created: {count(db, FinanceBudget)}",
                f"Approved budget: {money(total(db, FinanceBudget, 'approved_amount'))}",
                f"Actual spend: {money(total(db, FinanceBudget, 'actual_amount'))}",
            ]),
        ]
    if report_type == "sales":
        return [
            ("Sales Pipeline", [
                f"Accounts: {count(db, CRMAccount)}",
                f"Opportunities: {count(db, CRMOpportunity)}",
                f"Pipeline value: {money(total(db, CRMOpportunity, 'opportunity_value'))}",
                f"Gross profit pipeline: {money(total(db, CRMOpportunity, 'gross_profit'))}",
                f"Won deals: {count(db, CRMDeal, CRMDeal.deal_status == 'closed_won')}",
                f"Won deal revenue: {money(total(db, CRMDeal, 'revenue_amount', CRMDeal.deal_status == 'closed_won'))}",
            ]),
            ("Customer Collections", [
                f"CRM invoice value: {money(total(db, CRMInvoice, 'amount'))}",
                f"CRM paid amount: {money(total(db, CRMInvoice, 'paid_amount'))}",
            ]),
        ]
    if report_type == "hr":
        return [
            ("People Overview", [
                f"Employees: {count(db, HRMEmployee)}",
                f"Active employees: {count(db, HRMEmployee, HRMEmployee.employment_status == 'active')}",
                f"Departments: {count(db, HRMDepartment)}",
                f"Recruitment records: {count(db, HRMRecruitment)}",
                f"Performance reviews: {count(db, HRMPerformance)}",
            ]),
            ("HR Operations", [
                f"Pending leave: {count(db, HRMLeave, HRMLeave.status == 'pending')}",
                f"Attendance records: {count(db, HRMAttendance)}",
                f"Payroll cost: {money(total(db, HRMPayroll, 'net_pay'))}",
            ]),
        ]
    if report_type == "sla":
        return [
            ("SLA Overview", [
                f"Total SLAs: {count(db, CRMSLAAssignment)}",
                f"Active SLAs: {count(db, CRMSLAAssignment, CRMSLAAssignment.status == 'active')}",
                f"Completed SLAs: {count(db, CRMSLAAssignment, CRMSLAAssignment.status == 'completed')}",
                f"Open tickets: {count(db, CRMTicket, CRMTicket.status.in_(['open', 'in_progress']))}",
                f"Resolved tickets: {count(db, CRMTicket, CRMTicket.status == 'resolved')}",
            ]),
        ]
    if report_type == "projects":
        return [
            ("Project Delivery", [
                f"Projects: {count(db, CRMPMOProject)}",
                f"Active projects: {count(db, CRMPMOProject, CRMPMOProject.status == 'active')}",
                f"Completed projects: {count(db, CRMPMOProject, CRMPMOProject.status == 'completed')}",
                f"Project finance revenue: {money(total(db, FinanceRevenueRecord, 'amount'))}",
            ]),
            ("Delivery Workload", [
                f"Active SLAs: {count(db, CRMSLAAssignment, CRMSLAAssignment.status == 'active')}",
                f"Open tickets: {count(db, CRMTicket, CRMTicket.status.in_(['open', 'in_progress']))}",
            ]),
        ]
    raise HTTPException(status_code=404, detail="Report type not found")


def filter_sections(sections: list[tuple[str, list[str]]], include: str | None):
    if not include:
        return sections
    wanted = {item.strip().lower() for item in include.split(",") if item.strip()}
    return [(heading, items) for heading, items in sections if heading.lower() in wanted] or sections


def sections_html(title: str, sections: list[tuple[str, list[str]]]):
    section_html = "\n".join(
        f"<section><h2>{heading}</h2><ul>{''.join(f'<li>{item}</li>' for item in items)}</ul></section>"
        for heading, items in sections
    )
    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>{title}</title>
        <style>
          body {{ font-family: Arial, sans-serif; color: #0f172a; margin: 40px; }}
          h1 {{ margin-bottom: 4px; }}
          .meta {{ color: #64748b; margin-bottom: 28px; }}
          section {{ border-top: 1px solid #e2e8f0; padding-top: 18px; margin-top: 18px; }}
          h2 {{ font-size: 18px; }}
          li {{ margin: 8px 0; }}
        </style>
      </head>
      <body>
        <h1>{title}</h1>
        <p class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        {section_html}
      </body>
    </html>
    """


@router.get("")
def list_reports():
    return [{"key": key, "title": title, "download_url": f"/api/reports/{key}.pdf"} for key, title in REPORTS.items()]


@router.get("/summary")
def reports_summary(db: Session = Depends(get_db)):
    finance_revenue = total(db, FinanceRevenueRecord, "amount") + total(db, FinanceInvoice, "total_amount")
    finance_expenses = total(db, FinanceBill, "amount") + total(db, FinanceExpenseClaim, "amount") + total(db, HRMPayroll, "net_pay")
    open_tickets = count(db, CRMTicket, CRMTicket.status.in_(["open", "in_progress", "assigned", "escalated"]))
    active_projects = count(db, CRMPMOProject, CRMPMOProject.status.in_(["active", "in_progress", "planning"]))
    active_employees = count(db, HRMEmployee, HRMEmployee.employment_status == "active")
    return {
        "generated_at": datetime.now().isoformat(),
        "available_reports": len(REPORTS),
        "executive": {
            "accounts": count(db, CRMAccount),
            "active_employees": active_employees,
            "open_opportunities": count(db, CRMOpportunity, CRMOpportunity.status == "open"),
            "active_projects": active_projects,
            "open_tickets": open_tickets,
        },
        "finance": {
            "revenue": finance_revenue,
            "expenses": finance_expenses,
            "profit_loss": finance_revenue - finance_expenses,
            "outstanding_invoices": total(db, FinanceInvoice, "total_amount") - total(db, FinanceInvoice, "paid_amount"),
        },
        "operations": {
            "sla_health": "attention" if open_tickets else "healthy",
            "project_load": active_projects,
            "pending_leave": count(db, HRMLeave, HRMLeave.status == "pending"),
        },
    }


@router.get("/{report_type}.pdf")
def download_report(report_type: str, include: str | None = None, db: Session = Depends(get_db)):
    title = REPORTS.get(report_type)
    if not title:
        raise HTTPException(status_code=404, detail="Report type not found")
    pdf = build_pdf(title, filter_sections(report_sections(report_type, db), include))
    filename = f"business-os-{report_type}-report-{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_type}/preview", response_class=HTMLResponse)
def preview_report(report_type: str, include: str | None = None, db: Session = Depends(get_db)):
    title = REPORTS.get(report_type)
    if not title:
        raise HTTPException(status_code=404, detail="Report type not found")
    return HTMLResponse(sections_html(title, filter_sections(report_sections(report_type, db), include)))


@router.get("/{report_type}/sections")
def report_section_options(report_type: str, db: Session = Depends(get_db)):
    title = REPORTS.get(report_type)
    if not title:
        raise HTTPException(status_code=404, detail="Report type not found")
    sections = report_sections(report_type, db)
    return {"title": title, "sections": [{"heading": heading, "items": items} for heading, items in sections]}
