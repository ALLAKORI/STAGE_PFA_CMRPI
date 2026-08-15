"""Persistance SQLite des analyses et des alertes du MVP."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = ROOT_DIR / "data" / "threats.db"


@contextmanager
def connect(db_path: str | Path = DEFAULT_DB_PATH):
    """Ouvre une connexion transactionnelle et garantit sa fermeture."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                date_analyse TEXT NOT NULL,
                prediction INTEGER NOT NULL,
                verdict_ml TEXT NOT NULL,
                probabilite REAL NOT NULL,
                niveau_risque TEXT NOT NULL,
                urlhaus_match INTEGER NOT NULL DEFAULT 0,
                source_detection TEXT NOT NULL,
                raisons_json TEXT NOT NULL DEFAULT '[]',
                alerte_envoyee INTEGER NOT NULL DEFAULT 0,
                erreur_alerte TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_date ON analyses(date_analyse)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_url ON analyses(url)"
        )


def save_analysis(result: dict[str, Any], db_path: str | Path = DEFAULT_DB_PATH) -> int:
    init_database(db_path)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses (
                url, date_analyse, prediction, verdict_ml, probabilite,
                niveau_risque, urlhaus_match, source_detection, raisons_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["url"],
                result["date_analyse"],
                int(result["prediction"]),
                result["verdict_ml"],
                float(result["probabilite_phishing"]),
                result["niveau_risque"],
                int(result["urlhaus_match"]),
                result["source_detection"],
                json.dumps(result.get("raisons", []), ensure_ascii=False),
            ),
        )
        return int(cursor.lastrowid)


def update_alert_status(
    analysis_id: int,
    sent: bool,
    error: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE analyses SET alerte_envoyee = ?, erreur_alerte = ? WHERE id = ?",
            (int(sent), error, analysis_id),
        )


def recent_alert_exists(
    url: str,
    minutes: int = 60,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> bool:
    threshold = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT 1 FROM analyses
            WHERE url = ? AND alerte_envoyee = 1 AND date_analyse >= ?
            LIMIT 1
            """,
            (url, threshold),
        ).fetchone()
    return row is not None


def get_analyses(
    limit: int = 500,
    risk: str | None = None,
    verdict: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict[str, Any]]:
    init_database(db_path)
    clauses: list[str] = []
    parameters: list[Any] = []
    if risk and risk != "Tous":
        clauses.append("niveau_risque = ?")
        parameters.append(risk)
    if verdict and verdict != "Tous":
        clauses.append("verdict_ml = ?")
        parameters.append(verdict)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    parameters.append(max(1, min(int(limit), 5000)))
    with connect(db_path) as connection:
        rows = connection.execute(
            f"SELECT * FROM analyses {where} ORDER BY date_analyse DESC LIMIT ?",
            parameters,
        ).fetchall()
    return [dict(row) for row in rows]


def get_dashboard_stats(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, int]:
    init_database(db_path)
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN niveau_risque = 'Faible' THEN 1 ELSE 0 END) AS faibles,
                SUM(CASE WHEN niveau_risque != 'Faible' THEN 1 ELSE 0 END) AS menaces,
                SUM(alerte_envoyee) AS alertes
            FROM analyses
            """
        ).fetchone()
    return {key: int(row[key] or 0) for key in row.keys()}
