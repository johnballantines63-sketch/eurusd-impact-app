"""
Mise à jour DB & Caches
=======================

Interface unifiée pour :
- vérifier l’état de la base (events, prix M1)
- lancer l’import Myfxbook (rev6 auto-login)
- lancer l’import Dukascopy incrémental
- rafraîchir les caches cluster/pattern
"""

from __future__ import annotations

import sys
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List

import duckdb
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
import config  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MYFXBOOK_SCRIPT = SCRIPTS_DIR / "myfxbook_auto_update_rev6_auto_login.py"
DUKASCOPY_SCRIPT = SCRIPTS_DIR / "session113" / "update_dukascopy_prices.py"
FINNHUB_SCRIPT = SCRIPTS_DIR / "finnhub_import_prices.py"
CACHE_SCRIPT = SCRIPTS_DIR / "cache_refresh.py"
POST_PIPELINE_SCRIPT = SCRIPTS_DIR / "post_update_pipeline.py"

st.set_page_config(page_title="Mise à jour DB & Caches", page_icon="🔄", layout="wide")
st.title("🔄 Mise à jour DB & Caches")
st.caption("Import Myfxbook • Import Dukascopy • Pré-calculs clusters")


@st.cache_data(ttl=300)
def load_db_stats() -> Dict[str, Optional[str]]:
    stats = {
        "events_total": None,
        "events_first": None,
        "events_last": None,
        "future_events": None,
        "prices_total": None,
        "prices_first": None,
        "prices_last": None,
        "prices_age_days": None,
    }
    if not config.DB_PATH.exists():
        stats["error"] = f"DB introuvable : {config.DB_PATH}"
        return stats
    conn = duckdb.connect(str(config.DB_PATH), read_only=True)
    try:
        ev = conn.execute(
            """
            SELECT 
                COUNT(*) AS total,
                MIN(ts_utc) AS first_event,
                MAX(ts_utc) AS last_event,
                SUM(CASE WHEN ts_utc >= now() THEN 1 ELSE 0 END) AS future_events
            FROM events
            """
        ).fetchone()
        stats["events_total"], stats["events_first"], stats["events_last"], stats["future_events"] = ev

        # Stats M1
        prices = conn.execute(
            """
            SELECT 
                COUNT(*) AS total,
                MIN(datetime) AS first_price,
                MAX(datetime) AS last_price
            FROM prices_finnhub_m1
            """
        ).fetchone()
        stats["prices_total"], stats["prices_first"], stats["prices_last"] = prices
        if stats["prices_last"]:
            last_dt = pd.Timestamp(stats["prices_last"]).to_pydatetime()
            stats["prices_age_days"] = (datetime.now().date() - last_dt.date()).days
        
        # Stats toutes timeframes
        stats["prices_m5"] = conn.execute("SELECT COUNT(*) FROM prices_finnhub_m5").fetchone()[0]
        stats["prices_m15"] = conn.execute("SELECT COUNT(*) FROM prices_finnhub_m15").fetchone()[0]
        stats["prices_m30"] = conn.execute("SELECT COUNT(*) FROM prices_finnhub_m30").fetchone()[0]
        stats["prices_h1"] = conn.execute("SELECT COUNT(*) FROM prices_finnhub_h1").fetchone()[0]
    finally:
        conn.close()
    return stats


def run_python_script(
    script_path: Path,
    args: Optional[List[str]] = None,
    input_text: Optional[str] = None,
) -> Dict[str, str]:
    if not script_path.exists():
        return {"status": "missing", "stderr": f"Script introuvable: {script_path}", "stdout": "", "returncode": -1}

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60 * 30,
        )
        status = "success" if result.returncode == 0 else "error"
        return {
            "status": status,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "stdout": "", "stderr": "Durée > 30 min", "returncode": -2}
    except Exception as exc:
        return {"status": "error", "stdout": "", "stderr": str(exc), "returncode": -3}


def display_result(result: Dict[str, str], label: str):
    if result["status"] == "success":
        st.success(f"{label} terminé (code {result['returncode']})")
    elif result["status"] == "missing":
        st.error(result["stderr"])
        return
    elif result["status"] == "timeout":
        st.error(f"{label} interrompu (timeout)")
    else:
        st.error(f"{label} a échoué (code {result['returncode']})")

    with st.expander(f"Logs - {label}"):
        if result["stdout"]:
            st.text(result["stdout"])
        if result["stderr"]:
            st.text(result["stderr"])


stats = load_db_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Événements", f"{stats.get('events_total','?'):,}" if stats.get("events_total") else "N/A")
    st.caption(f"Dernier : {stats.get('events_last','n/a')}")
