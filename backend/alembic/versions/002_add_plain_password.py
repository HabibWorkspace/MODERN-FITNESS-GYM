"""Add plain text password field to users table.

Revision ID: 002_add_plain_password
Revises: 001
Create Date: 2026-02-05 03:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_plain_password'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add plain text password column
    op.add_column('users', sa.Column('password', sa.String(255), nullable=True))


def downgrade():
    # Remove plain text password column
    op.drop_column('users', 'password')
