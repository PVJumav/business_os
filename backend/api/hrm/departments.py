from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.api.crud import create_record, delete_record, get_or_404, update_record
from backend.core.database import get_db
from backend.models.hrm import HRMDepartment
from backend.schemas.hrm.departments import DepartmentCreate, DepartmentResponse, DepartmentUpdate


router = APIRouter(prefix="/hrm/departments", tags=["HRM Departments"])


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    return create_record(db, HRMDepartment, department)


@router.get("", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(HRMDepartment).order_by(HRMDepartment.name.asc()).all()


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: UUID, db: Session = Depends(get_db)):
    return get_or_404(db, HRMDepartment, department_id, "Department")


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: UUID,
    department_update: DepartmentUpdate,
    db: Session = Depends(get_db),
):
    department = get_or_404(db, HRMDepartment, department_id, "Department")
    return update_record(db, department, department_update)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: UUID, db: Session = Depends(get_db)):
    department = get_or_404(db, HRMDepartment, department_id, "Department")
    return delete_record(db, department)
