from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request
from app.models import  User
from app import db

from flask_login import login_required, current_user
from app.routes.admin import role_required

bp = Blueprint('main', __name__)

features = [
    {
        'nom': 'Ajout Stock Critique',
        'description': 'En plus du stock, l\'ajout du stock critique déclenche une réapprovisionnement en urgence.',
        'demande_par': 'Si Youssef',
        'status': 'En cours'
    },
    {
        'nom': 'Correction Bug Interface',
        'description': 'Correction d\'un bug lors de l\'ajout d\'une nouvelle entrée d\'ingrédient.',
        'demande_par': 'Mme Dyaa',
        'status': 'Complété'
    },
]


@bp.route('/home')
@login_required
def index():
    return render_template('main/index.html', features=features)

