"""Interface Streamlit du MVP de détection et d'alerte pour PME."""

from __future__ import annotations

from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from alert_service import config_status, load_alert_config, send_alert
from database import (
    get_analyses,
    get_dashboard_stats,
    init_database,
    save_analysis,
    update_alert_status,
)
from detection_service import analyze_url, get_urlhaus_last_update
from ip_reputation_service import analyze_ip


ROOT_DIR = Path(__file__).resolve().parent
RISK_COLORS = {
    "Faible": "🟢",
    "Moyen": "🟠",
    "Élevé": "🔴",
    "Critique": "🚨",
}


st.set_page_config(
    page_title="CyberVeille PME",
    page_icon="🛡️",
    layout="wide",
)
init_database()


def inject_styles() -> None:
    """Applique une identité visuelle sobre sans modifier le pipeline métier."""
    st.markdown(
        """
        <style>
        :root {
            --navy-950: #07111f;
            --navy-900: #0b1728;
            --navy-800: #111f33;
            --border: rgba(148, 163, 184, .18);
            --text-soft: #9fb0c5;
            --cyan: #38bdf8;
            --green: #22c55e;
            --amber: #f59e0b;
            --red: #ef4444;
        }
        .stApp {
            background:
              radial-gradient(circle at 82% -10%, rgba(14,165,233,.12), transparent 30rem),
              linear-gradient(180deg, #07111f 0%, #091421 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1a2b 0%, #091321 100%);
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label {
            padding: .38rem .45rem;
            border-radius: .55rem;
        }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
            background: rgba(56,189,248,.08);
        }
        .block-container {
            max-width: 1280px;
            padding-top: 2.4rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3 { letter-spacing: -.025em; }
        h1 { font-size: 2.2rem !important; }
        .hero {
            padding: 1.45rem 1.6rem;
            border: 1px solid var(--border);
            border-radius: 1rem;
            background: linear-gradient(120deg, rgba(56,189,248,.10), rgba(15,23,42,.72));
            margin-bottom: 1.4rem;
        }
        .hero-kicker {
            color: var(--cyan); font-size: .75rem; font-weight: 800;
            letter-spacing: .12em; text-transform: uppercase; margin-bottom: .35rem;
        }
        .hero-title { font-size: 1.75rem; font-weight: 750; margin: 0; color: #f8fafc; }
        .hero-copy { color: var(--text-soft); margin: .35rem 0 0; max-width: 760px; }
        .brand {
            display:flex; align-items:center; gap:.75rem; padding:.35rem 0 1rem;
            border-bottom: 1px solid var(--border); margin-bottom:.8rem;
        }
        .brand-mark {
            width:2.3rem; height:2.3rem; display:grid; place-items:center;
            border-radius:.7rem; background:linear-gradient(135deg,#0ea5e9,#2563eb);
            box-shadow:0 8px 25px rgba(14,165,233,.25); font-size:1.2rem;
        }
        .brand-title { font-weight:800; color:#f8fafc; line-height:1.1; }
        .brand-subtitle { color:var(--text-soft); font-size:.72rem; margin-top:.15rem; }
        .metric-grid {
            display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.8rem;
            margin:.65rem 0 1.2rem;
        }
        .metric-card {
            min-width:0; padding:1rem 1.05rem; border-radius:.85rem;
            background:rgba(17,31,51,.86); border:1px solid var(--border);
            box-shadow:0 10px 30px rgba(0,0,0,.12);
        }
        .metric-label { color:var(--text-soft); font-size:.78rem; margin-bottom:.4rem; }
        .metric-value {
            color:#f8fafc; font-size:1.35rem; font-weight:760; line-height:1.2;
            overflow-wrap:anywhere;
        }
        .risk-banner {
            display:flex; justify-content:space-between; align-items:center; gap:1rem;
            border-radius:.9rem; padding:1rem 1.2rem; margin:1.25rem 0 .8rem;
            border:1px solid var(--risk-border); background:var(--risk-bg);
        }
        .risk-label { color:var(--text-soft); font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
        .risk-value { color:var(--risk-color); font-size:1.55rem; font-weight:850; }
        .section-card {
            padding:1.05rem 1.2rem; background:rgba(17,31,51,.60);
            border:1px solid var(--border); border-radius:.85rem; margin:.7rem 0;
        }
        .stTextInput input, .stNumberInput input, [data-baseweb="select"] > div {
            border-color:rgba(148,163,184,.25) !important; background:#101b2c !important;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius:.65rem; font-weight:700; min-height:2.7rem;
        }
        .stButton > button[kind="primary"] {
            background:linear-gradient(135deg,#0284c7,#2563eb); border:0;
            box-shadow:0 8px 20px rgba(2,132,199,.22);
        }
        [data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:.75rem; overflow:hidden; }
        @media (max-width: 900px) { .metric-grid { grid-template-columns:repeat(2,1fr); } }
        @media (max-width: 600px) { .metric-grid { grid-template-columns:1fr; } .block-container { padding-top:1.2rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">{escape(kicker)}</div>
          <div class="hero-title">{escape(title)}</div>
          <p class="hero-copy">{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_cards(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


inject_styles()


def persist_and_alert(result: dict) -> tuple[int, str]:
    analysis_id = save_analysis(result)
    if not result["alerte_requise"]:
        return analysis_id, "Aucune alerte requise pour ce niveau."
    sent, message = send_alert(result)
    update_alert_status(analysis_id, sent, None if sent else message)
    return analysis_id, message


def show_result(result: dict, alert_message: str | None = None) -> None:
    risk_styles = {
        "Faible": ("#22c55e", "rgba(34,197,94,.09)", "rgba(34,197,94,.28)"),
        "Moyen": ("#f59e0b", "rgba(245,158,11,.09)", "rgba(245,158,11,.28)"),
        "Élevé": ("#fb7185", "rgba(244,63,94,.10)", "rgba(244,63,94,.30)"),
        "Critique": ("#f87171", "rgba(239,68,68,.12)", "rgba(239,68,68,.34)"),
    }
    color, background, border = risk_styles[result["niveau_risque"]]
    st.markdown(
        f"""
        <div class="risk-banner" style="--risk-color:{color};--risk-bg:{background};--risk-border:{border}">
          <div><div class="risk-label">Décision finale</div>
          <div class="risk-value">{RISK_COLORS[result['niveau_risque']]} {escape(result['niveau_risque'].upper())}</div></div>
          <div style="color:#cbd5e1;font-size:.85rem">Analyse terminée</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_cards(
        [
            ("Verdict Machine Learning", result["verdict_ml"]),
            ("Probabilité de phishing", f"{result['probabilite_phishing'] * 100:.1f} %"),
            ("Threat Intelligence", "Répertoriée" if result["urlhaus_match"] else "Non répertoriée"),
            ("Source de détection", result["source_detection"]),
        ]
    )
    st.caption(
        "Le score est une estimation statistique. Une absence dans URLHaus ne prouve pas qu'une URL est sûre."
    )
    st.write("**URL analysée :**", result["url"])
    st.write("**Indicateurs observés :**")
    for reason in result["raisons"]:
        st.write(f"- {reason}")
    if result["urlhaus_info"]:
        with st.expander("Informations URLHaus"):
            st.json(result["urlhaus_info"])
    st.write("**Recommandations :**")
    for recommendation in result["recommandations"]:
        st.write(f"- {recommendation}")
    if alert_message:
        st.info(alert_message)


def dashboard_page() -> None:
    page_header(
        "Vue opérationnelle",
        "Tableau de bord de cybersécurité",
        "Suivez les analyses, les risques détectés et les alertes transmises à votre équipe.",
    )
    stats = get_dashboard_stats()
    metric_cards(
        [
            ("Analyses effectuées", str(stats["total"])),
            ("Risque faible", str(stats["faibles"])),
            ("Menaces / suspicions", str(stats["menaces"])),
            ("Alertes envoyées", str(stats["alertes"])),
        ]
    )
    update = get_urlhaus_last_update()
    st.caption(f"Dernière mise à jour locale URLHaus : {update or 'indisponible'}")
    recent = get_analyses(limit=10)
    st.subheader("Analyses récentes")
    if recent:
        st.dataframe(pd.DataFrame(recent), width="stretch", hide_index=True)
    else:
        st.info("Aucune analyse enregistrée pour le moment.")


def single_analysis_page() -> None:
    page_header(
        "Centre d'analyse",
        "Analyser un indicateur",
        "Collez une URL ou vérifiez une adresse IP sans visiter la ressource distante.",
    )
    indicator_type = st.radio("Type d'indicateur", ["URL", "Adresse IP"], horizontal=True)
    if indicator_type == "Adresse IP":
        address = st.text_input("Adresse IP", placeholder="8.8.8.8")
        if st.button("Vérifier l'adresse IP", type="primary"):
            try:
                result = analyze_ip(address)
                if not result.get("configured"):
                    st.warning(result["message"])
                elif not result.get("available"):
                    st.error(result["message"])
                else:
                    st.json(result)
            except ValueError as exc:
                st.error(str(exc))
        st.caption("Extension facultative : aucune donnée n'est inventée si AbuseIPDB n'est pas configuré.")
        return

    url = st.text_input("URL à analyser", placeholder="https://exemple.com/connexion")
    if st.button("Analyser l'URL", type="primary"):
        try:
            result = analyze_url(url)
            _, alert_message = persist_and_alert(result)
            show_result(result, alert_message)
        except (ValueError, FileNotFoundError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Une erreur inattendue empêche l'analyse. Consultez les journaux locaux.")


def bulk_analysis_page() -> None:
    page_header(
        "Traitement CSV",
        "Analyse en masse",
        "Évaluez jusqu'à 1 000 URL avec le même pipeline de détection et exportez les résultats.",
    )
    uploaded = st.file_uploader("Importer un fichier CSV", type=["csv"])
    if uploaded is None:
        st.info("Le fichier doit contenir une colonne nommée `url`.")
        return
    try:
        frame = pd.read_csv(uploaded)
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"CSV illisible : {exc}")
        return
    if "url" not in frame.columns:
        st.error("La colonne `url` est obligatoire.")
        return
    clean_urls = frame["url"].dropna().astype(str).str.strip()
    clean_urls = clean_urls[clean_urls.ne("")].head(1000)
    st.caption(f"{len(clean_urls)} URL prêtes (maximum par import : 1 000).")
    if st.button("Lancer l'analyse en masse", type="primary"):
        results: list[dict] = []
        progress = st.progress(0)
        for position, url in enumerate(clean_urls, start=1):
            try:
                result = analyze_url(url)
                _, alert_status = persist_and_alert(result)
                results.append(
                    {
                        "url": url,
                        "verdict": result["verdict_ml"],
                        "probabilite_phishing": round(result["probabilite_phishing"], 4),
                        "niveau_risque": result["niveau_risque"],
                        "urlhaus_match": result["urlhaus_match"],
                        "source": result["source_detection"],
                        "alerte": alert_status,
                        "erreur": "",
                    }
                )
            except Exception as exc:
                results.append({"url": url, "erreur": str(exc)})
            progress.progress(position / max(len(clean_urls), 1))
        output = pd.DataFrame(results)
        if "niveau_risque" in output.columns:
            valid = output[output["niveau_risque"].notna()]
            risk_counts = valid["niveau_risque"].value_counts()
        else:
            valid = pd.DataFrame()
            risk_counts = pd.Series(dtype=int)
        columns = st.columns(4)
        columns[0].metric("Total", len(output))
        columns[1].metric("Faibles", int(risk_counts.get("Faible", 0)))
        columns[2].metric(
            "Suspectes",
            int(risk_counts.get("Moyen", 0) + risk_counts.get("Élevé", 0)),
        )
        columns[3].metric("Critiques", int(risk_counts.get("Critique", 0)))
        st.dataframe(output, width="stretch", hide_index=True)
        st.download_button(
            "Télécharger les résultats CSV",
            output.to_csv(index=False).encode("utf-8-sig"),
            file_name="resultats_analyse_urls.csv",
            mime="text/csv",
        )


def history_page() -> None:
    page_header(
        "Traçabilité",
        "Historique des analyses",
        "Consultez les décisions précédentes et filtrez les incidents par niveau de risque.",
    )
    col1, col2, col3 = st.columns(3)
    risk = col1.selectbox("Risque", ["Tous", "Faible", "Moyen", "Élevé", "Critique"])
    verdict = col2.selectbox("Verdict", ["Tous", "Probablement légitime", "Phishing probable"])
    limit = col3.number_input("Nombre de lignes", 10, 5000, 500, 10)
    rows = get_analyses(limit=int(limit), risk=risk, verdict=verdict)
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Aucun résultat pour ces filtres.")


def alerts_page() -> None:
    page_header(
        "Notification sécurité",
        "État des alertes",
        "Contrôlez le seuil, le destinataire et la protection contre les notifications répétées.",
    )
    config = load_alert_config()
    ready, status = config_status(config)
    st.success(status) if ready else st.warning(status)
    st.write("**Activation :**", "Oui" if config.enabled else "Non")
    st.write("**Seuil minimum :**", config.minimum_risk)
    st.write("**Destinataire :**", config.recipient or "Non configuré")
    st.write("**Anti-doublon :**", f"{config.deduplication_minutes} minutes")
    st.caption("Les secrets ne sont jamais affichés. Modifiez `.env`, puis redémarrez l'application.")


def reflex_cards_page() -> None:
    page_header(
        "Réponse à incident",
        "Fiches réflexes PME",
        "Des actions courtes et prioritaires pour limiter l'impact d'un incident de phishing.",
    )
    cards = [
        ("Lien suspect reçu", "lien_suspect.md"),
        ("L'utilisateur a cliqué", "clic_phishing.md"),
        ("Identifiants saisis", "identifiants_compromis.md"),
    ]
    for title, filename in cards:
        with st.expander(title, expanded=filename == "lien_suspect.md"):
            st.markdown((ROOT_DIR / "fiches_reflexes" / filename).read_text(encoding="utf-8"))


def configuration_page() -> None:
    page_header(
        "Administration",
        "Configuration sécurisée",
        "Paramétrez les alertes et les services facultatifs sans exposer de secrets dans le code.",
    )
    st.write("La configuration sensible est lue depuis un fichier local `.env`.")
    st.code((ROOT_DIR / ".env.example").read_text(encoding="utf-8"), language="ini")
    st.warning("Ne publiez jamais le fichier `.env` ni un mot de passe d'application.")
    st.subheader("Limites du MVP")
    st.write("- Analyse statique de l'URL : aucun site n'est ouvert.")
    st.write("- Le modèle peut produire des faux positifs et des faux négatifs.")
    st.write("- Gmail et Outlook automatiques sont réservés à une évolution future.")


PAGES = {
    "Tableau de bord": dashboard_page,
    "Analyser une URL": single_analysis_page,
    "Analyse en masse": bulk_analysis_page,
    "Historique": history_page,
    "Alertes": alerts_page,
    "Fiches réflexes": reflex_cards_page,
    "Configuration": configuration_page,
}

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-mark">◈</div>
          <div><div class="brand-title">CyberVeille PME</div>
          <div class="brand-subtitle">Threat Intelligence & ML</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_page = st.radio("Navigation", list(PAGES))
    st.caption("MVP Jalon 3 · CMRPI")

PAGES[selected_page]()
