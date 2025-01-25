"""enlever  uuid

Revision ID: 51927222f69f
Revises: 31892a1711e6
Create Date: 2025-01-25 10:03:18.304931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51927222f69f'
down_revision = '31892a1711e6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utilisateur', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.Integer(),
               existing_nullable=False,
               autoincrement=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('utilisateur', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False,
               autoincrement=True)

    # ### end Alembic commands ###
