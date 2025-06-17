from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify,request
from app.models import  (User, Secteur, Domaine,
        SousDomaine, Reglementation,Theme, ReglementationSecteur,
        VersionReglementation, Article, Entreprise, EntrepriseSecteur, EntrepriseReglementation)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,DateField,SelectMultipleField, EmailField
from wtforms.validators import DataRequired, Length, Email

from flask_login import login_required, current_user
from app.routes.admin import role_required

bp = Blueprint('article', __name__)


class ArticleForm(FlaskForm):
    numero = StringField('Numéro', validators=[DataRequired()])
    titre = StringField('Titre')
    contenu = TextAreaField('Contenu', validators=[DataRequired()])

    submit = SubmitField('Ajouter Article')

@bp.route('/modifier-article/<int:article_id>', methods=['GET', 'POST'])
@role_required(['ADMIN'])
def modifier_article(article_id):
    # Récupérer l'article à modifier
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)

    if form.validate_on_submit():
        # Mise à jour des champs
        article.numero = form.numero.data
        article.titre = form.titre.data
        article.contenu = form.contenu.data

        # Enregistrer les modifications
        db.session.commit()

        flash('Article modifié avec succès.', 'success')
        return redirect(url_for('reglementation.detail_reglementation', id=article.reglementation_id))

    return render_template('articles/modifier_article.html', form=form, article=article)


@bp.route('/supprimer-article/<int:article_id>', methods=['POST'])
@role_required(['ADMIN'])
def supprimer_article(article_id):
    # Récupérer l'article à supprimer
    article = Article.query.get_or_404(article_id)
    reglementation_id = article.reglementation_id

    # Supprimer l'article de la base de données
    db.session.delete(article)
    db.session.commit()

    flash('Article supprimé avec succès.', 'success')
    return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))
