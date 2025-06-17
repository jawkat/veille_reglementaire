from . import db
from uuid import uuid4
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# Note: itsdangerous.URLSafeTimedSerializer is typically used for tokens (e.g., password reset),
# but its import is not strictly part of the DB model definition itself.
# from itsdangerous import URLSafeTimedSerializer as Serializer 


# --- Enums ---

class RoleUtilisateur(Enum):
    ADMIN = "admin"
    MANAGER = "Manager"
    RESPONSABLE = "Responsable Veille"
    COLLABORATEUR = "Collaborateur"
    AUDITEUR = "Auditeur"
    CONSULTANT = "Consultant"

class ApplicableEnum(Enum):
    OUI = "Oui"
    NON_EVALUE = "Non évalué"
    NON = "Non"
    INFO = "Information"
    PARTIEL = "Partiellement Applicable"

class SeveriteEnum(Enum):
    FAIBLE = "Faible"
    MOYEN = "Moyen"
    ELEVE = "Élevé"
    CRITIQUE = "Critique"

class StatutAlerte(Enum):
    NOUVEAU = "Nouveau"
    EN_COURS = "En cours"
    TRAITE = "Traité"
    ARCHIVE = "Archivé"

class ConformeEnum(Enum):
    CONFORME = "Conforme"
    NON_EVALUE = "Non évalué"
    NON_CONFORME = "Non conforme"

# --- Database Models ---

class User(db.Model, UserMixin):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    role = db.Column(db.Enum(RoleUtilisateur), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True)

    # Relations
    entreprise = db.relationship('Entreprise', back_populates='utilisateurs')
    reglementations_supervisees = db.relationship(
        'EntrepriseReglementation', back_populates='responsable', lazy=True
    )
    # Add other relationships if 'User' is linked to 'Evaluation' or 'Action' for auditing/responsibility
    # For example, if User can update an Evaluation:
    # evaluations_made = db.relationship('Evaluation', back_populates='last_updated_by', lazy=True)
    # If User can be assigned an Action:
    # actions_assigned = db.relationship('Action', back_populates='assigned_to_user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # These token methods are for user authentication/password reset and rely on Flask app config
    # You'd typically include them in your application's User model
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
        return f"User('{self.name}', '{self.email}', '{self.role.value}')"


class Secteur(db.Model):
    __tablename__ = 'secteur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relations Many-to-Many via association tables
    entreprises = db.relationship('Entreprise', secondary='entreprise_secteur', back_populates='secteurs')
    reglementations_via_link = db.relationship('ReglementationSecteur', back_populates='secteur', lazy=True, cascade="all, delete-orphan")


class EntrepriseSecteur(db.Model):
    __tablename__ = 'entreprise_secteur'
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), primary_key=True)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteur.id'), primary_key=True)


class Entreprise(db.Model):
    __tablename__ = 'entreprise'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    pays = db.Column(db.String(100), nullable=True)
    date_creation = db.Column(db.Date, default=datetime.utcnow().date(), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Active")

    # Relations One-to-Many
    utilisateurs = db.relationship('User', back_populates='entreprise', lazy=True, cascade="all, delete-orphan")
    reglementations_suivies = db.relationship('EntrepriseReglementation', back_populates='entreprise', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', back_populates='entreprise', lazy=True, cascade="all, delete-orphan")
    audits = db.relationship('Audit', back_populates='entreprise', lazy=True, cascade="all, delete-orphan")
    
    # New: Relationship for Evaluations (one-to-many from Entreprise to Evaluation)
    evaluations_received_from_evaluation = db.relationship('Evaluation', back_populates='entreprise', lazy=True, cascade="all, delete-orphan")

    # Relation Many-to-Many with Secteur
    secteurs = db.relationship('Secteur', secondary='entreprise_secteur', back_populates='entreprises')

    def assign_reglementations(self):
        """
        Automatically assigns regulations linked to the company's sectors
        and initializes evaluations for their articles.
        """
        reglementations_existantes_ids = {r.reglementation_id for r in self.reglementations_suivies}
        nouvelles_reglementations_a_suivre = []
        nouvelles_evaluations_a_creer = []

        for secteur in self.secteurs:
            for reg_sect_link in secteur.reglementations_via_link: 
                reglementation_id = reg_sect_link.reglementation_id
                if reglementation_id not in reglementations_existantes_ids:
                    nouvelles_reglementations_a_suivre.append(EntrepriseReglementation(
                        entreprise_id=self.id,
                        reglementation_id=reglementation_id,
                        suivi = True
                    ))
                    reglementations_existantes_ids.add(reglementation_id) 

                    reglementation = reg_sect_link.reglementation
                    if reglementation:
                        for article in reglementation.articles:
                            evaluation_existante = Evaluation.query.filter_by(
                                entreprise_id=self.id,
                                article_id=article.id
                            ).first()
                            if not evaluation_existante:
                                nouvelles_evaluations_a_creer.append(Evaluation(
                                    entreprise_id=self.id,
                                    article_id=article.id,
                                    applicable=ApplicableEnum.NON_EVALUE,
                                    conforme=ConformeEnum.NON_EVALUE,
                                    date_derniere_maj=datetime.utcnow()
                                ))
        try:
            db.session.add_all(nouvelles_reglementations_a_suivre)
            db.session.add_all(nouvelles_evaluations_a_creer)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de l'ajout des réglementations : {e}")
            raise 

class ReglementationSecteur(db.Model):
    __tablename__ = 'reglementation_secteur'
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), primary_key=True)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteur.id'), primary_key=True)

    # Relations
    secteur = db.relationship('Secteur', back_populates='reglementations_via_link')
    reglementation = db.relationship('Reglementation', back_populates='secteurs_via_link')


