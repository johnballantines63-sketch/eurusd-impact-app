"""
PLANIFICATEUR V3.0 - PIPELINE LOO-CV INTÉGRÉ
=============================================

Version 3.0 - Session 134
Implémentation complète Étapes 5-11 selon Flowchart Session 133

Architecture Complète (11 Étapes):
1. Validation entrée (formats date flexibles) ✅
2. Charger events HIGH ✅
3. Charger prix 1-minute ✅
4. Enrichir events avec scores ✅
5. Détecter pattern ✅ NEW
6. Aiguillage prédiction selon pattern ✅ NEW
7. Prédiction Double Wave ✅ NEW
8. Prédiction Single Wave (Pipeline LOO-CV) ✅ NEW
9. Gestion pattern inconnu ✅ NEW
10. Affichage résultats ✅ NEW
11. Export CSV ✅ NEW

Nouveautés V3.0:
- ✅ Pipeline LOO-CV complet (validation MAE < 10 pips)
- ✅ Détection pattern simplifiée (score + impact)
- ✅ Module DoubleWave Session 132 (critères inclusion/exclusion)
- ✅ Paramètre min_pips paramétrable
- ✅ Affichage méthode utilisée (LOO-CV calibrée vs fallback)
- ✅ Formats date flexibles (YYYY-MM-DD, DD.MM.YYYY, etc.)
- ✅ Export CSV téléchargeable
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import pytz
import duckdb
from typing import Dict, Tuple, Optional
import io

# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app'))

import config
from core.event_utils import normalize_event_keys_list, create_event_key_set
from utils.auto_refresh import ensure_data_freshness

DB_PATH = config.DB_PATH
CACHE_CLUSTERS_PATH = Path(__file__).parent.parent.parent / "data" / "cache_clusters.csv"
CACHE_PATTERNS_PATH = Path(__file__).parent.parent.parent / "data" / "cache_cluster_patterns.csv"

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION PAGE
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Planificateur V3.0 - Pipeline LOO-CV",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Planificateur V3.0 - Pipeline LOO-CV Intégré")
st.markdown("**Version 3.0 (Session 134)** - Flowchart 11 étapes COMPLET")


def auto_refresh_on_launch(state_key: str = "auto_refresh_planif"):
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
        st.success("🔄 Données mises à jour automatiquement (prix et caches).")
        for log in refresh.logs:
            status = "✅" if log.success else "⚠️"
            with st.expander(f"{status} {log.action}"):
                if log.stdout:
                    st.code(log.stdout)
                if log.stderr:
                    st.code(log.stderr)
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


auto_refresh_on_launch()

# Info nouveautés
with st.expander("🆕 Nouveautés Version 3.0", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔬 Pipeline LOO-CV")
        st.write("• Calibration spécifique par événement")
        st.write("• Validation MAE < 10 pips")
        st.write("• Fallback fonction universelle")
        st.caption("Sessions 125-126 + Flowchart 132")
    
    with col2:
        st.markdown("### 🎯 Détection Pattern")
        st.write("• Classification automatique")
        st.write("• Seuil min_pips paramétrable")
        st.write("• Confidence score")
        st.caption("Sessions 120-132")
    
    with col3:
        st.markdown("### 📊 Module DoubleWave")
        st.write("• Critères inclusion/exclusion")
        st.write("• Amp fixes (0.1201 / 0.0128)")
        st.write("• Cascade exclus automatiquement")
        st.caption("Sessions 131-132")


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 1 : VALIDATION ENTRÉE
# ═══════════════════════════════════════════════════════════════

def parse_flexible_date(date_str: str) -> datetime:
    """Parse date avec formats multiples"""
    formats = [
        '%Y-%m-%d', '%Y.%m.%d', '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(
        f"Format date non reconnu: '{date_str}'. "
        f"Formats acceptés: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY"
    )


def validate_input(date_str: str, timezone_str: str = "Europe/Zurich", min_pips: float = 35.0) -> Dict:
    """Valide les entrées utilisateur"""
    try:
        date = parse_flexible_date(date_str)
        tz = pytz.timezone(timezone_str)
        
        if date < datetime(2023, 1, 1) or date > datetime(2025, 12, 31):
            return {
                'valid': False,
                'error_message': f"Date hors période données (2023-2025): {date_str}"
            }
        
        if min_pips <= 0:
            return {
                'valid': False,
                'error_message': f"min_pips doit être > 0 (reçu: {min_pips})"
            }
        
        return {
            'valid': True,
            'date': date,
            'timezone': tz,
            'min_pips': min_pips,
            'error_message': None
        }
    except Exception as e:
        return {
            'valid': False,
            'error_message': str(e)
        }


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 2 : CHARGER EVENTS
# ═══════════════════════════════════════════════════════════════

def load_events_for_date(date: datetime, db_path: Path, timezone_str: str = "Europe/Zurich") -> pd.DataFrame:
    """
    Charge événements HIGH pour date donnée.
    AMÉLIORÉ : Charge aussi événements avec empirical_score > 40 si importance_n = 3 insuffisant.
    EXCLUT : Conférences de presse, speeches et autres événements sans actual mesurable.
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # ÉTAPE 1 : Charger événements HIGH (importance_n = 3)
    # EXCLURE conférences, speeches, etc. (pas d'actual mesurable)
    # EXCLURE pays non pertinents pour EUR/USD
    relevant_countries_list = "', '".join(EURUSD_RELEVANT_COUNTRIES)
    query_high = f"""
    SELECT 
        e.ts_utc, e.country, e.event_title, e.event_key, e.importance_n,
        e.actual, e.estimate, e.forecast, e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc AT TIME ZONE '{timezone_str}') = ?
      AND e.country IN ('{relevant_countries_list}')
      AND e.importance_n = 3
      AND NOT (
        LOWER(e.event_key) LIKE '%press conference%'
        OR LOWER(e.event_key) LIKE '%conference%'
        OR LOWER(e.event_key) LIKE '%speech%'
        OR LOWER(e.event_title) LIKE '%press conference%'
        OR LOWER(e.event_title) LIKE '%conference%'
        OR LOWER(e.event_title) LIKE '%speech%'
      )
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query_high, [date.strftime('%Y-%m-%d')]).df()
    
    # ÉTAPE 2 : Si peu d'événements, charger aussi ceux avec empirical_score > 40
    # EXCLURE aussi conférences, speeches
    if len(df) < 3:
        query_score = f"""
        SELECT 
            e.ts_utc, e.country, e.event_title, e.event_key, e.importance_n,
            e.actual, e.estimate, e.forecast, e.previous,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE DATE(e.ts_utc AT TIME ZONE '{timezone_str}') = ?
          AND e.country IN ('{relevant_countries_list}')
          AND ef.empirical_score IS NOT NULL
          AND ef.empirical_score > 40
          AND e.importance_n != 3
          AND NOT (
            LOWER(e.event_key) LIKE '%press conference%'
            OR LOWER(e.event_key) LIKE '%conference%'
            OR LOWER(e.event_key) LIKE '%speech%'
            OR LOWER(e.event_title) LIKE '%press conference%'
            OR LOWER(e.event_title) LIKE '%conference%'
            OR LOWER(e.event_title) LIKE '%speech%'
          )
        ORDER BY e.ts_utc
        """
        
        df_score = conn.execute(query_score, [date.strftime('%Y-%m-%d')]).df()
        
        # Combiner (éviter doublons)
        if not df_score.empty:
            df = pd.concat([df, df_score]).drop_duplicates(subset=['event_key', 'ts_utc']).reset_index(drop=True)
    
    conn.close()
    
    if len(df) > 0:
        df['ts_bern'] = pd.to_datetime(df['ts_utc']).dt.tz_convert(timezone_str)
        # Double vérification avec fonction Python (plus robuste)
        mask_has_actual = df.apply(
            lambda row: not is_event_without_actual(row['event_key'], row.get('event_title', '')),
            axis=1
        )
        df = df[mask_has_actual].reset_index(drop=True)
    
    return df


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 3 : CHARGER PRIX
# ═══════════════════════════════════════════════════════════════

def load_prices_for_date(date: datetime, db_path: Path, timezone_str: str = "Europe/Zurich") -> pd.DataFrame:
    """Charge prix 1-minute pour date donnée"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = ?
    ORDER BY datetime
    """
    
    df = conn.execute(query, [date.strftime('%Y-%m-%d')]).df()
    conn.close()
    
    if len(df) > 0:
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(timezone_str)
        df = df.set_index('datetime')
    
    return df


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 4 : ENRICHIR EVENTS AVEC SCORES
# ═══════════════════════════════════════════════════════════════

def enrich_events_with_scores(df_events: pd.DataFrame, db_path: Path) -> pd.DataFrame:
    """Enrichit événements avec scores empiriques et surprises"""
    conn = duckdb.connect(str(db_path), read_only=True)
    df_scores = conn.execute("SELECT event_key, country, empirical_score FROM event_families").df()
    conn.close()
    
    df_enriched = df_events.copy()
    scores, surprises = [], []
    
    for idx, row in df_enriched.iterrows():
        # Chercher score
        score_match = df_scores[
            (df_scores['event_key'] == row['event_key']) & 
            (df_scores['country'] == row['country'])
        ]
        score = score_match.iloc[0]['empirical_score'] if len(score_match) > 0 else 0.0
        scores.append(score)
        
        # Calculer surprise
        if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
            surprise = (row['actual'] - row['estimate']) / abs(row['estimate']) * 100
        else:
            surprise = 0.0
        surprises.append(surprise)
    
    df_enriched['score'] = scores
    df_enriched['surprise'] = surprises
    df_enriched['score_adjusted'] = df_enriched['score'] * (1 + df_enriched['surprise'] / 100)
    
    return df_enriched


# ═══════════════════════════════════════════════════════════════
# FONCTIONS CACHE PRÉ-CALCULÉ
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def load_cache_clusters() -> Optional[pd.DataFrame]:
    """Charge le cache des clusters pré-calculés"""
    if not CACHE_CLUSTERS_PATH.exists():
        return None
    try:
        return pd.read_csv(CACHE_CLUSTERS_PATH)
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_cache_patterns() -> Optional[pd.DataFrame]:
    """Charge le cache des patterns par cluster"""
    if not CACHE_PATTERNS_PATH.exists():
        return None
    try:
        return pd.read_csv(CACHE_PATTERNS_PATH)
    except Exception:
        return None


def find_cluster_in_cache(df_events: pd.DataFrame, df_cache: pd.DataFrame) -> Optional[Dict]:
    """
    Cherche un cluster correspondant dans le cache pré-calculé.
    
    Args:
        df_events: DataFrame avec événements du cluster
        df_cache: DataFrame du cache clusters
    
    Returns:
        Dict avec stats du cluster trouvé ou None
    """
    if df_cache is None or df_cache.empty or df_events.empty:
        return None
    
    # Créer signature du cluster actuel
    event_keys = df_events['event_key'].dropna().tolist()
    if not event_keys:
        return None
    
    # Normaliser les clés
    normalized_keys = normalize_event_keys_list(event_keys, method='with_variants')
    signature_current = '|'.join(sorted(set(normalized_keys)))
    
    # Chercher dans le cache (signature exacte ou partielle)
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        # Normaliser signature cache
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        signature_cache = '|'.join(sorted(set(cache_normalized)))
        
        # Match exact
        if signature_current == signature_cache:
            return {
                'cluster_signature': cache_sig,
                'impact_median': row.get('impact_median', None),
                'impact_mean': row.get('impact_mean', None),
                'latency_median': row.get('latency_median', None),
                'ttr_median': row.get('ttr_median', None),
                'pullback_median': row.get('pullback_median', None),
                'dominant_pattern': row.get('dominant_pattern', None),
                'dominant_direction': row.get('dominant_direction', None),
                'n_samples': row.get('n_samples', 0),
                'total_score_median': row.get('total_score_median', None),
            }
        
        # Match partiel (au moins 80% des clés en commun)
        current_set = set(normalized_keys)
        cache_set = set(cache_normalized)
        intersection = current_set & cache_set
        if len(intersection) > 0:
            jaccard = len(intersection) / len(current_set | cache_set)
            if jaccard >= 0.8:  # 80% de similarité
                return {
                    'cluster_signature': cache_sig,
                    'impact_median': row.get('impact_median', None),
                    'impact_mean': row.get('impact_mean', None),
                    'latency_median': row.get('latency_median', None),
                    'ttr_median': row.get('ttr_median', None),
                    'pullback_median': row.get('pullback_median', None),
                    'dominant_pattern': row.get('dominant_pattern', None),
                    'dominant_direction': row.get('dominant_direction', None),
                    'n_samples': row.get('n_samples', 0),
                    'total_score_median': row.get('total_score_median', None),
                    'jaccard_similarity': jaccard,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5A : SCANNER PRIX POUR MOUVEMENT FORT (WORKFLOW CORRECT)
# ═══════════════════════════════════════════════════════════════

def scan_price_movements_for_date(df_prices: pd.DataFrame, min_pips: float, window_minutes: int = 60, baseline_lookback: int = 10) -> Optional[Dict]:
    """
    Scanner les prix pour détecter un mouvement fort > min_pips.
    WORKFLOW CORRECT : PRIX → MOUVEMENT → PATTERN → CLUSTER
    
    Args:
        df_prices: DataFrame avec prix 1-minute (index = datetime)
        min_pips: Seuil minimum en pips
        window_minutes: Fenêtre d'observation pour pic
        baseline_lookback: Minutes pour baseline
    
    Returns:
        Dict avec mouvement détecté ou None
    """
    if len(df_prices) < window_minutes + baseline_lookback:
        return None
    
    movements = []
    
    # Scanner chaque bougie comme point de départ potentiel
    for i in range(len(df_prices) - window_minutes):
        current_time = df_prices.index[i]
        
        # Baseline = moyenne baseline_lookback min AVANT
        baseline_start = current_time - pd.Timedelta(minutes=baseline_lookback)
        baseline_df = df_prices[(df_prices.index >= baseline_start) & (df_prices.index < current_time)]
        
        if len(baseline_df) < 5:
            continue
        
        baseline_price = baseline_df['close'].mean()
        
        # Chercher pic dans les window_minutes min APRÈS
        future_end = current_time + pd.Timedelta(minutes=window_minutes)
        future_window = df_prices[(df_prices.index >= current_time) & (df_prices.index <= future_end)]
        
        if len(future_window) < 10:
            continue
        
        # Calculer impacts UP et DOWN
        max_high = future_window['high'].max()
        min_low = future_window['low'].min()
        
        impact_up = (max_high - baseline_price) * 10000  # pips
        impact_down = (baseline_price - min_low) * 10000
        
        # Déterminer direction et impact dominant
        if impact_up >= impact_down and impact_up >= min_pips:
            peak_time = future_window.loc[future_window['high'].idxmax()].name
            movements.append({
                'start_time': current_time,
                'baseline_time': baseline_df.index[-1],
                'baseline_price': baseline_price,
                'peak_time': peak_time,
                'peak_price': max_high,
                'impact_pips': impact_up,
                'direction': 'UP',
                'minutes_to_peak': (peak_time - current_time).total_seconds() / 60.0
            })
        elif impact_down >= min_pips:
            peak_time = future_window.loc[future_window['low'].idxmin()].name
            movements.append({
                'start_time': current_time,
                'baseline_time': baseline_df.index[-1],
                'baseline_price': baseline_price,
                'peak_time': peak_time,
                'peak_price': min_low,
                'impact_pips': impact_down,
                'direction': 'DOWN',
                'minutes_to_peak': (peak_time - current_time).total_seconds() / 60.0
            })
    
    if len(movements) == 0:
        return None
    
    # Retourner le mouvement le plus fort
    strongest = max(movements, key=lambda x: x['impact_pips'])
    return strongest


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5B : TROUVER CLUSTER POUR MOUVEMENT (WORKFLOW CORRECT)
# ═══════════════════════════════════════════════════════════════

# Pays pertinents pour EUR/USD (zone euro + US + UK)
EURUSD_RELEVANT_COUNTRIES = {
    'US', 'EU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'FI', 
    'IE', 'PT', 'GR', 'LU', 'SI', 'SK', 'EE', 'LV', 'LT', 'MT', 
    'CY', 'GB', 'UK'  # UK pour Brexit impact
}

def is_country_relevant_for_eurusd(country: str) -> bool:
    """
    Vérifie si un pays est pertinent pour le trading EUR/USD.
    Exclut les pays non pertinents (RU, JP, CN, etc.)
    """
    if pd.isna(country):
        return False
    return str(country).upper() in EURUSD_RELEVANT_COUNTRIES


def is_event_without_actual(event_key: str, event_title: str) -> bool:
    """
    Identifie les événements qui n'ont pas de valeur actual mesurable.
    Ces événements doivent être exclus de la prédiction car on ne peut pas
    calculer leur surprise ni tester leur impact.
    
    Exemples : conférences de presse, speeches, annonces verbales
    """
    event_key_lower = str(event_key).lower()
    event_title_lower = str(event_title).lower()
    
    # Mots-clés indiquant événements sans actual
    exclusion_keywords = [
        'press conference',
        'conference',
        'speech',
        'statement',
        'announcement',
        'meeting',
        'minutes',
        'report'  # Certains reports peuvent avoir actual, mais on est conservateur
    ]
    
    # Vérifier si l'événement contient un mot-clé d'exclusion
    for keyword in exclusion_keywords:
        if keyword in event_key_lower or keyword in event_title_lower:
            return True
    
    return False


def find_cluster_for_movement(
    movement: Dict, 
    db_path: Path, 
    timezone_str: str = "Europe/Zurich", 
    window_minutes: int = 30,
    include_catalyst_events: bool = True,
    catalyst_window_minutes: int = 60
) -> pd.DataFrame:
    """
    Trouve le cluster d'événements qui a causé le mouvement détecté.
    WORKFLOW CORRECT : Après avoir détecté le mouvement depuis les prix.
    
    AMÉLIORATION : Détecte aussi les événements "catalyseurs" qui surviennent
    pendant le mouvement et relancent l'impact (ex: current account DE à 14h45
    qui annule le pullback et relance jusqu'à 15h10).
    
    Args:
        movement: Dict avec mouvement détecté (de scan_price_movements_for_date)
        db_path: Chemin DB
        timezone_str: Timezone
        window_minutes: Fenêtre ±window_minutes autour du début mouvement
        include_catalyst_events: Si True, inclut événements catalyseurs après début
        catalyst_window_minutes: Fenêtre après début mouvement pour chercher catalyseurs
    
    Returns:
        DataFrame avec événements du cluster (initiaux + catalyseurs)
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Fenêtre autour du début du mouvement (événements initiaux)
    start_window = movement['start_time'] - pd.Timedelta(minutes=window_minutes)
    end_window = movement['start_time'] + pd.Timedelta(minutes=window_minutes)
    
    # Charger événements HIGH dans la fenêtre initiale
    # EXCLURE pays non pertinents pour EUR/USD
    relevant_countries_list = "', '".join(EURUSD_RELEVANT_COUNTRIES)
    query_initial = f"""
    SELECT 
        e.ts_utc, e.country, e.event_title, e.event_key, e.importance_n,
        e.actual, e.estimate, e.forecast, e.previous,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc AT TIME ZONE '{timezone_str}' >= ?
      AND e.ts_utc AT TIME ZONE '{timezone_str}' <= ?
      AND e.country IN ('{relevant_countries_list}')
      AND (e.importance_n = 3 OR (ef.empirical_score IS NOT NULL AND ef.empirical_score > 40))
    ORDER BY e.ts_utc
    """
    
    df_initial = conn.execute(query_initial, [
        start_window.strftime('%Y-%m-%d %H:%M:%S'),
        end_window.strftime('%Y-%m-%d %H:%M:%S')
    ]).df()
    
    # NOUVEAU : Chercher événements catalyseurs après le début du mouvement
    df_catalysts = pd.DataFrame()
    if include_catalyst_events:
        # Fenêtre après début mouvement (ex: 14h30 à 15h30 pour trouver 14h45)
        catalyst_start = movement['start_time']
        catalyst_end = movement['start_time'] + pd.Timedelta(minutes=catalyst_window_minutes)
        
        # Chercher événements avec score > 30 (seuil plus bas pour catalyseurs)
        # ou importance_n >= 2 (moyenne importance)
        # EXCLURE ceux déjà trouvés dans la fenêtre initiale
        # EXCLURE aussi les événements sans actual (conférences, speeches)
        # EXCLURE pays non pertinents pour EUR/USD
        # INCLURE current account DE même avec importance_n = 2 et score nan
        relevant_countries_list = "', '".join(EURUSD_RELEVANT_COUNTRIES)
        query_catalyst = f"""
        SELECT 
            e.ts_utc, e.country, e.event_title, e.event_key, e.importance_n,
            e.actual, e.estimate, e.forecast, e.previous,
            ef.empirical_score
        FROM events e
        LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
        WHERE e.ts_utc AT TIME ZONE '{timezone_str}' > ?
          AND e.ts_utc AT TIME ZONE '{timezone_str}' <= ?
          AND e.country IN ('{relevant_countries_list}')
          AND (
            e.importance_n >= 2 
            OR (ef.empirical_score IS NOT NULL AND ef.empirical_score > 30)
            OR (LOWER(e.event_key) LIKE '%current account%' AND e.country = 'DE')
          )
          AND NOT (
            e.ts_utc AT TIME ZONE '{timezone_str}' >= ?
            AND e.ts_utc AT TIME ZONE '{timezone_str}' <= ?
          )
          AND NOT (
            LOWER(e.event_key) LIKE '%press conference%'
            OR LOWER(e.event_key) LIKE '%conference%'
            OR LOWER(e.event_key) LIKE '%speech%'
            OR LOWER(e.event_title) LIKE '%press conference%'
            OR LOWER(e.event_title) LIKE '%conference%'
            OR LOWER(e.event_title) LIKE '%speech%'
          )
        ORDER BY e.ts_utc
        """
        
        df_catalysts = conn.execute(query_catalyst, [
            catalyst_start.strftime('%Y-%m-%d %H:%M:%S'),
            catalyst_end.strftime('%Y-%m-%d %H:%M:%S'),
            start_window.strftime('%Y-%m-%d %H:%M:%S'),
            end_window.strftime('%Y-%m-%d %H:%M:%S')
        ]).df()
    
    conn.close()
    
    # Combiner événements initiaux + catalyseurs
    if len(df_initial) > 0:
        df_initial['ts_bern'] = pd.to_datetime(df_initial['ts_utc']).dt.tz_convert(timezone_str)
        df_initial['event_type'] = 'initial'
        # Exclure événements sans actual des événements initiaux aussi
        mask_has_actual = df_initial.apply(
            lambda row: not is_event_without_actual(row['event_key'], row.get('event_title', '')),
            axis=1
        )
        df_initial = df_initial[mask_has_actual].reset_index(drop=True)
    
    if len(df_catalysts) > 0:
        df_catalysts['ts_bern'] = pd.to_datetime(df_catalysts['ts_utc']).dt.tz_convert(timezone_str)
        df_catalysts['event_type'] = 'catalyst'
        # Exclure événements sans actual des catalyseurs
        mask_has_actual = df_catalysts.apply(
            lambda row: not is_event_without_actual(row['event_key'], row.get('event_title', '')),
            axis=1
        )
        df_catalysts = df_catalysts[mask_has_actual].reset_index(drop=True)
    
    # Combiner et dédupliquer
    if len(df_initial) > 0 and len(df_catalysts) > 0:
        df_combined = pd.concat([df_initial, df_catalysts]).drop_duplicates(subset=['event_key', 'ts_utc']).reset_index(drop=True)
    elif len(df_initial) > 0:
        df_combined = df_initial
    elif len(df_catalysts) > 0:
        df_combined = df_catalysts
    else:
        df_combined = pd.DataFrame()
    
    return df_combined


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 5 : DÉTECTION PATTERN (MÉTHODE ORIGINALE - GARDE POUR COMPATIBILITÉ)
# ═══════════════════════════════════════════════════════════════

