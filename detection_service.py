"""Service central d'analyse d'URL (Threat Intelligence + Machine Learning)."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import joblib
import pandas as pd

from feature_engineering import extract_features, normalize_url


ROOT_DIR = Path(__file__).resolve().parent
MODEL_PATH = ROOT_DIR / "models" / "logistic_regression_model.pkl"
SCALER_PATH = ROOT_DIR / "models" / "scaler.pkl"
URLHAUS_PATH = ROOT_DIR / "data" / "collected" / "urlhaus" / "current_urls.csv"
URLHAUS_STATE_PATH = ROOT_DIR / "data" / "collected" / "urlhaus" / ".urlhaus_state.json"

PHISHING_LABEL = 0
LEGITIMATE_LABEL = 1

_resource_lock = threading.Lock()
_model: Any | None = None
_scaler: Any | None = None
_urlhaus_cache: dict[str, dict[str, Any]] | None = None
_urlhaus_mtime: float | None = None


@dataclass(slots=True)
class AnalysisResult:
    url: str
    normalized_url: str
    date_analyse: str
    prediction: int
    verdict_ml: str
    probabilite_phishing: float
    confiance_prediction: float
    urlhaus_match: bool
    urlhaus_info: dict[str, Any]
    niveau_risque: str
    source_detection: str
    raisons: list[str]
    recommandations: list[str]
    alerte_requise: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_url(value: str) -> str:
    """Valide et normalise une URL HTTP(S) sans effectuer de requête réseau."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Veuillez saisir une URL.")
    if len(value.strip()) > 4096:
        raise ValueError("L'URL est trop longue (maximum : 4096 caractères).")

    normalized = normalize_url(value)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Seules les URL HTTP et HTTPS sont acceptées.")
    if not parsed.hostname or any(character.isspace() for character in parsed.hostname):
        raise ValueError("Le nom d'hôte de l'URL est invalide.")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Le port de l'URL est invalide.") from exc
    return normalized


def _load_ml_resources() -> tuple[Any, Any]:
    global _model, _scaler
    if _model is None or _scaler is None:
        with _resource_lock:
            if _model is None or _scaler is None:
                missing = [str(path) for path in (MODEL_PATH, SCALER_PATH) if not path.exists()]
                if missing:
                    raise FileNotFoundError(
                        "Artefact(s) ML introuvable(s) : " + ", ".join(missing)
                    )
                _model = joblib.load(MODEL_PATH)
                _scaler = joblib.load(SCALER_PATH)
                if set(_model.classes_) != {PHISHING_LABEL, LEGITIMATE_LABEL}:
                    raise ValueError("Convention de labels inattendue dans le modèle.")
    return _model, _scaler


def _url_variants(url: str) -> set[str]:
    stripped = url.strip()
    normalized = normalize_url(stripped)
    return {stripped, stripped.rstrip("/"), normalized, normalized.rstrip("/")}


def _load_urlhaus_index() -> dict[str, dict[str, Any]]:
    """Charge la base locale à nouveau uniquement lorsque son fichier change."""
    global _urlhaus_cache, _urlhaus_mtime
    if not URLHAUS_PATH.exists():
        _urlhaus_cache, _urlhaus_mtime = {}, None
        return _urlhaus_cache

    mtime = URLHAUS_PATH.stat().st_mtime
    if _urlhaus_cache is not None and _urlhaus_mtime == mtime:
        return _urlhaus_cache

    with _resource_lock:
        if _urlhaus_cache is not None and _urlhaus_mtime == mtime:
            return _urlhaus_cache
        try:
            frame = pd.read_csv(URLHAUS_PATH, dtype=str).fillna("")
        except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
            _urlhaus_cache, _urlhaus_mtime = {}, mtime
            return _urlhaus_cache

        index: dict[str, dict[str, Any]] = {}
        if "url" in frame.columns:
            for row in frame.to_dict(orient="records"):
                for variant in _url_variants(str(row["url"])):
                    index[variant] = row
        _urlhaus_cache, _urlhaus_mtime = index, mtime
        return index


def get_urlhaus_last_update() -> str | None:
    """Retourne la date déclarée dans l'état URLHaus, sinon la date du CSV."""
    if URLHAUS_STATE_PATH.exists():
        try:
            state = json.loads(URLHAUS_STATE_PATH.read_text(encoding="utf-8"))
            if state.get("derniere_maj"):
                return str(state["derniere_maj"])
        except (OSError, json.JSONDecodeError):
            pass
    if URLHAUS_PATH.exists():
        return datetime.fromtimestamp(
            URLHAUS_PATH.stat().st_mtime, tz=timezone.utc
        ).isoformat()
    return None


