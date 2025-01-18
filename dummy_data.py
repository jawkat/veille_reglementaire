from datetime import datetime, timedelta
from app import create_app, db
from app.models import Secteur, Entreprise, ReglementationSecteur, Domaine, SousDomaine, Reglementation, Theme, VersionReglementation, Article, Evaluation, Action, Notification, Audit

app = create_app()

def generate_dummy_data():
    # Clear existing data
    db.session.query(Notification).delete()
    db.session.query(Action).delete()
    db.session.query(Evaluation).delete()
    db.session.query(Article).delete()
    db.session.query(VersionReglementation).delete()
    db.session.query(Reglementation).delete()
    db.session.query(SousDomaine).delete()
    db.session.query(Domaine).delete()
    db.session.query(Theme).delete()
    db.session.query(Entreprise).delete()
    db.session.query(Secteur).delete()
    db.session.commit()

    # Secteurs
    secteur1 = Secteur(nom="Technologie", description="Secteur lié aux technologies modernes.")
    secteur2 = Secteur(nom="Énergie", description="Secteur lié aux ressources énergétiques.")
    db.session.add_all([secteur1, secteur2])
    db.session.commit()

    # Entreprises
    entreprise1 = Entreprise(nom="TechCorp", secteur="Technologie", description="Entreprise spécialisée dans les logiciels.", pays="France", secteur_id=secteur1.id)
    entreprise2 = Entreprise(nom="GreenPower", secteur="Énergie", description="Entreprise spécialisée dans les énergies renouvelables.", pays="Allemagne", secteur_id=secteur2.id)
    db.session.add_all([entreprise1, entreprise2])
    db.session.commit()

    # Domaines et Sous-Domaines
    domaine1 = Domaine(nom="Informatique", description="Domaine lié aux technologies de l'information.")
    domaine2 = Domaine(nom="Énergies renouvelables", description="Domaine lié aux énergies renouvelables.")
    db.session.add_all([domaine1, domaine2])
    db.session.commit()

    sous_domaine1 = SousDomaine(nom="Développement logiciel", description="Sous-domaine de l'informatique.", domaine_id=domaine1.id)
    sous_domaine2 = SousDomaine(nom="Énergie solaire", description="Sous-domaine des énergies renouvelables.", domaine_id=domaine2.id)
    db.session.add_all([sous_domaine1, sous_domaine2])
    db.session.commit()

    # Thèmes et Réglementations
    theme1 = Theme(nom="Sécurité informatique", description="Thème lié à la sécurité des systèmes informatiques.")
    theme2 = Theme(nom="Normes environnementales", description="Thème lié aux normes de protection de l'environnement.")
    db.session.add_all([theme1, theme2])
    db.session.commit()

    reglementation1 = Reglementation(
        titre="RGPD",
        type_texte="Règlement",
        date_publication=datetime(2018, 5, 25),
        source="https://europa.eu",
        theme_id=theme1.id,
        sous_domaine_id=sous_domaine1.id
    )
    reglementation2 = Reglementation(
        titre="Directive Énergies Renouvelables",
        type_texte="Directive",
        date_publication=datetime(2021, 3, 10),
        source="https://europa.eu",
        theme_id=theme2.id,
        sous_domaine_id=sous_domaine2.id
    )
    db.session.add_all([reglementation1, reglementation2])
    db.session.commit()

    # Versions des Réglementations
    version1 = VersionReglementation(reglementation_id=reglementation1.id, version_numero=1, contenu="Version initiale.")
    version2 = VersionReglementation(reglementation_id=reglementation2.id, version_numero=1, contenu="Version initiale.")
    db.session.add_all([version1, version2])
    db.session.commit()

    # Articles
    article1 = Article(numero="1", titre="Protection des données", contenu="Contenu sur la protection des données.", langue="FR", reglementation_id=reglementation1.id)
    article2 = Article(numero="2", titre="Transition énergétique", contenu="Contenu sur la transition énergétique.", langue="FR", reglementation_id=reglementation2.id)
    db.session.add_all([article1, article2])
    db.session.commit()

    # Évaluations
    evaluation1 = Evaluation(entreprise_id=entreprise1.id, article_id=article1.id, applicable="Applicable", conforme="Conforme", champ_d_application="Champ spécifique à TechCorp.", commentaires="Rien à signaler.")
    evaluation2 = Evaluation(entreprise_id=entreprise2.id, article_id=article2.id, applicable="Applicable", conforme="Non Conforme", champ_d_application="Champ spécifique à GreenPower.", commentaires="Actions correctives requises.")
    db.session.add_all([evaluation1, evaluation2])
    db.session.commit()

    # Actions Correctives
    action1 = Action(description="Mettre en place des mesures de sécurité", responsable="Jean Dupont", date_echeance=datetime.now() + timedelta(days=30), statut="En cours", evaluation_id=evaluation1.id)
    action2 = Action(description="Réduire les émissions de CO2", responsable="Hans Müller", date_echeance=datetime.now() + timedelta(days=45), statut="En cours", evaluation_id=evaluation2.id)
    db.session.add_all([action1, action2])
    db.session.commit()

    # Notifications
    notification1 = Notification(titre="Mise à jour RGPD", message="Nouvelle version du RGPD disponible.", type_notification="Mise à jour", entreprise_id=entreprise1.id)
    notification2 = Notification(titre="Rappel Audit", message="Audit à réaliser avant la fin du mois.", type_notification="Rappel", entreprise_id=entreprise2.id)
    db.session.add_all([notification1, notification2])
    db.session.commit()

    # Audit
    audit1 = Audit(entreprise_id=entreprise1.id, date_audit=datetime.now(), resultat="Conforme", observations="Bon respect des normes.", rapport="Rapport PDF")
    audit2 = Audit(entreprise_id=entreprise2.id, date_audit=datetime.now(), resultat="Non Conforme", observations="Améliorations nécessaires.", rapport="Rapport PDF")
    db.session.add_all([audit1, audit2])
    db.session.commit()

    print("Données fictives créées avec succès.")

# Exécuter la génération des données
if __name__ == "__main__":
    with app.app_context():
        generate_dummy_data()
