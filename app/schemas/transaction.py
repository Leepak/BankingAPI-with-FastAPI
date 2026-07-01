# app/schemas/transaction.py

"""
Transaction Schemas - Pydantic models for request/response validation.

Validates all transaction inputs and structures all API responses.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.transaction import TransactionStatus, TransactionType


# ============================================================================
# DEPOSIT SCHEMA
# ============================================================================

class DepositRequest(BaseModel):
    """Request model for deposit operation."""
    account_number: str = Field(
        min_length=1,
        max_length=20,
        description="Account number to deposit into"
    )
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        description="Deposit amount (must be > 0)"
    )
    remarks: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional transaction remarks"
    )

    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is valid."""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class DepositResponse(BaseModel):
    """Response model for successful deposit."""
    transaction_id: int
    reference_number: str
    account_number: str
    amount: Decimal
    new_balance: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# WITHDRAW SCHEMA
# ============================================================================

class WithdrawRequest(BaseModel):
    """Request model for withdrawal operation."""
    account_number: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Account number to withdraw from"
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Withdrawal amount (must be > 0)"
    )
    remarks: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional transaction remarks"
    )

    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is valid."""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class WithdrawResponse(BaseModel):
    """Response model for successful withdrawal."""
    transaction_id: int
    reference_number: str
    account_number: str
    withdrawn: Decimal
    remaining_balance: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TRANSFER SCHEMA
# ============================================================================

class TransferRequest(BaseModel):
    """Request model for transfer operation."""
    from_account: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Sender account number"
    )
    to_account: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Receiver account number"
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Transfer amount (must be > 0)"
    )
    remarks: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional transaction remarks"
    )

    @field_validator('amount', mode='before')
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount is valid."""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator('to_account')
    @classmethod
    def validate_different_accounts(cls, v, info):
        """Ensure sender and receiver are different."""
        if 'from_account' in info.data and v == info.data['from_account']:
            raise ValueError("Sender and receiver accounts must be different")
        return v


class TransferResponse(BaseModel):
    """Response model for successful transfer."""
    transaction_id: int
    reference_number: str
    amount: Decimal
    from_account: str
    to_account: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TRANSACTION DETAILS
# ============================================================================

class TransactionResponse(BaseModel):
    """Response model for single transaction."""
    id: int
    reference_number: str
    transaction_type: TransactionType
    status: TransactionStatus
    amount: Decimal
    fee: Decimal = Decimal("0.00")
    balance_before: Decimal
    balance_after: Decimal
    currency: str
    source_account_id: int
    destination_account_id: Optional[int]
    remarks: Optional[str]
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TRANSACTION HISTORY SCHEMA
# ============================================================================

class TransactionHistoryResponse(BaseModel):
    """Response model for transaction history entry."""
    id: int
    reference_number: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str
    remarks: Optional[str]
    created_at: datetime
    source_account_id: Optional[int] = None  # Made optional
    destination_account_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionHistoryListResponse(BaseModel):
    """Response model for transaction history list with pagination."""
    total_count: int
    page: int
    page_size: int
    transactions: list[TransactionHistoryResponse]


# ============================================================================
# BALANCE INQUIRY SCHEMA
# ============================================================================

class BalanceInquiryResponse(BaseModel):
    """Response model for balance inquiry."""
    account_number: str
    balance: Decimal
    currency: str
    status: str
    is_active: bool
    account_type: str

    model_config = ConfigDict(from_attributes=True)


class AccountStatementResponse(BaseModel):
    """Response model for account statement."""
    account_number: str
    customer_name: str
    from_date: datetime
    to_date: datetime
    opening_balance: Decimal
    closing_balance: Decimal
    transactions: list[TransactionHistoryResponse]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# NEW SCHEMAS FOR ADDITIONAL ENDPOINTS
# ============================================================================

class TransactionSummaryResponse(BaseModel):
    """
    Transaction summary response for /transactions/summary endpoint.
    """
    total_transactions: int = Field(..., description="Total number of transactions")
    total_deposits: int = Field(..., description="Total number of deposits")
    total_withdrawals: int = Field(..., description="Total number of withdrawals")
    total_transfers: int = Field(..., description="Total number of transfers")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    total_deposit_amount: Decimal = Field(..., description="Total deposit amount")
    total_withdrawal_amount: Decimal = Field(..., description="Total withdrawal amount")
    total_transfer_amount: Decimal = Field(..., description="Total transfer amount")
    successful_count: int = Field(..., description="Number of successful transactions")
    failed_count: int = Field(..., description="Number of failed transactions")
    pending_count: int = Field(..., description="Number of pending transactions")
    start_date: Optional[datetime] = Field(None, description="Summary start date")
    end_date: Optional[datetime] = Field(None, description="Summary end date")
    
    model_config = ConfigDict(from_attributes=True)


class TransactionStatisticsResponse(BaseModel):
    """
    Transaction statistics response for /transactions/statistics endpoint.
    """
    period: str = Field(..., description="Aggregation period (day, week, month, year)")
    start_date: Optional[datetime] = Field(None, description="Statistics start date")
    end_date: Optional[datetime] = Field(None, description="Statistics end date")
    
    # Trends
    daily_trend: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Daily transaction trends"
    )
    weekly_trend: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Weekly transaction trends"
    )
    monthly_trend: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Monthly transaction trends"
    )
    
    # Top accounts
    top_source_accounts: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Top source accounts by transaction volume"
    )
    top_destination_accounts: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Top destination accounts by transaction volume"
    )
    
    # Peak times
    peak_hours: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Peak transaction hours"
    )
    peak_days: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Peak transaction days"
    )
    
    # Additional statistics
    average_transaction_amount: Decimal = Field(
        default=Decimal('0.00'),
        description="Average transaction amount"
    )
    max_transaction_amount: Decimal = Field(
        default=Decimal('0.00'),
        description="Maximum transaction amount"
    )
    min_transaction_amount: Decimal = Field(
        default=Decimal('0.00'),
        description="Minimum transaction amount"
    )

    model_config = ConfigDict(from_attributes=True)


class RecentTransactionResponse(BaseModel):
    """
    Response model for recent transactions.
    """
    id: int
    reference_number: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    status: str
    remarks: Optional[str]
    created_at: datetime
    source_account_number: Optional[str] = None
    destination_account_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# RE-EXPORT FOR BACKWARD COMPATIBILITY
# ============================================================================

# Make sure all schemas are available from the module
__all__ = [
    # Deposit
    "DepositRequest",
    "DepositResponse",
    # Withdraw
    "WithdrawRequest",
    "WithdrawResponse",
    # Transfer
    "TransferRequest",
    "TransferResponse",
    # Transaction details
    "TransactionResponse",
    "TransactionHistoryResponse",
    "TransactionHistoryListResponse",
    # Balance
    "BalanceInquiryResponse",
    "AccountStatementResponse",
    # New schemas
    "TransactionSummaryResponse",
    "TransactionStatisticsResponse",
    "RecentTransactionResponse",
    # Enums
    "TransactionStatus",
    "TransactionType",
]
