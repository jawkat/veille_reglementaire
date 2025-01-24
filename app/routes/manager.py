from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify,request, abort
from app.models import  (User, Secteur, Domaine,
        SousDomaine, Reglementation,Theme, ReglementationSecteur,
        VersionReglementation, Article, Entreprise, EntrepriseSecteur)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,DateField,SelectMultipleField, EmailField
from wtforms.validators import DataRequired, Length, Email

from flask_login import login_required, current_user
from app.routes.admin import role_required


bp = Blueprint('manager', __name__)


class UserForm(FlaskForm):
    name = StringField('Nom de l\'utilisateur', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[
            ('RESPONSABLE','Responsable Veille'),
            ('COLLABORATEUR','Collaborateur')], validators=[DataRequired()])
    password = StringField('Mot de passe', validators=[DataRequired()])



@bp.route('/entreprise/<int:entreprise_id>/users')
@login_required
@role_required(['ADMIN', 'MANAGER'])
def liste_utilisateurs(entreprise_id):
    # Vérifier si l'entreprise existe et appartient au manager connecté
    entreprise = Entreprise.query.filter_by(id=entreprise_id).first()

    if entreprise is None or entreprise.id != current_user.entreprise_id:
        abort(404)  # Retourner une erreur 404 si l'entreprise n'existe pas ou si l'utilisateur n'y a pas accès

    # Récupérer les utilisateurs associés à l'entreprise
    utilisateurs = User.query.filter_by(entreprise_id=entreprise_id).all()

    return render_template('manager/liste_utilisateurs.html', entreprise=entreprise, utilisateurs=utilisateurs)


@bp.route('/entreprise/<int:entreprise_id>/ajouter_utilisateur', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN', 'MANAGER'])
def ajouter_utilisateur(entreprise_id):
    entreprise = Entreprise.query.get_or_404(entreprise_id)
    user_form = UserForm()

    if user_form.validate_on_submit():
        existant_user = User.query.filter_by(email=user_form.email.data).first()
        if existant_user:
            flash("Un utilisateur avec cet email existe déjà. Veuillez en choisir un autre.", "danger")
            return render_template(
                'manager/ajouter_utilisateur.html',
                entreprise=entreprise,
                user_form=user_form
            )
        # Vérification du nom existant
        existant_name = User.query.filter_by(name=user_form.name.data).first()
        if existant_name:
                flash("Un utilisateur avec ce nom existe déjà. Veuillez en choisir un autre.", "danger")
                return render_template(
                'manager/ajouter_utilisateur.html',
                entreprise=entreprise,
                user_form=user_form
                )

        nouvel_utilisateur = User(
            name=user_form.name.data,
            email=user_form.email.data,
            role=user_form.role.data,
            entreprise_id=entreprise.id
        )
        nouvel_utilisateur.set_password(user_form.password.data)
        db.session.add(nouvel_utilisateur)
        db.session.commit()
        flash(f"L'utilisateur {user_form.name.data} a été ajouté avec succès à l'entreprise {entreprise.nom}.", 'success')
        return redirect(url_for('manager.liste_utilisateurs', entreprise_id=entreprise.id))

    return render_template('manager/ajouter_utilisateur.html', entreprise=entreprise, user_form=user_form)


# Modifier un utilisateur
@bp.route('/entreprise/<int:entreprise_id>/modifier_utilisateur/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN', 'MANAGER'])
def modifier_utilisateur(entreprise_id, user_id):
    entreprise = Entreprise.query.get_or_404(entreprise_id)
    utilisateur = User.query.get_or_404(user_id)

    # Vérification de l'accès
    if utilisateur.entreprise_id != entreprise_id:
        abort(403)

    user_form = UserForm(obj=utilisateur)  # Préremplir le formulaire avec les données de l'utilisateur

    if user_form.validate_on_submit():
        existant_email = User.query.filter(User.email == user_form.email.data, User.id != utilisateur.id).first()
        if existant_email:
            flash("Cet email est déjà utilisé par un autre utilisateur.", "danger")
            return render_template('manager/modifier_utilisateur.html', entreprise=entreprise, user_form=user_form)

        utilisateur.name = user_form.name.data
        utilisateur.email = user_form.email.data
        utilisateur.role = user_form.role.data
        if user_form.password.data.strip():  # Met à jour le mot de passe uniquement s'il est fourni
            utilisateur.set_password(user_form.password.data)

        db.session.commit()
        flash("Les informations de l'utilisateur ont été modifiées avec succès.", 'success')
        return redirect(url_for('manager.liste_utilisateurs', entreprise_id=entreprise.id))

    return render_template('manager/modifier_utilisateur.html', entreprise=entreprise, user_form=user_form)

# Supprimer un utilisateur
@bp.route('/entreprise/<int:entreprise_id>/supprimer_utilisateur/<int:user_id>', methods=['POST'])
@login_required
@role_required(['ADMIN', 'MANAGER'])
def supprimer_utilisateur(entreprise_id, user_id):
    entreprise = Entreprise.query.get_or_404(entreprise_id)
    utilisateur = User.query.get_or_404(user_id)

    # Vérification de l'accès
    if utilisateur.entreprise_id != entreprise_id:
        abort(403)

    db.session.delete(utilisateur)
    db.session.commit()
    flash("L'utilisateur a été supprimé avec succès.", 'success')
    return redirect(url_for('manager.liste_utilisateurs', entreprise_id=entreprise.id))