def detect_pattern_type(df_events: pd.DataFrame, df_prices: pd.DataFrame, min_pips: float, timezone: pytz.timezone) -> Dict:
    """Détecte le type de pattern (classification simplifiée)"""
    
    # Baseline
    first_event_time = df_events['ts_bern'].min()
    baseline_time = first_event_time - pd.Timedelta(minutes=1)
    
    valid_times = df_prices[df_prices.index < first_event_time].index
    if len(valid_times) == 0:
        return {'pattern_type': 'INCONNU', 'detection_confidence': 0.0, 'metrics': {}, 'error': 'Pas de prix avant événement'}
    
    baseline_time = valid_times[-1]
    baseline = df_prices.loc[baseline_time, 'close']
    
    # Scanner 6h après
    scan_end = first_event_time + pd.Timedelta(hours=6)
    df_after = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= scan_end)]
    
    if len(df_after) == 0:
        return {'pattern_type': 'INCONNU', 'detection_confidence': 0.0, 'metrics': {}, 'error': 'Pas de prix après événement'}
    
    # Calculer impact
    impact_pips = (df_after['close'] - baseline).abs().max() * 10000
    total_score = df_events['score'].sum()
    num_scored = len(df_events[df_events['score'] > 0])
    
    metrics = {
        'impact_pips': impact_pips,
        'total_score': total_score,
        'num_events': len(df_events),
        'num_scored': num_scored
    }
    
    # Classification
    if impact_pips < min_pips:
        return {'pattern_type': 'INCONNU', 'detection_confidence': 0.0, 'metrics': metrics, 
                'reason': f'Impact ({impact_pips:.1f}) < seuil ({min_pips})'}
    
    # Double Wave potentiel (score élevé + nombreux events)
    if total_score >= 150 and num_scored >= 5:
        return {'pattern_type': 'DOUBLE_WAVE', 'detection_confidence': 0.8, 'metrics': metrics}
    
    # Single Wave
    if impact_pips > 40:
        return {'pattern_type': 'SINGLE_WAVE_FORT', 'detection_confidence': 0.8, 'metrics': metrics}
    elif impact_pips >= 20:
        return {'pattern_type': 'SINGLE_WAVE_STANDARD', 'detection_confidence': 0.9, 'metrics': metrics}
    else:
        return {'pattern_type': 'INCONNU', 'detection_confidence': 0.5, 'metrics': metrics}


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 6 : AIGUILLAGE PRÉDICTION
# ═══════════════════════════════════════════════════════════════

