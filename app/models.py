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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    num = num = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(10))  # 'student' or 'instructor'
    password_hash = db.Column(db.String(128), nullable=False)



    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Generate a password reset token
    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    # Verify the reset token
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
class Organisation(db.Model):
    __tablename__ = 'organisations'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteurs.id'), nullable=False)
    utilisateurs = db.relationship('Utilisateur', backref='organisation', lazy=True)
    conformites = db.relationship('Conformite', backref='organisation', lazy=True)
    non_conformites = db.relationship('NonConformite', backref='organisation', lazy=True)
    # audits = db.relationship('Audit', backref='organisation', lazy=True)


# Utilisateur
class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)


# Secteur
class Secteur(db.Model):
    __tablename__ = 'secteurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    organisations = db.relationship('Organisation', backref='secteur', lazy=True)
    reglementations = db.relationship('Reglementation', secondary='secteur_reglementation', back_populates='secteurs')


# Association Secteur-Reglementation
secteur_reglementation = db.Table(
    'secteur_reglementation',
    db.Column('secteur_id', db.Integer, db.ForeignKey('secteurs.id'), primary_key=True),
    db.Column('reglementation_id', db.Integer, db.ForeignKey('reglementations.id'), primary_key=True)
)


# Réglementation
class Reglementation(db.Model):
    __tablename__ = 'reglementations'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_publication = db.Column(db.Date, nullable=False)
    secteurs = db.relationship('Secteur', secondary='secteur_reglementation', back_populates='reglementations')
    articles = db.relationship('Article', backref='reglementation', lazy=True)


# Article
class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    reglementation_id = db.Column(db.Integer, db.ForeignKey('reglementations.id'), nullable=False)
    conformites = db.relationship('Conformite', backref='article', lazy=True)
    non_conformites = db.relationship('NonConformite', backref='article', lazy=True)


# Conformité
class Conformite(db.Model):
    __tablename__ = 'conformites'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    statut = db.Column(db.String(50), nullable=False)  # Conforme, Non-Conforme, En cours
    date_derniere_verification = db.Column(db.DateTime, default=datetime.utcnow)
    commentaire = db.Column(db.Text, nullable=True)


# Non-Conformité
class NonConformite(db.Model):
    __tablename__ = 'non_conformites'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_identification = db.Column(db.DateTime, default=datetime.utcnow)
    critique = db.Column(db.String(50), nullable=False)  # Mineur, Majeur, Critique
    statut = db.Column(db.String(50), nullable=False)  # Ouvert, En cours, Fermé
    actions_correctives = db.relationship('ActionCorrective', backref='non_conformite', lazy=True)


# Action Corrective
class ActionCorrective(db.Model):
    __tablename__ = 'actions_correctives'
    id = db.Column(db.Integer, primary_key=True)
    non_conformite_id = db.Column(db.Integer, db.ForeignKey('non_conformites.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsable = db.Column(db.String(100), nullable=False)
    date_echeance = db.Column(db.Date, nullable=False)
    date_realisation = db.Column(db.Date, nullable=True)
    statut = db.Column(db.String(50), nullable=False)  # À faire, En cours, Terminé
    efficacite = db.Column(db.Boolean, nullable=True)  # None si pas encore évaluée


# # Audit
# class Audit(db.Model):
#     __tablename__ = 'audits'
#     id = db.Column(db.Integer, primary_key=True)
#     organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)
#     date_audit = db.Column(db.DateTime, default=datetime.utcnow)
#     actions_correctives = db.relationship('ActionCorrective', backref='audit', lazy=True)
#     statut_actions = db.Column(db.String(50), nullable=True)  # Globalement Terminé, En cours, Bloqué
