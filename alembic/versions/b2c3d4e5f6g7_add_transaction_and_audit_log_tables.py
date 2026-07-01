"""Add transaction and audit log tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add transaction and audit log tables."""

    # Create transaction type enum
    op.execute("""
        CREATE TYPE transactiontype AS ENUM ('DEPOSIT', 'WITHDRAW', 'TRANSFER');
    """)

    # Create transaction status enum
    op.execute("""
        CREATE TYPE transactionstatus AS ENUM ('SUCCESS', 'FAILED', 'PENDING');
    """)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(length=50), nullable=False),
        sa.Column(
            'transaction_type',
            sa.Enum('DEPOSIT', 'WITHDRAW', 'TRANSFER', name='transactiontype'),
            nullable=False
        ),
        sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('balance_before', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('balance_after', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('SUCCESS', 'FAILED', 'PENDING', name='transactionstatus'),
            server_default='PENDING',
            nullable=False
        ),
        sa.Column('source_account_id', sa.Integer(), nullable=False),
        sa.Column('destination_account_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['source_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['destination_account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes on transactions
    op.create_index('idx_transactions_source_account', 'transactions', ['source_account_id'])
    op.create_index('idx_transactions_destination_account', 'transactions', ['destination_account_id'])
    op.create_index('idx_transactions_type_status', 'transactions', ['transaction_type', 'status'])
    op.create_index('idx_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('ix_transactions_reference_number', 'transactions', ['reference_number'], unique=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes on audit_logs
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_user', 'audit_logs', ['performed_by'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Downgrade schema - remove transaction and audit log tables."""

    # Drop indexes
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user', table_name='audit_logs')
    op.drop_index('idx_audit_logs_entity', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')

    op.drop_index('ix_transactions_reference_number', table_name='transactions')
    op.drop_index('idx_transactions_created_at', table_name='transactions')
    op.drop_index('idx_transactions_type_status', table_name='transactions')
    op.drop_index('idx_transactions_destination_account', table_name='transactions')
    op.drop_index('idx_transactions_source_account', table_name='transactions')

    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('transactions')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS transactionstatus')
    op.execute('DROP TYPE IF EXISTS transactiontype')
