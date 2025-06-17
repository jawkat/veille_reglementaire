from datetime import datetime, timedelta, date
from functools import wraps
from flask import Blueprint, render_template, flash, redirect, url_for, jsonify, request
from app.models import (User, Secteur, Domaine,
        SousDomaine, Reglementation, Theme, ReglementationSecteur,
        VersionReglementation, Article, Entreprise, EntrepriseSecteur, 
        EntrepriseReglementation, Evaluation, ApplicableEnum, ConformeEnum)
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateField, SelectMultipleField, EmailField
from wtforms.validators import DataRequired, Length, Email, Optional

from flask_login import login_required, current_user
from app.routes.admin import role_required
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('reglementation', __name__)

def check_existing_entry(model, field, value, message):
    """Vérifie si une entrée existe déjà dans la base de données."""
    existing = model.query.filter(field == value).first()
    if existing:
        flash(message, "warning")
        return True
    return False

def log_error(message):
    """Enregistre une erreur dans les logs."""
    logger.error(message)


class ReglementationForm(FlaskForm):
    """Formulaire pour la création et modification d'une réglementation."""
    titre = StringField('Titre', validators=[DataRequired(), Length(min=3, max=200)])
    type_texte = StringField('Type de Texte', validators=[DataRequired(), Length(max=100)])
    date_publication = DateField('Date de Publication', format='%Y-%m-%d', validators=[DataRequired()])
    date_derniere_mise_a_jour = DateField('Date de Dernière Mise à Jour', format='%Y-%m-%d', validators=[Optional()])
    source = StringField('Source', validators=[DataRequired(), Length(max=200)])
    langue = StringField('Langue', validators=[DataRequired(), Length(max=50)])
    resume_exigences = TextAreaField('Résumé des Exigences', validators=[Optional(), Length(max=2000)])
    
    sous_domaine_id = SelectField('Sous-Domaine', coerce=int, validators=[DataRequired()])
    theme_id = SelectField('Thème', coerce=int, validators=[DataRequired()])
    secteurs = SelectMultipleField('Secteurs', coerce=int)
    
    submit = SubmitField('Enregistrer')

    def __init__(self, *args, **kwargs):
        super(ReglementationForm, self).__init__(*args, **kwargs)
        self.sous_domaine_id.choices = [(sd.id, f"{sd.domaine.nom} - {sd.nom}") 
                                      for sd in SousDomaine.query.join(Domaine).order_by(Domaine.nom, SousDomaine.nom)]
        self.theme_id.choices = [(t.id, t.nom) for t in Theme.query.order_by(Theme.nom)]
        self.secteurs.choices = [(s.id, s.nom) for s in Secteur.query.order_by(Secteur.nom)]

class VersionReglementationForm(FlaskForm):
    """Formulaire pour l'ajout d'une nouvelle version d'une réglementation."""
    version_numero = StringField('Numéro de Version', validators=[DataRequired()])
    contenu = TextAreaField('Contenu', validators=[DataRequired()])
    modifications_detail = TextAreaField('Détails des Modifications', validators=[Optional()])
    submit = SubmitField('Ajouter Version')


@bp.route('/ajouter-reglementation', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def ajouter_reglementation():
    """Route pour ajouter une nouvelle réglementation."""
    form = ReglementationForm()
    
    if form.validate_on_submit():
        try:
            if check_existing_entry(Reglementation, Reglementation.titre, form.titre.data, 
                                  "Une réglementation avec ce titre existe déjà."):
                return redirect(url_for('reglementation.ajouter_reglementation'))

            # Création de la réglementation
            reglementation = Reglementation(
                titre=form.titre.data,
                type_texte=form.type_texte.data,
                date_publication=form.date_publication.data,
                date_derniere_mise_a_jour=form.date_derniere_mise_a_jour.data,
                source=form.source.data,
                langue=form.langue.data,
                resume_exigences=form.resume_exigences.data,
                theme_id=form.theme_id.data,
                sous_domaine_id=form.sous_domaine_id.data
            )
            db.session.add(reglementation)
            db.session.flush()  # Pour obtenir l'ID de la réglementation

            # Association avec les secteurs
            for secteur_id in form.secteurs.data:
                reglementation_secteur = ReglementationSecteur(
                    reglementation_id=reglementation.id,
                    secteur_id=secteur_id
                )
                db.session.add(reglementation_secteur)

            # Création de la première version
            version = VersionReglementation(
                reglementation_id=reglementation.id,
                version_numero=1,
                date_creation=datetime.utcnow(),
                contenu="Version initiale de la réglementation",
                modifications_detail="Création initiale"
            )
            db.session.add(version)

            # Assignation automatique aux entreprises des secteurs concernés
            entreprises_concernees = (Entreprise.query
                .join(EntrepriseSecteur)
                .filter(EntrepriseSecteur.secteur_id.in_(form.secteurs.data))
                .distinct().all())

            for entreprise in entreprises_concernees:
                entreprise_reglementation = EntrepriseReglementation(
                    entreprise_id=entreprise.id,
                    reglementation_id=reglementation.id,
                    suivi=True,
                    date_derniere_evaluation=datetime.utcnow()
                )
                db.session.add(entreprise_reglementation)

            db.session.commit()
            flash("Réglementation ajoutée avec succès.", "success")
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation.id))

        except Exception as e:
            db.session.rollback()
            log_error(f"Erreur lors de l'ajout de la réglementation : {str(e)}")
            flash("Une erreur est survenue lors de l'ajout de la réglementation.", "danger")
            return redirect(url_for('reglementation.ajouter_reglementation'))

    return render_template('reglementations/ajouter_reglementation.html', form=form)



