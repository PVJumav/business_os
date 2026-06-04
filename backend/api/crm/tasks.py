from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.api.crm.v6_workflows import _active_employee, _employee_name
from backend.models.crm import CRMTask
from backend.schemas.crm.tasks import TaskCreate, TaskUpdate, TaskResponse


router = APIRouter(prefix="/crm/tasks", tags=["CRM Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = CRMTask(**task.model_dump())
    if new_task.assigned_employee_id:
        assignee = _active_employee(db, new_task.assigned_employee_id)
        new_task.assigned_to = _employee_name(assignee)
    if new_task.owner_employee_id:
        _active_employee(db, new_task.owner_employee_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("", response_model=List[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    return db.query(CRMTask).order_by(CRMTask.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    if update_data.get("assigned_employee_id"):
        assignee = _active_employee(db, update_data["assigned_employee_id"])
        update_data["assigned_to"] = _employee_name(assignee)
    if update_data.get("owner_employee_id"):
        _active_employee(db, update_data["owner_employee_id"])

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(CRMTask).filter(CRMTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"status": "success", "message": "Task deleted successfully"}
