from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import alert_service
import database
import detection_service
from alert_service import AlertConfig


class DetectionTests(unittest.TestCase):
    def setUp(self):
        detection_service.reset_resource_cache()

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            detection_service.analyze_url("")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            detection_service.analyze_url("http://exa mple.com")

    def test_url_without_protocol(self):
        result = detection_service.analyze_url("example.com/login")
        self.assertEqual(result["normalized_url"], "http://example.com/login")
        self.assertIn(result["prediction"], [0, 1])

    def test_legitimate_known_url(self):
        result = detection_service.analyze_url("https://www.google.com")
        self.assertEqual(result["prediction"], 1)
        self.assertFalse(result["urlhaus_match"])

    def test_manifestly_suspicious_ip_url(self):
        result = detection_service.analyze_url(
            "http://192.0.2.10/secure-login/verify-account?password=confirm"
        )
        self.assertTrue(any("adresse IP" in reason for reason in result["raisons"]))
        self.assertTrue(any("mot(s)-clé(s)" in reason for reason in result["raisons"]))

    def test_urlhaus_present_and_absent(self):
        index = detection_service._load_urlhaus_index()
        if not index:
            self.skipTest("Base URLHaus locale vide ou indisponible")
        known_url = next(iter(index))
        known = detection_service.analyze_url(known_url)
        absent = detection_service.analyze_url("https://example.com/url-absente-du-jeu")
        self.assertTrue(known["urlhaus_match"])
        self.assertEqual(known["niveau_risque"], "Critique")
        self.assertFalse(absent["urlhaus_match"])

    def test_missing_model(self):
        detection_service.reset_resource_cache()
        with patch.object(detection_service, "MODEL_PATH", Path("missing-model.pkl")):
            with self.assertRaises(FileNotFoundError):
                detection_service.analyze_url("https://example.com")

    def test_urlhaus_unavailable(self):
        detection_service.reset_resource_cache()
        with patch.object(detection_service, "URLHAUS_PATH", Path("missing-urlhaus.csv")):
            result = detection_service.analyze_url("https://example.com")
        self.assertFalse(result["urlhaus_match"])

    def test_csv_input(self):
        frame = pd.DataFrame({"url": ["https://example.com", "example.org"]})
        results = [detection_service.analyze_url(url) for url in frame["url"]]
        self.assertEqual(len(results), 2)


class DatabaseTests(unittest.TestCase):
    def test_sqlite_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.db"
            result = detection_service.analyze_url("https://example.com")
            row_id = database.save_analysis(result, path)
            database.update_alert_status(row_id, True, db_path=path)
            rows = database.get_analyses(db_path=path)
            stats = database.get_dashboard_stats(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["alerte_envoyee"], 1)
            self.assertEqual(stats["total"], 1)


class AlertTests(unittest.TestCase):
    def config(self, enabled=True, host="smtp.invalid"):
        return AlertConfig(
            enabled=enabled,
            smtp_host=host,
            smtp_port=587,
            smtp_security="starttls",
            sender="sender@example.com",
            password="not-a-real-secret",
            recipient="security@example.com",
            minimum_risk="Élevé",
            deduplication_minutes=60,
        )

    def test_alert_disabled(self):
        result = detection_service.analyze_url("https://example.com")
        sent, message = alert_service.send_alert(result, self.config(enabled=False))
        self.assertFalse(sent)
        self.assertIn("désactivées", message)

    def test_smtp_failure_does_not_raise(self):
        result = detection_service.analyze_url("https://example.com")
        result["niveau_risque"] = "Critique"
        with patch.object(alert_service, "recent_alert_exists", return_value=False):
            with patch.object(alert_service.smtplib, "SMTP", side_effect=OSError("offline")):
                sent, message = alert_service.send_alert(result, self.config())
        self.assertFalse(sent)
        self.assertIn("Échec SMTP", message)


if __name__ == "__main__":
    unittest.main()

