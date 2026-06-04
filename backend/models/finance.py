import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from backend.core.database import Base


class FinanceChartAccount(Base):
    __tablename__ = "chart_accounts"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_code = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    currency = Column(String(20), default="KES")
    reporting_category = Column(String(120), nullable=True)
    normal_balance = Column(String(20), nullable=False)
    accounting_basis = Column(String(50), default="accrual")
    is_system_account = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceJournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_number = Column(String(100), unique=True, nullable=False)
    entry_date = Column(Date, nullable=False)
    fiscal_period = Column(String(50), nullable=True)
    source_module = Column(String(100), nullable=True)
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    total_debit = Column(Numeric(14, 2), default=0)
    total_credit = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="draft")
    posted_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    reversed_entry_id = Column(UUID(as_uuid=True), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    journal_type = Column(String(80), default="manual")
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceJournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=False)
    line_description = Column(Text, nullable=True)
    debit_amount = Column(Numeric(14, 2), default=0)
    credit_amount = Column(Numeric(14, 2), default=0)
    department = Column(String(150), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceGLMappingRule(Base):
    __tablename__ = "gl_mapping_rules"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_module = Column(String(120), nullable=False, index=True)
    transaction_type = Column(String(120), nullable=False, index=True)
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=False)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=False)
    accounting_basis = Column(String(50), default="accrual")
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceVendor(Base):
    __tablename__ = "vendors"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_code = Column(String(100), unique=True, nullable=True, index=True)
    vendor_name = Column(String(255), nullable=False)
    vendor_type = Column(String(100), nullable=True)
    tax_pin = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    bank_details = Column(Text, nullable=True)
    payment_terms = Column(String(100), nullable=True)
    onboarding_status = Column(String(50), default="draft")
    verification_status = Column(String(50), default="pending")
    risk_profile = Column(String(80), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceBill(Base):
    __tablename__ = "bills"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("finance.purchase_orders.id"), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("finance.documents.id"), nullable=True)
    bill_number = Column(String(100), unique=True, nullable=False)
    bill_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    paid_amount = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    currency = Column(String(20), default="KES")
    invoice_quantity = Column(Numeric(14, 2), default=0)
    po_match_status = Column(String(50), default="pending")
    grn_match_status = Column(String(50), default="pending")
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    approval_status = Column(String(50), default="draft")
    department = Column(String(150), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinancePayment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_number = Column(String(100), unique=True, nullable=False)
    payment_type = Column(String(50), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("finance.bills.id"), nullable=True)
    payment_date = Column(Date, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    payment_method = Column(String(100), nullable=True)
    bank_account_id = Column(UUID(as_uuid=True), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    reversed_payment_id = Column(UUID(as_uuid=True), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    approved_by = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceInvoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(String(80), unique=True, nullable=True, index=True)
    crm_invoice_id = Column(UUID(as_uuid=True), nullable=True)
    crm_opportunity_id = Column(UUID(as_uuid=True), nullable=True)
    quotation_id = Column(UUID(as_uuid=True), nullable=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    deal_id = Column(UUID(as_uuid=True), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    source_module = Column(String(120), nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)
    customer_code = Column(String(100), nullable=True, index=True)
    ar_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    revenue_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    delivery_method = Column(String(80), nullable=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    paid_amount = Column(Numeric(14, 2), default=0)
    tax_country = Column(String(100), default="Kenya")
    tax_region = Column(String(100), nullable=True)
    tax_rate = Column(Numeric(5, 2), default=16)
    recurring = Column(Boolean, default=False)
    approval_status = Column(String(50), default="draft")
    status = Column(String(50), default="draft")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceReceipt(Base):
    __tablename__ = "receipts"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_number = Column(String(100), unique=True, nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    receipt_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    allocated_amount = Column(Numeric(14, 2), default=0)
    currency = Column(String(20), default="KES")
    payment_method = Column(String(100), nullable=True)
    payment_reference = Column(String(150), nullable=True)
    received_from = Column(String(255), nullable=True)
    bank_account_id = Column(UUID(as_uuid=True), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    status = Column(String(50), default="received")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCreditNote(Base):
    __tablename__ = "credit_notes"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_note_number = Column(String(100), unique=True, nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=True)
    issue_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceExpenseClaim(Base):
    __tablename__ = "expense_claims"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number = Column(String(100), unique=True, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    employee_name = Column(String(255), nullable=True)
    expense_category = Column(String(100), nullable=False)
    expense_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    receipt_url = Column(String(500), nullable=True)
    department = Column(String(150), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    distance = Column(Numeric(12, 2), default=0)
    mileage_rate = Column(Numeric(12, 2), default=0)
    per_diem_days = Column(Numeric(12, 2), default=0)
    per_diem_rate = Column(Numeric(12, 2), default=0)
    approval_status = Column(String(50), default="submitted")
    reimbursement_status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceBudget(Base):
    __tablename__ = "budgets"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_name = Column(String(255), nullable=False)
    budget_type = Column(String(100), nullable=False)
    department = Column(String(150), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    fiscal_year = Column(String(20), nullable=False)
    period_label = Column(String(50), nullable=True)
    approved_amount = Column(Numeric(14, 2), default=0)
    committed_amount = Column(Numeric(14, 2), default=0)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    branch = Column(String(150), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=True)
    actual_amount = Column(Numeric(14, 2), default=0)
    threshold_percent = Column(Numeric(5, 2), default=100)
    approval_status = Column(String(50), default="draft")
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinancePurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number = Column(String(100), unique=True, nullable=False)
    requested_by = Column(String(255), nullable=True)
    department = Column(String(150), nullable=True)
    request_date = Column(Date, nullable=False)
    required_date = Column(Date, nullable=True)
    description = Column(Text, nullable=False)
    estimated_amount = Column(Numeric(14, 2), default=0)
    approval_status = Column(String(50), default="submitted")
    status = Column(String(50), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinancePurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), unique=True, nullable=False)
    purchase_request_id = Column(UUID(as_uuid=True), ForeignKey("finance.purchase_requests.id"), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=True)
    po_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(14, 2), default=0)
    received_quantity = Column(Numeric(14, 2), default=0)
    approval_status = Column(String(50), default="draft")
    goods_received_status = Column(String(50), default="pending")
    service_acceptance_status = Column(String(50), default="pending")
    invoice_match_status = Column(String(50), default="pending")
    bill_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="open")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceRFQ(Base):
    __tablename__ = "rfqs"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_number = Column(String(100), unique=True, nullable=False, index=True)
    purchase_request_id = Column(UUID(as_uuid=True), ForeignKey("finance.purchase_requests.id"), nullable=True)
    vendor_list = Column(Text, nullable=True)
    requested_items = Column(Text, nullable=True)
    closing_date = Column(Date, nullable=False)
    status = Column(String(50), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceVendorEvaluation(Base):
    __tablename__ = "vendor_evaluations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("finance.rfqs.id"), nullable=True, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=False, index=True)
    price_score = Column(Numeric(8, 2), default=0)
    quality_score = Column(Numeric(8, 2), default=0)
    delivery_score = Column(Numeric(8, 2), default=0)
    compliance_score = Column(Numeric(8, 2), default=0)
    risk_score = Column(Numeric(8, 2), default=0)
    weighted_score = Column(Numeric(8, 2), default=0)
    selected = Column(Boolean, default=False)
    selection_reason = Column(Text, nullable=True)
    status = Column(String(50), default="evaluated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceGoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grn_number = Column(String(100), unique=True, nullable=False, index=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("finance.purchase_orders.id"), nullable=False, index=True)
    received_quantity = Column(Numeric(14, 2), default=0)
    unit_cost = Column(Numeric(14, 2), default=0)
    received_value = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="received")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceRecurringJournal(Base):
    __tablename__ = "recurring_journals"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    frequency = Column(String(50), nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=False)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=False)
    next_run_date = Column(Date, nullable=True)
    last_generated_journal_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    approval_required = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceVendorOnboarding(Base):
    __tablename__ = "vendor_onboarding"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=False, index=True)
    required_documents = Column(Text, nullable=True)
    submitted_documents = Column(Text, nullable=True)
    compliance_status = Column(String(50), default="pending")
    risk_profile = Column(String(80), nullable=True)
    status = Column(String(50), default="incomplete")
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceVendorVerification(Base):
    __tablename__ = "vendor_verifications"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=False, index=True)
    tax_status = Column(String(50), default="pending")
    sanctions_status = Column(String(50), default="pending")
    blacklist_status = Column(String(50), default="pending")
    document_status = Column(String(50), default="pending")
    result = Column(String(50), default="pending")
    next_review_date = Column(Date, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceAPReconciliation(Base):
    __tablename__ = "ap_reconciliations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=False, index=True)
    statement_balance = Column(Numeric(14, 2), default=0)
    system_balance = Column(Numeric(14, 2), default=0)
    variance_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="draft")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBankAccount(Base):
    __tablename__ = "bank_accounts"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=True)
    account_number = Column(String(100), nullable=True)
    account_type = Column(String(100), nullable=True)
    currency = Column(String(20), default="KES")
    opening_balance = Column(Numeric(14, 2), default=0)
    current_balance = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.bank_accounts.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    reference_number = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    reconciled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBankReconciliation(Base):
    __tablename__ = "bank_reconciliations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.bank_accounts.id"), nullable=False, index=True)
    book_balance = Column(Numeric(14, 2), default=0)
    deposits_in_transit = Column(Numeric(14, 2), default=0)
    outstanding_cheques = Column(Numeric(14, 2), default=0)
    bank_statement_balance = Column(Numeric(14, 2), default=0)
    bank_errors = Column(Numeric(14, 2), default=0)
    outstanding_items = Column(Numeric(14, 2), default=0)
    difference = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceTaxRecord(Base):
    __tablename__ = "tax_records"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_type = Column(String(100), nullable=False)
    tax_period = Column(String(100), nullable=False)
    taxable_amount = Column(Numeric(14, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    due_date = Column(Date, nullable=True)
    filing_status = Column(String(50), default="pending")
    filed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceFixedAsset(Base):
    __tablename__ = "fixed_assets"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_code = Column(String(100), unique=True, nullable=False)
    asset_name = Column(String(255), nullable=False)
    asset_category = Column(String(100), nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Numeric(14, 2), default=0)
    depreciation_method = Column(String(100), nullable=True)
    accumulated_depreciation = Column(Numeric(14, 2), default=0)
    location = Column(String(255), nullable=True)
    custodian = Column(String(255), nullable=True)
    disposal_date = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    maintenance_cost = Column(Numeric(14, 2), default=0)
    residual_value = Column(Numeric(14, 2), default=0)
    useful_life_years = Column(Numeric(8, 2), default=0)
    current_book_value = Column(Numeric(14, 2), default=0)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    source_purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("finance.purchase_orders.id"), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceAssetMovement(Base):
    __tablename__ = "asset_movements"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("finance.fixed_assets.id"), nullable=False, index=True)
    movement_type = Column(String(80), nullable=False)
    from_location = Column(String(255), nullable=True)
    to_location = Column(String(255), nullable=True)
    from_custodian = Column(String(255), nullable=True)
    to_custodian = Column(String(255), nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    reason = Column(Text, nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceProjectFinance(Base):
    __tablename__ = "project_finance"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    project_name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=True)
    budget_amount = Column(Numeric(14, 2), default=0)
    revenue_amount = Column(Numeric(14, 2), default=0)
    expense_amount = Column(Numeric(14, 2), default=0)
    milestone_billing = Column(Text, nullable=True)
    profitability = Column(Numeric(14, 2), default=0)
    overrun_amount = Column(Numeric(14, 2), default=0)
    forecast_revenue = Column(Numeric(14, 2), default=0)
    forecast_cost = Column(Numeric(14, 2), default=0)
    cost_centers = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceRevenueRecord(Base):
    __tablename__ = "revenue_records"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revenue_source = Column(String(150), nullable=False)
    customer_name = Column(String(255), nullable=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    deal_id = Column(UUID(as_uuid=True), nullable=True)
    invoice_id = Column(UUID(as_uuid=True), nullable=True)
    source_module = Column(String(120), nullable=True, index=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    revenue_type = Column(String(100), nullable=False)
    recognition_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="recognized")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceApproval(Base):
    __tablename__ = "approvals"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_type = Column(String(100), nullable=False)
    related_record_type = Column(String(100), nullable=False)
    related_record_id = Column(UUID(as_uuid=True), nullable=True)
    requested_by = Column(String(255), nullable=True)
    approver = Column(String(255), nullable=True)
    approval_level = Column(Integer, default=1)
    status = Column(String(50), default="pending")
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceApprovalMatrix(Base):
    __tablename__ = "approval_matrices"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matrix_name = Column(String(255), nullable=False)
    module = Column(String(100), nullable=False, index=True)
    transaction_type = Column(String(100), nullable=False, index=True)
    min_amount = Column(Numeric(14, 2), default=0)
    max_amount = Column(Numeric(14, 2), nullable=True)
    approval_levels = Column(Text, nullable=False)
    effective_date = Column(Date, nullable=False)
    version_number = Column(Integer, default=1)
    status = Column(String(50), default="active")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceApprovalDelegation(Base):
    __tablename__ = "approval_delegations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delegator_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    delegate_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=False)
    module = Column(String(100), nullable=True)
    transaction_type = Column(String(100), nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceApprovalHistory(Base):
    __tablename__ = "approval_history"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("finance.approvals.id"), nullable=True)
    source_module = Column(String(100), nullable=True, index=True)
    source_record_type = Column(String(100), nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)
    requestor = Column(String(255), nullable=True)
    approver = Column(String(255), nullable=True)
    decision = Column(String(80), nullable=False)
    comments = Column(Text, nullable=True)
    delegation_id = Column(UUID(as_uuid=True), ForeignKey("finance.approval_delegations.id"), nullable=True)
    escalation_level = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceAuditTrail(Base):
    __tablename__ = "audit_trails"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(255), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceDocument(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_title = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)
    related_record_type = Column(String(100), nullable=True)
    related_record_id = Column(UUID(as_uuid=True), nullable=True)
    document_number = Column(String(150), nullable=True, index=True)
    party_name = Column(String(255), nullable=True)
    amount = Column(Numeric(14, 2), default=0)
    currency = Column(String(20), default="KES")
    document_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_hash = Column(String(255), nullable=True, index=True)
    ocr_text = Column(Text, nullable=True)
    change_comments = Column(Text, nullable=True)
    version_number = Column(Integer, default=1)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archive_reason = Column(Text, nullable=True)
    retention_until = Column(Date, nullable=True)
    retention_policy = Column(String(100), nullable=True)
    legal_hold = Column(Boolean, default=False)
    confidentiality_level = Column(String(50), default="finance")
    status = Column(String(50), default="active")
    uploaded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceDocumentRetentionRule(Base):
    __tablename__ = "document_retention_rules"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type = Column(String(100), nullable=False, unique=True)
    retention_years = Column(Integer, nullable=False)
    legal_hold = Column(Boolean, default=False)
    auto_archive = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceDeferredRevenueSchedule(Base):
    __tablename__ = "deferred_revenue_schedules"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    project_finance_id = Column(UUID(as_uuid=True), ForeignKey("finance.project_finance.id"), nullable=True)
    schedule_period = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    recognition_status = Column(String(50), default="deferred")
    renewal_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceIntegrationEvent(Base):
    __tablename__ = "integration_events"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_module = Column(String(100), nullable=False)
    target_module = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    related_record_type = Column(String(100), nullable=True)
    related_record_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="pending")
    payload_summary = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceAccountCategory(Base):
    __tablename__ = "account_categories"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_code = Column(String(80), unique=True, nullable=False, index=True)
    category_name = Column(String(255), nullable=False)
    normal_balance = Column(String(20), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCostCenter(Base):
    __tablename__ = "cost_centers"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_code = Column(String(80), unique=True, nullable=False, index=True)
    cost_center_name = Column(String(255), nullable=False)
    department = Column(String(150), nullable=True, index=True)
    branch = Column(String(150), nullable=True, index=True)
    owner_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    manager_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True)
    status = Column(String(50), default="active")
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceCostCenterAssignment(Base):
    __tablename__ = "cost_center_assignments"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    source_record_type = Column(String(120), nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    allocation_percent = Column(Numeric(6, 2), default=100)
    status = Column(String(50), default="active")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCostCenterAllocation(Base):
    __tablename__ = "cost_center_allocations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=False, index=True)
    source_record_type = Column(String(120), nullable=False)
    source_record_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    allocation_percent = Column(Numeric(6, 2), nullable=False)
    allocation_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="posted")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBudgetLine(Base):
    __tablename__ = "budget_lines"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("finance.budgets.id"), nullable=False, index=True)
    line_name = Column(String(255), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=True)
    planned_amount = Column(Numeric(14, 2), default=0)
    actual_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBudgetApproval(Base):
    __tablename__ = "budget_approvals"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("finance.budgets.id"), nullable=False, index=True)
    approver = Column(String(255), nullable=True)
    approval_level = Column(Integer, default=1)
    status = Column(String(50), default="pending")
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCustomerBillingProfile(Base):
    __tablename__ = "customer_billing_profiles"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=False, index=True)
    customer_code = Column(String(100), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    billing_address = Column(Text, nullable=True)
    tax_registration_number = Column(String(120), nullable=True)
    currency = Column(String(20), default="KES")
    payment_terms = Column(String(100), nullable=False)
    credit_limit = Column(Numeric(14, 2), default=0)
    ar_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    revenue_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceReceiptAllocation(Base):
    __tablename__ = "receipt_allocations"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("finance.receipts.id"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=False, index=True)
    allocated_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="allocated")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCollectionAction(Base):
    __tablename__ = "collection_actions"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    aging_bucket = Column(String(50), nullable=True)
    action_type = Column(String(80), default="reminder")
    assigned_to = Column(String(255), nullable=True)
    status = Column(String(50), default="open")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceBudgetRevision(Base):
    __tablename__ = "budget_revisions"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(UUID(as_uuid=True), ForeignKey("finance.budgets.id"), nullable=False, index=True)
    old_amount = Column(Numeric(14, 2), default=0)
    new_amount = Column(Numeric(14, 2), default=0)
    reason = Column(Text, nullable=False)
    approval_status = Column(String(50), default="pending")
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceExpenseCategory(Base):
    __tablename__ = "expense_categories"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_name = Column(String(255), unique=True, nullable=False)
    default_account_id = Column(UUID(as_uuid=True), ForeignKey("finance.chart_accounts.id"), nullable=True)
    requires_receipt = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceExpense(Base):
    __tablename__ = "expenses"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_number = Column(String(100), unique=True, nullable=True, index=True)
    expense_date = Column(Date, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("finance.expense_categories.id"), nullable=True)
    category = Column(String(150), nullable=True)
    claimant_employee_id = Column(UUID(as_uuid=True), ForeignKey("hrm_employees.id"), nullable=True, index=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("finance.cost_centers.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    financial_period_id = Column(UUID(as_uuid=True), ForeignKey("finance.financial_periods.id"), nullable=True)
    source_module = Column(String(120), nullable=True, index=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_label = Column(String(255), nullable=True)
    department = Column(String(150), nullable=True, index=True)
    amount = Column(Numeric(14, 2), default=0)
    currency = Column(String(20), default="KES")
    approval_status = Column(String(50), default="draft")
    payment_status = Column(String(50), default="unpaid")
    status = Column(String(50), default="draft")
    notes = Column(Text, nullable=True)
    soft_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FinanceInvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=False, index=True)
    product_service_id = Column(UUID(as_uuid=True), ForeignKey("crm.product_services.id"), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(14, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceDebitNote(Base):
    __tablename__ = "debit_notes"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debit_note_number = Column(String(100), unique=True, nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("finance.vendors.id"), nullable=True)
    note_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceTaxRule(Base):
    __tablename__ = "tax_rules"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tax_name = Column(String(255), nullable=False)
    country = Column(String(120), nullable=False, index=True)
    region = Column(String(120), nullable=True)
    tax_type = Column(String(100), nullable=False)
    rate = Column(Numeric(6, 3), default=0)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceCurrency(Base):
    __tablename__ = "currencies"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    currency_code = Column(String(10), unique=True, nullable=False, index=True)
    currency_name = Column(String(120), nullable=False)
    symbol = Column(String(20), nullable=True)
    is_base_currency = Column(Boolean, default=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_currency = Column(String(10), nullable=False, index=True)
    to_currency = Column(String(10), nullable=False, index=True)
    rate = Column(Numeric(18, 6), nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    source = Column(String(120), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceFinancialPeriod(Base):
    __tablename__ = "financial_periods"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_name = Column(String(120), unique=True, nullable=False, index=True)
    fiscal_year = Column(String(20), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), default="open", index=True)
    closed_by = Column(String(255), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinancePayrollPosting(Base):
    __tablename__ = "payroll_postings"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("hrm_payroll_runs.id"), nullable=True, index=True)
    financial_period_id = Column(UUID(as_uuid=True), ForeignKey("finance.financial_periods.id"), nullable=True)
    posting_number = Column(String(120), unique=True, nullable=True)
    total_gross = Column(Numeric(14, 2), default=0)
    total_deductions = Column(Numeric(14, 2), default=0)
    total_net = Column(Numeric(14, 2), default=0)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("finance.journal_entries.id"), nullable=True)
    status = Column(String(50), default="draft")
    posted_by = Column(String(255), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceProjectFinancialRecord(Base):
    __tablename__ = "project_financial_records"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    financial_period_id = Column(UUID(as_uuid=True), ForeignKey("finance.financial_periods.id"), nullable=True)
    budget_amount = Column(Numeric(14, 2), default=0)
    actual_cost = Column(Numeric(14, 2), default=0)
    invoiced_amount = Column(Numeric(14, 2), default=0)
    recognized_revenue = Column(Numeric(14, 2), default=0)
    profitability_amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="open")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FinanceRevenueRecognitionRecord(Base):
    __tablename__ = "revenue_recognition_records"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("crm.accounts.id"), nullable=True)
    recognition_method = Column(String(120), default="point_in_time")
    recognition_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), default=0)
    status = Column(String(50), default="recognized")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
