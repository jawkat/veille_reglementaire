from app import create_app, db
from app.models import User, Entreprise, Secteur, Reglementation, ReglementationSecteur, Domaine, SousDomaine, Theme, Article, Evaluation, EntrepriseReglementation
from datetime import datetime
from app.models import RoleUtilisateur, ApplicableEnum, ConformeEnum

app = create_app()

with app.app_context():
    db.create_all()
    print("Base de données initialisée")

with app.app_context():
    # --- Création du Secteur ---
    secteur = Secteur.query.filter_by(nom='Technologie').first()

    if not secteur:
        secteur = Secteur(
            nom='Technologie',
            description="Secteur des technologies de l'information."
        )
        db.session.add(secteur)
        db.session.commit()
        print("Secteur 'Technologie' ajouté avec succès.")
    else:
        print("Secteur 'Technologie' existe déjà.")

    # --- Création de l'Entreprise ---
    entreprise = Entreprise.query.filter_by(nom='JK-Info').first()

    if not entreprise:
        entreprise = Entreprise(
            nom='JK-Info',
            description="Entreprise innovante dans le secteur des technologies de l'information.",
            pays='Maroc'
        )
        db.session.add(entreprise)
        db.session.commit()
        print("Entreprise 'JK-Info' ajoutée avec succès.")

        entreprise.secteurs.append(secteur)
        db.session.commit()
        print(f"Secteur '{secteur.nom}' associé à l'entreprise '{entreprise.nom}'.")
    else:
        print("Entreprise 'JK-Info' existe déjà.")

    # --- Création de l'Utilisateur Administrateur ---
    admin_user = User.query.filter_by(email='jwd.katten@gmail.com').first()

    if not admin_user:
        admin_user = User(
            name='admin',
            email='jwd.katten@gmail.com',
            role=RoleUtilisateur.ADMIN,
            entreprise=entreprise
        )
        admin_user.set_password('00')
        db.session.add(admin_user)
        db.session.commit()
        print("Utilisateur administrateur ajouté avec succès.")
    else:
        print("Utilisateur administrateur existe déjà.")

    # --- Initialisation de données supplémentaires ---

    # Créer Domaine et SousDomaine
    domaine_env = Domaine.query.filter_by(nom="Environnement").first()
    if not domaine_env:
        domaine_env = Domaine(nom="Environnement", description="Réglementations environnementales")
        db.session.add(domaine_env)
        db.session.commit()
        print("Domaine 'Environnement' ajouté.")
    else:
        print("Domaine 'Environnement' existe déjà.")

    sous_domaine_air = SousDomaine.query.filter_by(nom="Qualité de l'Air").first()
    if not sous_domaine_air:
        sous_domaine_air = SousDomaine(nom="Qualité de l'Air", description="Réglementations sur la qualité de l'air", domaine=domaine_env)
        db.session.add(sous_domaine_air)
        db.session.commit()
        print("Sous-Domaine 'Qualité de l'Air' ajouté.")
    else:
        print("Sous-Domaine 'Qualité de l'Air' existe déjà.")

    # Créer un Thème
    theme_dechets = Theme.query.filter_by(nom="Gestion des Déchets").first()
    if not theme_dechets:
        theme_dechets = Theme(nom="Gestion des Déchets", description="Réglementations relatives à la gestion des déchets")
        db.session.add(theme_dechets)
        db.session.commit()
        print("Thème 'Gestion des Déchets' ajouté.")
    else:
        print("Thème 'Gestion des Déchets' existe déjà.")

    # Créer une Réglementation
    reglementation_dechets = Reglementation.query.filter_by(titre="Loi sur la gestion des déchets").first()
    if not reglementation_dechets:
        reglementation_dechets = Reglementation(
            titre="Loi sur la gestion des déchets",
            type_texte="Loi",
            date_publication=datetime(2020, 1, 1).date(),
            source="Journal Officiel",
            langue="Fr",
            resume_exigences="Exigences relatives à la collecte et au traitement des déchets industriels.",
            theme=theme_dechets,
            sous_domaine=sous_domaine_air
        )
        db.session.add(reglementation_dechets)
        db.session.commit()
        print("Réglementation 'Loi sur la gestion des déchets' ajoutée.")

        reg_sect_link_exists = db.session.query(ReglementationSecteur).filter_by(
            reglementation_id=reglementation_dechets.id,
            secteur_id=secteur.id
        ).first()
        if not reg_sect_link_exists:
            new_link = ReglementationSecteur(
                reglementation_id=reglementation_dechets.id,
                secteur_id=secteur.id
            )
            db.session.add(new_link)
            db.session.commit()
            print(f"Réglementation '{reglementation_dechets.titre}' liée au secteur '{secteur.nom}'.")
    else:
        print("Réglementation 'Loi sur la gestion des déchets' existe déjà.")

    # Créer un Article pour la Réglementation
    article_dechets = Article.query.filter_by(reglementation=reglementation_dechets, numero="Article 5").first()
    if not article_dechets:
        article_dechets = Article(
            reglementation=reglementation_dechets,
            numero="Article 5",
            titre="Déclaration des déchets dangereux",
            contenu="Toute entreprise produisant des déchets dangereux doit les déclarer annuellement."
        )
        db.session.add(article_dechets)
        db.session.commit()
        print("Article 'Article 5' ajouté.")
    else:
        print("Article 'Article 5' existe déjà.")

    # Appeler la méthode assign_reglementations pour l'entreprise
    # *** FIX: Querying the EntrepriseReglementation model directly ***
    # Before calling assign_reglementations, ensure the specific link doesn't already exist
    entreprise_reg_link_check = EntrepriseReglementation.query.filter_by(
        entreprise_id=entreprise.id, 
        reglementation_id=reglementation_dechets.id
    ).first()

    if not entreprise_reg_link_check:
        print(f"Assignation des réglementations pour {entreprise.nom}...")
        entreprise.assign_reglementations()
        print("Assignation terminée.")
    else:
        print(f"Réglementations déjà assignées pour {entreprise.nom}.")

    # Vérifier l'évaluation de l'article pour l'entreprise
    evaluation = Evaluation.query.filter_by(entreprise=entreprise, article=article_dechets).first()
    if evaluation:
        print(f"Évaluation pour '{article_dechets.titre}' de '{entreprise.nom}': Applicable={evaluation.applicable.value}, Conforme={evaluation.conforme.value}")
        if evaluation.conforme == ConformeEnum.NON_EVALUE:
            print("Mise à jour de l'évaluation...")
            evaluation.applicable = ApplicableEnum.OUI
            evaluation.conforme = ConformeEnum.NON_CONFORME # Exemple: initialement non conforme
            db.session.commit()
            print("Évaluation mise à jour.")
            
            entreprise_reg = EntrepriseReglementation.query.filter_by(entreprise=entreprise, reglementation=reglementation_dechets).first()
            if entreprise_reg:
                entreprise_reg.mettre_a_jour_score()
                print(f"Score de conformité pour '{reglementation_dechets.titre}' mis à jour: {entreprise_reg.score}%")
    else:
        print("Aucune évaluation trouvée pour l'article et l'entreprise spécifiés.")

    db.session.close() # Good practice to close the session
    print("Script d'initialisation terminé.")