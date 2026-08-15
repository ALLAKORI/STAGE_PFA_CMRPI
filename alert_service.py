"""Envoi d'alertes SMTP configurable, sans secret dans le code."""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

from dotenv import load_dotenv

from database import recent_alert_exists


LOGGER = logging.getLogger(__name__)
RISK_ORDER = {"Faible": 0, "Moyen": 1, "Élevé": 2, "Critique": 3}


@dataclass(frozen=True, slots=True)
class AlertConfig:
    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_security: str
    sender: str
    password: str
    recipient: str
    minimum_risk: str
    deduplication_minutes: int


def _as_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "oui", "on"}


def load_alert_config() -> AlertConfig:
    load_dotenv()
    return AlertConfig(
        enabled=_as_bool(os.getenv("ALERT_ENABLED", "false")),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_security=os.getenv("SMTP_SECURITY", "starttls").strip().lower(),
        sender=os.getenv("SMTP_SENDER", "").strip(),
        password=os.getenv("SMTP_PASSWORD", ""),
        recipient=os.getenv("ALERT_RECIPIENT", "").strip(),
        minimum_risk=os.getenv("ALERT_MIN_RISK", "Élevé").strip(),
        deduplication_minutes=max(1, int(os.getenv("ALERT_DEDUP_MINUTES", "60"))),
    )


def config_status(config: AlertConfig | None = None) -> tuple[bool, str]:
    config = config or load_alert_config()
    if not config.enabled:
        return False, "Alertes désactivées."
    if config.minimum_risk not in RISK_ORDER:
        return False, "Seuil d'alerte invalide."
    missing = [
        name
        for name, value in {
            "SMTP_HOST": config.smtp_host,
            "SMTP_SENDER": config.sender,
            "SMTP_PASSWORD": config.password,
            "ALERT_RECIPIENT": config.recipient,
        }.items()
        if not value
    ]
    if missing:
        return False, "Configuration incomplète : " + ", ".join(missing)
    return True, "Configuration SMTP prête."


def should_send_alert(result: dict, config: AlertConfig | None = None) -> bool:
    config = config or load_alert_config()
    ready, _ = config_status(config)
    return ready and RISK_ORDER.get(result["niveau_risque"], -1) >= RISK_ORDER[config.minimum_risk]


def build_alert_message(result: dict, config: AlertConfig) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = f"[ALERTE CYBER] URL à risque {result['niveau_risque']}"
    message["From"] = config.sender
    message["To"] = config.recipient
    urlhaus = "Oui" if result["urlhaus_match"] else "Non"
    recommendations = "\n".join(f"- {item}" for item in result["recommandations"])
    message.set_content(
        f"""Une URL dangereuse ou suspecte a été détectée.

URL : {result['url']}
Date UTC : {result['date_analyse']}
Niveau de risque : {result['niveau_risque']}
Probabilité estimée de phishing : {result['probabilite_phishing'] * 100:.2f} %
Présence dans URLHaus : {urlhaus}
Source : {result['source_detection']}

Actions recommandées :
{recommendations}

Cette estimation automatise une première analyse et ne constitue pas une certitude absolue.
"""
    )
    return message


def send_alert(result: dict, config: AlertConfig | None = None) -> tuple[bool, str]:
    """Envoie une alerte si nécessaire ; toute erreur est capturée et journalisée."""
    config = config or load_alert_config()
    ready, status = config_status(config)
    if not ready:
        return False, status
    if not should_send_alert(result, config):
        return False, "Niveau inférieur au seuil configuré."
    if recent_alert_exists(result["url"], config.deduplication_minutes):
        return False, "Alerte récente déjà envoyée pour cette URL."

    message = build_alert_message(result, config)
    try:
        if config.smtp_security == "ssl":
            with smtplib.SMTP_SSL(
                config.smtp_host,
                config.smtp_port,
                timeout=15,
                context=ssl.create_default_context(),
            ) as server:
                server.login(config.sender, config.password)
                server.send_message(message)
        else:
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=15) as server:
                server.ehlo()
                if config.smtp_security == "starttls":
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(config.sender, config.password)
                server.send_message(message)
        return True, "Alerte envoyée."
    except (OSError, smtplib.SMTPException) as exc:
        LOGGER.error("Échec de l'alerte SMTP : %s", type(exc).__name__)
        return False, f"Échec SMTP ({type(exc).__name__}). L'analyse reste enregistrée."

