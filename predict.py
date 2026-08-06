import joblib
import pandas as pd

from feature_engineering import extract_features


# Charger le modèle et le scaler
model = joblib.load("logistic_regression_model.pkl")
scaler = joblib.load("scaler.pkl")


# Demander une URL
url = input("Entrez une URL à analyser : ").strip()


# Extraire les caractéristiques
features = extract_features(url)

features_df = pd.DataFrame([features])


# Appliquer la même standardisation que pendant l'entraînement
features_scaled = scaler.transform(features_df)


# Faire la prédiction
prediction = model.predict(features_scaled)[0]
probabilities = model.predict_proba(features_scaled)[0]


# Dans PhiUSIIL :
# 0 = phishing
# 1 = légitime
if prediction == 1:
    result = "URL légitime"
    confidence = probabilities[1]
else:
    result = "URL phishing"
    confidence = probabilities[0]


print("\nRésultat :", result)
print(f"Confiance : {confidence * 100:.2f} %")