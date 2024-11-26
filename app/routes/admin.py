from flask import Blueprint, render_template, redirect, url_for, flash

from app.models import User
from flask_login import login_required, current_user
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email
from wtforms.fields.choices import RadioField
from functools import wraps
from flask import abort, flash

bp = Blueprint('admin', __name__)

# Décorateur pour vérifier les rôles
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Vous devez être connecté pour accéder à cette page.", 'danger')
                return redirect(url_for('main.index'))  # Redirige vers un endroit sûr

            if current_user.role not in allowed_roles:
                flash("Vous n'avez pas la permission d'accéder à cette page.", 'danger')
                return redirect(url_for('main.index'))  # Redirige vers un endroit sûr

            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/admin/manage-users')
@role_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# ***********************************************************************************************

class AddUserForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = RadioField('Rôle',
                      choices=[('gerant', 'Gérant Nomai'), ('manager', 'Manager Nomai'), ('qualite', 'Technicienne Qualité'), ('admin', 'Admin')], validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Ajouter l’utilisateur')


# Route pour ajouter un nouvel utilisateur
@bp.route('/admin/add_user', methods=['GET', 'POST'])
@role_required('admin')
def add_user():
    form = AddUserForm()

    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        existing_email_user = User.query.filter_by(email=form.email.data).first()
        if existing_email_user:
            flash("L'email est déjà utilisé par un autre utilisateur.", 'danger')
            return redirect(url_for('admin.add_user'))

        # Vérifier si le nom existe déjà
        existing_name_user = User.query.filter_by(name=form.name.data).first()
        if existing_name_user:
            flash("Le nom est déjà utilisé par un autre utilisateur.", 'danger')
            return redirect(url_for('admin.add_user'))

        # Créer un nouvel objet User
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data,
        )
        user.set_password(form.password.data)  # Hacher le mot de passe

        db.session.add(user)
        db.session.commit()


        flash(f'L’utilisateur {user.name} a été ajouté avec succès!', 'success')
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/add_user.html', form=form)


class EditUserForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Mettre à jour')



# Route pour éditer un utilisateur
@bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm()

    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != user.id:
            flash("L'email est déjà utilisé par un autre utilisateur.", 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        # Vérifier si le nom existe déjà
        existing_user_by_name = User.query.filter_by(name=form.name.data).first()
        if existing_user_by_name and existing_user_by_name.id != user.id:
            flash("Le nom est déjà utilisé par un autre utilisateur.", 'danger')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        # Mettre à jour les informations de l'utilisateur
        user.name = form.name.data
        user.email = form.email.data
        db.session.commit()

        flash(f'L’utilisateur {user.name} a été mis à jour avec succès!', 'success')
        return redirect(url_for('admin.manage_users'))

    form.name.data = user.name
    form.email.data = user.email

    return render_template('admin/edit_user.html', user=user, form=form)




@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Procéder à la suppression de l'utilisateur
    db.session.delete(user)
    db.session.commit()

    flash(f'L’utilisateur {user.name} a été supprimé.', 'danger')
    return redirect(url_for('admin.manage_users'))
