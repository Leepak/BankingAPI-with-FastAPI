"""
AuditLog Model - Records all system actions for compliance and debugging.

Tracks:
- Account operations (creation, update, closure)
- Transaction operations (deposit, withdraw, transfer)
- Customer operations
- User actions
"""
from sqlalchemy import Column, Integer, String, DateTime, func, Text, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AuditAction(str, enum.Enum):
    """Types of audit events."""
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"


class AuditLog(Base):
    """
    AuditLog Model.

    Comprehensive audit trail for all system actions. Used for:
    - Compliance and regulatory requirements
    - Debugging and troubleshooting
    - Security monitoring
    - Accountability tracking
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Action performed
    action = Column(
        String(50),
        nullable=False,
        index=True
    )

    # Type of entity affected (ACCOUNT, CUSTOMER, USER, TRANSACTION)
    entity_type = Column(String(50), nullable=False, index=True)

    # ID of the entity affected
    entity_id = Column(Integer, nullable=False, index=True)

    # Previous value (JSON serialized)
    old_value = Column(Text, nullable=True)

    # New value (JSON serialized)
    new_value = Column(Text, nullable=True)

    # User who performed the action
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # IP address of the request (for security)
    ip_address = Column(String(45), nullable=True)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationship
    user = relationship("User", foreign_keys=[performed_by], viewonly=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_user', 'performed_by'),
        Index('idx_audit_logs_created_at', 'created_at'),
    )
