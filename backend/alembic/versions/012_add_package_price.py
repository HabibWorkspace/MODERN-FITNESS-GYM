"""add package_price to transactions

Revision ID: 012_add_package_price
Revises: 011_add_discount_type
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_package_price'
down_revision = '011_add_discount_type'
branch_labels = None
depends_on = None


def upgrade():
    # Add package_price column to transactions table
    op.add_column('transactions', sa.Column('package_price', sa.Numeric(10, 2), nullable=True, default=0))


def downgrade():
    # Remove package_price column from transactions table
    op.drop_column('transactions', 'package_price')
