"""Add description field to transactions

Revision ID: 019_add_transaction_description
Revises: 018_add_transaction_reverse_fields
Create Date: 2026-05-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019_add_transaction_description'
down_revision = '018_add_transaction_reverse_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add description column to transactions table
    op.add_column('transactions', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    # Remove description column from transactions table
    op.drop_column('transactions', 'description')
