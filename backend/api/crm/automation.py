from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.crud import create_record, delete_record, get_or_404, update_record
from backend.core.database import get_db
from backend.models.crm import CRMAutomationRule
from backend.schemas.crm.automation import (
    AutomationRuleCreate,
    AutomationRuleResponse,
    AutomationRuleUpdate,
)


router = APIRouter(prefix="/crm/automation/rules", tags=["CRM Automation"])


@router.post("", response_model=AutomationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(rule: AutomationRuleCreate, db: Session = Depends(get_db)):
    return create_record(db, CRMAutomationRule, rule)


@router.get("", response_model=List[AutomationRuleResponse])
def get_rules(db: Session = Depends(get_db)):
    return db.query(CRMAutomationRule).order_by(CRMAutomationRule.created_at.desc()).all()


@router.get("/{rule_id}", response_model=AutomationRuleResponse)
def get_rule(rule_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, CRMAutomationRule, rule_id, "Automation rule")


@router.put("/{rule_id}", response_model=AutomationRuleResponse)
def update_rule(
    rule_id: UUID,
    rule_update: AutomationRuleUpdate,
    db: Session = Depends(get_db),
):
    rule = get_or_404(db, CRMAutomationRule, rule_id, "Automation rule")
    return update_record(db, rule, rule_update)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: UUID, db: Session = Depends(get_db)):
    rule = get_or_404(db, CRMAutomationRule, rule_id, "Automation rule")
    return delete_record(db, rule)
