"""Extension optionnelle de réputation IP via AbuseIPDB."""

from __future__ import annotations

import ipaddress
import os
from typing import Any

import requests
from dotenv import load_dotenv


API_URL = "https://api.abuseipdb.com/api/v2/check"


def analyze_ip(address: str) -> dict[str, Any]:
    """Interroge AbuseIPDB seulement lorsqu'une clé est configurée."""
    try:
        ip = str(ipaddress.ip_address(address.strip()))
    except ValueError as exc:
        raise ValueError("Adresse IP invalide.") from exc

    load_dotenv()
    api_key = os.getenv("ABUSEIPDB_API_KEY", "").strip()
    if not api_key:
        return {
            "configured": False,
            "ip": ip,
            "message": "Extension AbuseIPDB non configurée.",
        }

    try:
        response = requests.get(
            API_URL,
            headers={"Key": api_key, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
    except (requests.RequestException, ValueError) as exc:
        return {
            "configured": True,
            "available": False,
            "ip": ip,
            "message": f"Service AbuseIPDB indisponible ({type(exc).__name__}).",
        }

    return {
        "configured": True,
        "available": True,
        "ip": ip,
        "abuse_confidence_score": data.get("abuseConfidenceScore"),
        "total_reports": data.get("totalReports"),
        "country_code": data.get("countryCode"),
        "last_reported_at": data.get("lastReportedAt"),
        "isp": data.get("isp"),
        "usage_type": data.get("usageType"),
    }