@bp.route('/liste-reglementations', methods=['GET'])
@login_required
def liste_reglementations():
    """Route pour afficher la liste des réglementations."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Nombre de réglementations par page
        
        query = Reglementation.query.order_by(Reglementation.date_publication.desc())
        
        # Filtrage par thème si spécifié
        theme_id = request.args.get('theme_id', type=int)
        if theme_id:
            query = query.filter_by(theme_id=theme_id)
        
        # Filtrage par secteur si spécifié
        secteur_id = request.args.get('secteur_id', type=int)
        if secteur_id:
            query = query.join(ReglementationSecteur).filter(ReglementationSecteur.secteur_id == secteur_id)

        # Pagination
        reglementations = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Récupération des données pour les filtres
        themes = Theme.query.order_by(Theme.nom).all()
        secteurs = Secteur.query.order_by(Secteur.nom).all()
        
        # Pour les utilisateurs connectés, récupérer le statut de suivi
        suivi_map = {}
        if current_user.is_authenticated and current_user.entreprise_id:
            suivis = EntrepriseReglementation.query.filter_by(entreprise_id=current_user.entreprise_id).all()
            suivi_map = {reg.reglementation_id: reg for reg in suivis}

        return render_template('reglementations/liste_reglementations.html',
                             reglementations=reglementations,
                             themes=themes,
                             secteurs=secteurs,
                             suivi_map=suivi_map,
                             theme_id=theme_id,
                             secteur_id=secteur_id)

    except Exception as e:
        log_error(f"Erreur lors de la récupération des réglementations : {str(e)}")
        flash("Une erreur est survenue lors de la récupération des réglementations.", "danger")
        return redirect(url_for('main.index'))

@bp.route('/reglementation/<int:id>', methods=['GET'])
@login_required
def detail_reglementation(id):
    """Route pour afficher les détails d'une réglementation."""
    try:
        reglementation = Reglementation.query.get_or_404(id)
        
        # Récupération des informations associées
        versions = VersionReglementation.query.filter_by(reglementation_id=id).order_by(VersionReglementation.version_numero.desc()).all()
        articles = Article.query.filter_by(reglementation_id=id).order_by(Article.numero).all()
        
        # Statut de suivi pour l'entreprise de l'utilisateur actuel
        suivi_entreprise = None
        if current_user.entreprise_id:
            suivi_entreprise = EntrepriseReglementation.query.filter_by(
                entreprise_id=current_user.entreprise_id,
                reglementation_id=id
            ).first()
        
        # Récupération des entreprises qui suivent cette réglementation
        entreprises_suivis = EntrepriseReglementation.query\
            .filter_by(reglementation_id=id)\
            .join(Entreprise)\
            .order_by(Entreprise.nom)\
            .all()

        return render_template('reglementations/detail_reglementation.html',
                             reglementation=reglementation,
                             versions=versions,
                             articles=articles,
                             suivi_entreprise=suivi_entreprise,
                             entreprises_suivis=entreprises_suivis)

    except Exception as e:
        log_error(f"Erreur lors de l'affichage de la réglementation : {str(e)}")
        flash("Une erreur est survenue lors de l'affichage de la réglementation.", "danger")
        return redirect(url_for('reglementation.liste_reglementations'))

##****************** ajout article **********************


class ArticleForm(FlaskForm):
    numero = StringField('Numéro', validators=[DataRequired()])
    titre = StringField('Titre')
    contenu = TextAreaField('Contenu', validators=[DataRequired()])

    submit = SubmitField('Ajouter Article')



