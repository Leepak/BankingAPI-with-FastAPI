

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, func, Enum, CheckConstraint, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base
import enum
from datetime import datetime
from decimal import Decimal


class AccountType(str, enum.Enum):
    """Enum for account types."""
    SAVINGS = "savings"
    CURRENT = "current"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive matching."""
        if isinstance(value, str):
            value = value.lower().strip()
            if value == "saving":
                return cls.SAVINGS
            for member in cls:
                if member.value == value:
                    return member
        return None


class AccountStatus(str, enum.Enum):
    """Enum for account statuses."""
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    FROZEN = "FROZEN"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive matching."""
        if isinstance(value, str):
            value = value.upper().strip()
            for member in cls:
                if member.value == value:
                    return member
        return None


class Account(Base):
    """
    Account model representing a bank account.
    
    Attributes:
        id: Primary key
        account_number: Unique account number
        account_type: Type of account (savings/current)
        balance: Current account balance
        currency: Currency code (default: NPR)
        status: Account status (ACTIVE/DORMANT/FROZEN/BLOCKED/CLOSED)
        is_active: Boolean flag for active status
        opened_at: Date account was opened
        closed_at: Date account was closed (if applicable)
        customer_id: Foreign key to customer
        created_by: User who created the account
        updated_by: User who last updated the account
        version: Optimistic locking version
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    
    __tablename__ = "accounts"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Account Identification
    account_number = Column(
        String(20), 
        unique=True, 
        index=True, 
        nullable=False,
        doc="Unique account number"
    )
    
    # Account Type
    account_type = Column(
        Enum(AccountType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        doc="Type of account (savings/current)"
    )
    
    # Financial Fields
    balance = Column(
        Numeric(18, 2), 
        default=Decimal('0.00'), 
        nullable=False,
        doc="Current account balance"
    )
    
    currency = Column(
        String(3), 
        default="NPR", 
        nullable=False,
        doc="Currency code (ISO 4217)"
    )
    
    # Account Status
    status = Column(
        Enum(AccountStatus, values_callable=lambda x: [e.value for e in x]),
        default=AccountStatus.ACTIVE,
        nullable=False,
        index=True,
        doc="Current account status"
    )
    
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        doc="Flag indicating if account is active"
    )
    
    # Timestamps
    opened_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        doc="Date and time account was opened"
    )
    
    closed_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        doc="Date and time account was closed (if applicable)"
    )
    
    # Foreign Keys
    customer_id = Column(
        Integer, 
        ForeignKey("customers.id", ondelete="RESTRICT"), 
        nullable=False, 
        index=True,
        doc="Foreign key to customer"
    )
    
    created_by = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        doc="User ID who created this account"
    )
    
    updated_by = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        doc="User ID who last updated this account"
    )
    
    # Audit Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        doc="Timestamp of creation"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update"
    )
    
    # Optimistic Locking
    version = Column(
        Integer, 
        default=1, 
        nullable=False,
        doc="Version number for optimistic locking"
    )
    
    # Relationships (without transactions)
    customer = relationship(
        "Customer", 
        back_populates="accounts",
        doc="Customer owning this account"
    )
    
    created_by_user = relationship(
        "User", 
        foreign_keys=[created_by], 
        viewonly=True,
        doc="User who created this account"
    )
    
    updated_by_user = relationship(
        "User", 
        foreign_keys=[updated_by], 
        viewonly=True,
        doc="User who last updated this account"
    )
    
    # Table Constraints and Indexes
    __table_args__ = (
        # Ensure balance is never negative
        CheckConstraint(
            'balance >= 0',
            name='check_balance_non_negative'
        ),
        
        # Ensure closed accounts have closed_at set
        CheckConstraint(
            'status != "CLOSED" OR closed_at IS NOT NULL',
            name='check_closed_at_for_closed_accounts'
        ),
        
        # Ensure account number format (starts with type code)
        CheckConstraint(
            "account_number ~ '^[SC][0-9]{10,15}$'",
            name='check_account_number_format'
        ),
        
        # Composite indexes for common query patterns
        Index('ix_accounts_customer_status', 'customer_id', 'status'),
        Index('ix_accounts_account_type_status', 'account_type', 'status'),
        Index('ix_accounts_status_balance', 'status', 'balance'),
    )

    def __init__(self, **kwargs):
        """Initialize account with default values."""
        super().__init__(**kwargs)
        if self.balance is None:
            self.balance = Decimal('0.00')
        if self.currency is None:
            self.currency = "NPR"

    def __repr__(self):
        """String representation of account."""
        return (
            f"<Account(id={self.id}, "
            f"account_number='{self.account_number}', "
            f"type='{self.account_type.value}', "
            f"balance={self.balance}, "
            f"status='{self.status.value}')>"
        )

    def __str__(self):
        """Human-readable string representation."""
        return (
            f"Account {self.account_number} "
            f"({self.account_type.value}) - "
            f"Balance: {self.currency} {self.balance:,.2f}"
        )

    # ==================== Hybrid Properties ====================

    @hybrid_property
    def is_closed(self):
        """Check if account is closed."""
        return self.status == AccountStatus.CLOSED

    @hybrid_property
    def is_frozen(self):
        """Check if account is frozen."""
        return self.status == AccountStatus.FROZEN

    @hybrid_property
    def is_blocked(self):
        """Check if account is blocked."""
        return self.status == AccountStatus.BLOCKED

    @hybrid_property
    def is_dormant(self):
        """Check if account is dormant."""
        return self.status == AccountStatus.DORMANT

    @hybrid_property
    def is_active_status(self):
        """Check if account status is active."""
        return self.status == AccountStatus.ACTIVE

    @hybrid_property
    def can_transact(self):
        """Check if transactions are allowed on this account."""
        return (
            self.is_active and 
            self.status in [AccountStatus.ACTIVE, AccountStatus.DORMANT]
        )

    @hybrid_property
    def account_age_days(self):
        """Calculate account age in days."""
        if self.opened_at:
            delta = datetime.utcnow() - self.opened_at
            return delta.days
        return 0

    @hybrid_property
    def has_balance(self):
        """Check if account has any balance."""
        return self.balance > Decimal('0.00')

    @hybrid_property
    def is_zero_balance(self):
        """Check if account balance is zero."""
        return self.balance == Decimal('0.00')

    # ==================== Status Management Methods ====================

    def freeze(self, user_id: int = None) -> bool:
        """
        Freeze the account.
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status == AccountStatus.CLOSED:
            return False
        
        self.status = AccountStatus.FROZEN
        self.is_active = False
        self.updated_by = user_id
        self.version += 1
        return True

    def unfreeze(self, user_id: int = None) -> bool:
        """
        Unfreeze the account (set to active).
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status != AccountStatus.FROZEN:
            return False
        
        self.status = AccountStatus.ACTIVE
        self.is_active = True
        self.updated_by = user_id
        self.version += 1
        return True

    def block(self, user_id: int = None) -> bool:
        """
        Block the account.
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status == AccountStatus.CLOSED:
            return False
        
        self.status = AccountStatus.BLOCKED
        self.is_active = False
        self.updated_by = user_id
        self.version += 1
        return True

    def unblock(self, user_id: int = None) -> bool:
        """
        Unblock the account (set to active).
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status != AccountStatus.BLOCKED:
            return False
        
        self.status = AccountStatus.ACTIVE
        self.is_active = True
        self.updated_by = user_id
        self.version += 1
        return True

    def close(self, user_id: int = None) -> bool:
        """
        Close the account.
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status == AccountStatus.CLOSED:
            return False
        
        if self.balance > Decimal('0.00'):
            return False
        
        self.status = AccountStatus.CLOSED
        self.is_active = False
        self.closed_at = datetime.utcnow()
        self.updated_by = user_id
        self.version += 1
        return True

    def activate(self, user_id: int = None) -> bool:
        """
        Activate the account.
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status == AccountStatus.CLOSED:
            return False
        
        self.status = AccountStatus.ACTIVE
        self.is_active = True
        self.updated_by = user_id
        self.version += 1
        return True

    def make_dormant(self, user_id: int = None) -> bool:
        """
        Mark account as dormant.
        
        Args:
            user_id: ID of user performing the action
            
        Returns:
            bool: True if successful
        """
        if self.status not in [AccountStatus.ACTIVE, AccountStatus.DORMANT]:
            return False
        
        self.status = AccountStatus.DORMANT
        self.updated_by = user_id
        self.version += 1
        return True

    # ==================== Balance Management ====================

    def update_balance(self, amount: Decimal) -> bool:
        """
        Update account balance.
        
        Args:
            amount: Amount to add (positive for credit, negative for debit)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(amount, Decimal):
                amount = Decimal(str(amount))
            
            new_balance = self.balance + amount
            
            if new_balance < 0:
                return False
            
            self.balance = new_balance
            self.version += 1
            return True
        except (ValueError, TypeError):
            return False

    def credit(self, amount: Decimal) -> bool:
        """
        Credit (add) amount to account.
        
        Args:
            amount: Amount to credit
            
        Returns:
            bool: True if successful
        """
        if amount <= 0:
            return False
        return self.update_balance(amount)

    def debit(self, amount: Decimal) -> bool:
        """
        Debit (subtract) amount from account.
        
        Args:
            amount: Amount to debit
            
        Returns:
            bool: True if successful
        """
        if amount <= 0:
            return False
        return self.update_balance(-amount)

    # ==================== Utility Methods ====================

    @classmethod
    def get_status_transitions(cls, current_status: AccountStatus) -> list:
        """
        Get valid status transitions for a given status.
        
        Args:
            current_status: Current account status
            
        Returns:
            list: List of valid target statuses
        """
        transitions = {
            AccountStatus.ACTIVE: [
                AccountStatus.DORMANT,
                AccountStatus.FROZEN,
                AccountStatus.BLOCKED,
                AccountStatus.CLOSED
            ],
            AccountStatus.DORMANT: [
                AccountStatus.ACTIVE,
                AccountStatus.CLOSED
            ],
            AccountStatus.FROZEN: [
                AccountStatus.ACTIVE,
                AccountStatus.CLOSED
            ],
            AccountStatus.BLOCKED: [
                AccountStatus.ACTIVE,
                AccountStatus.CLOSED
            ],
            AccountStatus.CLOSED: []
        }
        return transitions.get(current_status, [])

    @classmethod
    def is_valid_status_transition(
        cls, 
        current_status: AccountStatus, 
        new_status: AccountStatus
    ) -> bool:
        """
        Check if a status transition is valid.
        
        Args:
            current_status: Current account status
            new_status: Target account status
            
        Returns:
            bool: True if transition is valid
        """
        return new_status in cls.get_status_transitions(current_status)

    def to_dict(self, include_balance: bool = True) -> dict:
        """
        Convert account to dictionary.
        
        Args:
            include_balance: Whether to include balance in output
            
        Returns:
            dict: Account data
        """
        data = {
            "id": self.id,
            "account_number": self.account_number,
            "account_type": self.account_type.value,
            "currency": self.currency,
            "status": self.status.value,
            "is_active": self.is_active,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "customer_id": self.customer_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version
        }
        
        if include_balance:
            data["balance"] = float(self.balance) if self.balance else 0.0
        
        return data

    def to_json(self, include_balance: bool = True) -> dict:
        """
        Convert to JSON-serializable dict.
        
        Args:
            include_balance: Whether to include balance in output
            
        Returns:
            dict: JSON-serializable account data
        """
        return self.to_dict(include_balance=include_balance)


# ==================== Helper Functions ====================

def validate_account_number(account_number: str) -> bool:
    """
    Validate account number format.
    
    Args:
        account_number: Account number to validate
        
    Returns:
        bool: True if valid
    """
    import re
    pattern = r'^[SC][0-9]{10,15}$'
    return bool(re.match(pattern, account_number))


def generate_display_account_number(account_number: str) -> str:
    """
    Generate a display-friendly account number with masking.
    
    Args:
        account_number: Full account number
        
    Returns:
        str: Masked account number (e.g., S****5678)
    """
    if len(account_number) <= 8:
        return account_number
    return f"{account_number[0]}****{account_number[-4:]}"


def get_default_currency() -> str:
    """Get default currency."""
    return "NPR"


def is_valid_currency(currency: str) -> bool:
    """
    Check if currency code is valid.
    
    Args:
        currency: Currency code to validate
        
    Returns:
        bool: True if valid
    """
    valid_currencies = ["NPR", "USD", "EUR", "GBP", "INR"]
    return currency.upper() in valid_currencies



