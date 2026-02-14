"""Initial database schema creation.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite, postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'trainer', 'member', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create packages table
    op.create_table(
        'packages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create member_profiles table
    op.create_table(
        'member_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('cnic', sa.String(20), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('admission_fee_paid', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('current_package_id', sa.String(36)),
        sa.Column('package_start_date', sa.DateTime()),
        sa.Column('package_expiry_date', sa.DateTime()),
        sa.Column('is_frozen', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['current_package_id'], ['packages.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_member_profiles_cnic'), 'member_profiles', ['cnic'], unique=True)
    op.create_index(op.f('ix_member_profiles_email'), 'member_profiles', ['email'], unique=True)
    op.create_index(op.f('ix_member_profiles_phone'), 'member_profiles', ['phone'], unique=True)

    # Create trainer_profiles table
    op.create_table(
        'trainer_profiles',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('specialization', sa.String(100), nullable=False),
        sa.Column('salary_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('hire_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # Create attendance table
    op.create_table(
        'attendance',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('method', sa.Enum('QR', 'GPS', 'QR+GPS', name='attendancemethod'), nullable=False),
        sa.Column('status', sa.Enum('success', 'failed', name='attendancestatus'), nullable=False),
        sa.Column('latitude', sa.Float()),
        sa.Column('longitude', sa.Float()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_attendance_user_id'), 'attendance', ['user_id'], unique=False)

    # Create diet_logs table
    op.create_table(
        'diet_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('member_id', sa.String(36), nullable=False),
        sa.Column('food_name', sa.String(200), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('protein_g', sa.Float(), nullable=False),
        sa.Column('carbs_g', sa.Float(), nullable=False),
        sa.Column('fats_g', sa.Float(), nullable=False),
        sa.Column('logged_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['member_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_diet_logs_logged_date'), 'diet_logs', ['logged_date'], unique=False)
    op.create_index(op.f('ix_diet_logs_member_id'), 'diet_logs', ['member_id'], unique=False)

    # Create progress_metrics table
    op.create_table(
        'progress_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('member_id', sa.String(36), nullable=False),
        sa.Column('metric_type', sa.Enum('weight', 'bmi', 'body_fat', name='metrictype'), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('recorded_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['member_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_progress_metrics_member_id'), 'progress_metrics', ['member_id'], unique=False)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('member_id', sa.String(36), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('transaction_type', sa.Enum('ADMISSION', 'PACKAGE', 'PAYMENT', name='transactiontype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'OVERDUE', name='transactionstatus'), nullable=False),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('paid_date', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['member_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_transactions_member_id'), 'transactions', ['member_id'], unique=False)

    # Create workout_routines table
    op.create_table(
        'workout_routines',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('trainer_id', sa.String(36), nullable=False),
        sa.Column('member_id', sa.String(36), nullable=False),
        sa.Column('routine_name', sa.String(200), nullable=False),
        sa.Column('exercises', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['member_profiles.id'], ),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainer_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workout_routines_trainer_id'), 'workout_routines', ['trainer_id'], unique=False)

    # Create trainer_feedbacks table
    op.create_table(
        'trainer_feedbacks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('trainer_id', sa.String(36), nullable=False),
        sa.Column('member_id', sa.String(36), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('feedback_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['member_profiles.id'], ),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainer_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_trainer_feedbacks_trainer_id'), 'trainer_feedbacks', ['trainer_id'], unique=False)

    # Create trainer_attendance table
    op.create_table(
        'trainer_attendance',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('trainer_id', sa.String(36), nullable=False),
        sa.Column('check_in_time', sa.DateTime(), nullable=False),
        sa.Column('check_out_time', sa.DateTime()),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainer_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_trainer_attendance_attendance_date'), 'trainer_attendance', ['attendance_date'], unique=False)
    op.create_index(op.f('ix_trainer_attendance_trainer_id'), 'trainer_attendance', ['trainer_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_trainer_attendance_trainer_id'), table_name='trainer_attendance')
    op.drop_index(op.f('ix_trainer_attendance_attendance_date'), table_name='trainer_attendance')
    op.drop_table('trainer_attendance')
    op.drop_index(op.f('ix_trainer_feedbacks_trainer_id'), table_name='trainer_feedbacks')
    op.drop_table('trainer_feedbacks')
    op.drop_index(op.f('ix_workout_routines_trainer_id'), table_name='workout_routines')
    op.drop_table('workout_routines')
    op.drop_index(op.f('ix_transactions_member_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_progress_metrics_member_id'), table_name='progress_metrics')
    op.drop_table('progress_metrics')
    op.drop_index(op.f('ix_diet_logs_member_id'), table_name='diet_logs')
    op.drop_index(op.f('ix_diet_logs_logged_date'), table_name='diet_logs')
    op.drop_table('diet_logs')
    op.drop_index(op.f('ix_attendance_user_id'), table_name='attendance')
    op.drop_table('attendance')
    op.drop_table('trainer_profiles')
    op.drop_index(op.f('ix_member_profiles_phone'), table_name='member_profiles')
    op.drop_index(op.f('ix_member_profiles_email'), table_name='member_profiles')
    op.drop_index(op.f('ix_member_profiles_cnic'), table_name='member_profiles')
    op.drop_table('member_profiles')
    op.drop_table('packages')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
