"""
API & Infrastructure Monitor
============================

Objectif : vérifier en un coup d'oeil que tout l'écosystème est prêt :
- Connexion DuckDB + tables critiques
- Fraîcheur des données (events & prices)
- Présence des caches pré-calculés
- Clés API disponibles
- Scripts critiques exécutables
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import duckdb
import pandas as pd
import streamlit as st

SRC_DIR = Path(__file__).parent.parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config  # noqa: E402

DB_PATH = config.DB_PATH
CACHE_FILES = [
    Path("data/cache_clusters.csv"),
    Path("data/cache_cluster_patterns.csv"),
]


def check_env_keys() -> Dict[str, bool]:
    return {
        "EODHD_API_KEY": bool(os.getenv("EODHD_API_KEY")),
        "TE_API_KEY": bool(os.getenv("TE_API_KEY")),
        "FINNHUB_API_KEY": bool(os.getenv("FINNHUB_API_KEY")),
    }


def run_duckdb_query(query: str, params: Optional[List] = None) -> pd.DataFrame:
    conn = duckdb.connect(database=str(DB_PATH), read_only=True)
    try:
        df = conn.execute(query, params or []).df()
    finally:
        conn.close()
    return df


def get_db_snapshot() -> Dict[str, Optional[str]]:
    snapshot = {
        "events_count": None,
        "last_event": None,
        "future_events": None,
        "prices_last": None,
        "prices_rows": None,
    }
    try:
        events_df = run_duckdb_query(
            """
            SELECT 
                COUNT(*) AS total,
                MAX(ts_utc) AS last_event,
                SUM(CASE WHEN ts_utc >= now() THEN 1 ELSE 0 END) AS future_events
            FROM events
            """
        )
        snapshot["events_count"] = int(events_df.loc[0, "total"])
        snapshot["last_event"] = str(events_df.loc[0, "last_event"])
        snapshot["future_events"] = int(events_df.loc[0, "future_events"])
    except Exception as exc:
        snapshot["events_error"] = str(exc)

    try:
        prices_df = run_duckdb_query(
            """
            SELECT COUNT(*) AS rows, MAX(ts_utc) AS last_price
            FROM prices
            """
        )
        snapshot["prices_rows"] = int(prices_df.loc[0, "rows"])
        snapshot["prices_last"] = str(prices_df.loc[0, "last_price"])
    except Exception as exc:
        snapshot["prices_error"] = str(exc)

    return snapshot


def get_cache_status() -> List[Dict[str, str]]:
    stats = []
    for path in CACHE_FILES:
        abs_path = Path(path)
        info = {
            "file": str(path),
            "exists": abs_path.exists(),
            "size_kb": "",
            "rows": "",
            "last_mod": "",
        }
        if abs_path.exists():
            info["size_kb"] = f"{abs_path.stat().st_size / 1024:.1f}"
            info["last_mod"] = datetime.fromtimestamp(
                abs_path.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")
            try:
                df = pd.read_csv(abs_path, nrows=5)
                info["rows"] = f"{len(pd.read_csv(abs_path)):,}"
                info["preview"] = df.to_dict(orient="records")
            except Exception as exc:
                info["rows"] = f"Erreur: {exc}"
        stats.append(info)
    return stats


def run_python_script(script_path: Path) -> Dict[str, str]:
    started = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=240,
        )
        status = "success" if result.returncode == 0 else "error"
    except Exception as exc:
        status = "error"
        result = type("obj", (), {"stdout": "", "stderr": str(exc), "returncode": -1})

    duration = (datetime.now(timezone.utc) - started).total_seconds()
    return {
        "status": status,
        "stdout": result.stdout[-1500:],
        "stderr": result.stderr[-1500:],
        "returncode": result.returncode,
        "duration": f"{duration:.1f}s",
    }


st.set_page_config(page_title="API & Infra Monitor", page_icon="🛡️", layout="wide")
st.title("🛡️ API & Infrastructure Monitor")
st.caption(f"DB : `{DB_PATH}`")

env_keys = check_env_keys()
db_snapshot = get_db_snapshot()
cache_stats = get_cache_status()

col1, col2, col3, col4 = st.columns(4)
with col1:
    ok = db_snapshot.get("events_count") is not None
    st.metric(
        "Événements",
        f"{db_snapshot.get('events_count','?')}",
        help=f"Dernier event : {db_snapshot.get('last_event','N/A')}",
    )
with col2:
    st.metric(
        "Prix en base",
        f"{db_snapshot.get('prices_rows','?')}",
        help=f"Dernier prix : {db_snapshot.get('prices_last','N/A')}",
    )
with col3:
    st.metric("Événements futurs", f"{db_snapshot.get('future_events','?')}")
with col4:
    healthy_cache = all(item["exists"] for item in cache_stats)
    st.metric("Caches prêts", "✅" if healthy_cache else "⚠️", help=str(cache_stats))

st.divider()

st.subheader("🔑 Clés API détectées")
cols = st.columns(len(env_keys) or 1)
for (key, present), col in zip(env_keys.items(), cols):
    col.metric(key, "✅" if present else "❌")

st.subheader("📦 Caches pré-calculés")
for cache in cache_stats:
    with st.expander(f"{cache['file']} — {'OK' if cache['exists'] else 'Manquant'}", expanded=not cache["exists"]):
        st.write(cache)

st.subheader("🧪 Tests rapides")
col_a, col_b = st.columns(2)
with col_a:
    if st.button("Tester connexion DB", use_container_width=True):
        try:
            df = run_duckdb_query("SELECT * FROM events ORDER BY ts_utc DESC LIMIT 5")
            st.success("Connexion OK, 5 derniers events chargés")
            st.dataframe(
                df,
                use_container_width=True,
                height=240,
                hide_index=True,
            )
        except Exception as exc:
            st.error(f"Erreur DuckDB : {exc}")

with col_b:
    cache_script = Path("scripts/cache_refresh.py")
    if st.button("Rafraîchir caches maintenant", use_container_width=True):
        if cache_script.exists():
            result = run_python_script(cache_script)
            if result["status"] == "success":
                st.success(f"Caches régénérés en {result['duration']}")
                st.code(result["stdout"] or "OK")
            else:
                st.error(f"Erreur (code {result['returncode']})")
                st.code(result["stderr"] or result["stdout"])
        else:
            st.error(f"Script introuvable : {cache_script}")

st.subheader("📊 Vérification tables critiques")
tabs = st.tabs(["events", "prices", "clusters"])

with tabs[0]:
    try:
        df = run_duckdb_query(
            """
            SELECT country, COUNT(*) AS n, MIN(ts_utc) AS first, MAX(ts_utc) AS last
            FROM events
            GROUP BY country
            ORDER BY n DESC
            LIMIT 10
            """
        )
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        st.error(f"Impossible de lire events : {exc}")

with tabs[1]:
    try:
        df = run_duckdb_query(
            """
            SELECT DATE_TRUNC('day', ts_utc) AS day, COUNT(*) AS rows
            FROM prices
            WHERE ts_utc >= now() - INTERVAL '3 days'
            GROUP BY 1
            ORDER BY day DESC
            """
        )
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        st.error(f"Impossible de lire prices : {exc}")

with tabs[2]:
    if cache_stats and cache_stats[0]["exists"]:
        df = pd.read_csv(CACHE_FILES[0]).head(20)
        st.dataframe(df)
    else:
        st.info("Cache cluster manquant. Lancez le rafraîchissement.")

st.divider()
st.markdown(
    """
### Checklist quotidienne recommandée
1. ✅ Vérifier connexion DuckDB et présence d'événements futurs
2. ✅ Contrôler qu'au moins 1 point prix a été ingéré sur les dernières 24h
3. ✅ Confirmer caches `cache_clusters*` à jour (timestamp du jour)
4. ✅ Rafraîchir les caches après chaque mise à jour DB
5. ✅ S'assurer que les clés API nécessaires sont chargées avant extraction
"""
)
