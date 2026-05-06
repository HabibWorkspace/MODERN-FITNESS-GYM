"""add transaction description

Revision ID: 019
Revises: 018
Create Date: 2026-05-07 04:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    # Add description field to transactions table
    op.add_column('transactions', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    # Remove description field from transactions table
    op.drop_column('transactions', 'description')
