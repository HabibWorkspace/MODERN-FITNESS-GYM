"""Add full_name to member_profiles

Revision ID: 009_add_full_name_to_members
Revises: 008_add_gym_contact_info
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_full_name_to_members'
down_revision = '008_add_gym_contact_info'
branch_labels = None
depends_on = None


def upgrade():
    # Add full_name column to member_profiles
    op.add_column('member_profiles', sa.Column('full_name', sa.String(100), nullable=True))


def downgrade():
    # Remove full_name column from member_profiles
    op.drop_column('member_profiles', 'full_name')
