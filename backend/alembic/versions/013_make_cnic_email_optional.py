"""Make CNIC and email optional for members

Revision ID: 013_make_cnic_email_optional
Revises: 012_add_package_price
Create Date: 2026-02-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_make_cnic_email_optional'
down_revision = '012_add_package_price'
branch_labels = None
depends_on = None


def upgrade():
    # Make CNIC and email nullable
    with op.batch_alter_table('member_profiles', schema=None) as batch_op:
        batch_op.alter_column('cnic',
                              existing_type=sa.String(20),
                              nullable=True)
        batch_op.alter_column('email',
                              existing_type=sa.String(100),
                              nullable=True)
        # Drop unique constraints if they exist
        # SQLite doesn't support dropping constraints directly, so we skip this
        # The unique=False in the model will handle it


def downgrade():
    # Revert changes
    with op.batch_alter_table('member_profiles', schema=None) as batch_op:
        batch_op.alter_column('cnic',
                              existing_type=sa.String(20),
                              nullable=False)
        batch_op.alter_column('email',
                              existing_type=sa.String(100),
                              nullable=False)
