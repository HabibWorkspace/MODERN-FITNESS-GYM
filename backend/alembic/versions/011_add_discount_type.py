"""add discount_type to transactions

Revision ID: 011_add_discount_type
Revises: 010_add_transaction_fees
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011_add_discount_type'
down_revision = '010_add_transaction_fees'
branch_labels = None
depends_on = None


def upgrade():
    # Add discount_type column to transactions table
    op.add_column('transactions', sa.Column('discount_type', sa.String(20), server_default='fixed', nullable=True))


def downgrade():
    # Remove discount_type column
    op.drop_column('transactions', 'discount_type')
