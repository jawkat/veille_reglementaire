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


bp = Blueprint('entreprise', __name__)


class EntrepriseForm(FlaskForm):
    nom = StringField('Nom de l\'entreprise', validators=[DataRequired()])
    description = TextAreaField('Description de l\'entreprise')
    pays = StringField('Pays', validators=[DataRequired()])
    date_creation = DateField('Date de Creation', format='%Y-%m-%d', validators=[DataRequired()], default=date.today)
    secteurs = SelectMultipleField('Secteurs', coerce=int, choices=[])  # champ de sélection multiple

    def __init__(self, *args, **kwargs):
        super(EntrepriseForm, self).__init__(*args, **kwargs)
        # Charger les secteurs dans le formulaire
        self.secteurs.choices = [(secteur.id, secteur.nom) for secteur in Secteur.query.all()]


class UserForm(FlaskForm):
    name = StringField('Nom de l\'utilisateur', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[
            ('RESPONSABLE','Responsable Veille'),
            ('COLLABORATEUR','Collaborateur')], validators=[DataRequired()])
    password = StringField('Mot de passe', validators=[DataRequired()])



@bp.route('/ajouter_entreprise_et_manager', methods=['GET', 'POST'])
@role_required(['ADMIN'])
def ajouter_entreprise_et_manager():
    entreprise_form = EntrepriseForm()
    user_form = UserForm()
    secteurs = Secteur.query.all()  # Récupérer tous les secteurs

    # Initialiser les choix pour le champ secteurs
    entreprise_form.secteurs.choices = [(secteur.id, secteur.nom) for secteur in secteurs]

    if entreprise_form.validate_on_submit() and user_form.validate_on_submit():
        # Vérifier si l'entreprise existe déjà
        entreprise = Entreprise.query.filter_by(nom=entreprise_form.nom.data).first()

        if not entreprise:
            # Créer l'entreprise
            entreprise = Entreprise(
                nom=entreprise_form.nom.data,
                description=entreprise_form.description.data,
                pays=entreprise_form.pays.data,
                date_creation= date.today()
            )
            db.session.add(entreprise)
            db.session.commit()

            # Associer les secteurs sélectionnés à l'entreprise
            secteurs_selectionnes = entreprise_form.secteurs.data
            for secteur_id in secteurs_selectionnes:
                entreprise_secteur = EntrepriseSecteur(
                    entreprise_id=entreprise.id,
                    secteur_id=secteur_id
                )
                db.session.add(entreprise_secteur)
            db.session.commit()

            # Appeler la méthode pour attribuer les réglementations liées aux secteurs
            entreprise.assign_reglementations()
            db.session.commit()

            flash('Entreprise ajoutée avec succès.', 'success')
        else:
            flash('L\'entreprise existe déjà.', 'warning')

        # Vérifier si un utilisateur avec cet email existe déjà
        existant_user = User.query.filter_by(email=user_form.email.data).first()

        if existant_user:
            flash("Un utilisateur avec cet email existe déjà. Veuillez en choisir un autre.", "danger")
            return render_template(
                'entreprise/ajouter_entreprise_et_manager.html',
                entreprise_form=entreprise_form,
                user_form=user_form
            )

        # Créer l'utilisateur avec le rôle approprié
        manager_user = User(
            name=user_form.name.data,
            email=user_form.email.data,
            role=user_form.role.data,
            entreprise_id=entreprise.id
        )
        manager_user.set_password(user_form.password.data)
        db.session.add(manager_user)
        db.session.commit()
        flash('l\'Utilisateur ajouté avec succès.', 'success')

        return redirect(url_for('entreprise.liste_entreprises'))

    return render_template(
        'entreprise/ajouter_entreprise_et_manager.html',
        entreprise_form=entreprise_form,
        user_form=user_form
    )


@bp.route('/entreprise/<int:entreprise_id>', methods=['GET'])
@login_required
def afficher_entreprise(entreprise_id):
    # Récupérer l'entreprise avec ses utilisateurs
    entreprise = Entreprise.query.filter_by(id=entreprise_id).first_or_404()
    utilisateurs = User.query.filter_by(entreprise_id=entreprise.id).all()

    return render_template(
        'entreprise/afficher_entreprise.html',
        entreprise=entreprise,
        utilisateurs=utilisateurs
    )


@bp.route('/entreprises', methods=['GET'])
@role_required(['ADMIN'])
def liste_entreprises():
    # Récupérer toutes les entreprises
    entreprises = Entreprise.query.all()
    return render_template('entreprise/liste_entreprises.html', entreprises=entreprises)


@bp.route('/entreprise', methods=['GET'])
@login_required
def afficher_entreprise_pour_utilisateur():
    # Vérifier si l'utilisateur est associé à une entreprise
    if current_user.entreprise_id:
        entreprise_id = current_user.entreprise_id
        return redirect(url_for('entreprise.afficher_entreprise', entreprise_id=entreprise_id))
    else:
        flash('Aucune entreprise associée à votre compte.', 'danger')
        return redirect(url_for('main.index'))  # Ou vers une autre page d'accueil
