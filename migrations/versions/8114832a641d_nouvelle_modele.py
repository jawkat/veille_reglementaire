"""nouvelle modele

Revision ID: 8114832a641d
Revises: 
Create Date: 2025-02-07 22:18:35.518673

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8114832a641d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entreprise_reglementation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('niveau_risque', sa.Enum('FAIBLE', 'MOYEN', 'ELEVE', 'CRITIQUE', name='severiteenum'), nullable=True))
        batch_op.add_column(sa.Column('impact_financier', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('probabilite', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('date_derniere_evaluation', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('frequence_revision', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('prochaine_revision', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('responsable_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('date_ajout', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('commentaires', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('statut_implementation', sa.String(length=50), nullable=True))
        batch_op.create_foreign_key('fk_responsable_id', 'utilisateur', ['responsable_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entreprise_reglementation', schema=None) as batch_op:
        batch_op.drop_constraint('fk_responsable_id', type_='foreignkey')
        batch_op.drop_column('statut_implementation')
        batch_op.drop_column('commentaires')
        batch_op.drop_column('date_ajout')
        batch_op.drop_column('responsable_id')
        batch_op.drop_column('prochaine_revision')
        batch_op.drop_column('frequence_revision')
        batch_op.drop_column('date_derniere_evaluation')
        batch_op.drop_column('probabilite')
        batch_op.drop_column('impact_financier')
        batch_op.drop_column('niveau_risque')

    # ### end Alembic commands ###