with col2:
    st.metric("Événements futurs", f"{stats.get('future_events','?')}")
with col3:
    st.metric("Bougies M1", f"{stats.get('prices_total','?'):,}" if stats.get("prices_total") else "N/A")
with col4:
    age = stats.get("prices_age_days")
    age_display = f"{age} j" if age is not None else "?"
    st.metric("Âge dernière bougie", age_display)
    if age is not None and age > 1:
        st.warning("Prix à rafraîchir")

# Stats toutes timeframes
with st.expander("📊 Statistiques toutes timeframes"):
    col_m1, col_m5, col_m15, col_m30, col_h1 = st.columns(5)
    with col_m1:
        st.metric("M1", f"{stats.get('prices_total', 0):,}" if stats.get('prices_total') else "N/A")
    with col_m5:
        st.metric("M5", f"{stats.get('prices_m5', 0):,}" if stats.get('prices_m5') else "N/A")
    with col_m15:
        st.metric("M15", f"{stats.get('prices_m15', 0):,}" if stats.get('prices_m15') else "N/A")
    with col_m30:
        st.metric("M30", f"{stats.get('prices_m30', 0):,}" if stats.get('prices_m30') else "N/A")
    with col_h1:
        st.metric("H1", f"{stats.get('prices_h1', 0):,}" if stats.get('prices_h1') else "N/A")

st.divider()

st.header("1. Import Myfxbook (Events)")
st.markdown(
"""
Script utilisé : `scripts/myfxbook_auto_update_rev6_auto_login.py`

Configurer un identifiant de session Myfxbook **ou** vos identifiants email/mot de passe.
Le script supprime/réinsère jour par jour sur la période choisie puis met à jour la table `events`.
"""
)

with st.form("events_form"):
    current_year = datetime.now().year
    col_a, col_b = st.columns(2)
    start_year = col_a.number_input("Année de début", min_value=2015, max_value=current_year, value=current_year - 1, step=1)
    end_year = col_b.number_input("Année de fin", min_value=2015, max_value=current_year, value=current_year, step=1)
    session_id = st.text_input("Session Myfxbook (facultatif)")
    email = st.text_input("Email Myfxbook (option auto-login)")
    password = st.text_input("Mot de passe Myfxbook", type="password")
    auto_pipeline_events = st.checkbox(
        "Exécuter le pipeline post-MAJ (détection + caches) après l'import",
        value=True,
    )
    submit_events = st.form_submit_button("🚀 Importer les événements")

if submit_events:
    if end_year < start_year:
        st.error("L'année de fin doit être supérieure ou égale à l'année de début.")
    else:
        args = [
            "--db-path", str(config.DB_PATH),
            "--data-dir", str(config.DATA_DIR),
            "--tz", config.TIMEZONE_BERN,
            "--start-year", str(int(start_year)),
            "--end-year", str(int(end_year)),
        ]
        if session_id:
            args += ["--session", session_id.strip()]
        if email:
            args += ["--email", email.strip()]
        if password:
            args += ["--password", password]

        result = run_python_script(MYFXBOOK_SCRIPT, args=args)
        display_result(result, "Import Myfxbook")

        if result["status"] == "success" and auto_pipeline_events:
            pipeline_result = run_python_script(POST_PIPELINE_SCRIPT)
            display_result(pipeline_result, "Pipeline post-MAJ")

st.divider()

st.header("2. Import Dukascopy (Prix EUR/USD M1)")
st.markdown(
"""
Script utilisé : `scripts/session113/update_dukascopy_prices.py`

Il détecte automatiquement la dernière bougie disponible dans `prices_finnhub_m1`,
télécharge uniquement la période manquante depuis Finnhub.
"""
)

auto_confirm = st.checkbox("Confirmer automatiquement l'import (répond 'oui')", value=True)
auto_pipeline_prices = st.checkbox(
    "Exécuter le pipeline post-MAJ après import prix",
    value=False,
)
if st.button("📥 Importer les prix Dukascopy", use_container_width=True):
    confirm_input = "oui\n" if auto_confirm else None
    result = run_python_script(DUKASCOPY_SCRIPT, input_text=confirm_input)
    display_result(result, "Import Dukascopy")
    if result["status"] == "success" and auto_pipeline_prices:
        pipeline_result = run_python_script(POST_PIPELINE_SCRIPT)
        display_result(pipeline_result, "Pipeline post-MAJ")

st.divider()

