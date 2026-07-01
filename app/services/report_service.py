# app/services/report_service.py

import io
import csv
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from xhtml2pdf import pisa
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction


class ReportService:
    """Service for generating reports in various formats."""

    @staticmethod
    def generate_csv(data: List[Dict[str, Any]], filename: str) -> bytes:
        """Generate CSV file from data."""
        if not data:
            raise HTTPException(status_code=404, detail="No data available for report")
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue().encode('utf-8')

    @staticmethod
    def generate_excel(data: List[Dict[str, Any]], filename: str) -> bytes:
        """Generate Excel file from data."""
        if not data:
            raise HTTPException(status_code=404, detail="No data available for report")
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Report']
            for column in df.columns:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                column_length = min(column_length, 50)  # Limit to 50 characters
                worksheet.column_dimensions[column].width = column_length + 2
        
        return output.getvalue()

    @staticmethod
    def generate_pdf(data: List[Dict[str, Any]], title: str, headers: Optional[List[str]] = None) -> bytes:
        """Generate PDF file from data."""
        if not data:
            raise HTTPException(status_code=404, detail="No data available for report")
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 20))

        # Add generation date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray
        )
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        elements.append(Spacer(1, 20))

        # Prepare table data
        if headers:
            table_data = [headers]
        else:
            table_data = [list(data[0].keys())]
        
        for row in data:
            row_values = []
            for key in table_data[0]:
                value = row.get(key, '')
                if isinstance(value, Decimal):
                    value = f"{value:.2f}"
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                row_values.append(str(value))
            table_data.append(row_values)

        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        # Build PDF
        doc.build(elements)
        return output.getvalue()

    @staticmethod
    def generate_pdf_from_html(html_content: str) -> bytes:
        """Generate PDF from HTML content."""
        output = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html_content), output)
        return output.getvalue()


class ReportDataService:
    """Service for fetching report data."""

    @staticmethod
    def get_customers_data(db: Session, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch customer data for reports."""
        query = db.query(Customer)
        
        if filters.get('start_date'):
            query = query.filter(Customer.created_at >= filters['start_date'])
        if filters.get('end_date'):
            query = query.filter(Customer.created_at <= filters['end_date'])
        if filters.get('customer_id'):
            query = query.filter(Customer.id == filters['customer_id'])
        
        customers = query.all()
        
        return [
            {
                "ID": c.id,
                "Full Name": c.full_name,
                "Email": c.email,
                "Phone": c.phone_number,
                "Address": c.address or "N/A",
                "Created At": c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else "",
                "Updated At": c.updated_at.strftime('%Y-%m-%d %H:%M:%S') if c.updated_at else ""
            }
            for c in customers
        ]

    @staticmethod
    def get_accounts_data(db: Session, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch account data for reports."""
        query = db.query(Account)
        
        if filters.get('customer_id'):
            query = query.filter(Account.customer_id == filters['customer_id'])
        if filters.get('account_number'):
            query = query.filter(Account.account_number == filters['account_number'])
        if filters.get('status'):
            query = query.filter(Account.status == filters['status'])
        
        accounts = query.all()
        
        return [
            {
                "ID": a.id,
                "Account Number": a.account_number,
                "Type": a.account_type.value,
                "Balance": float(a.balance),
                "Currency": a.currency,
                "Status": a.status.value,
                "Customer ID": a.customer_id,
                "Opened At": a.opened_at.strftime('%Y-%m-%d %H:%M:%S') if a.opened_at else "",
                "Closed At": a.closed_at.strftime('%Y-%m-%d %H:%M:%S') if a.closed_at else "Active"
            }
            for a in accounts
        ]

    @staticmethod
    def get_transactions_data(db: Session, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch transaction data for reports."""
        from app.crud.transaction import get_transactions
        
        transactions, _ = get_transactions(
            db=db,
            account_number=filters.get('account_number'),
            transaction_type=filters.get('transaction_type'),
            status=filters.get('status'),
            min_amount=filters.get('min_amount'),
            max_amount=filters.get('max_amount'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            skip=0,
            limit=10000  # Max limit for reports
        )
        
        return [
            {
                "ID": t.id,
                "Reference": t.reference_number,
                "Type": t.transaction_type.value,
                "Amount": float(t.amount),
                "Balance Before": float(t.balance_before),
                "Balance After": float(t.balance_after),
                "Status": t.status.value,
                "Remarks": t.remarks or "",
                "Source Account ID": t.source_account_id,
                "Destination Account ID": t.destination_account_id or "",
                "Created At": t.created_at.strftime('%Y-%m-%d %H:%M:%S') if t.created_at else ""
            }
            for t in transactions
        ]