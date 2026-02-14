"""Add password reset token fields to users table.

Revision ID: 003_add_password_reset
Revises: 002_add_plain_password
Create Date: 2026-02-05 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_password_reset'
down_revision = '002_add_plain_password'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the plain text password column if it exists
    try:
        op.drop_column('users', 'password')
    except:
        pass
    
    # Add password reset fields (without unique constraint for SQLite compatibility)
    op.add_column('users', sa.Column('reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('reset_token_expiry', sa.DateTime, nullable=True))


def downgrade():
    # Remove password reset fields
    op.drop_column('users', 'reset_token')
    op.drop_column('users', 'reset_token_expiry')
