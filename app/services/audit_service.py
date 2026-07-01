"""
Audit Logging Service - Reusable helper for creating audit logs.

Provides centralized audit logging functionality for all system actions.
"""
import json
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog, AuditAction
from typing import Any, Optional


def create_audit_log(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    performed_by: int,
    old_value: Optional[Any] = None,
    new_value: Optional[Any] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Create an audit log entry for system actions.

    Args:
        db: Database session
        action: Action performed (e.g., DEPOSIT, WITHDRAW)
        entity_type: Type of entity affected (ACCOUNT, CUSTOMER, etc.)
        entity_id: ID of the entity affected
        performed_by: User ID who performed the action
        old_value: Previous value (optional)
        new_value: New value (optional)
        ip_address: IP address of the request (optional)

    Returns:
        Created AuditLog entry

    Example:
        create_audit_log(
            db=db,
            action="DEPOSIT",
            entity_type="ACCOUNT",
            entity_id=1,
            performed_by=5,
            old_value={"balance": 1000},
            new_value={"balance": 2000},
            ip_address="192.168.1.1"
        )
    """
    # Convert values to JSON strings if provided
    old_value_str = json.dumps(old_value) if old_value else None
    new_value_str = json.dumps(new_value) if new_value else None

    audit_log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value_str,
        new_value=new_value_str,
        performed_by=performed_by,
        ip_address=ip_address
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_user_ip_from_request(request) -> str:
    """
    Extract IP address from FastAPI request.

    Handles proxies and load balancers by checking X-Forwarded-For header.

    Args:
        request: FastAPI request object

    Returns:
        IP address string
    """
    # Check for forwarded IP (from proxy/load balancer)
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for").split(",")[0].strip()

    # Fall back to client IP
    return request.client.host if request.client else "unknown"
