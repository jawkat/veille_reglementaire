from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify,request, abort, jsonify
from app.models import  (User, Secteur, Domaine,
        SousDomaine, Reglementation,Theme, ReglementationSecteur,
        VersionReglementation, Article, Entreprise, EntrepriseSecteur,Evaluation)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,DateField,SelectMultipleField, EmailField, BooleanField
from wtforms.validators import DataRequired, Length, Email

from flask_login import login_required, current_user
from app.routes.admin import role_required


bp = Blueprint('veille', __name__)

@bp.route('/entreprise/<int:entreprise_id>/reglementation/<int:reglementation_id>')
def afficher_evaluations(entreprise_id, reglementation_id):
    reglementation=Reglementation.query.filter_by(id=reglementation_id).first()
    # Charger les articles de la réglementation
    articles = Article.query.filter_by(reglementation_id=reglementation_id).all()
    # Charger les évaluations pour cette entreprise
    evaluations = Evaluation.query.filter_by(entreprise_id=entreprise_id).all()
    return render_template('evaluation/evaluations.html', articles=articles, evaluations=evaluations, entreprise_id=entreprise_id, reglementation=reglementation)


class ModifierEvaluationForm(FlaskForm):
    applicable = BooleanField("Applicable")
    conforme = BooleanField("Conforme")
    champ_d_application = TextAreaField("Champ d'application", validators=[DataRequired()])
    commentaires = TextAreaField("Commentaires", validators=[DataRequired()])
    submit = SubmitField("Sauvegarder")



@bp.route('/evaluation/<int:evaluation_id>/modifier', methods=['GET', 'POST'])
def modifier_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    form = ModifierEvaluationForm(obj=evaluation)  # Pré-remplit le formulaire avec les données existantes

    if form.validate_on_submit():
        # Mise à jour des données de l'évaluation
        evaluation.applicable = form.applicable.data
        evaluation.conforme = form.conforme.data
        evaluation.champ_d_application = form.champ_d_application.data
        evaluation.commentaires = form.commentaires.data

        # Sauvegarde dans la base de données
        db.session.commit()
        flash("L'évaluation a été mise à jour avec succès.", "success")
        return redirect(url_for('veille.afficher_evaluations'))  # Redirection vers la liste des évaluations

    return render_template('evaluation/modifier_evaluation.html', form=form, evaluation=evaluation)
