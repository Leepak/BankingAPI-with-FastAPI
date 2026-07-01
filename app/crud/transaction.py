"""
Transaction CRUD - Database operations for transactions.

Handles querying and filtering transactions from the database.
"""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from typing import Optional, List, Tuple

def get_transaction_by_id(
    db: Session,
    transaction_id: int
) -> Optional[Transaction]:
    """
    Return transaction by primary key.
    """
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )


def get_transaction_by_reference(
    db: Session,
    reference_number: str
) -> Optional[Transaction]:
    """
    Return transaction by reference number.
    """
    return (
        db.query(Transaction)
        .filter(Transaction.reference_number == reference_number)
        .first()
    )


# =============================================================================
# TRANSACTION LIST (UPDATED WITH customer_id)
# =============================================================================

def get_transactions(
    db: Session,
    *,
    account_number: Optional[str] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    reference: Optional[str] = None,
    remarks: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    customer_id: Optional[int] = None,  # <-- ADD THIS
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:
    """
    Get transactions using advanced filtering.

    Supports

    - account number
    - transaction type
    - status
    - reference
    - remarks search
    - amount range
    - date range
    - sorting
    - pagination
    - customer_id filter
    """

    query = db.query(Transaction)

    filters = []

    # -------------------------------------------------------------------------
    # Account filter
    # -------------------------------------------------------------------------

    if account_number:

        account = (
            db.query(Account)
            .filter(Account.account_number == account_number)
            .first()
        )

        if not account:
            return [], 0

        filters.append(
            or_(
                Transaction.source_account_id == account.id,
                Transaction.destination_account_id == account.id
            )
        )

    # -------------------------------------------------------------------------
    # Customer filter (ADD THIS)
    # -------------------------------------------------------------------------

    if customer_id:
        # Get customer's account IDs
        customer_accounts = (
            db.query(Account.id)
            .filter(Account.customer_id == customer_id)
            .subquery()
        )
        filters.append(
            or_(
                Transaction.source_account_id.in_(customer_accounts),
                Transaction.destination_account_id.in_(customer_accounts)
            )
        )

    # -------------------------------------------------------------------------
    # Transaction Type
    # -------------------------------------------------------------------------

    if transaction_type:

        transaction_type = transaction_type.upper()

        try:
            filters.append(
                Transaction.transaction_type ==
                TransactionType(transaction_type)
            )
        except ValueError:
            return [], 0

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    if status:

        status = status.upper()

        try:
            filters.append(
                Transaction.status ==
                TransactionStatus(status)
            )
        except ValueError:
            return [], 0

    # -------------------------------------------------------------------------
    # Reference Search
    # -------------------------------------------------------------------------

    if reference:

        filters.append(
            Transaction.reference_number.ilike(
                f"%{reference}%"
            )
        )

    # -------------------------------------------------------------------------
    # Remarks Search
    # -------------------------------------------------------------------------

    if remarks:

        filters.append(
            Transaction.remarks.ilike(
                f"%{remarks}%"
            )
        )

    # -------------------------------------------------------------------------
    # Amount Filters
    # -------------------------------------------------------------------------

    if min_amount is not None:

        filters.append(
            Transaction.amount >= min_amount
        )

    if max_amount is not None:

        filters.append(
            Transaction.amount <= max_amount
        )

    # -------------------------------------------------------------------------
    # Date Filters
    # -------------------------------------------------------------------------

    if start_date:

        filters.append(
            Transaction.created_at >= start_date
        )

    if end_date:

        filters.append(
            Transaction.created_at <= end_date
        )

    # -------------------------------------------------------------------------
    # Apply Filters
    # -------------------------------------------------------------------------

    if filters:

        query = query.filter(*filters)

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    sortable_columns = {
        "created_at": Transaction.created_at,
        "amount": Transaction.amount,
        "reference": Transaction.reference_number,
        "transaction_type": Transaction.transaction_type,
        "status": Transaction.status,
    }

    sort_column = sortable_columns.get(
        sort_by,
        Transaction.created_at
    )

    if order.lower() == "asc":

        query = query.order_by(
            asc(sort_column)
        )

    else:

        query = query.order_by(
            desc(sort_column)
        )

    # -------------------------------------------------------------------------
    # Count
    # -------------------------------------------------------------------------

    total = query.count()

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------

    transactions = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transactions, total


# =============================================================================
# ACCOUNT TRANSACTIONS
# =============================================================================

def get_account_transactions(
    db: Session,
    account_id: int,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:
    """
    Return all transactions belonging to an account.

    Includes

    - Deposits
    - Withdrawals
    - Transfers (incoming & outgoing)
    """

    query = db.query(Transaction)

    filters = [
        or_(
            Transaction.source_account_id == account_id,
            Transaction.destination_account_id == account_id
        )
    ]

    if transaction_type:
        try:
            filters.append(
                Transaction.transaction_type ==
                TransactionType(transaction_type.upper())
            )
        except ValueError:
            return [], 0

    if status:
        try:
            filters.append(
                Transaction.status ==
                TransactionStatus(status.upper())
            )
        except ValueError:
            return [], 0

    if start_date:
        filters.append(
            Transaction.created_at >= start_date
        )

    if end_date:
        filters.append(
            Transaction.created_at <= end_date
        )

    if min_amount is not None:
        filters.append(
            Transaction.amount >= min_amount
        )

    if max_amount is not None:
        filters.append(
            Transaction.amount <= max_amount
        )

    query = query.filter(*filters)

    total = query.count()

    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transactions, total


# =============================================================================
# DEPOSITS
# =============================================================================

def get_deposit_transactions(
    db: Session,
    account_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:

    return get_account_transactions(
        db=db,
        account_id=account_id,
        transaction_type=TransactionType.DEPOSIT.value,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# WITHDRAWALS
# =============================================================================

def get_withdrawal_transactions(
    db: Session,
    account_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:

    return get_account_transactions(
        db=db,
        account_id=account_id,
        transaction_type=TransactionType.WITHDRAWAL.value,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# TRANSFERS
# =============================================================================

def get_transfer_transactions(
    db: Session,
    account_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:

    return get_account_transactions(
        db=db,
        account_id=account_id,
        transaction_type=TransactionType.TRANSFER.value,
        skip=skip,
        limit=limit,
    )


# =============================================================================
# RECENT TRANSACTIONS (UPDATED WITH customer_id)
# =============================================================================

def get_recent_transactions(
    db: Session,
    customer_id: Optional[int] = None,  # <-- ADD THIS
    limit: int = 10
) -> List[Transaction]:
    """
    Dashboard helper.

    Returns latest successful transactions.
    """

    query = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.SUCCESS
    )

    # Filter by customer
    if customer_id:
        customer_accounts = (
            db.query(Account.id)
            .filter(Account.customer_id == customer_id)
            .subquery()
        )
        query = query.filter(
            or_(
                Transaction.source_account_id.in_(customer_accounts),
                Transaction.destination_account_id.in_(customer_accounts)
            )
        )

    return (
        query
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


# =============================================================================
# CUSTOMER TRANSACTIONS
# =============================================================================

def get_transactions_by_customer(
    db: Session,
    customer_id: int,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Transaction], int]:
    """
    Returns all transactions for every account owned by a customer.
    """

    account_ids = (
        db.query(Account.id)
        .filter(Account.customer_id == customer_id)
        .all()
    )

    account_ids = [row[0] for row in account_ids]

    if not account_ids:
        return [], 0

    query = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.source_account_id.in_(account_ids),
                Transaction.destination_account_id.in_(account_ids)
            )
        )
    )

    total = query.count()

    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transactions, total


# =============================================================================
# TRANSACTION SUMMARY (UPDATED WITH customer_id)
# =============================================================================

def get_transaction_summary(
    db: Session,
    account_number: Optional[str] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """
    Returns transaction summary for dashboard.
    """

    query = db.query(Transaction)

    filters = []

    # Filter by account
    if account_number:
        account = db.query(Account).filter(Account.account_number == account_number).first()
        if account:
            filters.append(
                or_(
                    Transaction.source_account_id == account.id,
                    Transaction.destination_account_id == account.id
                )
            )
        else:
            return {
                "total_transactions": 0,
                "deposits": 0,
                "withdrawals": 0,
                "transfers": 0,
                "successful": 0,
                "failed": 0,
                "pending": 0,
                "reversed": 0,
            }

    # Filter by customer
    if customer_id:
        customer_accounts = (
            db.query(Account.id)
            .filter(Account.customer_id == customer_id)
            .subquery()
        )
        filters.append(
            or_(
                Transaction.source_account_id.in_(customer_accounts),
                Transaction.destination_account_id.in_(customer_accounts)
            )
        )

    # Filter by date range
    if start_date:
        filters.append(Transaction.created_at >= start_date)
    if end_date:
        filters.append(Transaction.created_at <= end_date)

    if filters:
        query = query.filter(*filters)

    total = query.count()

    deposits = query.filter(Transaction.transaction_type == TransactionType.DEPOSIT).count()
    withdrawals = query.filter(Transaction.transaction_type == TransactionType.WITHDRAWAL).count()
    transfers = query.filter(Transaction.transaction_type == TransactionType.TRANSFER).count()

    successful = query.filter(Transaction.status == TransactionStatus.SUCCESS).count()
    failed = query.filter(Transaction.status == TransactionStatus.FAILED).count()
    pending = query.filter(Transaction.status == TransactionStatus.PENDING).count()
    reversed_transactions = query.filter(Transaction.status == TransactionStatus.REVERSED).count()

    return {
        "total_transactions": total,
        "deposits": deposits,
        "withdrawals": withdrawals,
        "transfers": transfers,
        "successful": successful,
        "failed": failed,
        "pending": pending,
        "reversed": reversed_transactions,
        "start_date": start_date,
        "end_date": end_date,
    }


# =============================================================================
# TRANSACTION STATISTICS (UPDATED)
# =============================================================================

def get_transaction_statistics(
    db: Session,
    account_number: Optional[str] = None,
    customer_id: Optional[int] = None,
    period: str = "month",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """
    Returns transaction statistics for dashboard.
    """

    query = db.query(Transaction)

    filters = []

    # Filter by account
    if account_number:
        account = db.query(Account).filter(Account.account_number == account_number).first()
        if account:
            filters.append(
                or_(
                    Transaction.source_account_id == account.id,
                    Transaction.destination_account_id == account.id
                )
            )
        else:
            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_amount": 0,
                "average_amount": 0,
                "largest_transaction": 0,
                "smallest_transaction": 0,
                "today_transactions": 0,
                "today_successful": 0,
                "today_failed": 0,
            }

    # Filter by customer
    if customer_id:
        customer_accounts = (
            db.query(Account.id)
            .filter(Account.customer_id == customer_id)
            .subquery()
        )
        filters.append(
            or_(
                Transaction.source_account_id.in_(customer_accounts),
                Transaction.destination_account_id.in_(customer_accounts)
            )
        )

    # Filter by date range
    if start_date:
        filters.append(Transaction.created_at >= start_date)
    if end_date:
        filters.append(Transaction.created_at <= end_date)

    if filters:
        query = query.filter(*filters)

    # Statistics
    total_amount = query.with_entities(func.coalesce(func.sum(Transaction.amount), 0)).scalar() or Decimal('0.00')
    average_amount = query.with_entities(func.coalesce(func.avg(Transaction.amount), 0)).scalar() or Decimal('0.00')

    largest_transaction = query.order_by(Transaction.amount.desc()).first()
    smallest_transaction = query.order_by(Transaction.amount.asc()).first()

    today = datetime.utcnow().date()

    today_transactions = query.filter(func.date(Transaction.created_at) == today).count()
    successful_today = query.filter(
        func.date(Transaction.created_at) == today,
        Transaction.status == TransactionStatus.SUCCESS
    ).count()
    failed_today = query.filter(
        func.date(Transaction.created_at) == today,
        Transaction.status == TransactionStatus.FAILED
    ).count()

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_amount": total_amount,
        "average_amount": average_amount,
        "largest_transaction": largest_transaction.amount if largest_transaction else Decimal('0.00'),
        "smallest_transaction": smallest_transaction.amount if smallest_transaction else Decimal('0.00'),
        "today_transactions": today_transactions,
        "today_successful": successful_today,
        "today_failed": failed_today,
    }


# =============================================================================
# DAILY TRANSACTIONS
# =============================================================================

def get_daily_transactions(
    db: Session,
    transaction_date: date
) -> List[Transaction]:
    """
    Get all transactions for a specific date.
    """

    return (
        db.query(Transaction)
        .filter(
            func.date(Transaction.created_at) == transaction_date
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )


# =============================================================================
# MONTHLY TRANSACTIONS
# =============================================================================

def get_monthly_transactions(
    db: Session,
    year: int,
    month: int,
) -> List[Transaction]:
    """
    Get all transactions for a month.
    """

    return (
        db.query(Transaction)
        .filter(
            func.extract("year", Transaction.created_at) == year,
            func.extract("month", Transaction.created_at) == month,
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )


# =============================================================================
# DATE RANGE
# =============================================================================

def get_transactions_between_dates(
    db: Session,
    start_date: datetime,
    end_date: datetime,
) -> List[Transaction]:
    """
    Used by reports.
    """

    return (
        db.query(Transaction)
        .filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
        )
        .order_by(Transaction.created_at.desc())
        .all()
    )


# =============================================================================
# ACCOUNT STATEMENT
# =============================================================================

def get_account_statement(
    db: Session,
    account_id: int,
    start_date: datetime,
    end_date: datetime,
) -> List[Transaction]:
    """
    Returns transactions used to generate account statements.
    """

    return (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.source_account_id == account_id,
                Transaction.destination_account_id == account_id,
            ),
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == TransactionStatus.SUCCESS,
        )
        .order_by(Transaction.created_at.asc())
        .all()
    )


# =============================================================================
# TOTAL TRANSACTION AMOUNT
# =============================================================================

def get_total_transaction_amount(db: Session) -> Decimal:
    """
    Returns total amount processed.
    """

    amount = (
        db.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        )
        .scalar()
    )

    return amount or Decimal('0.00')


# =============================================================================
# TRANSACTION COUNT
# =============================================================================

def get_total_transaction_count(db: Session) -> int:
    """
    Returns total transaction count.
    """

    return db.query(Transaction).count()


# =============================================================================
# SUCCESS RATE
# =============================================================================

def get_transaction_success_rate(db: Session) -> float:
    """
    Returns success percentage.
    """

    total = db.query(Transaction).count()

    if total == 0:
        return 0

    success = (
        db.query(Transaction)
        .filter(
            Transaction.status == TransactionStatus.SUCCESS
        )
        .count()
    )

    return round((success / total) * 100, 2)


# =============================================================================
# FAILED TRANSACTIONS
# =============================================================================

def get_failed_transactions(
    db: Session,
    limit: int = 100,
) -> List[Transaction]:

    return (
        db.query(Transaction)
        .filter(
            Transaction.status == TransactionStatus.FAILED
        )
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


# =============================================================================
# PENDING TRANSACTIONS
# =============================================================================

def get_pending_transactions(
    db: Session,
    limit: int = 100,
) -> List[Transaction]:

    return (
        db.query(Transaction)
        .filter(
            Transaction.status == TransactionStatus.PENDING
        )
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )


# =============================================================================
# REVERSED TRANSACTIONS
# =============================================================================

def get_reversed_transactions(
    db: Session,
    limit: int = 100,
) -> List[Transaction]:

    return (
        db.query(Transaction)
        .filter(
            Transaction.status == TransactionStatus.REVERSED
        )
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )