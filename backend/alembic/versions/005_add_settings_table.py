"""Add settings table

Revision ID: 005_add_settings_table
Revises: 004_add_trainer_contact_fields
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_settings_table'
down_revision = '004_add_trainer_contact_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admission_fee', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert default settings row
    op.execute("INSERT INTO settings (admission_fee) VALUES (0)")


def downgrade():
    op.drop_table('settings')
