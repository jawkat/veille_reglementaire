from . import db
from uuid import uuid4
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import relationship
from sqlalchemy.types import PickleType
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

class RoleUtilisateur(Enum):
    ADMIN = "admin"
    MANAGER = "Manager"
    RESPONSABLE = "Responsable Veille"
    COLLABORATEUR = "Collaborateur"

class ApplicableEnum(Enum):
    OUI = "Oui"
    NON_EVALUE = "Non évalué"
    NON = "Non"
    INFO = "Information"

class ConformeEnum(Enum):
    CONFORME = "Conforme"
    NON_EVALUE = "Non évalué"
    NON_CONFORME = "Non conforme"

#*************************************************************************************
class User(db.Model, UserMixin):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    role = db.Column(db.Enum(RoleUtilisateur), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"


#*******************************************************************************************


class Secteur(db.Model):
    __tablename__ = 'secteur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    entreprises = db.relationship('Entreprise', secondary='entreprise_secteur', back_populates='secteurs')
    reglementations = db.relationship('ReglementationSecteur', back_populates='secteur', lazy=True)


class EntrepriseSecteur(db.Model):
    __tablename__ = 'entreprise_secteur'
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), primary_key=True)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteur.id'), primary_key=True)

# Organisation

class Entreprise(db.Model):
    __tablename__ = 'entreprise'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True )

    description = db.Column(db.Text, nullable=True)
    pays = db.Column(db.String(100), nullable=True)

    date_creation = db.Column(db.Date, nullable=True)

    utilisateurs = db.relationship('User', backref='entreprise', lazy=True,  cascade="all, delete-orphan")
    reglementations = db.relationship('EntrepriseReglementation', backref='entreprise', lazy=True,  cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='entreprise', lazy=True)
    audits = db.relationship('Audit', backref='entreprise', lazy=True)
    secteurs = db.relationship('Secteur', secondary='entreprise_secteur', back_populates='entreprises',  cascade="all")

    def assign_reglementations(self):
        """Attribuer automatiquement les réglementations liées aux secteurs de l'entreprise."""
        # Créez un ensemble des réglementations déjà associées
        reglementations_existantes = {r.reglementation_id for r in self.reglementations}

        # Ajoutez uniquement les réglementations non associées

    # Ajoutez uniquement les réglementations non associées
        for secteur in self.secteurs:
            for reglementation_secteur in secteur.reglementations:
                reglementation_id = reglementation_secteur.reglementation_id
                if reglementation_id not in reglementations_existantes:
                    # Ajouter la réglementation à l'entreprise
                    entreprise_reglementation = EntrepriseReglementation(
                        entreprise_id=self.id,
                        reglementation_id=reglementation_id,
                        suivi = True
                    )
                    db.session.add(entreprise_reglementation)

                    # Créer les évaluations par défaut pour les articles de cette réglementation
                    reglementation = Reglementation.query.get(reglementation_id)
                    if reglementation:
                        for article in reglementation.articles:
                            evaluation_existante = Evaluation.query.filter_by(
                                entreprise_id=self.id,
                                article_id=article.id
                            ).first()
                            if not evaluation_existante:
                                evaluation = Evaluation(
                                    entreprise_id=self.id,
                                    article_id=article.id,
                                    applicable=ApplicableEnum.NON_EVALUE,
                                    conforme=ConformeEnum.NON_EVALUE
                                )
                                db.session.add(evaluation)


class ReglementationSecteur(db.Model):
    __tablename__ = 'reglementation_secteur'
    id = db.Column(db.Integer, primary_key=True)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteur.id'), nullable=False)

    # Relations explicites
    secteur = db.relationship('Secteur', back_populates='reglementations')
    reglementation = db.relationship('Reglementation', back_populates='secteurs')


class Domaine(db.Model):
    __tablename__ = 'domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    sous_domaines = db.relationship('SousDomaine', backref='domaine', lazy=True)

class SousDomaine(db.Model):
    __tablename__ = 'sous_domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id'), nullable=False)
    reglementations = db.relationship('Reglementation', backref='sous_domaine', lazy=True)

