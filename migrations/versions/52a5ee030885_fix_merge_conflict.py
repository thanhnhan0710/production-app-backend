"""fix merge conflict

Revision ID: 52a5ee030885
Revises: 144da03464af, f80e77f471af
Create Date: 2026-01-18 09:59:34.842912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52a5ee030885'
down_revision: Union[str, Sequence[str], None] = ('144da03464af', 'f80e77f471af')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
