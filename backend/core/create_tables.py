import json
import uuid

from sqlalchemy import text

from backend.core.crm_policy import CRM_DEPARTMENT_HEADS, DEPARTMENT_RESPONSIBILITIES
from backend.core.database import Base, engine
from backend.core.init_db import create_schemas

# Import models so SQLAlchemy registers them
from backend.models import auth, automation, config, crm, enterprise, finance, hrm, iam, projects  # noqa: F401
from backend.services.automation_enterprise import seed_defaults


def create_tables():
    create_schemas()
    Base.metadata.create_all(bind=engine)
    with engine.connect() as connection:
        connection.execute(text("ALTER TABLE IF EXISTS crm.activities ADD COLUMN IF NOT EXISTS account_name VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.activities ADD COLUMN IF NOT EXISTS due_date TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.activities ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.activities ALTER COLUMN related_id DROP NOT NULL"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ALTER COLUMN account_id DROP NOT NULL"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS account_manager VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS parent_account_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS billing_address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS shipping_address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS country VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS region VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS vertical VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS account_type VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS manager_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS created_by_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS created_by_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS country VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS actual_close_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS win_loss_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS competitors TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS product_service_ids JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'not_required'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS vertical VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS pipeline_type VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS arena VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS distributor_cost NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS vendor_cost NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS internal_cost NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS gross_profit NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS presales_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS project_manager_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS manager_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS created_by_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS lpo_document_url VARCHAR(500)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS handover_status VARCHAR(80) DEFAULT 'not_started'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS customer_success_owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS technical_owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS renewal_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS licence_expiry_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS renewal_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS licence_expiry_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS tax_country VARCHAR(100) DEFAULT 'Kenya'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS tax_region VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS tax_rate NUMERIC(5, 2) DEFAULT 16"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS crm_opportunity_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS quotation_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS source_module VARCHAR(120)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS source_record_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS customer_code VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS ar_account_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS revenue_account_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS delivery_method VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS account_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS allocated_amount NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS currency VARCHAR(20) DEFAULT 'KES'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.receipts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'received'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.credit_notes ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.debit_notes ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.budgets ADD COLUMN IF NOT EXISTS committed_amount NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.budgets ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.budgets ADD COLUMN IF NOT EXISTS branch VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.budgets ADD COLUMN IF NOT EXISTS cost_center_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.journal_entries ADD COLUMN IF NOT EXISTS rejection_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.journal_entries ADD COLUMN IF NOT EXISTS reversed_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.journal_entries ADD COLUMN IF NOT EXISTS reversal_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.journal_entries ADD COLUMN IF NOT EXISTS journal_type VARCHAR(80) DEFAULT 'manual'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.chart_accounts ADD COLUMN IF NOT EXISTS currency VARCHAR(20) DEFAULT 'KES'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.chart_accounts ADD COLUMN IF NOT EXISTS reporting_category VARCHAR(120)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.chart_accounts ADD COLUMN IF NOT EXISTS accounting_basis VARCHAR(50) DEFAULT 'accrual'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.chart_accounts ADD COLUMN IF NOT EXISTS is_system_account BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.journal_lines ADD COLUMN IF NOT EXISTS cost_center_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.cost_centers ADD COLUMN IF NOT EXISTS branch VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.cost_centers ADD COLUMN IF NOT EXISTS manager_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS vendor_code VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS bank_details TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS onboarding_status VARCHAR(50) DEFAULT 'draft'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS risk_profile VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.vendors ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS purchase_order_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS document_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS currency VARCHAR(20) DEFAULT 'KES'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS invoice_quantity NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS po_match_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS grn_match_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.bills ADD COLUMN IF NOT EXISTS rejection_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.payments ADD COLUMN IF NOT EXISTS scheduled_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.payments ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.payments ADD COLUMN IF NOT EXISTS reversed_payment_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.payments ADD COLUMN IF NOT EXISTS reversal_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.purchase_orders ADD COLUMN IF NOT EXISTS received_quantity NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS residual_value NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS useful_life_years NUMERIC(8, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS current_book_value NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS source_purchase_order_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.fixed_assets ADD COLUMN IF NOT EXISTS journal_entry_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.project_finance ADD COLUMN IF NOT EXISTS forecast_revenue NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.project_finance ADD COLUMN IF NOT EXISTS forecast_cost NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.project_finance ADD COLUMN IF NOT EXISTS cost_centers TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expense_claims ADD COLUMN IF NOT EXISTS distance NUMERIC(12, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expense_claims ADD COLUMN IF NOT EXISTS mileage_rate NUMERIC(12, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expense_claims ADD COLUMN IF NOT EXISTS per_diem_days NUMERIC(12, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expense_claims ADD COLUMN IF NOT EXISTS per_diem_rate NUMERIC(12, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.purchase_orders ADD COLUMN IF NOT EXISTS service_acceptance_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.purchase_orders ADD COLUMN IF NOT EXISTS invoice_match_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS archive_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS retention_until DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS document_number VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS party_name VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS amount NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS currency VARCHAR(20) DEFAULT 'KES'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS document_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS expiry_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS file_hash VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS ocr_text TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS change_comments TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS retention_policy VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.documents ADD COLUMN IF NOT EXISTS legal_hold BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.revenue_records ADD COLUMN IF NOT EXISTS source_module VARCHAR(120)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.revenue_records ADD COLUMN IF NOT EXISTS source_record_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.revenue_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.integration_events ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS vendor_name VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS customer_license BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS purchased_licenses INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS used_licenses INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS consumption_percent NUMERIC(5, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS finance_cost_amount NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS projects.licenses ADD COLUMN IF NOT EXISTS finance_revenue_amount NUMERIC(14, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expenses ADD COLUMN IF NOT EXISTS source_module VARCHAR(120)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expenses ADD COLUMN IF NOT EXISTS source_record_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expenses ADD COLUMN IF NOT EXISTS source_label VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.expenses ADD COLUMN IF NOT EXISTS department VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_payroll ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS job_group VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS salary_grade VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS role_category VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS internal_only BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS candidate_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS middle_name VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS preferred_name VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS national_id VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS tax_pin VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS passport_number VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS nationality VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS place_of_birth VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS religion VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS marital_status VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS biography TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS professional_summary TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS skills TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS languages TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS certifications_summary TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS photo_url VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS profile_completion_percentage NUMERIC(5, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS salary_band VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS cost_center_code VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS functional_manager_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS functional_manager_scope VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS personal_email VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS corporate_email VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS alternative_phone VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS physical_address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS postal_address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS city VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS county VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS country VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS business_unit VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS pay_frequency VARCHAR DEFAULT 'monthly'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS base_salary NUMERIC(12, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS contract_signed BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS budget_approved BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS payroll_profile_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS iam_request_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS onboarding_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS finance_mapping_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS asset_request_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS activation_date TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS activated_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS employment_type_status VARCHAR DEFAULT 'active'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS employment_start_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS employment_end_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS institution VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS internship_supervisor VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS consultancy_agreement_ref VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS consultancy_project VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS extension_approved_until DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_required BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_start_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_end_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_status VARCHAR DEFAULT 'Not Applicable'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_duration_months INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_extended BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_extension_count INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_extension_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_confirmed_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_confirmed_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS confirmation_status VARCHAR DEFAULT 'Not Applicable'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS confirmation_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS confirmed_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS confirmation_notes TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS probation_review_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_employees ADD COLUMN IF NOT EXISTS next_confirmation_review_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS leave_type_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS policy_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS start_day_type VARCHAR DEFAULT 'Full Day'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS end_day_type VARCHAR DEFAULT 'Full Day'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS calendar_days NUMERIC(8, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS working_days NUMERIC(8, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS leave_days NUMERIC(8, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS excluded_weekends_count INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS excluded_public_holidays_count INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS return_to_work_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS supporting_document_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS current_approver_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS payroll_lock_status VARCHAR DEFAULT 'open'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS attendance_sync_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS payroll_sync_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS created_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS updated_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS payroll_impact JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS attendance_impact JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS paid_or_unpaid VARCHAR DEFAULT 'paid'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS paid_percentage NUMERIC(5, 2) DEFAULT 100"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS requires_balance BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS requires_document BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS requires_manager_approval BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS requires_hr_review BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS allows_half_day BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS allows_backdating BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS allows_future_dating BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS excludes_weekends BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS excludes_public_holidays BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS minimum_notice_days INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS maximum_consecutive_days NUMERIC(8, 2)"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS maximum_days_per_cycle NUMERIC(8, 2)"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_employment_types JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_departments JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_branches JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_countries JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_gender_rules JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS applicable_confirmation_status JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS payroll_impact_enabled BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS attendance_exclusion_enabled BOOLEAN DEFAULT TRUE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS document_type_required VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS encashment_allowed BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_leave_policies ADD COLUMN IF NOT EXISTS max_encashable_days NUMERIC(8, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS headcount_approved BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS budget_approved BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS offer_accepted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS contract_signed BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS employment_contract_reference VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS target_start_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS branch VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS business_unit VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS reporting_manager_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS national_id VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS passport_number VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS date_of_birth DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS gender VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS source_channel VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS opening_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS requisition_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS employment_type VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS contract_end_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS salary_band VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS base_salary NUMERIC(12, 2)"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS pay_frequency VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS probation_required BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS probation_duration_months INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS probation_end_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS screening_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS interview_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS assessment_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS background_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS total_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS ranking INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS background_check_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS offer_status VARCHAR DEFAULT 'draft'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS offer_expiry_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS successful_applicant_status VARCHAR DEFAULT 'not_ready'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS conversion_status VARCHAR DEFAULT 'not_converted'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS converted_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS converted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS parsed_cv_json JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS document_readiness VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_recruitment ADD COLUMN IF NOT EXISTS compliance_readiness VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS job_title VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS business_unit VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS hiring_manager_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS reporting_manager_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS vacancies INTEGER DEFAULT 1"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS employment_type VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS contract_duration VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS salary_band VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS budget_code VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS replacement_or_new_role VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS reason_for_hire TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS required_start_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS job_description TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS required_skills JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS required_certifications JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS approved_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS rejection_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_requisitions ADD COLUMN IF NOT EXISTS created_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS job_title VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS branch VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS business_unit VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS employment_type VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS salary_band VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS description TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS publishing_channels JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_job_openings ADD COLUMN IF NOT EXISTS created_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ALTER COLUMN interview_stage_id DROP NOT NULL"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS interview_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS recruitment_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS panel_member_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS technical_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS culture_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS communication_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS experience_score NUMERIC(6, 2) DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS submitted_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_interview_feedback ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ALTER COLUMN application_id DROP NOT NULL"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS recruitment_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS offer_reference VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS job_title VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS department VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS employment_type VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS start_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS salary_band VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS base_salary NUMERIC(12, 2)"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS benefits_summary TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS contract_end_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS probation_months INTEGER"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS offer_expiry_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS approval_status VARCHAR DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS offer_status VARCHAR DEFAULT 'draft'"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS approved_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_offer_letters ADD COLUMN IF NOT EXISTS created_by VARCHAR"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_hrm_employees_national_id_not_null ON hrm_employees(national_id) WHERE national_id IS NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_hrm_employees_tax_pin_not_null ON hrm_employees(tax_pin) WHERE tax_pin IS NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_hrm_employees_passport_number_not_null ON hrm_employees(passport_number) WHERE passport_number IS NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_hrm_employees_personal_email_not_null ON hrm_employees(personal_email) WHERE personal_email IS NOT NULL"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_emergency_contacts ADD COLUMN IF NOT EXISTS alternative_phone VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_emergency_contacts ADD COLUMN IF NOT EXISTS created_by VARCHAR"))
        connection.execute(text("ALTER TABLE IF EXISTS hrm_emergency_contacts ADD COLUMN IF NOT EXISTS updated_by VARCHAR"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_profiles (
                id UUID PRIMARY KEY,
                employee_id UUID UNIQUE NOT NULL REFERENCES hrm_employees(id),
                first_name VARCHAR NOT NULL,
                middle_name VARCHAR,
                last_name VARCHAR NOT NULL,
                preferred_name VARCHAR,
                gender VARCHAR NOT NULL,
                date_of_birth DATE NOT NULL,
                nationality VARCHAR,
                national_id VARCHAR,
                passport_number VARCHAR,
                place_of_birth VARCHAR,
                religion VARCHAR,
                marital_status VARCHAR,
                employee_status VARCHAR,
                profile_completion_percentage NUMERIC(5, 2) DEFAULT 0,
                created_by VARCHAR,
                updated_by VARCHAR,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_profile_history (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                section VARCHAR NOT NULL,
                field_name VARCHAR,
                old_value TEXT,
                new_value TEXT,
                change_reason TEXT,
                changed_by VARCHAR,
                approval_status VARCHAR DEFAULT 'applied',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_contact_information (
                id UUID PRIMARY KEY,
                employee_id UUID UNIQUE NOT NULL REFERENCES hrm_employees(id),
                personal_email VARCHAR,
                corporate_email VARCHAR,
                mobile_number VARCHAR,
                alternative_phone VARCHAR,
                physical_address TEXT,
                postal_address TEXT,
                city VARCHAR,
                county VARCHAR,
                country VARCHAR,
                created_by VARCHAR,
                updated_by VARCHAR,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_dependants (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                full_name VARCHAR NOT NULL,
                relationship VARCHAR NOT NULL,
                date_of_birth DATE,
                gender VARCHAR,
                occupation VARCHAR,
                contact_information VARCHAR,
                beneficiary_percentage NUMERIC(5, 2) DEFAULT 0,
                medical_cover_eligible BOOLEAN DEFAULT FALSE,
                archived_at TIMESTAMP WITH TIME ZONE,
                archive_reason TEXT,
                created_by VARCHAR,
                updated_by VARCHAR,
                status VARCHAR DEFAULT 'active',
                soft_deleted BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_dependant_history (
                id UUID PRIMARY KEY,
                dependant_id UUID REFERENCES hrm_employee_dependants(id),
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                action VARCHAR NOT NULL,
                before_json JSON,
                after_json JSON,
                changed_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_emergency_contact_history (
                id UUID PRIMARY KEY,
                contact_id UUID REFERENCES hrm_emergency_contacts(id),
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                action VARCHAR NOT NULL,
                before_json JSON,
                after_json JSON,
                changed_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_biographies (
                id UUID PRIMARY KEY,
                employee_id UUID UNIQUE NOT NULL REFERENCES hrm_employees(id),
                employee_bio TEXT,
                professional_summary TEXT,
                skills TEXT,
                languages TEXT,
                certifications_summary TEXT,
                created_by VARCHAR,
                updated_by VARCHAR,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_profile_photos (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                file_name VARCHAR NOT NULL,
                file_url VARCHAR NOT NULL,
                thumbnail_url VARCHAR,
                content_type VARCHAR,
                file_size INTEGER,
                file_hash VARCHAR,
                active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_change_requests (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                section VARCHAR NOT NULL,
                requested_changes JSON NOT NULL,
                reason TEXT,
                approval_status VARCHAR DEFAULT 'pending_hr_approval',
                requested_by VARCHAR,
                approved_by VARCHAR,
                applied_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_job_titles (
                id UUID PRIMARY KEY,
                title_code VARCHAR UNIQUE NOT NULL,
                title_name VARCHAR NOT NULL,
                department VARCHAR NOT NULL,
                function VARCHAR,
                compatible_grade_codes JSON,
                default_salary_band_code VARCHAR,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_salary_bands (
                id UUID PRIMARY KEY,
                band_code VARCHAR UNIQUE NOT NULL,
                band_name VARCHAR NOT NULL,
                grade_code VARCHAR,
                min_salary NUMERIC(12, 2),
                max_salary NUMERIC(12, 2),
                currency VARCHAR DEFAULT 'KES',
                confidentiality_level VARCHAR DEFAULT 'restricted',
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_employment_info (
                id UUID PRIMARY KEY,
                employee_id UUID UNIQUE NOT NULL REFERENCES hrm_employees(id),
                job_title VARCHAR,
                job_grade VARCHAR,
                salary_band VARCHAR,
                cost_center_code VARCHAR,
                reporting_manager_id UUID REFERENCES hrm_employees(id),
                functional_manager_id UUID REFERENCES hrm_employees(id),
                functional_manager_scope VARCHAR,
                effective_from DATE,
                status VARCHAR DEFAULT 'active',
                updated_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_employment_history (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                buc_code VARCHAR NOT NULL,
                field_type VARCHAR NOT NULL,
                previous_value VARCHAR,
                new_value VARCHAR,
                effective_from DATE NOT NULL,
                effective_to DATE,
                status VARCHAR DEFAULT 'active',
                reason TEXT,
                supporting_document_url VARCHAR,
                initiated_by VARCHAR,
                approved_by VARCHAR,
                approval_date TIMESTAMP WITH TIME ZONE,
                audit_trail_reference VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_manager_assignments (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                manager_id UUID NOT NULL REFERENCES hrm_employees(id),
                manager_type VARCHAR NOT NULL,
                authority_scope VARCHAR,
                effective_from DATE NOT NULL,
                effective_to DATE,
                status VARCHAR DEFAULT 'active',
                reason TEXT,
                initiated_by VARCHAR,
                approved_by VARCHAR,
                approval_date TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employment_change_requests (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                buc_code VARCHAR NOT NULL,
                field_type VARCHAR NOT NULL,
                previous_value VARCHAR,
                new_value VARCHAR NOT NULL,
                effective_date DATE NOT NULL,
                reason TEXT NOT NULL,
                supporting_document_url VARCHAR,
                authority_scope VARCHAR,
                approval_status VARCHAR DEFAULT 'pending',
                requested_by VARCHAR,
                approved_by VARCHAR,
                approval_date TIMESTAMP WITH TIME ZONE,
                applied_at TIMESTAMP WITH TIME ZONE,
                rejection_reason TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employment_approvals (
                id UUID PRIMARY KEY,
                request_id UUID NOT NULL REFERENCES hrm_employment_change_requests(id),
                approver_role VARCHAR NOT NULL,
                approver_name VARCHAR,
                decision VARCHAR DEFAULT 'pending',
                comments TEXT,
                decided_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employment_audit_logs (
                id UUID PRIMARY KEY,
                actor_email VARCHAR,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                buc_code VARCHAR NOT NULL,
                action VARCHAR NOT NULL,
                previous_value VARCHAR,
                new_value VARCHAR,
                approval_reference UUID,
                reason TEXT,
                result VARCHAR DEFAULT 'success',
                metadata_json JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employment_history_employee_field ON hrm_employee_employment_history(employee_id, field_type, status)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employment_change_requests_status ON hrm_employment_change_requests(approval_status, effective_date)"))
        for column_def in [
            "description TEXT",
            "file_key VARCHAR",
            "file_extension VARCHAR",
            "file_hash VARCHAR",
            "file_size INTEGER",
            "mime_type VARCHAR",
            "content_type VARCHAR",
            "version_number INTEGER DEFAULT 1",
            "current_version BOOLEAN DEFAULT TRUE",
            "is_mandatory BOOLEAN DEFAULT FALSE",
            "is_confidential BOOLEAN DEFAULT FALSE",
            "is_archived BOOLEAN DEFAULT FALSE",
            "visibility_level VARCHAR DEFAULT 'hr'",
            "uploaded_by UUID",
            "uploaded_by_name VARCHAR",
            "uploaded_at TIMESTAMP WITH TIME ZONE",
            "verification_status VARCHAR DEFAULT 'Pending Verification'",
            "verified_by VARCHAR",
            "verified_at TIMESTAMP WITH TIME ZONE",
            "rejected_by VARCHAR",
            "rejected_at TIMESTAMP WITH TIME ZONE",
            "rejection_reason TEXT",
            "archived_at TIMESTAMP WITH TIME ZONE",
            "archived_by VARCHAR",
            "archive_reason TEXT",
            "ocr_summary TEXT",
            "updated_at TIMESTAMP WITH TIME ZONE",
        ]:
            connection.execute(text(f"ALTER TABLE IF EXISTS hrm_documents ADD COLUMN IF NOT EXISTS {column_def}"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_department_assignments (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), department VARCHAR NOT NULL,
                effective_from DATE NOT NULL, effective_to DATE, reason TEXT NOT NULL, approval_status VARCHAR DEFAULT 'approved',
                status VARCHAR DEFAULT 'active', initiated_by VARCHAR, approved_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_branch_assignments (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), branch VARCHAR NOT NULL,
                effective_from DATE NOT NULL, effective_to DATE, reason TEXT NOT NULL, approval_status VARCHAR DEFAULT 'approved',
                status VARCHAR DEFAULT 'active', initiated_by VARCHAR, approved_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_business_unit_assignments (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), business_unit VARCHAR NOT NULL,
                effective_from DATE NOT NULL, effective_to DATE, reason TEXT NOT NULL, approval_status VARCHAR DEFAULT 'approved',
                status VARCHAR DEFAULT 'active', initiated_by VARCHAR, approved_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_project_assignments (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), project_id UUID NOT NULL,
                project_name VARCHAR, project_role VARCHAR NOT NULL, allocation_percentage NUMERIC(5,2) DEFAULT 0,
                start_date DATE NOT NULL, end_date DATE, reason TEXT, status VARCHAR DEFAULT 'active', initiated_by VARCHAR,
                removed_at TIMESTAMP WITH TIME ZONE, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_team_assignments (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), team_name VARCHAR NOT NULL,
                department VARCHAR NOT NULL, primary_team BOOLEAN DEFAULT FALSE, effective_from DATE NOT NULL, effective_to DATE,
                reason TEXT, status VARCHAR DEFAULT 'active', initiated_by VARCHAR, removed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_assignment_history (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), buc_code VARCHAR NOT NULL,
                assignment_type VARCHAR NOT NULL, previous_value VARCHAR, new_value VARCHAR, effective_from DATE, effective_to DATE,
                reason TEXT, status VARCHAR DEFAULT 'active', initiated_by VARCHAR, audit_reference VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_transfer_requests (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), transfer_type VARCHAR NOT NULL,
                current_value VARCHAR, new_value VARCHAR NOT NULL, effective_date DATE NOT NULL, reason TEXT NOT NULL,
                approval_status VARCHAR DEFAULT 'pending', requested_by VARCHAR, approved_by VARCHAR, applied_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_movements (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), movement_code VARCHAR NOT NULL,
                movement_type VARCHAR NOT NULL, current_status VARCHAR, new_status VARCHAR, current_job_details JSON,
                new_job_details JSON, effective_date DATE NOT NULL, end_date DATE, reason TEXT NOT NULL,
                supporting_document_url VARCHAR, initiated_by VARCHAR, approved_by VARCHAR, approval_status VARCHAR DEFAULT 'approved',
                workflow_status VARCHAR DEFAULT 'completed', integration_events JSON, status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employee_movements_employee_code ON hrm_employee_movements(employee_id, movement_code, effective_date)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_movement_approvals (
                id UUID PRIMARY KEY, movement_id UUID NOT NULL REFERENCES hrm_employee_movements(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                approval_level INTEGER DEFAULT 1, approver_role VARCHAR, approver_name VARCHAR, decision VARCHAR DEFAULT 'approved',
                comments TEXT, decided_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_status_history (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), status_code VARCHAR NOT NULL,
                old_status VARCHAR, new_status VARCHAR NOT NULL, effective_date DATE NOT NULL, end_date DATE, reason TEXT NOT NULL,
                initiated_by VARCHAR, approved_by VARCHAR, approval_status VARCHAR DEFAULT 'approved', workflow_status VARCHAR DEFAULT 'completed',
                supporting_document_url VARCHAR, metadata_json JSON, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employee_status_history_employee_status ON hrm_employee_status_history(employee_id, new_status, effective_date)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_suspension_records (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), suspension_type VARCHAR DEFAULT 'administrative',
                start_date DATE NOT NULL, expected_end_date DATE, reason TEXT NOT NULL, paid BOOLEAN DEFAULT TRUE,
                iam_access_disabled BOOLEAN DEFAULT TRUE, payroll_notified BOOLEAN DEFAULT TRUE, approval_status VARCHAR DEFAULT 'approved',
                status VARCHAR DEFAULT 'active', created_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_reinstatement_records (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), reinstatement_date DATE NOT NULL,
                previous_status VARCHAR, reason TEXT NOT NULL, payroll_review_status VARCHAR DEFAULT 'queued',
                iam_reactivation_status VARCHAR DEFAULT 'queued', approval_status VARCHAR DEFAULT 'approved',
                created_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_leave_of_absence_records (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), leave_type VARCHAR NOT NULL,
                start_date DATE NOT NULL, expected_return_date DATE NOT NULL, actual_return_date DATE, reason TEXT NOT NULL,
                payroll_impact VARCHAR DEFAULT 'review_required', iam_access_impact VARCHAR DEFAULT 'review_required',
                status VARCHAR DEFAULT 'active', created_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_retirement_records (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), retirement_type VARCHAR NOT NULL,
                retirement_date DATE NOT NULL, reason TEXT NOT NULL, approval_status VARCHAR DEFAULT 'approved',
                final_benefits_status VARCHAR DEFAULT 'queued', clearance_status VARCHAR DEFAULT 'queued',
                iam_deactivation_status VARCHAR DEFAULT 'queued', created_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_death_records (
                id UUID PRIMARY KEY, employee_id UUID NOT NULL REFERENCES hrm_employees(id), date_of_death DATE NOT NULL,
                supporting_document_url VARCHAR NOT NULL, notes TEXT, payroll_final_processing_status VARCHAR DEFAULT 'queued',
                benefits_workflow_status VARCHAR DEFAULT 'queued', iam_deactivation_status VARCHAR DEFAULT 'queued',
                clearance_status VARCHAR DEFAULT 'sensitive_review', created_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_versions (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                version_number INTEGER NOT NULL, file_name VARCHAR NOT NULL, file_url VARCHAR NOT NULL, file_hash VARCHAR, file_size INTEGER,
                uploaded_by_name VARCHAR, status VARCHAR DEFAULT 'current', created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_reviews (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                decision VARCHAR NOT NULL, reviewer VARCHAR, comments TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_expiry_tracking (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                expiry_date DATE NOT NULL, reminder_stage VARCHAR NOT NULL, escalation_level VARCHAR DEFAULT 'employee',
                notification_status VARCHAR DEFAULT 'pending', created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_rejections (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                rejection_reason TEXT NOT NULL, rejected_by VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_archive (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                archived_by VARCHAR, archive_reason TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_type_configs (
                id UUID PRIMARY KEY, document_type VARCHAR UNIQUE NOT NULL, display_name VARCHAR NOT NULL,
                is_mandatory BOOLEAN DEFAULT FALSE, requires_verification BOOLEAN DEFAULT TRUE, allows_expiry_date BOOLEAN DEFAULT FALSE,
                requires_issue_date BOOLEAN DEFAULT FALSE, is_confidential BOOLEAN DEFAULT FALSE, allowed_file_types JSON,
                max_file_size_mb INTEGER DEFAULT 15, retention_policy VARCHAR DEFAULT 'employee_lifecycle_plus_7_years',
                access_level_required VARCHAR DEFAULT 'hr', status VARCHAR DEFAULT 'active', created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_document_access_logs (
                id UUID PRIMARY KEY, document_id UUID NOT NULL REFERENCES hrm_documents(id), employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                accessed_by VARCHAR, access_type VARCHAR NOT NULL, ip_address VARCHAR, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        document_type_seed = [
            ("NATIONAL_ID", "National ID", True, True, False, False, True, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 15, "employee_lifecycle_plus_7_years", "hr"),
            ("PASSPORT", "Passport", False, True, True, True, True, ["pdf", "jpg", "jpeg", "png"], 15, "employee_lifecycle_plus_7_years", "hr"),
            ("ACADEMIC_CERTIFICATE", "Academic Certificate", False, True, False, True, False, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 15, "employee_lifecycle_plus_7_years", "manager"),
            ("PROFESSIONAL_CERTIFICATION", "Professional Certification", False, True, True, True, False, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 15, "employee_lifecycle_plus_7_years", "manager"),
            ("EMPLOYMENT_CONTRACT", "Employment Contract", True, True, True, True, True, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 20, "employee_lifecycle_plus_7_years", "hr"),
            ("NDA", "NDA", False, True, True, True, True, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 15, "employee_lifecycle_plus_7_years", "hr"),
            ("CV", "CV", False, False, False, False, False, ["pdf", "doc", "docx"], 10, "employee_lifecycle_plus_3_years", "manager"),
            ("MEDICAL_DOCUMENT", "Medical Document", False, True, True, True, True, ["pdf", "jpg", "jpeg", "png"], 15, "medical_confidential", "medical"),
            ("TAX_DOCUMENT", "Tax Document", True, True, True, False, True, ["pdf", "jpg", "jpeg", "png", "doc", "docx"], 15, "statutory_plus_7_years", "payroll"),
            ("WORK_PERMIT", "Work Permit", False, True, True, True, True, ["pdf", "jpg", "jpeg", "png"], 15, "statutory_plus_7_years", "hr"),
        ]
        for document_type, display_name, mandatory, verification, expiry, issue, confidential, file_types, max_size, retention, access_level in document_type_seed:
            connection.execute(
                text(
                    """
                    INSERT INTO hrm_employee_document_type_configs (
                        id, document_type, display_name, is_mandatory, requires_verification, allows_expiry_date,
                        requires_issue_date, is_confidential, allowed_file_types, max_file_size_mb, retention_policy,
                        access_level_required, status, created_at
                    )
                    SELECT :id, :document_type, :display_name, :mandatory, :verification, :expiry, :issue, :confidential,
                        CAST(:file_types AS JSON), :max_size, :retention, :access_level, 'active', now()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM hrm_employee_document_type_configs WHERE document_type = :document_type
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "document_type": document_type,
                    "display_name": display_name,
                    "mandatory": mandatory,
                    "verification": verification,
                    "expiry": expiry,
                    "issue": issue,
                    "confidential": confidential,
                    "file_types": json.dumps(file_types),
                    "max_size": max_size,
                    "retention": retention,
                    "access_level": access_level,
                },
            )
        for column_def in ["file_key VARCHAR", "replacement_reason TEXT", "uploaded_by UUID", "uploaded_at TIMESTAMP WITH TIME ZONE"]:
            connection.execute(text(f"ALTER TABLE IF EXISTS hrm_employee_document_versions ADD COLUMN IF NOT EXISTS {column_def}"))
        for column_def in ["review_action VARCHAR", "reviewer_id UUID", "review_notes TEXT", "reviewed_at TIMESTAMP WITH TIME ZONE"]:
            connection.execute(text(f"ALTER TABLE IF EXISTS hrm_employee_document_reviews ADD COLUMN IF NOT EXISTS {column_def}"))
        for column_def in [
            "reminder_90_sent BOOLEAN DEFAULT FALSE",
            "reminder_60_sent BOOLEAN DEFAULT FALSE",
            "reminder_30_sent BOOLEAN DEFAULT FALSE",
            "reminder_7_sent BOOLEAN DEFAULT FALSE",
            "escalation_status VARCHAR DEFAULT 'not_escalated'",
        ]:
            connection.execute(text(f"ALTER TABLE IF EXISTS hrm_employee_document_expiry_tracking ADD COLUMN IF NOT EXISTS {column_def}"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_number_sequences (
                id UUID PRIMARY KEY,
                year INTEGER NOT NULL,
                prefix VARCHAR(80) NOT NULL,
                last_sequence INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                UNIQUE(year, prefix)
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_import_batches (
                id UUID PRIMARY KEY,
                batch_number VARCHAR UNIQUE NOT NULL,
                file_name VARCHAR,
                file_hash VARCHAR,
                source_format VARCHAR NOT NULL,
                import_mode VARCHAR DEFAULT 'create',
                uploaded_by VARCHAR,
                approval_status VARCHAR DEFAULT 'not_required',
                processing_status VARCHAR DEFAULT 'uploaded',
                total_rows INTEGER DEFAULT 0,
                valid_rows INTEGER DEFAULT 0,
                created_rows INTEGER DEFAULT 0,
                updated_rows INTEGER DEFAULT 0,
                rejected_rows INTEGER DEFAULT 0,
                parse_summary TEXT,
                validation_errors JSON,
                rollback_status VARCHAR DEFAULT 'not_requested',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_import_rows (
                id UUID PRIMARY KEY,
                batch_id UUID NOT NULL REFERENCES hrm_employee_import_batches(id),
                row_number INTEGER NOT NULL,
                employee_id UUID REFERENCES hrm_employees(id),
                employee_code VARCHAR,
                row_payload JSON,
                normalized_payload JSON,
                row_status VARCHAR DEFAULT 'pending',
                action_taken VARCHAR,
                error_messages JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employee_import_rows_batch_id ON hrm_employee_import_rows(batch_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employee_import_rows_employee_id ON hrm_employee_import_rows(employee_id)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_employment_details (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                employment_type VARCHAR NOT NULL,
                start_date DATE,
                end_date DATE,
                institution VARCHAR,
                internship_supervisor VARCHAR,
                consultancy_agreement_ref VARCHAR,
                consultancy_project VARCHAR,
                extension_approved_until DATE,
                expiry_status VARCHAR DEFAULT 'active',
                status VARCHAR DEFAULT 'active',
                created_by VARCHAR,
                updated_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_employment_type_history (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                previous_type VARCHAR,
                new_type VARCHAR NOT NULL,
                previous_end_date DATE,
                new_end_date DATE,
                change_reason TEXT,
                changed_by VARCHAR,
                changed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_contract_extensions (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                employment_detail_id UUID REFERENCES hrm_employee_employment_details(id),
                previous_end_date DATE,
                new_end_date DATE NOT NULL,
                reason TEXT,
                approval_status VARCHAR DEFAULT 'approved',
                approved_by VARCHAR,
                created_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employment_details_employee_id ON hrm_employee_employment_details(employee_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_employment_details_end_date ON hrm_employee_employment_details(end_date)"))
        for column_def in [
            "probation_required BOOLEAN DEFAULT FALSE",
            "probation_start_date DATE",
            "probation_end_date DATE",
            "probation_status VARCHAR DEFAULT 'Not Applicable'",
            "probation_duration_months INTEGER",
            "probation_extended BOOLEAN DEFAULT FALSE",
            "probation_extension_count INTEGER DEFAULT 0",
            "probation_extension_reason TEXT",
            "probation_confirmed_date DATE",
            "probation_confirmed_by VARCHAR",
        ]:
            connection.execute(text(f"ALTER TABLE IF EXISTS hrm_employee_employment_details ADD COLUMN IF NOT EXISTS {column_def}"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_probation_records (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                employment_detail_id UUID REFERENCES hrm_employee_employment_details(id),
                probation_required BOOLEAN DEFAULT FALSE,
                start_date DATE,
                end_date DATE,
                duration_months INTEGER,
                status VARCHAR DEFAULT 'Not Applicable',
                extended BOOLEAN DEFAULT FALSE,
                extension_count INTEGER DEFAULT 0,
                max_extension_count INTEGER DEFAULT 2,
                extension_reason TEXT,
                confirmed_date DATE,
                confirmed_by VARCHAR,
                failed_date DATE,
                failed_reason TEXT,
                created_by VARCHAR,
                updated_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_probation_reviews (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                probation_record_id UUID NOT NULL REFERENCES hrm_employee_probation_records(id),
                review_type VARCHAR NOT NULL,
                outcome VARCHAR NOT NULL,
                comments TEXT,
                reviewer VARCHAR,
                review_date DATE DEFAULT CURRENT_DATE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_probation_records_employee_id ON hrm_employee_probation_records(employee_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_probation_records_end_date ON hrm_employee_probation_records(end_date)"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS hrm_employee_confirmation_records (
                id UUID PRIMARY KEY,
                employee_id UUID NOT NULL REFERENCES hrm_employees(id),
                probation_record_id UUID REFERENCES hrm_employee_probation_records(id),
                probation_review_id UUID REFERENCES hrm_employee_probation_reviews(id),
                decision VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'Pending Confirmation' NOT NULL,
                confirmation_date DATE,
                confirmed_by VARCHAR,
                notes TEXT,
                reason TEXT,
                next_review_date DATE,
                created_by VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_confirmation_records_employee_id ON hrm_employee_confirmation_records(employee_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_hrm_confirmation_records_status ON hrm_employee_confirmation_records(status)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS qualification_status VARCHAR(80) DEFAULT 'unqualified'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS converted_contact_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS converted_opportunity_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS assigned_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS manager_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS created_by_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS duplicate_flag BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS duplicate_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS disqualification_reason TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_industry VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_website VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_address TEXT"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_country VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_region VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_vertical VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS account_type VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS contact_job_title VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS contact_department VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS expected_close_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS expected_activation_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS expected_renewal_date DATE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS pipeline_type VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS arena VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.leads ADD COLUMN IF NOT EXISTS service_scope VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.tasks ADD COLUMN IF NOT EXISTS assigned_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.tasks ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS owner_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS approved_by_employee_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.accounts ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS service_scope VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.deals ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.opportunities ADD COLUMN IF NOT EXISTS service_scope VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.pmo_projects ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.sla_assignments ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.tenders ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.tenders ADD COLUMN IF NOT EXISTS service_scope VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS deal_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'draft'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS approval_required BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS version_number INTEGER DEFAULT 1"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.quotations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS crm.customer_lpos (
                id UUID PRIMARY KEY,
                lpo_number VARCHAR(120) UNIQUE NOT NULL,
                account_id UUID NOT NULL,
                opportunity_id UUID,
                quotation_id UUID,
                contract_id UUID,
                lpo_date DATE NOT NULL,
                currency VARCHAR(20) DEFAULT 'KES',
                subtotal NUMERIC(14, 2) DEFAULT 0,
                tax_amount NUMERIC(14, 2) DEFAULT 0,
                discount_amount NUMERIC(14, 2) DEFAULT 0,
                total_amount NUMERIC(14, 2) DEFAULT 0,
                variance_amount NUMERIC(14, 2) DEFAULT 0,
                variance_reason TEXT,
                validation_status VARCHAR(80) DEFAULT 'pending',
                approval_status VARCHAR(80) DEFAULT 'not_required',
                document_url VARCHAR(500),
                uploaded_by VARCHAR(255),
                status VARCHAR(80) DEFAULT 'received',
                notes TEXT,
                soft_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_customer_lpos_account_id ON crm.customer_lpos(account_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_customer_lpos_opportunity_id ON crm.customer_lpos(opportunity_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_customer_lpos_quotation_id ON crm.customer_lpos(quotation_id)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS contact_role VARCHAR(150)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS communication_preferences JSON"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS unlinked_prospect BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.contacts ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS contact_id UUID"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS category VARCHAR(100)"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS sla_status VARCHAR(50) DEFAULT 'on_track'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS response_due_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS resolution_due_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS soft_deleted BOOLEAN DEFAULT FALSE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.customer_tickets ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.licences ADD COLUMN IF NOT EXISTS purchase_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.licences ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(50) DEFAULT 'pending'"))
        connection.execute(text("ALTER TABLE IF EXISTS crm.licences ADD COLUMN IF NOT EXISTS invoice_status VARCHAR(50) DEFAULT 'not_ready'"))
        connection.execute(text("ALTER TABLE IF EXISTS finance.invoices ADD COLUMN IF NOT EXISTS business_id VARCHAR(80)"))
        capability_defaults = [
            ("CRM", "Lead, contact, account, opportunity, quotation, pipeline, journey, territory, and customer history management", "Zoho CRM, Zendesk, ServiceNow", "CRM", "CRM entities, sales workflow rules, territory rules, quote/deal conversion, entity explorer", "/crm/leads", "/api/crm/leads"),
            ("HRM", "HRIS, recruitment, onboarding, payroll, leave, lifecycle, performance, benefits, employee self-service, and HR service delivery", "BambooHR, ServiceNow", "HRM", "HRM records, staff roles, portal requests, approvals, policies, reports", "/hrm", "/api/hrm/employees"),
            ("ERP", "Inventory, sales operations, procurement, service operations, enterprise workflow ERP, and portfolio operations", "Zoho CRM, DualEntry, ServiceNow, Asana, Microsoft Project", "ERP", "Inventory register, procurement, workflow rules, integrations, resource allocations", "/erp/inventory", "/api/enterprise/inventory-items"),
            ("Finance & Accounting", "Accounting, revenue recognition, AP/AR automation, billing, consolidation, audit trails, payroll and cost management", "DualEntry, BambooHR, ServiceNow, Microsoft Project", "Finance", "General ledger, invoices, bills, payments, budgets, tax, assets, revenue records, audit trails", "/finance", "/api/finance/dashboard"),
            ("Invoice Management", "Quotations, sales invoicing, OCR-ready documents, recurring/subscription billing, approvals, payment tracking, and billing support", "Zoho CRM, DualEntry, Zendesk, ServiceNow", "Finance", "Finance invoices, CRM quotes, documents, approval workflows, payment status automation", "/finance/invoices", "/api/finance/invoices"),
            ("Project Management", "Projects, portfolios, tasks, milestones, dependencies, risks, budgets, billing, resource plans, and delivery tracking", "Asana, Microsoft Project, ServiceNow, Zoho CRM", "Projects", "PMO projects, tasks, milestones, risks, SLAs, project finance and resource allocations", "/projects/tasks", "/api/enterprise/project-tasks"),
            ("Task Management", "Tasks, follow-ups, activities, ticket tasks, approval tasks, HR tasks, and project work packages", "Zoho CRM, BambooHR, Asana, Microsoft Project, Zendesk", "Projects", "CRM activities, project tasks, workflow-generated tasks, support tickets", "/projects/tasks", "/api/enterprise/project-tasks"),
            ("Workflow Automation", "Workflow rules, blueprints, triggers, HR automation, finance automation, approval routing, escalations, and orchestration", "Zoho CRM, BambooHR, DualEntry, Zendesk, ServiceNow, Asana", "Automation", "Workflow rules, logs, notification queue, policies, approvals, sync endpoints", "/workflows", "/api/enterprise/workflow-rules"),
            ("AI & Automation", "AI-ready lead scoring, forecasting, reconciliation, ticket routing, scheduling prediction, and copilots for MVP2", "Zoho Zia, DualEntry AI, Zendesk AI, ServiceNow AI, Asana AI, Microsoft Project", "Automation", "MVP1 stores clean operational data and workflow events for later AI training; AI route remains isolated for MVP2", "/workflows", "/api/enterprise/workflow-rules"),
            ("Analytics & Reports", "CRM dashboards, workforce analytics, financial dashboards, SLA reporting, portfolio dashboards, KPI reports, and PDF reports", "All compared platforms", "Analytics", "Executive dashboard, analytics filters, reports center, resource analytics endpoints", "/analytics", "/api/analytics/dashboard"),
            ("Customer Support / Helpdesk", "Support cases, requests, approvals, ticketing, history, SLA routing, escalation, and support analytics", "Zendesk, ServiceNow, Zoho CRM, BambooHR", "Support", "Support tickets, portal requests, SLA assignments, knowledge base, notifications", "/support", "/api/enterprise/support-tickets"),
            ("ITSM / Service Management", "Incident, problem, change, service desk, CMDB-ready records, service portals, operational workflows", "ServiceNow, Zendesk", "Support", "Support tickets, assets/inventory, portal requests, workflow rules, integrations", "/support", "/api/enterprise/support-tickets"),
            ("Security & Compliance", "RBAC, permissions, audit logs, HR compliance, finance compliance, fraud/anomaly readiness, GRC and SLA governance", "Zoho CRM, BambooHR, DualEntry, Zendesk, ServiceNow, Asana, Microsoft Project", "Admin", "Access rights, policies, audit trails, GRC records, approvals, workflow logs", "/settings/access-rights", "/api/admin/access-rights"),
            ("Governance & Risk", "Sales governance, HR policies, compliance controls, SLA governance, risk management, workflow governance", "All compared platforms", "Admin", "Organization policies, GRC, project risks, workflow logs, approval records", "/settings/policies", "/api/admin/policies"),
            ("Asset Management", "CRM assets, employee assets, financial assets, IT assets, enterprise assets, and project resource assets", "Zoho CRM, BambooHR, DualEntry, Zendesk, ServiceNow, Asana, Microsoft Project", "ERP", "Finance fixed assets, ERP inventory, custodians, resource allocation", "/erp/inventory", "/api/enterprise/inventory-items"),
            ("Document Management", "CRM docs, HR docs, OCR-ready finance docs, contracts, KB, records, file sharing, and SharePoint-style document references", "All compared platforms", "Documents", "Finance documents, HR documents, tender docs, knowledge base, upload/preview/download", "/knowledge-base", "/api/enterprise/knowledge-base"),
            ("Collaboration", "Internal notes, mentions-ready logs, employee communication, finance collaboration, agent collaboration, team coordination", "Zoho CRM, BambooHR, DualEntry, Zendesk, ServiceNow, Asana, Microsoft Project", "Collaboration", "Communication logs, activities, support tickets, project tasks, portal requests", "/communications", "/api/enterprise/communications"),
            ("Approvals & Escalations", "Multi-level approvals, HR approvals, invoice approvals, support escalations, enterprise approval chains, project approvals", "All compared platforms", "Automation", "Finance approvals, workflow rules, notification queue, support priority/escalation status", "/workflows", "/api/enterprise/workflow-rules"),
            ("Mobile Access", "Responsive internal web access for CRM, HR, finance, support, projects, reports, and approvals", "All compared platforms", "Platform", "Next.js responsive application, role-based access, API-backed screens", "/", "/api/health"),
            ("Integrations & APIs", "CRM, HRIS, ERP, banking, AD, ticketing, marketplace, Microsoft ecosystem, file import, APIs and webhooks", "All compared platforms", "Integrations", "Integration gateways, import batches, CSV/JSON/YAML/XLSX/DOCX parsing, API endpoints", "/integrations", "/api/enterprise/connectors"),
            ("Portfolio / Program Management", "Sales portfolios, workforce planning, multi-entity finance, multi-team support, enterprise programs, PPM", "Asana, Microsoft Project, ServiceNow, DualEntry", "Projects", "Goals, PMO projects, project finance, milestones, resource allocations, analytics", "/goals", "/api/enterprise/goals"),
            ("Scheduling & Calendars", "Meetings, shifts, billing schedules, support schedules, enterprise calendars, timelines, advanced scheduling", "All compared platforms", "Scheduling", "Schedule events, HR attendance/leave, project dates, licence renewal dates, workflow reminders", "/schedule", "/api/enterprise/schedule-events"),
            ("Resource Management", "Sales resources, workforce allocation, financial allocation, support allocation, workload management, resource leveling", "BambooHR, Asana, Microsoft Project, ServiceNow", "Resources", "Resource allocations, staff roles, PMO assignments, SLA engineers, targets", "/resources", "/api/enterprise/resource-allocations"),
            ("Knowledge Management", "CRM KB, HR KB, finance docs, help center, enterprise KB, shared docs, SharePoint-style knowledge", "All compared platforms", "Knowledge", "Knowledge base articles, documents, reports and policies", "/knowledge-base", "/api/enterprise/knowledge-base"),
            ("Self-Service Portals", "Customer portals, employee self-service, finance dashboards, customer self-service, service portals, request forms, project portals", "Zoho CRM, BambooHR, DualEntry, Zendesk, ServiceNow, Asana, Microsoft Project", "Portals", "Portal requests, role-based screens, reports, ticketing, employee/staff views", "/portal-requests", "/api/enterprise/portal-requests"),
            ("Communication Channels", "Email, WhatsApp, telephony, social, employee communications, notifications, chat, voice, SMS, Teams collaboration", "Zoho CRM, BambooHR, Zendesk, ServiceNow, Asana, Microsoft Project", "Communications", "Communication logs, notification queue, integration gateways, activity history", "/communications", "/api/enterprise/communications"),
            ("Scalability", "SME-to-enterprise architecture across CRM, HRM, finance, support, work management, and project portfolio", "All compared platforms", "Platform", "Modular schemas, RBAC, generic resource manager, integrations, analytics, configurable policies", "/settings/policies", "/api/admin/policies"),
        ]
        for category, capability, platforms, module, mechanism, route_path, api_endpoint in capability_defaults:
            connection.execute(
                text(
                    """
                    INSERT INTO auth.feature_capabilities (id, category, capability, source_platforms, module, mechanism, implementation_status, route_path, api_endpoint, created_at)
                    SELECT :id, :category, :capability, :platforms, :module, :mechanism, 'implemented', :route_path, :api_endpoint, now()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM auth.feature_capabilities
                        WHERE category = :category AND capability = :capability
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "category": category,
                    "capability": capability,
                    "platforms": platforms,
                    "module": module,
                    "mechanism": mechanism,
                    "route_path": route_path,
                    "api_endpoint": api_endpoint,
                },
            )
        sequence_defaults = [
            ("crm.accounts", "IS-ACC"),
            ("crm.leads", "IS-LED"),
            ("crm.deals", "IS-DEA"),
            ("crm.opportunities", "IS-OPP"),
            ("crm.customer_lpos", "IS-LPO"),
            ("crm.contracts", "IS-CON"),
            ("crm.licences", "IS-LIC"),
            ("crm.pmo_projects", "IS-PRJ"),
            ("projects.projects", "IS-PRJ"),
            ("projects.licenses", "IS-LIC"),
            ("crm.sla_assignments", "IS-SLA"),
            ("projects.slas", "IS-SLA"),
            ("crm.tenders", "IS-TEN"),
            ("finance.invoices", "IS-INV"),
            ("finance.receipts", "IS-RCT"),
            ("finance.expenses", "IS-EXP"),
            ("finance.purchase_requests", "IS-PR"),
            ("finance.payroll_postings", "IS-PAY"),
            ("auth.integration_connectors", "IS-INT"),
            ("auth.data_import_batches", "IS-IMP"),
            ("auth.workflow_rules", "IS-WFL"),
            ("auth.notification_events", "IS-NOT"),
            ("crm.support_tickets", "IS-TCK"),
            ("auth.knowledge_base_articles", "IS-KBA"),
            ("crm.project_tasks", "IS-TSK"),
            ("crm.project_milestones", "IS-MIL"),
            ("crm.project_risks", "IS-RSK"),
            ("finance.inventory_items", "IS-INVY"),
            ("auth.organization_goals", "IS-GOL"),
            ("crm.territory_rules", "IS-TER"),
            ("auth.portal_requests", "IS-REQ"),
            ("auth.communication_logs", "IS-COM"),
            ("auth.schedule_events", "IS-SCH"),
            ("auth.resource_allocations", "IS-RES"),
        ]
        for entity_key, prefix in sequence_defaults:
            connection.execute(
                text(
                    """
                    INSERT INTO auth.entity_sequences (id, organization_code, entity_key, prefix, next_number, padding, active, created_at)
                    SELECT :id, 'IS', :entity_key, :prefix, 1, 5, true, now()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM auth.entity_sequences WHERE entity_key = :entity_key
                    )
                    """
                ),
                {"id": str(uuid.uuid4()), "entity_key": entity_key, "prefix": prefix},
            )
        iam_roles = [
            ("user", "Standard User", "Daily operational access for CRM, self-service HR, expenses, purchase requests, and assigned project work."),
            ("manager", "Manager", "Team visibility, operational approvals, and assigned department workflow access."),
            ("sales", "Sales Executive", "Lead, account, contact, opportunity, activity, and quotation workflow access."),
            ("finance_admin", "Finance Administrator", "Full finance administration and posting access."),
            ("accountant", "Accountant", "Finance transaction processing and reporting access."),
            ("hr_admin", "HR Administrator", "Full HRMS employee lifecycle and IAM-linked access administration."),
            ("security_admin", "Security Administrator", "IAM role, permission, access review, and audit administration."),
        ]
        for role_code, role_name, description in iam_roles:
            connection.execute(
                text(
                    """
                    INSERT INTO auth.roles (id, role_code, role_name, module_scope, description, requires_mfa, status, soft_deleted, created_at)
                    SELECT :id, :role_code, :role_name, 'enterprise', :description, false, 'active', false, now()
                    WHERE NOT EXISTS (SELECT 1 FROM auth.roles WHERE role_code = :role_code)
                    """
                ),
                {"id": str(uuid.uuid4()), "role_code": role_code, "role_name": role_name, "description": description},
            )
        iam_permissions = [
            ("CRM_LEAD_CREATE", "crm", "leads", "create"),
            ("CRM_LEAD_VIEW", "crm", "leads", "read"),
            ("CRM_LEAD_UPDATE", "crm", "leads", "update"),
            ("CRM_ACCOUNT_CREATE", "crm", "accounts", "create"),
            ("CRM_ACCOUNT_VIEW", "crm", "accounts", "read"),
            ("CRM_ACCOUNT_UPDATE", "crm", "accounts", "update"),
            ("CRM_CONTACT_CREATE", "crm", "contacts", "create"),
            ("CRM_CONTACT_VIEW", "crm", "contacts", "read"),
            ("CRM_CONTACT_UPDATE", "crm", "contacts", "update"),
            ("CRM_OPPORTUNITY_CREATE", "crm", "opportunities", "create"),
            ("CRM_OPPORTUNITY_VIEW", "crm", "opportunities", "read"),
            ("CRM_OPPORTUNITY_UPDATE", "crm", "opportunities", "update"),
            ("CRM_ACTIVITY_CREATE", "crm", "activities", "create"),
            ("CRM_ACTIVITY_VIEW", "crm", "activities", "read"),
            ("CRM_ACTIVITY_UPDATE", "crm", "activities", "update"),
            ("PROJECT_TASK_CREATE", "projects", "tasks", "create"),
            ("PROJECT_TASK_VIEW", "projects", "tasks", "read"),
            ("PROJECT_TASK_UPDATE", "projects", "tasks", "update"),
            ("PROJECT_TIMESHEET_CREATE", "projects", "timesheets", "create"),
            ("PROJECT_TIMESHEET_VIEW", "projects", "timesheets", "read"),
            ("PROJECT_TIMESHEET_UPDATE", "projects", "timesheets", "update"),
            ("HR_LEAVE_CREATE", "hrm", "leave-requests", "create"),
            ("HR_LEAVE_VIEW", "hrm", "leave-requests", "read"),
            ("HR_DOCUMENT_CREATE", "hrm", "documents", "create"),
            ("HR_DOCUMENT_VIEW", "hrm", "documents", "read"),
            ("FIN_EXPENSE_CREATE", "finance", "expense-claims", "create"),
            ("FIN_EXPENSE_VIEW", "finance", "expense-claims", "read"),
            ("FIN_PURCHASE_REQUEST_CREATE", "finance", "purchase-requests", "create"),
            ("FIN_PURCHASE_REQUEST_VIEW", "finance", "purchase-requests", "read"),
            ("FINANCE_VIEW", "finance", "*", "read"),
            ("IAM_ADMIN", "iam", "*", "*"),
            ("ENTERPRISE_ADMIN", "*", "*", "*"),
        ]
        for permission_code, module, resource, action in iam_permissions:
            connection.execute(
                text(
                    """
                    INSERT INTO auth.permissions (id, permission_code, module, resource, action, status, created_at)
                    SELECT :id, :permission_code, :module, :resource, :action, 'active', now()
                    WHERE NOT EXISTS (SELECT 1 FROM auth.permissions WHERE permission_code = :permission_code)
                    """
                ),
                {"id": str(uuid.uuid4()), "permission_code": permission_code, "module": module, "resource": resource, "action": action},
            )
        role_permission_map = {
            "user": [
                "CRM_LEAD_CREATE", "CRM_LEAD_VIEW", "CRM_LEAD_UPDATE", "CRM_ACCOUNT_VIEW", "CRM_CONTACT_CREATE",
                "CRM_CONTACT_VIEW", "CRM_CONTACT_UPDATE", "CRM_OPPORTUNITY_CREATE", "CRM_OPPORTUNITY_VIEW",
                "CRM_OPPORTUNITY_UPDATE", "CRM_ACTIVITY_CREATE", "CRM_ACTIVITY_VIEW", "CRM_ACTIVITY_UPDATE",
                "PROJECT_TASK_CREATE", "PROJECT_TASK_VIEW", "PROJECT_TASK_UPDATE", "PROJECT_TIMESHEET_CREATE",
                "PROJECT_TIMESHEET_VIEW", "PROJECT_TIMESHEET_UPDATE", "HR_LEAVE_CREATE", "HR_LEAVE_VIEW",
                "HR_DOCUMENT_CREATE", "HR_DOCUMENT_VIEW", "FIN_EXPENSE_CREATE", "FIN_EXPENSE_VIEW",
                "FIN_PURCHASE_REQUEST_CREATE", "FIN_PURCHASE_REQUEST_VIEW",
            ],
            "manager": ["FINANCE_VIEW", "CRM_ACCOUNT_VIEW", "CRM_OPPORTUNITY_VIEW", "CRM_ACTIVITY_VIEW"],
            "sales": ["CRM_LEAD_CREATE", "CRM_LEAD_VIEW", "CRM_LEAD_UPDATE", "CRM_ACCOUNT_CREATE", "CRM_ACCOUNT_VIEW", "CRM_ACCOUNT_UPDATE", "CRM_CONTACT_CREATE", "CRM_CONTACT_VIEW", "CRM_CONTACT_UPDATE", "CRM_OPPORTUNITY_CREATE", "CRM_OPPORTUNITY_VIEW", "CRM_OPPORTUNITY_UPDATE", "CRM_ACTIVITY_CREATE", "CRM_ACTIVITY_VIEW", "CRM_ACTIVITY_UPDATE"],
            "finance_admin": ["ENTERPRISE_ADMIN"],
            "accountant": ["FINANCE_VIEW", "FIN_EXPENSE_VIEW", "FIN_PURCHASE_REQUEST_VIEW"],
            "hr_admin": ["ENTERPRISE_ADMIN"],
            "security_admin": ["IAM_ADMIN"],
        }
        for role_code, permission_codes in role_permission_map.items():
            for permission_code in permission_codes:
                connection.execute(
                    text(
                        """
                        INSERT INTO auth.role_permissions (id, role_id, permission_id, created_at)
                        SELECT :id, r.id, p.id, now()
                        FROM auth.roles r, auth.permissions p
                        WHERE r.role_code = :role_code AND p.permission_code = :permission_code
                        AND NOT EXISTS (
                            SELECT 1 FROM auth.role_permissions rp
                            WHERE rp.role_id = r.id AND rp.permission_id = p.id
                        )
                        """
                    ),
                    {"id": str(uuid.uuid4()), "role_code": role_code, "permission_code": permission_code},
                )
        for department, responsibility in DEPARTMENT_RESPONSIBILITIES.items():
            connection.execute(
                text(
                    """
                    INSERT INTO crm.department_workflows (id, department, head_role, responsibility, status, created_at)
                    SELECT :id, :department, :head_role, :responsibility, 'pending', now()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM crm.department_workflows
                        WHERE department = :department AND responsibility = :responsibility
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "department": department,
                    "head_role": CRM_DEPARTMENT_HEADS.get(department),
                    "responsibility": responsibility,
                },
            )
        connection.commit()
    from backend.core.database import SessionLocal
    from backend.models.auth import AuthUser
    from backend.models.iam import IAMRole, IAMUserRole

    db = SessionLocal()
    try:
        for auth_user in db.query(AuthUser).all():
            role = db.query(IAMRole).filter(IAMRole.role_code == str(auth_user.role).lower(), IAMRole.status == "active").first()
            if not role:
                continue
            exists = db.query(IAMUserRole).filter(IAMUserRole.user_id == auth_user.id, IAMUserRole.role_id == role.id).first()
            if not exists:
                db.add(IAMUserRole(user_id=auth_user.id, role_id=role.id, status="active"))
        db.commit()
        seed_defaults(db)
    finally:
        db.close()
    print("BusinessOS database tables created successfully.")


if __name__ == "__main__":
    create_tables()
