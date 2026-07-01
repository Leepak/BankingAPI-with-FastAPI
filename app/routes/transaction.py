

"""
Transaction Routes - FastAPI endpoints for financial operations.

Provides REST API endpoints for:
- Deposits
- Withdrawals
- Transfers
- Transaction history with advanced filtering
- Balance inquiries
- Transaction details by ID/reference
- Recent transactions
- Transaction statistics and summaries
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from app.database import get_db
from app.core.permission import is_admin, admin_or_customer, is_customer
from app.models.transaction import TransactionType, TransactionStatus
from app.models.user import User
from app.exceptions import BankingException
from app.services.transaction_service import deposit, withdraw, transfer
from app.services.audit_service import get_user_ip_from_request
from app.schemas.transaction import (
    DepositRequest, DepositResponse,
    WithdrawRequest, WithdrawResponse,
    TransferRequest, TransferResponse,
    TransactionHistoryResponse, TransactionHistoryListResponse,
    BalanceInquiryResponse,
    TransactionSummaryResponse,
    TransactionStatisticsResponse,
    TransactionResponse
)
from app.crud.transaction import (
    get_transactions,
    get_account_transactions,
    get_transaction_by_id,
    get_transaction_by_reference,
    get_recent_transactions,
    get_transaction_summary,
    get_transaction_statistics
)
from app.crud.account import get_accounts, get_account_by_number
from app.models.account import Account

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_transaction_response(transaction) -> TransactionHistoryResponse:
    """Build a consistent transaction response object."""
    return TransactionHistoryResponse(
        id=transaction.id,
        reference_number=transaction.reference_number,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        balance_before=transaction.balance_before,
        balance_after=transaction.balance_after,
        status=transaction.status.value,
        remarks=transaction.remarks,
        created_at=transaction.created_at,
        source_account_id=transaction.source_account_id,
        destination_account_id=transaction.destination_account_id,
    )


def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> None:
    """Validate that start_date is before end_date."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date"
        )


def validate_amount_range(min_amount: Optional[Decimal], max_amount: Optional[Decimal]) -> None:
    """Validate amount range."""
    if min_amount is not None and min_amount < 0:
        raise HTTPException(
            status_code=400,
            detail="Minimum amount cannot be negative"
        )
    if max_amount is not None and max_amount < 0:
        raise HTTPException(
            status_code=400,
            detail="Maximum amount cannot be negative"
        )
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(
            status_code=400,
            detail="Minimum amount cannot be greater than maximum amount"
        )


def validate_sort_by(sort_by: Optional[str]) -> None:
    """Validate sort_by parameter."""
    allowed_fields = ["created_at", "amount", "transaction_type", "status"]
    if sort_by and sort_by not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by field. Allowed: {', '.join(allowed_fields)}"
        )


def validate_order(order: Optional[str]) -> None:
    """Validate order parameter."""
    if order and order.upper() not in ["ASC", "DESC"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be 'ASC' or 'DESC'"
        )


def get_customer_id_from_user(user: User) -> Optional[int]:
    """Get customer ID from user object."""
    if hasattr(user, 'customer') and user.customer:
        return user.customer.id
    if hasattr(user, 'customer_id') and user.customer_id:
        return user.customer_id
    return None


def verify_account_ownership(db: Session, account_number: str, customer_id: int) -> Account:
    """Verify that an account belongs to the customer."""
    account = db.query(Account).filter(
        Account.account_number == account_number,
        Account.customer_id == customer_id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this account"
        )
    return account


# ============================================================================
# DEPOSIT ENDPOINT
# ============================================================================

@router.post("/deposit", response_model=DepositResponse, status_code=201)
def deposit_endpoint(
    request: Request,
    deposit_request: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
) -> DepositResponse:
    """
    Deposit money into an account.

    **Account Status:** Must be ACTIVE or DORMANT
    **Amount:** Must be greater than 0
    **Returns:** Transaction details with new balance

    Args:
        request: HTTP request object
        deposit_request: Deposit details
        db: Database session
        current_user: Authenticated user

    Returns:
        Transaction details

    Raises:
        404: Account not found
        400: Invalid amount or account status
        403: Account is blocked or frozen
    """
    try:
        transaction = deposit(db, deposit_request, current_user.id)
        return DepositResponse(
            transaction_id=transaction.id,
            reference_number=transaction.reference_number,
            account_number=deposit_request.account_number,
            amount=transaction.amount,
            new_balance=transaction.balance_after,
            status=transaction.status.value,
            created_at=transaction.created_at
        )
    except BankingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# WITHDRAW ENDPOINT
