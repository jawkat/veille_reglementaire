from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.choices import RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_wtf import FlaskForm
from functools import wraps
from app import db, mail
from app.models import User

# Définition des blueprints
bp = Blueprint('admin', __name__)

# ------------------------------------
# Décorateur pour vérifier les rôles
# ------------------------------------
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Vous devez être connecté pour accéder à cette page.", 'danger')
                return redirect(url_for('main.index'))

            if current_user.role not in allowed_roles:
                flash("Vous n'avez pas la permission d'accéder à cette page.", 'danger')
                return redirect(url_for('main.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ------------------------------------
# Formulaires FlaskWTF
# ------------------------------------
class AddUserForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = RadioField(
        'Rôle',
        choices=[
            ('gerant', 'Gérant Nomai'), 
            ('manager', 'Manager Nomai'), 
            ('qualite', 'Technicienne Qualité'), 
            ('admin', 'Admin')
        ], 
        validators=[DataRequired()]
    )
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Ajouter l’utilisateur')

class EditUserForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Mettre à jour')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation du mot de passe')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("Il n'y a aucun compte associé à cet e-mail.")

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirmer le mot de passe', 
        validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Réinitialiser le mot de passe')

# ------------------------------------
# Routes pour la gestion des utilisateurs (Admin)
# ------------------------------------
@bp.route('/admin/manage-users')
@role_required(['admin'])
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/admin/add_user', methods=['GET', 'POST'])
@role_required(['admin'])
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("L'email est déjà utilisé.", 'danger')
            return redirect(url_for('admin.add_user'))

        if User.query.filter_by(name=form.name.data).first():
            flash("Le nom est déjà utilisé.", 'danger')
            return redirect(url_for('admin.add_user'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"L’utilisateur {user.name} a été ajouté avec succès!", 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/add_user.html', form=form)

@bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@role_required(['admin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first() and user.email != form.email.data:
            flash("L'email est déjà utilisé.", 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        user.name = form.name.data
        user.email = form.email.data
        db.session.commit()
        flash(f"L’utilisateur {user.name} a été mis à jour avec succès!", 'success')
        return redirect(url_for('admin.manage_users'))
    return render_template('admin/edit_user.html', form=form)

@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@role_required(['admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"L’utilisateur {user.name} a été supprimé.", 'danger')
    return redirect(url_for('admin.manage_users'))

# ------------------------------------
# Routes pour l'authentification (Auth)
# ------------------------------------
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Connexion réussie.', 'success')
            return redirect(url_for('main.index'))
        flash('Nom ou mot de passe incorrect.', 'danger')
    return render_template('admin/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnexion réussie.', 'info')
    return redirect(url_for('admin.login'))

@bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Un e-mail de réinitialisation a été envoyé.', 'info')
        return redirect(url_for('admin.login'))
    return render_template('admin/reset_request.html', form=form)

@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Jeton invalide ou expiré.', 'warning')
        return redirect(url_for('admin.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Mot de passe réinitialisé avec succès.', 'success')
        return redirect(url_for('admin.login'))
    return render_template('admin/reset_token.html', form=form)

# ------------------------------------
# Fonction d'envoi d'email
# ------------------------------------
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        'Réinitialisation du mot de passe',
        sender='noreply@demo.com',
        recipients=[user.email]
    )
    msg.body = f'''Pour réinitialiser votre mot de passe, cliquez ici :
{url_for('admin.reset_token', token=token, _external=True)}
Si vous n'avez pas demandé cette réinitialisation, ignorez cet e-mail.'''
    mail.send(msg)
