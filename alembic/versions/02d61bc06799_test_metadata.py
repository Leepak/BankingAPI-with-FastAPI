revision = '02d61bc06799'
down_revision = 'b2c3d4e5f6g7'
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.Enum(
                'ADMIN',
                'CUSTOMER',
                name='userrole'
            ),
            nullable=False,
            server_default='CUSTOMER'
        )
    )

def downgrade() -> None:
    op.drop_column('users', 'role')