# ============================================================================

@router.post("/withdraw", response_model=WithdrawResponse, status_code=201)
def withdraw_endpoint(
    request: Request,
    withdraw_request: WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
) -> WithdrawResponse:
    """
    Withdraw money from an account.

    **Account Status:** Must be ACTIVE
    **Amount:** Must be greater than 0
    **Balance:** Cannot go negative (overdraft prevention)
    **Returns:** Transaction details with remaining balance

    Args:
        request: HTTP request object
        withdraw_request: Withdrawal details
        db: Database session
        current_user: Authenticated user

    Returns:
        Transaction details

    Raises:
        404: Account not found
        400: Invalid amount, insufficient balance, or account status
        403: Account is not active
    """
    try:
        transaction = withdraw(db, withdraw_request, current_user.id)
        return WithdrawResponse(
            transaction_id=transaction.id,
            reference_number=transaction.reference_number,
            account_number=withdraw_request.account_number,
            withdrawn=transaction.amount,
            remaining_balance=transaction.balance_after,
            status=transaction.status.value,
            created_at=transaction.created_at
        )
    except BankingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TRANSFER ENDPOINT
# ============================================================================

@router.post("/transfer", response_model=TransferResponse, status_code=201)
def transfer_endpoint(
    request: Request,
    transfer_request: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
) -> TransferResponse:
    """
    Transfer money between two accounts.

    **Accounts:** Both must exist and be ACTIVE
    **Amount:** Must be greater than 0
    **Sender Balance:** Must have sufficient funds
    **Transaction:** Atomic operation (all-or-nothing)
    **Rollback:** Automatic rollback if any step fails

    Args:
        request: HTTP request object
        transfer_request: Transfer details
        db: Database session
        current_user: Authenticated user

    Returns:
        Transaction details

    Raises:
        404: Account not found
        400: Invalid amount, sender and receiver same, insufficient balance
        403: Accounts not active
    """
    try:
        transaction = transfer(db, transfer_request, current_user.id)
        return TransferResponse(
            transaction_id=transaction.id,
            reference_number=transaction.reference_number,
            amount=transaction.amount,
            from_account=transfer_request.from_account,
            to_account=transfer_request.to_account,
            status=transaction.status.value,
            created_at=transaction.created_at
        )
    except BankingException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# TRANSACTION HISTORY ENDPOINT (Enhanced)
# ============================================================================

@router.get("", response_model=TransactionHistoryListResponse)
def get_transactions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer),
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by type: DEPOSIT, WITHDRAWAL, TRANSFER"),
    status: Optional[TransactionStatus] = Query(None, description="Filter by status: SUCCESS, FAILED, PENDING"),
    reference: Optional[str] = Query(None, description="Filter by reference number"),
    remarks: Optional[str] = Query(None, description="Filter by remarks (partial match)"),
    min_amount: Optional[Decimal] = Query(None, description="Minimum amount filter", ge=0),
    max_amount: Optional[Decimal] = Query(None, description="Maximum amount filter", ge=0),
    start_date: Optional[datetime] = Query(None, description="Filter from start date"),
    end_date: Optional[datetime] = Query(None, description="Filter to end date"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, amount, transaction_type, status"),
    order: Optional[str] = Query("DESC", description="Sort order: ASC or DESC"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Records per page")
) -> TransactionHistoryListResponse:
    """
    Get transaction history with advanced filtering.

    **Pagination:** Supports page and page_size parameters
    **Filtering:** By account, type, status, reference, remarks, amount range, and date range
    **Sorting:** By multiple fields with ASC/DESC order

    Query Parameters:
        account_number: Optional account number to filter
        transaction_type: Optional transaction type (DEPOSIT, WITHDRAWAL, TRANSFER)
        status: Optional status (SUCCESS, FAILED, PENDING)
        reference: Optional reference number (partial match)
        remarks: Optional remarks (partial match)
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        start_date: Optional start date (ISO format)
        end_date: Optional end date (ISO format)
        sort_by: Sort field (created_at, amount, transaction_type, status)
        order: Sort order (ASC or DESC)
        page: Page number (default: 1)
        page_size: Records per page (default: 50, max: 100)

    Returns:
        List of transactions with pagination info

    Example:
        GET /transactions?account_number=SAV10000001&page=1&page_size=25
        GET /transactions?status=SUCCESS&start_date=2026-06-01&sort_by=amount&order=DESC
    """
    # Validate parameters
    validate_date_range(start_date, end_date)
    validate_amount_range(min_amount, max_amount)
    validate_sort_by(sort_by)
    validate_order(order)
    
    skip = (page - 1) * page_size

    # If user is customer, restrict to their accounts
    customer_id = None
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )

    transactions, total_count = get_transactions(
        db=db,
        account_number=account_number,
        transaction_type=transaction_type,
        status=status,
        reference=reference,
        remarks=remarks,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        customer_id=customer_id,
        skip=skip,
        limit=page_size
    )

    transaction_responses = [
        build_transaction_response(t) for t in transactions
    ]

    return TransactionHistoryListResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        transactions=transaction_responses
    )


