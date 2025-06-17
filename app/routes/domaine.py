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
import logging

bp = Blueprint('domaine', __name__)



class DomaineForm(FlaskForm):
    nom = StringField('Nom du Domaine', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Ajouter Domaine')

@bp.route('/ajouter-domaine', methods=['GET', 'POST'])
def ajouter_domaine():
    form = DomaineForm()
    if form.validate_on_submit():
        existing_domaine = Domaine.query.filter_by(nom=form.nom.data).first()
        if existing_domaine:
            flash("Un domaine avec ce nom existe déjà.", "warning")
            return redirect(url_for('domaine.ajouter_domaine'))

        nouveau_domaine = Domaine(nom=form.nom.data, description=form.description.data)
        db.session.add(nouveau_domaine)
        db.session.commit()
        flash("Domaine ajouté avec succès.", "success")
        return redirect(url_for('domaine.liste_domaines'))

    return render_template('domaine/ajouter_domaine.html', form=form)


@bp.route('/domaines', methods=['GET'])
@role_required('ADMIN')
def liste_domaines():
    try:
        domaines = Domaine.query.all()
        return render_template('domaine/liste_domaines.html', domaines=domaines)
    except Exception as e:
        flash(f"Erreur lors de la récupération des domaines : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur



class SousDomaineForm(FlaskForm):
    nom = StringField('Nom du Sous-Domaine', validators=[DataRequired()])
    description = TextAreaField('Description')
    domaine_id = SelectField('Domaine', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Ajouter Sous-Domaine')

@bp.route('/ajouter-sous-domaine', methods=['GET', 'POST'])
def ajouter_sous_domaine():
    form = SousDomaineForm()
    form.domaine_id.choices = [(d.id, d.nom) for d in Domaine.query.all()]
    if form.validate_on_submit():
        existing_sous_domaine = SousDomaine.query.filter_by(nom=form.nom.data).first()
        if existing_sous_domaine:
            flash("Un sous-domaine avec ce nom existe déjà.", "warning")
            return redirect(url_for('domaine.ajouter_sous_domaine'))

        sous_domaine = SousDomaine(
            nom=form.nom.data,
            description=form.description.data,
            domaine_id=form.domaine_id.data
        )
        db.session.add(sous_domaine)
        db.session.commit()
        flash("Sous-domaine ajouté avec succès.", "success")
        return redirect(url_for('domaine.liste_sous_domaines'))

    return render_template('domaine/ajouter_sous_domaine.html', form=form)

@bp.route('/sous-domaines', methods=['GET'])
@role_required('ADMIN')
def liste_sous_domaines():
    try:
        sous_domaines = SousDomaine.query.all()
        return render_template('domaine/liste_sous_domaines.html', sous_domaines=sous_domaines)
    except Exception as e:
        flash(f"Erreur lors de la récupération des sous-domaines : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur




@bp.route('/get_sous_domaines/<int:domaine_id>', methods=['GET'])
def get_sous_domaines(domaine_id):
    try:
        sous_domaines = SousDomaine.query.filter_by(domaine_id=domaine_id).all()
        sous_domaines_data = [{'id': s.id, 'nom': s.nom} for s in sous_domaines]
        return jsonify(sous_domaines_data)
    except Exception as e:
        return jsonify({'error': f"Erreur lors du chargement des sous-domaines : {str(e)}"}), 500