class Domaine(db.Model):
    __tablename__ = 'domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relations
    sous_domaines = db.relationship('SousDomaine', back_populates='domaine', lazy=True, cascade="all, delete-orphan")


class SousDomaine(db.Model):
    __tablename__ = 'sous_domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id'), nullable=False)
    
    # Relations
    domaine = db.relationship('Domaine', back_populates='sous_domaines')
    reglementations = db.relationship('Reglementation', back_populates='sous_domaine', lazy=True, cascade="all, delete-orphan")

class Reglementation(db.Model):
    __tablename__ = 'reglementation'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False, unique=True)
    type_texte = db.Column(db.String(100), nullable=False)
    date_publication = db.Column(db.Date, nullable=False)
    date_derniere_mise_a_jour = db.Column(db.Date, nullable=True)
    source = db.Column(db.String(200), nullable=False)
    langue = db.Column(db.String(50), nullable=True)
    
    # Content fields
    resume_exigences = db.Column(db.Text, nullable=True)

    # Foreign Keys
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=False)
    sous_domaine_id = db.Column(db.Integer, db.ForeignKey('sous_domaine.id'), nullable=False)

    # Relations
    secteurs_via_link = db.relationship('ReglementationSecteur', back_populates='reglementation', lazy=True, cascade='all, delete-orphan')
    theme = db.relationship('Theme', back_populates='reglementations')
    sous_domaine = db.relationship('SousDomaine', back_populates='reglementations')
    versions = db.relationship('VersionReglementation', back_populates='reglementation', lazy=True, cascade='all, delete-orphan')
    articles = db.relationship('Article', back_populates='reglementation', lazy=True, cascade='all, delete-orphan')
    entreprises_associees = db.relationship('EntrepriseReglementation', back_populates='reglementation', lazy=True)

    # Constraints
    __table_args__ = (UniqueConstraint('titre', name='_reglementation_titre_uc'),)