def _reasons(features: dict[str, float], urlhaus_match: bool) -> list[str]:
    reasons: list[str] = []
    if urlhaus_match:
        reasons.append("Correspondance trouvée dans la base locale URLHaus.")
    if features["has_ip_address"]:
        reasons.append("Une adresse IP est utilisée comme nom d'hôte.")
    if not features["uses_https"]:
        reasons.append("L'URL n'utilise pas HTTPS.")
    if features["suspicious_keyword_count"]:
        reasons.append(
            f"{int(features['suspicious_keyword_count'])} mot(s)-clé(s) suspect(s) détecté(s)."
        )
    if features["number_of_subdomains"] >= 3:
        reasons.append("Le nom d'hôte contient de nombreux sous-domaines.")
    if features["url_length"] >= 100:
        reasons.append("L'URL est particulièrement longue.")
    return reasons or ["Aucun indicateur lexical simple particulièrement marqué."]


def _risk_level(phishing_probability: float, urlhaus_match: bool) -> str:
    if urlhaus_match:
        return "Critique"
    if phishing_probability >= 0.85:
        return "Élevé"
    if phishing_probability >= 0.55:
        return "Moyen"
    return "Faible"


def _recommendations(risk: str) -> list[str]:
    if risk in {"Critique", "Élevé"}:
        return [
            "Ne cliquez pas sur le lien et ne saisissez aucune information.",
            "Signalez immédiatement l'URL au responsable informatique ou sécurité.",
            "Si le lien a déjà été ouvert, appliquez la fiche réflexe correspondante.",
        ]
    if risk == "Moyen":
        return [
            "Vérifiez le domaine par un canal officiel avant toute action.",
            "Demandez l'avis du responsable informatique en cas de doute.",
        ]
    return [
        "Le résultat est rassurant mais ne constitue pas une garantie absolue.",
        "Vérifiez toujours le domaine et le contexte du message.",
    ]


def analyze_url(url: str) -> dict[str, Any]:
    """Analyse une URL avec URLHaus et le modèle existant, sans l'ouvrir."""
    normalized = validate_url(url)
    model, scaler = _load_ml_resources()
    features = extract_features(url.strip())

    feature_order = list(getattr(scaler, "feature_names_in_", features.keys()))
    if set(feature_order) != set(features):
        raise ValueError("Les caractéristiques extraites ne correspondent pas au scaler.")
    features_frame = pd.DataFrame([[features[name] for name in feature_order]], columns=feature_order)
    scaled = scaler.transform(features_frame)
    prediction = int(model.predict(scaled)[0])
    probabilities = model.predict_proba(scaled)[0]
    class_probabilities = {
        int(label): float(probability)
        for label, probability in zip(model.classes_, probabilities)
    }
    phishing_probability = class_probabilities[PHISHING_LABEL]
    confidence = class_probabilities[prediction]

    urlhaus_info: dict[str, Any] = {}
    index = _load_urlhaus_index()
    for variant in _url_variants(url):
        if variant in index:
            urlhaus_info = index[variant]
            break
    urlhaus_match = bool(urlhaus_info)
    risk = _risk_level(phishing_probability, urlhaus_match)
    ml_verdict = "Phishing probable" if prediction == PHISHING_LABEL else "Probablement légitime"
    source = "URLHaus + Machine Learning" if urlhaus_match else "Machine Learning"

    result = AnalysisResult(
        url=url.strip(),
        normalized_url=normalized,
        date_analyse=datetime.now(timezone.utc).isoformat(),
        prediction=prediction,
        verdict_ml=ml_verdict,
        probabilite_phishing=phishing_probability,
        confiance_prediction=confidence,
        urlhaus_match=urlhaus_match,
        urlhaus_info=urlhaus_info,
        niveau_risque=risk,
        source_detection=source,
        raisons=_reasons(features, urlhaus_match),
        recommandations=_recommendations(risk),
        alerte_requise=risk in {"Élevé", "Critique"},
    )
    return result.to_dict()


def analyze_urls(urls: list[str]) -> list[dict[str, Any]]:
    """Analyse une liste en réutilisant les ressources chargées en mémoire."""
    return [analyze_url(url) for url in urls]


def reset_resource_cache() -> None:
    """Réinitialise les caches ; utile pour les tests et mises à jour."""
    global _model, _scaler, _urlhaus_cache, _urlhaus_mtime
    _model = _scaler = _urlhaus_cache = _urlhaus_mtime = None

