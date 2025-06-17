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

bp = Blueprint('theme', __name__)




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

