"""add role level sort_order unit

Revision ID: a9d3f6e2b1c4
Revises: 1d274621db78
Create Date: 2026-06-14 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9d3f6e2b1c4'
down_revision: Union[str, Sequence[str], None] = '1d274621db78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # add columns with temporary server defaults so existing rows are populated
    op.add_column('roles', sa.Column('level', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('roles', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('roles', sa.Column('unit_id', sa.Integer(), nullable=True))

    # create foreign key for unit_id
    op.create_foreign_key('fk_roles_unit_id_units', 'roles', 'units', ['unit_id'], ['id'], ondelete='SET NULL')

    # assign unique sort_order per (company_id, level) for existing rows
    op.execute(
        """
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY company_id, level ORDER BY id) as rn
            FROM roles
        )
        UPDATE roles
        SET sort_order = numbered.rn
        FROM numbered
        WHERE roles.id = numbered.id;
        """
    )

    # unique constraints
    op.create_unique_constraint('uq_roles_company_name', 'roles', ['company_id', 'name'])
    op.create_unique_constraint('uq_roles_company_level_sort', 'roles', ['company_id', 'level', 'sort_order'])

    # remove server defaults
    op.alter_column('roles', 'level', server_default=None)
    op.alter_column('roles', 'sort_order', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_roles_company_level_sort', 'roles', type_='unique')
    op.drop_constraint('uq_roles_company_name', 'roles', type_='unique')
    op.drop_constraint('fk_roles_unit_id_units', 'roles', type_='foreignkey')
    op.drop_column('roles', 'unit_id')
    op.drop_column('roles', 'sort_order')
    op.drop_column('roles', 'level')
