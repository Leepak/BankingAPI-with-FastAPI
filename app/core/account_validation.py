from fastapi import HTTPException

from app.models.account import AccountStatus


def validate_account_for_transaction(account):

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    if not account.is_active:
        raise HTTPException(
            status_code=400,
            detail="Account is inactive"
        )

    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Account status is {account.status}"
        )


def validate_sufficient_balance(account, amount):

    if account.balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Insufficient balance"
        )


def validate_transaction_amount(amount):

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero"
        )