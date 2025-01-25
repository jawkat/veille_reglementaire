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

bp = Blueprint('reglement', __name__)



class SecteurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Créer Secteur')


@bp.route('/ajouter_secteur', methods=['GET', 'POST'])
def ajouter_secteur():
    form = SecteurForm()
    if form.validate_on_submit():
        # Vérifier si le secteur existe déjà
        secteur_existant = Secteur.query.filter_by(nom=form.nom.data).first()
        if secteur_existant:
            flash("Un secteur avec ce nom existe déjà.", "danger")
            return redirect(url_for('reglement.ajouter_secteur'))

        # Créer un nouveau secteur
        nouveau_secteur = Secteur(
            nom=form.nom.data,
            description=form.description.data
        )
        db.session.add(nouveau_secteur)
        db.session.commit()
        flash("Secteur créé avec succès !", "success")
        return redirect(url_for('reglement.liste_secteurs'))

    return render_template('secteur/ajouter_secteur.html', form=form)

@bp.route('/secteurs', methods=['GET'])
def liste_secteurs():
    secteurs = Secteur.query.all()
    return render_template('secteur/liste_secteurs.html', secteurs=secteurs)

#**********************************************************************************************

class DomaineForm(FlaskForm):
    nom = StringField('Nom du Domaine', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Ajouter Domaine')


@bp.route('/ajouter-domaine', methods=['GET', 'POST'])
def ajouter_domaine():
    form = DomaineForm()
    if form.validate_on_submit():

        # Vérifier si le domaine existe déjà
        domaine_existant = Domaine.query.filter_by(nom=form.nom.data).first()
        if domaine_existant:
            flash("Un domaine avec ce nom existe déjà.", "danger")
            return redirect(url_for('reglement.ajouter_domaine'))

        # Créer un nouveau secteur
        nouveau_domaine = Domaine(nom=form.nom.data, description=form.description.data)
        db.session.add(nouveau_domaine)
        db.session.commit()
        flash('Domaine ajouté avec succès.', 'success')
        return redirect(url_for('reglement.liste_domaines'))
    return render_template('domaine/ajouter_domaine.html', form=form)


@bp.route('/domaines', methods=['GET'])
def liste_domaines():
    domaines = Domaine.query.all()
    return render_template('domaine/liste_domaines.html', domaines=domaines)


# *************************************************************************


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
        sous_domaine = SousDomaine(
            nom=form.nom.data,
            description=form.description.data,
            domaine_id=form.domaine_id.data
        )
        db.session.add(sous_domaine)
        db.session.commit()
        flash('Sous-domaine ajouté avec succès.', 'success')
        return redirect(url_for('reglement.liste_sous_domaines'))
    return render_template('domaine/ajouter_sous_domaine.html', form=form)

@bp.route('/sous-domaines', methods=['GET'])
def liste_sous_domaines():
    sous_domaines = SousDomaine.query.all()
    return render_template('domaine/liste_sous_domaines.html', sous_domaines=sous_domaines)


class ReglementationForm(FlaskForm):
    titre = StringField('Titre', validators=[DataRequired()])
    type_texte = StringField('Type de Texte', validators=[DataRequired()])
    date_publication = DateField('Date de Publication', format='%Y-%m-%d', validators=[DataRequired()])
    source = StringField('Source', validators=[DataRequired()])

    langue = StringField('Langue', validators=[DataRequired()])
    sous_domaine_id = SelectField('Sous-Domaine', choices=[], coerce=int, validators=[DataRequired()])
    theme_id = SelectField('Thème', coerce=int, validators=[DataRequired()])

     # Champ pour sélectionner plusieurs secteurs
    secteurs = SelectMultipleField('Secteurs', coerce=int, choices=[])  # champ de sélection multiple
    submit = SubmitField('Ajouter Réglementation')

    def __init__(self, *args, **kwargs):
        super(ReglementationForm, self).__init__(*args, **kwargs)
        # Charger les secteurs dans le formulaire
        self.secteurs.choices = [(secteur.id, secteur.nom) for secteur in Secteur.query.all()]

class VersionReglementationForm(FlaskForm):
    version_numero = StringField('Numéro de Version', validators=[DataRequired()])
    contenu = TextAreaField('Contenu', validators=[DataRequired()])
    reglementation_id = SelectField('Réglementation', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Ajouter Version')


@bp.route('/ajouter-reglementation', methods=['GET', 'POST'])
def ajouter_reglementation():
    form = ReglementationForm()
    domaines = Domaine.query.all()
    themes = Theme.query.all()
    secteurs = Secteur.query.all()  # Récupérer tous les secteurs

    if not domaines:
        flash("Aucun domaine disponible. Veuillez ajouter des domaines avant de continuer.", "warning")
        return redirect(url_for('reglement.ajouter_domaine'))

    if not themes:
        flash("Aucun thème disponible. Veuillez ajouter des thèmes avant de continuer.", "warning")
        return redirect(url_for('reglement.ajouter_theme'))



    # Initialisation des choix pour le formulaire
    form.theme_id.choices = [(theme.id, theme.nom) for theme in themes]
    form.sous_domaine_id.choices = [(sous_domaine.id, sous_domaine.nom) for sous_domaine in SousDomaine.query.all()]


    if form.validate_on_submit():

        # Vérifier si le titre existe déjà
        titre_existant = Reglementation.query.filter_by(titre=form.titre.data).first()
        if titre_existant:
            flash("Une réglementation avec ce titre existe déjà. Veuillez en choisir un autre.", "danger")
            return render_template('reglementations/ajouter_reglementation.html', form=form, domaines=domaines,
                                    secteurs=secteurs, selected_secteurs=form.secteurs.data)

        submitted_sous_domaine = form.sous_domaine_id.data
        valid_choices = [choice[0] for choice in form.sous_domaine_id.choices]


        if submitted_sous_domaine not in valid_choices:
            flash("Sous-domaine sélectionné invalide.", "danger")
        else:
            reglementation = Reglementation(
                titre=form.titre.data,
                type_texte=form.type_texte.data,
                date_publication=form.date_publication.data,
                source=form.source.data,
                langue=form.langue.data,
                theme_id=form.theme_id.data,
                sous_domaine_id=form.sous_domaine_id.data
            )
            db.session.add(reglementation)
            db.session.commit()


            # Création de la première version de la réglementation (Version 1)
            version = VersionReglementation(
                version_numero='1',
                contenu="Version initiale de la réglementation.",
                reglementation_id=reglementation.id
            )
            db.session.add(version)
            db.session.commit()  # Commit de la version


            secteurs_selectionnes = request.form.getlist('secteurs')

            for secteur_id in secteurs_selectionnes:
                reglementation_secteur = ReglementationSecteur(
                    reglementation_id=reglementation.id,
                    secteur_id=secteur_id
                )
                db.session.add(reglementation_secteur)

            db.session.commit()

            flash("Réglementation ajoutée avec succès.", "success")
            return redirect(url_for('reglement.liste_reglementations'))


    return render_template('reglementations/ajouter_reglementation.html', form=form, domaines=domaines,
                secteurs=secteurs, selected_secteurs=form.secteurs.data)





@bp.route('/get_sous_domaines/<int:domaine_id>', methods=['GET'])
def get_sous_domaines(domaine_id):
    try:
        sous_domaines = SousDomaine.query.filter_by(domaine_id=domaine_id).all()
        sous_domaines_data = [{'id': s.id, 'nom': s.nom} for s in sous_domaines]
        return jsonify(sous_domaines_data)
    except Exception as e:
        return jsonify({'error': f"Erreur lors du chargement des sous-domaines : {str(e)}"}), 500




@bp.route('/liste-reglementations', methods=['GET'])
def liste_reglementations():
    try:
        # Récupérer toutes les réglementations
        reglementations = Reglementation.query.all()

        # Vérifier si des réglementations existent
        if not reglementations:
            flash("Aucune réglementation n'est disponible.", "warning")
            return render_template('reglementations/liste_reglementations.html', reglementations=[])
        
        # Ajouter le statut de suivi pour chaque réglementation
        suivi_map = {
            reg.reglementation_id: reg.suivi
            for reg in EntrepriseReglementation.query.filter_by(entreprise_id=current_user.entreprise_id).all()
        }

        return render_template('reglementations/liste_reglementations.html', reglementations=reglementations, suivi_map=suivi_map)
    except Exception as e:
        flash(f"Erreur lors de la récupération des réglementations : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur



@bp.route('/reglementation/<int:id>', methods=['GET'])
def detail_reglementation(id):
    reglementation = Reglementation.query.get_or_404(id)

    # Ajouter le statut de suivi pour chaque réglementation
    suivi_map = {
        reg.reglementation_id: reg.suivi
        for reg in EntrepriseReglementation.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    }

    theme = Theme.query.get(reglementation.theme_id)
    sous_domaine = SousDomaine.query.get(reglementation.sous_domaine_id)

    # Récupérer les secteurs associés à la réglementation
    secteurs = [secteur for secteur in
                (ReglementationSecteur.query.filter_by(reglementation_id=id)
                .join(Secteur, Secteur.id == ReglementationSecteur.secteur_id)
                .all())]

    return render_template('reglementations/detail_reglementation.html',
            reglementation=reglementation,
            theme=theme,
            sous_domaine=sous_domaine,
            secteurs=secteurs,
            suivi_map=suivi_map)



@bp.route('/ajouter-theme', methods=['POST'])
@role_required(['ADMIN'])
def ajouter_theme():
    try:
        data = request.get_json()
        nom = data.get('nom')
        description = data.get('description', '')

        if not nom:
            return jsonify({'status': 'error', 'message': 'Le nom est requis.'}), 400

        # Création du nouveau thème
        theme = Theme(nom=nom, description=description)
        db.session.add(theme)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Thème ajouté avec succès',
            'theme': {'id': theme.id, 'nom': theme.nom},
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f"Erreur lors de l'ajout du thème : {str(e)}"}), 500


##****************** ajout article **********************


class ArticleForm(FlaskForm):
    numero = StringField('Numéro', validators=[DataRequired()])
    titre = StringField('Titre', validators=[DataRequired()])
    contenu = TextAreaField('Contenu', validators=[DataRequired()])

    submit = SubmitField('Ajouter Article')



@bp.route('/ajouter-article/<int:reglementation_id>', methods=['GET', 'POST'])
@role_required(['ADMIN'])
def ajouter_article(reglementation_id):
    # Récupérer la réglementation pour afficher ses informations dans le formulaire
    reglementation = Reglementation.query.get_or_404(reglementation_id)

    form = ArticleForm()


    if form.validate_on_submit():
        # Créer un nouvel article lié à la réglementation
        article = Article(
            numero=form.numero.data,
            titre = form.titre.data,
            contenu=form.contenu.data,
            reglementation_id=reglementation.id
        )

        # Ajouter l'article à la session et commettre
        db.session.add(article)
        db.session.commit()

        flash('Article ajouté avec succès.', 'success')
        return redirect(url_for('reglement.detail_reglementation', id=reglementation.id))

    return render_template('articles/ajouter_article.html', form=form, reglementation=reglementation)


# ********************  ajout entreprise et le Manager du compte ****************************************


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

        return redirect(url_for('reglement.liste_entreprises'))

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
        return redirect(url_for('reglement.afficher_entreprise', entreprise_id=entreprise_id))
    else:
        flash('Aucune entreprise associée à votre compte.', 'danger')
        return redirect(url_for('main.index'))  # Ou vers une autre page d'accueil
