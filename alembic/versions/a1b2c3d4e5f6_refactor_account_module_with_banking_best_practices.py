"""refactor account module with banking best practices

Revision ID: a1b2c3d4e5f6
Revises: 71fa080e24ae
Create Date: 2026-06-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '71fa080e24ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        BEGIN;
        DROP TABLE IF EXISTS accounts CASCADE;

        CREATE TYPE accounttype AS ENUM ('savings', 'current');
        CREATE TYPE accountstatus AS ENUM ('ACTIVE', 'DORMANT', 'FROZEN', 'BLOCKED', 'CLOSED');

        CREATE TABLE accounts (
            id SERIAL PRIMARY KEY,
            account_number VARCHAR(20) NOT NULL UNIQUE,
            account_type accounttype NOT NULL,
            balance NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
            currency VARCHAR(3) NOT NULL DEFAULT 'NPR',
            status accountstatus NOT NULL DEFAULT 'ACTIVE',
            is_active BOOLEAN NOT NULL DEFAULT true,
            opened_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            closed_at TIMESTAMP WITH TIME ZONE,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_accounts_id ON accounts(id);
        CREATE INDEX ix_accounts_account_number ON accounts(account_number);
        CREATE INDEX ix_accounts_account_type ON accounts(account_type);
        CREATE INDEX ix_accounts_customer_id ON accounts(customer_id);
        CREATE INDEX ix_accounts_status ON accounts(status);

        COMMIT;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        BEGIN;
        DROP TABLE IF EXISTS accounts CASCADE;
        DROP TYPE IF EXISTS accountstatus;
        DROP TYPE IF EXISTS accounttype;
        COMMIT;
    """)
