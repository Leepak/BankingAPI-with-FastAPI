# alembic/versions/084053977463_add_customer_id_to_users.py

"""add_customer_id_to_users

Revision ID: 084053977463
Revises: 42eb1e86177d
Create Date: 2026-06-26 22:47:24.119028
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '084053977463'
down_revision: Union[str, Sequence[str], None] = '42eb1e86177d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ===== FIX FOR ACCOUNTS TABLE =====
    # First, add version column as nullable
    op.add_column('accounts', sa.Column('version', sa.Integer(), nullable=True))
    
    # Set default value for existing rows
    op.execute("UPDATE accounts SET version = 1 WHERE version IS NULL")
    
    # Now make it NOT NULL
    op.alter_column('accounts', 'version', existing_type=sa.Integer(), nullable=False)
    
    # ===== CONTINUE WITH REST OF MIGRATION =====
    op.drop_constraint(op.f('accounts_account_number_key'), 'accounts', type_='unique')
    op.drop_index(op.f('ix_accounts_account_number'), table_name='accounts')
    op.create_index(op.f('ix_accounts_account_number'), 'accounts', ['account_number'], unique=True)
    op.create_index('ix_accounts_account_type_status', 'accounts', ['account_type', 'status'], unique=False)
    op.create_index('ix_accounts_customer_status', 'accounts', ['customer_id', 'status'], unique=False)
    op.create_index('ix_accounts_status_balance', 'accounts', ['status', 'balance'], unique=False)
    op.drop_constraint(op.f('accounts_created_by_fkey'), 'accounts', type_='foreignkey')
    op.drop_constraint(op.f('accounts_updated_by_fkey'), 'accounts', type_='foreignkey')
    op.drop_constraint(op.f('accounts_customer_id_fkey'), 'accounts', type_='foreignkey')
    op.create_foreign_key(None, 'accounts', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'accounts', 'customers', ['customer_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key(None, 'accounts', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    
    # ===== USERS TABLE CHANGES =====
    op.add_column('users', sa.Column('customer_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False,
               existing_server_default=sa.text('now()'))
    
    op.create_index(op.f('ix_users_customer_id'), 'users', ['customer_id'], unique=False)
    op.create_foreign_key(None, 'users', 'customers', ['customer_id'], ['id'], ondelete='SET NULL')

def downgrade() -> None:
    # ... your downgrade code ...
    pass