
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.account import Account, AccountStatus
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountResponse
)
from app.crud.account import (
    create_account,
    get_account,
    get_accounts,
    get_accounts_by_customer,
    get_customer_account_by_id,
    get_customer_account_balance,
    get_customer_accounts_summary,
    update_account,
    close_account,
    CustomerNotFoundError,
    DuplicateAccountTypeError,
    AccountNotFoundError
)
from app.core.permission import is_admin, is_customer

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"]
)

# ==================== HELPER FUNCTIONS ====================

def get_customer_id_from_user(user: User) -> int:
    """Get customer ID from user object."""
    if hasattr(user, 'customer') and user.customer:
        return user.customer.id
    if hasattr(user, 'customer_id') and user.customer_id:
        return user.customer_id
    raise HTTPException(
        status_code=400,
        detail="User is not linked to a customer profile"
    )

def get_account_by_identifier(
    db: Session,
    identifier: str,
    customer_id: int
) -> Optional[Account]:
    """Get account by either ID or account number."""
    try:
        account_id = int(identifier)
        return get_customer_account_by_id(db, account_id, customer_id)
    except ValueError:
        return db.query(Account).filter(
            Account.account_number == identifier,
            Account.customer_id == customer_id,
            Account.status != AccountStatus.CLOSED
        ).first()

def format_balance_response(account: Account) -> dict:
    """Format account balance response."""
    return {
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "currency": account.currency,
        "balance": float(account.balance),
        "status": account.status.value,
        "opened_at": account.opened_at,
        "customer_id": account.customer_id
    }

# ==================== ADMIN ENDPOINTS ====================

@router.post("/", response_model=AccountResponse, status_code=201)
def create_account_endpoint(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """Create a new account (Admin only)."""
    try:
        return create_account(db, account, current_user.id)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateAccountTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/admin/all", response_model=list[AccountResponse])
def get_all_accounts_endpoint(  # <-- Renamed
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    account_type: Optional[str] = Query(None, description="Filter by account type (savings/current)"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE/DORMANT/FROZEN/BLOCKED/CLOSED)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    """Get all accounts with optional filtering (Admin only)."""
    return get_accounts(
        db,
        customer_id=customer_id,
        account_type=account_type,
        status=status,
        skip=skip,
        limit=limit
    )

@router.get("/{account_id}", response_model=AccountResponse)
def get_account_by_id_endpoint(  # <-- Renamed
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """Get account by ID (Admin only)."""
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/customer/{customer_id}", response_model=list[AccountResponse])
def get_customer_accounts_admin_endpoint(  # <-- Renamed
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin),
    include_closed: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get all accounts for a specific customer (Admin only)."""
    return get_accounts_by_customer(
        db,
        customer_id,
        include_closed=include_closed,
        skip=skip,
        limit=limit
    )

@router.patch("/{account_id}", response_model=AccountResponse)
def update_account_endpoint(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """Update account (Admin only)."""
    account = update_account(db, account_id, account_data, current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.patch("/{account_id}/close", response_model=AccountResponse)
def close_account_endpoint(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """Close account (Admin only)."""
    account = close_account(db, account_id, current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/{account_id}/balance")
def get_account_balance_admin_endpoint(  # <-- Renamed
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """Get account balance (Admin only)."""
    account = get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return format_balance_response(account)

# ==================== CUSTOMER ENDPOINTS ====================

# @router.get("/indivisual-accounts", response_model=list[AccountResponse])
# def indivisual_accounts_endpoint(  # <-- Different name
#     db: Session = Depends(get_db),
#     current_user: User = Depends(is_customer),
#     include_closed: bool = Query(False, description="Include closed accounts"),
#     skip: int = Query(0, ge=0, description="Number of records to skip"),
#     limit: int = Query(20, ge=1, le=100, description="Number of records to return")
# ):
#     """Get all accounts belonging to the authenticated customer."""
#     customer_id = get_customer_id_from_user(current_user)
#     return get_accounts_by_customer(
#         db,
#         customer_id=customer_id,
#         include_closed=include_closed,
#         skip=skip,
#         limit=limit
#     )

@router.get("/my-accounts/summary")
def get_my_accounts_summary_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(is_customer)
):
    customer_id = get_customer_id_from_user(current_user)
    return get_customer_accounts_summary(db, customer_id)




@router.get("/my-accounts/{identifier}", response_model=AccountResponse)
def get_my_account_by_identifier_endpoint(  # <-- Different name
    identifier: str = Path(
        ..., 
        description="Account ID (e.g., 1) or Account Number (e.g., SAV10000001)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_customer)
):
    """Get details of a specific account (Customer only)."""
    customer_id = get_customer_id_from_user(current_user)
    account = get_account_by_identifier(db, identifier, customer_id)
    
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found or access denied"
        )
    return account

@router.get("/my-accounts/{identifier}/balance")
def get_my_account_balance_endpoint(  # <-- Different name
    identifier: str = Path(
        ..., 
        description="Account ID (e.g., 1) or Account Number (e.g., SAV10000001)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_customer)
):
    """Get balance of a specific account (Customer only)."""
    customer_id = get_customer_id_from_user(current_user)
    account = get_account_by_identifier(db, identifier, customer_id)
    
    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found or access denied"
        )
    
    return format_balance_response(account)






