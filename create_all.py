from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()
    print("Base de données initialisée")

with app.app_context():
    # Create a new user instance
    admin_user = User(
        name='admin',
        email='jwd.katten@gmail.com',
        role='admin'
    )

    # Set the user's password (assuming the set_password method hashes the password)
    admin_user.set_password('00')

    # Add the user to the database
    db.session.add(admin_user)
    db.session.commit()

    print("Admin user added successfully.")
