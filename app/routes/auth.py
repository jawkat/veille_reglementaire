from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from wtforms.fields.choices import RadioField
from werkzeug.security import generate_password_hash
from app import db, mail
from app.models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

bp = Blueprint('auth', __name__)


# Formulaire de connexion
class LoginForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

# Route de connexion
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Rechercher un utilisateur par son nom
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Vous vous êtes connecté avec succès.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Nom ou mot de passe incorrect.', 'danger')

    return render_template('auth/login2.html', form=form)


# Route de déconnexion
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation du mot de passe')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("Il n'y a aucun compte associé à cet e-mail.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Réinitialiser le mot de passe')

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Demande de réinitialisation du mot de passe',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''Pour réinitialiser votre mot de passe, visitez le lien suivant :
{url_for('auth.reset_token', token=token, _external=True)}

Si vous n'avez pas demandé cette réinitialisation, ignorez cet e-mail et aucune modification ne sera effectuée.
'''
    mail.send(msg)


@bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Un e-mail a été envoyé avec des instructions pour réinitialiser votre mot de passe. Veuillez fermer cette fenêtre et vérifier votre e-mail.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html', form=form)


@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Ceci est un jeton invalide ou expiré', 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Votre mot de passe a été mis à jour ! Vous pouvez désormais vous connecter', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', form=form)
