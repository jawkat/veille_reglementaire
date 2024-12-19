from . import db
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import relationship
from sqlalchemy.types import PickleType
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash



#*************************************************************************************
class User(db.Model, UserMixin):
    __tablename__ = 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(10))  # Exemple: "Admin", "Manager", "Collaborateur"
    password_hash = db.Column(db.String(128), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}).decode('utf-8')

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

# Organisation

class Entreprise(db.Model):
    __tablename__ = 'entreprise'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    secteur = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    pays = db.Column(db.String(100), nullable=True)
    utilisateurs = db.relationship('User', backref='entreprise', lazy=True)
    reglementations = db.relationship('EntrepriseReglementation', backref='entreprise', lazy=True)
    notifications = db.relationship('Notification', backref='entreprise', lazy=True)
    audits = db.relationship('Audit', backref='entreprise', lazy=True)


class Domaine(db.Model):
    __tablename__ = 'domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sous_domaines = db.relationship('SousDomaine', backref='domaine', lazy=True)

class SousDomaine(db.Model):
    __tablename__ = 'sous_domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id'), nullable=False)
    reglementations = db.relationship('Reglementation', backref='sous_domaine', lazy=True)

class Reglementation(db.Model):
    __tablename__ = 'reglementation'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    type_texte = db.Column(db.String(100), nullable=False)
    date_publication = db.Column(db.Date, nullable=False)
    date_derniere_mise_a_jour = db.Column(db.Date, nullable=True)
    source = db.Column(db.String(200), nullable=False)
    secteurs_concernes = db.Column(db.String(200), nullable=True)
    theme_id = db.Column(db.Integer, db.ForeignKey('theme.id'), nullable=False)
    sous_domaine_id = db.Column(db.Integer, db.ForeignKey('sous_domaine.id'), nullable=False)
    versions = db.relationship('VersionReglementation', backref='reglementation', lazy=True)
    articles = db.relationship('Article', backref='reglementation', lazy=True)

class Theme(db.Model):
    __tablename__ = 'theme'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
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
    titre = db.Column(db.String(200), nullable=False)
    contenu = db.Column(db.Text, nullable=True)
    langue = db.Column(db.String(50), nullable=True)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    evaluations = db.relationship('Evaluation', backref='article', lazy=True)

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    applicable = db.Column(db.String(20), nullable=False)  # "Applicable", "Non Applicable"
    conforme = db.Column(db.String(20), nullable=True)  # "Conforme", "Non Conforme"
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

class EntrepriseReglementation(db.Model):
    __tablename__ = 'entreprise_reglementation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementation.id'), nullable=False)
    suivi = db.Column(db.Boolean, default=True, nullable=False)  # Permet de savoir si l'entreprise suit cette réglementation