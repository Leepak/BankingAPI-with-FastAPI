

from typing import Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.account import Account, AccountType, AccountStatus
from app.models.customer import Customer
from app.schemas.account import AccountCreate, AccountUpdate
from app.utils.account_number import generate_account_number
from datetime import datetime


class AccountException(Exception):
    """Base exception for account operations."""
    pass


class CustomerNotFoundError(AccountException):
    """Raised when customer is not found."""
    pass


class DuplicateAccountTypeError(AccountException):
    """Raised when customer already has account of same type."""
    pass


class AccountNotFoundError(AccountException):
    """Raised when account is not found."""
    pass


class AccountAccessDeniedError(AccountException):
    """Raised when customer tries to access account they don't own."""
    pass


def _normalize_account_type(account_type: str) -> str:
    """Normalize account type to lowercase enum value."""
    account_type = account_type.lower().strip()
    if account_type == "saving":
        account_type = "savings"
    if account_type not in ["savings", "current"]:
        raise ValueError("account_type must be 'savings' or 'current'")
    return account_type


def _normalize_status(status: str) -> str:
    """Normalize status to uppercase enum value."""
    status = status.upper().strip()
    valid_statuses = ["ACTIVE", "DORMANT", "FROZEN", "BLOCKED", "CLOSED"]
    if status not in valid_statuses:
        raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
    return status


# ==================== CREATE ====================

def create_account(
    db: Session,
    account_data: AccountCreate,
    current_user_id: int
) -> Account:
    """
    Create a new account for a customer.
    """
    account_type_value = _normalize_account_type(account_data.account_type)

    customer = db.query(Customer).filter(Customer.id == account_data.customer_id).first()
    if not customer:
        raise CustomerNotFoundError(f"Customer {account_data.customer_id} not found")

    existing_account = db.query(Account).filter(
        and_(
            Account.customer_id == account_data.customer_id,
            Account.account_type == AccountType(account_type_value),
            Account.status != AccountStatus.CLOSED
        )
    ).first()

    if existing_account:
        raise DuplicateAccountTypeError(
            f"Customer already has an active {account_type_value} account"
        )

    account_number = generate_account_number(db, AccountType(account_type_value))

    db_account = Account(
        account_number=account_number,
        account_type=AccountType(account_type_value),
        currency=account_data.currency.upper() if account_data.currency else "NPR",
        status=AccountStatus.ACTIVE,
        is_active=True,
        balance=0.00,
        customer_id=account_data.customer_id,
        created_by=current_user_id,
        opened_at=datetime.utcnow()
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


# ==================== READ ====================

def get_account(db: Session, account_id: int) -> Optional[Account]:
    """Get account by ID."""
    return db.query(Account).filter(Account.id == account_id).first()


def get_accounts(
    db: Session,
    customer_id: Optional[int] = None,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Account]:
    """
    Get accounts with optional filtering and pagination.
    """
    query = db.query(Account)

    if customer_id is not None:
        query = query.filter(Account.customer_id == customer_id)

    if account_type is not None:
        normalized_type = _normalize_account_type(account_type)
        query = query.filter(Account.account_type == AccountType(normalized_type))

    if status is not None:
        normalized_status = _normalize_status(status)
        query = query.filter(Account.status == AccountStatus(normalized_status))

    return query.offset(skip).limit(limit).all()

def get_account_by_number(
    db: Session,
    account_number: str
) -> Optional[Account]:
    return (
        db.query(Account)
        .filter(Account.account_number == account_number)
        .first()
    )

def get_accounts_by_customer(
    db: Session, 
    customer_id: int,
    include_closed: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[Account]:
    """
    Get all accounts for a specific customer with pagination.
    """
    query = db.query(Account).filter(Account.customer_id == customer_id)
    
    if not include_closed:
        query = query.filter(Account.status != AccountStatus.CLOSED)
    
    return query.offset(skip).limit(limit).all()


def get_customer_account_by_id(
    db: Session,
    account_id: int,
    customer_id: int
) -> Optional[Account]:
    """
    Get a specific account if it belongs to the customer.
    """
    return db.query(Account).filter(
        Account.id == account_id,
        Account.customer_id == customer_id,
        Account.status != AccountStatus.CLOSED
    ).first()


def get_customer_account_by_number(
    db: Session,
    account_number: str,
    customer_id: int
) -> Optional[Account]:
    """
    Get account by account number if it belongs to the customer.
    """
    return db.query(Account).filter(
        Account.account_number == account_number,
        Account.customer_id == customer_id,
        Account.status != AccountStatus.CLOSED
    ).first()


def get_customer_account_by_id_or_number(
    db: Session,
    identifier: Union[int, str],
    customer_id: int
) -> Optional[Account]:
    """
    Get account by either ID or account number.
    """
    # Try as integer ID first
    if isinstance(identifier, int):
        return get_customer_account_by_id(db, identifier, customer_id)
    
    # Try as string
    if isinstance(identifier, str):
        # Try to parse as integer ID
        try:
            account_id = int(identifier)
            return get_customer_account_by_id(db, account_id, customer_id)
        except ValueError:
            # Not an integer, try as account number
            return get_customer_account_by_number(db, identifier, customer_id)
    
    return None


def get_customer_account_balance(
    db: Session,
    account_id: int,
    customer_id: int
) -> Optional[dict]:
    """
    Get account balance by ID if it belongs to the customer.
    """
    account = get_customer_account_by_id(db, account_id, customer_id)
    if not account:
        return None
    
    return {
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "currency": account.currency,
        "balance": float(account.balance),
        "status": account.status.value,
        "opened_at": account.opened_at,
        "customer_id": account.customer_id
    }


def get_customer_account_balance_by_number(
    db: Session,
    account_number: str,
    customer_id: int
) -> Optional[dict]:
    """
    Get account balance by account number if it belongs to the customer.
    """
    account = get_customer_account_by_number(db, account_number, customer_id)
    if not account:
        return None
    
    return {
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "currency": account.currency,
        "balance": float(account.balance),
        "status": account.status.value,
        "opened_at": account.opened_at,
        "customer_id": account.customer_id
    }


def get_customer_account_balance_by_id_or_number(
    db: Session,
    identifier: Union[int, str],
    customer_id: int
) -> Optional[dict]:
    """
    Get account balance by either ID or account number.
    """
    account = get_customer_account_by_id_or_number(db, identifier, customer_id)
    if not account:
        return None
    
    return {
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "currency": account.currency,
        "balance": float(account.balance),
        "status": account.status.value,
        "opened_at": account.opened_at,
        "customer_id": account.customer_id
    }


def get_customer_accounts_summary(db: Session, customer_id: int) -> dict:
    """
    Get summary of all accounts for a customer.
    """
    accounts = get_accounts_by_customer(db, customer_id, include_closed=False)
    
    total_balance = sum(account.balance for account in accounts)
    
    return {
        "customer_id": customer_id,
        "total_accounts": len(accounts),
        "total_balance": float(total_balance),
        "accounts": [
            {
                "account_id": account.id,
                "account_number": account.account_number,
                "account_type": account.account_type.value,
                "currency": account.currency,
                "balance": float(account.balance),
                "status": account.status.value,
                "opened_at": account.opened_at
            }
            for account in accounts
        ]
    }


# ==================== UPDATE ====================

def update_account(
    db: Session,
    account_id: int,
    updated_data: AccountUpdate,
    current_user_id: int
) -> Optional[Account]:
    """
    Update an account.
    """
    db_account = get_account(db, account_id)  # FIXED: was get_accounts

    if not db_account:
        return None

    if updated_data.status is not None:
        normalized_status = _normalize_status(updated_data.status)
        db_account.status = AccountStatus(normalized_status)

    if updated_data.currency is not None:
        db_account.currency = updated_data.currency.upper()

    db_account.updated_by = current_user_id
    db_account.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_account)
    return db_account


# ==================== STATUS CHANGES ====================

def close_account(
    db: Session,
    account_id: int,
    current_user_id: int
) -> Optional[Account]:
    """
    Close an account (soft close, not delete).
    """
    db_account = get_account(db, account_id)  # FIXED: was get_accounts

    if not db_account:
        return None

    if db_account.balance > 0:
        raise ValueError(f"Cannot close account with positive balance: {db_account.balance}")

    db_account.status = AccountStatus.CLOSED
    db_account.is_active = False
    db_account.closed_at = datetime.utcnow()
    db_account.updated_by = current_user_id

    db.commit()
    db.refresh(db_account)
    return db_account


def freeze_account(
    db: Session,
    account_id: int,
    current_user_id: int
) -> Optional[Account]:
    """Freeze an account."""
    db_account = get_account(db, account_id)
    if not db_account:
        return None
    
    db_account.status = AccountStatus.FROZEN
    db_account.is_active = False
    db_account.updated_by = current_user_id
    db_account.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_account)
    return db_account


