"""Remove gym address and contact info from settings.

Revision ID: 009a_remove_gym_contact_info
Revises: 009_add_full_name_to_members
Create Date: 2026-02-11 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009a_remove_gym_contact_info'
down_revision = '009_add_full_name_to_members'
branch_labels = None
depends_on = None


def upgrade():
    # Remove gym_address and gym_phone columns from settings table
    op.drop_column('settings', 'gym_phone')
    op.drop_column('settings', 'gym_address')


def downgrade():
    # Add gym_address and gym_phone columns back
    op.add_column('settings', sa.Column('gym_address', sa.String(500), nullable=True))
    op.add_column('settings', sa.Column('gym_phone', sa.String(50), nullable=True))
