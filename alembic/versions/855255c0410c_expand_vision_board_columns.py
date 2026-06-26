"""expand_vision_board_columns

Revision ID: xxxxx
Revises: c7ddf4ff6d2f
Create Date: xxxx
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'xxxxx'  # Keep the auto-generated ID
down_revision: Union[str, None] = 'c7ddf4ff6d2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # Create new enum types (with checkfirst to avoid duplicate errors)
    # ──────────────────────────────────────────────
    bind = op.get_bind()
    
    # Create visionitemtype enum if not exists
    bind.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE visionitemtype AS ENUM ('image', 'text', 'affirmation', 'quote', 'goal', 'letter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create visionitemsize enum if not exists
    bind.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE visionitemsize AS ENUM ('small', 'medium', 'large');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # ──────────────────────────────────────────────
    # Add new columns to vision_boards table
    # ──────────────────────────────────────────────
    
    # Type & display
    op.add_column('vision_boards',
        sa.Column('item_type',
            postgresql.ENUM('image', 'text', 'affirmation', 'quote', 'goal', 'letter',
                            name='visionitemtype', create_type=False),
            nullable=False, server_default='image'))
    
    op.add_column('vision_boards',
        sa.Column('size',
            postgresql.ENUM('small', 'medium', 'large',
                            name='visionitemsize', create_type=False),
            nullable=False, server_default='medium'))
    
    # Letter-specific
    op.add_column('vision_boards', sa.Column('mood', sa.String(50), nullable=True))
    op.add_column('vision_boards', sa.Column('delivery_date', sa.Date(), nullable=True))
    op.add_column('vision_boards', sa.Column('is_sealed', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Goal-specific
    op.add_column('vision_boards', sa.Column('progress', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('vision_boards', sa.Column('milestones', sa.JSON(), nullable=False, server_default='[]'))
    
    # Image-specific
    op.add_column('vision_boards', sa.Column('image_source', sa.String(20), nullable=True))
    
    # Change image_url to Text to support base64 data URLs (was VARCHAR(500))
    op.alter_column('vision_boards', 'image_url',
                    existing_type=sa.String(500),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    # Create index on item_type for fast filtering
    op.create_index('ix_vision_boards_item_type', 'vision_boards', ['item_type'])


def downgrade() -> None:
    op.drop_index('ix_vision_boards_item_type', table_name='vision_boards')
    op.alter_column('vision_boards', 'image_url',
                    existing_type=sa.Text(),
                    type_=sa.String(500),
                    existing_nullable=True)
    op.drop_column('vision_boards', 'image_source')
    op.drop_column('vision_boards', 'milestones')
    op.drop_column('vision_boards', 'progress')
    op.drop_column('vision_boards', 'is_sealed')
    op.drop_column('vision_boards', 'delivery_date')
    op.drop_column('vision_boards', 'mood')
    op.drop_column('vision_boards', 'size')
    op.drop_column('vision_boards', 'item_type')
    
    op.execute("DROP TYPE IF EXISTS visionitemsize")
    op.execute("DROP TYPE IF EXISTS visionitemtype")