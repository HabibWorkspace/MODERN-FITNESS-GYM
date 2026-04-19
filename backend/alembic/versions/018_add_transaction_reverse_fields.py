"""Add transaction reverse fields

Revision ID: 018
Revises: 017
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    # Add reversed_at column to track when payment was reversed
    op.add_column('transactions', sa.Column('reversed_at', sa.DateTime(), nullable=True))
    
    # Add reversed_by column to track who reversed the payment
    op.add_column('transactions', sa.Column('reversed_by', sa.String(36), nullable=True))
    
    # Add is_reversed boolean flag for quick filtering
    op.add_column('transactions', sa.Column('is_reversed', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('transactions', 'is_reversed')
    op.drop_column('transactions', 'reversed_by')
    op.drop_column('transactions', 'reversed_at')
