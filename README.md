# Détection d’URL de phishing

Projet de classification d’URL réalisé dans le cadre du stage PFA au CMRPI.
Il extrait des caractéristiques d’une URL, entraîne un modèle de régression
logistique et permet d’estimer si une URL est légitime ou liée au phishing.

## Contenu

- `feature_engineering.py` : extraction des caractéristiques d’une URL.
- `train_model.py` : entraînement et évaluation du modèle.
- `predict.py` : prédiction interactive sur une URL.
- `Download_urls.py` : collecte de données récentes depuis URLhaus.
- `jalon2.ipynb` : notebook d’exploration et de préparation.
- `dataset_features.csv` : caractéristiques utilisées pour l’entraînement.
- `PhiUSIIL_Phishing_URL_Dataset.csv` : jeu de données PhiUSIIL.
- `urls_malveillantes.csv` : export d’URL malveillantes.

## Installation

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Utilisation

Pour entraîner le modèle :

```powershell
python train_model.py
```

Pour analyser une URL :

```powershell
python predict.py
```

Pour mettre à jour la liste provenant d’URLhaus :

```powershell
python Download_urls.py
```

## Avertissement

Les fichiers de données contiennent des URL potentiellement malveillantes.
Ne les ouvrez pas dans un navigateur et ne téléchargez pas leur contenu.
