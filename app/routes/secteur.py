from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify, request, abort
from app.models import (User, Secteur, Domaine,
                        SousDomaine, Reglementation, Theme, ReglementationSecteur,
                        VersionReglementation, Article, Entreprise, EntrepriseSecteur, EntrepriseReglementation)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, SelectMultipleField, EmailField
from wtforms.validators import DataRequired, Length, Email
from flask_login import login_required, current_user
from app.routes.admin import role_required # Assuming this is correctly defined and imported
import logging

logger = logging.getLogger(__name__) # Logger for server-side error details
bp = Blueprint('secteur', __name__)


class SecteurForm(FlaskForm):
    """Formulaire de création/modification d'un secteur."""
    nom = StringField('Nom', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Enregistrer')


@bp.route('/ajouter_secteur', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def ajouter_secteur():
    """
    Route pour ajouter un nouveau secteur.
    Retourne une réponse JSON pour les requêtes AJAX.
    """
    form = SecteurForm()
    if form.validate_on_submit():
        try:
            # Check for existing sector name (case-insensitive for better UX)
            existing_secteur = Secteur.query.filter(db.func.lower(Secteur.nom) == db.func.lower(form.nom.data)).first()
            if existing_secteur:
                # Log the attempted duplicate creation
                logger.warning(f"Attempted to create duplicate sector: {form.nom.data}")
                flash("Un secteur avec ce nom existe déjà. Veuillez en choisir un autre.", "danger")
                return redirect(url_for('secteur.ajouter_secteur'))

            nouveau_secteur = Secteur(nom=form.nom.data, description=form.description.data)
            db.session.add(nouveau_secteur)
            db.session.commit()
            flash("Secteur ajouté avec succès.", "success") # For general feedback on page reload
            logger.info(f"Secteur '{nouveau_secteur.nom}' (ID: {nouveau_secteur.id}) ajouté par {current_user.email}")
            return redirect(url_for('secteur.liste_secteurs')) 
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Erreur lors de l'ajout du secteur '{form.nom.data}'") # Log full traceback
            # Provide a generic but informative message to the user
            flash(f"Une erreur inattendue est survenue lors de l'ajout du secteur. Veuillez réessayer.", "danger")
            return redirect(url_for('secteur.ajouter_secteur'))
    # If it's a GET request or form validation failed
    return render_template('secteur/ajouter_secteur.html', form=form, title="Ajouter un Secteur")

@bp.route('/secteurs', methods=['GET'])
@login_required
@role_required('ADMIN')
def liste_secteurs():
    """Route pour afficher la liste de tous les secteurs."""
    try:
        secteurs = Secteur.query.order_by(Secteur.nom).all()
        # Optionally, add pagination here if you expect many sectors (e.g., sectors = Secteur.query.paginate(page=1, per_page=20))
        return render_template('secteur/liste_secteurs.html', secteurs=secteurs, title="Liste des Secteurs")
    except Exception as e:
        logger.exception("Erreur lors de la récupération de la liste des secteurs.")
        flash("Une erreur est survenue lors de la récupération des secteurs. Veuillez réessayer plus tard.", "danger")
        return redirect(url_for('main.dashboard')) # Redirect to a safe page if list fails

@bp.route('/modifier_secteur/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def modifier_secteur(id):
    """
    Route pour modifier un secteur existant.
    Retourne une réponse JSON pour les requêtes AJAX.
    """
    secteur = Secteur.query.get_or_404(id) # Returns 404 if not found
    form = SecteurForm(obj=secteur) # Pre-populate form with existing data
    
    if form.validate_on_submit():
        try:
            # Check for existing sector name (case-insensitive) if name is changed
            if secteur.nom.lower() != form.nom.data.lower():
                existing_secteur = Secteur.query.filter(db.func.lower(Secteur.nom) == db.func.lower(form.nom.data)).first()
                if existing_secteur:
                    logger.warning(f"Attempted to rename sector {secteur.id} to duplicate name: {form.nom.data}")
                    return jsonify(success=False, message="Un secteur avec ce nom existe déjà. Veuillez en choisir un autre.")
            
            secteur.nom = form.nom.data
            secteur.description = form.description.data
            db.session.commit()
            flash("Secteur modifié avec succès.", "success")
            logger.info(f"Secteur '{secteur.nom}' (ID: {secteur.id}) modifié par {current_user.email}")
            return jsonify(success=True, message="Secteur modifié avec succès.")
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Erreur lors de la modification du secteur '{secteur.nom}' (ID: {secteur.id})")
            flash("Une erreur inattendue est survenue lors de la modification du secteur. Veuillez réessayer.", "danger")
            return jsonify(success=False, message="Une erreur est survenue lors de la modification du secteur.")
    
    # If it's a GET request or form validation failed
    return render_template('secteur/modifier_secteur.html', form=form, secteur=secteur, title=f"Modifier {secteur.nom}")

@bp.route('/supprimer_secteur/<int:id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def supprimer_secteur(id):
    """
    Route pour supprimer un secteur.
    Retourne une réponse JSON.
    """
    try:
        secteur = Secteur.query.get_or_404(id)
        
        # Comprehensive check for existing relationships (more direct using ORM relationships if defined)
        # Assuming Entreprise and Reglementation have back_populates for Secteur (e.g., entreprise.secteurs, reglementation.secteurs)
        if secteur.entreprises or secteur.reglementations_via_link: # Using ORM relationships for direct check
            message = "Ce secteur ne peut pas être supprimé car il est lié à des entreprises ou à des réglementations."
            logger.warning(f"Attempted to delete sector '{secteur.nom}' (ID: {id}) but it has existing links.")
            return jsonify(success=False, message=message)
        
        db.session.delete(secteur)
        db.session.commit()
        flash("Secteur supprimé avec succès.", "success")
        logger.info(f"Secteur '{secteur.nom}' (ID: {id}) supprimé par {current_user.email}")
        return jsonify(success=True, message="Secteur supprimé avec succès.")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Erreur lors de la suppression du secteur ID: {id}")
        flash("Une erreur inattendue est survenue lors de la suppression du secteur. Veuillez réessayer.", "danger")
        return jsonify(success=False, message="Une erreur est survenue lors de la suppression du secteur.")

@bp.route('/secteur/<int:id>', methods=['GET'])
@login_required
def afficher_secteur(id):
    """Route pour afficher les détails d'un secteur."""
    try:
        secteur = Secteur.query.get_or_404(id)
        
        # Leveraging direct ORM relationships for associated data
        # 'secteur.entreprises' will directly give a list of Entreprise objects
        # 'secteur.reglementations_via_link' will give a list of ReglementationSecteur objects
        # To get Reglementation objects, you'd then access reg_link.reglementation
        associated_entreprises = secteur.entreprises # Direct access to Entreprise objects
        associated_reglementations = [link.reglementation for link in secteur.reglementations_via_link]

        return render_template('secteur/detail_secteur.html', 
                               secteur=secteur, 
                               entreprises=associated_entreprises, # Pass direct objects
                               reglementations=associated_reglementations, # Pass direct objects
                               title=f"Détails du Secteur: {secteur.nom}")
    except Exception as e:
        logger.exception(f"Erreur lors de l'affichage du secteur ID: {id}")
        flash("Une erreur est survenue lors de l'affichage du secteur. Veuillez réessayer plus tard.", "danger")
        return redirect(url_for('secteur.liste_secteurs'))