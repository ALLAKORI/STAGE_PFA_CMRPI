# Détection d’URL de phishing

Projet de classification d’URL réalisé dans le cadre du stage PFA au CMRPI.
Il extrait des caractéristiques d’une URL, entraîne un modèle de régression
logistique et permet d’estimer si une URL est légitime ou liée au phishing.

## Organisation

- `feature_engineering.py` : extraction des caractéristiques d’une URL.
- `train_model.py` : entraînement et évaluation du modèle.
- `predict.py` : prédiction interactive sur une URL.
- `Download_urls.py` : collecte de données récentes depuis URLhaus.
- `prepare_phishing_url_features.ipynb` : préparation et extraction des caractéristiques du jeu de données d'URL.
- `data/raw/` : jeu de données PhiUSIIL original.
- `data/processed/` : caractéristiques préparées pour l’entraînement.
- `data/collected/urlhaus/` : export URLhaus courant et historique des collectes.
- `models/` : modèle de régression logistique et scaler sauvegardés.
- `docs/` : document de cadrage, évaluation du modèle et rapport du Jalon 2.

## Installation

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
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

Les fichiers créés sont conservés dans `data/collected/urlhaus/`. Le modèle
et le scaler entraînés sont enregistrés dans `models/`.

## Avertissement

Les fichiers de données contiennent des URL potentiellement malveillantes.
Ne les ouvrez pas dans un navigateur et ne téléchargez pas leur contenu.
