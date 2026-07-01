from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"   


class ReportType(str, Enum):
    CUSTOMER = "customer"   
    ACCOUNT = "account"
    TRANSACTION = "transaction"

class ReportFilter(BaseModel):
    """Base filters for reports."""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    customer_id: Optional[int] = Field(None, description="Filter by customer ID")
    account_number: Optional[str] = Field(None, description="Filter by account number")
    transaction_type: Optional[str] = Field(None, description="Filter by transaction type")
    status: Optional[str] = Field(None, description="Filter by status")
    min_amount: Optional[float] = Field(None, description="Minimum amount")
    max_amount: Optional[float] = Field(None, description="Maximum amount")

class ReportResponse(BaseModel):
    """Response model for report generation."""
    filename: str
    format: str
    file_size: int
    generated_at: datetime
    download_url: str

    class Config:
        from_attributes = True