@bp.route('/ajouter-article/<int:reglementation_id>', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def ajouter_article(reglementation_id):
    """Route pour ajouter un nouvel article à une réglementation."""
    reglementation = Reglementation.query.get_or_404(reglementation_id)
    form = ArticleForm()

    if form.validate_on_submit():
        try:
            # Vérifier si le numéro d'article existe déjà pour cette réglementation
            existing_article = Article.query.filter_by(
                reglementation_id=reglementation_id,
                numero=form.numero.data
            ).first()
            if existing_article:
                flash("Un article avec ce numéro existe déjà pour cette réglementation.", "warning")
                return redirect(url_for('reglementation.ajouter_article', reglementation_id=reglementation_id))

            article = Article(
                numero=form.numero.data,
                titre=form.titre.data,
                contenu=form.contenu.data,
                reglementation_id=reglementation.id
            )
            db.session.add(article)
            db.session.flush()  # Pour obtenir l'ID de l'article

            # Créer des évaluations pour toutes les entreprises qui suivent cette réglementation
            entreprises_suivies = EntrepriseReglementation.query.filter_by(
                reglementation_id=reglementation_id, 
                suivi=True
            ).all()
            
            for er_suivi in entreprises_suivies:
                evaluation_existante = Evaluation.query.filter_by(
                    entreprise_id=er_suivi.entreprise_id,
                    article_id=article.id
                ).first()
                if not evaluation_existante:
                    evaluation = Evaluation(
                        entreprise_id=er_suivi.entreprise_id,
                        article_id=article.id,
                        applicable=ApplicableEnum.NON_EVALUE,
                        conforme=ConformeEnum.NON_EVALUE,
                        date_derniere_maj=datetime.utcnow()
                    )
                    db.session.add(evaluation)
            
            db.session.commit()
            flash('Article ajouté avec succès. Les évaluations initiales ont été créées.', 'success')
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation.id))
        except Exception as e:
            db.session.rollback()
            log_error(f"Erreur lors de l'ajout de l'article : {str(e)}")
            flash("Une erreur est survenue lors de l'ajout de l'article.", "danger")

    return render_template('articles/ajouter_article.html', form=form, reglementation=reglementation)


# ********************  ajout entreprise et le Manager du compte ****************************************


@bp.route('/modifier-reglementation/<int:reglementation_id>', methods=['GET', 'POST'])
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
        try:
            # Vérifier si le numéro de version a changé et s'il entre en conflit
            if version.version_numero != form.version_numero.data:
                existing_version = VersionReglementation.query.filter_by(
                    reglementation_id=version.reglementation_id,
                    version_numero=form.version_numero.data
                ).first()
                if existing_version:
                    flash("Ce numéro de version existe déjà pour cette réglementation.", "warning")
                    return redirect(url_for('reglementation.modifier_version', version_id=version_id))
            
            version.version_numero = form.version_numero.data
            version.contenu = form.contenu.data
            version.modifications_detail = form.modifications_detail.data
            # La date de création ne change pas, mais on pourrait ajouter une date de modification si nécessaire
            db.session.commit()
            flash('Version modifiée avec succès.', 'success')
            return redirect(url_for('reglementation.detail_reglementation', id=version.reglementation_id))
        except Exception as e:
            db.session.rollback()
            log_error(f"Erreur lors de la modification de la version : {str(e)}")
            flash("Une erreur est survenue lors de la modification de la version.", "danger")

    return render_template('reglementations/modifier_version.html', form=form, version=version)


@bp.route('/supprimer-version/<int:version_id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def supprimer_version(version_id):
    """Route pour supprimer une version."""
    try:
        version = VersionReglementation.query.get_or_404(version_id)
        reglementation_id = version.reglementation_id

        # Vérifier si c'est la dernière version
        if VersionReglementation.query.filter_by(reglementation_id=reglementation_id).count() <= 1:
            flash("Impossible de supprimer la dernière version d'une réglementation.", "warning")
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

        db.session.delete(version)
        db.session.commit()
        flash('Version supprimée avec succès.', 'success')
        return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))
    except Exception as e:
        db.session.rollback()
        log_error(f"Erreur lors de la suppression de la version : {str(e)}")
        flash("Une erreur est survenue lors de la suppression de la version.", "danger")
        return redirect(url_for('reglementation.detail_reglementation', id=version.reglementation_id if 'version' in locals() else url_for('reglementation.liste_reglementations')))


