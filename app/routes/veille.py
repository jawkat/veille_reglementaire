from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify,request, abort, jsonify
from app.models import  (User, Secteur, Domaine,
        SousDomaine, Reglementation,Theme, ReglementationSecteur,EntrepriseReglementation,
        VersionReglementation, Article, Entreprise, EntrepriseSecteur,Evaluation, ConformeEnum, ApplicableEnum)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,DateField,SelectMultipleField, EmailField, BooleanField
from wtforms.validators import DataRequired, Length, Email

from flask_login import login_required, current_user
from app.routes.admin import role_required


bp = Blueprint('veille', __name__)

@bp.route('/evaluations/<int:reglementation_id>/<int:entreprise_id>')
def afficher_evaluations(reglementation_id, entreprise_id):
    # Charger la réglementation et ses articles
    reglementation = Reglementation.query.get_or_404(reglementation_id)
    articles = Article.query.filter_by(reglementation_id=reglementation_id).all()

    # Charger les évaluations existantes pour les articles et l'entreprise
    evaluations = Evaluation.query.filter(
        Evaluation.entreprise_id == entreprise_id,
        Evaluation.article_id.in_([article.id for article in articles])
    ).all()

    # Créer un dictionnaire des évaluations avec article_id comme clé
    evaluations_dict = {evaluation.article_id: evaluation for evaluation in evaluations}

    # Récupérer la relation entre l'entreprise et la réglementation
    entreprise_reglementation = EntrepriseReglementation.query.filter_by(
        entreprise_id=entreprise_id,
        reglementation_id=reglementation_id
    ).first()

    if entreprise_reglementation:
        entreprise_reglementation.mettre_a_jour_score()

    # Vérifier si la relation existe et récupérer la valeur de suivi
    suivi = entreprise_reglementation.suivi if entreprise_reglementation else None

    # Rendu du modèle
    return render_template(
        'evaluation/evaluations.html',
        reglementation=reglementation,
        articles=articles,
        evaluations_dict=evaluations_dict,
        entreprise_id=entreprise_id,
        suivi=suivi
    )



class ModifierEvaluationForm(FlaskForm):
    applicable = SelectField(
        'Applicable',
        choices=[(choice.name, choice.value) for choice in ApplicableEnum],
        validators=[DataRequired()]
    )
    conforme = SelectField(
        'Conforme',
        choices=[(choice.name, choice.value) for choice in ConformeEnum],
        validators=[DataRequired()]
    )
    champ_d_application = TextAreaField('Champ d\'application')
    commentaires = TextAreaField('Commentaires')
    submit = SubmitField('Modifier')


@bp.route('/modifier_evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
def modifier_evaluation(evaluation_id):
    # Charger l'évaluation à modifier
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    form = ModifierEvaluationForm(obj=evaluation)

    if form.validate_on_submit():
        # Mettre à jour les champs avec les données du formulaire
        evaluation.applicable = ApplicableEnum[form.applicable.data]
        evaluation.conforme = ConformeEnum[form.conforme.data]
        evaluation.champ_d_application = form.champ_d_application.data
        evaluation.commentaires = form.commentaires.data

        # Sauvegarder les modifications dans la base de données
        try:
            db.session.commit()
            
           # Obtenir l'instance de EntrepriseReglementation associée et mettre à jour le score
            entreprise_reglementation = EntrepriseReglementation.query.filter_by(
                reglementation_id=evaluation.article.reglementation_id,
                entreprise_id=evaluation.entreprise_id
            ).first()

            if entreprise_reglementation:
                entreprise_reglementation.mettre_a_jour_score()  # Appeler la méthode sur l'objet EntrepriseReglementation


            flash('Évaluation modifiée avec succès.', 'success')
            return redirect(url_for('veille.afficher_evaluations', 
                                    reglementation_id=evaluation.article.reglementation_id, 
                                    entreprise_id=evaluation.entreprise_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur s\'est produite : {e}', 'danger')

    return render_template('evaluation/modifier_evaluation.html', form=form, evaluation=evaluation)