from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class CustomerSummary(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class AccountCreate(BaseModel):
    customer_id: int
    account_type: str
    currency: Optional[str] = "NPR"

    @field_validator("account_type", mode="before")
    @classmethod
    def validate_account_type(cls, v):
        if isinstance(v, str):
            v = v.lower().strip()
            if v == "saving":
                v = "savings"
            if v not in ["savings", "current"]:
                raise ValueError("account_type must be 'savings' or 'current'")
        return v

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, v):
        if v and isinstance(v, str):
            v = v.upper().strip()
            if len(v) != 3:
                raise ValueError("currency must be a 3-letter ISO code")
        return v


class AccountUpdate(BaseModel):
    status: Optional[str] = None
    currency: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v:
            v = v.upper().strip()
            valid_statuses = ["ACTIVE", "DORMANT", "FROZEN", "BLOCKED", "CLOSED"]
            if v not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if v:
            v = v.upper().strip()
            if len(v) != 3:
                raise ValueError("currency must be a 3-letter ISO code")
        return v


class AccountResponse(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: Decimal
    currency: str
    status: str
    is_active: bool
    customer_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerSummary] = None

    model_config = ConfigDict(from_attributes=True)

