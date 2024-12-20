from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request
from app.models import  User
from app import db

from flask_login import login_required, current_user
from app.routes.admin import role_required

bp = Blueprint('main', __name__)



@bp.route('/')
@login_required
def index():
    return render_template('main/index.html')
