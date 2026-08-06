# Évaluation du modèle de détection de phishing

## Objectif

Le modèle de régression logistique distingue les URL de phishing des URL légitimes à partir des caractéristiques numériques extraites par `feature_engineering.py`.

Les étiquettes du jeu PhiUSIIL sont :

- `0` : phishing ;
- `1` : légitime.

La détection du phishing est donc la métrique prioritaire.

## Protocole d'évaluation

- Jeu de données : `data/raw/PhiUSIIL_Phishing_URL_Dataset.csv`, transformé en `data/processed/dataset_features.csv`.
- Observations : 235 795 URL, dont 100 945 URL de phishing et 134 850 URL légitimes.
- Variables : 21 caractéristiques structurelles d'URL.
- Modèle : régression logistique de scikit-learn.
- Séparation : 80 % entraînement et 20 % test, avec `stratify=y` et `random_state=42`.
- Normalisation : `StandardScaler` est ajusté exclusivement sur les données d'entraînement, puis appliqué au jeu de test.

## Résultats du jeu de test

Résultats produits par `python train_model.py` :

| Mesure | Valeur |
|---|---:|
| Accuracy globale | 99,32 % |
| Precision phishing | 99,91 % |
| Recall phishing | 98,49 % |
| F1-score phishing | 99,20 % |

Matrice de confusion, avec les lignes correspondant aux classes réelles et les colonnes aux prédictions :

| Réel / prédit | Phishing | Légitime |
|---|---:|---:|
| Phishing | 19 885 | 304 |
| Légitime | 18 | 26 952 |

Le modèle détecte 19 885 URL de phishing sur 20 189. Les 304 URL de phishing prédites comme légitimes sont les faux négatifs : elles constituent l'erreur la plus importante à surveiller dans le cadre d'un détecteur de menaces. Les 18 URL légitimes prédites comme phishing sont les faux positifs.

## Limite connue de l'évaluation

Les caractéristiques sont volontairement simples et plusieurs URL différentes peuvent produire le même vecteur de caractéristiques. Une évaluation complémentaire avec une séparation groupée et stratifiée par vecteur de caractéristiques a obtenu 99,23 % d'accuracy. Ce résultat proche confirme le bon comportement global du modèle, tout en évitant qu'un même vecteur apparaisse dans les données d'entraînement et de test.

## Reproduction

Depuis la racine du dépôt :

```bash
python train_model.py
```

Le script affiche les mesures ci-dessus et enregistre `models/logistic_regression_model.pkl` ainsi que `models/scaler.pkl`.