class Reglementation(db.Model):
    __tablename__ = 'reglementation'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False, unique=True)
    type_texte = db.Column(db.String(100), nullable=False)
    date_publication = db.Column(db.Date, nullable=False)
    date_derniere_mise_a_jour = db.Column(db.Date, nullable=True)
    source = db.Column(db.String(200), nullable=False)
    langue = db.Column(db.String(50), nullable=True)

    secteurs=db.relationship('ReglementationSecteur', back_populates='reglementation', lazy=True, cascade='all, delete-orphan')

    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=False)
    sous_domaine_id = db.Column(db.Integer, db.ForeignKey('sous_domaine.id'), nullable=False)
    versions = db.relationship('VersionReglementation', backref='reglementation', lazy=True, cascade='all, delete-orphan')
    articles = db.relationship('Article', backref='reglementation', lazy=True, cascade='all, delete-orphan')

class EntrepriseReglementation(db.Model):
    __tablename__ = 'entreprise_reglementation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    suivi = db.Column(db.Boolean, default=True, nullable=False)  # Permet de savoir si l'entreprise suit cette réglementation
    score = db.Column(db.Integer, default=0, nullable=True)

    reglementation = db.relationship('Reglementation', backref='entreprises_associees')


    def mettre_a_jour_score(self):
        """
        Met à jour le score basé sur les évaluations des articles de la réglementation pour cette entreprise.
        """
        # Obtenir la réglementation liée à cette instance d'EntrepriseReglementation
        reglementation = self.reglementation

        # Initialiser les compteurs pour les articles applicables et conformes
        total_applicable = 0
        total_conforme = 0

        # Parcourir tous les articles de la réglementation
        for article in reglementation.articles:
            # Vérifier si l'article a des évaluations
            if article.evaluations:
                # Parcourir toutes les évaluations pour cet article
                for evaluation in article.evaluations:
                    # Vérifier si l'évaluation est applicable pour cette entreprise
                    if evaluation.entreprise_id == self.entreprise_id and evaluation.applicable.name == "OUI":
                        total_applicable += 1  # L'article est applicable
                        if evaluation.conforme.name == "CONFORME":
                            total_conforme += 1  # L'article est conforme

        # Calculer le score
        if total_applicable == 0:
            self.score = 0  # Éviter la division par zéro
        else:
            self.score = round((total_conforme / total_applicable) * 100)

        # Sauvegarder le score dans la base de données
        db.session.commit()



class Theme(db.Model):
    __tablename__ = 'theme'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    reglementations = db.relationship('Reglementation', backref='theme', lazy=True)

class VersionReglementation(db.Model):
    __tablename__ = 'version_reglementation'
    id = db.Column(db.Integer, primary_key=True)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    version_numero = db.Column(db.Integer, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    contenu = db.Column(db.Text, nullable=False)

class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    titre = db.Column(db.String(200), nullable=True)
    contenu = db.Column(db.Text, nullable=True)

    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    evaluations = db.relationship('Evaluation', backref='article', lazy=True)

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

    applicable = db.Column(db.Enum(ApplicableEnum), nullable=True, default=ApplicableEnum.NON_EVALUE)
    conforme = db.Column(db.Enum(ConformeEnum), nullable=True, default=ConformeEnum.NON_EVALUE)

    champ_d_application = db.Column(db.Text, nullable=True)  # Description du champ d'application
    commentaires = db.Column(db.Text, nullable=True)
    actions = db.relationship('Action', backref='evaluation', lazy=True)



class Action(db.Model):
    __tablename__ = 'action'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    responsable = db.Column(db.String(100), nullable=False)
    date_echeance = db.Column(db.Date, nullable=False)
    date_realisation = db.Column(db.Date, nullable=True)
    statut = db.Column(db.String(50), nullable=False)  # Exemple : "En cours", "Réalisée"
    kpi = db.Column(db.Float, nullable=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type_notification = db.Column(db.String(50), nullable=False)  # Exemple : "Mise à jour", "Rappel"
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)

class Audit(db.Model):
    __tablename__ = 'audit'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_audit = db.Column(db.Date, nullable=False)
    resultat = db.Column(db.String(50), nullable=False)  # Exemple : "Conforme", "Non Conforme"
    observations = db.Column(db.Text, nullable=True)
    rapport = db.Column(db.Text, nullable=True)