# ============================================================================
# GET TRANSACTION BY ID
# ============================================================================

@router.get("/{transaction_id}", response_model=TransactionHistoryResponse)
def get_transaction_by_id_endpoint(
    transaction_id: int = Path(..., description="Transaction ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer)
) -> TransactionHistoryResponse:
    """
    Get a specific transaction by ID.

    Args:
        transaction_id: Transaction ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Transaction details

    Raises:
        404: Transaction not found
        403: Access denied (customer trying to access another's transaction)
    """
    transaction = get_transaction_by_id(db, transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )
    
    # If customer, verify they own the associated account
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        
        # Check if transaction belongs to customer's accounts
        account = None
        if transaction.source_account_id:
            account = db.query(Account).filter(
                Account.id == transaction.source_account_id,
                Account.customer_id == customer_id
            ).first()
        if not account and transaction.destination_account_id:
            account = db.query(Account).filter(
                Account.id == transaction.destination_account_id,
                Account.customer_id == customer_id
            ).first()
        
        if not account:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this transaction"
            )
    
    return build_transaction_response(transaction)


# ============================================================================
# GET TRANSACTION BY REFERENCE
# ============================================================================

@router.get("/reference/{reference_number}", response_model=TransactionHistoryResponse)
def get_transaction_by_reference_endpoint(
    reference_number: str = Path(..., description="Transaction reference number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer)
) -> TransactionHistoryResponse:
    """
    Get a transaction by its reference number.

    Args:
        reference_number: Transaction reference number
        db: Database session
        current_user: Authenticated user

    Returns:
        Transaction details

    Raises:
        404: Transaction not found
        403: Access denied (customer trying to access another's transaction)
    """
    transaction = get_transaction_by_reference(db, reference_number)
    
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction '{reference_number}' not found"
        )
    
    # If customer, verify they own the associated account
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        
        # Check if transaction belongs to customer's accounts
        account = None
        if transaction.source_account_id:
            account = db.query(Account).filter(
                Account.id == transaction.source_account_id,
                Account.customer_id == customer_id
            ).first()
        if not account and transaction.destination_account_id:
            account = db.query(Account).filter(
                Account.id == transaction.destination_account_id,
                Account.customer_id == customer_id
            ).first()
        
        if not account:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this transaction"
            )
    
    return build_transaction_response(transaction)


# ============================================================================
# RECENT TRANSACTIONS ENDPOINT
# ============================================================================

@router.get("/recent", response_model=List[TransactionHistoryResponse])
def get_recent_transactions_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer),
    limit: int = Query(10, ge=1, le=50, description="Number of recent transactions")
) -> List[TransactionHistoryResponse]:
    """
    Get recent transactions.

    **Purpose:** Quick view of most recent transactions
    **Returns:** Latest transactions (default: 10, max: 50)

    Args:
        db: Database session
        current_user: Authenticated user
        limit: Number of transactions to return

    Returns:
        List of recent transactions
    """
    customer_id = None
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )

    transactions = get_recent_transactions(
        db=db,
        customer_id=customer_id,
        limit=limit
    )
    
    return [build_transaction_response(t) for t in transactions]


# ============================================================================
# TRANSACTION SUMMARY ENDPOINT
# ============================================================================