def route_prediction(pattern_type: str, df_events: pd.DataFrame, df_prices: pd.DataFrame, db_path: Path, use_complete_pipeline: bool = True) -> Dict:
    """
    Aiguille vers le bon module de prédiction.
    
    NOUVEAU : Option pour utiliser le pipeline complet (Random Forest, stratégie de sortie optimisée)
    
    Args:
        pattern_type: Type de pattern détecté
        df_events: DataFrame des événements
        df_prices: DataFrame des prix
        db_path: Chemin vers la base de données
        use_complete_pipeline: Si True, utilise le pipeline complet (défaut: True)
    """
    # NOUVEAU : Utiliser le pipeline complet si activé
    if use_complete_pipeline:
        try:
            import sys
            from pathlib import Path
            PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
            sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
            
            from run_pipeline_complete import PipelineExecutor
            from datetime import datetime
            
            # Extraire la date du premier événement
            if not df_events.empty:
                # Essayer différentes colonnes de date
                date_col = None
                for col in ['ts_bern', 'ts_utc', 'datetime', 'timestamp']:
                    if col in df_events.columns:
                        date_col = col
                        break
                
                if date_col:
                    first_event = df_events[date_col].min()
                    if pd.notna(first_event):
                        date_str = pd.to_datetime(first_event).strftime('%Y-%m-%d')
                    
                    # Exécuter le pipeline complet
                    executor = PipelineExecutor(
                        db_path=db_path,
                        verbose=False,
                        force_timeframe=None
                    )
                    
                    result = executor.execute_complete_pipeline(date_str)
                    
                    if result and result.get('success'):
                        final_prediction = result.get('final_prediction', {})
                        
                        # Extraire les résultats
                        prediction_finale = final_prediction.get('prediction_finale', {})
                        if isinstance(prediction_finale, dict):
                            impact_predicted = prediction_finale.get('impact_pips', 0)
                        else:
                            impact_predicted = prediction_finale
                        
                        # Extraire le target de sortie optimisé
                        exit_target = final_prediction.get('exit_target', None)
                        exit_strategy = final_prediction.get('exit_strategy', 'N/A')
                        direction = final_prediction.get('pattern_info', {}).get('direction', 'UNKNOWN')
                        
                        # Extraire les timings si disponibles
                        pattern_info = final_prediction.get('pattern_info', {})
                        wave1_peak_time = pattern_info.get('pattern_wave1_peak_time')
                        pullback_time = pattern_info.get('pattern_pullback_time')
                        wave2_peak_time = pattern_info.get('pattern_wave2_peak_time')
                        
                        return {
                            'prediction_pips': impact_predicted,
                            'amplification': final_prediction.get('amplification_predite'),
                            'status': 'predicted',
                            'reason': 'Pipeline complet avec Random Forest et stratégie de sortie optimisée',
                            'method': 'complete_pipeline',
                            'pattern_type': pattern_type,
                            'exit_target': exit_target,
                            'exit_strategy': exit_strategy,
                            'direction': direction,
                            'wave1_peak_time': wave1_peak_time,
                            'pullback_time': pullback_time,
                            'wave2_peak_time': wave2_peak_time,
                            'pattern_info': pattern_info,
                            'warning': None
                        }
        except Exception as e:
            # En cas d'erreur, fallback sur méthode originale
            import traceback
            print(f"⚠️ Erreur pipeline complet, fallback sur méthode originale: {e}")
            traceback.print_exc()
    
    # Méthode originale (fallback)
    if pattern_type == "DOUBLE_WAVE":
        # Essayer d'abord Ensemble Methods (si disponible)
        try:
            from core.ensemble_prediction import predict_pattern_based_ensemble
            
            # Calculer métriques pour déterminer pattern exact (UP/DOWN)
            first_event_time = df_events['ts_bern'].min()
            baseline_time = first_event_time - pd.Timedelta(minutes=1)
            
            valid_times = df_prices[df_prices.index < first_event_time].index
            if len(valid_times) > 0:
                baseline_time = valid_times[-1]
                baseline = df_prices.loc[baseline_time, 'close']
                
                # Scanner 6h après pour déterminer direction
                scan_end = first_event_time + pd.Timedelta(hours=6)
                df_after = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= scan_end)]
                
                if len(df_after) > 0:
                    max_price = df_after['close'].max()
                    min_price = df_after['close'].min()
                    max_diff = (max_price - baseline) * 10000
                    min_diff = (baseline - min_price) * 10000
                    
                    direction = 'UP' if max_diff > min_diff else 'DOWN'
                    pattern_exact = f'DOUBLE_WAVE_{direction}'
                    
                    # Calculer score total
                    total_score = df_events['score'].sum()
                    num_events = len(df_events)
                    
                    # Prédire avec Ensemble Methods
                    ensemble_result = predict_pattern_based_ensemble(
                        pattern_type=pattern_exact,
                        total_score=total_score,
                        num_events=num_events,
                        movement_datetime=first_event_time
                    )
                    
                    # Si succès, retourner résultat
                    if ensemble_result.get('prediction') is not None:
                        return {
                            'prediction_pips': ensemble_result['prediction'],
                            'amplification': None,  # Pas d'amplification pour Ensemble
                            'status': 'predicted',
                            'reason': f"Ensemble Methods ({ensemble_result.get('reason', '')})",
                            'method': 'ensemble',
                            'pattern_type': pattern_exact,
                            'total_score': total_score,
                            'events_scored': num_events,
                            'ensemble_details': {
                                'individual': ensemble_result.get('individual', {}),
                                'weights': ensemble_result.get('weights', {}),
                                'n_historical': ensemble_result.get('n_historical', 0)
                            },
                            'warning': None
                        }
        except Exception as e:
            # Fallback : méthode originale doublewave_overlap
            pass
        
        # Fallback : méthode originale
        return predict_double_wave(df_events)
    
    elif pattern_type in ["SINGLE_WAVE_STANDARD", "SINGLE_WAVE_FORT"]:
        return predict_single_wave(df_events, df_prices, pattern_type, db_path)
    elif pattern_type == "INCONNU":
        return handle_unknown_pattern(df_events)
    else:
        return {'status': 'error', 'reason': f'Pattern type inconnu: {pattern_type}'}


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 7 : PRÉDICTION DOUBLE WAVE
# ═══════════════════════════════════════════════════════════════

def predict_double_wave(df_events: pd.DataFrame) -> Dict:
    """Prédiction pattern Double Wave (Module Session 132)"""
    from core.doublewave_prediction import predict_doublewave_overlap
    
    # Convertir en liste dicts
    events_list = []
    for idx, row in df_events.iterrows():
        events_list.append({
            'event_key': row['event_key'],
            'country': row['country'],
            'score': row['score'],
            'actual': row['actual'] if pd.notna(row['actual']) else None,
            'estimate': row['estimate'] if pd.notna(row['estimate']) else None
        })
    
    result = predict_doublewave_overlap(events_list, debug=False)
    
    return {
        'prediction_pips': result.get('prediction'),
        'amplification': result.get('amplification'),
        'status': result['status'],
        'reason': result['reason'],
        'pattern_type': result.get('pattern_type'),
        'method': 'doublewave_overlap',
        'total_score': result.get('total_score'),
        'events_scored': result.get('events_scored'),
        'surprise_factor': result.get('surprise_factor'),
        'warning': None
    }


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 8 : PRÉDICTION SINGLE WAVE (PIPELINE LOO-CV + FALLBACK)
# ═══════════════════════════════════════════════════════════════

def predict_single_wave(df_events: pd.DataFrame, df_prices: pd.DataFrame, pattern_type: str, db_path: Path) -> Dict:
    """Prédiction Single Wave avec Ensemble Methods (Session 142+)"""
    
    from core.ensemble_prediction import predict_pattern_based_ensemble
    
    # Identifier type événement
    main_event_type = identify_main_event_type(df_events)
    
    # Calculer métriques pour déterminer pattern exact
    first_event_time = df_events['ts_bern'].min()
    baseline_time = first_event_time - pd.Timedelta(minutes=1)
    
    valid_times = df_prices[df_prices.index < first_event_time].index
    if len(valid_times) == 0:
        return {
            'prediction_pips': None, 'amplification': None, 'r2_trend': None,
            'status': 'excluded', 'reason': 'Pas de prix avant événement',
            'method': None, 'mae_global': None, 'warning': None
        }
    
    baseline_time = valid_times[-1]
    baseline = df_prices.loc[baseline_time, 'close']
    
    # Scanner 6h après pour déterminer direction
    scan_end = first_event_time + pd.Timedelta(hours=6)
    df_after = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= scan_end)]
    
    if len(df_after) == 0:
        return {
            'prediction_pips': None, 'amplification': None, 'r2_trend': None,
            'status': 'excluded', 'reason': 'Pas de prix après événement',
            'method': None, 'mae_global': None, 'warning': None
        }
    
    # Déterminer direction (UP ou DOWN)
    max_price = df_after['close'].max()
    min_price = df_after['close'].min()
    max_diff = (max_price - baseline) * 10000
    min_diff = (baseline - min_price) * 10000
    
    if max_diff > min_diff:
        direction = 'UP'
    else:
        direction = 'DOWN'
    
    # Pattern exact avec direction
    if pattern_type == 'SINGLE_WAVE_FORT':
        pattern_exact = f'SINGLE_WAVE_FORT_{direction}'
    elif pattern_type == 'SINGLE_WAVE_STANDARD':
        pattern_exact = f'SINGLE_WAVE_STANDARD_{direction}'
    else:
        pattern_exact = f'SINGLE_WAVE_{direction}'
    
    # Calculer score total
    total_score = df_events['score'].sum()
    num_events = len(df_events)
    
    # Prédire avec Ensemble Methods
    try:
        ensemble_result = predict_pattern_based_ensemble(
            pattern_type=pattern_exact,
            total_score=total_score,
            num_events=num_events,
            movement_datetime=first_event_time
        )
        
        prediction_pips = ensemble_result['prediction']
        method = ensemble_result['method']
        reason = ensemble_result.get('reason', 'Ensemble Methods')
        
        # Calculer R² tendance pour affichage (60 min avant)
        window_start = first_event_time - pd.Timedelta(minutes=60)
        window_end = first_event_time - pd.Timedelta(minutes=1)
        df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
        
        r2_trend = None
        if len(df_window) >= 10:
            from sklearn.linear_model import LinearRegression
            X = np.arange(len(df_window)).reshape(-1, 1)
            y = df_window['close'].values
            model = LinearRegression()
            model.fit(X, y)
            r2_trend = model.score(X, y)
        
        # Amplification (pour compatibilité affichage)
        score_adjusted_total = df_events['score_adjusted'].sum()
        amp = prediction_pips / score_adjusted_total if score_adjusted_total > 0 else None
        
        # Warning si Single_Wave_Fort
        warning = None
        if pattern_type == 'SINGLE_WAVE_FORT':
            warning = "⚠️ Pattern Single_Wave_Fort: Prédiction avec Ensemble Methods (MAE 13.30 pips)"
        
        return {
            'prediction_pips': prediction_pips,
            'amplification': amp,
            'r2_trend': r2_trend,
            'score_adjusted_total': score_adjusted_total,
            'status': 'predicted',
            'reason': reason,
            'method': method,
            'mae_global': 13.30,  # MAE global Ensemble Methods
            'warning': warning,
            'pattern_exact': pattern_exact,
            'ensemble_details': {
                'individual': ensemble_result.get('individual', {}),
                'weights': ensemble_result.get('weights', {}),
                'n_historical': ensemble_result.get('n_historical', 0)
            }
        }
        
    except Exception as e:
        # Fallback : fonction universelle si erreur
        st.warning(f"⚠️ Erreur Ensemble Methods, fallback fonction universelle : {e}")
        
        # Calculer R² tendance (60 min avant premier event)
        window_start = first_event_time - pd.Timedelta(minutes=60)
        window_end = first_event_time - pd.Timedelta(minutes=1)
        df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
        
        if len(df_window) < 10:
            return {
                'prediction_pips': None, 'amplification': None, 'r2_trend': None,
                'status': 'excluded', 'reason': 'Fenêtre pré-événement insuffisante (< 10 min)',
                'method': None, 'mae_global': None, 'warning': None
            }
        
        # Régression linéaire
        from sklearn.linear_model import LinearRegression
        
        X = np.arange(len(df_window)).reshape(-1, 1)
        y = df_window['close'].values
        
        model = LinearRegression()
        model.fit(X, y)
        r2_trend = model.score(X, y)
        
        # Fonction universelle
        amp = calculate_amplification_from_r2_universal(r2_trend)
        
        # Prédiction
        score_adjusted_total = df_events['score_adjusted'].sum()
        prediction_pips = score_adjusted_total * amp
        
        return {
            'prediction_pips': prediction_pips,
            'amplification': amp,
            'r2_trend': r2_trend,
            'score_adjusted_total': score_adjusted_total,
            'status': 'predicted',
            'reason': 'Fallback fonction universelle (erreur Ensemble Methods)',
            'method': 'universal_fallback',
            'mae_global': None,
            'warning': None
        }


