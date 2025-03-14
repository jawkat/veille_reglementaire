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

bp = Blueprint('reglement', __name__)

# Refactor repeated logic into helper functions
def check_existing_entry(model, field, value, message):
    existing_entry = model.query.filter(field == value).first()
    if existing_entry:
        flash(message, "danger")
        return True
    return False

def log_error(message):
    logging.error(message)

class SecteurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Créer Secteur')


@bp.route('/ajouter_secteur', methods=['GET', 'POST'])
def ajouter_secteur():
    form = SecteurForm()
    if form.validate_on_submit():
        if check_existing_entry(Secteur, Secteur.nom, form.nom.data, "Un secteur avec ce nom existe déjà."):
            return jsonify(success=False, message="Un secteur avec ce nom existe déjà.")

        nouveau_secteur = Secteur(nom=form.nom.data, description=form.description.data)
        db.session.add(nouveau_secteur)
        db.session.commit()
        return jsonify(success=True, message="Secteur ajouté avec succès.")

    return render_template('secteur/ajouter_secteur.html', form=form)

@bp.route('/secteurs', methods=['GET'])
@role_required('ADMIN')
def liste_secteurs():
    try:
        secteurs = Secteur.query.all()
        return render_template('secteur/liste_secteurs.html', secteurs=secteurs)
    except Exception as e:
        log_error(f"Erreur lors de la récupération des secteurs : {str(e)}")
        flash(f"Erreur lors de la récupération des secteurs : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur


# **********************************************************************************************

class DomaineForm(FlaskForm):
    nom = StringField('Nom du Domaine', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Ajouter Domaine')


@bp.route('/ajouter-domaine', methods=['GET', 'POST'])
def ajouter_domaine():
    form = DomaineForm()
    if form.validate_on_submit():
        if check_existing_entry(Domaine, Domaine.nom, form.nom.data, "Un domaine avec ce nom existe déjà."):
            return jsonify(success=False, message="Un domaine avec ce nom existe déjà.")

        nouveau_domaine = Domaine(nom=form.nom.data, description=form.description.data)
        db.session.add(nouveau_domaine)
        db.session.commit()
        return jsonify(success=True, message="Domaine ajouté avec succès.")

    return render_template('domaine/ajouter_domaine.html', form=form)


@bp.route('/domaines', methods=['GET'])
@role_required('ADMIN')
def liste_domaines():
    try:
        domaines = Domaine.query.all()
        return render_template('domaine/liste_domaines.html', domaines=domaines)
    except Exception as e:
        log_error(f"Erreur lors de la récupération des domaines : {str(e)}")
        flash(f"Erreur lors de la récupération des domaines : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur


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
        if check_existing_entry(SousDomaine, SousDomaine.nom, form.nom.data, "Un sous-domaine avec ce nom existe déjà."):
            return jsonify(success=False, message="Un sous-domaine avec ce nom existe déjà.")

        sous_domaine = SousDomaine(
            nom=form.nom.data,
            description=form.description.data,
            domaine_id=form.domaine_id.data
        )
        db.session.add(sous_domaine)
        db.session.commit()
        return jsonify(success=True, message="Sous-domaine ajouté avec succès.")

    return render_template('domaine/ajouter_sous_domaine.html', form=form)

@bp.route('/sous-domaines', methods=['GET'])
@role_required('ADMIN')
def liste_sous_domaines():
    try:
        sous_domaines = SousDomaine.query.all()
        return render_template('domaine/liste_sous_domaines.html', sous_domaines=sous_domaines)
    except Exception as e:
        log_error(f"Erreur lors de la récupération des sous-domaines : {str(e)}")
        flash(f"Erreur lors de la récupération des sous-domaines : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur


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
        if check_existing_entry(Reglementation, Reglementation.titre, form.titre.data, "Une réglementation avec ce titre existe déjà."):
            return jsonify(success=False, message="Une réglementation avec ce titre existe déjà.")

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
        log_error(f"Erreur lors du chargement des sous-domaines : {str(e)}")
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
        log_error(f" jk Erreur lors de la récupération des réglementations : {str(e)}")
        flash(f"jk Erreur lors de la récupération des réglementations : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur



@bp.route('/reglementation/<int:id>', methods=['GET'])
@role_required('ADMIN','MANAGER')
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
        log_error(f"Erreur lors de l'ajout du thème : {str(e)}")
        return jsonify({'status': 'error', 'message': f"Erreur lors de l'ajout du thème : {str(e)}"}), 500


##****************** ajout article **********************


class ArticleForm(FlaskForm):
    numero = StringField('Numéro', validators=[DataRequired()])
    titre = StringField('Titre')
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


@bp.route('/modifier-reglementation/<int:reglementation_id>', methods=['GET', 'POST'])
@role_required('ADMIN','MANAGER')
def modifier_reglementation(reglementation_id):
    reglementation = Reglementation.query.get_or_404(reglementation_id)
    form = ReglementationForm(obj=reglementation)
    
    # Récupérer tous les domaines, thèmes et secteurs
    domaines = Domaine.query.all()
    themes = Theme.query.all()
    secteurs = Secteur.query.all()

    form.theme_id.choices = [(theme.id, theme.nom) for theme in themes]
    form.sous_domaine_id.choices = [(sous_domaine.id, sous_domaine.nom) for sous_domaine in SousDomaine.query.all()]

    # Récupérer les secteurs associés à la réglementation existante
    secteurs_selectionnes = [secteur.id for secteur in reglementation.secteurs]

    if form.validate_on_submit():
        reglementation.titre = form.titre.data
        reglementation.type_texte = form.type_texte.data
        reglementation.date_publication = form.date_publication.data
        reglementation.source = form.source.data
        reglementation.langue = form.langue.data
        reglementation.theme_id = form.theme_id.data
        reglementation.sous_domaine_id = form.sous_domaine_id.data
        


        db.session.commit()
        flash("Réglementation modifiée avec succès.", "success")
        return redirect(url_for('reglement.liste_reglementations'))

    return render_template('reglementations/modifier_reglementation.html', form=form, domaines=domaines,
                           secteurs=secteurs, reglementation=reglementation, secteurs_selectionnes=secteurs_selectionnes)


@bp.route('/supprimer-reglementation/<int:reglementation_id>', methods=['POST'])
@role_required('ADMIN')
def supprimer_reglementation(reglementation_id):
    reglementation = Reglementation.query.get_or_404(reglementation_id)

    # Supprimer les relations dans la table entreprise_reglementation
    for entreprise_reglementation in reglementation.entreprises_associees:
        db.session.delete(entreprise_reglementation)
    


    db.session.delete(reglementation)
    db.session.commit()
    flash("Réglementation supprimée avec succès.", "success")
    return redirect(url_for('reglement.liste_reglementations'))