def block_account(
    db: Session,
    account_id: int,
    current_user_id: int
) -> Optional[Account]:
    """Block an account."""
    db_account = get_account(db, account_id)
    if not db_account:
        return None
    
    db_account.status = AccountStatus.BLOCKED
    db_account.is_active = False
    db_account.updated_by = current_user_id
    db_account.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_account)
    return db_account


def activate_account(
    db: Session,
    account_id: int,
    current_user_id: int
) -> Optional[Account]:
    """Activate an account."""
    db_account = get_account(db, account_id)
    if not db_account:
        return None
    
    db_account.status = AccountStatus.ACTIVE
    db_account.is_active = True
    db_account.updated_by = current_user_id
    db_account.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_account)
    return db_account


# ==================== HELPER FUNCTIONS ====================

def verify_account_ownership(
    db: Session,
    account_id: int,
    customer_id: int
) -> bool:
    """
    Verify if an account belongs to a customer.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.customer_id == customer_id
    ).first()
    return account is not None


def get_account_count_by_customer(
    db: Session,
    customer_id: int,
    include_closed: bool = False
) -> int:
    """
    Get count of accounts for a customer.
    """
    query = db.query(Account).filter(Account.customer_id == customer_id)
    
    if not include_closed:
        query = query.filter(Account.status != AccountStatus.CLOSED)
    
    return query.count()


def get_active_accounts_by_customer(
    db: Session,
    customer_id: int
) -> List[Account]:
    """
    Get only active accounts for a customer.
    """
    return db.query(Account).filter(
        Account.customer_id == customer_id,
        Account.status != AccountStatus.CLOSED,
        Account.is_active == True
    ).all()