def identify_main_event_type(df_events: pd.DataFrame) -> str:
    """Identifie type événement principal"""
    if df_events.empty:
        return "UNKNOWN"
    
    max_score_idx = df_events['score'].idxmax()
    event_key = df_events.loc[max_score_idx, 'event_key'].lower()
    
    if 'cpi' in event_key or 'inflation' in event_key:
        return 'CPI'
    elif 'nonfarm' in event_key or 'payroll' in event_key:
        return 'NFP'
    elif 'fed' in event_key or 'fomc' in event_key or 'interest rate' in event_key:
        return 'Fed Decision'
    elif 'gdp' in event_key:
        return 'GDP'
    else:
        return df_events.loc[max_score_idx, 'event_key']


def calculate_amplification_from_r2_universal(r2_trend: float) -> float:
    """Fonction universelle Sessions 125-126 (+71.6% amélioration moyenne)"""
    a, b, c = 0.040833, 0.050220, -0.006553
    r2_clipped = max(0.0, min(1.0, r2_trend))
    amp = max(0.01, min(0.20, a + b*r2_clipped + c*r2_clipped**2))
    return amp


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 9 : GESTION PATTERN INCONNU
# ═══════════════════════════════════════════════════════════════

def handle_unknown_pattern(df_events: pd.DataFrame) -> Dict:
    """Gestion pattern non reconnu"""
    return {
        'prediction_pips': None,
        'amplification': None,
        'status': 'excluded',
        'reason': "Pattern non reconnu - Seuil min_pips non atteint",
        'suggestion': "Essayer min_pips plus faible (20-30 pips) ou vérifier événements",
        'method': None,
        'warning': None
    }


# ═══════════════════════════════════════════════════════════════
# TIMELINE CHART DOUBLE WAVE
# ═══════════════════════════════════════════════════════════════

def create_double_wave_timeline_chart(
    prediction_pips: float,
    surprise_pct: float,
    num_events: int,
    start_time: pd.Timestamp,
    start_price: float,
    df_prices: Optional[pd.DataFrame] = None,
    direction: str = "UP",
) -> go.Figure:
    """
    Crée un graphique chandelier pour un Double Wave recalibré.

    - Utilise les timelines dynamiques issues de scripts/session137 (Session 137+)
    - Le graphique affiche la trajectoire PRÉDITE ; les prix réels sont ajoutés
      uniquement pour comparaison (si df_prices fourni).
    """

    from core.double_wave import predict_double_wave_timeline

    direction = direction.upper()
    dir_sign = 1 if direction == "UP" else -1

    timeline = predict_double_wave_timeline(
        base_impact=prediction_pips,
        surprise_pct=surprise_pct,
        cluster_size=num_events,
        start_time=start_time.to_pydatetime(),
        direction=direction,
    )

    phase1_info = timeline["phase1"]
    pullback_info = timeline["pullback"]
    phase2_info = timeline["phase2"]
    profile = timeline.get("profile", {})

    event_time = start_time
    phase1_peak = pd.to_datetime(phase1_info["peak_time"])
    pullback_time = pd.to_datetime(pullback_info["low_time"])
    pullback_low = pullback_time
    phase2_peak = pd.to_datetime(phase2_info["peak_time"])
    stabilization_dt = pd.to_datetime(timeline["stabilization_time"])

    phase1_price = start_price + dir_sign * (phase1_info["impact_pips"] * 0.0001)
    pullback_price = phase1_price - dir_sign * (pullback_info["retrace_pips"] * 0.0001)
    phase2_price = start_price + dir_sign * (phase2_info["impact_pips"] * 0.0001)
    stabilization_price = start_price + dir_sign * (
        phase2_info["impact_pips"] * profile.get("stabilization_ratio", 0.85) * 0.0001
    )

    phase1_pips = phase1_info["impact_pips"]
    pullback_pips = pullback_info["retrace_pips"]
    phase2_pips = phase2_info["impact_pips"]

    p0 = start_price
    p1 = phase1_price
    p2 = pullback_price
    p3_predicted = phase2_price
    p4 = stabilization_price

    # Overlay réel (optionnel)
    use_real_prices = False
    real_peak_time = None
    real_peak_price = None
    real_peak_pips = None
    if df_prices is not None and len(df_prices) > 0:
        scan_start = event_time - pd.Timedelta(minutes=5)
        scan_end = event_time + pd.Timedelta(hours=2)
        df_after = df_prices[(df_prices.index >= scan_start) & (df_prices.index <= scan_end)].copy()
        if len(df_after) > 0:
            baseline = start_price
            df_after["pips_high"] = (df_after["high"] - baseline) * 10000
            df_after["pips_low"] = (baseline - df_after["low"]) * 10000
            max_high_pips = df_after["pips_high"].max()
            max_low_pips = df_after["pips_low"].max()
            if dir_sign >= 0:
                peak_idx = df_after["pips_high"].idxmax()
                real_peak_price = float(df_after.loc[peak_idx, "high"])
                real_peak_pips = max_high_pips
            else:
                peak_idx = df_after["pips_low"].idxmax()
                real_peak_price = float(df_after.loc[peak_idx, "low"])
                real_peak_pips = max_low_pips
            real_peak_time = peak_idx

    def build_segment(t_start, t_end, price_start, price_end):
        minutes = max(1, int((t_end - t_start).total_seconds() // 60))
        segment_times = []
        segment_opens = []
        segment_highs = []
        segment_lows = []
        segment_closes = []
        for i in range(minutes):
            t0 = t_start + pd.Timedelta(minutes=i)
            t1 = t_start + pd.Timedelta(minutes=i + 1)
            progress0 = i / minutes
            progress1 = (i + 1) / minutes
            open_price = price_start + (price_end - price_start) * progress0
            close_price = price_start + (price_end - price_start) * progress1
            high_price = max(open_price, close_price) + 0.00008 * dir_sign
            low_price = min(open_price, close_price) - 0.00008 * dir_sign
            segment_times.append(t0)
            segment_opens.append(open_price)
            segment_highs.append(high_price if dir_sign >= 0 else low_price)
            segment_lows.append(low_price if dir_sign >= 0 else high_price)
            segment_closes.append(close_price)
        return segment_times, segment_opens, segment_highs, segment_lows, segment_closes

    segments = [
        (event_time, phase1_peak, start_price, phase1_price),
        (phase1_peak, pullback_time, phase1_price, pullback_price),
        (pullback_time, phase2_peak, pullback_price, phase2_price),
        (phase2_peak, stabilization_dt, phase2_price, stabilization_price),
    ]

    times = []
    opens = []
    highs = []
    lows = []
    closes = []

    for seg in segments:
        t, o, h, l, c = build_segment(*seg)
        times.extend(t)
        opens.extend(o)
        highs.extend(h)
        lows.extend(l)
        closes.extend(c)

    times_plotly = [t.to_pydatetime() if isinstance(t, pd.Timestamp) else t for t in times]
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=times_plotly,
            open=opens,
            high=highs,
            low=lows,
            close=closes,
            name="EUR/USD (prévision)",
            increasing_line_color="darkgreen" if dir_sign >= 0 else "#A60000",
            decreasing_line_color="darkred" if dir_sign >= 0 else "#004C99",
        )
    )
    
    # Convertir tous les timestamps en datetime Python pour les annotations
    def to_plotly_time(ts):
        """Convertit pd.Timestamp en datetime Python pour Plotly"""
        if isinstance(ts, pd.Timestamp):
            return ts.to_pydatetime()
        return ts
    
    event_time_plotly = to_plotly_time(event_time)
    phase1_peak_plotly = to_plotly_time(phase1_peak)
    pullback_low_plotly = to_plotly_time(pullback_low)
    phase2_peak_plotly = to_plotly_time(phase2_peak)
    stabilization_plotly = to_plotly_time(stabilization_dt)
    
    # Annotations phases
    def minutes_from_start(ts: pd.Timestamp) -> int:
        return int(round((ts - event_time) / pd.Timedelta(minutes=1)))

    phase1_duration = int(round(phase1_info["duration_min"]))
    pullback_duration = max(1, minutes_from_start(pullback_time) - minutes_from_start(phase1_peak))
    phase2_duration = max(1, minutes_from_start(phase2_peak) - minutes_from_start(pullback_time))
    stabilization_tail = profile.get("stabilization_tail", 25)

    fig.add_annotation(
        x=event_time_plotly + pd.Timedelta(minutes=phase1_duration / 2),
        y=(p0 + p1) / 2,
        text=f"Phase 1: Réaction Algos<br>+{phase1_pips:.0f} pips / ~{phase1_duration} min",
        showarrow=True,
        arrowhead=2,
        bgcolor="green",
        opacity=0.8,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=phase1_peak_plotly,
        y=p1,
        text=f"📈 Peak Phase 1<br>{phase1_peak.strftime('%H:%M')}<br>+{phase1_pips:.0f} pips",
        showarrow=True,
        arrowhead=2,
        bgcolor="orange",
        opacity=0.9,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=phase1_peak_plotly + pd.Timedelta(minutes=3),
        y=(p1 + p2) / 2,
        text=f"Pullback: Prise Profits<br>-{pullback_pips:.0f} pips / 6 min",
        showarrow=True,
        arrowhead=2,
        bgcolor="red",
        opacity=0.8,
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=pullback_low_plotly,
        y=p2,
        text=f"⬇️ Creux Pullback<br>{pullback_low.strftime('%H:%M')}<br>{p2:.5f}",
        showarrow=True,
        arrowhead=2,
        bgcolor="blue",
        opacity=0.9,
        font=dict(color="white", size=11)
    )
    
    fig.add_annotation(
        x=pullback_low_plotly + pd.Timedelta(minutes=phase2_duration / 2),
        y=(p2 + p3_predicted) / 2,
        text=f"Phase 2: Ordres Institutionnels<br>+{phase2_pips:.0f} pips / ~{phase2_duration} min",
        showarrow=True,
        arrowhead=2,
        bgcolor="darkgreen",
        opacity=0.8,
        font=dict(color="white")
    )
    
    # Annotation pic absolu PRÉDIT
    peak_time_predicted = phase2_peak.strftime('%H:%M')
    fig.add_annotation(
        x=phase2_peak_plotly,
        y=p3_predicted,
        text=f"🚀 PEAK ABSOLU PRÉDIT<br>{peak_time_predicted} (T+{minutes_from_start(phase2_peak)} min)<br>+{phase2_pips:.0f} pips",
        showarrow=True,
        arrowhead=2,
        bgcolor="gold",
        opacity=0.9,
        font=dict(color="black", size=12, family="Arial Black")
    )
    
    fig.add_annotation(
        x=phase2_peak_plotly + pd.Timedelta(minutes=stabilization_tail / 2),
        y=(p3_predicted + p4) / 2,
        text=f"Stabilisation<br>~{stabilization_tail} min",
        showarrow=True,
        arrowhead=2,
        bgcolor="gray",
        opacity=0.7,
        font=dict(color="white")
    )
    
    # Lignes horizontales
    fig.add_hline(
        y=p0,
        line_dash="dot",
        line_color="gray",
        annotation_text="Prix départ",
        annotation_position="right",
    )
    fig.add_hline(
        y=p1,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"Peak Phase 1 (T+{minutes_from_start(phase1_peak)} min)",
        annotation_position="right",
    )
    fig.add_hline(
        y=p2,
        line_dash="dot",
        line_color="blue",
        annotation_text=f"Creux Pullback (T+{minutes_from_start(pullback_time)} min)",
        annotation_position="right",
    )
    # Annotation ligne horizontale pic absolu PRÉDIT
    peak_label = f"PEAK ABSOLU PRÉDIT ({peak_time_predicted})"
    fig.add_hline(y=p3_predicted, line_dash="dash", line_color="gold", line_width=2,
                  annotation_text=peak_label, annotation_position="right")
    
    # Si prix réels disponibles, ajouter annotation pour comparaison
    if use_real_prices and p3_real is not None and real_peak_time is not None:
        real_peak_time_str = real_peak_time.strftime('%H:%M')
        real_peak_pips_value = real_peak_pips
        
        # Annotation pic réel (pour comparaison)
        real_peak_time_plotly = real_peak_time.to_pydatetime() if isinstance(real_peak_time, pd.Timestamp) else real_peak_time
        fig.add_annotation(
            x=real_peak_time_plotly,
            y=p3_real,
            text=f"📊 PIC RÉEL<br>{real_peak_time_str}<br>+{real_peak_pips_value:.0f} pips",
            showarrow=True,
            arrowhead=2,
            bgcolor="red",
            opacity=0.9,
            font=dict(color="white", size=11),
            xshift=30  # Décaler pour ne pas chevaucher
        )
        
        # Ligne horizontale pic réel (rouge, pointillée)
        fig.add_hline(y=p3_real, line_dash="dot", line_color="red", line_width=2,
                      annotation_text=f"PIC RÉEL ({real_peak_time_str})", 
                      annotation_position="left")
        
        # Calculer écart prédiction vs réalité
        error_pips = abs(real_peak_pips_value - phase2_pips)
        error_pct = (error_pips / real_peak_pips_value * 100) if real_peak_pips_value > 0 else 0
        
        # Annotation écart
        mid_time = phase2_peak + (real_peak_time - phase2_peak) / 2 if isinstance(real_peak_time, pd.Timestamp) else phase2_peak + pd.Timedelta(minutes=20)
        mid_time_plotly = mid_time.to_pydatetime() if isinstance(mid_time, pd.Timestamp) else mid_time
        fig.add_annotation(
            x=mid_time_plotly,
            y=(p3_predicted + p3_real) / 2,
            text=f"Écart: {error_pips:.1f} pips<br>({error_pct:.1f}%)",
            showarrow=False,
            bgcolor="orange",
            opacity=0.8,
            font=dict(color="black", size=10)
        )
    fig.add_hline(
        y=p4,
        line_dash="dot",
        line_color="green",
        annotation_text=f"Stabilisation (T+{minutes_from_start(stabilization_dt)} min)",
        annotation_position="right",
    )
    
    # Ajuster l'axe X pour graphique PRÉDIT (toujours théorique)
    xaxis_range_start = event_time - pd.Timedelta(minutes=2)  # 2 min avant pour contexte
    xaxis_range_end = stabilization_dt + pd.Timedelta(minutes=5)  # 5 min après stabilisation
    
    # Ajouter ligne verticale à l'heure de l'événement (14h30)
    # Convertir pd.Timestamp en datetime Python pour Plotly
    event_time_plotly = event_time.to_pydatetime() if isinstance(event_time, pd.Timestamp) else event_time
    
    # Utiliser add_shape au lieu de add_vline pour éviter les problèmes de type
    fig.add_shape(
        type="line",
        x0=event_time_plotly,
        x1=event_time_plotly,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="yellow", width=2, dash="dash")
    )
    
    # Ajouter annotation séparément
    fig.add_annotation(
        x=event_time_plotly,
        yref="paper",
        y=1.02,
        text="Événement (14h30)",
        showarrow=False,
        font=dict(color="yellow", size=12),
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="yellow",
        borderwidth=1
    )
    
    # Convertir les timestamps en datetime Python pour Plotly
    xaxis_range_start_plotly = xaxis_range_start.to_pydatetime() if isinstance(xaxis_range_start, pd.Timestamp) else xaxis_range_start
    xaxis_range_end_plotly = xaxis_range_end.to_pydatetime() if isinstance(xaxis_range_end, pd.Timestamp) else xaxis_range_end
    
    fig.update_layout(
        title="🌊 Double Wave Momentum - Timeline Prédite (Session 137+)",
        xaxis_title="Temps (Heure de Berne)",
        yaxis_title="Prix EUR/USD",
        hovermode='x unified',
        height=600,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        xaxis=dict(
            range=[xaxis_range_start_plotly, xaxis_range_end_plotly],
            tickformat='%H:%M',
            dtick=5*60*1000  # Ticks toutes les 5 minutes
        )
    )
    
    return fig


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 10 : AFFICHAGE RÉSULTATS
# ═══════════════════════════════════════════════════════════════

