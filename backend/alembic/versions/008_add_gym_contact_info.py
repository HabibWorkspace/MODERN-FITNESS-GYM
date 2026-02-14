"""Add gym contact information to settings

Revision ID: 008_add_gym_contact_info
Revises: 007_add_trainer_to_member
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_gym_contact_info'
down_revision = '007_add_trainer_to_member'
branch_labels = None
depends_on = None


def upgrade():
    # Add gym_address and gym_phone columns to settings table
    op.add_column('settings', sa.Column('gym_address', sa.String(500), nullable=True))
    op.add_column('settings', sa.Column('gym_phone', sa.String(50), nullable=True))


def downgrade():
    # Remove gym_address and gym_phone columns
    op.drop_column('settings', 'gym_phone')
    op.drop_column('settings', 'gym_address')
