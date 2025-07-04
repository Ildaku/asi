"""Add expiration_date to raw_materials

Revision ID: b0dfb14a93c8
Revises: 9b47a33d2182
Create Date: 2025-06-25 10:19:00.118591

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0dfb14a93c8'
down_revision = '9b47a33d2182'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('raw_materials', schema=None) as batch_op:
        batch_op.add_column(sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=7),
               type_=sa.Enum('ADMIN', 'OPERATOR', name='userrole'),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.Enum('ADMIN', 'OPERATOR', name='userrole'),
               type_=sa.VARCHAR(length=7),
               existing_nullable=True)

    with op.batch_alter_table('raw_materials', schema=None) as batch_op:
        batch_op.drop_column('expiration_date')

    # ### end Alembic commands ###
