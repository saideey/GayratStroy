"""
Printer and Print Queue Models
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from ..base import BaseModel, SoftDeleteMixin


class PrinterType(PyEnum):
    """Printer types."""
    THERMAL_80MM = "thermal_80mm"
    THERMAL_58MM = "thermal_58mm"
    A4 = "a4"


class ConnectionType(PyEnum):
    """Printer connection types."""
    USB = "usb"
    NETWORK = "network"
    BLUETOOTH = "bluetooth"


class PrintJobStatus(PyEnum):
    """Print job status."""
    PENDING = "pending"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Printer(BaseModel, SoftDeleteMixin):
    """
    Printer configuration.
    Each printer can be assigned to multiple users.
    """

    __tablename__ = 'printers'

    # Basic info
    name = Column(String(100), nullable=False)  # "Asosiy kassa printeri"
    description = Column(String(255), nullable=True)

    # Printer specifications
    printer_type = Column(SQLEnum(PrinterType), default=PrinterType.THERMAL_80MM)
    paper_width = Column(Integer, default=80)  # mm

    # Connection settings
    connection_type = Column(SQLEnum(ConnectionType), default=ConnectionType.USB)
    connection_address = Column(String(200), nullable=True)  # USB port name or IP

    # Location
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)

    # Agent identification
    agent_token = Column(String(100), unique=True, nullable=True)  # Token for print agent auth

    # Status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)  # Updated by print agent
    last_seen = Column(DateTime, nullable=True)  # Last heartbeat from agent

    # Relationships
    warehouse = relationship("Warehouse")
    user_assignments = relationship("UserPrinter", back_populates="printer", cascade="all, delete-orphan")
    print_jobs = relationship("PrintJob", back_populates="printer")

    def __repr__(self):
        return f"<Printer {self.name}>"


class UserPrinter(BaseModel):
    """
    User-Printer assignment (Many-to-Many).
    A user can have multiple printers, a printer can serve multiple users.
    """

    __tablename__ = 'user_printers'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    printer_id = Column(Integer, ForeignKey('printers.id'), nullable=False)

    # Settings
    is_default = Column(Boolean, default=True)  # Default printer for this user
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="printer_assignments")
    printer = relationship("Printer", back_populates="user_assignments")

    __table_args__ = (
        UniqueConstraint('user_id', 'printer_id', name='uq_user_printer'),
        Index('ix_user_printer_user_id', 'user_id'),
        Index('ix_user_printer_printer_id', 'printer_id'),
    )


class PrintJob(BaseModel):
    """
    Print queue - stores pending print jobs.
    Print agent polls this table and prints pending jobs.
    """

    __tablename__ = 'print_jobs'

    # Target printer
    printer_id = Column(Integer, ForeignKey('printers.id'), nullable=False)

    # Source
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Who created this job

    # Job type
    job_type = Column(String(50), default='receipt')  # 'receipt', 'report', 'label'

    # Content - ESC/POS commands or structured data
    content = Column(Text, nullable=False)  # JSON format receipt data
    content_type = Column(String(50), default='json')  # 'json', 'escpos', 'text'

    # Status tracking
    status = Column(SQLEnum(PrintJobStatus), default=PrintJobStatus.PENDING)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    printed_at = Column(DateTime, nullable=True)

    # Priority (lower = higher priority)
    priority = Column(Integer, default=10)

    # Relationships
    printer = relationship("Printer", back_populates="print_jobs")
    sale = relationship("Sale")
    user = relationship("User")

    __table_args__ = (
        Index('ix_print_jobs_status', 'status'),
        Index('ix_print_jobs_printer_status', 'printer_id', 'status'),
        Index('ix_print_jobs_created', 'created_at'),
    )