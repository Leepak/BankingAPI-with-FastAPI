
"""
Report Routes - FastAPI endpoints for report generation.

Provides REST API endpoints for:
- Customer reports (CSV, Excel, PDF)
- Account reports (CSV, Excel, PDF)
- Transaction reports (CSV, Excel, PDF)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import io

from app.database import get_db
from app.core.permission import is_admin
from app.models.user import User
from app.schemas.report import ReportFilter, ReportFormat, ReportType
from app.services.report_service import ReportService, ReportDataService

router = APIRouter(prefix="/reports", tags=["Reports"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_filename(prefix: str, format: str) -> str:
    """Generate filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{format}"

def get_content_type(format: str) -> str:
    """Get content type for response."""
    content_types = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf"
    }
    return content_types.get(format, "application/octet-stream")


# ============================================================================
# CUSTOMER REPORTS
# ============================================================================

@router.get("/customers")
def generate_customer_report(
    format: str = Query(..., description="Report format: csv, xlsx, pdf"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """
    Generate customer report in CSV, Excel, or PDF format.
    
    **Admin Only Endpoint**
    
    Args:
        format: Output format (csv, xlsx, pdf)
        customer_id: Optional customer ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        File download with customer data
    """
    # Validate format
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use csv, xlsx, or pdf")
    
    # Fetch data
    filters = {
        "customer_id": customer_id,
        "start_date": start_date,
        "end_date": end_date
    }
    data = ReportDataService.get_customers_data(db, filters)
    
    if not data:
        raise HTTPException(status_code=404, detail="No customer data found")
    
    # Generate report based on format
    filename = get_filename("customers", format)
    content_type = get_content_type(format)
    
    if format == "csv":
        content = ReportService.generate_csv(data, filename)
    elif format == "xlsx":
        content = ReportService.generate_excel(data, filename)
    else:  # pdf
        content = ReportService.generate_pdf(data, "Customer Report")
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# ACCOUNT REPORTS
# ============================================================================

@router.get("/accounts")
def generate_account_report(
    format: str = Query(..., description="Report format: csv, xlsx, pdf"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """
    Generate account report in CSV, Excel, or PDF format.
    
    **Admin Only Endpoint**
    
    Args:
        format: Output format (csv, xlsx, pdf)
        customer_id: Optional customer ID filter
        account_number: Optional account number filter
        status: Optional status filter
    
    Returns:
        File download with account data
    """
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use csv, xlsx, or pdf")
    
    # Fetch data
    filters = {
        "customer_id": customer_id,
        "account_number": account_number,
        "status": status
    }
    data = ReportDataService.get_accounts_data(db, filters)
    
    if not data:
        raise HTTPException(status_code=404, detail="No account data found")
    
    # Generate report
    filename = get_filename("accounts", format)
    content_type = get_content_type(format)
    
    if format == "csv":
        content = ReportService.generate_csv(data, filename)
    elif format == "xlsx":
        content = ReportService.generate_excel(data, filename)
    else:  # pdf
        content = ReportService.generate_pdf(data, "Account Report")
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# TRANSACTION REPORTS
# ============================================================================

@router.get("/transactions")
def generate_transaction_report(
    format: str = Query(..., description="Report format: csv, xlsx, pdf"),
    account_number: Optional[str] = Query(None, description="Filter by account number"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """
    Generate transaction report in CSV, Excel, or PDF format.
    
    **Admin Only Endpoint**
    
    Args:
        format: Output format (csv, xlsx, pdf)
        account_number: Optional account number filter
        transaction_type: Optional transaction type filter
        status: Optional status filter
        min_amount: Minimum amount filter
        max_amount: Maximum amount filter
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        File download with transaction data
    """
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use csv, xlsx, or pdf")
    
    # Fetch data
    filters = {
        "account_number": account_number,
        "transaction_type": transaction_type,
        "status": status,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "start_date": start_date,
        "end_date": end_date
    }
    data = ReportDataService.get_transactions_data(db, filters)
    
    if not data:
        raise HTTPException(status_code=404, detail="No transaction data found")
    
    # Generate report
    filename = get_filename("transactions", format)
    content_type = get_content_type(format)
    
    if format == "csv":
        content = ReportService.generate_csv(data, filename)
    elif format == "xlsx":
        content = ReportService.generate_excel(data, filename)
    else:  # pdf
        content = ReportService.generate_pdf(data, "Transaction Report")
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# SUMMARY REPORTS
# ============================================================================

@router.get("/summary")
def generate_summary_report(
    format: str = Query(..., description="Report format: csv, xlsx, pdf"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    """
    Generate summary report with combined data.
    
    **Admin Only Endpoint**
    """
    if format not in ["csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use csv, xlsx, or pdf")
    
    # Fetch data
    customers = ReportDataService.get_customers_data(db, {})
    accounts = ReportDataService.get_accounts_data(db, {})
    transactions = ReportDataService.get_transactions_data(db, {})
    
    # Create summary
    summary = {
        "Report Generated At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Customers": len(customers),
        "Total Accounts": len(accounts),
        "Total Transactions": len(transactions),
        "Total Transaction Amount": sum(t.get("Amount", 0) for t in transactions)
    }
    
    data = [{"Metric": k, "Value": v} for k, v in summary.items()]
    
    filename = get_filename("summary", format)
    content_type = get_content_type(format)
    
    if format == "csv":
        content = ReportService.generate_csv(data, filename)
    elif format == "xlsx":
        content = ReportService.generate_excel(data, filename)
    else:  # pdf
        content = ReportService.generate_pdf(data, "Summary Report")
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )