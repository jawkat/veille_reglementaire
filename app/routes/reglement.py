from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify,request
from app.models import  User, Secteur, Domaine, SousDomaine, Reglementation,Theme, ReglementationSecteur
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,DateField,SelectMultipleField
from wtforms.validators import DataRequired, Length

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
    description = TextAreaField('Description', validators=[DataRequired()])
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
    description = TextAreaField('Description', validators=[DataRequired()])
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
                theme_id=form.theme_id.data,
                sous_domaine_id=form.sous_domaine_id.data
            )
            db.session.add(reglementation)
            db.session.commit()

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

        return render_template('reglementations/liste_reglementations.html', reglementations=reglementations)
    except Exception as e:
        flash(f"Erreur lors de la récupération des réglementations : {str(e)}", "danger")
        return redirect(url_for('main.index'))  # Rediriger en cas d'erreur



@bp.route('/reglementation/<int:id>', methods=['GET'])
def detail_reglementation(id):
    reglementation = Reglementation.query.get_or_404(id)

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
            secteurs=secteurs)



@bp.route('/ajouter-theme', methods=['POST'])
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



# *********************** ajout Secteur à la reglemanatation  *********************


