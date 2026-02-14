"""Add member personal fields

Revision ID: 006_add_member_personal_fields
Revises: 005_add_settings_table
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_member_personal_fields'
down_revision = '005_add_settings_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add gender, date_of_birth, and admission_date columns to member_profiles
    op.add_column('member_profiles', sa.Column('gender', sa.String(10), nullable=True))
    op.add_column('member_profiles', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('member_profiles', sa.Column('admission_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('member_profiles', 'admission_date')
    op.drop_column('member_profiles', 'date_of_birth')
    op.drop_column('member_profiles', 'gender')