st.header("3. Import Finnhub (Toutes timeframes)")
st.markdown(
"""
Script utilisé : `scripts/finnhub_import_prices.py`

Import des prix EUR/USD depuis l'API Finnhub pour **toutes les timeframes** (M1, M5, M15, M30, H1, D, W, M).

**Options :**
- **Import incrémental** : Télécharge uniquement les données manquantes depuis la dernière date en DB
- **Import période** : Télécharge une période spécifique (utile pour réimporter des dates manquantes)
- **Sélection timeframes** : Choisir quelles timeframes importer (ou toutes)

⚠️ **Important** : Une clé API Finnhub Premium est requise.
"""
)

with st.form("finnhub_form"):
    import_mode = st.radio(
        "Mode d'import",
        ["Incrémental (depuis dernière date)", "Période spécifique"],
        index=0
    )
    
    if import_mode == "Période spécifique":
        col_from, col_to = st.columns(2)
        from_date = col_from.date_input("Date de début", value=datetime.now().date() - timedelta(days=30))
        to_date = col_to.date_input("Date de fin", value=datetime.now().date())
    
    timeframes_options = st.multiselect(
        "Timeframes à importer",
        options=["M1", "M5", "M15", "M30", "H1", "D", "W", "M"],
        default=["M1", "M5", "M15", "M30", "H1"]
    )
    
    auto_pipeline_finnhub = st.checkbox(
        "Exécuter le pipeline post-MAJ après import prix",
        value=False,
    )
    
    submit_finnhub = st.form_submit_button("📥 Importer les prix Finnhub", use_container_width=True)

if submit_finnhub:
    if not timeframes_options:
        st.error("⚠️ Veuillez sélectionner au moins une timeframe")
    else:
        # Préparer les arguments de base
        base_args = []
        
        if import_mode == "Incrémental (depuis dernière date)":
            base_args.append("--incremental")
        else:
            base_args.extend(["--from-date", from_date.strftime("%Y-%m-%d")])
            base_args.extend(["--to-date", to_date.strftime("%Y-%m-%d")])
        
        # Importer les timeframes
        if len(timeframes_options) == 8:
            # Toutes les timeframes en une fois
            args = base_args.copy()
            args.append("--all-timeframes")
            result = run_python_script(FINNHUB_SCRIPT, args=args)
            display_result(result, "Import Finnhub (toutes timeframes)")
            
            if result["status"] == "success" and auto_pipeline_finnhub:
                pipeline_result = run_python_script(POST_PIPELINE_SCRIPT)
                display_result(pipeline_result, "Pipeline post-MAJ")
        else:
            # Importer chaque timeframe séparément
            progress_bar = st.progress(0)
            status_text = st.empty()
            all_success = True
            
            for idx, tf in enumerate(timeframes_options):
                status_text.text(f"📊 Import {tf} ({idx+1}/{len(timeframes_options)})...")
                progress_bar.progress((idx + 1) / len(timeframes_options))
                
                tf_args = base_args.copy()
                tf_args.extend(["--resolution", tf])
                
                result = run_python_script(FINNHUB_SCRIPT, args=tf_args)
                if result["status"] != "success":
                    all_success = False
                display_result(result, f"Import Finnhub {tf}")
            
            progress_bar.empty()
            status_text.empty()
            
            if all_success:
                st.success(f"✅ Import de {len(timeframes_options)} timeframes terminé")
                if auto_pipeline_finnhub:
                    pipeline_result = run_python_script(POST_PIPELINE_SCRIPT)
                    display_result(pipeline_result, "Pipeline post-MAJ")
            else:
                st.warning("⚠️ Certains imports ont échoué. Vérifiez les logs ci-dessus.")

st.divider()

st.header("4. Pipeline post-MAJ manuel")
st.markdown(
    "Relance detection → clusters → caches (équivalent aux cases cochées ci-dessus)."
)
if st.button("▶️ Lancer le pipeline complet", use_container_width=True):
    pipeline_result = run_python_script(POST_PIPELINE_SCRIPT)
    display_result(pipeline_result, "Pipeline post-MAJ")

if st.button("♻️ Rafraîchir uniquement les caches", use_container_width=True):
    cache_result = run_python_script(CACHE_SCRIPT)
    display_result(cache_result, "Rafraîchissement caches")

st.divider()
st.markdown(
"""
### Checklist opératoire
1. Importer les événements Myfxbook pour la période voulue
2. Importer les prix :
   - **Dukascopy** : Import M1 uniquement (legacy)
   - **Finnhub** : Import toutes timeframes (M1, M5, M15, M30, H1, D, W, M) - **Recommandé**
3. Rafraîchir les caches clusters/patterns
4. Relancer le Planificateur / Calendrier pour profiter des données à jour

**Note** : L'import Finnhub permet de mettre à jour toutes les timeframes nécessaires pour l'analyse multi-timeframe.
"""
)
