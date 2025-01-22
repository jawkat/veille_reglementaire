"""Remove secteur_id foreign key

Revision ID: 56f4b2191e22
Revises: 
Create Date: 2025-01-22 15:12:11.028499

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56f4b2191e22'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('entreprise') as batch_op:
        batch_op.drop_column('secteur_id')

def downgrade():
    with op.batch_alter_table('entreprise') as batch_op:
        batch_op.add_column(sa.Column('secteur_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(None, 'secteur', ['secteur_id'], ['id'])

