from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import create_engine
from app import create_app, db  # Remplacez par l'import correct de votre app Flask

# Créez l'application et le contexte
app = create_app()  # Remplacez par la fonction qui initialise votre app
with app.app_context():  # Assurez-vous que le contexte de l'app est actif
    # Créer l'engine SQLAlchemy à partir de la configuration de votre application
    engine = create_engine(db.engine.url)

    # Génération du schéma
    graph = create_schema_graph(
        metadata=db.metadata,
        engine=engine,          # Ajoutez l'engine ici
        show_datatypes=True,    # Affiche les types de données
        show_indexes=True,      # Inclut les index
        rankdir="LR",           # Orientation gauche-droite
    )

    # Sauvegarde du schéma au format PNG
    graph.write_png("schema.png")
    print("Diagramme généré avec succès dans 'schema.png'")
