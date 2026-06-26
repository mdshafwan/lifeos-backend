"""vision_board_enums_to_strings

Revision ID: b0f1b5fc1ef5
Revises: xxxxx
Create Date: 2026-06-22 15:55:30.413241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0f1b5fc1ef5'
down_revision: Union[str, None] = 'xxxxx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert enum columns to plain VARCHAR
    op.alter_column('vision_boards', 'item_type',
                    type_=sa.String(20),
                    existing_nullable=False,
                    postgresql_using='item_type::text')
    
    op.alter_column('vision_boards', 'size',
                    type_=sa.String(20),
                    existing_nullable=False,
                    postgresql_using='size::text')
    
    op.alter_column('vision_boards', 'category',
                    type_=sa.String(50),
                    existing_nullable=False,
                    postgresql_using='category::text')
    
    # Drop the now-unused enum types
    op.execute("DROP TYPE IF EXISTS visionitemtype CASCADE")
    op.execute("DROP TYPE IF EXISTS visionitemsize CASCADE")
    op.execute("DROP TYPE IF EXISTS visioncategory CASCADE")


def downgrade() -> None:
    pass