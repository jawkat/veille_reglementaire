from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager



db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)


    # Set the login view for the LoginManager
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'You must be logged in to access this page.'
    login_manager.login_message_category = 'info'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    # Register Blueprints
    from .routes.main import bp as main_bp
    from .routes.admin import bp as admin_bp

    from .routes.reglementation import bp as reglementation_bp
    from .routes.manager import bp as manager_bp
    from .routes.evaluation import bp as evaluation_bp
    from .routes.entreprise import bp as entreprise_bp
    from .routes.article import bp as article_bp
    
    from .routes.theme import bp as theme_bp
    from .routes.domaine import bp as domaine_bp
    from .routes.secteur import bp as secteur_bp
    




    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reglementation_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(entreprise_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(theme_bp)
    app.register_blueprint(domaine_bp)
    app.register_blueprint(secteur_bp)

    return app
