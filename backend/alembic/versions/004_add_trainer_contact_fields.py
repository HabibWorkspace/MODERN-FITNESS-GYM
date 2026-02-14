"""add trainer contact fields

Revision ID: 004_add_trainer_contact_fields
Revises: 003_add_password_reset
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_trainer_contact_fields'
down_revision = '003_add_password_reset'
branch_labels = None
depends_on = None


def upgrade():
    # Add phone, cnic, and email columns to trainer_profiles table
    op.add_column('trainer_profiles', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('trainer_profiles', sa.Column('cnic', sa.String(20), nullable=True))
    op.add_column('trainer_profiles', sa.Column('email', sa.String(100), nullable=True))


def downgrade():
    # Remove phone, cnic, and email columns from trainer_profiles table
    op.drop_column('trainer_profiles', 'email')
    op.drop_column('trainer_profiles', 'cnic')
    op.drop_column('trainer_profiles', 'phone')
