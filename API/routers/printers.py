"""
Printers Router - Printer management and print queue API.
"""
import secrets
import json
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel

from database import get_db
from database.models import User, PermissionType
from database.models.printer import Printer, UserPrinter, PrintJob, PrinterType, ConnectionType, PrintJobStatus
from core.dependencies import get_current_active_user, PermissionChecker


router = APIRouter()


# ==================== SCHEMAS ====================

class PrinterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    printer_type: str = "thermal_80mm"
    paper_width: int = 80
    connection_type: str = "usb"
    connection_address: Optional[str] = None
    warehouse_id: Optional[int] = None


class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    printer_type: Optional[str] = None
    paper_width: Optional[int] = None
    connection_type: Optional[str] = None
    connection_address: Optional[str] = None
    warehouse_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserPrinterAssign(BaseModel):
    user_id: int
    printer_id: int
    is_default: bool = True


class PrintJobCreate(BaseModel):
    printer_id: int
    sale_id: Optional[int] = None
    job_type: str = "receipt"
    content: str  # JSON string
    priority: int = 10


# ==================== PRINTER ENDPOINTS ====================

@router.get(
    "",
    summary="Barcha printerlar",
)
async def get_printers(
    warehouse_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all printers."""
    query = db.query(Printer).filter(Printer.is_deleted == False)

    if warehouse_id:
        query = query.filter(Printer.warehouse_id == warehouse_id)

    if is_active is not None:
        query = query.filter(Printer.is_active == is_active)

    printers = query.order_by(Printer.name).all()

    return {
        "success": True,
        "data": [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "printer_type": p.printer_type.value if p.printer_type else None,
            "paper_width": p.paper_width,
            "connection_type": p.connection_type.value if p.connection_type else None,
            "connection_address": p.connection_address,
            "warehouse_id": p.warehouse_id,
            "warehouse_name": p.warehouse.name if p.warehouse else None,
            "is_active": p.is_active,
            "is_online": p.is_online,
            "last_seen": p.last_seen.isoformat() if p.last_seen else None,
            "agent_token": p.agent_token,  # Only admin should see this
            "assigned_users": [{
                "user_id": ua.user_id,
                "user_name": f"{ua.user.first_name} {ua.user.last_name}",
                "is_default": ua.is_default
            } for ua in p.user_assignments if ua.is_active]
        } for p in printers]
    }


@router.post(
    "",
    summary="Yangi printer qo'shish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def create_printer(
    data: PrinterCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new printer."""
    # Generate unique agent token
    agent_token = secrets.token_urlsafe(32)

    printer = Printer(
        name=data.name,
        description=data.description,
        printer_type=PrinterType(data.printer_type),
        paper_width=data.paper_width,
        connection_type=ConnectionType(data.connection_type),
        connection_address=data.connection_address,
        warehouse_id=data.warehouse_id,
        agent_token=agent_token
    )

    db.add(printer)
    db.commit()
    db.refresh(printer)

    return {
        "success": True,
        "message": "Printer qo'shildi",
        "data": {
            "id": printer.id,
            "name": printer.name,
            "agent_token": printer.agent_token  # Important for print agent config
        }
    }


@router.put(
    "/{printer_id}",
    summary="Printerni tahrirlash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def update_printer(
    printer_id: int,
    data: PrinterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update printer."""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.is_deleted == False
    ).first()

    if not printer:
        raise HTTPException(status_code=404, detail="Printer topilmadi")

    if data.name is not None:
        printer.name = data.name
    if data.description is not None:
        printer.description = data.description
    if data.printer_type is not None:
        printer.printer_type = PrinterType(data.printer_type)
    if data.paper_width is not None:
        printer.paper_width = data.paper_width
    if data.connection_type is not None:
        printer.connection_type = ConnectionType(data.connection_type)
    if data.connection_address is not None:
        printer.connection_address = data.connection_address
    if data.warehouse_id is not None:
        printer.warehouse_id = data.warehouse_id
    if data.is_active is not None:
        printer.is_active = data.is_active

    db.commit()

    return {
        "success": True,
        "message": "Printer yangilandi"
    }


@router.delete(
    "/{printer_id}",
    summary="Printerni o'chirish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def delete_printer(
    printer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete printer (soft delete)."""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.is_deleted == False
    ).first()

    if not printer:
        raise HTTPException(status_code=404, detail="Printer topilmadi")

    printer.is_deleted = True
    printer.is_active = False
    db.commit()

    return {
        "success": True,
        "message": "Printer o'chirildi"
    }


@router.post(
    "/{printer_id}/regenerate-token",
    summary="Printer tokenini yangilash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def regenerate_printer_token(
    printer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate printer agent token."""
    printer = db.query(Printer).filter(
        Printer.id == printer_id,
        Printer.is_deleted == False
    ).first()

    if not printer:
        raise HTTPException(status_code=404, detail="Printer topilmadi")

    printer.agent_token = secrets.token_urlsafe(32)
    db.commit()

    return {
        "success": True,
        "message": "Token yangilandi",
        "data": {
            "agent_token": printer.agent_token
        }
    }


# ==================== USER-PRINTER ASSIGNMENT ====================

@router.post(
    "/assign",
    summary="Kassirga printer biriktirish",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def assign_printer_to_user(
    data: UserPrinterAssign,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign printer to user."""
    # Check if assignment already exists
    existing = db.query(UserPrinter).filter(
        UserPrinter.user_id == data.user_id,
        UserPrinter.printer_id == data.printer_id
    ).first()

    if existing:
        existing.is_active = True
        existing.is_default = data.is_default
    else:
        assignment = UserPrinter(
            user_id=data.user_id,
            printer_id=data.printer_id,
            is_default=data.is_default
        )
        db.add(assignment)

    # If this is default, remove default from other printers for this user
    if data.is_default:
        db.query(UserPrinter).filter(
            UserPrinter.user_id == data.user_id,
            UserPrinter.printer_id != data.printer_id
        ).update({"is_default": False})

    db.commit()

    return {
        "success": True,
        "message": "Printer biriktirildi"
    }


@router.delete(
    "/assign/{user_id}/{printer_id}",
    summary="Kassirdan printerni olib tashlash",
    dependencies=[Depends(PermissionChecker([PermissionType.SETTINGS_MANAGE]))]
)
async def unassign_printer_from_user(
    user_id: int,
    printer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove printer assignment from user."""
    assignment = db.query(UserPrinter).filter(
        UserPrinter.user_id == user_id,
        UserPrinter.printer_id == printer_id
    ).first()

    if assignment:
        assignment.is_active = False
        db.commit()

    return {
        "success": True,
        "message": "Printer olib tashlandi"
    }


@router.get(
    "/user/{user_id}",
    summary="Kassirning printerlari"
)
async def get_user_printers(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get printers assigned to user."""
    assignments = db.query(UserPrinter).filter(
        UserPrinter.user_id == user_id,
        UserPrinter.is_active == True
    ).all()

    return {
        "success": True,
        "data": [{
            "printer_id": a.printer_id,
            "printer_name": a.printer.name,
            "is_default": a.is_default,
            "is_online": a.printer.is_online
        } for a in assignments if a.printer and not a.printer.is_deleted]
    }


# ==================== PRINT QUEUE ====================

@router.get(
    "/queue/pending",
    summary="Kutayotgan print ishlar (Agent uchun)"
)
async def get_pending_print_jobs(
    agent_token: str = Query(..., description="Printer agent token"),
    db: Session = Depends(get_db)
):
    """
    Get pending print jobs for a printer.
    Used by Print Agent to poll for new jobs.
    """
    # Find printer by token
    printer = db.query(Printer).filter(
        Printer.agent_token == agent_token,
        Printer.is_active == True,
        Printer.is_deleted == False
    ).first()

    if not printer:
        raise HTTPException(status_code=401, detail="Invalid agent token")

    # Update printer status
    printer.is_online = True
    printer.last_seen = datetime.now()

    # Get pending jobs
    jobs = db.query(PrintJob).filter(
        PrintJob.printer_id == printer.id,
        PrintJob.status == PrintJobStatus.PENDING
    ).order_by(PrintJob.priority, PrintJob.created_at).limit(10).all()

    db.commit()

    return {
        "success": True,
        "printer_id": printer.id,
        "printer_name": printer.name,
        "jobs": [{
            "id": j.id,
            "job_type": j.job_type,
            "content": j.content,
            "content_type": j.content_type,
            "sale_id": j.sale_id,
            "priority": j.priority,
            "created_at": j.created_at.isoformat()
        } for j in jobs]
    }


@router.post(
    "/queue/{job_id}/start",
    summary="Print ishni boshlash (Agent uchun)"
)
async def start_print_job(
    job_id: int,
    agent_token: str = Query(..., description="Printer agent token"),
    db: Session = Depends(get_db)
):
    """Mark print job as printing."""
    printer = db.query(Printer).filter(
        Printer.agent_token == agent_token,
        Printer.is_active == True
    ).first()

    if not printer:
        raise HTTPException(status_code=401, detail="Invalid agent token")

    job = db.query(PrintJob).filter(
        PrintJob.id == job_id,
        PrintJob.printer_id == printer.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = PrintJobStatus.PRINTING
    db.commit()

    return {"success": True}


@router.post(
    "/queue/{job_id}/complete",
    summary="Print ish tugadi (Agent uchun)"
)
async def complete_print_job(
    job_id: int,
    agent_token: str = Query(..., description="Printer agent token"),
    db: Session = Depends(get_db)
):
    """Mark print job as completed."""
    printer = db.query(Printer).filter(
        Printer.agent_token == agent_token,
        Printer.is_active == True
    ).first()

    if not printer:
        raise HTTPException(status_code=401, detail="Invalid agent token")

    job = db.query(PrintJob).filter(
        PrintJob.id == job_id,
        PrintJob.printer_id == printer.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = PrintJobStatus.COMPLETED
    job.printed_at = datetime.now()
    db.commit()

    return {"success": True, "message": "Print completed"}


@router.post(
    "/queue/{job_id}/fail",
    summary="Print ish muvaffaqiyatsiz (Agent uchun)"
)
async def fail_print_job(
    job_id: int,
    error_message: str = "",
    agent_token: str = Query(..., description="Printer agent token"),
    db: Session = Depends(get_db)
):
    """Mark print job as failed."""
    printer = db.query(Printer).filter(
        Printer.agent_token == agent_token,
        Printer.is_active == True
    ).first()

    if not printer:
        raise HTTPException(status_code=401, detail="Invalid agent token")

    job = db.query(PrintJob).filter(
        PrintJob.id == job_id,
        PrintJob.printer_id == printer.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.retry_count += 1
    job.error_message = error_message

    if job.retry_count >= job.max_retries:
        job.status = PrintJobStatus.FAILED
    else:
        job.status = PrintJobStatus.PENDING  # Will retry

    db.commit()

    return {"success": True, "will_retry": job.status == PrintJobStatus.PENDING}


@router.post(
    "/queue",
    summary="Yangi print job qo'shish"
)
async def create_print_job(
    data: PrintJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create new print job."""
    # Verify printer exists
    printer = db.query(Printer).filter(
        Printer.id == data.printer_id,
        Printer.is_active == True,
        Printer.is_deleted == False
    ).first()

    if not printer:
        raise HTTPException(status_code=404, detail="Printer topilmadi")

    job = PrintJob(
        printer_id=data.printer_id,
        sale_id=data.sale_id,
        user_id=current_user.id,
        job_type=data.job_type,
        content=data.content,
        content_type="json",
        priority=data.priority
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "success": True,
        "message": "Print job qo'shildi",
        "data": {
            "job_id": job.id
        }
    }


@router.get(
    "/queue/history",
    summary="Print tarixi"
)
async def get_print_history(
    printer_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get print job history."""
    query = db.query(PrintJob)

    if printer_id:
        query = query.filter(PrintJob.printer_id == printer_id)

    if status:
        query = query.filter(PrintJob.status == PrintJobStatus(status))

    total = query.count()
    jobs = query.order_by(PrintJob.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "success": True,
        "data": [{
            "id": j.id,
            "printer_name": j.printer.name if j.printer else None,
            "job_type": j.job_type,
            "status": j.status.value,
            "sale_id": j.sale_id,
            "user_name": f"{j.user.first_name} {j.user.last_name}" if j.user else None,
            "created_at": j.created_at.isoformat(),
            "printed_at": j.printed_at.isoformat() if j.printed_at else None,
            "error_message": j.error_message
        } for j in jobs],
        "total": total,
        "page": page,
        "per_page": per_page
    }