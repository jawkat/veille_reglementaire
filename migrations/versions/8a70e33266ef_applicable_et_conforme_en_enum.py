"""applicable et conforme en enum 

Revision ID: 8a70e33266ef
Revises: 7b5cefdc9031
Create Date: 2025-01-24 10:55:58.989337

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a70e33266ef'
down_revision = '7b5cefdc9031'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.alter_column('applicable',
               existing_type=sa.BOOLEAN(),
               type_=sa.Enum('OUI', 'NON_EVALUE', 'NON', name='applicableenum'),
               existing_nullable=False)
        batch_op.alter_column('conforme',
               existing_type=sa.BOOLEAN(),
               type_=sa.Enum('CONFORME', 'NON_EVALUE', 'NON_CONFORME', name='conformeenum'),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.alter_column('conforme',
               existing_type=sa.Enum('CONFORME', 'NON_EVALUE', 'NON_CONFORME', name='conformeenum'),
               type_=sa.BOOLEAN(),
               existing_nullable=False)
        batch_op.alter_column('applicable',
               existing_type=sa.Enum('OUI', 'NON_EVALUE', 'NON', name='applicableenum'),
               type_=sa.BOOLEAN(),
               existing_nullable=False)

    # ### end Alembic commands ###