class EntrepriseReglementation(db.Model):
    __tablename__ = 'entreprise_reglementation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    
    suivi = db.Column(db.Boolean, default=True, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    
    # Risk assessment fields
    niveau_risque = db.Column(db.Enum(SeveriteEnum), nullable=True) 
    impact_financier = db.Column(db.Float, nullable=True)
    probabilite = db.Column(db.Integer, nullable=True)
    date_derniere_evaluation = db.Column(db.DateTime, nullable=True)
    
    # Monitoring fields
    frequence_revision = db.Column(db.Integer, nullable=True)
    prochaine_revision = db.Column(db.DateTime, nullable=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    
    # Relationships
    entreprise = db.relationship('Entreprise', back_populates='reglementations_suivies')
    reglementation = db.relationship('Reglementation', back_populates='entreprises_associees')
    responsable = db.relationship('User', back_populates='reglementations_supervisees')
    
    # Constraints
    __table_args__ = (UniqueConstraint('entreprise_id', 'reglementation_id', name='_entreprise_reglementation_uc'),)


    def mettre_a_jour_score(self):
        """
        Updates the overall compliance score for this regulation for this company,
        based on the evaluations of all articles of the regulation.
        """
        reglementation = self.reglementation

        total_applicable = 0
        total_conforme = 0

        # Query evaluations specific to this company and this regulation's articles
        evaluations_pertinentes = db.session.query(Evaluation).join(Article).filter(
            Evaluation.entreprise_id == self.entreprise_id,
            Article.reglementation_id == self.reglementation_id
        ).all()

        for evaluation in evaluations_pertinentes:
            if evaluation.applicable == ApplicableEnum.OUI:
                total_applicable += 1
                if evaluation.conforme == ConformeEnum.CONFORME:
                    total_conforme += 1

        if total_applicable == 0:
            self.score = 0
        else:
            self.score = round((total_conforme / total_applicable) * 100)

        db.session.add(self) 
        db.session.commit()


class Theme(db.Model):
    __tablename__ = 'theme'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    # Relations
    reglementations = db.relationship('Reglementation', back_populates='theme', lazy=True, cascade="all, delete-orphan")

class VersionReglementation(db.Model):
    __tablename__ = 'version_reglementation'
    id = db.Column(db.Integer, primary_key=True)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    
    version_numero = db.Column(db.Integer, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    modifications_detail = db.Column(db.Text, nullable=True)

    # Relations
    reglementation = db.relationship('Reglementation', back_populates='versions')

    # Constraints
    __table_args__ = (UniqueConstraint('reglementation_id', 'version_numero', name='_reglementation_version_numero_uc'),)


class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    titre = db.Column(db.String(200), nullable=True)
    contenu = db.Column(db.Text, nullable=True)

    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    # Relations
    reglementation = db.relationship('Reglementation', back_populates='articles')
    evaluations = db.relationship('Evaluation', back_populates='article', lazy=True, cascade='all, delete-orphan')

    # Constraints
    __table_args__ = (UniqueConstraint('reglementation_id', 'numero', name='_reglementation_article_numero_uc'),)


class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

    # Relations (explicitly defined for clarity and to resolve errors)
    entreprise = db.relationship('Entreprise', back_populates='evaluations_received_from_evaluation')
    article = db.relationship('Article', back_populates='evaluations')

    applicable = db.Column(db.Enum(ApplicableEnum), nullable=False, default=ApplicableEnum.NON_EVALUE)
    conforme = db.Column(db.Enum(ConformeEnum), nullable=False, default=ConformeEnum.NON_EVALUE)

    champ_d_application = db.Column(db.Text, nullable=True)
    commentaires = db.Column(db.Text, nullable=True)
    date_derniere_maj = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    actions = db.relationship('Action', back_populates='evaluation', lazy=True, cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (UniqueConstraint('entreprise_id', 'article_id', name='_entreprise_article_evaluation_uc'),)


class Action(db.Model):
    __tablename__ = 'action'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    
    responsable = db.Column(db.String(100), nullable=False) # This is a string field, not a FK to User.
    
    date_echeance = db.Column(db.Date, nullable=False)
    date_realisation = db.Column(db.Date, nullable=True)
    statut = db.Column(db.String(50), nullable=False)
    priorite = db.Column(db.String(50), nullable=True)
    kpi = db.Column(db.Float, nullable=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)

    # Relations
    evaluation = db.relationship('Evaluation', back_populates='actions')


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type_notification = db.Column(db.String(50), nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)

    # Relations
    entreprise = db.relationship('Entreprise', back_populates='notifications')


class Audit(db.Model):
    __tablename__ = 'audit'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_audit = db.Column(db.Date, default=datetime.utcnow().date(), nullable=False)
    type_audit = db.Column(db.String(50), nullable=False)
    resultat = db.Column(db.String(50), nullable=False)
    observations = db.Column(db.Text, nullable=True)
    rapport = db.Column(db.Text, nullable=True)
    auditeur = db.Column(db.String(100), nullable=False)
    plan_actions = db.Column(db.Text, nullable=True)

    # Relations
    entreprise = db.relationship('Entreprise', back_populates='audits')