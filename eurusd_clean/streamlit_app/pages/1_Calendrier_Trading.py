"""
Calendrier Trading 2.0
======================

Nouvelle version reposant sur :
- Workflow correct (Prix → Mouvement → Cluster → Projection)
- Cache pré-calculé des clusters (`data/cache_clusters.csv`)
- Projection automatique des clusters connus sur les événements futurs
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import duckdb
import pandas as pd
import streamlit as st

# ═══════════════════════════════════════════════════════════════
# Configuration Paths & Imports
# ═══════════════════════════════════════════════════════════════

SRC_DIR = Path(__file__).parent.parent.parent / "src"
SESSION_SCRIPTS = Path(__file__).parent.parent.parent / "SESSION_VALIDATION_ACTUELLE" / "scripts"

for p in (SRC_DIR, SESSION_SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import config  # noqa: E402
from core.event_utils import normalize_event_keys_list  # noqa: E402
from utils.auto_refresh import ensure_data_freshness

# ⭐ V8 Adapter (optionnel, pour prédictions temps réel)
try:
    from core.v8_ui_adapter import predict_cluster_v8
    V8_AVAILABLE = True
except ImportError:
    V8_AVAILABLE = False
    predict_cluster_v8 = None

st.set_page_config(page_title="Calendrier Trading 2.0", page_icon="📅", layout="wide")

CACHE_CLUSTERS_PATH = Path("data/cache_clusters.csv")
CACHE_PATTERNS_PATH = Path("data/cache_cluster_patterns.csv")
WINDOW_MINUTES_DEFAULT = 60
BERN_TZ = "Europe/Zurich"

EURUSD_RELEVANT_COUNTRIES = [
    "US",
    "EU",
    "DE",
    "FR",
    "IT",
    "ES",
    "NL",
    "BE",
    "AT",
    "PT",
    "IE",
    "GR",
    "CH",
    "GB",
]


@st.cache_data(ttl=3600)
def load_cache_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not CACHE_CLUSTERS_PATH.exists() or not CACHE_PATTERNS_PATH.exists():
        raise FileNotFoundError(
            "Cache introuvable. Lancez `python3 scripts/cache_refresh.py`."
        )
    clusters = pd.read_csv(CACHE_CLUSTERS_PATH)
    cluster_patterns = pd.read_csv(CACHE_PATTERNS_PATH)
    return clusters, cluster_patterns


@st.cache_data(ttl=600)
def load_future_events(
    start_dt: datetime,
    end_dt: datetime,
    countries: List[str],
    min_importance: int,
) -> pd.DataFrame:
    conn = duckdb.connect(database=str(config.DB_PATH), read_only=True)
    query = """
            SELECT 
            ts_utc,
            country,
            event_title,
            event_key,
            importance_n,
            empirical_score,
            score_source,
            previous,
            forecast
            FROM events 
        WHERE ts_utc BETWEEN ? AND ?
          AND country IN ({countries})
          AND importance_n <= ?
        ORDER BY ts_utc
    """.replace(
        "{countries}",
        ",".join(["?"] * len(countries)),
    )
    params = [start_dt, end_dt, *countries, min_importance]
    df = conn.execute(query, params).df()
    conn.close()
    
    if df.empty:
        return df

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["ts_bern"] = df["ts_utc"].dt.tz_convert(BERN_TZ)
    df["event_key"] = df["event_key"].fillna("").astype(str)
    df["event_title"] = df["event_title"].fill_na("").astype(str)
    return df


def compute_signature(event_keys: List[str]) -> str:
    normalized = [key for key in normalize_event_keys_list(event_keys) if key]
    if not normalized:
        return ""
    unique_sorted = sorted(dict.fromkeys(normalized))
    return "|".join(unique_sorted)


def build_future_clusters(
    df_events: pd.DataFrame,
    window_minutes: int,
) -> pd.DataFrame:
    if df_events.empty:
        return pd.DataFrame()

    df_events = df_events.sort_values("ts_utc").reset_index(drop=True)
    timestamps = df_events["ts_utc"].tolist()
    event_keys = df_events["event_key"].tolist()
    rows: List[Dict] = []
    window = pd.Timedelta(minutes=window_minutes)

    for idx, anchor_time in enumerate(timestamps):
        start = anchor_time - window
        end = anchor_time + window
        mask = (df_events["ts_utc"] >= start) & (df_events["ts_utc"] <= end)
        events_slice = df_events.loc[mask]
        signature = compute_signature(events_slice["event_key"].tolist())
        if not signature:
            continue

        rows.append(
            {
                "anchor_ts": anchor_time,
                "anchor_ts_bern": events_slice["ts_bern"].min(),
                "cluster_signature": signature,
                "num_events_window": len(events_slice),
                "countries": ", ".join(sorted(events_slice["country"].unique())),
                "titles": ", ".join(events_slice["event_title"].unique()),
                "main_importance": events_slice["importance_n"].min(),
            }
        )

    df_clusters = pd.DataFrame(rows)
    if df_clusters.empty:
        return df_clusters

    df_clusters = (
        df_clusters.sort_values("anchor_ts")
        .drop_duplicates(subset=["cluster_signature", "anchor_ts"], keep="first")
        .reset_index(drop=True)
    )
    return df_clusters


def compute_confidence(n_samples: float) -> str:
    if pd.isna(n_samples) or n_samples == 0:
        return "❔"
    if n_samples >= 20:
        return "🟢 élevée"
    if n_samples >= 8:
        return "🟡 moyenne"
    if n_samples >= 3:
        return "🟠 faible"
    return "🔴 très faible"


def auto_refresh_on_launch(state_key: str = "auto_refresh_calendar"):
    if st.session_state.get(state_key):
        return
    progress_text = st.empty()
    progress_bar = st.progress(0.0)

    def progress_cb(value: float, message: str):
        progress_bar.progress(min(max(value, 0.0), 1.0))
        progress_text.text(message)

    refresh = ensure_data_freshness(progress_callback=progress_cb)
    progress_bar.empty()
    progress_text.empty()
    if refresh.price_update_triggered or refresh.pipeline_triggered:
        st.success("🔄 Données mises à jour automatiquement avant affichage du calendrier.")
    else:
        if refresh.price_age_hours is not None:
            cache_age = (
                f"{refresh.cache_age_hours:.1f} h"
                if refresh.cache_age_hours is not None
                else "inconnue"
            )
            st.caption(
                f"📈 Dernière bougie M1 : {refresh.price_age_hours:.1f} h "
                f"(cache : {cache_age})"
            )
        else:
            st.caption("📈 Informations prix indisponibles (aucune donnée en base).")
    st.session_state[state_key] = True


def main():
    st.title("📅 Calendrier Trading 2.0")
    st.caption(
        "Projection des clusters historiques dans le futur pour identifier les fenêtres "
        "de forte probabilité sur EUR/USD."
    )

    auto_refresh_on_launch()

    cache_clusters, cache_cluster_patterns = load_cache_files()

    st.sidebar.header("⚙️ Paramètres")
    lookahead_days = st.sidebar.slider("Nombre de jours à venir", 1, 21, 7)
    window_minutes = st.sidebar.slider("Fenêtre cluster (minutes)", 15, 120, WINDOW_MINUTES_DEFAULT, 15)
    min_importance = st.sidebar.select_slider(
        "Importance minimale (1=High)",
        options=[1, 2, 3],
        value=2,
    )
    min_expected_impact = st.sidebar.slider("Impact médian minimal (pips)", 0, 150, 40, 10)
    min_samples = st.sidebar.slider("Occurrences min. pour valider un cluster", 1, 30, 5)
    
    # ⭐ V8 Option : Prédictions temps réel
    use_v8_realtime = False
    if V8_AVAILABLE:
        use_v8_realtime = st.sidebar.checkbox(
            "🔬 Utiliser moteur V8 (prédictions temps réel)",
            value=False,
            help="Active les prédictions V8 backtestées au lieu du cache historique"
        )

    countries_default = ["US", "EU"]
    countries = st.sidebar.multiselect(
        "Pays",
        EURUSD_RELEVANT_COUNTRIES,
        default=countries_default,
    )
    if not countries:
        st.sidebar.warning("Sélectionnez au moins un pays.")
        return

    st.sidebar.divider()
    st.sidebar.markdown("### 🎯 Objectif")
    st.sidebar.write(
        "1. Recherche de multi-événements futurs\n"
        "2. Match avec les clusters historiques\n"
        "3. Affichage impact + pattern attendu"
    )

    start_dt = datetime.now(timezone.utc)
    end_dt = start_dt + timedelta(days=lookahead_days)

    with st.spinner("Chargement des événements futurs…"):
        df_events = load_future_events(start_dt, end_dt, countries, min_importance)

    if df_events.empty:
        st.warning("Aucun événement trouvé sur la période sélectionnée.")
        return

    with st.spinner("Recherche des clusters…"):
        df_future_clusters = build_future_clusters(df_events, window_minutes)

    if df_future_clusters.empty:
        st.info("Aucun cluster multi-événement détecté avec ces paramètres.")
        return

    enriched = df_future_clusters.merge(
        cache_clusters,
        on="cluster_signature",
        how="left",
        suffixes=("", "_cache"),
    )

    enriched = enriched.merge(
        cache_cluster_patterns.rename(
            columns={
                "pattern_type": "pattern_type_cache",
                "direction": "direction_cache",
                "impact_median": "impact_median_pattern",
                "latency_median": "latency_median_pattern",
                "ttr_median": "ttr_median_pattern",
            }
        ),
        on="cluster_signature",
        how="left",
    )

    enriched["confidence_label"] = enriched["n_samples"].apply(compute_confidence)
    enriched["expected_pattern"] = (
        enriched["pattern_type_cache"].fillna(enriched["dominant_pattern"])
    )
    enriched["expected_direction"] = (
        enriched["direction_cache"].fillna(enriched["dominant_direction"])
    )
    enriched["impact_candidate"] = enriched["impact_median_pattern"].fillna(
        enriched["impact_median"]
    )

    filtered = enriched[
        (enriched["impact_candidate"] >= min_expected_impact)
        & (enriched["n_samples"] >= min_samples)
    ].copy()

    if filtered.empty:
        st.warning("Aucun cluster ne satisfait les seuils impact/échantillons.")
        st.dataframe(
            enriched[
                [
                    "anchor_ts_bern",
                    "cluster_signature",
                    "impact_candidate",
                    "n_samples",
                    "expected_pattern",
                ]
            ],
            use_container_width=True,
        )
        return

    filtered["anchor_ts_bern_str"] = filtered["anchor_ts_bern"].dt.strftime("%Y-%m-%d %H:%M")
    filtered = filtered.sort_values("anchor_ts_bern")

    st.success(f"{len(filtered)} clusters futurs détectés.")

    summary_cols = [
        "anchor_ts_bern_str",
        "countries",
        "num_events_window",
        "impact_candidate",
        "expected_pattern",
        "expected_direction",
        "latency_median",
        "ttr_median",
        "pullback_median",
        "confidence_label",
        "n_samples",
        "titles",
    ]
    st.dataframe(
        filtered[summary_cols].rename(
            columns={
                "anchor_ts_bern_str": "Date (Bern)",
                "countries": "Pays",
                "num_events_window": "#événements",
                "impact_candidate": "Impact médian (pips)",
                "expected_pattern": "Pattern attendu",
                "expected_direction": "Direction",
                "latency_median": "Latence médiane (min)",
                "ttr_median": "TTR médian (min)",
                "pullback_median": "Pullback médian (pips)",
                "confidence_label": "Confiance",
                "n_samples": "Occurrences historiques",
                "titles": "Événements",
            }
        ),
        use_container_width=True,
    )

    for _, row in filtered.iterrows():
        # ⭐ V8 : Calculer prédiction temps réel si activé
        v8_pred = None
        if use_v8_realtime and V8_AVAILABLE:
            try:
                # Charger events pour cette date
                anchor_ts = row['anchor_ts']
                day_start = pd.Timestamp(anchor_ts).normalize()
                day_end = day_start + pd.Timedelta(days=1)
                
                conn_v8 = duckdb.connect(database=str(config.DB_PATH), read_only=True)
                query_events = """
                    SELECT 
                        ts_utc, country, event_key,
                        actual, estimate, previous, forecast,
                        empirical_score, latency_median
                    FROM events
                    WHERE ts_utc >= ? AND ts_utc < ?
                      AND country IN ('US', 'EU', 'GB', 'DE')
                      AND estimate IS NOT NULL
                    ORDER BY ts_utc
                """
                events_day = conn_v8.execute(query_events, [day_start, day_end]).df()
                conn_v8.close()
                
                if not events_day.empty:
                    # Filtrer events du cluster (par signature)
                    cluster_keys = row['cluster_signature'].split('|')
                    events_cluster = events_day[
                        events_day['event_key'].isin(cluster_keys)
                    ].copy()
                    
                    if not events_cluster.empty and 'actual' in events_cluster.columns:
                        # Utiliser actuals si disponibles, sinon estimate comme proxy
                        events_cluster['actual'] = events_cluster['actual'].fillna(
                            events_cluster['estimate']
                        )
                        
                        v8_pred = predict_cluster_v8(
                            date=anchor_ts,
                            events_df=events_cluster,
                            db_path=config.DB_PATH,
                            movement_start_time=anchor_ts
                        )
            except Exception as e:
                st.warning(f"⚠️ Erreur prédiction V8 pour {row['anchor_ts_bern_str']}: {str(e)}")
        
        # Afficher métriques (V8 si disponible, sinon cache)
        impact_display = row['impact_candidate']
        direction_display = row['expected_direction']
        pattern_display = row['expected_pattern']
        
        if v8_pred and v8_pred.get('success'):
            impact_display = v8_pred['impact_pips']
            direction_display = v8_pred['direction'] or direction_display
            pattern_display = v8_pred['pattern_type'] or pattern_display
        
        expander_label = (
            f"{row['anchor_ts_bern_str']} | {pattern_display} "
            f"{direction_display} | Impact ~{impact_display:.1f} pips"
        )
        if v8_pred and v8_pred.get('success'):
            expander_label += " 🔬V8"
        
        with st.expander(expander_label):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Impact médian", f"{impact_display:.1f} pips")
                st.metric("Latence", f"{row.get('latency_median', 0) or 0:.0f} min")
                st.metric("TTR", f"{row.get('ttr_median', 0) or 0:.0f} min")
            with col2:
                st.metric("Pullback", f"{row.get('pullback_median', 0) or 0:.1f} pips")
                st.metric("Occurrences historiques", int(row.get("n_samples", 0)))
                st.metric("Confiance", row["confidence_label"])
            with col3:
                st.metric("Pattern dominant", pattern_display or "N/A")
                st.metric("Direction dominante", direction_display or "N/A")
                st.caption(row["titles"])
            
            # ⭐ V8 : Afficher détails prédiction si disponible
            if v8_pred and v8_pred.get('success'):
                st.divider()
                st.markdown("**🔬 Prédiction V8 (temps réel)**")
                col_v8_1, col_v8_2 = st.columns(2)
                with col_v8_1:
                    st.metric("Direction V8", v8_pred['direction'])
                    st.metric("Impact V8", f"{v8_pred['impact_pips']:.1f} pips")
                    st.metric("Pattern V8", v8_pred['pattern_type'] or "N/A")
                with col_v8_2:
                    st.metric("Trigger strength", f"{v8_pred['trigger_strength']:.2f}")
                    st.metric("Cluster type", v8_pred['cluster_type'] or "N/A")
                    if v8_pred.get('leg1') and v8_pred.get('leg2'):
                        st.caption(
                            f"Leg1: {v8_pred['leg1']['amp_pips']:.1f} pips "
                            f"({v8_pred['leg1']['direction']}) | "
                            f"Leg2: {v8_pred['leg2']['amp_pips']:.1f} pips "
                            f"({v8_pred['leg2']['direction']})"
                        )
                
                # Afficher warnings SAFE si présents
                if v8_pred.get('warnings'):
                    for warning in v8_pred['warnings']:
                        st.warning(warning)
            
            st.markdown("**Cluster signature**")
            st.code(row["cluster_signature"], language="text")

    # -------------------------------------------------------------------------
    # Export CSV des clusters filtrés
    # -------------------------------------------------------------------------
    st.divider()
    export_df = filtered[summary_cols].copy()
    
    st.download_button(
        label="📥 Exporter les clusters (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=f"calendrier_clusters_{datetime.now().date()}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
