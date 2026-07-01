"""
Transaction Model - Records all financial transactions in the banking system.

Supports:
- Deposits (credit to account)
- Withdrawals (debit from account)
- Transfers (debit sender, credit receiver)
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey,
    func, Enum, Text, Index
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime


class TransactionType(str, enum.Enum):
    """Types of transactions in the banking system."""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, enum.Enum):
    """Status of a transaction."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REVERSED = "REVERSED"


class TransactionChannel(str, enum.Enum):
    CASH = "CASH"
    ATM = "ATM"
    BRANCH = "BRANCH"
    MOBILE_BANKING = "MOBILE_BANKING"
    INTERNET_BANKING = "INTERNET_BANKING"
    API = "API"



class Transaction(Base):
    """
    Transaction Model.

    Records all financial transactions including deposits, withdrawals, and transfers.
    Uses row locking to prevent race conditions on balance updates.
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Unique reference number for tracking
    reference_number = Column(String(50), unique=True, index=True, nullable=False)


    # Prevent duplicate requests
    client_reference = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    # Transaction type (DEPOSIT, WITHDRAW, TRANSFER)
      
    transaction_type = Column(
        Enum(
            TransactionType,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        index=True,
    )

    channel = Column(
        Enum(
            TransactionChannel,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=TransactionChannel.API,
    )

    status = Column(
        Enum(
            TransactionStatus,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )
    
    # Amount involved in transaction
    amount = Column(Numeric(18, 2), nullable=False)

    # Balance tracking before and after
    balance_before = Column(Numeric(18, 2), nullable=False)
    balance_after = Column(Numeric(18, 2), nullable=False)

    # Optional remarks/description
    remarks = Column(Text, nullable=True)

    

    # Source account (account being debited or receiving deposit)
    source_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    # Destination account (account being credited in transfer)
    destination_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)

    # REVERSAL SUPPORT
    # -------------------------------------------------

    reversed_transaction_id = Column(
        Integer,
        ForeignKey("transactions.id"),
        nullable=True,
    )

    # Audit trail
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
     
     
    # Relationships
    source_account = relationship(
        "Account",
        foreign_keys=[source_account_id],
        viewonly=True
    )
    destination_account = relationship(
        "Account",
        foreign_keys=[destination_account_id],
        viewonly=True
    )
    created_by_user = relationship("User", foreign_keys=[created_by], viewonly=True)
    reversed_transaction = relationship(
        "Transaction",
        remote_side=[id],
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_transaction_reference", "reference_number"),
        Index('idx_transactions_source_account', 'source_account_id'),
        Index('idx_transactions_destination_account', 'destination_account_id'),
         Index(
            "idx_transaction_status",
            "status"
        ),
        Index(
            "idx_transaction_type",
            "transaction_type"
        ),
        Index('idx_transactions_type_status', 'transaction_type', 'status'),
        Index('idx_transactions_created_at', 'created_at'),
    )
