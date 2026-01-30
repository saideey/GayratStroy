"""
Settings, Audit, and Notification models.
System configuration, audit trail, and notifications.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Date,
    ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from ..base import BaseModel


class SystemSetting(BaseModel):
    """
    Key-value system settings.
    
    Examples:
    - max_discount_percent: Maximum discount sellers can give
    - sms_enabled: Whether SMS notifications are enabled
    - company_name: Company name for receipts
    """
    
    __tablename__ = 'system_settings'
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default='string')  # string, number, boolean, json
    
    # Grouping
    category = Column(String(50), nullable=True)  # general, sales, warehouse, sms, etc.
    
    # Description
    description = Column(Text, nullable=True)
    
    # Flags
    is_public = Column(Boolean, default=False)  # Can be viewed by non-admins
    is_editable = Column(Boolean, default=True)  # Can be changed
    
    __table_args__ = (
        Index('ix_settings_category', 'category'),
    )
    
    def get_typed_value(self):
        """Get value with proper type conversion."""
        if self.value is None:
            return None
        if self.value_type == 'number':
            return float(self.value)
        if self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        if self.value_type == 'json':
            import json
            return json.loads(self.value)
        return self.value


class AuditLog(BaseModel):
    """
    Audit trail for important actions.
    
    Tracks who did what and when.
    """
    
    __tablename__ = 'audit_logs'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null for system actions
    
    # Action details
    action = Column(String(50), nullable=False)  # create, update, delete, login, logout, etc.
    table_name = Column(String(100), nullable=True)
    record_id = Column(Integer, nullable=True)
    
    # Changes
    old_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values
    
    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
        Index('ix_audit_logs_action', 'action'),
        Index('ix_audit_logs_table', 'table_name'),
        Index('ix_audit_logs_record', 'table_name', 'record_id'),
        Index('ix_audit_logs_created_at', 'created_at'),
    )


class SMSTemplate(BaseModel):
    """
    SMS message templates.
    """
    
    __tablename__ = 'sms_templates'
    
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)  # sale_complete, debt_reminder, etc.
    
    # Template
    template_text = Column(Text, nullable=False)
    
    # Variables available in template
    # e.g., {customer_name}, {amount}, {debt_amount}
    variables = Column(JSON, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('ix_sms_templates_code', 'code'),
    )


class SMSLog(BaseModel):
    """
    SMS sending log.
    """
    
    __tablename__ = 'sms_logs'
    
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    
    # Message details
    phone_number = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey('sms_templates.id'), nullable=True)
    
    # Reference
    reference_type = Column(String(50), nullable=True)  # sale, debt_reminder, etc.
    reference_id = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), default='pending')  # pending, sent, delivered, failed
    error_message = Column(Text, nullable=True)
    
    # Provider response
    provider_message_id = Column(String(100), nullable=True)
    sent_at = Column(String(50), nullable=True)
    delivered_at = Column(String(50), nullable=True)
    
    # Cost
    cost = Column(String(20), nullable=True)
    
    # Relationships
    customer = relationship("Customer")
    template = relationship("SMSTemplate")
    
    __table_args__ = (
        Index('ix_sms_logs_customer_id', 'customer_id'),
        Index('ix_sms_logs_status', 'status'),
        Index('ix_sms_logs_reference', 'reference_type', 'reference_id'),
        Index('ix_sms_logs_created_at', 'created_at'),
    )


class Notification(BaseModel):
    """
    In-app notifications for users.
    """
    
    __tablename__ = 'notifications'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Notification details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # alert, info, warning, success
    
    # Priority
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Reference
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    action_url = Column(String(500), nullable=True)  # URL to navigate to
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(String(50), nullable=True)
    
    # Expiry
    expires_at = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_is_read', 'is_read'),
        Index('ix_notifications_type', 'notification_type'),
        Index('ix_notifications_created_at', 'created_at'),
    )


class StockAlert(BaseModel):
    """
    Low stock alerts.
    """
    
    __tablename__ = 'stock_alerts'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    
    # Alert details
    alert_type = Column(String(20), nullable=False)  # low_stock, out_of_stock, overstock
    current_quantity = Column(String(50), nullable=False)
    threshold_quantity = Column(String(50), nullable=False)
    
    # Status
    status = Column(String(20), default='active')  # active, acknowledged, resolved
    acknowledged_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledged_at = Column(String(50), nullable=True)
    resolved_at = Column(String(50), nullable=True)
    
    # Notification tracking
    sms_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    telegram_sent = Column(Boolean, default=False)
    
    # Relationships
    product = relationship("Product")
    warehouse = relationship("Warehouse")
    acknowledged_by = relationship("User")
    
    __table_args__ = (
        Index('ix_stock_alerts_product_id', 'product_id'),
        Index('ix_stock_alerts_warehouse_id', 'warehouse_id'),
        Index('ix_stock_alerts_status', 'status'),
        Index('ix_stock_alerts_type', 'alert_type'),
    )


class ScheduledTask(BaseModel):
    """
    Scheduled tasks for background jobs.
    """
    
    __tablename__ = 'scheduled_tasks'
    
    name = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False)  # report, backup, notification, etc.
    
    # Schedule (cron format or interval)
    schedule = Column(String(100), nullable=False)  # e.g., "0 0 * * *" for daily
    
    # Configuration
    config = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(String(50), nullable=True)
    next_run_at = Column(String(50), nullable=True)
    last_status = Column(String(20), nullable=True)  # success, failed
    last_error = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_scheduled_tasks_type', 'task_type'),
        Index('ix_scheduled_tasks_is_active', 'is_active'),
    )


class FileAttachment(BaseModel):
    """
    File attachments for various records.
    """
    
    __tablename__ = 'file_attachments'
    
    # Reference to parent record
    reference_type = Column(String(50), nullable=False)  # product, purchase_order, sale, etc.
    reference_id = Column(Integer, nullable=False)
    
    # File details
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=True)  # MIME type
    file_size = Column(Integer, nullable=True)  # Bytes
    file_url = Column(String(500), nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    
    # Uploaded by
    uploaded_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    uploaded_by = relationship("User")
    
    __table_args__ = (
        Index('ix_file_attachments_reference', 'reference_type', 'reference_id'),
        Index('ix_file_attachments_uploaded_by', 'uploaded_by_id'),
    )


class ReportExport(BaseModel):
    """
    Track exported reports.
    """
    
    __tablename__ = 'report_exports'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Report details
    report_type = Column(String(50), nullable=False)  # sales, stock, profit, etc.
    report_name = Column(String(200), nullable=False)
    
    # Parameters used
    parameters = Column(JSON, nullable=True)  # Filters, date range, etc.
    
    # File
    file_format = Column(String(20), nullable=False)  # excel, pdf, csv
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    completed_at = Column(String(50), nullable=True)
    
    # Expiry (auto-delete after)
    expires_at = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('ix_report_exports_user_id', 'user_id'),
        Index('ix_report_exports_type', 'report_type'),
        Index('ix_report_exports_status', 'status'),
    )
