import joblib
import pandas as pd

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
data = pd.read_csv("dataset_features.csv")


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
print("Accuracy :", accuracy_score(y_test, y_pred))
print("Precision :", precision_score(y_test, y_pred))
print("Recall :", recall_score(y_test, y_pred))
print("F1-score :", f1_score(y_test, y_pred))

print("\nMatrice de confusion :")
print(confusion_matrix(y_test, y_pred))

print("\nRapport de classification :")
print(classification_report(y_test, y_pred))


# 8. Sauvegarder le modèle et le scaler
joblib.dump(model, "logistic_regression_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("\nModèle sauvegardé dans logistic_regression_model.pkl")
print("Scaler sauvegardé dans scaler.pkl")

from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt

ConfusionMatrixDisplay.from_estimator(
    model,
    X_test_scaled,
    y_test,
)

plt.show()