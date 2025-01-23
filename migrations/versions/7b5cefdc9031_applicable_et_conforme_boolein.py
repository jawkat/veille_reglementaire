"""applicable et conforme boolein 

Revision ID: 7b5cefdc9031
Revises: 751fdee4ad99
Create Date: 2025-01-23 23:59:05.052201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b5cefdc9031'
down_revision = '751fdee4ad99'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.alter_column('applicable',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.Boolean(),
               existing_nullable=False)
        batch_op.alter_column('conforme',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.Boolean(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.alter_column('conforme',
               existing_type=sa.Boolean(),
               type_=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('applicable',
               existing_type=sa.Boolean(),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)

    # ### end Alembic commands ###
