from sqlalchemy.orm import Session
from app.models.account import Account, AccountType


def generate_account_number(db: Session, account_type: AccountType) -> str:
    """
    Generate a unique, human-readable account number.

    Format:
    - Savings: SAV10000001, SAV10000002, etc.
    - Current: CUR10000001, CUR10000002, etc.

    Args:
        db: Database session
        account_type: AccountType enum value

    Returns:
        A unique account number string
    """
    prefix = "SAV" if account_type == AccountType.SAVINGS else "CUR"

    last_account = db.query(Account).filter(
        Account.account_type == account_type
    ).order_by(Account.id.desc()).first()

    if last_account:
        last_number = int(last_account.account_number[3:])
        next_number = last_number + 1
    else:
        next_number = 10000001

    return f"{prefix}{next_number}"