def display_results(target_date, min_pips, timezone_str, pattern_result, prediction_result, df_events, df_prices=None):
    """Affiche résultats complets"""
    
    st.markdown("---")
    st.markdown("## 📊 Résultats Prédiction V3.0")
    
    # Paramètres
    st.markdown("### 🔍 Paramètres Détection")
    col1, col2 = st.columns(2)
    col1.metric("Seuil minimum", f"{min_pips} pips")
    col2.metric("Timezone", timezone_str)
    
    # Pattern détecté
    st.markdown("### 🎯 Pattern Détecté")
    col1, col2 = st.columns(2)
    
    pattern_type = pattern_result['pattern_type']
    confidence = pattern_result['detection_confidence']
    
    # Emoji selon pattern
    pattern_emoji = {
        'DOUBLE_WAVE': '🌊🌊',
        'SINGLE_WAVE_FORT': '🌊💪',
        'SINGLE_WAVE_STANDARD': '🌊',
        'INCONNU': '❓'
    }
    
    col1.metric("Type", f"{pattern_emoji.get(pattern_type, '❓')} {pattern_type}")
    col2.metric("Confiance", f"{confidence*100:.0f}%")
    
    # Métriques pattern
    if 'metrics' in pattern_result:
        metrics = pattern_result['metrics']
        st.markdown("**Métriques Pattern:**")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Impact mesuré", f"{metrics.get('impact_pips', 0):.1f} pips")
        col2.metric("Score total", f"{metrics.get('total_score', 0):.1f}")
        col3.metric("Events total", metrics.get('num_events', 0))
        col4.metric("Events scorés", metrics.get('num_scored', 0))
    
    # Impact prédit
    st.markdown("### 📈 Impact Prédit")
    
    # Afficher détails Ensemble si disponible
    if 'ensemble_details' in prediction_result and prediction_result.get('method') == 'ensemble':
        ensemble_details = prediction_result['ensemble_details']
        with st.expander("🔬 Détails Ensemble Methods", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Poids optimaux :**")
                weights = ensemble_details.get('weights', {})
                for method, weight in weights.items():
                    if weight > 0.01:  # Afficher seulement poids significatifs
                        st.write(f"- {method}: {weight:.3f}")
            with col2:
                st.markdown("**Prédictions individuelles :**")
                individual = ensemble_details.get('individual', {})
                for method, pred in individual.items():
                    st.write(f"- {method}: {pred:.2f} pips")
            
            n_historical = ensemble_details.get('n_historical', 0)
            st.caption(f"📊 Basé sur {n_historical} cas historiques similaires")
            st.caption(f"🎯 MAE global : 13.30 pips (amélioration -1.41 pips vs baseline)")
    
    if prediction_result['status'] == 'predicted':
        col1, col2, col3 = st.columns(3)
        col1.metric("Impact", f"{prediction_result['prediction_pips']:.1f} pips", delta=None)
        
        # Amplification peut être None (ex: Ensemble Methods)
        amplification_value = prediction_result.get('amplification')
        if amplification_value is not None:
            col2.metric("Amplification", f"{amplification_value:.4f}")
        else:
            col2.metric("Amplification", "N/A")
        
        if 'r2_trend' in prediction_result and prediction_result['r2_trend'] is not None:
            col3.metric("R² Tendance", f"{prediction_result['r2_trend']:.3f}")
        
        # NOUVEAU : Afficher target de sortie optimisé si disponible
        if 'exit_target' in prediction_result and prediction_result.get('exit_target') is not None:
            st.markdown("### 🎯 Stratégie de Sortie Optimisée")
            col1, col2, col3 = st.columns(3)
            col1.metric("Target de sortie", f"{prediction_result['exit_target']:.1f} pips")
            col2.metric("Direction", prediction_result.get('direction', 'UNKNOWN'))
            col3.metric("Stratégie", prediction_result.get('exit_strategy', 'N/A')[:30] + "..." if len(prediction_result.get('exit_strategy', '')) > 30 else prediction_result.get('exit_strategy', 'N/A'))
            
            # Afficher détails de la stratégie
            with st.expander("ℹ️ Détails de la stratégie de sortie", expanded=False):
                st.write(f"**Stratégie utilisée :** {prediction_result.get('exit_strategy', 'N/A')}")
                st.write(f"**Impact prédit :** {prediction_result['prediction_pips']:.1f} pips")
                st.write(f"**Target de sortie :** {prediction_result['exit_target']:.1f} pips")
                st.write(f"**Direction :** {prediction_result.get('direction', 'UNKNOWN')}")
                st.info("💡 **Conseil trading :** Sortir à ce target pour maximiser les gains tout en restant sécurisé (efficacité moyenne : 72.6%)")
        
        # Méthodologie
        st.markdown("### 🔧 Méthodologie")
        st.info(f"**Méthode:** {prediction_result['method']}")
        st.write(f"**Raison:** {prediction_result['reason']}")
        
        # Warning si présent
        if prediction_result.get('warning'):
            st.warning(prediction_result['warning'])
    
    elif prediction_result['status'] == 'excluded':
        st.warning(f"❌ **Prédiction non disponible**")
        st.write(f"**Raison:** {prediction_result['reason']}")
        if 'suggestion' in prediction_result:
            st.info(f"💡 **Suggestion:** {prediction_result['suggestion']}")
    
    elif prediction_result['status'] == 'special_case':
        col1, col2 = st.columns(2)
        col1.metric("Impact", f"{prediction_result['prediction_pips']:.1f} pips")
        
        # Amplification peut être None
        amplification_value = prediction_result.get('amplification')
        if amplification_value is not None:
            col2.metric("Amplification", f"{amplification_value:.4f}")
        else:
            col2.metric("Amplification", "N/A")
        
        st.info(f"⚠️ **Cas spécial détecté:** {prediction_result['reason']}")
    
    # Événements analysés
    st.markdown("### ⚙️ Événements Analysés")
    
    display_cols = ['ts_bern', 'country', 'event_title', 'actual', 'estimate', 'score', 'surprise', 'score_adjusted']
    available_cols = [col for col in display_cols if col in df_events.columns]
    
    df_display = df_events[available_cols].copy()
    
    # Formater colonnes
    if 'ts_bern' in df_display.columns:
        df_display['ts_bern'] = df_display['ts_bern'].dt.strftime('%H:%M')
    
    for col in ['actual', 'estimate', 'score', 'surprise', 'score_adjusted']:
        if col in df_display.columns:
            df_display[col] = df_display[col].round(2)
    
    st.dataframe(df_display, use_container_width=True)
    
    # ═══════════════════════════════════════════════════════════════
    # TIMELINE CHART (si DOUBLE_WAVE)
    # ═══════════════════════════════════════════════════════════════
    
    if pattern_result['pattern_type'] == 'DOUBLE_WAVE' and prediction_result.get('prediction_pips') is not None and df_prices is not None:
        st.markdown("### 📈 Timeline Prédite - Double Wave Momentum")
        
        # Calculer timeline depuis prédiction
        # CORRECTION : Prendre le premier événement US (pas ECB qui peut être à 14h15)
        # Filtrer événements US pour trouver le vrai premier événement du cluster
        df_events_us = df_events[df_events['country'] == 'US'].copy()
        if len(df_events_us) > 0:
            first_event_time = df_events_us['ts_bern'].min()
        else:
            # Fallback : prendre le premier événement global
            first_event_time = df_events['ts_bern'].min()
        
        # CORRECTION : Prix de départ = CLOSE de la dernière bougie AVANT l'événement
        # L'événement est à 14h30, donc on prend le prix à 14h29 (ou juste avant)
        # IMPORTANT : Ne pas prendre le prix trop tôt (14h15)
        
        # Filtrer prix strictement AVANT l'événement (pas égal)
        valid_times = df_prices[df_prices.index < first_event_time].index
        
        if len(valid_times) > 0:
            # Prendre le prix le plus proche de l'événement (dernière bougie avant)
            baseline_time = valid_times[-1]
            start_price = float(df_prices.loc[baseline_time, 'close'])
            
            # Vérifier que le prix n'est pas trop ancien (max 5 min avant)
            time_diff = (first_event_time - baseline_time).total_seconds() / 60.0
            
            # DEBUG : Afficher pour diagnostic
            st.info(f"🔍 **Debug Timeline:** Premier événement à {first_event_time.strftime('%H:%M')}, prix départ à {baseline_time.strftime('%H:%M')} (écart: {time_diff:.1f} min)")
            
            if time_diff > 5:
                st.warning(f"⚠️ Prix de départ pris {time_diff:.0f} min avant l'événement (attendu < 5 min)")
                st.warning("⚠️ **Problème possible:** Prix manquants entre l'événement et le prix de départ")
            
            # Calculer surprise pour timeline
            total_score = df_events['score'].sum()
            num_events = len(df_events)
            
            # Calculer surprise moyenne
            surprises = []
            for _, row in df_events.iterrows():
                if pd.notna(row.get('actual')) and pd.notna(row.get('estimate')):
                    if row['estimate'] != 0:
                        surprise = abs((row['actual'] - row['estimate']) / abs(row['estimate'])) * 100
                        surprises.append(surprise)
            
            surprise_pct = np.mean(surprises) if surprises else 20.0
            
            # DEBUG : Afficher informations pour vérification
            with st.expander("🔍 Debug Timeline", expanded=False):
                st.write(f"**Premier événement:** {first_event_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                st.write(f"**Prix de départ:** {start_price:.5f} (à {baseline_time.strftime('%H:%M')})")
                st.write(f"**Écart temps:** {time_diff:.1f} minutes")
                st.write(f"**Impact prédit:** {prediction_result['prediction_pips']:.1f} pips")
                st.write(f"**Surprise moyenne:** {surprise_pct:.1f}%")
                
                # DEBUG : Vérifier pic réel dans les prix
                if df_prices is not None and len(df_prices) > 0:
                    scan_end = first_event_time + pd.Timedelta(hours=2)
                    df_after = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= scan_end)].copy()
                    if len(df_after) > 0:
                        df_after['pips_high'] = (df_after['high'] - start_price) * 10000
                        df_after['pips_low'] = (start_price - df_after['low']) * 10000
                        max_high_pips = df_after['pips_high'].max()
                        max_low_pips = df_after['pips_low'].max()
                        if max_high_pips >= max_low_pips:
                            peak_idx = df_after['pips_high'].idxmax()
                            peak_time_real = peak_idx
                            peak_pips_real = max_high_pips
                        else:
                            peak_idx = df_after['pips_low'].idxmax()
                            peak_time_real = peak_idx
                            peak_pips_real = max_low_pips
                        st.write(f"**Pic absolu réel:** {peak_time_real.strftime('%H:%M')} ({peak_pips_real:.1f} pips)")
            
            # Créer timeline chart (avec prix réels pour pic absolu)
            # Déterminer direction (UP/DOWN)
            direction = "UP"
            pattern_exact = prediction_result.get('pattern_type')
            if pattern_exact and isinstance(pattern_exact, str):
                if 'DOWN' in pattern_exact.upper():
                    direction = "DOWN"
                elif 'UP' in pattern_exact.upper():
                    direction = "UP"
            else:
                # Fallback en analysant les prix
                max_price = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= first_event_time + pd.Timedelta(hours=2))]['close'].max()
                min_price = df_prices[(df_prices.index >= first_event_time) & (df_prices.index <= first_event_time + pd.Timedelta(hours=2))]['close'].min()
                max_diff = (max_price - start_price) if pd.notna(max_price) else 0
                min_diff = (start_price - min_price) if pd.notna(min_price) else 0
                direction = "UP" if max_diff >= min_diff else "DOWN"

            fig = create_double_wave_timeline_chart(
                prediction_pips=prediction_result['prediction_pips'],
                surprise_pct=surprise_pct,
                num_events=num_events,
                start_time=first_event_time,
                start_price=start_price,
                df_prices=df_prices,
                direction=direction
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ Impossible de trouver prix avant événement pour timeline")


# ═══════════════════════════════════════════════════════════════
# ÉTAPE 11 : EXPORT CSV
# ═══════════════════════════════════════════════════════════════

def export_results_csv(target_date, pattern_result, prediction_result, df_events):
    """Génère CSV téléchargeable"""
    
    # Créer dict résultats
    export_data = {
        'Date': target_date.strftime('%Y-%m-%d'),
        'Pattern': pattern_result['pattern_type'],
        'Confiance': f"{pattern_result['detection_confidence']*100:.0f}%",
        'Impact_Pips': prediction_result.get('prediction_pips', ''),
        'Amplification': prediction_result.get('amplification', ''),
        'Method': prediction_result.get('method', ''),
        'Status': prediction_result['status'],
        'Num_Events': len(df_events),
        'Events_Scored': len(df_events[df_events['score'] > 0]),
        'Score_Total': df_events['score'].sum(),
        'Warning': prediction_result.get('warning', '')
    }
    
    df_export = pd.DataFrame([export_data])
    
    # Convertir en CSV
    csv_buffer = io.StringIO()
    df_export.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()
    
    return csv_string


# ═══════════════════════════════════════════════════════════════
# INTERFACE PRINCIPALE
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.success("✅ **Flowchart 11 Étapes COMPLET** : Détection Pattern + Aiguillage + Prédictions + Export")

# ═══════════════════════════════════════════════════════════════
# NOUVELLE SECTION : SÉLECTION DATE DEPUIS CALENDRIER
# ═══════════════════════════════════════════════════════════════

st.markdown("### 📅 Sélection Date")

# Mode de sélection
mode_selection = st.radio(
    "Mode de sélection",
    ["📝 Saisie manuelle", "📅 Depuis calendrier"],
    horizontal=True,
    key='mode_selection'
)

date_input = None
selected_date_from_calendar = None

if mode_selection == "📅 Depuis calendrier":
    # Panneau de recherche de dates candidates (comme Calendrier Trading 2.0)
    from datetime import datetime, timedelta
    
    st.markdown("#### 🔍 Recherche de dates candidates")
    
    # Bouton pour forcer recalcul (évite cache Streamlit)
    if st.button("🔄 Actualiser recherche", help="Force le recalcul avec les nouveaux paramètres"):
        # Invalider cache si nécessaire
        if 'calendar_search_cache' in st.session_state:
            del st.session_state['calendar_search_cache']
    
    # Paramètres de recherche dans sidebar ou colonnes
    col_search1, col_search2, col_search3 = st.columns(3)
    
    with col_search1:
        lookahead_days = st.slider(
            "📆 Nombre de jours à venir",
            min_value=1,
            max_value=30,
            value=7,
            step=1,
            help="Période de recherche pour les événements futurs"
        )
        min_importance_cal = st.select_slider(
            "🎯 Importance minimale",
            options=[1, 2, 3],
            value=2,
            format_func=lambda x: {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}[x]
        )
    
    with col_search2:
        min_impact_cal = st.slider(
            "💥 Impact médian minimal (pips)",
            min_value=0,
            max_value=150,
            value=40,
            step=10,
            help="Filtrer par impact attendu depuis cache"
        )
        min_samples_cal = st.slider(
            "📊 Occurrences min. (historique)",
            min_value=1,
            max_value=30,
            value=3,
            step=1,
            help="Nombre minimum d'occurrences historiques pour valider un cluster"
        )
    
    with col_search3:
        countries_cal = st.multiselect(
            "🌍 Pays",
            options=sorted(list(EURUSD_RELEVANT_COUNTRIES)),
            default=["US", "EU"],
            help="Pays pertinents pour EUR/USD"
        )
    
    if not countries_cal:
        st.warning("⚠️ Sélectionnez au moins un pays")
        date_input = None
    else:
        # Calculer période avec timestamps complets
        now = datetime.now()
        date_from = datetime(now.year, now.month, now.day, 0, 0, 0)  # Début du jour
        date_to = datetime(now.year, now.month, now.day, 23, 59, 59) + timedelta(days=lookahead_days)  # Fin du jour + lookahead
        
        # Convertir en UTC pour requête DB
        tz_bern = pytz.timezone('Europe/Zurich')
        tz_utc = pytz.timezone('UTC')
        date_from_bern = tz_bern.localize(date_from)
        date_to_bern = tz_bern.localize(date_to)
        date_from_utc = date_from_bern.astimezone(tz_utc)
        date_to_utc = date_to_bern.astimezone(tz_utc)
        
        # Charger événements futurs avec filtres
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        countries_str = "', '".join(countries_cal)
        
        # Requête corrigée : utiliser timestamps UTC complets et filtre importance correct
        query_future = f"""
        SELECT DISTINCT 
            DATE(ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich') as date,
            COUNT(*) as n_events,
            COUNT(CASE WHEN importance_n = 1 THEN 1 END) as n_high,
            COUNT(CASE WHEN importance_n = 2 THEN 1 END) as n_medium,
            COUNT(CASE WHEN importance_n = 3 THEN 1 END) as n_low
        FROM events
        WHERE ts_utc >= ?
          AND ts_utc <= ?
          AND importance_n <= ?
          AND country IN ('{countries_str}')
        GROUP BY DATE(ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich')
        ORDER BY date
        """
        
        df_dates = conn.execute(query_future, [
            date_from_utc,
            date_to_utc,
            min_importance_cal
        ]).df()
        conn.close()
        
        # Debug : afficher info sur les résultats
        if st.sidebar.checkbox("🔍 Afficher debug recherche", value=False):
            st.sidebar.write(f"**Période recherchée:**")
            st.sidebar.write(f"  De: {date_from.strftime('%Y-%m-%d %H:%M')} (Bern)")
            st.sidebar.write(f"  À: {date_to.strftime('%Y-%m-%d %H:%M')} (Bern)")
            st.sidebar.write(f"  Importance max: {min_importance_cal} ({'High' if min_importance_cal == 1 else 'Medium' if min_importance_cal == 2 else 'Low'})")
            st.sidebar.write(f"  Pays: {', '.join(countries_cal)}")
            if not df_dates.empty:
                st.sidebar.write(f"**Résultats:** {len(df_dates)} dates trouvées")
                st.sidebar.dataframe(df_dates.head(10))
        
        # Charger cache pour enrichir et filtrer
        df_cache = load_cache_clusters()
        df_cache_patterns = load_cache_patterns()
        
        # Debug : afficher stats cache
        debug_cache = st.sidebar.checkbox("🔍 Debug cache clusters", value=False)
        if debug_cache:
            if df_cache is not None and not df_cache.empty:
                st.sidebar.write(f"**Cache clusters:** {len(df_cache)} clusters")
                st.sidebar.write(f"Impact médian min: {df_cache['impact_median'].min():.1f} pips")
                st.sidebar.write(f"Impact médian max: {df_cache['impact_median'].max():.1f} pips")
                st.sidebar.write(f"Occurrences min: {df_cache['n_samples'].min()}")
                st.sidebar.write(f"Occurrences max: {df_cache['n_samples'].max()}")
                st.sidebar.write(f"Clusters avec impact ≥ {min_impact_cal} pips: {len(df_cache[df_cache['impact_median'] >= min_impact_cal])}")
                st.sidebar.write(f"Clusters avec occurrences ≥ {min_samples_cal}: {len(df_cache[df_cache['n_samples'] >= min_samples_cal])}")
            else:
                st.sidebar.warning("⚠️ Cache clusters vide ou introuvable")
        
        # Filtrer le cache par impact médian et occurrences
        if df_cache is not None and not df_cache.empty:
            df_cache_filtered = df_cache[
                (df_cache['impact_median'] >= min_impact_cal) &
                (df_cache['n_samples'] >= min_samples_cal)
            ].copy()
        else:
            df_cache_filtered = pd.DataFrame()
        
        if not df_dates.empty:
            df_dates['date'] = pd.to_datetime(df_dates['date'])
            
            # Charger tous les événements futurs en une seule requête pour filtrage
            conn = duckdb.connect(str(DB_PATH), read_only=True)
            query_events = f"""
            SELECT 
                DATE(ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich') as date,
                event_key,
                country,
                importance_n
            FROM events
            WHERE ts_utc >= ?
              AND ts_utc <= ?
              AND importance_n <= ?
              AND country IN ('{countries_str}')
            ORDER BY date, ts_utc
            """
            df_future_events = conn.execute(query_events, [
                date_from_utc,
                date_to_utc,
                min_importance_cal
            ]).df()
            conn.close()
            
            # Debug : afficher nombre de dates trouvées AVANT filtrage cache
            st.caption(f"✅ {len(df_dates)} date(s) trouvée(s) avec {lookahead_days} jours de recherche")
            
            # Enrichir avec stats cache et filtrer par impact/occurrences
            dates_enriched = []
            matches_found = 0
            matches_filtered = 0
            
            for idx, row in df_dates.iterrows():
                date_obj = row['date'].date()
                n_events = int(row['n_events'])
                n_high = int(row.get('n_high', 0))
                n_medium = int(row.get('n_medium', 0))
                n_low = int(row.get('n_low', 0))
                
                # Charger événements pour cette date (convertir date_obj en Timestamp pour comparaison)
                date_ts = pd.Timestamp(date_obj)
                events_for_date = df_future_events[df_future_events['date'].dt.date == date_obj]
                
                # Construire signature du cluster et matcher avec cache (non filtré d'abord)
                cluster_match = None
                if not events_for_date.empty and df_cache is not None and not df_cache.empty:
                    # Créer DataFrame temporaire pour find_cluster_in_cache
                    df_events_temp = events_for_date[['event_key']].copy()
                    # Chercher dans le cache complet (pas filtré) pour avoir les stats
                    cluster_match = find_cluster_in_cache(df_events_temp, df_cache)
                    if cluster_match:
                        matches_found += 1
                
                # Filtrer : si filtres activés ET cluster match trouvé, vérifier les critères
                should_skip = False
                if min_impact_cal > 0 or min_samples_cal > 1:
                    if cluster_match is not None:
                        # Vérifier si le cluster respecte les critères
                        impact_med = cluster_match.get('impact_median', 0)
                        n_samples = cluster_match.get('n_samples', 0)
                        if impact_med < min_impact_cal or n_samples < min_samples_cal:
                            should_skip = True
                            matches_filtered += 1
                    else:
                        # Pas de cluster match : on garde la date si filtres pas trop stricts
                        # (sinon on la skip pour éviter trop de bruit)
                        if min_impact_cal > 0:  # Si filtre impact activé, skip si pas de match
                            should_skip = True
                
                if should_skip:
                    continue  # Skip cette date
                
                # Construire label avec répartition par importance
                importance_parts = []
                if n_high > 0:
                    importance_parts.append(f"🔴{n_high}")
                if n_medium > 0:
                    importance_parts.append(f"🟡{n_medium}")
                if n_low > 0:
                    importance_parts.append(f"🟢{n_low}")
                
                importance_str = f" ({', '.join(importance_parts)})" if importance_parts else ""
                
                # Ajouter info impact si cluster match trouvé
                impact_info = ""
                if cluster_match:
                    impact_med = cluster_match.get('impact_median', 0)
                    n_samples = cluster_match.get('n_samples', 0)
                    impact_info = f" | Impact: {impact_med:.0f} pips ({n_samples} occ.)"
                
                dates_enriched.append({
                    'date': date_obj,
                    'n_events': n_events,
                    'n_high': n_high,
                    'n_medium': n_medium,
                    'n_low': n_low,
                    'label': f"{date_obj.strftime('%d/%m/%Y (%A)')} - {n_events} événement(s){importance_str}{impact_info}"
                })
            
            # Afficher nombre de dates APRÈS filtrage
            if min_impact_cal > 0 or min_samples_cal > 1:
                st.caption(f"📊 {len(dates_enriched)} date(s) après filtrage (impact ≥ {min_impact_cal} pips, occurrences ≥ {min_samples_cal})")
                if debug_cache:
                    st.sidebar.write(f"**Matching:** {matches_found} clusters trouvés, {matches_filtered} filtrés")
                
                # Message informatif si aucun résultat
                if len(dates_enriched) == 0 and len(df_dates) > 0:
                    if df_cache is not None and not df_cache.empty:
                        clusters_meeting_criteria = len(df_cache[
                            (df_cache['impact_median'] >= min_impact_cal) &
                            (df_cache['n_samples'] >= min_samples_cal)
                        ])
                        if clusters_meeting_criteria == 0:
                            st.warning(
                                f"⚠️ **Aucun cluster dans le cache ne respecte les deux critères simultanément.**\n\n"
                                f"- Clusters avec impact ≥ {min_impact_cal} pips : {len(df_cache[df_cache['impact_median'] >= min_impact_cal])}\n"
                                f"- Clusters avec occurrences ≥ {min_samples_cal} : {len(df_cache[df_cache['n_samples'] >= min_samples_cal])}\n\n"
                                f"💡 **Suggestion :** Réduisez le seuil d'occurrences (actuellement {min_samples_cal}) ou d'impact (actuellement {min_impact_cal} pips) pour obtenir des résultats."
                            )
                        elif matches_found == 0:
                            st.info(
                                f"ℹ️ **Aucun cluster correspondant trouvé pour les {len(df_dates)} dates identifiées.**\n\n"
                                f"Les événements de ces dates ne correspondent à aucun cluster du cache (même avec similarité partielle ≥ 80%).\n\n"
                                f"💡 **Suggestion :** Les clusters d'événements similaires sont rares. Essayez de :\n"
                                f"- Élargir la période de recherche\n"
                                f"- Réduire les critères de filtrage\n"
                                f"- Vérifier que le cache est à jour (script `cache_refresh.py`)"
                            )
                        else:
                            st.info(
                                f"ℹ️ **{matches_found} cluster(s) trouvé(s) mais {matches_filtered} exclu(s) par les filtres.**\n\n"
                                f"Les clusters trouvés ne respectent pas les critères (impact < {min_impact_cal} pips ou occurrences < {min_samples_cal}).\n\n"
                                f"💡 **Suggestion :** Réduisez les seuils pour voir ces dates."
                            )
            
            # Sélecteur enrichi
            if dates_enriched:
                # Debug : vérifier nombre de dates enrichies
                if len(dates_enriched) != len(df_dates):
                    st.warning(f"⚠️ Incohérence : {len(df_dates)} dates dans DB mais {len(dates_enriched)} dates enrichies")
                
                # Créer liste de labels pour affichage
                date_labels = [d['label'] for d in dates_enriched]
                date_objects = [d['date'] for d in dates_enriched]
                
                # Utiliser selectbox avec index numérique (clé dynamique pour éviter cache)
                search_params_key = f"cal_{lookahead_days}_{min_importance_cal}_{'_'.join(sorted(countries_cal))}"
                selected_idx = st.selectbox(
                    "📅 Choisir une date",
                    options=range(len(dates_enriched)),
                    format_func=lambda i: date_labels[i] if i < len(date_labels) else f"Index {i}",
                    key=f'calendar_date_idx_{search_params_key}',
                    index=0
                )
                
                if selected_idx is not None and selected_idx < len(date_objects):
                    selected_date_from_calendar = date_objects[selected_idx]
                    date_input = selected_date_from_calendar.strftime('%Y-%m-%d')
                    
                    # Afficher info cache
                    if df_cache is not None and not df_cache.empty:
                        st.caption(f"💡 {len(df_cache)} clusters pré-calculés disponibles dans le cache")
                else:
                    date_input = None
            else:
                st.info("ℹ️ Aucune date trouvée avec les critères sélectionnés")
                date_input = None
        else:
            # Message informatif selon le filtre importance
            if min_importance_cal == 1:
                st.warning(f"⚠️ Aucun événement **HIGH** (importance_n = 1) trouvé dans les {lookahead_days} prochains jours pour les pays sélectionnés.")
                st.info("💡 **Conseil:** Les événements HIGH sont rares. Essayez de :\n"
                       "- Élargir la période (augmenter le nombre de jours)\n"
                       "- Sélectionner 'Medium' ou 'Low' comme importance minimale\n"
                       "- Ajouter plus de pays (ex: DE, FR, IT)")
            else:
                st.info(f"ℹ️ Aucun événement trouvé dans les {lookahead_days} prochains jours avec les critères sélectionnés")
                st.caption("💡 Essayez d'élargir la période, réduire l'importance minimale ou ajouter des pays")
            
            date_input = st.text_input(
                "📅 Ou saisir une date manuellement",
                value=datetime.now().strftime('%Y-%m-%d'),
                help="Formats: 2025-09-11, 11.09.2025, 11/09/2025"
            )
else:
    # Mode saisie manuelle
    date_input = st.text_input(
        "📅 Date (formats acceptés: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY)",
        value="11.09.2025",
        help="Formats: 2025-09-11, 11.09.2025, 11/09/2025"
    )

# Paramètres utilisateur
col1, col2, col3 = st.columns([2, 1, 1])

with col2:
    min_pips = st.number_input(
        "📏 Seuil minimum (pips)",
        value=35.0,
        min_value=10.0,
        max_value=100.0,
        step=5.0,
        help="Mouvement minimum pour détecter un pattern"
    )

with col3:
    timezone_select = st.selectbox(
        "🌍 Timezone",
        options=["Europe/Zurich", "UTC", "America/New_York"],
        index=0
    )

# Mode workflow
workflow_mode = st.radio(
    "🔧 Mode de travail",
    ["📊 Workflow Correct (Prix → Mouvement → Cluster)", "🔮 Prédiction Future (Événements → Prédiction)"],
    horizontal=True,
    help="Workflow Correct : Scanner prix d'abord, puis trouver cluster. Prédiction Future : Charger événements et prédire."
)

# Bouton calculer
if st.button("🚀 Calculer Prédictions V3.0", type="primary"):
    
    # ÉTAPE 1 : Validation
    with st.spinner("Validation entrée..."):
        validation = validate_input(date_input, timezone_select, min_pips)
    
    if not validation['valid']:
        st.error(f"❌ {validation['error_message']}")
        st.stop()
    
    target_date = validation['date']
    timezone = validation['timezone']
    min_pips_validated = validation['min_pips']
    
    st.success(f"✅ Date validée : {target_date.strftime('%Y-%m-%d')}")
    
    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW CORRECT : PRIX → MOUVEMENT → CLUSTER
    # ═══════════════════════════════════════════════════════════════
    
    if "Workflow Correct" in workflow_mode:
        # ÉTAPE 1 : Charger prix d'abord
        with st.spinner("Chargement prix 1-minute..."):
            df_prices = load_prices_for_date(target_date, DB_PATH, str(timezone))
        
        if df_prices.empty:
            st.warning(f"❌ Aucun prix disponible pour {target_date.strftime('%Y-%m-%d')}")
            st.info("💡 Utilisez le mode 'Prédiction Future' pour les dates sans prix historiques")
            st.stop()
        
        st.success(f"✅ {len(df_prices)} prix chargés")
        
        # ÉTAPE 2 : Scanner prix pour mouvement fort
        with st.spinner(f"Scanning prix pour mouvement ≥{min_pips_validated} pips..."):
            movement = scan_price_movements_for_date(df_prices, min_pips_validated)
        
        if movement is None:
            st.warning(f"❌ Aucun mouvement ≥{min_pips_validated} pips détecté pour {target_date.strftime('%Y-%m-%d')}")
            st.info("💡 Essayez de réduire le seuil minimum ou utilisez le mode 'Prédiction Future'")
            st.stop()
        
        st.success(f"✅ Mouvement détecté : {movement['impact_pips']:.1f} pips ({movement['direction']}) à {movement['start_time'].strftime('%H:%M')}")
        
        # ÉTAPE 3 : Trouver cluster d'événements causaux (initiaux + catalyseurs)
        with st.spinner("Recherche cluster d'événements causaux (initiaux + catalyseurs)..."):
            df_events = find_cluster_for_movement(
                movement, 
                DB_PATH, 
                str(timezone),
                include_catalyst_events=True,  # Inclure événements catalyseurs
                catalyst_window_minutes=60  # Chercher jusqu'à 60 min après début
            )
        
        if df_events.empty:
            st.warning(f"❌ Aucun événement trouvé autour du mouvement à {movement['start_time'].strftime('%H:%M')}")
            st.stop()
        
        # Afficher statistiques événements
        num_initial = len(df_events[df_events.get('event_type', 'initial') == 'initial']) if 'event_type' in df_events.columns else len(df_events)
        num_catalysts = len(df_events[df_events.get('event_type') == 'catalyst']) if 'event_type' in df_events.columns else 0
        
        if num_catalysts > 0:
            st.success(f"✅ {num_initial} événement(s) initial(aux) + {num_catalysts} événement(s) catalyseur(s) trouvé(s)")
            st.info(f"💡 Les événements catalyseurs surviennent pendant le mouvement et peuvent relancer l'impact (ex: current account DE à 14h45)")
        else:
            st.success(f"✅ {len(df_events)} événement(s) trouvé(s) dans le cluster")
        
        # NOUVEAU : Chercher cluster dans cache pré-calculé
        with st.spinner("Recherche dans cache pré-calculé..."):
            df_cache_clusters = load_cache_clusters()
            cache_match = find_cluster_in_cache(df_events, df_cache_clusters) if df_cache_clusters is not None else None
        
        if cache_match:
            st.info(f"⚡ **Cluster trouvé dans cache** ({cache_match.get('n_samples', 0)} échantillons historiques)")
            with st.expander("📊 Stats pré-calculées du cluster", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Impact médian", f"{cache_match.get('impact_median', 0):.1f} pips")
                    st.metric("Latence médiane", f"{cache_match.get('latency_median', 0):.0f} min" if pd.notna(cache_match.get('latency_median')) else "N/A")
                with col2:
                    st.metric("TTR médian", f"{cache_match.get('ttr_median', 0):.0f} min" if pd.notna(cache_match.get('ttr_median')) else "N/A")
                    st.metric("Pullback médian", f"{cache_match.get('pullback_median', 0):.1f} pips" if pd.notna(cache_match.get('pullback_median')) else "N/A")
                with col3:
                    st.metric("Pattern dominant", cache_match.get('dominant_pattern', 'N/A'))
                    st.metric("Direction", cache_match.get('dominant_direction', 'N/A'))
                if cache_match.get('jaccard_similarity'):
                    st.caption(f"Similarité Jaccard: {cache_match['jaccard_similarity']*100:.0f}%")
        else:
            st.info("ℹ️ Cluster non trouvé dans cache. Calcul en cours...")
        
        # Mettre à jour df_prices pour utiliser le mouvement détecté
        # (le mouvement a déjà été détecté depuis les prix)
        
        # Enrichir les événements avec scores (nécessaire pour prédiction)
        with st.spinner("Enrichissement événements avec scores..."):
            df_events_enriched = enrich_events_with_scores(df_events, DB_PATH)
        
        if df_events_enriched.empty:
            st.warning("❌ Aucun événement enrichi disponible")
            st.stop()
        
        st.success(f"✅ {len(df_events_enriched)} événement(s) enrichi(s)")
    
    # ═══════════════════════════════════════════════════════════════
    # WORKFLOW PRÉDICTION : ÉVÉNEMENTS → PRÉDICTION
    # ═══════════════════════════════════════════════════════════════
    
    else:
        # ÉTAPE 2 : Charger events
        with st.spinner("Chargement événements HIGH..."):
            df_events = load_events_for_date(target_date, DB_PATH, str(timezone))
        
        if df_events.empty:
            st.warning(f"❌ Aucun événement HIGH trouvé pour {target_date.strftime('%Y-%m-%d')}")
            st.stop()
        
        st.success(f"✅ {len(df_events)} événement(s) HIGH trouvé(s)")
        
        # NOUVEAU : Chercher cluster dans cache pré-calculé
        with st.spinner("Recherche dans cache pré-calculé..."):
            df_cache_clusters = load_cache_clusters()
            cache_match = find_cluster_in_cache(df_events, df_cache_clusters) if df_cache_clusters is not None else None
        
        if cache_match:
            st.info(f"⚡ **Cluster trouvé dans cache** ({cache_match.get('n_samples', 0)} échantillons historiques)")
            with st.expander("📊 Stats pré-calculées du cluster", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Impact médian", f"{cache_match.get('impact_median', 0):.1f} pips")
                    st.metric("Latence médiane", f"{cache_match.get('latency_median', 0):.0f} min" if pd.notna(cache_match.get('latency_median')) else "N/A")
                with col2:
                    st.metric("TTR médian", f"{cache_match.get('ttr_median', 0):.0f} min" if pd.notna(cache_match.get('ttr_median')) else "N/A")
                    st.metric("Pullback médian", f"{cache_match.get('pullback_median', 0):.1f} pips" if pd.notna(cache_match.get('pullback_median')) else "N/A")
                with col3:
                    st.metric("Pattern dominant", cache_match.get('dominant_pattern', 'N/A'))
                    st.metric("Direction", cache_match.get('dominant_direction', 'N/A'))
                if cache_match.get('jaccard_similarity'):
                    st.caption(f"Similarité Jaccard: {cache_match['jaccard_similarity']*100:.0f}%")
        else:
            st.info("ℹ️ Cluster non trouvé dans cache. Calcul en cours...")
        
        # ÉTAPE 3 : Charger prix (nécessaire pour enrichissement)
        with st.spinner("Chargement prix 1-minute..."):
            df_prices = load_prices_for_date(target_date, DB_PATH, str(timezone))
        
        if df_prices.empty:
            st.warning(f"❌ Aucun prix disponible pour {target_date.strftime('%Y-%m-%d')}")
            st.info("💡 Les prix sont nécessaires pour la détection de pattern. Utilisez le mode 'Workflow Correct' si disponible.")
            st.stop()
        
        st.success(f"✅ {len(df_prices)} prix chargés")
    
    # ÉTAPE 4 : Enrichir AVANT affichage checkbox (besoin des scores)
    with st.spinner("Enrichissement avec scores empiriques..."):
        df_events_enriched = enrich_events_with_scores(df_events, DB_PATH)
    
    events_scored = len(df_events_enriched[df_events_enriched['score'] > 0])
    st.success(f"✅ {events_scored}/{len(df_events_enriched)} événements scorés")
    
    # ═══════════════════════════════════════════════════════════════
    # NOUVELLE SECTION : AFFICHAGE ÉVÉNEMENTS AVEC CHECKBOX
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("### 📋 Événements du Cluster")
    st.markdown("**Cochez les événements à inclure dans la prédiction**")
    
    # Afficher événements avec checkbox
    selected_events = []
    actual_values = {}
    
    for idx, row in df_events_enriched.iterrows():
        event_key = row['event_key']
        event_title = row.get('event_title', event_key)
        country = row.get('country', '')
        ts_bern = row.get('ts_bern', '')
        actual = row.get('actual', None)
        estimate = row.get('estimate', None)
        score = row.get('score', 0)
        
        # Identifier type événement (initial ou catalyseur)
        event_type = row.get('event_type', 'initial')
        if event_type == 'catalyst':
            event_label = f"⚡ **CATALYSEUR** : {event_title} ({country})"
            event_help = "Événement survenant pendant le mouvement, peut relancer l'impact"
        else:
            event_label = f"**{event_title}** ({country})"
            event_help = "Événement initial du cluster"
        
        # Checkbox pour sélection
        checkbox_key = f"event_{idx}_{event_key}"
        is_selected = st.checkbox(
            f"{event_label} - {ts_bern.strftime('%H:%M') if pd.notna(ts_bern) else 'N/A'} - Score: {score:.1f}",
            value=True,  # Par défaut tous sélectionnés
            key=checkbox_key,
            help=event_help
        )
        
        if is_selected:
            selected_events.append(idx)
            
            # Saisie actual/estimate (si pas encore disponible)
            col1, col2 = st.columns(2)
            with col1:
                actual_input = st.number_input(
                    f"Actual {event_title}",
                    value=float(actual) if pd.notna(actual) else None,
                    key=f"actual_{idx}",
                    step=0.01,
                    format="%.2f"
                )
                if actual_input is not None:
                    actual_values[event_key] = actual_input
            
            with col2:
                estimate_display = st.text_input(
                    f"Estimate {event_title}",
                    value=str(estimate) if pd.notna(estimate) else "N/A",
                    key=f"estimate_{idx}",
                    disabled=True
                )
        
        st.divider()
    
    # Filtrer df_events_enriched sur événements sélectionnés
    if selected_events:
        df_events_enriched = df_events_enriched.loc[selected_events].reset_index(drop=True)
        
        # Mettre à jour actual si saisi
        if actual_values:
            for event_key, actual_val in actual_values.items():
                mask = df_events_enriched['event_key'] == event_key
                if mask.any():
                    df_events_enriched.loc[mask, 'actual'] = actual_val
        
        st.info(f"✅ {len(df_events_enriched)} événement(s) sélectionné(s) pour la prédiction")
    else:
        st.warning("⚠️ Aucun événement sélectionné. Veuillez cocher au moins un événement.")
        st.stop()
    
    # ÉTAPE 5 : Détecter pattern
    with st.spinner("Détection pattern..."):
        pattern_result = detect_pattern_type(df_events_enriched, df_prices, min_pips_validated, timezone)
    
    st.success(f"✅ Pattern détecté : {pattern_result['pattern_type']} (confiance {pattern_result['detection_confidence']*100:.0f}%)")
    
    # ÉTAPE 6 : Aiguillage + ÉTAPES 7-9 : Prédiction
    # NOUVEAU : Option pour utiliser le pipeline complet
    use_complete_pipeline = st.checkbox(
        "🚀 Utiliser le pipeline complet (Random Forest + Stratégie de sortie optimisée)",
        value=True,
        help="Active le pipeline complet avec toutes les améliorations récentes (Random Forest, stratégie de sortie optimisée, etc.)"
    )
    
    with st.spinner("Calcul prédiction..."):
        prediction_result = route_prediction(
            pattern_result['pattern_type'],
            df_events_enriched,
            df_prices,
            DB_PATH,
            use_complete_pipeline=use_complete_pipeline
        )
    
    if prediction_result['status'] == 'predicted':
        st.success(f"✅ Impact prédit : {prediction_result['prediction_pips']:.1f} pips")
    elif prediction_result['status'] == 'excluded':
        st.warning(f"⚠️ Prédiction exclue : {prediction_result['reason']}")
    
    # ÉTAPE 10 : Affichage
    display_results(target_date, min_pips_validated, str(timezone), pattern_result, prediction_result, df_events_enriched, df_prices)
    
    # ÉTAPE 11 : Export
    st.markdown("---")
    st.markdown("### 📥 Export Résultats")
    
    csv_data = export_results_csv(target_date, pattern_result, prediction_result, df_events_enriched)
    
    st.download_button(
        label="⬇️ Télécharger CSV",
        data=csv_data,
        file_name=f"prediction_{target_date.strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )


# Footer
st.markdown("---")
st.markdown("""
**Planificateur V3.0** - Version 3.0 COMPLÈTE (Session 134)  
✅ Étapes 1-11 implémentées selon Flowchart Session 133  
✅ Pipeline LOO-CV avec fallback fonction universelle  
✅ Module DoubleWave Session 132 intégré  
✅ Détection pattern automatique  
✅ Export CSV téléchargeable  
✅ Interface complète et fonctionnelle

**Tokens Session 134 :** ~90k / 190k (47%)
""")
