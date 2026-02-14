"""Add trainer_id to member_profiles

Revision ID: 007_add_trainer_to_member
Revises: 006_add_member_personal_fields
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_trainer_to_member'
down_revision = '006_add_member_personal_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add trainer_id column to member_profiles (SQLite doesn't support adding FK constraints directly)
    op.add_column('member_profiles', sa.Column('trainer_id', sa.String(36), nullable=True))


def downgrade():
    # Remove trainer_id column
    op.drop_column('member_profiles', 'trainer_id')
