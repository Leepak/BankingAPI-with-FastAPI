"""
Transaction Service - Core business logic for all financial operations.

Handles:
- Deposits (adding money to accounts)
- Withdrawals (removing money from accounts)
- Transfers (moving money between accounts)

Key features:
- Atomic transactions (all-or-nothing)
- Row locking to prevent race conditions
- Balance validation
- Account status checking
- Comprehensive audit logging
"""
import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.models.account import Account, AccountStatus
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import (
    DepositRequest, WithdrawRequest, TransferRequest
)
from app.exceptions import (
    AccountNotFoundError,
    InsufficientBalanceError,
    InvalidAmountError,
    InactiveAccountError,
    ClosedAccountError,
    BlockedAccountError,
    FrozenAccountError,
    SameAccountTransferError,
    TransactionFailedError,
    DuplicateTransactionError
)
from app.services.audit_service import create_audit_log


def _generate_reference_number() -> str:
    """Generate a unique transaction reference number."""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def _validate_account_for_operation(
    account: Account,
    allow_status: list[AccountStatus]
) -> None:
    """
    Validate account status for transaction operations.

    Args:
        account: Account to validate
        allow_status: List of allowed statuses

    Raises:
        ClosedAccountError: If account is closed
        BlockedAccountError: If account is blocked
        FrozenAccountError: If account is frozen
        InactiveAccountError: If account status not allowed
    """
    if account.status == AccountStatus.CLOSED:
        raise ClosedAccountError(account.account_number)

    if account.status == AccountStatus.BLOCKED:
        raise BlockedAccountError(account.account_number)

    if account.status == AccountStatus.FROZEN:
        raise FrozenAccountError(account.account_number)

    if account.status not in allow_status:
        raise InactiveAccountError(account.account_number, account.status.value)