@router.get("/summary", response_model=TransactionSummaryResponse)
def get_transaction_summary_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer),
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary")
) -> TransactionSummaryResponse:
    """
    Get transaction summary.

    **Purpose:** Overview of transaction activity
    **Returns:** Total count, total amounts, breakdown by type and status

    Args:
        db: Database session
        current_user: Authenticated user
        account_number: Optional account number filter
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Transaction summary statistics
    """
    validate_date_range(start_date, end_date)
    
    customer_id = None
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        
        # If customer, they can only view their own account
        if account_number:
            account = verify_account_ownership(db, account_number, customer_id)

    summary = get_transaction_summary(
        db=db,
        account_number=account_number,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return TransactionSummaryResponse(**summary)


# ============================================================================
# TRANSACTION STATISTICS ENDPOINT
# ============================================================================

@router.get("/statistics", response_model=TransactionStatisticsResponse)
def get_transaction_statistics_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer),
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    period: str = Query("month", description="Period: day, week, month, year"),
    start_date: Optional[datetime] = Query(None, description="Start date for statistics"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics")
) -> TransactionStatisticsResponse:
    """
    Get transaction statistics.

    **Purpose:** Detailed transaction analytics
    **Returns:** Daily/weekly/monthly trends, top accounts, peak times

    Args:
        db: Database session
        current_user: Authenticated user
        account_number: Optional account number filter
        period: Aggregation period (day, week, month, year)
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        Transaction statistics and trends
    """
    validate_date_range(start_date, end_date)
    
    valid_periods = ["day", "week", "month", "year"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    customer_id = None
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        
        if account_number:
            verify_account_ownership(db, account_number, customer_id)

    statistics = get_transaction_statistics(
        db=db,
        account_number=account_number,
        customer_id=customer_id,
        period=period,
        start_date=start_date,
        end_date=end_date
    )
    
    return TransactionStatisticsResponse(**statistics)


# ============================================================================
# BALANCE INQUIRY ENDPOINT
# ============================================================================

@router.get("/balance/{account_number}", response_model=BalanceInquiryResponse)
def get_balance_endpoint(
    account_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer)
) -> BalanceInquiryResponse:
    """
    Get account balance and status.

    **Purpose:** Quick balance inquiry for an account
    **Returns:** Current balance, currency, and account status

    Args:
        account_number: Account number
        db: Database session
        current_user: Authenticated user

    Returns:
        Account balance and status

    Raises:
        404: Account not found
        403: Access denied (customer trying to access another's account)
    """
    account = db.query(Account).filter(
        Account.account_number == account_number
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_number}' not found"
        )

    # If customer, verify ownership
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        if account.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this account"
            )

    return BalanceInquiryResponse(
        account_number=account.account_number,
        balance=account.balance,
        currency=account.currency,
        status=account.status.value,
        is_active=account.is_active,
        account_type=account.account_type.value
    )


# ============================================================================
# ACCOUNT TRANSACTION HISTORY ENDPOINT
# ============================================================================

@router.get("/account/{account_number}", response_model=TransactionHistoryListResponse)
def get_account_history_endpoint(
    account_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_customer),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
) -> TransactionHistoryListResponse:
    """
    Get transaction history for a specific account.

    **Purpose:** View all transactions for an account
    **Pagination:** Supported with page and page_size
    **Returns:** All transactions (deposits, withdrawals, transfers)

    Args:
        account_number: Account number
        db: Database session
        current_user: Authenticated user
        page: Page number
        page_size: Records per page

    Returns:
        List of transactions for the account

    Raises:
        404: Account not found
        403: Access denied (customer trying to access another's account)
    """
    account = db.query(Account).filter(
        Account.account_number == account_number
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_number}' not found"
        )

    # If customer, verify ownership
    if current_user.role.value == "CUSTOMER":
        customer_id = get_customer_id_from_user(current_user)
        if not customer_id:
            raise HTTPException(
                status_code=400,
                detail="User is not linked to a customer profile"
            )
        if account.customer_id != customer_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this account"
            )

    skip = (page - 1) * page_size

    transactions, total_count = get_account_transactions(
        db=db,
        account_id=account.id,
        skip=skip,
        limit=page_size
    )

    transaction_responses = [
        build_transaction_response(t) for t in transactions
    ]

    return TransactionHistoryListResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        transactions=transaction_responses
    )


