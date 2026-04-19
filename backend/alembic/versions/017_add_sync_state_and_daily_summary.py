"""Add sync_state and daily_attendance_summary tables

Revision ID: 017
Revises: 016
Create Date: 2026-03-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    # Create sync_state table
    op.create_table(
        'sync_state',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('device_user_id', sa.String(50), nullable=False),
        sa.Column('device_serial', sa.String(50), nullable=False),
        sa.Column('last_processed_timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_sync_state_device_user_id', 'sync_state', ['device_user_id'], unique=True)
    
    # Create daily_attendance_summary table with unique constraint in table definition
    op.create_table(
        'daily_attendance_summary',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('person_id', sa.String(36), nullable=False),
        sa.Column('person_name', sa.String(100), nullable=True),
        sa.Column('person_type', sa.String(10), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('first_check_in', sa.DateTime(), nullable=True),
        sa.Column('last_check_out', sa.DateTime(), nullable=True),
        sa.Column('total_time_minutes', sa.Integer(), nullable=True),
        sa.Column('visit_count', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('date', 'person_id', name='unique_person_date')
    )
    op.create_index('ix_daily_attendance_summary_date', 'daily_attendance_summary', ['date'])
    op.create_index('ix_daily_attendance_summary_person_id', 'daily_attendance_summary', ['person_id'])


def downgrade():
    op.drop_table('daily_attendance_summary')
    op.drop_table('sync_state')