def deposit(
    db: Session,
    deposit_request: DepositRequest,
    current_user_id: int
) -> Transaction:
    """
    Process a deposit transaction.

    Adds money to an account. Account must be ACTIVE or DORMANT.

    Args:
        db: Database session
        deposit_request: Deposit request data
        current_user_id: User ID performing the deposit

    Returns:
        Created Transaction record

    Raises:
        AccountNotFoundError: If account doesn't exist
        InvalidAmountError: If amount is invalid
        ClosedAccountError: If account is closed
        BlockedAccountError: If account is blocked
        FrozenAccountError: If account is frozen
        InactiveAccountError: If account status not allowed
        TransactionFailedError: If transaction processing fails

    Example:
        deposit(
            db=db,
            deposit_request=DepositRequest(
                account_number="SAV10000001",
                amount=1000.00
            ),
            current_user_id=5
        )
    """
    # Validate amount
    if deposit_request.amount <= 0:
        raise InvalidAmountError(deposit_request.amount)

    # Get account with row lock to prevent race conditions
    account = db.query(Account).filter(
        Account.account_number == deposit_request.account_number
    ).with_for_update().first()

    if not account:
        raise AccountNotFoundError(deposit_request.account_number)

    # Validate account status - allow ACTIVE and DORMANT for deposits
    _validate_account_for_operation(
        account,
        allow_status=[AccountStatus.ACTIVE, AccountStatus.DORMANT]
    )

    # Record old balance for audit
    old_balance = account.balance

    try:
        # Add funds to account
        account.balance += deposit_request.amount
        new_balance = account.balance

        # Generate reference number
        reference_number = _generate_reference_number()

        # Create transaction record
        transaction = Transaction(
            reference_number=reference_number,
            transaction_type=TransactionType.DEPOSIT,
            amount=deposit_request.amount,
            balance_before=old_balance,
            balance_after=new_balance,
            remarks=deposit_request.remarks,
            status=TransactionStatus.SUCCESS,
            source_account_id=account.id,
            destination_account_id=None,
            created_by=current_user_id
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Create audit log
        create_audit_log(
            db=db,
            action="DEPOSIT",
            entity_type="ACCOUNT",
            entity_id=account.id,
            performed_by=current_user_id,
            old_value={"balance": float(old_balance)},
            new_value={"balance": float(new_balance)}
        )

        return transaction

    except Exception as e:
        db.rollback()
        raise TransactionFailedError(str(e))


def withdraw(
    db: Session,
    withdraw_request: WithdrawRequest,
    current_user_id: int
) -> Transaction:
    """
    Process a withdrawal transaction.

    Removes money from an account. Account must be ACTIVE.
    Prevents overdraft - balance cannot go negative.

    Args:
        db: Database session
        withdraw_request: Withdrawal request data
        current_user_id: User ID performing the withdrawal

    Returns:
        Created Transaction record

    Raises:
        AccountNotFoundError: If account doesn't exist
        InvalidAmountError: If amount is invalid
        InsufficientBalanceError: If account balance is insufficient
        ClosedAccountError: If account is closed
        BlockedAccountError: If account is blocked
        FrozenAccountError: If account is frozen
        InactiveAccountError: If account is not ACTIVE
        TransactionFailedError: If transaction processing fails

    Example:
        withdraw(
            db=db,
            withdraw_request=WithdrawRequest(
                account_number="SAV10000001",
                amount=500.00
            ),
            current_user_id=5
        )
    """
    # Validate amount
    if withdraw_request.amount <= 0:
        raise InvalidAmountError(withdraw_request.amount)

    # Get account with row lock
    account = db.query(Account).filter(
        Account.account_number == withdraw_request.account_number
    ).with_for_update().first()

    if not account:
        raise AccountNotFoundError(withdraw_request.account_number)

    # Validate account status - only ACTIVE accounts can withdraw
    _validate_account_for_operation(
        account,
        allow_status=[AccountStatus.ACTIVE]
    )

    # Check sufficient balance
    if account.balance < withdraw_request.amount:
        raise InsufficientBalanceError(account.balance, withdraw_request.amount)

    # Record old balance for audit
    old_balance = account.balance

    try:
        # Deduct funds from account
        account.balance -= withdraw_request.amount
        new_balance = account.balance

        # Generate reference number
        reference_number = _generate_reference_number()

        # Create transaction record
        transaction = Transaction(
            reference_number=reference_number,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=withdraw_request.amount,
            balance_before=old_balance,
            balance_after=new_balance,
            remarks=withdraw_request.remarks,
            status=TransactionStatus.SUCCESS,
            source_account_id=account.id,
            destination_account_id=None,
            created_by=current_user_id
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Create audit log
        create_audit_log(
            db=db,
            action="WITHDRAWAL",
            entity_type="ACCOUNT",
            entity_id=account.id,
            performed_by=current_user_id,
            old_value={"balance": float(old_balance)},
            new_value={"balance": float(new_balance)}
        )

        return transaction

    except Exception as e:
        db.rollback()
        raise TransactionFailedError(str(e))


def transfer(
    db: Session,
    transfer_request: TransferRequest,
    current_user_id: int
) -> Transaction:
    """
    Process an internal account-to-account transfer.

    Transfers money from one account to another. Both accounts must be ACTIVE.
    Uses atomic transaction - all-or-nothing operation.

    Args:
        db: Database session
        transfer_request: Transfer request data
        current_user_id: User ID performing the transfer

    Returns:
        Created Transaction record

    Raises:
        AccountNotFoundError: If either account doesn't exist
        InvalidAmountError: If amount is invalid
        SameAccountTransferError: If sender and receiver are same
        InsufficientBalanceError: If sender doesn't have enough balance
        InactiveAccountError: If either account is not ACTIVE
        TransactionFailedError: If transaction processing fails

    Example:
        transfer(
            db=db,
            transfer_request=TransferRequest(
                from_account="SAV10000001",
                to_account="CUR10000001",
                amount=1000.00
            ),
            current_user_id=5
        )
    """
    # Validate amount
    if transfer_request.amount <= 0:
        raise InvalidAmountError(transfer_request.amount)

    # Prevent self-transfer
    if transfer_request.from_account == transfer_request.to_account:
        raise SameAccountTransferError()

    try:
        # Get sender account with row lock
        sender = db.query(Account).filter(
            Account.account_number == transfer_request.from_account
        ).with_for_update().first()

        if not sender:
            raise AccountNotFoundError(transfer_request.from_account)

        # Get receiver account with row lock
        receiver = db.query(Account).filter(
            Account.account_number == transfer_request.to_account
        ).with_for_update().first()

        if not receiver:
            raise AccountNotFoundError(transfer_request.to_account)

        # Validate both accounts are ACTIVE
        _validate_account_for_operation(
            sender,
            allow_status=[AccountStatus.ACTIVE]
        )
        _validate_account_for_operation(
            receiver,
            allow_status=[AccountStatus.ACTIVE]
        )

        # Check sender has sufficient balance
        if sender.balance < transfer_request.amount:
            raise InsufficientBalanceError(sender.balance, transfer_request.amount)

        # Record old balances
        sender_old_balance = sender.balance
        receiver_old_balance = receiver.balance

        # Debit sender
        sender.balance -= transfer_request.amount

        # Credit receiver
        receiver.balance += transfer_request.amount

        # Generate reference number
        reference_number = _generate_reference_number()

        # Create transaction record
        transaction = Transaction(
            reference_number=reference_number,
            transaction_type=TransactionType.TRANSFER,
            amount=transfer_request.amount,
            balance_before=sender_old_balance,
            balance_after=sender.balance,
            remarks=transfer_request.remarks,
            status=TransactionStatus.SUCCESS,
            source_account_id=sender.id,
            destination_account_id=receiver.id,
            created_by=current_user_id
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        # Create audit logs for both accounts
        create_audit_log(
            db=db,
            action="TRANSFER",
            entity_type="ACCOUNT",
            entity_id=sender.id,
            performed_by=current_user_id,
            old_value={"balance": float(sender_old_balance)},
            new_value={"balance": float(sender.balance)}
        )

        create_audit_log(
            db=db,
            action="TRANSFER",
            entity_type="ACCOUNT",
            entity_id=receiver.id,
            performed_by=current_user_id,
            old_value={"balance": float(receiver_old_balance)},
            new_value={"balance": float(receiver.balance)}
        )

        return transaction

    except Exception as e:
        db.rollback()
        if isinstance(e, (
            AccountNotFoundError,
            InvalidAmountError,
            SameAccountTransferError,
            InsufficientBalanceError,
            InactiveAccountError
        )):
            raise
        raise TransactionFailedError(str(e))
