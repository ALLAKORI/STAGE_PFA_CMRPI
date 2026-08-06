import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


URL_SOURCE = "https://urlhaus.abuse.ch/downloads/csv_recent/"

DOSSIER_URLHAUS = Path("data/collected/urlhaus")
FICHIER_SORTIE = DOSSIER_URLHAUS / "current_urls.csv"
FICHIER_ETAT = DOSSIER_URLHAUS / ".urlhaus_state.json"
DOSSIER_HISTORIQUE = DOSSIER_URLHAUS / "history"


COLONNES = [
    "id",
    "date_added",
    "url",
    "url_status",
    "last_online",
    "threat",
    "tags",
    "urlhaus_link",
    "reporter",
]

COLONNES_UTILES = [
    "date_added",
    "url",
    "url_status",
    "last_online",
    "threat",
]


def charger_etat():
    """
    Charge les informations de la dernière collecte.
    """
    if os.path.exists(FICHIER_ETAT):
        try:
            with open(FICHIER_ETAT, "r", encoding="utf-8") as fichier:
                return json.load(fichier)

        except (json.JSONDecodeError, OSError):
            return {}

    return {}


def sauvegarder_etat(etat):
    """
    Sauvegarde le hash et la date de la dernière mise à jour.
    """
    FICHIER_ETAT.parent.mkdir(parents=True, exist_ok=True)

    with open(FICHIER_ETAT, "w", encoding="utf-8") as fichier:
        json.dump(etat, fichier, indent=2)


def charger_base_locale():
    """
    Charge la base locale existante.
    """
    if os.path.exists(FICHIER_SORTIE):
        try:
            return pd.read_csv(FICHIER_SORTIE)

        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    return pd.DataFrame()


def sauvegarder_historique(nouvelles_urls):
    """
    Sauvegarde uniquement les nouvelles URL dans un fichier daté.
    """
    if nouvelles_urls.empty:
        return None

    DOSSIER_HISTORIQUE.mkdir(parents=True, exist_ok=True)

    date_collecte = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    fichier_historique = DOSSIER_HISTORIQUE / (
        f"collecte_urlhaus_{date_collecte}.csv"
    )

    nouvelles_urls.to_csv(
        fichier_historique,
        index=False,
        encoding="utf-8",
    )

    return fichier_historique


def main():
    print("[+] Vérification de la liste d'URL depuis URLHaus...")

    try:
        response = requests.get(URL_SOURCE, timeout=30)
        response.raise_for_status()

    except requests.RequestException as erreur:
        print(f"[-] Erreur de téléchargement : {erreur}")
        sys.exit(1)

    contenu_brut = response.text

    hash_actuel = hashlib.sha256(
        contenu_brut.encode("utf-8")
    ).hexdigest()

    etat = charger_etat()

    if etat.get("hash") == hash_actuel:
        print(
            "[=] Aucun changement détecté depuis "
            "le dernier téléchargement."
        )
        return

    lignes_utiles = [
        ligne
        for ligne in contenu_brut.splitlines()
        if ligne.strip() and not ligne.startswith("#")
    ]

    csv_propre = "\n".join(lignes_utiles)

    try:
        df = pd.read_csv(
            io.StringIO(csv_propre),
            names=COLONNES,
            sep=",",
        )

    except pd.errors.ParserError as erreur:
        print(f"[-] Erreur de lecture du CSV : {erreur}")
        sys.exit(1)

    df_final = df[COLONNES_UTILES].copy()

    df_final["url"] = (
        df_final["url"]
        .astype(str)
        .str.strip()
    )

    df_final = df_final.dropna(subset=["url"])

    df_final = df_final.drop_duplicates(
        subset=["url"],
        keep="first",
    )

    df_final["date_collecte"] = datetime.now(
        timezone.utc
    ).isoformat()

    base_locale = charger_base_locale()

    if base_locale.empty:
        nouvelles_urls = df_final.copy()

    else:
        urls_connues = set(
            base_locale["url"]
            .astype(str)
            .str.strip()
        )

        nouvelles_urls = df_final[
            ~df_final["url"].isin(urls_connues)
        ].copy()

    if nouvelles_urls.empty:
        print("[=] Aucune nouvelle URL à ajouter.")

        etat["hash"] = hash_actuel
        etat["derniere_maj"] = datetime.now(
            timezone.utc
        ).isoformat()

        sauvegarder_etat(etat)
        return

    if base_locale.empty:
        base_mise_a_jour = nouvelles_urls.copy()

    else:
        base_mise_a_jour = pd.concat(
            [base_locale, nouvelles_urls],
            ignore_index=True,
        )

    base_mise_a_jour = base_mise_a_jour.drop_duplicates(
        subset=["url"],
        keep="first",
    )

    base_mise_a_jour.to_csv(
        FICHIER_SORTIE,
        index=False,
        encoding="utf-8",
    )

    fichier_historique = sauvegarder_historique(
        nouvelles_urls
    )

    etat["hash"] = hash_actuel
    etat["derniere_maj"] = datetime.now(
        timezone.utc
    ).isoformat()

    sauvegarder_etat(etat)

    print(
        f"[+] Nouvelles URL ajoutées : "
        f"{len(nouvelles_urls)}"
    )

    print(
        f"[+] Taille totale de la base : "
        f"{len(base_mise_a_jour)}"
    )

    print(
        f"[+] Base locale mise à jour : "
        f"'{FICHIER_SORTIE}'"
    )

    if fichier_historique:
        print(
            f"[+] Historique créé : "
            f"'{fichier_historique}'"
        )

    print("\nPremières nouvelles URL :")
    print(nouvelles_urls.head())


if __name__ == "__main__":
    main()
