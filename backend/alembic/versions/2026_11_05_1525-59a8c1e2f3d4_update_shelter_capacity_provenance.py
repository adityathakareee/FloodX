"""update_shelter_capacity_provenance

Revision ID: 59a8c1e2f3d4
Revises: 482a93df1b7c
Create Date: 2026-11-05 15:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59a8c1e2f3d4'
down_revision: Union[str, None] = '482a93df1b7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter current_occupancy to be nullable with default NULL
    op.alter_column('shelters', 'current_occupancy',
                    existing_type=sa.Integer(),
                    nullable=True,
                    existing_nullable=False,
                    server_default=None)

    # 2. Add evidence provenance columns
    op.add_column('shelters', sa.Column('evidence_document', sa.String(length=255), nullable=True))
    op.add_column('shelters', sa.Column('evidence_date', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('shelters', 'evidence_date')
    op.drop_column('shelters', 'evidence_document')
    op.alter_column('shelters', 'current_occupancy',
                    existing_type=sa.Integer(),
                    nullable=False,
                    existing_nullable=True,
                    server_default='0')

