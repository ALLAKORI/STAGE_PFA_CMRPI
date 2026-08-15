# Jalon 3 — Travail restant

Cette liste distingue le **nécessaire pour terminer le PFA** des extensions
facultatives. Le cœur technique du MVP URL est déjà développé et testé.

## Priorité 1 — Valider l'alerte e-mail réelle

- [ ] Choisir un compte SMTP de démonstration, idéalement dédié au projet.
- [ ] Activer la double authentification si Gmail est utilisé.
- [ ] Générer un mot de passe d'application ; ne jamais utiliser le mot de passe normal.
- [ ] Copier `.env.example` vers `.env`.
- [ ] Renseigner `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_SENDER`,
      `SMTP_PASSWORD` et `ALERT_RECIPIENT`.
- [ ] Définir `ALERT_ENABLED=true`.
- [ ] Redémarrer Streamlit et vérifier « Configuration SMTP prête ».
- [ ] Analyser une URL URLHaus marquée `offline`, uniquement par copier-coller.
- [ ] Confirmer la réception de l'e-mail dans la boîte ou le dossier spam.
- [ ] Vérifier dans l'historique que `alerte_envoyee = 1`.
- [ ] Faire une capture d'écran sans afficher l'adresse privée ni le secret.

Exemple Gmail :

```env
ALERT_ENABLED=true
ALERT_MIN_RISK=Élevé
ALERT_DEDUP_MINUTES=60
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_SENDER=adresse_demo@gmail.com
SMTP_PASSWORD=mot_de_passe_application
ALERT_RECIPIENT=destinataire@gmail.com
```

Le fichier `.env` ne doit jamais être ajouté à Git.

## Priorité 2 — Recette fonctionnelle et démonstration

- [ ] Vérifier les sept pages de l'interface sur l'ordinateur de démonstration.
- [ ] Tester une URL légitime connue, par exemple `https://www.google.com`.
- [ ] Tester une URL factice suspecte utilisant `example.com`.
- [ ] Tester une URL réellement répertoriée dans la base locale URLHaus et
      marquée `offline` ; ne jamais l'ouvrir.
- [ ] Tester un CSV contenant plusieurs URL.
- [ ] Vérifier le téléchargement du CSV de résultats.
- [ ] Vérifier les statistiques du tableau de bord et les filtres de l'historique.
- [ ] Vérifier les trois fiches réflexes.
- [ ] Tester l'anti-doublon des alertes.
- [ ] Rejouer `python -m unittest discover -s tests -v`.

## Priorité 3 — Rapport final de stage

- [ ] Rédiger le rapport final demandé dans la fiche de cadrage.
- [ ] Reprendre brièvement les Jalons 1 et 2 sans recopier leurs rapports.
- [ ] Décrire l'architecture du Jalon 3 et la chaîne de bout en bout.
- [ ] Expliquer le rôle distinct d'URLHaus et du Machine Learning.
- [ ] Présenter SQLite, Streamlit, SMTP et les fiches réflexes.
- [ ] Ajouter les résultats des tests et des captures lisibles.
- [ ] Expliquer les faux positifs, faux négatifs et limites du score ML.
- [ ] Ajouter une section sécurité : secrets, validation, URL non ouvertes.
- [ ] Ajouter les perspectives : Gmail/Outlook, AbuseIPDB et déploiement.
- [ ] Relire les noms : **ALLADO Kossi Richard** et
      **ADJEVI Kodjo Marius-Ben**.
- [ ] Compiler et contrôler visuellement le PDF final.

## Priorité 4 — Présentation et soutenance

- [ ] Préparer une présentation courte avec problème, objectifs, architecture,
      démonstration, résultats, limites et perspectives.
- [ ] Préparer un scénario de démonstration de 5 à 7 minutes.
- [ ] Répartir clairement les parties entre les deux stagiaires.
- [ ] Prévoir des captures ou une vidéo de secours en cas de panne réseau/SMTP.
- [ ] Savoir expliquer `0 = phishing`, `1 = légitime`.
- [ ] Savoir expliquer accuracy, précision, rappel, F1-score et matrice de confusion.
- [ ] Savoir expliquer pourquoi une absence dans URLHaus ne prouve pas qu'une URL est sûre.
- [ ] Savoir justifier le choix de la régression logistique et de Streamlit.

## Priorité 5 — Finalisation GitHub

- [ ] Vérifier qu'aucun `.env`, mot de passe, adresse privée ou base SQLite
      opérationnelle n'est suivi par Git.
- [ ] Ajouter au README les captures finales utiles, sans données sensibles.
- [ ] Vérifier les commandes d'installation sur une machine propre ou dans un
      nouvel environnement virtuel.
- [ ] Marquer une version finale ou créer une release après validation de l'encadrant.

## Extensions facultatives — après le livrable principal

- [ ] Configurer et tester une clé AbuseIPDB de démonstration.
- [ ] Programmer automatiquement `Download_urls.py` avec le Planificateur de tâches.
- [ ] Étudier un déploiement Streamlit accessible à une PME.
- [ ] Étudier Gmail/Outlook automatiques avec consentement et analyse de confidentialité.
- [ ] Ajouter éventuellement Telegram après validation de l'encadrant.

Ces extensions ne doivent pas retarder le prototype URL, l'alerte SMTP, le
rapport et la présentation finale.

