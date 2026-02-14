"""add transaction fees and discount

Revision ID: 010_add_transaction_fees
Revises: 009a_remove_gym_contact_info
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_transaction_fees'
down_revision = '009a_remove_gym_contact_info'
branch_labels = None
depends_on = None


def upgrade():
    # Add trainer_fee and discount_amount columns to transactions table
    op.add_column('transactions', sa.Column('trainer_fee', sa.Numeric(10, 2), server_default='0', nullable=True))
    op.add_column('transactions', sa.Column('discount_amount', sa.Numeric(10, 2), server_default='0', nullable=True))


def downgrade():
    # Remove trainer_fee and discount_amount columns
    op.drop_column('transactions', 'discount_amount')
    op.drop_column('transactions', 'trainer_fee')
