from app import create_app, db
from app.models import User, Entreprise, Secteur


app = create_app()

with app.app_context():
    db.create_all()
    print("Base de données initialisée")

with app.app_context():

     # Vérifier si le secteur "Technologie" existe déjà
    secteur = Secteur.query.filter_by(nom='Technologie').first()

    if not secteur:
        # Créer le secteur "Technologie"
        secteur = Secteur(
            nom='Technologie',
            description="Secteur des technologies de l'information."
        )
        db.session.add(secteur)
        db.session.commit()
        print("Secteur 'Technologie' ajouté avec succès.")

     # Vérifier si l'entreprise existe déjà
    entreprise = Entreprise.query.filter_by(nom='JK-Info').first()

    if not entreprise:
        # Créer une instance de l'entreprise
        entreprise = Entreprise(
            nom='JK-Info',
            secteur_id=secteur.id,  # Utilisation de la clé étrangère
            description="Entreprise innovante dans le secteur des technologies de l'information.",
            pays='Maroc'
        )
        db.session.add(entreprise)
        db.session.commit()
        print("Entreprise 'JK-Info' ajoutée avec succès.")

    # Vérifier si l'administrateur existe déjà
    admin_user = User.query.filter_by(email='jwd.katten@gmail.com').first()

    if not admin_user:
        # Créer une instance de l'utilisateur administrateur
        admin_user = User(
            name='admin',
            email='jwd.katten@gmail.com',
            role='admin',
            entreprise_id=entreprise.id  # Lier l'utilisateur à l'entreprise
        )
        # Définir le mot de passe de l'administrateur
        admin_user.set_password('00')

    # Add the user to the database
    db.session.add(admin_user)
    db.session.commit()

    print("Utilisateur administrateur ajouté avec succès.")