@bp.route('/ajouter-version/<int:reglementation_id>', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def ajouter_version(reglementation_id):
    """Route pour ajouter une nouvelle version d'une réglementation."""
    reglementation = Reglementation.query.get_or_404(reglementation_id)
    form = VersionReglementationForm()

    if form.validate_on_submit():
        try:
            # Vérifier si le numéro de version existe déjà
            if VersionReglementation.query.filter_by(
                reglementation_id=reglementation_id,
                version_numero=form.version_numero.data
            ).first():
                flash("Ce numéro de version existe déjà pour cette réglementation.", "warning")
                return redirect(url_for('reglementation.ajouter_version', reglementation_id=reglementation_id))

            version = VersionReglementation(
                reglementation_id=reglementation_id,
                version_numero=form.version_numero.data,
                contenu=form.contenu.data,
                modifications_detail=form.modifications_detail.data,
                date_creation=datetime.utcnow()
            )
            db.session.add(version)
            
            # Mise à jour de la date de dernière mise à jour de la réglementation
            reglementation.date_derniere_mise_a_jour = datetime.utcnow().date()
            
            db.session.commit()
            flash("Nouvelle version ajoutée avec succès.", "success")
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

        except Exception as e:
            db.session.rollback()
            log_error(f"Erreur lors de l'ajout de la version : {str(e)}")
            flash("Une erreur est survenue lors de l'ajout de la version.", "danger")

    return render_template('reglementations/ajouter_version.html', 
                         form=form, reglementation=reglementation)

@bp.route('/version/<int:version_id>')
@login_required
def detail_version(version_id):
    """Route pour afficher les détails d'une version."""
    try:
        version = VersionReglementation.query.get_or_404(version_id)
        return render_template('reglementations/detail_version.html', version=version)
    except Exception as e:
        log_error(f"Erreur lors de l'affichage de la version : {str(e)}")
        flash("Une erreur est survenue lors de l'affichage de la version.", "danger")
        return redirect(url_for('reglementation.liste_reglementations'))

@bp.route('/reglementation/<int:reglementation_id>/suivre', methods=['POST'])
@login_required
def suivre_reglementation(reglementation_id):
    """Route pour suivre ou ne plus suivre une réglementation."""
    try:
        if not current_user.entreprise_id:
            flash("Vous devez être associé à une entreprise pour suivre une réglementation.", "warning")
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

        suivi = EntrepriseReglementation.query.filter_by(
            entreprise_id=current_user.entreprise_id,
            reglementation_id=reglementation_id
        ).first()

        if suivi:
            # Basculer le statut de suivi
            suivi.suivi = not suivi.suivi
            message = "Suivi désactivé" if not suivi.suivi else "Suivi activé"
        else:
            # Créer une nouvelle association
            suivi = EntrepriseReglementation(
                entreprise_id=current_user.entreprise_id,
                reglementation_id=reglementation_id,
                suivi=True,
                date_derniere_evaluation=datetime.utcnow()
            )
            db.session.add(suivi)
            message = "Suivi activé"

        db.session.commit()
        flash(f"{message} pour cette réglementation.", "success")

    except Exception as e:
        db.session.rollback()
        log_error(f"Erreur lors de la modification du suivi : {str(e)}")
        flash("Une erreur est survenue lors de la modification du suivi.", "danger")

    return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

@bp.route('/reglementation/<int:reglementation_id>/evaluation')
@login_required
def evaluation_reglementation(reglementation_id):
    """Route pour afficher l'évaluation d'une réglementation pour l'entreprise de l'utilisateur."""
    try:
        if not current_user.entreprise_id:
            flash("Vous devez être associé à une entreprise pour voir les évaluations.", "warning")
            return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

        reglementation = Reglementation.query.get_or_404(reglementation_id)
        
        # Récupérer toutes les évaluations pour cette réglementation et cette entreprise
        evaluations = Evaluation.query\
            .join(Article)\
            .filter(
                Article.reglementation_id == reglementation_id,
                Evaluation.entreprise_id == current_user.entreprise_id
            ).order_by(Article.numero).all()

        # Récupérer le suivi de la réglementation
        suivi = EntrepriseReglementation.query.filter_by(
            entreprise_id=current_user.entreprise_id,
            reglementation_id=reglementation_id
        ).first()

        return render_template('reglementations/evaluation.html',
                             reglementation=reglementation,
                             evaluations=evaluations,
                             suivi=suivi)

    except Exception as e:
        log_error(f"Erreur lors de l'affichage de l'évaluation : {str(e)}")
        flash("Une erreur est survenue lors de l'affichage de l'évaluation.", "danger")
        return redirect(url_for('reglementation.detail_reglementation', id=reglementation_id))

@bp.route('/reglementation/<int:reglementation_id>/mise-a-jour-score', methods=['POST'])
@login_required
def mettre_a_jour_score(reglementation_id):
    """Route pour mettre à jour le score de conformité d'une réglementation."""
    try:
        if not current_user.entreprise_id:
            return jsonify(success=False, message="Entreprise non trouvée")

        suivi = EntrepriseReglementation.query.filter_by(
            entreprise_id=current_user.entreprise_id,
            reglementation_id=reglementation_id
        ).first_or_404()

        suivi.mettre_a_jour_score()
        return jsonify(success=True, score=suivi.score)

    except Exception as e:
        log_error(f"Erreur lors de la mise à jour du score : {str(e)}")
        return jsonify(success=False, message="Erreur lors de la mise à jour du score")
