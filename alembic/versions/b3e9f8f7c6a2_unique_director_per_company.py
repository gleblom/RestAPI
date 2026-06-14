"""unique director per company

Revision ID: b3e9f8f7c6a2
Revises: a9d3f6e2b1c4
Create Date: 2026-06-14 12:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e9f8f7c6a2'
down_revision: Union[str, Sequence[str], None] = 'a9d3f6e2b1c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # create a partial unique index to ensure only one role with level=100 per company
    op.create_index(
        'uq_roles_company_director',
        'roles',
        ['company_id'],
        unique=True,
        postgresql_where=sa.text('level = 100'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_roles_company_director', table_name='roles')
