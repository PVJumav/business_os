from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.models.hrm import HRMAttendance
from backend.schemas.hrm.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse


router = APIRouter(prefix="/hrm/attendance", tags=["HRM Attendance"])


@router.post("", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(attendance: AttendanceCreate, db: Session = Depends(get_db)):
    new_attendance = HRMAttendance(**attendance.model_dump())
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return new_attendance


@router.get("", response_model=List[AttendanceResponse])
def get_attendance_records(db: Session = Depends(get_db)):
    return db.query(HRMAttendance).order_by(HRMAttendance.created_at.desc()).all()


@router.get("/{attendance_id}", response_model=AttendanceResponse)
def get_attendance(attendance_id: UUID, db: Session = Depends(get_db)):
    attendance = db.query(HRMAttendance).filter(HRMAttendance.id == attendance_id).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    return attendance


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(attendance_id: UUID, attendance_update: AttendanceUpdate, db: Session = Depends(get_db)):
    attendance = db.query(HRMAttendance).filter(HRMAttendance.id == attendance_id).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    for field, value in attendance_update.model_dump(exclude_unset=True).items():
        setattr(attendance, field, value)

    db.commit()
    db.refresh(attendance)
    return attendance


@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: UUID, db: Session = Depends(get_db)):
    attendance = db.query(HRMAttendance).filter(HRMAttendance.id == attendance_id).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(attendance)
    db.commit()

    return {"status": "success", "message": "Attendance record deleted successfully"}