import joblib
import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# 1. Charger le dataset contenant les features
DATASET_PATH = Path("data/processed/dataset_features.csv")
MODELS_DIR = Path("models")

data = pd.read_csv(DATASET_PATH)


# 2. Séparer les caractéristiques et le label
X = data.drop(columns=["label"])
y = data["label"]


# 3. Séparer les données d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)


# 4. Standardiser les caractéristiques
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# 5. Créer et entraîner le modèle
model = LogisticRegression(
    max_iter=1000,
    random_state=42,
)

model.fit(X_train_scaled, y_train)


# 6. Faire les prédictions
y_pred = model.predict(X_test_scaled)


# 7. Afficher les résultats
# Dans PhiUSIIL : 0 = phishing et 1 = légitime.
# Le phishing est la classe prioritaire à détecter.
PHISHING_LABEL = 0

print("Accuracy :", accuracy_score(y_test, y_pred))
print(
    "Precision phishing :",
    precision_score(
        y_test,
        y_pred,
        pos_label=PHISHING_LABEL,
        zero_division=0,
    ),
)
print(
    "Recall phishing :",
    recall_score(
        y_test,
        y_pred,
        pos_label=PHISHING_LABEL,
        zero_division=0,
    ),
)
print(
    "F1-score phishing :",
    f1_score(
        y_test,
        y_pred,
        pos_label=PHISHING_LABEL,
        zero_division=0,
    ),
)

print("\nMatrice de confusion :")
print(confusion_matrix(y_test, y_pred, labels=[0, 1]))

print("\nRapport de classification :")
print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["phishing", "legitimate"],
        zero_division=0,
    )
)


# 8. Sauvegarder le modèle et le scaler
MODELS_DIR.mkdir(parents=True, exist_ok=True)

model_path = MODELS_DIR / "logistic_regression_model.pkl"
scaler_path = MODELS_DIR / "scaler.pkl"

joblib.dump(model, model_path)
joblib.dump(scaler, scaler_path)

print(f"\nModèle sauvegardé dans {model_path}")
print(f"Scaler sauvegardé dans {scaler_path}")

from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt

ConfusionMatrixDisplay.from_estimator(
    model,
    X_test_scaled,
    y_test,
)

plt.show()
