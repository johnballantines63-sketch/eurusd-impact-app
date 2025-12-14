"""
PLANIFICATEUR V3.2 - FORMULE LINÉAIRE
=======================================

Version 3.2 - Intégration Formule Linéaire Validée
Date : 2025-12-07

⭐ NOUVELLE FORMULE : calculate_impact_linear()
- Validée sur 50 dates significatives (MOYEN/FORT/TRÈS_FORT)
- Performance FORT : Ratio médian 1.297 (excellent)
- MAE global : 13.98 pips (-64% vs formule D)

ARCHITECTURE MODULAIRE:
Basée sur Version 3.0 Clean + Formule Linéaire Validée

STRUCTURE MODULAIRE:
1. Configuration & Imports
2. Utilitaires (validation, parsing, normalisation)
3. Chargement Données (Events, Prix, Cache)
4. Détection Pattern (Workflow Correct)
5. Prédictions (Double Wave, Single Wave avec Ensemble)
6. Affichage & Export
7. Interface Streamlit

DÉVELOPPEMENT PROGRESSIF:
- Phase 1: Structure de base + Validation + Chargement
- Phase 2: Détection Pattern + Prédictions de base
- Phase 3: Ensemble Methods + Cache + Calendrier
- Phase 4: Workflow Correct + Timeline + Export

ARCHITECTURE POUR COMPILATION FUTURE:
--------------------------------------
Cette architecture est conçue pour faciliter une future compilation en app standalone :

1. SÉPARATION LOGIQUE/UI:
   - Toutes les fonctions métier sont dans ce fichier (pas de dépendance Streamlit)
   - Seule la fonction main() utilise Streamlit
   - Les fonctions peuvent être réutilisées dans Tkinter, PyQt, ou autre UI

2. COMPILATION POSSIBLE:
   - Option A: Streamlit + PyInstaller (lourd mais possible)
   - Option B: Extraire logique → créer UI séparée (Tkinter/PyQt)
   - Option C: API Flask/FastAPI + Interface web standalone

3. MIGRATION FACILITÉE:
   - Toutes les fonctions métier sont indépendantes de Streamlit
   - Il suffit de remplacer main() pour une autre UI
   - Les imports Streamlit sont isolés dans la fonction main()
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
from typing import Dict, Tuple, Optional, List
import io

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# -------------------------------------------------------------------------
# Global flags
# -------------------------------------------------------------------------
SILENT_WARNING_DEFAULT = True

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'streamlit_app'))
SESSION_SCRIPTS = PROJECT_ROOT / "SESSION_VALIDATION_ACTUELLE" / "scripts"
if str(SESSION_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SESSION_SCRIPTS))

import config

# ⭐ V8 Adapter (optionnel, pour prédictions V8 backtestées)
try:
    from core.v8_ui_adapter import predict_cluster_v8
    V8_AVAILABLE = True
except ImportError:
    V8_AVAILABLE = False
    predict_cluster_v8 = None
from core.event_utils import normalize_event_keys_list, create_event_key_set, normalize_event_key_with_variants
from core.doublewave_prediction import predict_doublewave_overlap
from core.ensemble_prediction import predict_pattern_based_ensemble
from core.impact_unified import calculate_impact_unified  # 🆕 Impact unifié selon IMPACT_SPEC_V1
from core.formulas_validated import (
    calculate_impact_d,
    calculate_impact_linear,  # ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
    calculate_ttr_c,
    calculate_pullback_v2,
    calculate_amplification_extended,
    calculate_adjusted_empirical_score,
    get_event_direction  # ⭐ Pour prédire la direction depuis les événements
)
from core.finnhub_patterns import (
    load_finnhub_patterns,
    match_finnhub_pattern_to_detection
)
# Finnhub support/resistance désactivé (modules supprimés)
# from core.finnhub_support_resistance import (
#     load_support_resistance,
#     find_nearest_levels,
#     validate_prediction_against_levels,
#     adjust_prediction_with_support_resistance
# )
# Finnhub aggregate indicators désactivé (modules supprimés)
# from core.finnhub_aggregate_indicators import (
#     load_aggregate_indicators,
#     adjust_prediction_with_indicators
# )
# Auto-refresh désactivé (module supprimé)
# # Auto-refresh désactivé (module supprimé)
# from utils.auto_refresh import ensure_data_freshness
# validate_coefficients_empirical désactivé (module supprimé)
# from validate_coefficients_empirical import extract_core_events_from_cluster, create_canonical_event_id

# Fonctions de remplacement pour validate_coefficients_empirical
from core.event_utils import normalize_event_key_with_variants

def create_canonical_event_id(event_key: str, country: str, importance: str) -> str:
    """
    Crée un identifiant canonique pour un événement.
    
    Format: {COUNTRY}__{event_key_normalized}__{importance}
    
    Args:
        event_key: Clé de l'événement
        country: Code pays
        importance: Niveau d'importance ('high', 'medium', 'low')
    
    Returns:
        Identifiant canonique
    """
    event_key_norm = normalize_event_key_with_variants(event_key) if event_key else ''
    return f"{country.upper()}__{event_key_norm}__{importance}"

def extract_core_events_from_cluster(
    conn,
    cluster_events: pd.DataFrame,
    date_str: str,
    support_threshold: float = 0.8,
    jaccard_threshold: float = 0.60,
    years_lookback: int = 5
) -> set:
    """
    Extrait les événements core d'un cluster (fonction simplifiée).
    
    Cette fonction est un placeholder. Dans le pipeline complet, cette logique
    est gérée par etape3_definir_noyau_dur qui détecte les patterns CPI/NFP.
    
    Args:
        conn: Connexion DuckDB
        cluster_events: DataFrame des événements du cluster
        date_str: Date du cluster
        support_threshold: Seuil de support (non utilisé dans cette version simplifiée)
        jaccard_threshold: Seuil Jaccard (non utilisé dans cette version simplifiée)
        years_lookback: Années de lookback (non utilisé dans cette version simplifiée)
    
    Returns:
        Set d'identifiants canoniques des événements core
    """
    # Version simplifiée : retourner tous les événements comme core
    # (la logique complète est dans etape3_definir_noyau_dur du pipeline)
    importance_map = {1: 'high', 2: 'medium', 3: 'low'}
    core_events = set()
    
    for _, event in cluster_events.iterrows():
        event_key = event.get('event_key', '')
        country = event.get('country', '')
        importance_n = event.get('importance_n', 3)
        importance_str = importance_map.get(int(importance_n), 'unknown')
        
        canon_id = create_canonical_event_id(event_key, country, importance_str)
        core_events.add(canon_id)
    
    return core_events

# Configuration
DB_PATH = config.DB_PATH
# Utiliser le nouveau cache catalogué (avec toutes les occurrences historiques)
CACHE_CLUSTERS_PATH = Path(__file__).parent.parent.parent / "data" / "cache_clusters_catalogued_simple.csv"
# Fallback vers l'ancien cache si le nouveau n'existe pas
CACHE_CLUSTERS_PATH_FALLBACK = Path(__file__).parent.parent.parent / "data" / "cache_clusters.csv"
CACHE_PATTERNS_PATH = Path(__file__).parent.parent.parent / "data" / "cache_cluster_patterns.csv"

# Pays pertinents pour EUR/USD
EURUSD_RELEVANT_COUNTRIES = {'US', 'EU', 'DE', 'FR', 'IT', 'ES', 'UK', 'CA', 'CH', 'JP'}

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION PAGE STREAMLIT
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Planificateur V3.0 Clean - Stratégie de Sortie Optimisée",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Planificateur V3.0 Clean - Stratégie de Sortie Optimisée")
st.markdown("**Version 3.0 Clean** - Architecture modulaire avec Random Forest et stratégie de sortie optimisée")

# ═══════════════════════════════════════════════════════════════
# SECTION 1: UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def parse_flexible_date(date_str: str) -> datetime:
    """
    Parse date avec formats multiples (flexible)
    
    Formats acceptés:
    - YYYY-MM-DD, YYYY.MM.DD (ISO)
    - DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY (Européen)
    - DDMMYY (110925) -> 11.09.2025
    - DDMMYYYY (11092025) -> 11.09.2025
    - YYYYMMDD (20250911) -> 2025-09-11
    - DD.MM.YY (11.09.25) -> 11.09.2025
    
    Returns:
        datetime object
    
    Raises:
        ValueError si format non reconnu
    """
    import re
    
    date_str = date_str.strip().replace(' ', '')
    
    # Formats standards avec séparateurs
    formats = [
        '%Y-%m-%d',      # 2025-09-11
        '%Y.%m.%d',      # 2025.09.11
        '%d.%m.%Y',      # 11.09.2025
        '%d/%m/%Y',      # 11/09/2025
        '%d-%m-%Y',      # 11-09-2025
        '%d.%m.%y',      # 11.09.25 (YY = 25 -> 2025)
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # strptime avec %y donne déjà l'année complète dans la plage 1969-2068
            # (00-68 -> 2000-2068, 69-99 -> 1969-1999)
            # Donc "25" -> 2025 directement, pas besoin d'ajustement
            return parsed
        except ValueError:
            continue
    
    # Format YYYY-MMDD (2025-0905) - un seul tiret, pas de séparateur entre mois et jour
    # "2025-0905" = 2025-09-05 (année-mois-jour sans séparateur entre mois et jour)
    if re.match(r'^\d{4}-\d{4}$', date_str):
        year = int(date_str[0:4])
        mdd = date_str[5:9]  # Les 4 chiffres après le tiret
        month = int(mdd[0:2])  # 2 premiers chiffres = mois
        day = int(mdd[2:4])    # 2 derniers chiffres = jour
        try:
            if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        except ValueError:
            pass
    
    # Format YYYY-MDD (2025-905) - un seul tiret, mois sans zéro initial
    if re.match(r'^\d{4}-\d{3}$', date_str):
        parts = date_str.split('-')
        if len(parts) == 2:
            year = int(parts[0])
            mdd = parts[1]
            # 3 chiffres : M-DD (ex: 905 = 9-05)
            month = int(mdd[0])
            day = int(mdd[1:3])
            try:
                if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day)
            except ValueError:
                pass
    
    # Formats sans séparateurs
    # DDMMYY (6 chiffres)
    if re.match(r'^\d{6}$', date_str):
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year_2digits = int(date_str[4:6])
        # Année 20XX si < 50, sinon 19XX
        year = 2000 + year_2digits if year_2digits < 50 else 1900 + year_2digits
        try:
            return datetime(year, month, day)
        except ValueError:
            pass
    
    # DDMMYYYY (8 chiffres) - tester DDMMYYYY d'abord
    if re.match(r'^\d{8}$', date_str):
        # Tester DDMMYYYY (plus probable pour dates récentes)
        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:8])
        try:
            if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
                return datetime(year, month, day)
        except ValueError:
            pass
        
        # Tester YYYYMMDD (format ISO sans séparateurs)
        year = int(date_str[0:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        try:
            if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        except ValueError:
            pass
    
    raise ValueError(
        f"Format date non reconnu: '{date_str}'. "
        f"Formats acceptés: YYYY-MM-DD, YYYY.MM.DD, DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY, "
        f"DDMMYY (110925), DDMMYYYY (11092025), YYYYMMDD (20250911), DD.MM.YY (11.09.25)"
    )


def validate_input(date_str: str, timezone_str: str = "Europe/Zurich", min_pips: float = 35.0) -> Dict:
    """
    Valide les entrées utilisateur avec parsing flexible
    
    Returns:
        {
            'valid': bool,
            'date': datetime or None,
            'timezone': pytz.timezone or None,
            'min_pips': float,
            'error_message': str or None
        }
    """
    try:
        date = parse_flexible_date(date_str)
        tz = pytz.timezone(timezone_str)
        
        # Vérifier période données
        if date < datetime(2023, 1, 1) or date > datetime(2025, 12, 31):
            return {
                'valid': False,
                'date': None,
                'timezone': None,
                'min_pips': min_pips,
                'error_message': f"Date hors période données (2023-2025): {date_str}"
            }
        
        # Valider min_pips
        if min_pips <= 0:
            return {
                'valid': False,
                'date': None,
                'timezone': None,
                'min_pips': min_pips,
                'error_message': f"min_pips doit être > 0 (reçu: {min_pips})"
            }
        
        return {
            'valid': True,
            'date': date,
            'timezone': tz,
            'min_pips': min_pips,
            'error_message': None
        }
    except ValueError as e:
        return {
            'valid': False,
            'date': None,
            'timezone': None,
            'min_pips': min_pips,
            'error_message': str(e)
        }
    except Exception as e:
        return {
            'valid': False,
            'date': None,
            'timezone': None,
            'min_pips': min_pips,
            'error_message': f"Erreur validation: {str(e)}"
        }


def is_event_without_actual(event_key: str, event_title: str) -> bool:
    """
    Identifie les événements sans valeur 'actual' (conférences, discours)
    
    Returns:
        True si l'événement n'a pas de valeur actual mesurable
    """
    if pd.isna(event_title):
        return False
    
    title_lower = str(event_title).lower()
    key_lower = str(event_key).lower()
    
    # Mots-clés indiquant absence d'actual
    keywords = [
        'press conference',
        'conference',
        'speech',
        'testimony',
        'hearing',
        'meeting',
        'minutes',
        'statement'
    ]
    
    return any(keyword in title_lower or keyword in key_lower for keyword in keywords)


# ═══════════════════════════════════════════════════════════════
# SECTION 2: CHARGEMENT DONNÉES
# ═══════════════════════════════════════════════════════════════

def load_events_for_date(
    date: datetime,
    db_path: Path,
    timezone_str: str = "Europe/Zurich",
    min_importance: int = 3,
    countries: Optional[List[str]] = None,
    exclude_no_actual: bool = True
) -> pd.DataFrame:
    """
    Charge événements pour date donnée avec filtres
    
    Args:
        date: Date cible
        db_path: Chemin vers DB DuckDB
        timezone_str: Timezone (défaut: Europe/Zurich)
        min_importance: Importance minimale (1=High, 2=Medium, 3=Low)
        countries: Liste pays à inclure (None = tous)
        exclude_no_actual: Exclure événements sans actual (conférences)
    
    Returns:
        DataFrame avec événements enrichis
    """
    if countries is None:
        countries = list(EURUSD_RELEVANT_COUNTRIES)
    
    conn = duckdb.connect(str(db_path), read_only=True)
    countries_str = "', '".join(countries)
    
    # Les timestamps sont avec timezone, utiliser directement les strings dans la requête
    # Format simple pour DuckDB : 'YYYY-MM-DD HH:MM:SS'
    # IMPORTANT : utiliser le jour suivant comme limite supérieure (ex: '2025-09-12 00:00:00')
    date_str = date.strftime('%Y-%m-%d')
    date_next_str = (date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    # IMPORTANT : Utiliser DATE() avec conversion timezone pour la comparaison
    # Cette syntaxe fonctionne correctement avec TIMESTAMP WITH TIME ZONE
    query_events = f"""
    SELECT 
        e.ts_utc,
        e.country,
        e.event_title,
        e.event_key,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous
    FROM events e
    WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = '{date_str}'
      AND e.importance_n <= {min_importance}
      AND e.country IN ('{countries_str}')
      AND NOT (
        LOWER(e.event_key) LIKE '%press conference%'
        OR LOWER(e.event_key) LIKE '%conference%'
        OR LOWER(e.event_key) LIKE '%speech%'
        OR LOWER(e.event_key) LIKE '%statement%'
        OR LOWER(e.event_key) LIKE '%meeting%'
        OR LOWER(e.event_key) LIKE '%minutes%'
        OR LOWER(e.event_title) LIKE '%press conference%'
        OR LOWER(e.event_title) LIKE '%conference%'
        OR LOWER(e.event_title) LIKE '%speech%'
        OR LOWER(e.event_title) LIKE '%statement%'
        OR LOWER(e.event_title) LIKE '%meeting%'
        OR LOWER(e.event_title) LIKE '%minutes%'
      )
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query_events).df()
    
    # Filtrer en Python pour s'assurer que les événements sont bien dans la date de Berne
    if not df.empty:
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)
        df['ts_bern'] = df['ts_utc'].dt.tz_convert('Europe/Zurich')
        df['date_bern'] = df['ts_bern'].dt.date
        target_date = date.date()
        df = df[df['date_bern'] == target_date].copy()
    
    # Charger les scores empiriques séparément
    if not df.empty:
        query_scores = """
        SELECT DISTINCT
            event_key,
            country,
            empirical_score
        FROM event_families
        WHERE empirical_score IS NOT NULL AND empirical_score > 0
        """
        df_scores = conn.execute(query_scores).df()
        
        # Créer un mapping (event_key, country) -> empirical_score
        scores_dict = {}
        for _, row in df_scores.iterrows():
            key = (row['event_key'], row['country'])
            scores_dict[key] = row['empirical_score']
        
        # Ajouter les scores empiriques
        df['empirical_score'] = df.apply(
            lambda row: scores_dict.get((row['event_key'], row['country']), 0.0),
            axis=1
        )
    
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
    
    # Supprimer doublons (par ex. Current Account DE répété)
    df = df.drop_duplicates(subset=['event_key', 'ts_utc']).reset_index(drop=True)
    
    # Convertir timezone si pas déjà fait (les timestamps sont en UTC pur, convertir vers Europe/Zurich)
    # (UTC+1 en hiver, UTC+2 en été - conversion automatique)
    if 'ts_bern' not in df.columns or df['ts_bern'].isna().any():
        df['ts_utc'] = pd.to_datetime(df['ts_utc'], utc=True)
        df['ts_bern'] = df['ts_utc'].dt.tz_convert('Europe/Zurich')
    
    # Filtrer événements sans actual si demandé
    if exclude_no_actual:
        mask = df.apply(
            lambda row: not is_event_without_actual(row['event_key'], row['event_title']),
            axis=1
        )
        df = df[mask].copy()
    
    # Remplacer NaN empirical_score par 0
    df['empirical_score'] = df['empirical_score'].fillna(0.0)
    
    # Si des scores empiriques sont manquants, essayer de les récupérer avec normalisation
    # (pour matcher les variantes _mom, _yoy, etc.)
    if df['empirical_score'].sum() == 0 or df['empirical_score'].isna().any():
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Charger tous les scores empiriques
        query_scores = """
        SELECT DISTINCT
            event_key,
            country,
            empirical_score
        FROM event_families
        WHERE empirical_score IS NOT NULL AND empirical_score > 0
        """
        df_scores = conn.execute(query_scores).df()
        conn.close()
        
        if not df_scores.empty:
            # Créer un dictionnaire de mapping normalisé
            scores_dict = {}
            for _, row in df_scores.iterrows():
                key_base = normalize_event_key_with_variants(row['event_key'])
                country = row['country']
                score = row['empirical_score']
                scores_dict[(key_base, country)] = max(scores_dict.get((key_base, country), 0), score)
            
            # Remplacer les scores manquants
            for idx, row in df.iterrows():
                if pd.isna(row['empirical_score']) or row['empirical_score'] == 0:
                    key_base = normalize_event_key_with_variants(row['event_key'])
                    country = row['country']
                    matched_score = scores_dict.get((key_base, country), 0.0)
                    if matched_score > 0:
                        df.at[idx, 'empirical_score'] = matched_score
    
    return df


def extract_core_events_for_ui(
    df_events: pd.DataFrame,
    date_str: str,
    db_path: Path,
    support_threshold: float = 0.8,
    jaccard_threshold: float = 0.7,
    years_lookback: int = 5,  # CORRIGÉ: 5 comme dans le pipeline (était 3)
    anchor_time: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Extrait le noyau dur des événements pour l'affichage dans l'UI.
    
    RÉPLIQUE EXACTEMENT LA LOGIQUE DU PIPELINE VALIDÉ :
    1. Cherche noyau dur pré-défini (CORE_EVENTS_{date}.txt, CPI, NFP)
    2. Essaie extraction dynamique avec tous les événements
    3. Si échec, essaie avec pays principal filtré (si multi-pays)
    4. Si échec, utilise tous les événements du cluster
    
    Args:
        df_events: DataFrame avec tous les événements du cluster
        date_str: Date au format YYYY-MM-DD
        db_path: Chemin vers DB DuckDB
        support_threshold: Seuil de support pour noyau dur (défaut: 0.8)
        jaccard_threshold: Seuil Jaccard pour clusters similaires (défaut: 0.7)
        years_lookback: Nombre d'années à regarder en arrière (défaut: 5)
        anchor_time: Heure d'ancrage du cluster (optionnel, pour recharger depuis DB)
    
    Returns:
        DataFrame filtré avec uniquement les événements du noyau dur
    """
    if df_events.empty:
        return df_events
    
    # IMPORTANT: Recharger TOUS les événements à la même heure depuis la DB
    # (comme dans le pipeline ligne 198-209)
    cluster_events = df_events.copy()
    if anchor_time is not None:
        try:
            conn = duckdb.connect(str(db_path), read_only=True)
            if isinstance(anchor_time, pd.Timestamp):
                if anchor_time.tz is None:
                    anchor_time = anchor_time.tz_localize('Europe/Zurich')
                else:
                    anchor_time = anchor_time.tz_convert('Europe/Zurich')
            
            anchor_hour = anchor_time.hour
            anchor_minute = anchor_time.minute
            
            query_all_events = f"""
            SELECT event_key, country, importance_n, ts_utc
            FROM events
            WHERE DATE(ts_utc AT TIME ZONE 'Europe/Zurich') = '{date_str}'
              AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Europe/Zurich') = {anchor_hour}
              AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Europe/Zurich') >= {max(0, anchor_minute - 15)}
              AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Europe/Zurich') <= {min(59, anchor_minute + 15)}
            ORDER BY ts_utc
            """
            cluster_events_all = conn.execute(query_all_events).df()
            cluster_events_all['ts_utc'] = pd.to_datetime(cluster_events_all['ts_utc'])
            conn.close()
            
            if len(cluster_events_all) > len(cluster_events):
                cluster_events = cluster_events_all
        except Exception as e:
            # En cas d'erreur, utiliser les événements déjà chargés
            pass
    
    # ÉTAPE 1: Chercher noyau dur pré-défini (comme pipeline ligne 215-290)
    core_events_file = PROJECT_ROOT / 'docs' / 'VALIDATION' / f'CORE_EVENTS_{date_str.replace("-", "_")}.txt'
    if not core_events_file.exists():
        # Détecter automatiquement le type (CPI ou NFP)
        core_events_file_cpi = PROJECT_ROOT / 'docs' / 'VALIDATION' / 'CORE_EVENTS_CPI.txt'
        core_events_file_nfp = PROJECT_ROOT / 'docs' / 'VALIDATION' / 'CORE_EVENTS_NFP.txt'
        
        importance_map = {1: 'high', 2: 'medium', 3: 'low'}
        events_present_canonical = set()
        
        # Filtrer par pays principal pour la détection
        if 'country' in cluster_events.columns:
            country_counts = cluster_events['country'].value_counts()
            main_country = country_counts.index[0]
            cluster_events_filtered = cluster_events[cluster_events['country'] == main_country].copy()
        else:
            cluster_events_filtered = cluster_events.copy()
        
        for _, event in cluster_events_filtered.iterrows():
            importance_str = importance_map.get(int(event.get('importance_n', 0)), 'unknown')
            canon_id = create_canonical_event_id(
                event.get('event_key', ''),
                event.get('country', ''),
                importance_str
            )
            events_present_canonical.add(canon_id)
        
        # Tester les deux fichiers et choisir celui avec le plus d'intersection
        best_file = None
        best_intersection = 0
        
        if core_events_file_cpi.exists():
            with open(core_events_file_cpi, 'r') as f:
                core_cpi = set([line.strip() for line in f if line.strip()])
            intersection_cpi = len(core_cpi & events_present_canonical)
            if intersection_cpi > best_intersection:
                best_intersection = intersection_cpi
                best_file = core_events_file_cpi
        
        if core_events_file_nfp.exists():
            with open(core_events_file_nfp, 'r') as f:
                core_nfp = set([line.strip() for line in f if line.strip()])
            intersection_nfp = len(core_nfp & events_present_canonical)
            if intersection_nfp > best_intersection:
                best_intersection = intersection_nfp
                best_file = core_events_file_nfp
        
        if best_file and best_intersection > 0:
            core_events_file = best_file
    
    # ÉTAPE 2: Extraire le noyau dur dynamiquement (comme pipeline ligne 332-361)
    core_events = None
    core_events_predefined_set = None
    
    # Si un noyau dur pré-défini existe, le charger
    if core_events_file.exists():
        with open(core_events_file, 'r') as f:
            core_events_predefined_set = set([line.strip() for line in f if line.strip()])
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Essayer d'abord avec tous les événements
    core_events_dynamic = extract_core_events_from_cluster(
        conn=conn,
        cluster_events=cluster_events,
        date_str=date_str,
        support_threshold=support_threshold,
        jaccard_threshold=jaccard_threshold,
        years_lookback=years_lookback
    )
    
    if core_events_dynamic and len(core_events_dynamic) > 0:
        # NOUVEAU : Combiner extraction dynamique avec noyau dur pré-défini
        if core_events_predefined_set:
            # Créer identifiants canoniques pour événements présents
            importance_map = {1: 'high', 2: 'medium', 3: 'low'}
            events_present_canonical = set()
            for _, event in cluster_events.iterrows():
                importance_str = importance_map.get(int(event.get('importance_n', 0)), 'unknown')
                canon_id = create_canonical_event_id(
                    event.get('event_key', ''),
                    event.get('country', ''),
                    importance_str
                )
                events_present_canonical.add(canon_id)
            
            # Intersection : événements du noyau dur pré-défini qui sont présents dans le cluster
            core_events_predefined_present = core_events_predefined_set & events_present_canonical
            
            # UNION : combiner extraction dynamique + noyau dur pré-défini présent
            core_events = core_events_dynamic | core_events_predefined_present
        else:
            core_events = core_events_dynamic
    else:
        # Si échec, essayer avec pays principal filtré (comme pipeline ligne 376-409)
        if 'country' in cluster_events.columns:
            country_counts = cluster_events['country'].value_counts()
            main_country = country_counts.index[0]
            n_events_main = country_counts.iloc[0]
            n_events_total = len(cluster_events)
            
            if len(country_counts) > 1 and n_events_main >= n_events_total * 0.7:
                cluster_events_filtered = cluster_events[cluster_events['country'] == main_country].copy()
                
                core_events = extract_core_events_from_cluster(
                    conn=conn,
                    cluster_events=cluster_events_filtered,
                    date_str=date_str,
                    support_threshold=support_threshold,
                    jaccard_threshold=jaccard_threshold,
                    years_lookback=years_lookback
                )
                
                # Si échec, essayer avec tous les événements
                if not core_events or len(core_events) == 0:
                    core_events = extract_core_events_from_cluster(
                        conn=conn,
                        cluster_events=cluster_events,
                        date_str=date_str,
                        support_threshold=support_threshold,
                        jaccard_threshold=jaccard_threshold,
                        years_lookback=years_lookback
                    )
    
    conn.close()
    
    # Si aucun noyau dur trouvé, essayer avec le noyau dur pré-défini (fallback)
    if not core_events or len(core_events) == 0:
        if core_events_predefined_set:
            # Créer identifiants canoniques pour événements présents
            importance_map = {1: 'high', 2: 'medium', 3: 'low'}
            events_present_canonical = set()
            for _, event in cluster_events.iterrows():
                importance_str = importance_map.get(int(event.get('importance_n', 0)), 'unknown')
                canon_id = create_canonical_event_id(
                    event.get('event_key', ''),
                    event.get('country', ''),
                    importance_str
                )
                events_present_canonical.add(canon_id)
            
            # Utiliser intersection : noyau dur pré-défini présent dans le cluster
            core_events = core_events_predefined_set & events_present_canonical
            
            if not core_events or len(core_events) == 0:
                # Dernier fallback : utiliser tous les événements
                return df_events
        else:
            # Dernier fallback : utiliser tous les événements
            return df_events
    
    # Créer identifiants canoniques et filtrer
    importance_map = {1: 'high', 2: 'medium', 3: 'low'}
    df_events_filtered = df_events.copy()
    
    df_events_filtered['canonical_id'] = df_events_filtered.apply(
        lambda row: create_canonical_event_id(
            row['event_key'],
            row['country'],
            importance_map.get(int(row.get('importance_n', 3)), 'unknown')
        ),
        axis=1
    )
    
    df_core = df_events_filtered[df_events_filtered['canonical_id'].isin(core_events)].copy()
    df_core = df_core.drop(columns=['canonical_id'])
    
    return df_core.reset_index(drop=True)


def load_prices_for_date(
    date: datetime,
    db_path: Path,
    timezone_str: str = "Europe/Zurich"
) -> pd.DataFrame:
    """
    Charge prix 1-minute pour date donnée
    
    Returns:
        DataFrame avec index datetime (timezone) et colonnes: open, high, low, close
    """
    conn = duckdb.connect(str(db_path), read_only=True)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = ?
    ORDER BY datetime
    """
    
    df = conn.execute(query, [date.strftime('%Y-%m-%d')]).df()
    conn.close()
    
    if df.empty:
        return pd.DataFrame()
    
    # Convertir en timezone
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(timezone_str)
    df = df.set_index('datetime')
    
    return df


def load_cache_clusters() -> Optional[pd.DataFrame]:
    """Charge le cache des clusters pré-calculés (nouveau cache catalogué en priorité)"""
    # Essayer d'abord le nouveau cache catalogué
    if CACHE_CLUSTERS_PATH.exists():
        try:
            df = pd.read_csv(CACHE_CLUSTERS_PATH)
            st.info(f"✅ Cache catalogué chargé : {len(df)} clusters uniques avec occurrences historiques")
            return df
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du chargement du cache catalogué : {e}")
    
    # Fallback vers l'ancien cache
    if CACHE_CLUSTERS_PATH_FALLBACK.exists():
        try:
            df = pd.read_csv(CACHE_CLUSTERS_PATH_FALLBACK)
            st.info(f"ℹ️ Ancien cache chargé : {len(df)} clusters")
            return df
        except Exception:
            pass
    
    return None


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
    
    # Créer signature du cluster actuel avec build_cluster_signature
    event_keys = df_events['event_key'].dropna().tolist()
    if not event_keys:
        return None
    
    signature_current = build_cluster_signature(event_keys)
    if not signature_current:
        return None
    
    # Normaliser les clés pour le calcul Jaccard
    normalized_keys = normalize_event_keys_list(event_keys, method='with_variants')
    current_set = set(normalized_keys)
    
    best_match = None
    best_jaccard = 0.0
    
    # Chercher dans le cache (signature exacte ou partielle)
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        # Match exact (signature identique)
        if signature_current == cache_sig:
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
                'jaccard_similarity': 1.0,
                'first_occurrence': row.get('first_occurrence', None),
                'last_occurrence': row.get('last_occurrence', None),
            }
        
        # Match partiel (calcul Jaccard)
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        cache_set = set(cache_normalized)
        
        intersection = current_set & cache_set
        union = current_set | cache_set
        
        if len(union) > 0:
            jaccard = len(intersection) / len(union)
            if jaccard > best_jaccard:
                best_jaccard = jaccard
                best_match = {
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
                    'first_occurrence': row.get('first_occurrence', None),
                    'last_occurrence': row.get('last_occurrence', None),
                }
    
    # Retourner le meilleur match avec seuil adaptatif
    # - Si le cluster a >= 10 occurrences historiques, accepter Jaccard >= 0.45 (clusters très validés)
    # - Si le cluster a >= 4 occurrences, accepter Jaccard >= 0.45 (clusters validés)
    # - Sinon, exiger Jaccard >= 0.5 (clusters rares doivent être plus similaires)
    if best_match:
        n_samples = best_match.get('n_samples', 0)
        min_jaccard = 0.45 if n_samples >= 4 else 0.5
        
        if best_jaccard >= min_jaccard:
            return best_match
    
    return None


def build_cluster_signature(event_keys: List[str]) -> str:
    """
    Construit la signature normalisée d'un cluster (séquence ADN)
    
    Args:
        event_keys: Liste des event_key du cluster
    
    Returns:
        Signature normalisée (clés triées, séparées par |)
    """
    if not event_keys:
        return ""
    
    normalized = normalize_event_keys_list(event_keys, method='with_variants')
    return '|'.join(sorted(set(normalized)))


def identify_cluster_from_date(
    date: datetime,
    db_path: Path,
    df_cache: pd.DataFrame,
    timezone_str: str = "Europe/Zurich",
    window_minutes: int = 30,
    min_importance: int = 1,
    countries: Optional[List[str]] = None,
    jaccard_threshold: float = 0.7,
    movement_time: Optional[datetime] = None,
    window_before_minutes: int = 10,
    window_after_minutes: int = 15
) -> Optional[Dict]:
    """
    IDENTIFIE un cluster à partir d'une date en comparant avec le cache (logique ADN)
    
    Workflow correct : Mouvement détecté → Événements dans fenêtre → Signature ADN → Identification dans cache
    
    Args:
        date: Date à analyser
        db_path: Chemin vers DB
        df_cache: DataFrame du cache clusters (clusters validés historiquement)
        timezone_str: Timezone
        window_minutes: Fenêtre pour regrouper événements (défaut: 30 min) - utilisé si movement_time=None
        min_importance: Importance minimale
        countries: Liste pays (None = tous)
        jaccard_threshold: Seuil de similarité Jaccard (défaut: 0.7)
        movement_time: Heure du mouvement détecté (si fourni, cherche événements autour de cette heure)
        window_before_minutes: Minutes avant le mouvement pour chercher événements (défaut: 10)
        window_after_minutes: Minutes après le mouvement pour chercher événements (défaut: 15)
    
    Returns:
        Dict avec cluster identifié et ses stats, ou None si non trouvé
    """
    if df_cache is None or df_cache.empty:
        return None
    
    # 1. Charger TOUS les événements de la date (sans filtre exclude_no_actual pour l'identification)
    df_events = load_events_for_date(
        date,
        db_path,
        timezone_str,
        min_importance,
        countries,
        exclude_no_actual=False  # Important : inclure tous les événements pour l'identification
    )
    
    if df_events.empty:
        return None
    
    # 2. Si movement_time fourni, chercher les événements dans une fenêtre autour de cette heure
    if movement_time is not None:
        # Normaliser movement_time
        if isinstance(movement_time, pd.Timestamp):
            if movement_time.tz is None:
                movement_time_bern = movement_time.tz_localize(timezone_str)
            else:
                movement_time_bern = movement_time.tz_convert(timezone_str)
        elif isinstance(movement_time, datetime):
            # Si c'est un datetime Python, vérifier s'il a un timezone
            ts = pd.Timestamp(movement_time)
            if ts.tz is None:
                movement_time_bern = ts.tz_localize(timezone_str)
            else:
                movement_time_bern = ts.tz_convert(timezone_str)
        else:
            movement_time_bern = pd.Timestamp(movement_time)
            if movement_time_bern.tz is None:
                movement_time_bern = movement_time_bern.tz_localize(timezone_str)
            else:
                movement_time_bern = movement_time_bern.tz_convert(timezone_str)
        
        # Définir la fenêtre autour du mouvement
        window_start = movement_time_bern - pd.Timedelta(minutes=window_before_minutes)
        window_end = movement_time_bern + pd.Timedelta(minutes=window_after_minutes)
        
        # Filtrer les événements dans cette fenêtre
        mask_window = (df_events['ts_bern'] >= window_start) & (df_events['ts_bern'] <= window_end)
        df_events_window = df_events[mask_window].copy()
        
        if df_events_window.empty:
            return None
        
        # Prioriser les clusters US
        df_us_events = df_events_window[df_events_window['country'] == 'US'].copy()
        
        if df_us_events.empty:
            return None
        
        # Construire le cluster avec tous les événements dans la fenêtre
        # Inclure aussi les événements DE Current Account proches
        df_other_events = df_events_window[df_events_window['country'] != 'US'].copy()
        mask_de = (
            (df_other_events['country'] == 'DE') &
            (df_other_events['ts_bern'] >= window_start) &
            (df_other_events['ts_bern'] <= window_end) &
            (df_other_events['event_key'].str.contains('current account', case=False, na=False))
        )
        events_de_in_window = df_other_events[mask_de]
        
        # Combiner US + DE
        events_in_window = pd.concat([df_us_events, events_de_in_window], ignore_index=True)
        
        # Construire la signature ADN
        event_keys = events_in_window['event_key'].dropna().tolist()
        if event_keys:
            # Identifier dans le cache avec find_cluster_in_cache
            matched_cluster = find_cluster_in_cache(events_in_window, df_cache)
            
            if matched_cluster:
                jaccard = matched_cluster.get('jaccard_similarity', 0.0)
                n_samples = matched_cluster.get('n_samples', 0)
                
                # Utiliser seuil adaptatif : si cluster validé (>= 4 occurrences), accepter Jaccard >= 0.45
                min_jaccard = 0.45 if n_samples >= 4 else jaccard_threshold
                
                if jaccard >= min_jaccard:
                    return {
                        **matched_cluster,
                        'anchor_time': movement_time_bern,
                        'n_events': len(events_in_window),
                        'df_events': events_in_window.copy(),
                        'n_us_events': len(df_us_events),
                        'signature_current': build_cluster_signature(event_keys)
                    }
        
        return None
    
    # 3. Si pas de movement_time, utiliser l'ancienne logique (par fenêtres temporelles)
    df_events = df_events.sort_values('ts_bern').reset_index(drop=True)
    df_us_events = df_events[df_events['country'] == 'US'].copy()
    
    if df_us_events.empty:
        return None
    
    # Pour chaque fenêtre temporelle, construire la signature ADN et identifier dans le cache
    best_match = None
    best_jaccard = 0.0
    processed_indices = set()
    
    for i in range(len(df_us_events)):
        if i in processed_indices:
            continue
        
        anchor_time = df_us_events.iloc[i]['ts_bern']
        window_end = anchor_time + pd.Timedelta(minutes=window_minutes)
        
        # Trouver tous les événements US dans cette fenêtre
        mask_us = (df_us_events['ts_bern'] >= anchor_time) & (df_us_events['ts_bern'] <= window_end)
        events_us_in_window = df_us_events[mask_us]
        
        # Marquer tous les indices de cette fenêtre comme traités
        processed_indices.update(events_us_in_window.index.tolist())
        
        if len(events_us_in_window) > 0:
            # Inclure aussi les événements DE Current Account proches (jusqu'à 15 min après)
            df_other_events = df_events[df_events['country'] != 'US'].copy()
            window_de_end = anchor_time + pd.Timedelta(minutes=15)
            mask_de = (
                (df_other_events['country'] == 'DE') &
                (df_other_events['ts_bern'] >= anchor_time) &
                (df_other_events['ts_bern'] <= window_de_end) &
                (df_other_events['event_key'].str.contains('current account', case=False, na=False))
            )
            events_de_in_window = df_other_events[mask_de]
            
            # Combiner US + DE
            events_in_window = pd.concat([events_us_in_window, events_de_in_window], ignore_index=True)
            
            # Construire la signature ADN
            event_keys = events_in_window['event_key'].dropna().tolist()
            if event_keys:
                # Identifier dans le cache avec find_cluster_in_cache
                matched_cluster = find_cluster_in_cache(events_in_window, df_cache)
                
                if matched_cluster:
                    jaccard = matched_cluster.get('jaccard_similarity', 0.0)
                    
                    # Garder le meilleur match
                    if jaccard >= jaccard_threshold and jaccard > best_jaccard:
                        best_jaccard = jaccard
                        best_match = {
                            **matched_cluster,  # Inclut tous les champs du cache (impact, pattern, etc.)
                            'anchor_time': anchor_time,
                            'n_events': len(events_in_window),
                            'df_events': events_in_window.copy(),
                            'n_us_events': len(events_us_in_window),
                            'signature_current': build_cluster_signature(event_keys)
                        }
    
    return best_match


def build_clusters_for_date(
    date: datetime,
    db_path: Path,
    timezone_str: str = "Europe/Zurich",
    window_minutes: int = 30,
    min_importance: int = 3,
    countries: Optional[List[str]] = None,
    exclude_no_actual: bool = True
) -> List[Dict]:
    """
    Construit tous les clusters d'événements pour une date donnée
    
    Args:
        date: Date cible
        db_path: Chemin vers DB
        timezone_str: Timezone
        window_minutes: Fenêtre temporelle pour regrouper événements (défaut: 30 min)
        min_importance: Importance minimale
        countries: Liste pays (None = tous)
        exclude_no_actual: Exclure événements sans actual
    
    Returns:
        Liste de dicts avec cluster_signature, event_keys, anchor_time, etc.
    """
    # Charger événements pour cette date
    df_events = load_events_for_date(
        date,
        db_path,
        timezone_str,
        min_importance,
        countries,
        exclude_no_actual
    )
    
    if df_events.empty:
        return []
    
    # Grouper par fenêtre temporelle, en priorisant les clusters US
    clusters = []
    df_events = df_events.sort_values('ts_bern').reset_index(drop=True)
    
    # Séparer les événements US des autres
    df_us_events = df_events[df_events['country'] == 'US'].copy()
    df_other_events = df_events[df_events['country'] != 'US'].copy()
    
    # 1. Construire clusters à partir des événements US (priorité)
    i = 0
    while i < len(df_us_events):
        anchor_time = df_us_events.iloc[i]['ts_bern']
        window_end = anchor_time + pd.Timedelta(minutes=window_minutes)
        
        # Trouver tous les événements US dans cette fenêtre
        mask_us = (df_us_events['ts_bern'] >= anchor_time) & (df_us_events['ts_bern'] <= window_end)
        events_us_in_window = df_us_events[mask_us]
        
        if len(events_us_in_window) > 0:
            # Inclure aussi les événements DE Current Account proches (jusqu'à 15 min après)
            window_de_end = anchor_time + pd.Timedelta(minutes=15)
            mask_de = (
                (df_other_events['country'] == 'DE') &
                (df_other_events['ts_bern'] >= anchor_time) &
                (df_other_events['ts_bern'] <= window_de_end) &
                (df_other_events['event_key'].str.contains('current account', case=False, na=False))
            )
            events_de_in_window = df_other_events[mask_de]
            
            # Combiner US + DE
            events_in_window = pd.concat([events_us_in_window, events_de_in_window], ignore_index=True)
            events_in_window = events_in_window.sort_values('ts_bern').reset_index(drop=True)
            
            event_keys = events_in_window['event_key'].dropna().tolist()
            if event_keys:
                signature = build_cluster_signature(event_keys)
                if signature:
                    clusters.append({
                        'cluster_signature': signature,
                        'event_keys': event_keys,
                        'anchor_time': anchor_time,
                        'n_events': len(events_in_window),
                        'df_events': events_in_window.copy()
                    })
        
        # Passer au prochain événement US après la fenêtre
        i = df_us_events[df_us_events['ts_bern'] > window_end].index
        if len(i) == 0:
            break
        i = i[0]
    
    # 2. Construire clusters pour les autres pays (si pas déjà inclus dans un cluster US)
    # On évite de créer des clusters ECB isolés si on a déjà des clusters US
    if len(clusters) == 0:  # Seulement si aucun cluster US trouvé
        i = 0
        while i < len(df_other_events):
            anchor_time = df_other_events.iloc[i]['ts_bern']
            window_end = anchor_time + pd.Timedelta(minutes=window_minutes)
            
            mask = (df_other_events['ts_bern'] >= anchor_time) & (df_other_events['ts_bern'] <= window_end)
            events_in_window = df_other_events[mask]
            
            if len(events_in_window) > 0:
                event_keys = events_in_window['event_key'].dropna().tolist()
                if event_keys:
                    signature = build_cluster_signature(event_keys)
                    if signature:
                        clusters.append({
                            'cluster_signature': signature,
                            'event_keys': event_keys,
                            'anchor_time': anchor_time,
                            'n_events': len(events_in_window),
                            'df_events': events_in_window.copy()
                        })
            
            i = df_other_events[df_other_events['ts_bern'] > window_end].index
            if len(i) == 0:
                break
            i = i[0]
    
    return clusters


def search_future_clusters(
    date_from: datetime,
    date_to: datetime,
    db_path: Path,
    df_cache: pd.DataFrame,
    timezone_str: str = "Europe/Zurich",
    window_minutes: int = 30,
    min_importance: int = 3,
    countries: Optional[List[str]] = None,
    exclude_no_actual: bool = True,
    min_impact: float = 0.0,
    min_samples: int = 1,
    min_events: int = 1,
    jaccard_threshold: float = 0.8
) -> List[Dict]:
    """
    Recherche les clusters historiques qui se reproduisent dans le futur
    
    Workflow:
    1. Pour chaque cluster du cache (historique)
    2. Chercher où il se reproduit dans la période future
    3. Retourner liste des clusters à venir avec dates et stats
    
    Args:
        date_from: Date début période recherche
        date_to: Date fin période recherche
        db_path: Chemin vers DB
        df_cache: DataFrame du cache clusters historiques
        timezone_str: Timezone
        window_minutes: Fenêtre pour regrouper événements
        min_importance: Importance minimale
        countries: Liste pays
        exclude_no_actual: Exclure événements sans actual
        min_impact: Impact médian minimum (filtre)
        min_samples: Occurrences minimum (filtre)
        min_events: Nombre minimum d'événements par cluster (filtre)
        jaccard_threshold: Seuil Jaccard pour match (défaut: 0.8)
    
    Returns:
        Liste de dicts avec:
        {
            'date': date,
            'cluster_signature': str,
            'anchor_time': datetime,
            'impact_median': float,
            'n_samples': int,
            'dominant_pattern': str,
            'dominant_direction': str,
            'jaccard_similarity': float,
            'event_keys': List[str],
            'df_events': DataFrame
        }
    """
    if df_cache is None or df_cache.empty:
        return []
    
    results = []
    
    # Normaliser signatures du cache
    cache_signatures = {}
    for idx, row in df_cache.iterrows():
        cache_sig = str(row.get('cluster_signature', ''))
        if pd.isna(cache_sig) or cache_sig == '':
            continue
        
        # Normaliser signature cache
        cache_keys = cache_sig.split('|')
        cache_normalized = normalize_event_keys_list(cache_keys, method='with_variants')
        signature_normalized = '|'.join(sorted(set(cache_normalized)))
        
        # Filtrer par impact/occurrences/nombre d'événements
        impact_med = row.get('impact_median', 0)
        n_samples = row.get('n_samples', 0)
        num_events = row.get('num_events_median', 0)
        
        if impact_med < min_impact or n_samples < min_samples or num_events < min_events:
            continue
        
        cache_signatures[signature_normalized] = {
            'original_signature': cache_sig,
            'impact_median': impact_med,
            'impact_mean': row.get('impact_mean', None),
            'n_samples': n_samples,
            'dominant_pattern': row.get('dominant_pattern', None),
            'dominant_direction': row.get('dominant_direction', None),
            'latency_median': row.get('latency_median', None),
            'ttr_median': row.get('ttr_median', None),
            'pullback_median': row.get('pullback_median', None),
        }
    
    if not cache_signatures:
        return []
    
    # Scanner toutes les dates de la période
    current_date = date_from
    while current_date <= date_to:
        # Construire clusters pour cette date
        clusters_today = build_clusters_for_date(
            current_date,
            db_path,
            timezone_str,
            window_minutes,
            min_importance,
            countries,
            exclude_no_actual
        )
        
        # Pour chaque cluster trouvé aujourd'hui, chercher match dans cache
        for cluster in clusters_today:
            cluster_sig = cluster['cluster_signature']
            
            # Normaliser signature cluster actuel
            cluster_keys = cluster_sig.split('|')
            cluster_normalized = normalize_event_keys_list(cluster_keys, method='with_variants')
            signature_normalized = '|'.join(sorted(set(cluster_normalized)))
            
            # Chercher match exact ou partiel dans cache
            matched_cache = None
            jaccard = 1.0
            
            if signature_normalized in cache_signatures:
                # Match exact
                matched_cache = cache_signatures[signature_normalized]
            else:
                # Match partiel (Jaccard)
                cluster_set = set(cluster_normalized)
                best_jaccard = 0.0
                best_match = None
                
                for cache_sig_norm, cache_data in cache_signatures.items():
                    cache_set = set(cache_sig_norm.split('|'))
                    intersection = cluster_set & cache_set
                    if len(intersection) > 0:
                        j = len(intersection) / len(cluster_set | cache_set)
                        if j > best_jaccard and j >= jaccard_threshold:
                            best_jaccard = j
                            best_match = cache_data
                
                if best_match:
                    matched_cache = best_match
                    jaccard = best_jaccard
            
            if matched_cache:
                results.append({
                    'date': current_date.date(),
                    'cluster_signature': matched_cache['original_signature'],
                    'anchor_time': cluster['anchor_time'],
                    'impact_median': matched_cache['impact_median'],
                    'impact_mean': matched_cache.get('impact_mean'),
                    'n_samples': matched_cache['n_samples'],
                    'dominant_pattern': matched_cache.get('dominant_pattern', 'INCONNU'),
                    'dominant_direction': matched_cache.get('dominant_direction', 'UNKNOWN'),
                    'latency_median': matched_cache.get('latency_median'),
                    'ttr_median': matched_cache.get('ttr_median'),
                    'pullback_median': matched_cache.get('pullback_median'),
                    'jaccard_similarity': jaccard,
                    'event_keys': cluster['event_keys'],
                    'n_events': cluster['n_events'],
                    'df_events': cluster['df_events']
                })
        
        current_date += timedelta(days=1)
    
    # Trier par date puis par impact
    results.sort(key=lambda x: (x['date'], -x['impact_median']))
    
    return results


# ═══════════════════════════════════════════════════════════════
# SECTION 3: ENRICHISSEMENT ÉVÉNEMENTS
# ═══════════════════════════════════════════════════════════════

def enrich_events_with_surprises(df_events: pd.DataFrame) -> pd.DataFrame:
    """
    Enrichit les événements avec calcul des surprises et scores ajustés
    
    Args:
        df_events: DataFrame avec colonnes: actual, estimate, forecast, previous, empirical_score
    
    Returns:
        DataFrame enrichi avec colonnes: surprise, surprise_pct, score_adjusted
    """
    df_enriched = df_events.copy()
    
    # Calculer surprise (priorité: actual vs estimate, sinon forecast, sinon previous)
    surprises = []
    surprises_pct = []
    scores_adjusted = []
    
    for idx, row in df_enriched.iterrows():
        actual = row.get('actual')
        estimate = row.get('estimate')
        forecast = row.get('forecast')
        previous = row.get('previous')
        score = row.get('empirical_score', 0.0)
        
        # Déterminer valeur de référence pour surprise
        reference = None
        if pd.notna(estimate) and estimate != 0:
            reference = estimate
        elif pd.notna(forecast) and forecast != 0:
            reference = forecast
        elif pd.notna(previous) and previous != 0:
            reference = previous
        
        # Calculer surprise
        if pd.notna(actual) and reference is not None and reference != 0:
            surprise = actual - reference
            surprise_pct = (surprise / abs(reference)) * 100
        else:
            surprise = 0.0
            surprise_pct = 0.0
        
        surprises.append(surprise)
        surprises_pct.append(surprise_pct)
        
        # Score ajusté selon surprise (Session 55, formule validée)
        adjusted_score = calculate_adjusted_empirical_score(score, surprise_pct)
        scores_adjusted.append(adjusted_score)
    
    df_enriched['surprise'] = surprises
    df_enriched['surprise_pct'] = surprises_pct
    df_enriched['score_adjusted'] = scores_adjusted
    
    return df_enriched


# ═══════════════════════════════════════════════════════════════
# SECTION 4: DÉTECTION PATTERN (WORKFLOW CORRECT)
# ═══════════════════════════════════════════════════════════════

def find_extrema_improved(prices: pd.DataFrame, window_minutes: int = 10) -> List[Dict]:
    """
    Trouve les extrema locaux avec une fenêtre glissante
    Basé sur la méthode validée Session 107
    """
    extrema = []
    window_size = window_minutes
    
    # S'assurer que prices a une colonne datetime ou utiliser l'index
    if 'datetime' not in prices.columns:
        prices = prices.copy()
        prices['datetime'] = prices.index
    
    for i in range(window_size, len(prices) - window_size):
        # Peak local : high plus élevé que les window_size minutes avant et après
        if prices.iloc[i]['high'] == prices.iloc[i-window_size:i+window_size+1]['high'].max():
            extrema.append({
                'type': 'HIGH',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['high']
            })
        
        # Trough local : low plus bas que les window_size minutes avant et après
        if prices.iloc[i]['low'] == prices.iloc[i-window_size:i+window_size+1]['low'].min():
            extrema.append({
                'type': 'LOW',
                'index': i,
                'datetime': prices.iloc[i]['datetime'],
                'price': prices.iloc[i]['low']
            })
    
    # Filtrer par distance temporelle (au moins 1h entre extrema)
    filtered = []
    for ext in extrema:
        too_close = False
        for prev in filtered:
            time_diff = abs((ext['datetime'] - prev['datetime']).total_seconds() / 3600)
            if time_diff < 1.0:
                too_close = True
                break
        if not too_close:
            filtered.append(ext)
    
    filtered.sort(key=lambda x: x['index'])
    return filtered


def detect_inversions_from_extrema(extrema: List[Dict], prices: pd.DataFrame,
                                   min_amplitude_pips: float = 30.0) -> List[Dict]:
    """Détecte les inversions de tendance entre extrema"""
    inversions = []
    
    # S'assurer que prices a une colonne datetime
    if 'datetime' not in prices.columns:
        prices = prices.copy()
        prices['datetime'] = prices.index
    
    for i in range(len(extrema) - 1):
        ext1 = extrema[i]
        ext2 = extrema[i + 1]
        
        # Inversion HIGH→LOW (PEAK)
        if ext1['type'] == 'HIGH' and ext2['type'] == 'LOW':
            start_idx = ext1['index']
            end_idx = ext2['index']
            if end_idx > start_idx:
                segment = prices.iloc[start_idx:end_idx+1]
                amplitude = (segment['high'].max() - segment['low'].min()) * 10000
                if amplitude >= min_amplitude_pips:
                    inversions.append({
                        'type': 'PEAK',
                        'datetime': ext1['datetime'],
                        'price': ext1['price'],
                        'amplitude': amplitude,
                        'start_idx': start_idx,
                        'end_idx': end_idx
                    })
        
        # Inversion LOW→HIGH (TROUGH)
        elif ext1['type'] == 'LOW' and ext2['type'] == 'HIGH':
            start_idx = ext1['index']
            end_idx = ext2['index']
            if end_idx > start_idx:
                segment = prices.iloc[start_idx:end_idx+1]
                amplitude = (segment['high'].max() - segment['low'].min()) * 10000
                if amplitude >= min_amplitude_pips:
                    inversions.append({
                        'type': 'TROUGH',
                        'datetime': ext1['datetime'],
                        'price': ext1['price'],
                        'amplitude': amplitude,
                        'start_idx': start_idx,
                        'end_idx': end_idx
                    })
    
    return inversions


def detect_movements_from_inversions(inversions: List[Dict], prices: pd.DataFrame,
                                     min_impact_pips: float = 35.0) -> List[Dict]:
    """Détecte les mouvements forts depuis les inversions"""
    movements = []
    
    # S'assurer que prices a une colonne datetime
    if 'datetime' not in prices.columns:
        prices = prices.copy()
        prices['datetime'] = prices.index
    
    for inv in inversions:
        start_idx = inv['start_idx']
        end_idx = inv['end_idx']
        segment = prices.iloc[start_idx:end_idx+1]
        
        if len(segment) < 10:
            continue
        
        if inv['type'] == 'TROUGH':  # Mouvement UP
            baseline_price = segment.iloc[0]['low']
            peak_price = segment['high'].max()
            peak_idx = segment['high'].idxmax()
            impact_pips = (peak_price - baseline_price) * 10000
            direction = 'UP'
            
            # Trouver le vrai début : remonter AVANT le segment
            start_time = segment.iloc[0]['datetime']
            start_idx_in_prices = start_idx
            
            search_back_minutes = 30
            search_back_start = max(0, start_idx - search_back_minutes)
            
            for j in range(start_idx - 1, search_back_start - 1, -1):
                if j < 0 or j >= len(prices):
                    break
                check_row = prices.iloc[j]
                check_impact = (check_row['high'] - baseline_price) * 10000
                if check_impact >= 5.0:  # seuil pour trouver le début progressif
                    start_time = check_row['datetime']
                    start_idx_in_prices = j
                else:
                    break
            
            peak_time = segment.loc[peak_idx, 'datetime']
        else:  # PEAK - Mouvement DOWN
            baseline_price = segment.iloc[0]['high']
            trough_price = segment['low'].min()
            trough_idx = segment['low'].idxmin()
            impact_pips = (baseline_price - trough_price) * 10000
            direction = 'DOWN'
            
            start_time = segment.iloc[0]['datetime']
            start_idx_in_prices = start_idx
            
            search_back_minutes = 30
            search_back_start = max(0, start_idx - search_back_minutes)
            
            for j in range(start_idx - 1, search_back_start - 1, -1):
                if j < 0 or j >= len(prices):
                    break
                check_row = prices.iloc[j]
                check_impact = (baseline_price - check_row['low']) * 10000
                if check_impact >= 5.0:
                    start_time = check_row['datetime']
                    start_idx_in_prices = j
                else:
                    break
            
            peak_time = segment.loc[trough_idx, 'datetime']
        
        if impact_pips < min_impact_pips:
            continue
        
        movements.append({
            'start_time': start_time,
            'peak_time': peak_time,
            'impact_pips': impact_pips,
            'direction': direction,
            'baseline_price': baseline_price
        })
    
    return movements


def scan_price_movements(
    df_prices: pd.DataFrame,
    min_pips: float = 35.0,
    window_minutes: int = 60
) -> List[Dict]:
    """
    Scanne les prix pour détecter des mouvements significatifs
    MÉTHODE D'INVERSION DE TENDANCE (Session 107)
    
    Workflow Correct: Prix → Mouvement → Pattern
    
    Args:
        df_prices: DataFrame avec index datetime et colonnes: open, high, low, close
        min_pips: Seuil minimum en pips pour considérer un mouvement
        window_minutes: Fenêtre pour détection extrema (défaut: 10 minutes)
    
    Returns:
        Liste de dictionnaires avec mouvements détectés:
        {
            'start_time': datetime,
            'peak_time': datetime,
            'impact_pips': float,
            'direction': 'UP' | 'DOWN',
            'baseline_price': float
        }
    """
    if df_prices.empty:
        return []
    
    # Préparer DataFrame avec colonne datetime
    prices = df_prices.copy()
    if 'datetime' not in prices.columns:
        prices['datetime'] = prices.index
    
    # 0. Détecter d'abord les mouvements EXPLOSIFS (>= 15 pips en une minute)
    # Ces mouvements sont souvent manqués par la méthode d'inversion car trop rapides
    explosive_movements = []
    for i in range(len(prices) - 1):
        current = prices.iloc[i]
        next_candle = prices.iloc[i + 1]
        
        # Calculer le mouvement dans la bougie suivante
        candle_range = (next_candle['high'] - next_candle['low']) * 10000  # En pips
        
        # Calculer aussi le mouvement "extreme" entre bougies consécutives
        # (low de la bougie actuelle → high de la bougie suivante, ou vice versa)
        move_extreme_up = (next_candle['high'] - current['low']) * 10000
        move_extreme_down = (current['high'] - next_candle['low']) * 10000
        
        # Utiliser le mouvement le plus significatif
        max_move = max(candle_range, move_extreme_up, move_extreme_down)
        
        # Si mouvement explosif (>= 15 pips dans une bougie OU entre deux bougies)
        if max_move >= 15.0:
            # Déterminer la direction et l'impact
            if move_extreme_up >= move_extreme_down and move_extreme_up >= candle_range:
                # Mouvement UP dominant
                direction = 'UP'
                baseline_price = current['low']
                peak_price = next_candle['high']
                impact_pips = move_extreme_up
            elif move_extreme_down >= candle_range:
                # Mouvement DOWN dominant
                direction = 'DOWN'
                baseline_price = current['high']
                peak_price = next_candle['low']
                impact_pips = move_extreme_down
            else:
                # Mouvement dans la bougie elle-même
                if next_candle['close'] > current['close']:
                    direction = 'UP'
                    baseline_price = current['low']
                    peak_price = next_candle['high']
                    impact_pips = (peak_price - baseline_price) * 10000
                else:
                    direction = 'DOWN'
                    baseline_price = current['high']
                    peak_price = next_candle['low']
                    impact_pips = (baseline_price - peak_price) * 10000
            
            # Pour les mouvements explosifs, utiliser un seuil réduit
            # Car un mouvement explosif de 15-20 pips est déjà très significatif
            # même s'il ne dépasse pas le seuil général de 35 pips
            min_explosive_pips = max(15.0, min_pips * 0.4)  # Au moins 15 pips, ou 40% du seuil normal
            
            # Vérifier que l'impact est significatif (seuil réduit pour explosifs)
            if impact_pips >= min_explosive_pips:
                start_time = current['datetime'] if 'datetime' in current else prices.index[i]
                peak_time = next_candle['datetime'] if 'datetime' in next_candle else prices.index[i + 1]
                
                explosive_movements.append({
                    'start_time': start_time,
                    'peak_time': peak_time,
                    'impact_pips': impact_pips,
                    'direction': direction,
                    'baseline_price': baseline_price,
                    'is_explosive': True  # Marquer comme explosif
                })
    
    # 0.5. Détecter les mouvements PROGRESSIFS (cumulés sur plusieurs bougies)
    # Pour capturer les mouvements qui ne sont pas explosifs mais significatifs sur plusieurs minutes
    # IMPORTANT : Les mouvements progressifs utilisent un seuil réduit (70% du seuil normal)
    # car ils sont cumulés et peuvent être légèrement en dessous du seuil explosif
    progressive_movements = []
    window_minutes_progressive = 10  # Fenêtre de 10 minutes pour calculer le mouvement cumulé
    min_cumulative_pips = max(min_pips * 0.7, 20.0)  # 70% du seuil normal, au moins 20 pips
    
    for i in range(len(prices) - window_minutes_progressive):
        start_candle = prices.iloc[i]
        start_time = start_candle['datetime'] if 'datetime' in start_candle else prices.index[i]
        
        # Calculer le mouvement cumulé sur les N prochaines bougies
        end_idx = min(i + window_minutes_progressive, len(prices) - 1)
        window_prices = prices.iloc[i:end_idx + 1]
        
        if len(window_prices) < 2:
            continue
        
        start_price = start_candle['open']
        end_price = window_prices.iloc[-1]['close']
        high_price = window_prices['high'].max()
        low_price = window_prices['low'].min()
        
        # Calculer le mouvement total
        move_up = (high_price - start_price) * 10000
        move_down = (start_price - low_price) * 10000
        
        # Déterminer la direction dominante
        if move_up > move_down and move_up >= min_cumulative_pips:
            direction = 'UP'
            impact_pips = move_up
            baseline_price = start_price
            peak_price = high_price
            peak_time = window_prices['high'].idxmax()
        elif move_down > move_up and move_down >= min_cumulative_pips:
            direction = 'DOWN'
            impact_pips = move_down
            baseline_price = start_price
            peak_price = low_price
            peak_time = window_prices['low'].idxmin()
        else:
            continue  # Mouvement insuffisant
        
        # Vérifier que ce mouvement n'est pas déjà capturé par un mouvement explosif
        is_duplicate = False
        for exp_mov in explosive_movements:
            time_diff = abs((pd.Timestamp(start_time) - pd.Timestamp(exp_mov['start_time'])).total_seconds() / 60)
            if time_diff < 5:  # Moins de 5 minutes de différence
                is_duplicate = True
                break
        
        if not is_duplicate:
            progressive_movements.append({
                'start_time': start_time,
                'peak_time': peak_time if 'datetime' in window_prices.loc[peak_time] else peak_time,
                'impact_pips': impact_pips,
                'direction': direction,
                'baseline_price': baseline_price,
                'is_progressive': True  # Marquer comme progressif
            })
    
    # 1. Trouver extrema
    extrema = find_extrema_improved(prices, window_minutes=10)
    
    # Si pas assez d'extrema mais des mouvements explosifs ou progressifs, les retourner
    if len(extrema) < 2:
        if len(explosive_movements) > 0:
            return explosive_movements
        if len(progressive_movements) > 0:
            return progressive_movements
        return []
    
    # 2. Détecter inversions
    inversions = detect_inversions_from_extrema(extrema, prices, min_amplitude_pips=30.0)
    
    # 3. Détecter mouvements depuis inversions
    movements = []
    if len(inversions) > 0:
        movements = detect_movements_from_inversions(inversions, prices, min_impact_pips=min_pips)
    
    # Si aucun mouvement d'inversion mais des mouvements explosifs ou progressifs, les utiliser
    if len(movements) == 0:
        if len(explosive_movements) > 0:
            return explosive_movements
        if len(progressive_movements) > 0:
            return progressive_movements
    
    # 4. Combiner tous les types de mouvements
    # Priorité : explosifs > progressifs > inversions
    all_movements = explosive_movements + progressive_movements + movements
    
    # Filtrer mouvements trop proches (garder le plus fort, prioriser : explosifs > progressifs > inversions)
    if len(all_movements) > 1:
        # Trier : explosifs d'abord, puis progressifs, puis par impact
        def movement_priority(mov):
            if mov.get('is_explosive', False):
                return (3, mov['impact_pips'])
            elif mov.get('is_progressive', False):
                return (2, mov['impact_pips'])
            else:
                return (1, mov['impact_pips'])
        
        movements_sorted = sorted(
            all_movements, 
            key=movement_priority, 
            reverse=True
        )
        filtered = []
        for mov in movements_sorted:
            too_close = False
            for existing in filtered:
                time_diff = abs((pd.Timestamp(mov['start_time']) - pd.Timestamp(existing['start_time'])).total_seconds() / 60)
                if time_diff < 30:  # Moins de 30 minutes
                    # Prioriser : explosifs > progressifs > inversions
                    mov_priority = movement_priority(mov)[0]
                    existing_priority = movement_priority(existing)[0]
                    if mov_priority > existing_priority:
                        filtered.remove(existing)
                        filtered.append(mov)
                        too_close = False  # On a remplacé, donc pas trop proche
                    else:
                        too_close = True
                    break
            if not too_close:
                filtered.append(mov)
        movements = filtered
    else:
        movements = all_movements
    
    return movements


def enrich_pattern_with_finnhub(
    pattern_result: Dict,
    movement_time: Optional[datetime],
    date: Optional[datetime] = None
) -> Dict:
    """
    Enrichit un résultat de détection de pattern avec les patterns Finnhub.
    
    Parameters
    ----------
    pattern_result : Dict
        Résultat de detect_pattern_type
    movement_time : Optional[datetime]
        Heure du mouvement détecté
    date : Optional[datetime]
        Date pour charger les patterns (défaut: date du mouvement)
    
    Returns
    -------
    Dict
        pattern_result enrichi avec finnhub_patterns et confidence_boost
    """
    if movement_time is None:
        return pattern_result
    
    try:
        # Charger patterns Finnhub pour la date
        if date is None:
            if isinstance(movement_time, datetime):
                date = movement_time.date()
                date = datetime.combine(date, datetime.min.time())
            else:
                date = datetime.now()
        
        finnhub_patterns = load_finnhub_patterns(
            date=date,
            db_path=DB_PATH,
            window_hours=24
        )
        
        if not finnhub_patterns.empty:
            # Comparer avec le pattern détecté
            match_result = match_finnhub_pattern_to_detection(
                detected_pattern=pattern_result.get('pattern_type', ''),
                finnhub_patterns=finnhub_patterns,
                movement_time=movement_time,
                window_minutes=120
            )
            
            # Ajouter les informations Finnhub au résultat
            pattern_result['finnhub_match'] = match_result
            pattern_result['finnhub_patterns'] = match_result.get('finnhub_patterns', [])
            
            # Ajuster la confiance si match trouvé
            if match_result.get('match_found', False):
                confidence_boost = match_result.get('confidence_boost', 0.0)
                current_confidence = pattern_result.get('detection_confidence', 0.0)
                pattern_result['detection_confidence'] = min(1.0, current_confidence + confidence_boost)
                pattern_result['finnhub_confidence_boost'] = confidence_boost
    except Exception as e:
        # En cas d'erreur, continuer sans patterns Finnhub
        pattern_result['finnhub_error'] = str(e)
        pattern_result['finnhub_patterns'] = []
    
    return pattern_result


def enrich_prediction_with_support_resistance(
    prediction_result: Dict,
    baseline_price: Optional[float],
    resolution: str = 'H1'
) -> Dict:
    """
    Enrichit une prédiction avec les niveaux Support/Résistance Finnhub.
    
    Parameters
    ----------
    prediction_result : Dict
        Résultat de prédiction (contient prediction_pips, etc.)
    baseline_price : Optional[float]
        Prix de base pour calculer le prix prédit
    resolution : str
        Résolution pour charger les niveaux (défaut: H1)
    
    Returns
    -------
    Dict
        prediction_result enrichi avec support_resistance
    """
    if baseline_price is None:
        prediction_result['support_resistance'] = {
            'available': False,
            'reason': 'Prix de base non disponible'
        }
        return prediction_result
    
    # Support/Résistance désactivé (modules supprimés)
    # try:
    #     # Charger niveaux Support/Résistance
    #     levels_df = load_support_resistance(
    #         db_path=DB_PATH,
    #         resolution=resolution
    #     )
    #     
    #     if levels_df.empty:
    #         prediction_result['support_resistance'] = {
    #             'available': False,
    #             'reason': 'Aucun niveau disponible'
    #         }
    #         return prediction_result
    #     
    #     # Calculer le prix prédit
    #     prediction_pips = prediction_result.get('prediction_pips', 0)
    #     direction = prediction_result.get('direction', 'UP')
    #     
    #     if direction == 'UP':
    #         predicted_price = baseline_price + prediction_pips / 10000
    #     else:
    #         predicted_price = baseline_price - prediction_pips / 10000
    #     
    #     # Trouver les niveaux proches
    #     nearest_levels = find_nearest_levels(levels_df, baseline_price, max_distance_pips=100)
    #     
    #     # Valider la prédiction contre les niveaux
    #     validation = validate_prediction_against_levels(
    #         predicted_price=predicted_price,
    #         levels=levels_df,
    #         tolerance_pips=20.0
    #     )
        
        # Ajouter les informations au résultat
        # Support/Résistance désactivé (modules supprimés)
        # prediction_result['support_resistance'] = {
        #     'available': True,
        #     'baseline_price': baseline_price,
        #     'predicted_price': predicted_price,
        #     'nearest_support': nearest_levels.get('nearest_support'),
        #     'nearest_resistance': nearest_levels.get('nearest_resistance'),
        #     'support_distance_pips': nearest_levels.get('support_distance_pips'),
        #     'resistance_distance_pips': nearest_levels.get('resistance_distance_pips'),
        #     'all_supports': nearest_levels.get('all_supports', [])[:3],  # Top 3
        #     'all_resistances': nearest_levels.get('all_resistances', [])[:3],  # Top 3
        #     'validation': validation,
        #     'resolution': resolution
        # }
    # Support/Résistance désactivé (modules supprimés)
    prediction_result['support_resistance'] = {
        'available': False,
        'reason': 'Module support/resistance désactivé'
    }
    
    return prediction_result


def detect_pattern_type(
    df_prices: pd.DataFrame,
    df_events: pd.DataFrame,
    min_pips: float = 35.0,
    timezone: pytz.timezone = None,
    cluster_anchor_time: Optional[datetime] = None,
    use_finnhub_patterns: bool = True,
    silent_warning: bool = False
) -> Dict:
    """
    Détecte le type de pattern (Double Wave, Single Wave Fort, Single Wave Standard, Inconnu)
    
    Workflow Correct: Prix → Mouvement → Pattern
    
    Args:
        df_prices: DataFrame avec prix
        df_events: DataFrame avec événements
        min_pips: Seuil minimum
        timezone: Timezone pour conversions
    
    Returns:
        {
            'pattern_type': str,
            'detection_confidence': float,
            'metrics': Dict,
            'movement': Dict or None
        }
    """
    if df_prices.empty or df_events.empty:
        result = {
            'pattern_type': 'INCONNU',
            'detection_confidence': 0.0,
            'metrics': {},
            'movement': None,
            'reason': 'Données insuffisantes'
        }
        if use_finnhub_patterns and cluster_anchor_time:
            result = enrich_pattern_with_finnhub(result, movement_time=cluster_anchor_time)
        return result
    
    # 1. Scanner mouvements avec seuil normal
    movements = scan_price_movements(df_prices, min_pips)
    
    # 2. Si cluster_anchor_time fourni, faire un scan supplémentaire avec seuil réduit
    # autour de l'heure du cluster pour capturer les mouvements progressifs ou plus faibles
    if cluster_anchor_time is not None:
        # Normaliser cluster_anchor_time
        if isinstance(cluster_anchor_time, datetime):
            cluster_anchor_ts = pd.Timestamp(cluster_anchor_time)
        elif isinstance(cluster_anchor_time, pd.Timestamp):
            cluster_anchor_ts = cluster_anchor_time
        else:
            cluster_anchor_ts = pd.Timestamp(cluster_anchor_time)
        
        if cluster_anchor_ts.tz is None:
            cluster_anchor_ts = cluster_anchor_ts.tz_localize('Europe/Zurich')
        else:
            cluster_anchor_ts = cluster_anchor_ts.tz_convert('Europe/Zurich')
        
        # Filtrer les prix autour de l'heure du cluster (±90 minutes)
        cluster_window_start = cluster_anchor_ts - pd.Timedelta(minutes=90)
        cluster_window_end = cluster_anchor_ts + pd.Timedelta(minutes=120)
        
        # Filtrer df_prices pour la fenêtre du cluster
        df_prices_cluster = df_prices[
            (df_prices.index >= cluster_window_start) & 
            (df_prices.index <= cluster_window_end)
        ]
        
        if not df_prices_cluster.empty:
            # Scanner avec seuil réduit (50% du seuil normal) pour capturer mouvements progressifs
            reduced_threshold = max(min_pips * 0.5, 10.0)  # Au moins 10 pips
            movements_cluster = scan_price_movements(df_prices_cluster, reduced_threshold)
            
            # Ajouter les mouvements trouvés dans la fenêtre du cluster (s'ils ne sont pas déjà dans movements)
            for mov in movements_cluster:
                # Vérifier si ce mouvement n'est pas déjà dans movements
                is_duplicate = False
                for existing_mov in movements:
                    if abs((pd.Timestamp(mov['start_time']) - pd.Timestamp(existing_mov['start_time'])).total_seconds()) < 60:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    movements.append(mov)
    
    if not movements:
        result = {
            'pattern_type': 'INCONNU',
            'detection_confidence': 0.0,
            'metrics': {'impact_pips': 0.0},
            'movement': None,
            'reason': f'Aucun mouvement >= {min_pips} pips détecté'
        }
        if use_finnhub_patterns and cluster_anchor_time:
            result = enrich_pattern_with_finnhub(result, movement_time=cluster_anchor_time)
        return result
    
    # 3. Si cluster_anchor_time fourni, prioriser les mouvements proches de cette heure
    # (cluster_anchor_ts est déjà défini dans la section 2 ci-dessus)
    if cluster_anchor_time is not None:
        # Filtrer mouvements proches de l'heure du cluster (±60 minutes avant, +120 minutes après)
        # Fenêtre élargie pour capturer les mouvements qui commencent légèrement avant ou après
        cluster_window_start = cluster_anchor_ts - pd.Timedelta(minutes=60)
        cluster_window_end = cluster_anchor_ts + pd.Timedelta(minutes=120)
        
        movements_near_cluster = [
            m for m in movements
            if cluster_window_start <= m['start_time'] <= cluster_window_end
        ]
        
        if movements_near_cluster:
            # Utiliser le mouvement le plus fort proche du cluster
            main_movement = max(movements_near_cluster, key=lambda x: x['impact_pips'])
        else:
            # Aucun mouvement trouvé dans la fenêtre du cluster
            # Utiliser le mouvement le plus proche de l'heure du cluster (même s'il est un peu éloigné)
            if movements:
                # Trouver le mouvement le plus proche de l'heure du cluster
                movements_with_distance = [
                    (m, abs((pd.Timestamp(m['start_time']).tz_localize('Europe/Zurich') if pd.Timestamp(m['start_time']).tz is None else pd.Timestamp(m['start_time']).tz_convert('Europe/Zurich') - cluster_anchor_ts).total_seconds() / 60))
                    for m in movements
                ]
                movements_with_distance.sort(key=lambda x: x[1])  # Trier par distance
                main_movement = movements_with_distance[0][0] if movements_with_distance else None
                
                if main_movement:
                    movement_start_ts = pd.Timestamp(main_movement['start_time'])
                    if movement_start_ts.tz is None:
                        movement_start_ts = movement_start_ts.tz_localize('Europe/Zurich')
                    else:
                        movement_start_ts = movement_start_ts.tz_convert('Europe/Zurich')
                    
                    time_diff_minutes = abs((movement_start_ts - cluster_anchor_ts).total_seconds() / 60)
                    # Stocker l'avertissement dans le résultat pour affichage ultérieur
                    if time_diff_minutes > 30:
                        # Le mouvement est éloigné de l'heure du cluster
                        # On continue quand même mais on ajoute un avertissement
                        pass  # L'avertissement sera géré dans l'affichage
            else:
                main_movement = None
    else:
        # Prendre le mouvement le plus fort
        main_movement = max(movements, key=lambda x: x['impact_pips']) if movements else None
    
    # Vérifier que main_movement est défini
    if main_movement is None:
        result = {
            'pattern_type': 'INCONNU',
            'detection_confidence': 0.0,
            'metrics': {'impact_pips': 0.0},
            'movement': None,
            'reason': f'Aucun mouvement >= {min_pips} pips détecté dans les données de prix'
        }
        if use_finnhub_patterns and cluster_anchor_time:
            result = enrich_pattern_with_finnhub(result, movement_time=cluster_anchor_time)
        return result
    
    # 3. Vérifier si Double Wave (chercher pullback + deuxième pic)
    first_event_time = df_events['ts_bern'].min()
    movement_start = main_movement['start_time']
    movement_peak = main_movement['peak_time']
    
    # S'assurer que movement_peak est compatible avec l'index de df_prices
    # (convertir en même timezone si nécessaire)
    if hasattr(movement_peak, 'tz') and movement_peak.tz is not None:
        # Si movement_peak a un timezone, s'assurer qu'il correspond à df_prices
        if df_prices.index.tz is not None:
            movement_peak = movement_peak.tz_convert(df_prices.index.tz)
    
    # Fenêtre après le premier pic pour chercher pullback
    window_after_peak = df_prices[df_prices.index >= movement_peak]
    
    if len(window_after_peak) > 20:  # Au moins 20 minutes après
        # Chercher pullback (contraire du mouvement principal)
        if main_movement['direction'] == 'UP':
            # Chercher creux après pic - fenêtre élargie à 60 minutes
            pullback_window = window_after_peak.head(60)  # 60 minutes après pic
            if not pullback_window.empty:
                pullback_low = pullback_window['low'].min()
                pullback_time = pullback_window['low'].idxmin()
                
                # Calculer le pullback depuis le pic (pas depuis baseline)
                peak_price = main_movement['baseline_price'] + main_movement['impact_pips']/10000
                pullback_pips = (peak_price - pullback_low) * 10000
                pullback_ratio = pullback_pips / main_movement['impact_pips'] if main_movement['impact_pips'] > 0 else 0
                
                # Si pullback significatif (>20% du mouvement initial, seuil réduit)
                if pullback_ratio > 0.2:  # Seuil réduit de 0.3 à 0.2
                    # Chercher deuxième pic après pullback - fenêtre élargie à 60 minutes
                    window_after_pullback = df_prices[df_prices.index > pullback_time]
                    if len(window_after_pullback) > 10:
                        # Chercher le pic dans les 60 minutes après le pullback
                        search_window = window_after_pullback.head(60)
                        if not search_window.empty:
                            second_peak_high = search_window['high'].max()
                            second_peak_time = search_window['high'].idxmax()
                            second_wave_pips = (second_peak_high - pullback_low) * 10000
                            
                            # Seuil réduit : au moins 30% du seuil (au lieu de 50%)
                            if second_wave_pips >= min_pips * 0.3:  # Au moins 30% du seuil
                                # Calculer impact NET depuis baseline jusqu'au pic final (pas la somme)
                                baseline_price = main_movement['baseline_price']
                                impact_net = (second_peak_high - baseline_price) * 10000
                                
                                # ⚠️ NOTE IMPORTANTE SUR LA DÉFINITION D'IMPACT ICI
                                # -------------------------------------------------
                                # - metrics_dw['impact_pips'] = impact détecté par le scanner de pattern
                                #   → Baseline = low/high du segment détecté (cluster), pas event_open
                                #   → C'est une mesure LOCALE du pattern (DOUBLE_WAVE)
                                #
                                # - Ce n'est PAS la métrique canonique d'impact macro du projet.
                                #   La définition canonique est celle d'IMPACT_SPEC_V1, exposée via:
                                #       measure_impact_from_finnhub(..., use_unified=True)
                                #   et affichée ici sous "Impact unifié (beta)".
                                metrics_dw = {
                                    'impact_pips': impact_net,  # Impact NET (baseline → pic final)
                                    'wave1_pips': main_movement['impact_pips'],
                                    'wave2_pips': second_wave_pips,
                                    'pullback_ratio': pullback_ratio,
                                    'pullback_pips': pullback_pips,
                                    'direction': main_movement['direction']
                                }
                                
                                # 🆕 Calcul impact unifié selon IMPACT_SPEC_V1
                                if cluster_anchor_time is not None:
                                    try:
                                        # Préparer df_prices pour calculate_impact_unified
                                        df_prices_for_unified = df_prices.copy()
                                        if df_prices_for_unified.index.name == 'datetime' or isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                                            df_prices_for_unified = df_prices_for_unified.reset_index()
                                        elif 'datetime' not in df_prices_for_unified.columns:
                                            if isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                                                df_prices_for_unified['datetime'] = df_prices_for_unified.index
                                        
                                        # Convertir timezone en string si nécessaire
                                        timezone_str_value = "Europe/Zurich"
                                        if timezone is not None:
                                            # Si c'est déjà une string
                                            if isinstance(timezone, str):
                                                timezone_str_value = timezone
                                            else:
                                                # Objet tzinfo (pytz, zoneinfo, etc.)
                                                timezone_str_value = str(timezone)
                                        
                                        # Convertir cluster_anchor_time en datetime si nécessaire
                                        event_timestamp_for_unified = cluster_anchor_time
                                        if isinstance(event_timestamp_for_unified, pd.Timestamp):
                                            event_timestamp_for_unified = event_timestamp_for_unified.to_pydatetime()
                                        
                                        unified_result = calculate_impact_unified(
                                            df_prices=df_prices_for_unified,
                                            event_timestamp=event_timestamp_for_unified,
                                            baseline_method="event_open",
                                            horizon_minutes=120,
                                            lookback_minutes=5,
                                            min_pips=None,
                                            timezone_str=timezone_str_value,
                                            debug=False,
                                        )
                                        
                                        if unified_result is not None:
                                            metrics_dw["impact_unified_pips"] = unified_result.impact_pips
                                            metrics_dw["impact_unified_signed_pips"] = unified_result.impact_signed_pips
                                            metrics_dw["impact_unified_direction"] = unified_result.direction
                                            metrics_dw["impact_unified_time_to_peak_minutes"] = unified_result.time_to_peak_minutes
                                        else:
                                            metrics_dw["impact_unified_pips"] = None
                                    except Exception:
                                        metrics_dw["impact_unified_pips"] = None
                                        pass
                                
                                return {
                                    'pattern_type': 'DOUBLE_WAVE',
                                    'detection_confidence': 0.85,
                                    'metrics': metrics_dw,
                                    'movement': main_movement,
                                    'wave1_peak': movement_peak,
                                    'pullback_low': pullback_time,
                                    'wave2_peak': second_peak_time
                                }
        
        # Même logique pour DOWN
        elif main_movement['direction'] == 'DOWN':
            pullback_window = window_after_peak.head(60)  # 60 minutes après pic
            if not pullback_window.empty:
                pullback_high = pullback_window['high'].max()
                pullback_time = pullback_window['high'].idxmax()
                
                # Calculer le pullback depuis le creux (pas depuis baseline)
                trough_price = main_movement['baseline_price'] - main_movement['impact_pips']/10000
                pullback_pips = (pullback_high - trough_price) * 10000
                pullback_ratio = pullback_pips / main_movement['impact_pips'] if main_movement['impact_pips'] > 0 else 0
                
                if pullback_ratio > 0.2:  # Seuil réduit de 0.3 à 0.2
                    window_after_pullback = df_prices[df_prices.index > pullback_time]
                    if len(window_after_pullback) > 10:
                        # Chercher le creux dans les 60 minutes après le pullback
                        search_window = window_after_pullback.head(60)
                        if not search_window.empty:
                            second_peak_low = search_window['low'].min()
                            second_peak_time = search_window['low'].idxmax()
                            second_wave_pips = (pullback_high - second_peak_low) * 10000
                            
                            if second_wave_pips >= min_pips * 0.3:  # Au moins 30% du seuil
                                # Calculer impact NET depuis baseline jusqu'au creux final (pas la somme)
                                baseline_price = main_movement['baseline_price']
                                impact_net = (baseline_price - second_peak_low) * 10000
                                
                                # ⚠️ NOTE IMPORTANTE SUR LA DÉFINITION D'IMPACT ICI
                                # -------------------------------------------------
                                # - metrics_dw_down['impact_pips'] = impact détecté par le scanner de pattern
                                #   → Baseline = low/high du segment détecté (cluster), pas event_open
                                #   → C'est une mesure LOCALE du pattern (DOUBLE_WAVE DOWN)
                                #
                                # - Ce n'est PAS la métrique canonique d'impact macro du projet.
                                #   La définition canonique est celle d'IMPACT_SPEC_V1, exposée via:
                                #       measure_impact_from_finnhub(..., use_unified=True)
                                #   et affichée ici sous "Impact unifié (beta)".
                                metrics_dw_down = {
                                    'impact_pips': impact_net,  # Impact NET (baseline → creux final)
                                    'wave1_pips': main_movement['impact_pips'],
                                    'wave2_pips': second_wave_pips,
                                    'pullback_ratio': pullback_ratio,
                                    'pullback_pips': pullback_pips,
                                    'direction': main_movement['direction']
                                }
                                
                                # 🆕 Calcul impact unifié selon IMPACT_SPEC_V1
                                if cluster_anchor_time is not None:
                                    try:
                                        # Préparer df_prices pour calculate_impact_unified
                                        df_prices_for_unified = df_prices.copy()
                                        if df_prices_for_unified.index.name == 'datetime' or isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                                            df_prices_for_unified = df_prices_for_unified.reset_index()
                                        elif 'datetime' not in df_prices_for_unified.columns:
                                            if isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                                                df_prices_for_unified['datetime'] = df_prices_for_unified.index
                                        
                                        # Convertir timezone en string si nécessaire
                                        timezone_str_value = "Europe/Zurich"
                                        if timezone is not None:
                                            # Si c'est déjà une string
                                            if isinstance(timezone, str):
                                                timezone_str_value = timezone
                                            else:
                                                # Objet tzinfo (pytz, zoneinfo, etc.)
                                                timezone_str_value = str(timezone)
                                        
                                        # Convertir cluster_anchor_time en datetime si nécessaire
                                        event_timestamp_for_unified = cluster_anchor_time
                                        if isinstance(event_timestamp_for_unified, pd.Timestamp):
                                            event_timestamp_for_unified = event_timestamp_for_unified.to_pydatetime()
                                        
                                        unified_result = calculate_impact_unified(
                                            df_prices=df_prices_for_unified,
                                            event_timestamp=event_timestamp_for_unified,
                                            baseline_method="event_open",
                                            horizon_minutes=120,
                                            lookback_minutes=5,
                                            min_pips=None,
                                            timezone_str=timezone_str_value,
                                            debug=False,
                                        )
                                        
                                        if unified_result is not None:
                                            metrics_dw_down["impact_unified_pips"] = unified_result.impact_pips
                                            metrics_dw_down["impact_unified_signed_pips"] = unified_result.impact_signed_pips
                                            metrics_dw_down["impact_unified_direction"] = unified_result.direction
                                            metrics_dw_down["impact_unified_time_to_peak_minutes"] = unified_result.time_to_peak_minutes
                                        else:
                                            metrics_dw_down["impact_unified_pips"] = None
                                    except Exception:
                                        metrics_dw_down["impact_unified_pips"] = None
                                        pass
                                
                                result = {
                                    'pattern_type': 'DOUBLE_WAVE',
                                    'detection_confidence': 0.85,
                                    'metrics': metrics_dw_down,
                                    'movement': main_movement,
                                    'wave1_peak': movement_peak,
                                    'pullback_low': pullback_time,
                                    'wave2_peak': second_peak_time
                                }
                                
                                # Enrichir avec patterns Finnhub si activé
                                if use_finnhub_patterns:
                                    result = enrich_pattern_with_finnhub(
                                        result,
                                        movement_time=movement_start,
                                        date=movement_start.date() if isinstance(movement_start, datetime) else None
                                    )
                                
                                return result
    
    # 4. Classification Single Wave
    impact = main_movement['impact_pips']
    
    if impact > 40:
        pattern_type = 'SINGLE_WAVE_FORT'
        confidence = 0.8
    elif impact >= 20:
        pattern_type = 'SINGLE_WAVE_STANDARD'
        confidence = 0.9
    else:
        pattern_type = 'INCONNU'
        confidence = 0.5
    
    # ⚠️ NOTE IMPORTANTE SUR LA DÉFINITION D'IMPACT ICI
    # -------------------------------------------------
    # - metrics['impact_pips'] = impact détecté par le scanner de pattern
    #   → Baseline = low/high du segment détecté (cluster), pas event_open
    #   → C'est une mesure LOCALE du pattern (SINGLE_WAVE / DOUBLE_WAVE)
    #
    # - Ce n'est PAS la métrique canonique d'impact macro du projet.
    #   La définition canonique est celle d'IMPACT_SPEC_V1, exposée via:
    #       measure_impact_from_finnhub(..., use_unified=True)
    #   et affichée ici sous "Impact unifié (beta)".
    metrics = {
        'impact_pips': impact,
        'direction': main_movement['direction']
    }
    
    # 🆕 Calcul impact unifié selon IMPACT_SPEC_V1
    if cluster_anchor_time is not None:
        try:
            # Préparer df_prices pour calculate_impact_unified
            # Si datetime est en index, le remettre en colonne
            df_prices_for_unified = df_prices.copy()
            if df_prices_for_unified.index.name == 'datetime' or isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                df_prices_for_unified = df_prices_for_unified.reset_index()
            elif 'datetime' not in df_prices_for_unified.columns:
                # Si datetime n'est ni en index ni en colonne, essayer de le créer depuis l'index
                if isinstance(df_prices_for_unified.index, pd.DatetimeIndex):
                    df_prices_for_unified['datetime'] = df_prices_for_unified.index
            
            # Convertir timezone en string si nécessaire
            timezone_str_value = "Europe/Zurich"
            if timezone is not None:
                # Si c'est déjà une string
                if isinstance(timezone, str):
                    timezone_str_value = timezone
                else:
                    # Objet tzinfo (pytz, zoneinfo, etc.)
                    timezone_str_value = str(timezone)
            
            # Convertir cluster_anchor_time en datetime si nécessaire
            event_timestamp_for_unified = cluster_anchor_time
            if isinstance(event_timestamp_for_unified, pd.Timestamp):
                event_timestamp_for_unified = event_timestamp_for_unified.to_pydatetime()
            
            unified_result = calculate_impact_unified(
                df_prices=df_prices_for_unified,
                event_timestamp=event_timestamp_for_unified,
                baseline_method="event_open",
                horizon_minutes=120,
                lookback_minutes=5,
                min_pips=None,  # Pas de filtre → on veut la vraie mesure brute
                timezone_str=timezone_str_value,
                debug=False,
            )
            
            if unified_result is not None:
                metrics["impact_unified_pips"] = unified_result.impact_pips
                metrics["impact_unified_signed_pips"] = unified_result.impact_signed_pips
                metrics["impact_unified_direction"] = unified_result.direction
                metrics["impact_unified_time_to_peak_minutes"] = unified_result.time_to_peak_minutes
            else:
                metrics["impact_unified_pips"] = None
        except Exception as e:
            # En cas d'erreur, on continue sans impact_unified
            metrics["impact_unified_pips"] = None
            # Option : log en debug Streamlit si nécessaire
            # st.caption(f"DEBUG impact_unified KO: {e}")
            pass
    
    result = {
        'pattern_type': pattern_type,
        'detection_confidence': confidence,
        'metrics': metrics,
        'movement': main_movement,
        'reason': f'Pattern {pattern_type} détecté (impact: {impact:.1f} pips)'
    }
    
    # Enrichir avec patterns Finnhub si activé
    if use_finnhub_patterns:
        movement_start = main_movement.get('start_time')
        if movement_start:
            result = enrich_pattern_with_finnhub(
                result,
                movement_time=movement_start,
                date=movement_start.date() if isinstance(movement_start, datetime) else None
            )
    
    return result


# ═══════════════════════════════════════════════════════════════
# SECTION 5: PRÉDICTIONS (BASE)
# ═══════════════════════════════════════════════════════════════

def predict_double_wave_base(
    df_events: pd.DataFrame,
    baseline_price: Optional[float] = None,
    direction: str = 'UP',
    use_support_resistance: bool = True,
    use_aggregate_indicators: bool = True
) -> Dict:
    """
    Prédiction Double Wave avec formules validées (⭐ Formule Linéaire + ratios Double Wave)
    
    Utilise les formules validées SESSION_VALIDATION_ACTUELLE :
    - ⭐ Formule Linéaire (calculate_impact_linear) - validée pour MOYEN/FORT/TRÈS_FORT
    - Ratios Double Wave validés (Phase 1: 58%, Pullback: 84%, Phase 2: 90%)
    - Impact net = Phase 1 - Pullback + Phase 2
    
    Args:
        df_events: DataFrame avec événements enrichis (score_adjusted, surprise, etc.)
    
    Returns:
        {
            'prediction_pips': float,
            'status': 'predicted',
            'reason': str,
            'amplification': float,
            'total_score': float,
            'base_impact': float,
            'phase1_pips': float,
            'phase2_pips': float,
            'pullback_pips': float
        }
    """
    from core.formulas_validated import (
        calculate_impact_d,
        calculate_impact_linear,  # ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
        calculate_amplification_extended,
        get_event_direction  # ⭐ Pour prédire la direction depuis les événements
    )
    from core.amplification_prediction import predict_impact_with_amplification
    
    # Calculer métriques agrégées
    score_adjusted_mean = df_events['score_adjusted'].mean()
    num_events = len(df_events)
    total_score = df_events['score_adjusted'].sum()
    mean_empirical_score = df_events['empirical_score'].mean()
    
    # ⭐ NOUVEAU : Calculer direction depuis les événements si non fournie
    if direction == 'UP' and 'family' in df_events.columns:
        # Calculer direction pour chaque événement
        directions = []
        for _, row in df_events.iterrows():
            family = row.get('family', 'Unknown')
            # Calculer surprise signée (actual - estimate)
            actual = row.get('actual')
            estimate = row.get('estimate')
            
            if pd.notna(actual) and pd.notna(estimate):
                surprise = actual - estimate
            else:
                # Fallback : utiliser surprise_pct si disponible
                surprise_pct = row.get('surprise_pct', 0.0)
                if pd.notna(surprise_pct):
                    surprise = abs(surprise_pct) if surprise_pct > 0 else -abs(surprise_pct)
                else:
                    surprise = 0.0
            
            event_direction = get_event_direction(family=family, surprise=surprise)
            directions.append(event_direction)
        
        # Direction dominante (somme vectorielle)
        direction_sum = sum(directions)
        if direction_sum > 0:
            direction = 'UP'
        elif direction_sum < 0:
            direction = 'DOWN'
        # Sinon garder 'UP' par défaut
    
    # Calculer surprises pour formule linéaire
    surprises = []
    for _, row in df_events.iterrows():
        surprise_pct = row.get('surprise_pct', 0.0)
        if pd.notna(surprise_pct):
            surprises.append(abs(surprise_pct))
    
    surprise_max = max(surprises) if surprises else 0.0
    surprise_avg = np.mean(surprises) if surprises else 0.0
    
    # ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
    # Utilise calculate_impact_linear() au lieu de calculate_impact_d()
    # Cette formule a été validée sur 50 dates significatives avec :
    # - MAE global : 13.98 pips (vs 38.63 formule D) → -64% d'erreur
    # - Ratio médian FORT : 1.297 (excellent)
    base_impact_no_amp = calculate_impact_linear(
        base_empirical_score=mean_empirical_score,
        adjusted_empirical_score=score_adjusted_mean,
        surprise_avg=surprise_avg,
        surprise_max=surprise_max,
        n_events=num_events
    )
    
    # Prédire amplification avec modèle de régression multiple (plus précis avec actuals)
    # On a les actuals (sinon surprise_pct serait 0), donc on peut utiliser le modèle 'APRÈS'
    amplification_result = predict_impact_with_amplification(
        impact_base=base_impact_no_amp,
        total_score=total_score,
        mean_adjusted_score=score_adjusted_mean,
        num_events=num_events,
        mean_empirical_score=mean_empirical_score,
        use_ensemble=False  # On combine avec Ensemble Methods plus tard si nécessaire
    )
    
    # Utiliser l'amplification prédite pour ajuster l'impact
    amplification = amplification_result['amplification']
    impact_adjusted = amplification_result['impact_adjusted']
    
    # Utiliser l'impact ajusté comme nouvelle base pour les ratios Double Wave
    base_impact = impact_adjusted
    amplification_base = amplification  # Pour affichage
    
    # Ratios Double Wave validés (Session 64)
    PHASE1_RATIO = 0.58      # Phase 1 = 58% impact total
    PULLBACK_RATIO = 0.84    # Pullback retrace 84% Phase 1
    PHASE2_RATIO = 0.90      # Phase 2 = 90% impact total
    
    # Calculs des phases
    phase1_pips = base_impact * PHASE1_RATIO
    pullback_pips = phase1_pips * PULLBACK_RATIO
    phase2_pips = base_impact * PHASE2_RATIO
    
    # Impact net total (Phase 1 - Pullback + Phase 2)
    total_net_pips = phase1_pips - pullback_pips + phase2_pips
    
    # Ajuster avec Support/Résistance si activé et baseline_price disponible
    # Support/Résistance désactivé (modules supprimés)
    sr_adjustment = None
    # if use_support_resistance and baseline_price is not None:
    #     try:
    #         levels = load_support_resistance(resolution='H1')
    #         if not levels.empty:
    #             sr_adjustment = adjust_prediction_with_support_resistance(
    #                 predicted_impact_pips=total_net_pips,
    #                 baseline_price=baseline_price,
    #                 direction=direction,
    #                 levels=levels
    #             )
    #             # Appliquer l'ajustement
    #             if sr_adjustment['adjustment_factor'] < 1.0:
    #                 total_net_pips = sr_adjustment['adjusted_impact_pips']
    #                 # Ajuster aussi les phases proportionnellement
    #                 adjustment_factor = sr_adjustment['adjustment_factor']
    #                 phase1_pips *= adjustment_factor
    #                 phase2_pips *= adjustment_factor
    #                 pullback_pips *= adjustment_factor
    #     except Exception as e:
    #         # En cas d'erreur, continuer sans ajustement
    #         pass
    
    # Ajuster avec Aggregate Indicators si activé
    # Aggregate indicators désactivé (modules supprimés)
    ai_adjustment = None
    # if use_aggregate_indicators:
    #     try:
    #         indicators = load_aggregate_indicators(
    #             db_path=DB_PATH,
    #             resolution='H1',
    #             lookback_hours=24
    #         )
    #         if indicators:
    #             ai_adjustment = adjust_prediction_with_indicators(
    #                 predicted_impact_pips=total_net_pips,
    #                 direction=direction,
    #                 indicators=indicators
    #             )
    #             # Appliquer l'ajustement
    #             if ai_adjustment['adjustment_factor'] < 1.0:
    #                 total_net_pips = ai_adjustment['adjusted_impact_pips']
    #                 # Ajuster aussi les phases proportionnellement
    #                 adjustment_factor = ai_adjustment['adjustment_factor']
    #                 phase1_pips *= adjustment_factor
    #                 phase2_pips *= adjustment_factor
    #                 pullback_pips *= adjustment_factor
    #     except Exception as e:
    #         # En cas d'erreur, continuer sans ajustement
    #         pass
    
    # Score total pour documentation
    total_score = df_events['score_adjusted'].sum()
    
    result = {
        'prediction_pips': round(total_net_pips, 2),
        'status': 'predicted',
        'reason': f'Double Wave validé (base: {base_impact:.1f} pips, net: {total_net_pips:.1f} pips)',
        'amplification': amplification,
        'amplification_base': amplification_base,  # Amplification de base (formule étendue)
        'amplification_predicted': amplification,  # Amplification prédite (modèle régression)
        'amplification_method': amplification_result['method'],  # 'with_actuals' ou 'without_actuals'
        'total_score': total_score,
        'base_impact': base_impact,
        'impact_base_before_amplification': amplification_result['impact_base'],
        'phase1_pips': phase1_pips,
        'phase2_pips': phase2_pips,
        'pullback_pips': pullback_pips,
        'surprise_max': surprise_max,
        'direction': direction
    }
    
    # Ajouter info Support/Résistance si ajustement appliqué
    if sr_adjustment and sr_adjustment['adjustment_factor'] < 1.0:
        result['sr_adjustment'] = sr_adjustment
        result['reason'] += f" | Ajusté SR: {sr_adjustment['adjustment_reason']}"
    
    # Ajouter info Aggregate Indicators si ajustement appliqué
    if ai_adjustment and ai_adjustment['adjustment_factor'] < 1.0:
        result['ai_adjustment'] = ai_adjustment
        result['reason'] += f" | Ajusté AI: {ai_adjustment['adjustment_reason']}"
        result['aggregate_indicators'] = indicators if indicators else None
    
    return result


def predict_single_wave_base(
    df_events: pd.DataFrame,
    df_prices: pd.DataFrame,
    pattern_type: str,
    movement_datetime: Optional[pd.Timestamp] = None,
    baseline_price: Optional[float] = None,
    direction: str = 'UP',
    use_support_resistance: bool = True,
    use_aggregate_indicators: bool = True
) -> Dict:
    """
    Prédiction Single Wave avec Ensemble Methods (si disponible) ou formules validées
    
    Args:
        df_events: DataFrame avec événements enrichis
        df_prices: DataFrame avec prix
        pattern_type: Type de pattern (SINGLE_WAVE_FORT, SINGLE_WAVE_STANDARD)
        movement_datetime: Timestamp du mouvement (pour Ensemble Methods)
    
    Returns:
        {
            'prediction_pips': float,
            'amplification': float,
            'r2_trend': float,
            'status': 'predicted',
            'method': str (ensemble | formulas_validated | universal_fallback)
        }
    """
    # Calculer R² tendance (60 min avant premier event)
    first_event_time = df_events['ts_bern'].min()
    window_start = first_event_time - pd.Timedelta(minutes=60)
    window_end = first_event_time - pd.Timedelta(minutes=1)
    
    df_window = df_prices[(df_prices.index >= window_start) & (df_prices.index <= window_end)]
    
    if len(df_window) < 10:
        return {
            'prediction_pips': None,
            'amplification': None,
            'r2_trend': None,
            'status': 'excluded',
            'reason': 'Fenêtre pré-événement insuffisante',
            'method': None
        }
    
    # Régression linéaire pour R²
    from sklearn.linear_model import LinearRegression
    
    X = np.arange(len(df_window)).reshape(-1, 1)
    y = df_window['close'].values
    
    model = LinearRegression()
    model.fit(X, y)
    r2_trend = model.score(X, y)
    
    # Score total ajusté
    total_score = df_events['score_adjusted'].sum()
    
    # Essayer d'abord Ensemble Methods (si movement_datetime fourni)
    if movement_datetime is not None:
        try:
            ensemble_result = predict_pattern_based_ensemble(
                pattern_type=pattern_type,
                total_score=total_score,
                num_events=len(df_events),
                movement_datetime=movement_datetime
            )
            
            if ensemble_result.get('prediction', 0) > 0:
                return {
                    'prediction_pips': ensemble_result['prediction'],
                    'amplification': None,  # Ensemble Methods n'utilise pas d'amplification directe
                    'r2_trend': r2_trend,
                    'status': 'predicted',
                    'method': 'ensemble',
                    'total_score': total_score,
                    'reason': ensemble_result.get('reason', 'Ensemble Methods'),
                    'ensemble_details': ensemble_result.get('individual', {}),
                    'weights': ensemble_result.get('weights', {})
                }
        except Exception as e:
            # Si Ensemble Methods échoue, continuer avec formules validées
            pass
    
    # Fallback : Formules validées (Impact D) avec amplification prédite
    try:
        from core.amplification_prediction import predict_impact_with_amplification
        from core.formulas_validated import get_event_direction
        
        # ⭐ NOUVEAU : Calculer direction depuis les événements si non fournie
        if direction == 'UP' and 'family' in df_events.columns:
            # Calculer direction pour chaque événement
            directions = []
            for _, row in df_events.iterrows():
                family = row.get('family', 'Unknown')
                # Calculer surprise signée (actual - estimate)
                actual = row.get('actual')
                estimate = row.get('estimate')
                
                if pd.notna(actual) and pd.notna(estimate):
                    surprise = actual - estimate
                else:
                    # Fallback : utiliser surprise_pct si disponible
                    surprise_pct = row.get('surprise_pct', 0.0)
                    if pd.notna(surprise_pct):
                        surprise = abs(surprise_pct) if surprise_pct > 0 else -abs(surprise_pct)
                    else:
                        surprise = 0.0
                
                event_direction = get_event_direction(family=family, surprise=surprise)
                directions.append(event_direction)
            
            # Direction dominante (somme vectorielle)
            direction_sum = sum(directions)
            if direction_sum > 0:
                direction = 'UP'
            elif direction_sum < 0:
                direction = 'DOWN'
            # Sinon garder 'UP' par défaut
        
        # Calculer surprises pour formule linéaire
        surprises = []
        for _, row in df_events.iterrows():
            if pd.notna(row.get('actual')) and pd.notna(row.get('estimate')):
                if row['estimate'] != 0:
                    surprise_pct = abs((row['actual'] - row['estimate']) / abs(row['estimate'])) * 100
                    surprises.append(surprise_pct)
        
        surprise_max = max(surprises) if surprises else 0.0
        surprise_avg = np.mean(surprises) if surprises else 0.0
        
        # Score empirique moyen ajusté
        avg_empirical_score = df_events['empirical_score'].mean()
        mean_adjusted_score = df_events['score_adjusted'].mean()
        
        # ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
        # Utilise calculate_impact_linear() au lieu de calculate_impact_d()
        # Cette formule a été validée sur 50 dates significatives avec :
        # - MAE global : 13.98 pips (vs 38.63 formule D) → -64% d'erreur
        # - Ratio médian FORT : 1.297 (excellent)
        impact_base_no_amp = calculate_impact_linear(
            base_empirical_score=avg_empirical_score,
            adjusted_empirical_score=mean_adjusted_score,
            surprise_avg=surprise_avg,
            surprise_max=surprise_max,
            n_events=len(df_events)
        )
        
        # Prédire amplification avec modèle de régression multiple
        amplification_result = predict_impact_with_amplification(
            impact_base=impact_base_no_amp,
            total_score=total_score,
            mean_adjusted_score=mean_adjusted_score,
            num_events=len(df_events),
            mean_empirical_score=avg_empirical_score,
            r2_trend=r2_trend,  # Disponible pour modèle 'AVANT' si nécessaire
            use_ensemble=False
        )
        
        impact_pips = amplification_result['impact_final']
        amplification = amplification_result['amplification']
        amplification_base = amplification  # Pour affichage
        
        # Ajuster avec Support/Résistance si activé et baseline_price disponible
        # Support/Résistance désactivé (modules supprimés)
        sr_adjustment = None
        # if use_support_resistance and baseline_price is not None:
        #     try:
        #         levels = load_support_resistance(resolution='H1')
        #         if not levels.empty:
        #             sr_adjustment = adjust_prediction_with_support_resistance(
        #                 predicted_impact_pips=impact_pips,
        #                 baseline_price=baseline_price,
        #                 direction=direction,
        #                 levels=levels
        #             )
        #             # Appliquer l'ajustement
        #             if sr_adjustment['adjustment_factor'] < 1.0:
        #                 impact_pips = sr_adjustment['adjusted_impact_pips']
        #     except Exception as e:
        #         # En cas d'erreur, continuer sans ajustement
        #         pass
        
        # Ajuster avec Aggregate Indicators si activé
        # Aggregate indicators désactivé (modules supprimés)
        ai_adjustment = None
        indicators = None
        # if use_aggregate_indicators:
        #     try:
        #         indicators = load_aggregate_indicators(
        #             db_path=DB_PATH,
        #             resolution='H1',
        #             lookback_hours=24
        #         )
        #         if indicators:
        #             ai_adjustment = adjust_prediction_with_indicators(
        #                 predicted_impact_pips=impact_pips,
        #                 direction=direction,
        #                 indicators=indicators
        #             )
        #             # Appliquer l'ajustement
        #             if ai_adjustment['adjustment_factor'] < 1.0:
        #                 impact_pips = ai_adjustment['adjusted_impact_pips']
        #     except Exception as e:
        #         # En cas d'erreur, continuer sans ajustement
        #         pass
        
        result = {
            'prediction_pips': impact_pips,
            'amplification': amplification,
            'amplification_base': amplification_base,
            'amplification_predicted': amplification,
            'amplification_method': amplification_result['method'],
            'r2_trend': r2_trend,
            'status': 'predicted',
            'method': 'formulas_validated',
            'total_score': total_score,
            'reason': f'Formules validées + amplification prédite (surprise: {surprise_max:.1f}%, amplification: {amplification:.2f}x)',
            'direction': direction
        }
        
        # Ajouter info Support/Résistance si ajustement appliqué
        if sr_adjustment and sr_adjustment['adjustment_factor'] < 1.0:
            result['sr_adjustment'] = sr_adjustment
            result['reason'] += f" | Ajusté SR: {sr_adjustment['adjustment_reason']}"
        
        # Ajouter info Aggregate Indicators si ajustement appliqué
        if ai_adjustment and ai_adjustment['adjustment_factor'] < 1.0:
            result['ai_adjustment'] = ai_adjustment
            result['reason'] += f" | Ajusté AI: {ai_adjustment['adjustment_reason']}"
            result['aggregate_indicators'] = indicators if indicators else None
        
        return result
    except Exception as e:
        # Fallback final : fonction universelle
        a, b, c = 0.040833, 0.050220, -0.006553
        r2_clipped = max(0.0, min(1.0, r2_trend))
        amplification = max(0.01, min(0.20, a + b * r2_clipped + c * r2_clipped**2))
        prediction_pips = total_score * amplification
        
        return {
            'prediction_pips': prediction_pips,
            'amplification': amplification,
            'r2_trend': r2_trend,
            'status': 'predicted',
            'method': 'universal_fallback',
            'total_score': total_score,
            'reason': f'Prédiction Single Wave (R²: {r2_trend:.3f}, amplification: {amplification:.4f})'
        }


# ═══════════════════════════════════════════════════════════════
# SECTION 6: AUTO-REFRESH
# ═══════════════════════════════════════════════════════════════

def auto_refresh_on_launch(state_key: str = "auto_refresh_planif_clean"):
    """Déclenche auto-refresh au lancement si nécessaire"""
    if st.session_state.get(state_key):
        return
    
    progress_text = st.empty()
    progress_bar = st.progress(0.0)

    def progress_cb(value: float, message: str):
        progress_bar.progress(min(max(value, 0.0), 1.0))
        progress_text.text(message)

    # Auto-refresh désactivé (module supprimé)
    # refresh = ensure_data_freshness(progress_callback=progress_cb)
    class DummyRefresh:
        price_update_triggered = False
        pipeline_triggered = False
        logs = []
        price_age_hours = None
        cache_age_hours = None
        last_price_time = None
        needs_update = False
    refresh = DummyRefresh()
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
    
    st.session_state[state_key] = True


# ═══════════════════════════════════════════════════════════════
# SECTION 4: INTERFACE STREAMLIT (BASE)
# ═══════════════════════════════════════════════════════════════

def main():
    """Fonction principale Streamlit"""
    
    # Auto-refresh au lancement
    auto_refresh_on_launch()
    
    st.sidebar.header("⚙️ Configuration")
    
    # Mode de sélection
    selection_mode = st.sidebar.radio(
        "Mode de sélection",
        ["Saisie manuelle", "Depuis calendrier"],
        key="selection_mode_clean"
    )
    
    # Filtre global sur le nombre d'événements par cluster
    min_cluster_events = st.sidebar.slider(
        "🔗 Événements minimum par cluster",
        min_value=1,
        max_value=20,
        value=7,
        step=1,
        help="Les prédictions sont plus fiables lorsque le cluster contient plusieurs événements "
             "simultanés. Ce filtre s'applique à la détection manuelle et au calendrier."
    )
    
    if selection_mode == "Saisie manuelle":
        # Mode de saisie (date unique ou période)
        date_mode = st.sidebar.radio(
            "Type de sélection",
            ["Date unique", "Période"],
            key="date_mode_clean"
        )
        
        if date_mode == "Date unique":
            date_input = st.sidebar.text_input(
                "📅 Date (YYYY-MM-DD)",
                value=datetime.now().strftime('%Y-%m-%d'),
                key="date_input_clean"
            )
            date_start = None
            date_end = None
        else:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                date_start_str = st.text_input(
                    "📅 Date début",
                    value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    key="date_start_clean"
                )
            with col2:
                date_end_str = st.text_input(
                    "📅 Date fin",
                    value=datetime.now().strftime('%Y-%m-%d'),
                    key="date_end_clean"
                )
            date_input = None
            date_start = None
            date_end = None
        
        timezone_str = st.sidebar.selectbox(
            "🌍 Timezone",
            options=["Europe/Zurich", "UTC", "America/New_York"],
            index=0,
            key="timezone_clean"
        )
        
        countries_manual = st.sidebar.multiselect(
            "🌍 Pays",
            options=sorted(list(EURUSD_RELEVANT_COUNTRIES)),
            default=["US", "EU"],
            key="countries_manual_clean"
        )
        
        if not countries_manual:
            st.sidebar.warning("Sélectionnez au moins un pays.")
            return
        
        # Ajouter automatiquement "DE" si "EU" est sélectionné (pour inclure Current Account DE)
        if "EU" in countries_manual and "DE" not in countries_manual:
            countries_manual = list(countries_manual) + ["DE"]
        
        min_pips = st.sidebar.number_input(
            "📊 Seuil minimum (pips)",
            min_value=10.0,
            max_value=100.0,
            value=35.0,
            step=5.0,
            key="min_pips_clean"
        )
        
        # Définir min_importance (1 = High, 2 = Medium, 3 = Low)
        # min_importance = 3 pour inclure tous les événements (High, Medium, Low)
        # La requête utilise maintenant importance_n >= min_importance
        min_importance = 3
        
        # Validation
        if date_mode == "Date unique":
            validation = validate_input(date_input, timezone_str, min_pips)
            if not validation['valid']:
                st.error(f"❌ Erreur validation: {validation['error_message']}")
                return
            target_date = validation['date']
            date_start = target_date
            date_end = target_date
        else:
            # Valider période
            try:
                date_start = parse_flexible_date(date_start_str)
                date_end = parse_flexible_date(date_end_str)
                if date_start > date_end:
                    st.error("❌ La date de début doit être avant la date de fin")
                    return
                if date_start < datetime(2023, 1, 1) or date_end > datetime(2025, 12, 31):
                    st.error("❌ Les dates doivent être entre 2023-01-01 et 2025-12-31")
                    return
            except ValueError as e:
                st.error(f"❌ Erreur format date: {str(e)}")
                return
        
        tz = pytz.timezone(timezone_str)
        
        # Si période, traiter chaque date
        if date_start != date_end:
            st.header("📊 Analyse sur Période")
            st.info(f"Analyse de {date_start.strftime('%Y-%m-%d')} à {date_end.strftime('%Y-%m-%d')}")
            
            # Calculer toutes les dates de la période
            current_date = date_start
            results = []
            
            progress_bar = st.progress(0.0)
            total_days = (date_end - date_start).days + 1
            
            while current_date <= date_end:
                day_num = (current_date - date_start).days + 1
                progress_bar.progress(day_num / total_days)
                
                # Charger données pour cette date
                df_events = load_events_for_date(
                    current_date,
                    DB_PATH,
                    timezone_str,
                    min_importance=3,
                    countries=countries_manual,
                    exclude_no_actual=True
                )
                
                if not df_events.empty:
                    df_prices = load_prices_for_date(current_date, DB_PATH, timezone_str)
                    if not df_prices.empty:
                        df_events_enriched = enrich_events_with_surprises(df_events)
                        pattern_result = detect_pattern_type(
                            df_prices,
                            df_events_enriched,
                            min_pips,
                            tz
                        )
                        
                        results.append({
                            'date': current_date,
                            'n_events': len(df_events),
                            'pattern': pattern_result['pattern_type'],
                            'confidence': pattern_result['detection_confidence'],
                            'impact_detected': pattern_result.get('metrics', {}).get('impact_pips', 0),
                            'has_prediction': pattern_result['pattern_type'] != 'INCONNU'
                        })
                
                current_date += timedelta(days=1)
            
            progress_bar.empty()
            
            # Afficher résultats
            if results:
                st.success(f"✅ {len(results)} date(s) analysée(s)")
                df_results = pd.DataFrame(results)
                st.dataframe(df_results)
            else:
                st.warning("⚠️ Aucune date avec événements et prix trouvée dans cette période")
            return
        
        # Sinon, traitement date unique (code existant)
        target_date = date_start
        
        # Chargement données
        st.header("📊 Chargement Données")
        
        with st.spinner("Chargement des événements..."):
            df_events = load_events_for_date(
                target_date,
                DB_PATH,
                timezone_str,
                min_importance=3,  # HIGH par défaut
                countries=countries_manual,
                exclude_no_actual=True
            )
        
        if df_events.empty:
            st.warning("⚠️ Aucun événement trouvé pour cette date")
            return
        
        st.success(f"✅ {len(df_events)} événement(s) chargé(s)")
        
        with st.spinner("Chargement des prix..."):
            df_prices = load_prices_for_date(target_date, DB_PATH, timezone_str)
        
        if df_prices.empty:
            st.warning("⚠️ Aucun prix trouvé pour cette date")
            return
        
        st.success(f"✅ {len(df_prices)} bougie(s) M1 chargée(s)")
        
        # DÉTECTION DU MOUVEMENT (Workflow Correct : Prix → Mouvement → Cluster)
        st.header("🔍 Détection Mouvement")
        
        with st.spinner("Scan des mouvements de prix..."):
            movements = scan_price_movements(df_prices, min_pips=min_pips, window_minutes=10)
        
        movement_time = None
        if movements:
            main_movement = movements[0]  # Prendre le mouvement principal
            movement_start = main_movement['start_time']
            if isinstance(movement_start, pd.Timestamp):
                if movement_start.tz is None:
                    movement_start = movement_start.tz_localize(timezone_str)
                else:
                    movement_start = movement_start.tz_convert(timezone_str)
            movement_time = movement_start.to_pydatetime()
            
            st.success(f"✅ {len(movements)} mouvement(s) détecté(s)")
            st.info(f"📍 Mouvement principal : {movement_start.strftime('%H:%M:%S')} - {main_movement['impact_pips']:.1f} pips - {main_movement.get('direction', 'N/A')}")
        else:
            st.warning("⚠️ Aucun mouvement significatif détecté")
            # Si pas de mouvement, chercher autour de l'heure la plus probable (14:30 pour US)
            if not df_events.empty:
                df_us_events = df_events[df_events['country'] == 'US']
                if not df_us_events.empty:
                    # Prendre l'heure du premier événement US
                    first_us_time = df_us_events.iloc[0]['ts_bern']
                    movement_time = first_us_time.to_pydatetime()
                    st.info(f"ℹ️ Utilisation de l'heure du premier événement US : {first_us_time.strftime('%H:%M:%S')}")
        
        # IDENTIFICATION du cluster (logique ADN : comparer avec cache au lieu de construire)
        st.header("🔍 Identification Cluster (ADN)")
        
        # Charger le cache des clusters validés historiquement
        df_cache = load_cache_clusters()
        
        if df_cache is None or df_cache.empty:
            st.warning("⚠️ Cache des clusters non disponible. Utilisation de la méthode de construction.")
            # Fallback : utiliser build_clusters_for_date
            with st.spinner("Construction du cluster..."):
                clusters = build_clusters_for_date(
                    target_date,
                    DB_PATH,
                    timezone_str=timezone_str,
                    window_minutes=30,
                    min_importance=min_importance,
                    countries=countries_manual if countries_manual else None,
                    exclude_no_actual=False
                )
                cluster_principal = None
                if clusters:
                    for cluster in clusters:
                        df_cluster_events = cluster.get('df_events', pd.DataFrame())
                        if not df_cluster_events.empty:
                            cluster['total_score'] = df_cluster_events['empirical_score'].sum()
                            cluster['n_us_events'] = len(df_cluster_events[df_cluster_events['country'] == 'US'])
                    clusters_with_us = [c for c in clusters if c.get('n_us_events', 0) > 0]
                    if clusters_with_us:
                        cluster_principal = max(clusters_with_us, key=lambda x: (x.get('n_us_events', 0), x.get('total_score', 0.0)))
                    else:
                        cluster_principal = max(clusters, key=lambda x: x.get('total_score', 0.0))
        else:
            with st.spinner("Identification du cluster par comparaison ADN avec le cache..."):
                # IDENTIFIER le cluster depuis le cache (logique ADN)
                # Utiliser movement_time si disponible pour chercher les événements dans une fenêtre autour
                cluster_principal = identify_cluster_from_date(
                    target_date,
                    DB_PATH,
                    df_cache,
                    timezone_str=timezone_str,
                    window_minutes=30,
                    min_importance=3,  # IMPORTANT : Inclure TOUS les événements (High, Medium, Low) pour l'identification
                    countries=countries_manual if countries_manual else None,
                    jaccard_threshold=0.5,  # Seuil réduit à 0.5 pour capturer plus de clusters (47-50% sont souvent valides)
                    movement_time=movement_time,  # Passer l'heure du mouvement détecté
                    window_before_minutes=10,  # Chercher 10 min avant
                    window_after_minutes=15   # Chercher 15 min après
                )
        
        if cluster_principal:
            # Afficher les stats du cluster identifié
            jaccard = cluster_principal.get('jaccard_similarity', 1.0)
            n_samples = cluster_principal.get('n_samples', 0)
            impact_median = cluster_principal.get('impact_median', None)
            dominant_pattern = cluster_principal.get('dominant_pattern', 'INCONNU')
            
            if jaccard >= 0.9:
                st.success(f"✅ Cluster identifié (ADN) : {cluster_principal['n_events']} événements, "
                          f"Similarité: {jaccard*100:.0f}%, {n_samples} occurrences historiques")
            elif jaccard >= 0.7:
                st.warning(f"⚠️ Cluster identifié (ADN partiel) : {cluster_principal['n_events']} événements, "
                          f"Similarité: {jaccard*100:.0f}%, {n_samples} occurrences historiques")
            else:
                st.info(f"ℹ️ Cluster identifié (ADN faible) : {cluster_principal['n_events']} événements, "
                       f"Similarité: {jaccard*100:.0f}%, {n_samples} occurrences historiques")
            
            # Afficher détails du cluster identifié
            with st.expander("📋 Détails du cluster identifié"):
                # Formater l'heure d'ancrage correctement
                anchor_time_display = cluster_principal['anchor_time']
                if isinstance(anchor_time_display, pd.Timestamp):
                    if anchor_time_display.tz is None:
                        anchor_time_display = anchor_time_display.tz_localize('Europe/Zurich')
                    else:
                        anchor_time_display = anchor_time_display.tz_convert('Europe/Zurich')
                    anchor_time_str = anchor_time_display.strftime('%H:%M')
                else:
                    anchor_time_str = str(anchor_time_display)
                
                st.write(f"**Heure d'ancrage :** {anchor_time_str}")
                st.write(f"**Nombre d'événements :** {cluster_principal['n_events']}")
                st.write(f"**Événements US :** {cluster_principal.get('n_us_events', 0)}")
                st.write(f"**Signature ADN :** {cluster_principal.get('cluster_signature', 'N/A')[:100]}...")
                st.write(f"**Similarité Jaccard :** {jaccard*100:.1f}%")
                st.write(f"**Occurrences historiques :** {n_samples}")
                first_occ = cluster_principal.get('first_occurrence', None)
                last_occ = cluster_principal.get('last_occurrence', None)
                if first_occ and last_occ:
                    st.write(f"**Période historique :** {first_occ} → {last_occ}")
                if impact_median is not None:
                    st.write(f"**Impact médian historique :** {impact_median:.1f} pips")
                st.write(f"**Pattern dominant historique :** {dominant_pattern}")
            
            # =============================================================================
            # Résumé historique du cluster (depuis le cache)
            # =============================================================================
            impact_median = cluster_principal.get("impact_median")
            impact_mean = cluster_principal.get("impact_mean")
            
            if impact_median is not None:
                if impact_mean is not None:
                    st.info(
                        f"📊 Impact médian historique du cluster (cache): **{impact_median:.1f} pips** | "
                        f"moyenne: **{impact_mean:.1f} pips**"
                    )
                else:
                    st.info(
                        f"📊 Impact médian historique du cluster (cache): **{impact_median:.1f} pips**"
                    )
            
            # =============================================================================
            # Extraction distribution historique des impacts du cluster (chemin ADN)
            # =============================================================================
            # Marqueur visible pour vérifier que le bloc s'exécute
            st.warning("🔍 DEBUG: entrée bloc distribution historique (chemin ADN)")
            
            df_hist = pd.DataFrame()
            
            # Extraire identifiants du cluster_principal
            cluster_signature = cluster_principal.get("cluster_signature")
            cluster_id = cluster_principal.get("cluster_id")
            adn_sig = cluster_principal.get("signature_adn") or cluster_principal.get("adn_signature") or cluster_principal.get("event_signature") or cluster_principal.get("signature") or cluster_signature
            
            # Log des identifiants utilisés pour debug
            st.write(f"🔍 DEBUG cluster_principal keys: {list(cluster_principal.keys())}")
            st.write("🔍 DEBUG cluster_id:", cluster_id)
            st.write("🔍 DEBUG adn_sig:", adn_sig)
            st.write("🔍 DEBUG cluster_signature:", cluster_signature)
            
            if cluster_id or adn_sig:
                try:
                    conn = duckdb.connect(str(DB_PATH), read_only=True)
                    
                    # 1) Tentative ancienne (clusters_occurrences), wrapped dans try/except
                    if cluster_id:
                        try:
                            df_hist = conn.execute("""
                                SELECT impact_pips
                                FROM clusters_occurrences
                                WHERE cluster_id = ?
                                ORDER BY date
                            """, [cluster_id]).df()
                        except Exception as e:
                            st.write(f"🔍 DEBUG clusters_occurrences/cluster_id KO: {e}")
                    
                    if df_hist.empty and adn_sig:
                        try:
                            df_hist = conn.execute("""
                                SELECT impact_pips
                                FROM clusters_occurrences
                                WHERE signature_adn = ? OR cluster_signature = ?
                                ORDER BY date
                            """, [adn_sig, adn_sig]).df()
                        except Exception as e:
                            st.write(f"🔍 DEBUG clusters_occurrences/signature KO: {e}")
                    
                    # 2) Nouveau : fallback sur event_impacts_v2
                    if df_hist.empty and adn_sig:
                        try:
                            df_hist = conn.execute("""
                                SELECT impact_pips
                                FROM event_impacts_v2
                                WHERE cluster_signature = ?
                                   OR signature_adn = ?
                                   OR signature_current = ?
                            """, [adn_sig, adn_sig, adn_sig]).df()
                            st.write(f"🔍 DEBUG event_impacts_v2 rows: {len(df_hist)}")
                        except Exception as e:
                            st.write(f"🔍 DEBUG event_impacts_v2 KO: {e}")
                    
                    conn.close()
                except Exception as e:
                    st.error(f"🔍 DEBUG erreur recherche cluster_id/signature: {e}")
                    df_hist = pd.DataFrame()
            
            # Chemin 3 : Si pas de cluster_id/signature, inspecter les tables disponibles
            if df_hist.empty:
                try:
                    conn = duckdb.connect(str(DB_PATH), read_only=True)
                    tables = conn.execute("SHOW TABLES").df()
                    st.write(f"🔍 DEBUG tables: {list(tables['name']) if not tables.empty else 'No tables'}")
                    
                    # Chercher tables candidates (élargi pour inclure "impact")
                    if not tables.empty:
                        candidates = [
                            t for t in tables['name']
                            if any(kw in t.lower() for kw in ['cluster', 'occurr', 'impact'])
                        ]
                        st.write(f"🔍 DEBUG candidates: {candidates}")
                        
                        # Pour chaque candidate, afficher colonnes
                        for t in candidates:
                            try:
                                cols = conn.execute(f"DESCRIBE {t}").df()
                                st.write(f"🔍 DEBUG cols {t}: {list(cols['column_name']) if not cols.empty else 'No cols'}")
                            except Exception as e:
                                st.write(f"🔍 DEBUG erreur DESCRIBE {t}: {e}")
                    
                    conn.close()
                except Exception as e:
                    st.error(f"🔍 DEBUG erreur inspection tables: {e}")
            
            # Vérifier si df_hist est toujours vide après toutes les tentatives
            if df_hist.empty:
                st.error("🔍 DEBUG: df_hist vide après requêtes cluster_id/signature.")
            
            # Calculer et afficher quantiles si distribution disponible
            # ⚠️ IMPORTANT : Vérifier que impact_pips dans la table historique utilise la même définition
            # que "Impact détecté" (peak-to-baseline, même window). Si quantiles incohérents, vérifier formule.
            with st.container():
                if not df_hist.empty and "impact_pips" in df_hist.columns:
                    dist = df_hist["impact_pips"].dropna().astype(float).values
                    if len(dist) >= 5:
                        p50 = np.percentile(dist, 50)
                        p75 = np.percentile(dist, 75)
                        p90 = np.percentile(dist, 90)
                        p95 = np.percentile(dist, 95)
                        mx = np.max(dist)
                        
                        st.subheader("📊 Distribution historique des impacts du cluster")
                        st.write({
                            "n": len(dist),
                            "p50": round(p50, 1),
                            "p75": round(p75, 1),
                            "p90": round(p90, 1),
                            "p95": round(p95, 1),
                            "max": round(mx, 1),
                        })
                        
                        # Guide d'interprétation des quantiles vs prédiction
                        # Si p50 ~ 70-90 pips → prédiction 80.3 est "normale", 150.7 est rare
                        # Si p75/p90 ~ 130-160 pips → modèle sous-prédit (features manquantes ou calibration conservative)
                        # Si max ~ 160+ mais p50 ~ 60 → 150 est dans la queue, OK modèle bas mais ajouter "mode tail risk"
                    else:
                        st.warning(f"⚠️ Distribution historique insuffisante (n={len(dist)} < 5)")
                else:
                    st.warning("⚠️ DEBUG: aucune distribution historique trouvée pour ce cluster (df_hist vide ou colonne impact_pips absente).")
            
            # Calculer le score total du cluster identifié
            df_events = cluster_principal.get('df_events', pd.DataFrame()).copy()
            if not df_events.empty:
                # Enrichir temporairement pour calculer le score
                df_events_temp = enrich_events_with_surprises(df_events)
                cluster_principal['total_score'] = df_events_temp['score_adjusted'].sum()
            else:
                cluster_principal['total_score'] = 0.0
            
            if not df_events.empty:
                de_events = df_events[df_events['country'] == 'DE']
                us_events = df_events[df_events['country'] == 'US']
                
                st.info(f"📌 {len(df_events)} événements du cluster identifié affichés")
                if len(de_events) > 0:
                    st.caption(f"✅ {len(us_events)} événements US + {len(de_events)} événement(s) DE inclus(s)")
                else:
                    st.caption(f"ℹ️ {len(us_events)} événements US (aucun événement DE trouvé)")
            else:
                st.warning("⚠️ Aucun événement dans le cluster identifié")
        else:
            st.warning(
                "⚠️ Aucun cluster identifié dans le cache pour cette date. "
                "Les événements seront utilisés directement (cluster unique/non validé)."
            )
            # Fallback : charger tous les événements
            df_events = load_events_for_date(
                target_date,
                DB_PATH,
                timezone_str=timezone_str,
                min_importance=min_importance,
                countries=countries_manual if countries_manual else None,
                exclude_no_actual=False
            )
        
        # NOUVEAU : Extraire le noyau dur des événements (le système décide seul)
        # IMPORTANT : Comme dans le pipeline, on doit extraire le noyau dur par cluster (heure spécifique)
        # et non sur tous les événements de la journée
        if not df_events.empty:
            date_str = target_date.strftime('%Y-%m-%d')
            with st.spinner("🔍 Extraction du noyau dur des événements (décision automatique)..."):
                df_events_all = df_events.copy()  # Garder tous les événements en mémoire
                
                # Identifier le cluster principal (événements à la même heure)
                # Si on a un cluster_principal avec anchor_time, utiliser cette heure
                if cluster_principal and 'anchor_time' in cluster_principal:
                    anchor_time = cluster_principal['anchor_time']
                    if isinstance(anchor_time, pd.Timestamp):
                        if anchor_time.tz is None:
                            anchor_time = anchor_time.tz_localize('Europe/Zurich')
                        else:
                            anchor_time = anchor_time.tz_convert('Europe/Zurich')
                        
                        # Filtrer les événements à la même heure (fenêtre ±15 min) comme dans le pipeline
                        anchor_hour = anchor_time.hour
                        anchor_minute = anchor_time.minute
                        
                        df_events['ts_bern'] = pd.to_datetime(df_events['ts_bern'])
                        df_events_cluster = df_events[
                            (df_events['ts_bern'].dt.hour == anchor_hour) &
                            (df_events['ts_bern'].dt.minute >= max(0, anchor_minute - 15)) &
                            (df_events['ts_bern'].dt.minute <= min(59, anchor_minute + 15))
                        ].copy()
                        
                        if not df_events_cluster.empty:
                            # Extraire le noyau dur sur ce cluster spécifique (comme dans le pipeline)
                            df_events = extract_core_events_for_ui(
                                df_events_cluster,
                                date_str,
                                DB_PATH,
                                support_threshold=0.8,  # Comme dans le pipeline
                                jaccard_threshold=0.7,  # Comme dans le pipeline
                                years_lookback=5,  # CORRIGÉ: 5 comme dans le pipeline
                                anchor_time=anchor_time  # Passer anchor_time pour recharger depuis DB
                            )
                        else:
                            # Si aucun événement dans la fenêtre, garder tous les événements
                            df_events = df_events_all.copy()
                else:
                    # Pas de cluster principal identifié, essayer d'identifier l'heure principale
                    if 'ts_bern' in df_events.columns:
                        df_events['ts_bern'] = pd.to_datetime(df_events['ts_bern'])
                        # Trouver l'heure avec le plus d'événements
                        hour_counts = df_events.groupby(df_events['ts_bern'].dt.hour).size()
                        if not hour_counts.empty:
                            main_hour = hour_counts.idxmax()
                            df_events_cluster = df_events[df_events['ts_bern'].dt.hour == main_hour].copy()
                            
                            if not df_events_cluster.empty:
                                # Extraire le noyau dur sur ce cluster
                                # Créer un anchor_time approximatif pour cette heure
                                anchor_time_approx = pd.Timestamp(date_str).replace(hour=main_hour, minute=0)
                                anchor_time_approx = anchor_time_approx.tz_localize('Europe/Zurich')
                                
                                df_events = extract_core_events_for_ui(
                                    df_events_cluster,
                                    date_str,
                                    DB_PATH,
                                    support_threshold=0.8,
                                    jaccard_threshold=0.7,
                                    years_lookback=5,  # CORRIGÉ: 5 comme dans le pipeline
                                    anchor_time=anchor_time_approx
                                )
                            else:
                                df_events = df_events_all.copy()
                        else:
                            df_events = df_events_all.copy()
                    else:
                        df_events = df_events_all.copy()
            
            if len(df_events) < len(df_events_all):
                st.success(f"✅ Noyau dur extrait : {len(df_events)} événements essentiels (sur {len(df_events_all)} au total)")
                with st.expander("ℹ️ Voir tous les événements (non-essentiels)"):
                    st.dataframe(df_events_all[['ts_bern', 'country', 'event_title', 'event_key', 'importance_n']], use_container_width=True)
            else:
                st.info(f"ℹ️ {len(df_events)} événements affichés (noyau dur = tous les événements)")
        
        # Section pour renseigner les actuals manquants (NOYAU DUR UNIQUEMENT)
        if not df_events.empty:
            st.header("✏️ Renseigner les Actuals Manquants")
            
            # Identifier les événements sans actual
            events_without_actual = df_events[
                (df_events['actual'].isna()) | (df_events['actual'] == '')
            ].copy()
            
            if not events_without_actual.empty:
                st.info(f"ℹ️ {len(events_without_actual)} événement(s) du **noyau dur** sans actual détecté(s). "
                       f"Vous pouvez les renseigner ci-dessous pour améliorer la prédiction.")
                
                actuals_dict = {}
                
                for idx, row in events_without_actual.iterrows():
                    event_key = row['event_key']
                    ts_bern = row['ts_bern']
                    event_title = row.get('event_title', event_key)
                    estimate = row.get('estimate', None)
                    previous = row.get('previous', None)
                    
                    # Créer une clé unique pour ce champ
                    if isinstance(ts_bern, pd.Timestamp):
                        ts_str = ts_bern.strftime('%Y%m%d_%H%M%S')
                    else:
                        ts_str = str(ts_bern).replace(' ', '_').replace(':', '')
                    unique_key = f"actual_manual_{event_key}_{ts_str}_{idx}"
                    
                    with st.expander(f"📝 {event_title} ({row['country']}) - {ts_bern.strftime('%H:%M') if isinstance(ts_bern, pd.Timestamp) else ts_bern}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            if previous is not None and not pd.isna(previous):
                                st.text(f"**Previous:** {previous}")
                            if estimate is not None and not pd.isna(estimate):
                                st.text(f"**Estimate:** {estimate}")
                        
                        with col2:
                            actual_input = st.text_input(
                                "**Actual:**",
                                value="",
                                key=unique_key,
                                help="Entrez la valeur réelle publiée (laissez vide si non disponible)"
                            )
                            actuals_dict[(event_key, ts_bern)] = actual_input
                
                # Mettre à jour df_events avec les actuals renseignés
                if actuals_dict:
                    for (event_key, ts_bern), actual_value in actuals_dict.items():
                        if actual_value.strip():  # Si une valeur a été saisie
                            try:
                                # Convertir en float si possible
                                actual_float = float(actual_value)
                                # Trouver la ligne correspondante et mettre à jour
                                mask = (df_events['event_key'] == event_key) & (df_events['ts_bern'] == ts_bern)
                                if mask.any():
                                    df_events.loc[mask, 'actual'] = actual_float
                                    st.success(f"✅ Actual mis à jour pour {event_key}")
                            except ValueError:
                                st.warning(f"⚠️ Valeur invalide pour {event_key}: '{actual_value}' (doit être un nombre)")
            else:
                st.success("✅ Tous les événements ont un actual")
        
        # Enrichissement Events
        st.header("🔧 Enrichissement Événements")
        
        with st.spinner("Calcul des surprises et scores ajustés..."):
            df_events_enriched = enrich_events_with_surprises(df_events)
        
        st.success("✅ Événements enrichis")
        
        with st.expander("📋 Détails des événements enrichis (Noyau dur uniquement)"):
            # Sélectionner les colonnes à afficher
            columns_to_show = [
                'ts_bern', 'country', 'event_title',
                'previous', 'estimate', 'actual',
                'empirical_score', 'surprise_pct', 'score_adjusted'
            ]
            
            # Filtrer pour ne garder que les colonnes qui existent
            available_columns = [col for col in columns_to_show if col in df_events_enriched.columns]
            
            # Créer une copie pour le formatage
            df_display = df_events_enriched[available_columns].copy()
            
            # Formater les colonnes numériques pour meilleure lisibilité
            numeric_cols = ['previous', 'estimate', 'actual', 'empirical_score', 'surprise_pct', 'score_adjusted']
            for col in numeric_cols:
                if col in df_display.columns:
                    # Formater avec 2 décimales si ce sont des valeurs numériques
                    df_display[col] = df_display[col].apply(
                        lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else str(x) if pd.notna(x) else "N/A"
                    )
            
            # Formater ts_bern pour affichage
            if 'ts_bern' in df_display.columns:
                df_display['ts_bern'] = df_display['ts_bern'].apply(
                    lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else "N/A"
                )
            
            st.dataframe(df_display, use_container_width=True)
        
        # Détection Pattern
        st.header("🎯 Détection Pattern")
        
        # Si cluster principal identifié, utiliser son heure d'ancrage pour filtrer les mouvements
        cluster_anchor_time = None
        if cluster_principal and 'anchor_time' in cluster_principal:
            cluster_anchor_time = cluster_principal['anchor_time']
            # anchor_time est déjà un pd.Timestamp (ts_bern), donc on peut l'utiliser directement
            # Mais on doit s'assurer qu'il a un timezone
            if isinstance(cluster_anchor_time, pd.Timestamp):
                if cluster_anchor_time.tz is None:
                    cluster_anchor_time = cluster_anchor_time.tz_localize('Europe/Zurich')
                else:
                    cluster_anchor_time = cluster_anchor_time.tz_convert('Europe/Zurich')
            st.info(f"📌 Recherche de mouvement autour de {cluster_anchor_time.strftime('%H:%M')} (cluster principal)")
        elif not df_events_enriched.empty:
            # Fallback : utiliser l'heure du premier événement pour prioriser les mouvements
            cluster_anchor_time = df_events_enriched['ts_bern'].min()
            if isinstance(cluster_anchor_time, pd.Timestamp):
                if cluster_anchor_time.tz is None:
                    cluster_anchor_time = cluster_anchor_time.tz_localize('Europe/Zurich')
                else:
                    cluster_anchor_time = cluster_anchor_time.tz_convert('Europe/Zurich')
            st.info(f"📌 Recherche de mouvement autour de {cluster_anchor_time.strftime('%H:%M')} (premier événement)")
        else:
            st.warning("⚠️ Aucune heure de référence disponible pour la recherche de mouvement")
        
        with st.spinner("Scan des mouvements de prix..."):
            pattern_result = detect_pattern_type(
                df_prices,
                df_events_enriched,
                min_pips,
                tz,  # tz est défini ligne 1314
                cluster_anchor_time=cluster_anchor_time  # Passer l'heure du cluster pour prioriser
            )
        
        pattern_type = pattern_result['pattern_type']
        confidence = pattern_result['detection_confidence']
        metrics = pattern_result.get('metrics', {})
        
        # Afficher résultat détection
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pattern détecté", pattern_type)
        with col2:
            st.metric("Confiance", f"{confidence * 100:.1f}%")
        
        # Définir silent_warning au début du scope pour éviter NameError
        silent_warning = SILENT_WARNING_DEFAULT  # fallback global
        
        if pattern_type != 'INCONNU':
            st.success(f"✅ {pattern_result.get('reason', 'Pattern détecté')}")
            
            # Vérifier si le mouvement détecté est éloigné de l'heure du cluster
            if cluster_anchor_time is not None and 'movement' in pattern_result and pattern_result['movement']:
                movement_start = pattern_result['movement'].get('start_time')
                if movement_start:
                    movement_start_ts = pd.Timestamp(movement_start)
                    if movement_start_ts.tz is None:
                        movement_start_ts = movement_start_ts.tz_localize('Europe/Zurich')
                    else:
                        movement_start_ts = movement_start_ts.tz_convert('Europe/Zurich')
                    
                    cluster_anchor_ts = pd.Timestamp(cluster_anchor_time)
                    if cluster_anchor_ts.tz is None:
                        cluster_anchor_ts = cluster_anchor_ts.tz_localize('Europe/Zurich')
                    else:
                        cluster_anchor_ts = cluster_anchor_ts.tz_convert('Europe/Zurich')
                    
                    time_diff_minutes = abs((movement_start_ts - cluster_anchor_ts).total_seconds() / 60)
                    if time_diff_minutes > 30 and not silent_warning:
                        st.warning(
                            f"⚠️ **Attention** : Le mouvement détecté commence à {movement_start_ts.strftime('%H:%M')}, "
                            f"alors que le cluster est à {cluster_anchor_ts.strftime('%H:%M')} "
                            f"(écart de {time_diff_minutes:.0f} minutes). "
                            f"Vérifiez que c'est bien le bon mouvement ou réduisez le seuil min_pips."
                        )
            
            if 'impact_pips' in metrics:
                # Afficher Impact détecté et Impact unifié côte à côte
                col_impact_1, col_impact_2 = st.columns(2)
                with col_impact_1:
                    st.metric("Impact détecté", f"{metrics['impact_pips']:.1f} pips")
                with col_impact_2:
                    # 🆕 Afficher Impact unifié (beta) si disponible
                    if 'impact_unified_pips' in metrics and metrics['impact_unified_pips'] is not None:
                        unified_pips = metrics['impact_unified_pips']
                        unified_dir = metrics.get('impact_unified_direction', 0)
                        direction_emoji = "⬆️" if unified_dir == 1 else "⬇️" if unified_dir == -1 else ""
                        st.metric(
                            "Impact unifié (beta)",
                            f"{unified_pips:.1f} pips {direction_emoji}",
                            help="Impact selon IMPACT_SPEC_V1 (baseline=event_open, horizon=120min)"
                        )
                    else:
                        st.metric("Impact unifié (beta)", "N/A", help="Non disponible")
        else:
            st.warning(f"⚠️ {pattern_result.get('reason', 'Pattern non détecté')}")
        
        # Prédictions selon pattern
        if pattern_type != 'INCONNU':
            st.header("🔮 Prédictions")
            
            # NOUVEAU : Option pour utiliser le pipeline complet
            use_complete_pipeline = st.checkbox(
                "🚀 Utiliser le pipeline complet (Random Forest + Stratégie de sortie optimisée)",
                value=True,
                help="Active le pipeline complet avec toutes les améliorations récentes (Random Forest, stratégie de sortie optimisée, etc.)"
            )
            
            if pattern_type == 'DOUBLE_WAVE':
                # NOUVEAU : Utiliser le pipeline complet si activé
                if use_complete_pipeline:
                    try:
                        from run_pipeline_complete import PipelineExecutor
                        
                        date_str = target_date.strftime('%Y-%m-%d')
                        
                        with st.spinner("Calcul avec pipeline complet (Random Forest + Stratégie de sortie optimisée)..."):
                            executor = PipelineExecutor(
                                db_path=DB_PATH,
                                verbose=False,
                                force_timeframe=None
                            )
                            
                            # Utiliser les mêmes paramètres par défaut que le pipeline validé
                            # Note: jaccard_threshold=0.8 dans execute_complete_pipeline, mais 0.7 dans etape3
                            # On utilise 0.8 pour être cohérent avec execute_complete_pipeline
                            result = executor.execute_complete_pipeline(
                                date_str,
                                window_minutes=30,  # Comme dans le pipeline
                                support_threshold=0.8,  # Comme dans le pipeline
                                jaccard_threshold=0.8,  # Comme dans execute_complete_pipeline (0.7 utilisé dans etape3)
                                years_lookback=5  # Comme dans le pipeline
                            )
                            
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
                                
                                # Extraire la direction avec fallback (même logique que pipeline)
                                # La direction peut être dans plusieurs endroits
                                direction = None
                                
                                # 1. Depuis pattern_info (dans final_prediction)
                                pattern_info = final_prediction.get('pattern_info', {})
                                if isinstance(pattern_info, dict):
                                    direction = pattern_info.get('direction')
                                
                                # 2. Depuis final_prediction directement (pattern_direction)
                                if not direction:
                                    direction = final_prediction.get('pattern_direction')
                                
                                # 3. Depuis pattern_type pour déduire direction
                                if not direction:
                                    pattern_type = final_prediction.get('pattern_type', '')
                                    if not pattern_type and isinstance(pattern_info, dict):
                                        pattern_type = pattern_info.get('pattern_type', '')
                                    if pattern_type:
                                        if 'UP' in str(pattern_type).upper():
                                            direction = 'UP'
                                        elif 'DOWN' in str(pattern_type).upper():
                                            direction = 'DOWN'
                                
                                # 4. Fallback : UNKNOWN
                                if not direction:
                                    direction = 'UNKNOWN'
                                
                                # Extraire les informations de pattern pour calculer les prix
                                # IMPORTANT: pattern_info contient toutes les métriques détectées
                                if isinstance(pattern_info, dict):
                                    wave1_pips = pattern_info.get('wave1_pips', 0) or 0
                                    pullback_pips_info = pattern_info.get('pullback_pips', 0) or 0
                                    wave2_pips = pattern_info.get('wave2_pips', 0) or 0
                                    baseline_price_from_pattern = pattern_info.get('baseline_price')
                                    
                                    # CORRIGÉ: Gérer SINGLE_WAVE vs DOUBLE_WAVE
                                    pattern_type_detected = pattern_info.get('pattern_type', '')
                                    
                                    if pattern_type_detected == 'DOUBLE_WAVE':
                                        # DOUBLE_WAVE : utiliser les valeurs directes
                                        if wave1_pips == 0 and pullback_pips_info == 0 and wave2_pips == 0:
                                            # Fallback : utiliser impact_pips avec ratios
                                            impact_pips = pattern_info.get('impact_pips', 0)
                                            if impact_pips > 0:
                                                wave1_pips = impact_pips * 0.58  # 58% pour wave1
                                                pullback_pips_info = wave1_pips * 0.84  # 84% pour pullback
                                                wave2_pips = impact_pips * 0.90  # 90% pour wave2
                                    else:
                                        # SINGLE_WAVE : utiliser impact_pips et calculer les ratios
                                        impact_pips = pattern_info.get('impact_pips', 0) or 0
                                        if impact_pips > 0:
                                            # Pour SINGLE_WAVE, simuler un Double Wave avec ratios standards
                                            wave1_pips = impact_pips * 0.58  # 58% pour wave1
                                            pullback_pips_info = wave1_pips * 0.84  # 84% pour pullback
                                            wave2_pips = impact_pips * 0.90  # 90% pour wave2
                                else:
                                    wave1_pips = 0
                                    pullback_pips_info = 0
                                    wave2_pips = 0
                                    baseline_price_from_pattern = None
                                
                                # Extraire les informations supplémentaires depuis final_prediction
                                exit_compensation_factor = final_prediction.get('exit_compensation_factor')
                                exit_percentage = final_prediction.get('exit_percentage')
                                
                                # Créer un prediction_result compatible avec toutes les infos nécessaires
                                prediction_result = {
                                    'prediction_pips': impact_predicted,
                                    'amplification': final_prediction.get('amplification_predite'),
                                    'status': 'predicted',
                                    'reason': 'Pipeline complet avec Random Forest et stratégie de sortie optimisée',
                                    'method': 'complete_pipeline',
                                    'exit_target': exit_target,
                                    'exit_strategy': exit_strategy,
                                    'exit_compensation_factor': exit_compensation_factor,
                                    'exit_percentage': exit_percentage,
                                    'direction': direction,
                                    'pattern_info': pattern_info,
                                    # Ajouter les pips pour compatibilité avec affichage
                                    'phase1_pips': wave1_pips,
                                    'pullback_pips': pullback_pips_info,
                                    'phase2_pips': wave2_pips,
                                    'baseline_price_from_pattern': baseline_price_from_pattern
                                }
                            else:
                                raise Exception("Pipeline complet échoué")
                    except Exception as e:
                        st.warning(f"⚠️ Erreur pipeline complet, utilisation de la méthode de base : {e}")
                        use_complete_pipeline = False
                
                # Méthode originale (fallback ou si pipeline complet désactivé)
                if not use_complete_pipeline or 'prediction_result' not in locals():
                    with st.spinner("Calcul prédiction Double Wave..."):
                        # Obtenir baseline_price et direction depuis le pattern détecté
                        baseline_price_sr = None
                        direction_sr = 'UP'
                        if 'movement' in pattern_result and pattern_result['movement']:
                            baseline_price_sr = pattern_result['movement'].get('baseline_price')
                            direction_sr = pattern_result['movement'].get('direction', 'UP')
                        elif not df_prices.empty:
                            first_price_row = df_prices.iloc[0]
                            baseline_price_sr = (first_price_row['open'] + first_price_row['close']) / 2
                        
                        prediction_result = predict_double_wave_base(
                            df_events_enriched,
                            baseline_price=baseline_price_sr,
                            direction=direction_sr,
                            use_support_resistance=True,
                            use_aggregate_indicators=True
                        )
                
                if prediction_result['status'] == 'predicted':
                    if prediction_result.get('method') == 'complete_pipeline':
                        st.success("✅ Prédiction calculée avec pipeline complet (Random Forest + Stratégie de sortie optimisée)")
                    else:
                        st.success("✅ Prédiction Double Wave calculée (formules validées)")
                    
                    col_top = st.columns(2)
                    with col_top[0]:
                        st.metric(
                            "Impact prédit",
                            f"{prediction_result['prediction_pips']:.1f} pips"
                        )
                    with col_top[1]:
                        if prediction_result.get('method') == 'complete_pipeline':
                            st.metric(
                                "Target de sortie",
                                f"{prediction_result.get('exit_target', 0):.1f} pips" if prediction_result.get('exit_target') else "N/A"
                            )
                        else:
                            st.metric(
                                "Impact de base (Formule D)",
                                f"{prediction_result.get('base_impact', 0):.1f} pips"
                            )
                    
                    # NOUVEAU : Afficher target de sortie optimisé si disponible (comme pour SINGLE_WAVE)
                    if prediction_result.get('exit_target') is not None and prediction_result.get('method') == 'complete_pipeline':
                        st.markdown("### 🎯 Stratégie de Sortie Optimisée")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Target de sortie", f"{prediction_result['exit_target']:.1f} pips")
                        col2.metric("Direction", prediction_result.get('direction', 'UNKNOWN'))
                        col3.metric("Stratégie", prediction_result.get('exit_strategy', 'N/A')[:30] + "..." if len(prediction_result.get('exit_strategy', '')) > 30 else prediction_result.get('exit_strategy', 'N/A'))
                        
                        with st.expander("ℹ️ Détails de la stratégie de sortie", expanded=False):
                            st.write(f"**Stratégie utilisée :** {prediction_result.get('exit_strategy', 'N/A')}")
                            st.write(f"**Impact prédit :** {prediction_result['prediction_pips']:.1f} pips")
                            st.write(f"**Target de sortie :** {prediction_result['exit_target']:.1f} pips")
                            st.write(f"**Direction :** {prediction_result.get('direction', 'UNKNOWN')}")
                            if prediction_result.get('exit_compensation_factor'):
                                st.write(f"**Facteur de compensation :** {prediction_result.get('exit_compensation_factor', 1.0):.3f}x")
                            if prediction_result.get('exit_percentage'):
                                st.write(f"**Pourcentage de sortie :** {prediction_result.get('exit_percentage', 80):.0f}%")
                            st.info("💡 **Conseil trading :** Sortir à ce target pour maximiser les gains tout en restant sécurisé (efficacité moyenne : 72.6%)")
                    
                    # Calculer les prix et heures correspondants
                    baseline_price = None
                    baseline_time = None
                    direction = 'UP'
                    
                    # NOUVEAU : Si pipeline complet, extraire depuis pattern_info
                    if prediction_result.get('method') == 'complete_pipeline':
                        pattern_info = prediction_result.get('pattern_info', {})
                        if isinstance(pattern_info, dict):
                            baseline_price = pattern_info.get('baseline_price')
                            # CORRIGÉ: Utiliser prediction_result au lieu de pattern_result (qui n'existe pas)
                            direction = prediction_result.get('direction', 'UNKNOWN')
                            if direction == 'UNKNOWN':
                                direction = pattern_info.get('direction', 'UP')
                            # Fallback supplémentaire : déduire depuis pattern_type
                            if direction == 'UNKNOWN' or not direction:
                                pattern_type_str = str(pattern_info.get('pattern_type', '')).upper()
                                if 'UP' in pattern_type_str:
                                    direction = 'UP'
                                elif 'DOWN' in pattern_type_str:
                                    direction = 'DOWN'
                                else:
                                    direction = 'UP'  # Default
                            
                            # Extraire les timings depuis pattern_info
                            wave1_peak_time = pattern_info.get('wave1_peak_time')
                            pullback_time_info = pattern_info.get('pullback_time')
                            wave2_peak_time = pattern_info.get('wave2_peak_time')
                            
                            # Extraire les pips depuis pattern_info
                            wave1_pips = pattern_info.get('wave1_pips', 0)
                            pullback_pips_info = pattern_info.get('pullback_pips', 0)
                            wave2_pips = pattern_info.get('wave2_pips', 0)
                            
                            # Utiliser l'heure du premier événement comme baseline_time si disponible
                            if not df_events_enriched.empty:
                                baseline_time = df_events_enriched['ts_bern'].min()
                            
                            # Si baseline_price n'est pas disponible, utiliser pattern_baseline_price depuis final_prediction
                            if baseline_price is None:
                                baseline_price = final_prediction.get('pattern_baseline_price')
                            
                            # Si toujours pas disponible, utiliser le prix au moment de l'événement
                            if baseline_price is None and not df_prices.empty and baseline_time:
                                # Chercher le prix le plus proche de baseline_time
                                df_prices_copy = df_prices.copy()
                                if 'datetime' in df_prices_copy.columns or df_prices_copy.index.name == 'datetime':
                                    if df_prices_copy.index.name == 'datetime':
                                        df_prices_copy = df_prices_copy.reset_index()
                                    df_prices_copy['datetime'] = pd.to_datetime(df_prices_copy['datetime'])
                                    closest_price = df_prices_copy.iloc[(df_prices_copy['datetime'] - baseline_time).abs().argsort()[:1]]
                                    if not closest_price.empty:
                                        baseline_price = (closest_price.iloc[0]['open'] + closest_price.iloc[0]['close']) / 2
                    else:
                        # Méthode originale : Obtenir baseline_price, baseline_time et direction
                        # PRIORITÉ : Utiliser l'heure du mouvement détecté depuis les prix
                        if 'movement' in pattern_result and pattern_result['movement']:
                            baseline_price = pattern_result['movement'].get('baseline_price')
                            baseline_time = pattern_result['movement'].get('start_time')
                            direction = pattern_result['movement'].get('direction', 'UP')
                            
                            # S'assurer que baseline_time est bien un datetime
                            if baseline_time is not None:
                                if isinstance(baseline_time, str):
                                    baseline_time = pd.Timestamp(baseline_time)
                                elif not isinstance(baseline_time, (pd.Timestamp, datetime)):
                                    baseline_time = None
                        elif 'metrics' in pattern_result:
                            direction = pattern_result['metrics'].get('direction', 'UP')
                        
                        # Si baseline_time n'est toujours pas disponible, utiliser l'heure du premier événement
                        if baseline_time is None and not df_events_enriched.empty:
                            baseline_time = df_events_enriched['ts_bern'].min()
                            st.info("ℹ️ Utilisation de l'heure du premier événement comme baseline (mouvement non détecté)")
                        
                        # Si baseline_price n'est pas disponible, essayer de l'extraire du premier prix
                        if baseline_price is None and not df_prices.empty:
                            first_price_row = df_prices.iloc[0]
                            baseline_price = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    if baseline_price is not None and baseline_time is not None:
                        # NOUVEAU : Extraire les pips selon la méthode utilisée
                        if prediction_result.get('method') == 'complete_pipeline':
                            # Utiliser les valeurs depuis pattern_info (déjà extraites plus haut)
                            phase1_pips = wave1_pips if 'wave1_pips' in locals() and wave1_pips else 0
                            pullback_pips = pullback_pips_info if 'pullback_pips_info' in locals() and pullback_pips_info else 0
                            phase2_pips = wave2_pips if 'wave2_pips' in locals() and wave2_pips else 0
                            prediction_pips = prediction_result.get('prediction_pips', 0)
                            
                            # DEBUG: Si les pips sont à 0, essayer depuis pattern_info directement
                            if phase1_pips == 0 and isinstance(pattern_info, dict):
                                phase1_pips = pattern_info.get('wave1_pips', 0) or pattern_info.get('impact_pips', 0) * 0.58  # 58% pour wave1
                            if pullback_pips == 0 and isinstance(pattern_info, dict):
                                pullback_pips = pattern_info.get('pullback_pips', 0) or (phase1_pips * 0.84)  # 84% pour pullback
                            if phase2_pips == 0 and isinstance(pattern_info, dict):
                                phase2_pips = pattern_info.get('wave2_pips', 0) or pattern_info.get('impact_pips', 0) * 0.90  # 90% pour wave2
                        else:
                            # Méthode originale
                            phase1_pips = prediction_result.get('phase1_pips', 0)
                            pullback_pips = prediction_result.get('pullback_pips', 0)
                            phase2_pips = prediction_result.get('phase2_pips', 0)
                            prediction_pips = prediction_result.get('prediction_pips', 0)
                        
                        # Calculer les prix selon la direction
                        if direction == 'UP':
                            baseline = baseline_price
                            pic1 = baseline + phase1_pips / 10000
                            pullback = pic1 - pullback_pips / 10000
                            pic2 = baseline + phase2_pips / 10000
                            stabilisation = pic2  # Stabilisation au pic 2
                        else:  # DOWN
                            baseline = baseline_price
                            pic1 = baseline - phase1_pips / 10000
                            pullback = pic1 + pullback_pips / 10000
                            pic2 = baseline - phase2_pips / 10000
                            stabilisation = pic2  # Stabilisation au pic 2
                        
                        # Utiliser les heures réelles détectées depuis les prix (si disponibles)
                        from datetime import timedelta
                        baseline_dt = pd.Timestamp(baseline_time) if isinstance(baseline_time, (str, pd.Timestamp)) else baseline_time
                        if baseline_dt.tz is None:
                            baseline_dt = baseline_dt.tz_localize('Europe/Zurich')
                        else:
                            # S'assurer que c'est en timezone de Berne
                            baseline_dt = baseline_dt.tz_convert('Europe/Zurich')
                        
                        # Afficher l'heure de baseline utilisée (pour debug)
                        st.caption(f"📍 Baseline détectée : {baseline_dt.strftime('%H:%M')} (début du mouvement depuis les prix)")
                        
                        # Essayer d'utiliser les heures réelles détectées
                        pic1_time = baseline_dt
                        pullback_time = baseline_dt
                        pic2_time = baseline_dt
                        stabilisation_time = baseline_dt
                        
                        if 'wave1_peak' in pattern_result:
                            pic1_time = pd.Timestamp(pattern_result['wave1_peak'])
                            if pic1_time.tz is None:
                                pic1_time = pic1_time.tz_localize('Europe/Zurich')
                        
                        if 'pullback_low' in pattern_result:
                            pullback_time = pd.Timestamp(pattern_result['pullback_low'])
                            if pullback_time.tz is None:
                                pullback_time = pullback_time.tz_localize('Europe/Zurich')
                        
                        if 'wave2_peak' in pattern_result:
                            pic2_time = pd.Timestamp(pattern_result['wave2_peak'])
                            if pic2_time.tz is None:
                                pic2_time = pic2_time.tz_localize('Europe/Zurich')
                            # Stabilisation = pic2 + 25 minutes (timing théorique pour stabilisation)
                            stabilisation_time = pic2_time + timedelta(minutes=25)
                        else:
                            # Fallback : timings théoriques si pas de détection
                            pic1_time = baseline_dt + timedelta(minutes=5)   # T+5
                            pullback_time = baseline_dt + timedelta(minutes=11)  # T+11
                            pic2_time = baseline_dt + timedelta(minutes=15)  # T+15
                            stabilisation_time = baseline_dt + timedelta(minutes=40)  # T+40
                        
                        # Calculer les délais réels depuis baseline
                        pic1_delay = int((pic1_time - baseline_dt).total_seconds() / 60)
                        pullback_delay = int((pullback_time - baseline_dt).total_seconds() / 60)
                        pic2_delay = int((pic2_time - baseline_dt).total_seconds() / 60)
                        stabilisation_delay = int((stabilisation_time - baseline_dt).total_seconds() / 60)
                        
                        # Afficher les phases avec prix et heures
                        st.subheader("🌊 Détails du mouvement Double Wave")
                        col_phases = st.columns(5)
                        
                        with col_phases[0]:
                            st.metric(
                                "Baseline",
                                f"{baseline:.5f}",
                                help=f"Prix de départ - {baseline_dt.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {baseline_dt.strftime('%H:%M')}")
                        with col_phases[1]:
                            st.metric(
                                "Pic 1 (algos)",
                                f"{pic1:.5f}",
                                delta=f"+{phase1_pips:.1f} pips" if direction == 'UP' else f"-{phase1_pips:.1f} pips",
                                help=f"Premier pic (Phase 1) - {pic1_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pic1_time.strftime('%H:%M')} (T+{pic1_delay})")
                        with col_phases[2]:
                            st.metric(
                                "Pullback (prises profits)",
                                f"{pullback:.5f}",
                                delta=f"-{pullback_pips:.1f} pips" if direction == 'UP' else f"+{pullback_pips:.1f} pips",
                                help=f"Point de pullback - {pullback_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pullback_time.strftime('%H:%M')} (T+{pullback_delay})")
                        with col_phases[3]:
                            st.metric(
                                "Pic 2 (institutionnels)",
                                f"{pic2:.5f}",
                                delta=f"+{phase2_pips:.1f} pips" if direction == 'UP' else f"-{phase2_pips:.1f} pips",
                                help=f"Deuxième pic (Phase 2) - {pic2_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pic2_time.strftime('%H:%M')} (T+{pic2_delay})")
                        with col_phases[4]:
                            st.metric(
                                "Stabilisation",
                                f"{stabilisation:.5f}",
                                delta=f"+{prediction_pips:.1f} pips" if direction == 'UP' else f"-{prediction_pips:.1f} pips",
                                help=f"Point de stabilisation - {stabilisation_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {stabilisation_time.strftime('%H:%M')} (T+{stabilisation_delay})")
                    else:
                        # Fallback si baseline_price non disponible
                        col_phases = st.columns(3)
                        with col_phases[0]:
                            st.metric(
                                "Phase 1 (algos)",
                                f"{prediction_result.get('phase1_pips', 0):.1f} pips"
                            )
                        with col_phases[1]:
                            st.metric(
                                "Pullback (prises profits)",
                                f"{prediction_result.get('pullback_pips', 0):.1f} pips"
                            )
                        with col_phases[2]:
                            st.metric(
                                "Phase 2 (institutionnels)",
                                f"{prediction_result.get('phase2_pips', 0):.1f} pips"
                            )
                        st.caption("⚠️ Prix non disponibles (baseline_price introuvable)")
                    
                    # Afficher Support/Résistance si disponible
                    sr_info = prediction_result.get('support_resistance', {})
                    if sr_info.get('available', False):
                        st.subheader("📊 Niveaux Support/Résistance (Finnhub)")
                        col_sr = st.columns(3)
                        
                        with col_sr[0]:
                            if sr_info.get('nearest_support'):
                                st.metric(
                                    "Support le plus proche",
                                    f"{sr_info['nearest_support']:.5f}",
                                    delta=f"{sr_info.get('support_distance_pips', 0):.1f} pips",
                                    help="Niveau de support le plus proche du prix de base"
                                )
                            else:
                                st.metric("Support le plus proche", "N/A")
                        
                        with col_sr[1]:
                            validation = sr_info.get('validation', {})
                            validation_status = validation.get('validation', 'weak')
                            if validation_status == 'strong':
                                st.success("✅ Prédiction validée par niveau")
                            elif validation_status == 'moderate':
                                st.info("⚠️ Prédiction proche d'un niveau")
                            else:
                                st.metric("Validation", "Aucun niveau proche")
                        
                        with col_sr[2]:
                            if sr_info.get('nearest_resistance'):
                                st.metric(
                                    "Résistance la plus proche",
                                    f"{sr_info['nearest_resistance']:.5f}",
                                    delta=f"{sr_info.get('resistance_distance_pips', 0):.1f} pips",
                                    help="Niveau de résistance le plus proche du prix prédit"
                                )
                            else:
                                st.metric("Résistance la plus proche", "N/A")
                        
                        # Afficher les top niveaux
                        if sr_info.get('all_supports') or sr_info.get('all_resistances'):
                            with st.expander("📋 Tous les niveaux (Top 3)"):
                                col_all = st.columns(2)
                                with col_all[0]:
                                    st.write("**Supports:**")
                                    for sup in sr_info.get('all_supports', []):
                                        st.write(f"  - {sup:.5f}")
                                with col_all[1]:
                                    st.write("**Résistances:**")
                                    for res in sr_info.get('all_resistances', []):
                                        st.write(f"  - {res:.5f}")
                    
                    # Afficher Aggregate Indicators si disponible
                    ai_info = prediction_result.get('aggregate_indicators')
                    ai_adjustment = prediction_result.get('ai_adjustment')
                    if ai_info:
                        st.subheader("📊 Aggregate Indicators (Finnhub)")
                        col_ai = st.columns(4)
                        
                        with col_ai[0]:
                            signal = ai_info.get('signal', 'neutral')
                            signal_emoji = {'buy': '🟢', 'strong buy': '🟢', 'sell': '🔴', 'strong sell': '🔴', 'neutral': '🟡'}.get(signal.lower(), '🟡')
                            st.metric("Signal agrégé", f"{signal_emoji} {signal.upper()}")
                        
                        with col_ai[1]:
                            buy_count = ai_info.get('buy_count', 0)
                            neutral_count = ai_info.get('neutral_count', 0)
                            sell_count = ai_info.get('sell_count', 0)
                            st.metric("Indicateurs", f"B:{buy_count} N:{neutral_count} S:{sell_count}")
                        
                        with col_ai[2]:
                            adx = ai_info.get('adx')
                            trending = ai_info.get('trending', False)
                            adx_str = f'{adx:.1f}' if adx else 'N/A'
                            trend_str = 'Trending' if trending else 'Sideways'
                            st.metric("Trend", f"{trend_str} (ADX: {adx_str})")
                        
                        with col_ai[3]:
                            if ai_adjustment and ai_adjustment.get('adjustment_factor', 1.0) < 1.0:
                                factor = ai_adjustment['adjustment_factor']
                                reduction = (1 - factor) * 100
                                st.warning(f"⚠️ Réduction: {reduction:.1f}%")
                            else:
                                st.success("✅ Pas d'ajustement")
                    
                    st.caption(
                        f"{prediction_result['reason']} – "
                        f"Amplification {prediction_result.get('amplification', 0):.2f} | "
                        f"Surprise max {prediction_result.get('surprise_max', 0):.1f}%"
                    )
                else:
                    st.warning(f"⚠️ {prediction_result['reason']}")
            
            elif pattern_type in ['SINGLE_WAVE_FORT', 'SINGLE_WAVE_STANDARD']:
                with st.spinner("Calcul prédiction Single Wave..."):
                    # Extraire movement_datetime si disponible
                    movement_datetime = None
                    if 'movement' in pattern_result and 'start_time' in pattern_result['movement']:
                        movement_datetime = pd.Timestamp(pattern_result['movement']['start_time'])
                    
                    # Obtenir baseline_price et direction depuis le pattern détecté
                    baseline_price_sr = None
                    direction_sr = 'UP'
                    if 'movement' in pattern_result and pattern_result['movement']:
                        baseline_price_sr = pattern_result['movement'].get('baseline_price')
                        direction_sr = pattern_result['movement'].get('direction', 'UP')
                    elif not df_prices.empty:
                        first_price_row = df_prices.iloc[0]
                        baseline_price_sr = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    prediction_result = predict_single_wave_base(
                        df_events_enriched,
                        df_prices,
                        pattern_type,
                        movement_datetime=movement_datetime,
                        baseline_price=baseline_price_sr,
                        direction=direction_sr,
                        use_support_resistance=True,
                        use_aggregate_indicators=True
                    )
                
                if prediction_result['status'] == 'predicted':
                    if prediction_result.get('method') == 'complete_pipeline':
                        st.success("✅ Prédiction calculée avec pipeline complet (Random Forest + Stratégie de sortie optimisée)")
                    else:
                        st.success("✅ Prédiction Single Wave calculée")
                    
                    # NOUVEAU : Afficher target de sortie optimisé si disponible
                    if prediction_result.get('exit_target') is not None:
                        st.markdown("### 🎯 Stratégie de Sortie Optimisée")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Target de sortie", f"{prediction_result['exit_target']:.1f} pips")
                        col2.metric("Direction", prediction_result.get('direction', 'UNKNOWN'))
                        col3.metric("Stratégie", prediction_result.get('exit_strategy', 'N/A')[:30] + "..." if len(prediction_result.get('exit_strategy', '')) > 30 else prediction_result.get('exit_strategy', 'N/A'))
                        
                        with st.expander("ℹ️ Détails de la stratégie de sortie", expanded=False):
                            st.write(f"**Stratégie utilisée :** {prediction_result.get('exit_strategy', 'N/A')}")
                            st.write(f"**Impact prédit :** {prediction_result['prediction_pips']:.1f} pips")
                            st.write(f"**Target de sortie :** {prediction_result['exit_target']:.1f} pips")
                            st.write(f"**Direction :** {prediction_result.get('direction', 'UNKNOWN')}")
                            st.info("💡 **Conseil trading :** Sortir à ce target pour maximiser les gains tout en restant sécurisé (efficacité moyenne : 72.6%)")
                    
                    # Obtenir baseline_price pour enrichissement Support/Résistance (affichage)
                    baseline_price = None
                    if 'movement' in pattern_result and pattern_result['movement']:
                        baseline_price = pattern_result['movement'].get('baseline_price')
                    elif not df_prices.empty:
                        first_price_row = df_prices.iloc[0]
                        baseline_price = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    # Enrichir avec Support/Résistance
                    if baseline_price is not None:
                        prediction_result = enrich_prediction_with_support_resistance(
                            prediction_result,
                            baseline_price=baseline_price,
                            resolution='H1'
                        )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Impact prédit",
                            f"{prediction_result['prediction_pips']:.1f} pips"
                        )
                    with col2:
                        st.metric(
                            "Amplification",
                            f"{prediction_result['amplification']:.4f}"
                        )
                    with col3:
                        st.metric(
                            "R² tendance",
                            f"{prediction_result['r2_trend']:.3f}"
                        )
                    
                    # Afficher Support/Résistance si disponible
                    sr_info = prediction_result.get('support_resistance', {})
                    if sr_info.get('available', False):
                        st.subheader("📊 Niveaux Support/Résistance (Finnhub)")
                        col_sr = st.columns(3)
                        
                        with col_sr[0]:
                            if sr_info.get('nearest_support'):
                                st.metric(
                                    "Support le plus proche",
                                    f"{sr_info['nearest_support']:.5f}",
                                    delta=f"{sr_info.get('support_distance_pips', 0):.1f} pips"
                                )
                            else:
                                st.metric("Support le plus proche", "N/A")
                        
                        with col_sr[1]:
                            validation = sr_info.get('validation', {})
                            validation_status = validation.get('validation', 'weak')
                            if validation_status == 'strong':
                                st.success("✅ Prédiction validée")
                            elif validation_status == 'moderate':
                                st.info("⚠️ Proche d'un niveau")
                            else:
                                st.metric("Validation", "Aucun niveau proche")
                        
                        with col_sr[2]:
                            if sr_info.get('nearest_resistance'):
                                st.metric(
                                    "Résistance la plus proche",
                                    f"{sr_info['nearest_resistance']:.5f}",
                                    delta=f"{sr_info.get('resistance_distance_pips', 0):.1f} pips"
                                )
                            else:
                                st.metric("Résistance la plus proche", "N/A")
                    
                    st.caption(prediction_result['reason'])
                else:
                    st.warning(f"⚠️ {prediction_result['reason']}")
        
        # Résumé Phase 2
        st.info("🚧 **Phase 2 complète** : Enrichissement + Détection Pattern + Prédictions de base")
        st.caption("Prochaines étapes : Ensemble Methods + Timeline Double Wave + Calendrier")
        
    else:
        # Mode calendrier
        st.header("📅 Recherche depuis Calendrier")
        
        # Mode de sélection de période
        period_mode = st.radio(
            "Mode de période",
            ["Période automatique", "Période manuelle (de... à)"],
            key="period_mode_cal_clean"
        )
        
        if period_mode == "Période automatique":
            col1, col2 = st.columns(2)
            with col1:
                search_direction = st.radio(
                    "Direction de recherche",
                    ["Futur", "Passé", "Les deux"],
                    key="search_direction_clean"
                )
            
            with col2:
                lookahead_days = st.number_input(
                    "Nombre de jours",
                    min_value=1,
                    max_value=365,
                    value=30,
                    step=1,
                    key="lookahead_days_clean"
                )
            
            # Calculer période automatique
            now = datetime.now()
            if search_direction == "Futur":
                date_from = datetime(now.year, now.month, now.day)
                date_to = date_from + timedelta(days=lookahead_days)
            elif search_direction == "Passé":
                date_to = datetime(now.year, now.month, now.day)
                date_from = date_to - timedelta(days=lookahead_days)
            else:  # Les deux
                date_from = datetime(now.year, now.month, now.day) - timedelta(days=lookahead_days)
                date_to = datetime(now.year, now.month, now.day) + timedelta(days=lookahead_days)
        else:
            # Période manuelle
            col1, col2 = st.columns(2)
            with col1:
                date_from_str = st.text_input(
                    "📅 Date début (YYYY-MM-DD)",
                    value=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    key="date_from_manual_clean"
                )
            with col2:
                date_to_str = st.text_input(
                    "📅 Date fin (YYYY-MM-DD)",
                    value=datetime.now().strftime('%Y-%m-%d'),
                    key="date_to_manual_clean"
                )
            
            # Valider période manuelle
            try:
                date_from = parse_flexible_date(date_from_str)
                date_to = parse_flexible_date(date_to_str)
                if date_from > date_to:
                    st.error("❌ La date de début doit être avant la date de fin")
                    return
                if date_from < datetime(2023, 1, 1) or date_to > datetime(2025, 12, 31):
                    st.error("❌ Les dates doivent être entre 2023-01-01 et 2025-12-31")
                    return
            except ValueError as e:
                st.error(f"❌ Erreur format date: {str(e)}")
                return
        
        # Filtres
        st.subheader("🔍 Filtres")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_importance = st.select_slider(
                "Importance minimale",
                options=[1, 2, 3],
                value=2,
                format_func=lambda x: {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}[x],
                key="min_importance_cal_clean"
            )
        
        with col2:
            min_impact = st.slider(
                "Impact médian min (pips)",
                min_value=0,
                max_value=150,
                value=30,
                step=10,
                key="min_impact_cal_clean"
            )
        
        with col3:
            min_samples = st.slider(
                "Occurrences min",
                min_value=1,
                max_value=30,
                value=1,  # Réduit à 1 car la plupart des clusters n'ont qu'1 occurrence
                step=1,
                key="min_samples_cal_clean"
            )
        
        countries_cal = st.multiselect(
            "🌍 Pays",
            options=sorted(list(EURUSD_RELEVANT_COUNTRIES)),
            default=["US", "EU"],
            key="countries_cal_clean"
        )
        
        min_pips_cal = st.number_input(
            "📊 Seuil minimum (pips)",
            min_value=10.0,
            max_value=100.0,
            value=35.0,
            step=5.0,
            key="min_pips_cal_clean"
        )
        
        if not countries_cal:
            st.warning("⚠️ Sélectionnez au moins un pays")
            return
        
        # Afficher période sélectionnée
        st.info(f"📅 Période de recherche : {date_from.strftime('%Y-%m-%d')} à {date_to.strftime('%Y-%m-%d')}")
        
        # Charger cache des clusters historiques
        with st.spinner("Chargement du cache des clusters historiques..."):
            df_cache = load_cache_clusters()
        
        if df_cache is None or df_cache.empty:
            st.error("❌ Cache des clusters non disponible. Veuillez exécuter `cache_refresh.py` d'abord.")
            return
        
        st.success(f"✅ Cache chargé : {len(df_cache)} cluster(s) historique(s)")
        
        # Rechercher clusters à venir dans la période
        # 1. Chercher avec seuil strict (0.7) pour clusters validés
        with st.spinner(f"Recherche des clusters à venir dans la période {date_from.strftime('%Y-%m-%d')} à {date_to.strftime('%Y-%m-%d')}..."):
            future_clusters_validated = search_future_clusters(
                date_from,
                date_to,
                DB_PATH,
                df_cache,
                timezone_str='Europe/Zurich',
                window_minutes=30,
                min_importance=min_importance,
                countries=countries_cal if countries_cal else None,
                exclude_no_actual=True,
                min_impact=min_impact,
                min_samples=min_samples,
                min_events=min_cluster_events,
                jaccard_threshold=0.7  # Seuil strict pour clusters validés
            )
            
            # 2. Chercher aussi avec seuil plus bas (0.5) pour détecter clusters uniques
            future_clusters_unique = search_future_clusters(
                date_from,
                date_to,
                DB_PATH,
                df_cache,
                timezone_str='Europe/Zurich',
                window_minutes=30,
                min_importance=min_importance,
                countries=countries_cal if countries_cal else None,
                exclude_no_actual=True,
                min_impact=min_impact,
                min_samples=min_samples,
                min_events=min_cluster_events,
                jaccard_threshold=0.5  # Seuil bas pour détecter clusters uniques
            )
            
            # Filtrer les clusters uniques (Jaccard < 0.7)
            future_clusters_unique = [
                c for c in future_clusters_unique 
                if c.get('jaccard_similarity', 1.0) < 0.7
            ]
        
        # Afficher les clusters validés
        if future_clusters_validated:
            st.success(f"✅ {len(future_clusters_validated)} cluster(s) validé(s) trouvé(s) (Jaccard >= 0.7)")
            future_clusters = future_clusters_validated
        else:
            future_clusters = []
        
        # Afficher les clusters uniques avec avertissement
        if future_clusters_unique:
            st.warning(f"⚠️ {len(future_clusters_unique)} cluster(s) unique(s) détecté(s) (Jaccard < 0.7)")
            with st.expander("🚫 Clusters uniques - NE PAS TRADER", expanded=True):
                st.error("""
                **⚠️ ATTENTION : CLUSTERS UNIQUES DÉTECTÉS**
                
                Ces clusters n'ont **AUCUNE correspondance historique** dans le cache (similarité < 70%).
                
                **❌ NE PAS TRADER ces clusters car :**
                - Aucune donnée historique pour valider la prédiction
                - Risque élevé d'erreur de prédiction
                - Pas de pattern reconnu dans l'historique
                
                **💡 Utilisez uniquement les clusters validés (Jaccard >= 0.7) pour le trading.**
                """)
                
                # Afficher la liste des clusters uniques
                unique_info = []
                for cluster in future_clusters_unique:
                    date_str = cluster['date'].strftime('%Y-%m-%d')
                    time_str = cluster['anchor_time'].strftime('%H:%M')
                    jaccard = cluster.get('jaccard_similarity', 0.0)
                    n_events = cluster.get('n_events', 0)
                    unique_info.append({
                        'Date': date_str,
                        'Heure': time_str,
                        'Événements': n_events,
                        'Similarité': f"{jaccard*100:.1f}%",
                        'Status': '❌ UNIQUE - NE PAS TRADER'
                    })
                
                if unique_info:
                    df_unique = pd.DataFrame(unique_info)
                    st.dataframe(df_unique, use_container_width=True)
        
        if not future_clusters and not future_clusters_unique:
            st.warning("⚠️ Aucun cluster trouvé dans cette période avec les critères sélectionnés.")
            st.info("💡 **Conseil :** Réduisez les filtres (impact médian, occurrences) ou élargissez la période de recherche.")
            
            # Mode debug : afficher pourquoi aucun cluster n'est trouvé
            with st.expander("🔍 Debug : Détails de la recherche"):
                st.write("**Vérification des clusters construits pour chaque date :**")
                current_date = date_from
                debug_info = []
                while current_date <= date_to:
                    clusters_today = build_clusters_for_date(
                        current_date,
                        DB_PATH,
                        'Europe/Zurich',
                        30,
                        min_importance,
                        countries_cal if countries_cal else None,
                        True
                    )
                    if clusters_today:
                        for cluster in clusters_today:
                            debug_info.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'n_events': cluster.get('n_events', 0),
                                'signature': cluster.get('cluster_signature', '')[:80] + '...' if len(cluster.get('cluster_signature', '')) > 80 else cluster.get('cluster_signature', '')
                            })
                    current_date += timedelta(days=1)
                
                if debug_info:
                    st.write(f"**{len(debug_info)} cluster(s) construit(s) mais non trouvé(s) dans le cache :**")
                    df_debug = pd.DataFrame(debug_info)
                    st.dataframe(df_debug, use_container_width=True)
                    st.caption("💡 Ces clusters existent dans la période mais n'ont pas de correspondance dans le cache historique (Jaccard < 0.5)")
                else:
                    st.write("**Aucun cluster construit pour cette période.**")
                    st.caption("💡 Vérifiez que les événements existent dans la DB pour ces dates")
            
            return
        
        if not future_clusters:
            st.info("💡 Seuls des clusters uniques ont été trouvés. Utilisez le mode 'Saisie manuelle' pour analyser ces dates, mais **ne les tradez pas** sans validation historique.")
            return
        
        # Construire liste pour sélection
        cluster_options = []
        for cluster in future_clusters:
            date_str = cluster['date'].strftime('%Y-%m-%d')
            time_str = cluster['anchor_time'].strftime('%H:%M')
            pattern = cluster.get('dominant_pattern', 'INCONNU')
            direction = cluster.get('dominant_direction', 'UNKNOWN')
            impact = cluster.get('impact_median', 0)
            n_samples = cluster.get('n_samples', 0)
            jaccard = cluster.get('jaccard_similarity', 1.0)
            
            n_events = cluster.get('n_events', 0)
            # Ajouter indicateur de validation (tous les clusters ici sont validés car Jaccard >= 0.7)
            label = (
                f"✅ {date_str} {time_str} | {pattern} {direction} | "
                f"Impact: {impact:.0f} pips ({n_samples} occ.) | "
                f"{n_events} évts | Similarité: {jaccard*100:.0f}%"
            )
            cluster_options.append({
                'label': label,
                'cluster': cluster
            })
        
        # Sélecteur de cluster
        selected_label = st.selectbox(
            "📅 Choisir un cluster à venir",
            options=[opt['label'] for opt in cluster_options],
            key="selected_cluster_cal_clean"
        )
        
        # Extraire le cluster sélectionné
        selected_cluster = None
        for opt in cluster_options:
            if opt['label'] == selected_label:
                selected_cluster = opt['cluster']
                break
        
        if selected_cluster is None:
            return
        
        # =============================================================================
        # Extraction distribution historique des impacts du cluster
        # =============================================================================
        # Marqueur visible pour vérifier que le bloc s'exécute
        st.warning("🔍 DEBUG: entrée bloc distribution historique")
        
        # DEBUG: Inspecter les clés disponibles dans selected_cluster
        st.write(f"🔍 DEBUG selected_cluster keys: {list(selected_cluster.keys())}")
        
        df_hist = pd.DataFrame()
        
        # Chemin 1 : Si cluster_id ou signature ADN disponible
        cluster_id = selected_cluster.get("cluster_id")
        cluster_signature = selected_cluster.get("cluster_signature")
        adn_sig = selected_cluster.get("signature_adn") or selected_cluster.get("adn_signature") or selected_cluster.get("event_signature") or selected_cluster.get("signature") or cluster_signature
        
        # Log des identifiants utilisés pour debug
        st.write("🔍 DEBUG cluster_id:", cluster_id)
        st.write("🔍 DEBUG adn_sig:", adn_sig)
        st.write("🔍 DEBUG cluster_signature:", cluster_signature)
        
        if cluster_id or adn_sig:
            try:
                conn = duckdb.connect(str(DB_PATH), read_only=True)
                
                if cluster_id:
                    # Chemin 1 : Recherche par cluster_id
                    try:
                        df_hist = conn.execute("""
                            SELECT impact_pips
                            FROM clusters_occurrences
                            WHERE cluster_id = ?
                            ORDER BY date
                        """, [cluster_id]).df()
                    except Exception:
                        # Si table n'existe pas, essayer autres variantes
                        pass
                
                if df_hist.empty and adn_sig:
                    # Chemin 2 : Recherche par signature ADN / cluster_signature
                    try:
                        df_hist = conn.execute("""
                            SELECT impact_pips
                            FROM clusters_occurrences
                            WHERE signature_adn = ? OR cluster_signature = ?
                            ORDER BY date
                        """, [adn_sig, adn_sig]).df()
                    except Exception:
                        pass
                
                conn.close()
            except Exception as e:
                st.error(f"🔍 DEBUG erreur recherche cluster_id/signature: {e}")
                df_hist = pd.DataFrame()
        
        # Chemin 3 : Si pas de cluster_id/signature, inspecter les tables disponibles
        if df_hist.empty:
            try:
                conn = duckdb.connect(str(DB_PATH), read_only=True)
                tables = conn.execute("SHOW TABLES").df()
                st.write(f"🔍 DEBUG tables: {list(tables['name']) if not tables.empty else 'No tables'}")
                
                # Chercher tables candidates
                if not tables.empty:
                    candidates = [t for t in tables['name'] if 'cluster' in t.lower() or 'occurr' in t.lower()]
                    st.write(f"🔍 DEBUG candidates: {candidates}")
                    
                    # Pour chaque candidate, afficher colonnes
                    for t in candidates:
                        try:
                            cols = conn.execute(f"DESCRIBE {t}").df()
                            st.write(f"🔍 DEBUG cols {t}: {list(cols['column_name']) if not cols.empty else 'No cols'}")
                        except Exception as e:
                            st.write(f"🔍 DEBUG erreur DESCRIBE {t}: {e}")
                
                conn.close()
            except Exception as e:
                st.error(f"🔍 DEBUG erreur inspection tables: {e}")
        
        # Vérifier si df_hist est toujours vide après toutes les tentatives
        if df_hist.empty:
            st.error("🔍 DEBUG: df_hist vide après requêtes cluster_id/signature.")
        
        # Calculer et afficher quantiles si distribution disponible
        # ⚠️ IMPORTANT : Vérifier que impact_pips dans la table historique utilise la même définition
        # que "Impact détecté" (peak-to-baseline, même window). Si quantiles incohérents, vérifier formule.
        with st.container():
            if not df_hist.empty and "impact_pips" in df_hist.columns:
                dist = df_hist["impact_pips"].dropna().astype(float).values
                if len(dist) >= 5:
                    p50 = np.percentile(dist, 50)
                    p75 = np.percentile(dist, 75)
                    p90 = np.percentile(dist, 90)
                    p95 = np.percentile(dist, 95)
                    mx = np.max(dist)
                    
                    st.subheader("📊 Distribution historique des impacts du cluster")
                    st.write({
                        "n": len(dist),
                        "p50": round(p50, 1),
                        "p75": round(p75, 1),
                        "p90": round(p90, 1),
                        "p95": round(p95, 1),
                        "max": round(mx, 1),
                    })
                    
                    # Guide d'interprétation des quantiles vs prédiction
                    # Si p50 ~ 70-90 pips → prédiction 80.3 est "normale", 150.7 est rare
                    # Si p75/p90 ~ 130-160 pips → modèle sous-prédit (features manquantes ou calibration conservative)
                    # Si max ~ 160+ mais p50 ~ 60 → 150 est dans la queue, OK modèle bas mais ajouter "mode tail risk"
                else:
                    st.warning(f"⚠️ Distribution historique insuffisante (n={len(dist)} < 5)")
            else:
                st.warning("⚠️ DEBUG: aucune distribution historique trouvée pour ce cluster (df_hist vide ou colonne impact_pips absente).")
        
        # Afficher détails du cluster sélectionné
        st.header(f"📊 Cluster - {selected_cluster['date'].strftime('%Y-%m-%d')} {selected_cluster['anchor_time'].strftime('%H:%M')}")
        
        # Afficher message de validation
        jaccard = selected_cluster.get('jaccard_similarity', 1.0)
        if jaccard >= 0.7:
            st.success(f"✅ **Cluster validé** - Similarité historique: {jaccard*100:.0f}% (>= 70%) - **Sûr à trader**")
        else:
            st.error(f"❌ **Cluster unique** - Similarité historique: {jaccard*100:.0f}% (< 70%) - **NE PAS TRADER**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Impact médian historique", f"{selected_cluster.get('impact_median', 0):.1f} pips")
        with col2:
            st.metric("Occurrences", f"{selected_cluster.get('n_samples', 0)}")
        with col3:
            st.metric("Pattern attendu", selected_cluster.get('dominant_pattern', 'INCONNU'))
        with col4:
            st.metric("Direction", selected_cluster.get('dominant_direction', 'UNKNOWN'))
        
        # Afficher événements du cluster avec Previous/Estimate/Actual (éditable)
        st.subheader("📋 Événements du cluster")
        
        # Recharger les événements pour cette date pour être sûr d'avoir tous les événements
        df_events_cluster = load_events_for_date(
            selected_cluster['date'],
            DB_PATH,
            timezone_str='Europe/Zurich',
            min_importance=min_importance,
            countries=countries_cal if countries_cal else None,
            exclude_no_actual=True
        )
        
        # Filtrer les événements autour de l'heure du cluster
        # Si le cluster contient des événements US, utiliser l'heure du premier événement US
        # Sinon, utiliser l'heure du cluster
        cluster_anchor = selected_cluster['anchor_time']
        
        # Chercher les événements US dans le cluster pour déterminer l'heure principale
        df_events_us = df_events_cluster[df_events_cluster['country'] == 'US']
        if len(df_events_us) > 0:
            # Utiliser l'heure du premier événement US comme heure principale
            main_event_time = df_events_us['ts_bern'].min()
            # Fenêtre centrée sur l'heure principale : ±5 min avant, +30 min après
            window_start = main_event_time - pd.Timedelta(minutes=5)
            window_end = main_event_time + pd.Timedelta(minutes=30)
        else:
            # Pas d'événements US, utiliser l'heure du cluster
            if isinstance(cluster_anchor, datetime):
                window_start = cluster_anchor - pd.Timedelta(minutes=5)
                window_end = cluster_anchor + pd.Timedelta(minutes=30)
            else:
                if hasattr(cluster_anchor, 'time'):
                    cluster_anchor = datetime.combine(selected_cluster['date'], cluster_anchor.time())
                else:
                    cluster_anchor = datetime.combine(selected_cluster['date'], datetime.min.time().replace(hour=14, minute=30))
                window_start = cluster_anchor - pd.Timedelta(minutes=5)
                window_end = cluster_anchor + pd.Timedelta(minutes=30)
        
        df_events_cluster = df_events_cluster[
            (df_events_cluster['ts_bern'] >= window_start) &
            (df_events_cluster['ts_bern'] <= window_end)
        ].copy()
        
        if df_events_cluster.empty:
            # Fallback : utiliser les événements du cluster si le rechargement ne fonctionne pas
            df_events_cluster = selected_cluster.get('df_events', pd.DataFrame()).copy()
        
        # Debug : afficher le nombre d'événements trouvés
        st.caption(f"ℹ️ {len(df_events_cluster)} événement(s) trouvé(s) pour cette fenêtre")
        
        # Indicateur mode simulation
        is_future_date = selected_cluster['date'] > datetime.now().date()
        if is_future_date:
            st.info("🎮 **MODE SIMULATION** : Cette date est dans le futur. Vous pouvez renseigner des actuals hypothétiques pour tester la prédiction.")
        else:
            st.info("📊 **MODE ANALYSE** : Cette date est dans le passé. Renseignez les actuals réels ou testez avec des valeurs hypothétiques.")
        
        st.divider()
        
        # Créer formulaire pour actuals
        actuals_dict = {}
        for idx, row in df_events_cluster.iterrows():
            event_key = row['event_key']
            event_title = row['event_title']
            previous = row.get('previous', 'N/A')
            estimate = row.get('estimate', 'N/A')
            actual_current = row.get('actual', None)
            ts_bern = row['ts_bern']
            
            # Clé unique : date + timestamp + event_key + index
            unique_key = f"actual_{selected_cluster['date']}_{ts_bern.strftime('%H%M%S')}_{event_key}_{idx}"
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{event_title}** ({row['country']})")
                st.caption(f"⏰ {ts_bern.strftime('%H:%M')}")
            with col2:
                st.write("**Previous:**")
                st.write(str(previous) if previous is not None and not pd.isna(previous) else "N/A")
            with col3:
                st.write("**Estimate:**")
                st.write(str(estimate) if estimate is not None and not pd.isna(estimate) else "N/A")
            with col4:
                actual_input = st.text_input(
                    "**Actual:**",
                    value=str(actual_current) if actual_current is not None and not pd.isna(actual_current) else "",
                    key=unique_key,
                    help="Renseigner la valeur actual (ou laisser vide si non disponible)"
                )
                # Stocker avec event_key + timestamp pour pouvoir retrouver l'événement
                actuals_dict[(event_key, ts_bern)] = actual_input
            
            st.divider()
        
        # Bouton pour calculer la prédiction
        if st.button("🔮 Calculer la prédiction", type="primary"):
            # Mettre à jour actuals dans df_events
            for (event_key, ts_bern), actual_str in actuals_dict.items():
                if actual_str and actual_str.strip():
                    try:
                        # Essayer de convertir en float
                        actual_value = float(actual_str)
                        # Trouver la ligne correspondante par event_key ET timestamp
                        mask = (df_events_cluster['event_key'] == event_key) & (df_events_cluster['ts_bern'] == ts_bern)
                        df_events_cluster.loc[mask, 'actual'] = actual_value
                    except ValueError:
                        pass
            
            # Enrichir avec surprises
            df_events_enriched = enrich_events_with_surprises(df_events_cluster)
            
            # Afficher les événements enrichis
            st.subheader("📋 Événements enrichis")
            with st.expander("📊 Détails des événements enrichis"):
                # Sélectionner les colonnes à afficher
                columns_to_show = [
                    'ts_bern', 'country', 'event_title',
                    'previous', 'estimate', 'actual',
                    'empirical_score', 'surprise_pct', 'score_adjusted'
                ]
                
                # Filtrer pour ne garder que les colonnes qui existent
                available_columns = [col for col in columns_to_show if col in df_events_enriched.columns]
                
                # Créer une copie pour le formatage
                df_display = df_events_enriched[available_columns].copy()
                
                # Formater les colonnes numériques pour meilleure lisibilité
                numeric_cols = ['previous', 'estimate', 'actual', 'empirical_score', 'surprise_pct', 'score_adjusted']
                for col in numeric_cols:
                    if col in df_display.columns:
                        # Formater avec 2 décimales si ce sont des valeurs numériques
                        df_display[col] = df_display[col].apply(
                            lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else str(x) if pd.notna(x) else "N/A"
                        )
                
                # Formater ts_bern pour affichage
                if 'ts_bern' in df_display.columns:
                    df_display['ts_bern'] = df_display['ts_bern'].apply(
                        lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else "N/A"
                    )
                
                st.dataframe(df_display, use_container_width=True)
            
            # Charger prix pour cette date
            target_date = datetime.combine(selected_cluster['date'], datetime.min.time())
            df_prices = load_prices_for_date(target_date, DB_PATH, 'Europe/Zurich')
            
            if df_prices.empty:
                st.warning("⚠️ Aucun prix trouvé pour cette date")
                return
            
            tz = pytz.timezone('Europe/Zurich')
            
            # Détection Pattern
            st.subheader("🎯 Détection Pattern")
            
            # =============================================================================
            # 1) Calculer cluster_ts (ancre) en TZ locale cohérente (df_prices est déjà local)
            # =============================================================================
            cluster_ts = pd.Timestamp(selected_cluster["date"])
            
            if "anchor_ts" in selected_cluster and pd.notna(selected_cluster["anchor_ts"]):
                cluster_ts = pd.Timestamp(selected_cluster["anchor_ts"])
            
            if cluster_ts.tzinfo is None:
                cluster_ts = cluster_ts.tz_localize(tz)
            else:
                cluster_ts = cluster_ts.tz_convert(tz)
            
            st.caption(
                f"DEBUG cluster_ts local={cluster_ts.strftime('%Y-%m-%d %H:%M %Z')}"
            )
            
            # Utiliser l'heure d'ancrage du cluster pour prioriser le mouvement autour de cette heure
            cluster_anchor_time = None
            if 'anchor_time' in selected_cluster:
                cluster_anchor_time = selected_cluster['anchor_time']
                if isinstance(cluster_anchor_time, datetime):
                    # Si c'est déjà un datetime, l'utiliser directement
                    pass
                elif hasattr(cluster_anchor_time, 'time'):
                    # Si c'est un time object, le combiner avec la date du cluster
                    cluster_anchor_time = datetime.combine(selected_cluster['date'], cluster_anchor_time.time())
                else:
                    cluster_anchor_time = None
                
                if cluster_anchor_time:
                    st.info(f"📌 Recherche de mouvement autour de {cluster_anchor_time.strftime('%H:%M')} (cluster sélectionné)")
            
            pattern_result = detect_pattern_type(
                df_prices,
                df_events_enriched,
                min_pips_cal,
                tz,
                cluster_anchor_time=cluster_anchor_time,  # Passer l'heure du cluster pour prioriser
                silent_warning=True  # ✅ Silencer le warning interne (on affiche le nôtre après re-sélection)
            )
            
            # =============================================================================
            # FIX: Re-sélectionner le mouvement "principal" le plus proche du cluster
            # =============================================================================
            cluster_ts_local = cluster_ts
            
            best_movement = None
            best_delta = 999999
            
            movements = pattern_result.get("movements", None)
            
            if movements and isinstance(movements, (list, tuple)):
                for mv in movements:
                    if not mv or "start_time" not in mv:
                        continue
                    mst_cand = pd.Timestamp(mv["start_time"])
                    if mst_cand.tzinfo is None:
                        mst_cand = mst_cand.tz_localize(tz)
                    else:
                        mst_cand = mst_cand.tz_convert(tz)
                    
                    delta_min_cand = abs((cluster_ts_local - mst_cand).total_seconds()) / 60.0
                    if delta_min_cand < best_delta:
                        best_delta = delta_min_cand
                        best_movement = mv
                
                if best_movement is not None:
                    pattern_result["movement"] = best_movement
            
            else:
                try:
                    all_movements = scan_price_movements(df_prices, min_pips_cal)
                    if all_movements:
                        for mv in all_movements:
                            if not mv or "start_time" not in mv:
                                continue
                            mst_cand = pd.Timestamp(mv["start_time"])
                            if mst_cand.tzinfo is None:
                                mst_cand = mst_cand.tz_localize(tz)
                            else:
                                mst_cand = mst_cand.tz_convert(tz)
                            
                            delta_min_cand = abs((cluster_ts_local - mst_cand).total_seconds()) / 60.0
                            if delta_min_cand < best_delta:
                                best_delta = delta_min_cand
                                best_movement = mv
                        
                        if best_movement is not None:
                            pattern_result["movement"] = best_movement
                except Exception as e:
                    st.caption(f"DEBUG fallback scan échoué: {e}")
            
            # DEBUG temporaire
            if pattern_result.get("movement"):
                mst_debug = pd.Timestamp(pattern_result["movement"]["start_time"])
                if mst_debug.tzinfo is None:
                    mst_debug = mst_debug.tz_localize(tz)
                else:
                    mst_debug = mst_debug.tz_convert(tz)
                st.caption(f"DEBUG movement choisi={mst_debug.strftime('%H:%M')}")
            
            # Maintenant seulement on fixe le type
            pattern_type = pattern_result["pattern_type"]
            
            # =============================================================================
            # 2) Filtrer le mouvement détecté : accepté seulement si proche (LOCAL)
            # =============================================================================
            movement_start_time = None
            movement_is_valid = False
            delta_min = None
            mst = None
            
            if pattern_result.get("movement"):
                mst = pd.Timestamp(pattern_result["movement"].get("start_time"))
                
                if mst.tzinfo is None:
                    mst = mst.tz_localize(tz)
                else:
                    mst = mst.tz_convert(tz)
                
                delta_min = abs((cluster_ts - mst).total_seconds()) / 60.0
                
                if delta_min <= 15:
                    movement_start_time = mst
                    movement_is_valid = True
            
            # =============================================================================
            # 3) Warning seulement si mouvement trop loin
            # =============================================================================
            if pattern_result.get("movement") and not movement_is_valid and mst is not None:
                st.warning(
                    f"⚠️ Attention : Le mouvement détecté commence à {mst.strftime('%H:%M')}, "
                    f"alors que le cluster est à {cluster_ts.strftime('%H:%M')} "
                    f"(écart de {delta_min:.0f} minutes). "
                    f"Vérifiez que c'est bien le bon mouvement ou réduisez le seuil min_pips."
                )
            
            # Prédiction selon pattern
            st.subheader("🔮 Prédiction")
            
            # ⭐ V8 Option : Utiliser moteur V8 si disponible et activé
            use_v8_engine = False
            if V8_AVAILABLE:
                use_v8_engine = st.checkbox(
                    "🔬 Utiliser moteur V8 (backtesté)",
                    value=False,
                    help="Active les prédictions V8 backtestées (58.8% direction accuracy, 95.9% hit rate)"
                )
            
            # Si V8 activé, utiliser adaptateur V8
            if use_v8_engine and V8_AVAILABLE:
                try:
                    # Préparer events pour V8
                    events_v8 = df_events_enriched.copy()
                    
                    # S'assurer que les colonnes requises sont présentes
                    required_v8_cols = ['event_key', 'actual', 'estimate', 'country']
                    missing_v8_cols = [col for col in required_v8_cols if col not in events_v8.columns]
                    if missing_v8_cols:
                        st.error(f"❌ Colonnes manquantes pour V8: {', '.join(missing_v8_cols)}")
                        use_v8_engine = False
                    else:
                        # Filtrer events avec actuals renseignés
                        events_v8 = events_v8[
                            events_v8['actual'].notna() & 
                            events_v8['estimate'].notna()
                        ].copy()
                        
                        if events_v8.empty:
                            st.warning("⚠️ Aucun event avec actual/estimate pour V8. Utilisation méthode standard.")
                            use_v8_engine = False
                        else:
                            # ⭐ movement_start_time est déjà validé (proximité <= 15 min)
                            # Si mouvement trop loin, movement_start_time = None (pas de pollution V8)
                            
                            # Frontière V8 : convertir en UTC pour l'adaptateur
                            movement_start_time_v8 = None
                            if movement_start_time is not None:
                                movement_start_time_v8 = movement_start_time.tz_convert("UTC")
                            
                            # Appeler adaptateur V8
                            v8_pred = predict_cluster_v8(
                                date=pd.Timestamp(selected_cluster['date']),
                                events_df=events_v8,
                                db_path=DB_PATH,
                                conn=None,  # Pas besoin de conn pour pattern detection ici
                                movement_start_time=movement_start_time_v8,  # ✅ Maintenant filtré (None si trop loin)
                                trigger_z=1.0,
                                theta=0.05
                            )
                            
                            if v8_pred.get('success'):
                                # Afficher résultats V8
                                st.success("✅ Prédiction V8 calculée")
                                
                                # Afficher warnings SAFE si présents
                                if v8_pred.get('warnings'):
                                    for warning in v8_pred['warnings']:
                                        st.warning(warning)
                                
                                # Créer prediction_result au format attendu par l'UI
                                prediction_result = {
                                    'prediction_pips': v8_pred['impact_pips'],
                                    'direction': v8_pred['direction'],
                                    'pattern_type': v8_pred['pattern_type'],
                                    'status': 'predicted',
                                    'method': 'v8',
                                    'trigger_strength': v8_pred['trigger_strength'],
                                    'cluster_type': v8_pred['cluster_type']
                                }
                                
                                # Ajouter legs si multi-wave
                                if v8_pred.get('leg1') and v8_pred.get('leg2'):
                                    prediction_result['phase1_pips'] = v8_pred['leg1']['amp_pips']
                                    prediction_result['pullback_pips'] = 0.0  # V8 ne calcule pas pullback directement
                                    prediction_result['phase2_pips'] = v8_pred['leg2']['amp_pips']
                                    prediction_result['leg1_direction'] = v8_pred['leg1']['direction']
                                    prediction_result['leg2_direction'] = v8_pred['leg2']['direction']
                                    prediction_result['leg1_t_peak'] = v8_pred['leg1']['t_peak_min']
                                    prediction_result['leg2_t_peak'] = v8_pred['leg2']['t_peak_min']
                                
                                # Afficher métriques V8
                                col_v8_1, col_v8_2, col_v8_3 = st.columns(3)
                                with col_v8_1:
                                    st.metric("Direction V8", v8_pred['direction'])
                                    st.metric("Impact V8", f"{v8_pred['impact_pips']:.1f} pips")
                                with col_v8_2:
                                    st.metric("Pattern V8", v8_pred['pattern_type'] or "N/A")
                                    st.metric("Trigger strength", f"{v8_pred['trigger_strength']:.2f}")
                                with col_v8_3:
                                    st.metric("Cluster type", v8_pred['cluster_type'] or "N/A")
                                    st.metric("Direction score", f"{v8_pred['direction_score']:.2f}")
                                
                                # =============================================================================
                                # 🧷 ADD-ON STRADDLE / EXIT MANAGER (post-actuals)
                                # =============================================================================
                                st.divider()
                                st.markdown("## 🧷 Gestion Straddle (pré-event)")
                                
                                use_straddle = st.checkbox(
                                    "Activer gestion Straddle (BUY + SELL ouverts pré-event)",
                                    value=True,
                                    help="Si activé, l'UI recommande quelle jambe couper après prédiction et quand sortir la jambe gagnante."
                                )
                                
                                if use_straddle:
                                    direction_v8 = v8_pred.get("direction", "UNKNOWN")
                                    pattern_v8 = v8_pred.get("pattern_type")
                                    
                                    st.markdown("### ✅ Action immédiate post-prédiction")
                                    
                                    if direction_v8 == "UP":
                                        st.info("Fermer la jambe **SELL** maintenant. Conserver la jambe **BUY**.")
                                    elif direction_v8 == "DOWN":
                                        st.info("Fermer la jambe **BUY** maintenant. Conserver la jambe **SELL**.")
                                    else:
                                        st.warning("Direction inconnue → conserver neutre / pas de recommandation straddle.")
                                    
                                    st.markdown("### 🎯 Plan de sortie (position gagnante)")
                                    
                                    # SAFE : si warnings missing stats -> mode conservateur
                                    safe_conservative = any("events core sans stats" in w for w in v8_pred.get("warnings", []))
                                    
                                    leg1 = v8_pred.get("leg1")
                                    leg2 = v8_pred.get("leg2")
                                    
                                    if pattern_v8 == "single_wave" or (pattern_v8 is None and leg2 is None):
                                        t_exit = leg1.get("t_peak_min") if leg1 else None
                                        tp_pips = float(v8_pred.get("impact_pips", 0.0))
                                        
                                        if t_exit is not None:
                                            st.success(f"Sortie recommandée au **pic estimé** (~{t_exit:.0f} min). TP ≈ **{tp_pips:.1f} pips**.")
                                        else:
                                            st.success(f"TP ≈ **{tp_pips:.1f} pips** (timing pic non disponible).")
                                    
                                    elif pattern_v8 == "double_wave" and leg1 and leg2:
                                        if safe_conservative:
                                            mode = "Conservateur (pic1)"
                                        else:
                                            mode = st.radio("Mode sortie", ["Conservateur (pic1)", "Optimal (pic2)"], index=1)
                                        
                                        if mode.startswith("Conservateur"):
                                            t_exit = float(leg1.get("t_peak_min", 0.0))
                                            tp_pips = float(leg1.get("amp_pips", 0.0))
                                            st.success(f"Sortie conservatrice au **pic1** (~{t_exit:.0f} min). TP ≈ **{tp_pips:.1f} pips**.")
                                        else:
                                            t_exit = float(leg2.get("t_peak_min", 0.0))
                                            tp_pips = float(leg1.get("amp_pips", 0.0)) + float(leg2.get("amp_pips", 0.0))
                                            st.success(f"Sortie optimale au **pic2** (~{t_exit:.0f} min). TP ≈ **{tp_pips:.1f} pips**.")
                                    
                                    elif pattern_v8 == "zig_zag" and leg1 and leg2:
                                        leg1_amp = float(leg1.get("amp_pips", 0.0))
                                        leg2_amp = float(leg2.get("amp_pips", 0.0))
                                        
                                        if leg2_amp > leg1_amp and not safe_conservative:
                                            t_exit = float(leg2.get("t_peak_min", 0.0))
                                            tp_pips = leg1_amp + leg2_amp
                                            st.success(f"Sortie recommandée au **pic2** (~{t_exit:.0f} min). TP ≈ **{tp_pips:.1f} pips**.")
                                        else:
                                            t_exit = float(leg1.get("t_peak_min", 0.0))
                                            tp_pips = leg1_amp
                                            st.success(f"Sortie recommandée au **pic1** (~{t_exit:.0f} min). TP ≈ **{tp_pips:.1f} pips**.")
                                    
                                    else:
                                        st.warning("Pattern non exploitable → pas de recommandation de sortie automatique.")
                                
                                # Continuer avec l'affichage standard (baseline_price, timeline, etc.)
                                # On skip le calcul standard et on utilise prediction_result V8
                                pattern_type = v8_pred['pattern_type'] or pattern_type
                                
                            elif v8_pred.get('skipped'):
                                st.warning(f"⚠️ Prédiction V8 non disponible: {v8_pred.get('skip_reason', 'Unknown')}")
                                use_v8_engine = False
                            else:
                                st.error(f"❌ Erreur prédiction V8: {v8_pred.get('error', 'Unknown')}")
                                use_v8_engine = False
                                
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'appel V8: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    use_v8_engine = False
            
            # Calcul standard si V8 non activé ou échec
            if not use_v8_engine:
                if pattern_type == 'DOUBLE_WAVE':
                    # Obtenir baseline_price et direction
                    baseline_price_sr = None
                    direction_sr = 'UP'
                    if 'movement' in pattern_result and pattern_result['movement']:
                        baseline_price_sr = pattern_result['movement'].get('baseline_price')
                        direction_sr = pattern_result['movement'].get('direction', 'UP')
                    elif not df_prices.empty:
                        first_price_row = df_prices.iloc[0]
                        baseline_price_sr = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    prediction_result = predict_double_wave_base(
                        df_events_enriched,
                        baseline_price=baseline_price_sr,
                        direction=direction_sr,
                        use_support_resistance=True,
                        use_aggregate_indicators=True
                    )
                elif pattern_type in ['SINGLE_WAVE_FORT', 'SINGLE_WAVE_STANDARD']:
                    # Extraire movement_datetime, baseline_price et direction si disponibles
                    movement_datetime = None
                    baseline_price_sr = None
                    direction_sr = 'UP'
                    if movement_is_valid and movement_start_time is not None:
                        movement_datetime = movement_start_time
                        if 'movement' in pattern_result and pattern_result['movement']:
                            baseline_price_sr = pattern_result['movement'].get('baseline_price')
                            direction_sr = pattern_result['movement'].get('direction', 'UP')
                    elif 'movement' in pattern_result and pattern_result['movement']:
                        movement_datetime = pd.Timestamp(pattern_result['movement']['start_time'])
                        baseline_price_sr = pattern_result['movement'].get('baseline_price')
                        direction_sr = pattern_result['movement'].get('direction', 'UP')
                    elif not df_prices.empty:
                        first_price_row = df_prices.iloc[0]
                        baseline_price_sr = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    prediction_result = predict_single_wave_base(
                        df_events_enriched,
                        df_prices,
                        pattern_type,
                        movement_datetime=movement_datetime,
                        baseline_price=baseline_price_sr,
                        direction=direction_sr,
                        use_support_resistance=True,
                        use_aggregate_indicators=True
                    )
                else:
                    st.warning("⚠️ Pattern non reconnu pour prédiction")
                    return
            
            if prediction_result.get('status') == 'predicted':
                is_future_date = selected_cluster['date'] > datetime.now().date()
                mode_label = "🎮 SIMULATION" if is_future_date else "📊 PRÉDICTION"
                st.success(f"✅ {mode_label} calculée (formules validées + amplification prédite)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Impact prédit", f"{prediction_result.get('prediction_pips', 0):.1f} pips")
                with col2:
                    st.metric("Impact médian historique", f"{selected_cluster.get('impact_median', 0):.1f} pips")
                with col3:
                    amplification_pred = prediction_result.get('amplification_predicted', prediction_result.get('amplification', 0))
                    amplification_method = prediction_result.get('amplification_method', 'unknown')
                    method_label = "Modèle 'APRÈS'" if amplification_method == 'with_actuals' else "Modèle 'AVANT'"
                    st.metric("Amplification prédite", f"{amplification_pred:.2f}x", help=f"{method_label} (R² = 0.68)")
                
                if pattern_type == 'DOUBLE_WAVE':
                    # Calculer les prix et heures correspondants
                    baseline_price = None
                    baseline_time = None
                    direction = 'UP'
                    
                    # Obtenir baseline_price, baseline_time et direction
                    # PRIORITÉ : Utiliser l'heure du mouvement validé (proximité <= 15 min)
                    if movement_is_valid and movement_start_time is not None:
                        # Utiliser le mouvement validé
                        baseline_time = movement_start_time
                        if 'movement' in pattern_result and pattern_result['movement']:
                            baseline_price = pattern_result['movement'].get('baseline_price')
                            direction = pattern_result['movement'].get('direction', 'UP')
                    elif 'movement' in pattern_result and pattern_result['movement']:
                        # Fallback : utiliser mouvement même si non validé (pour affichage)
                        baseline_price = pattern_result['movement'].get('baseline_price')
                        baseline_time_raw = pattern_result['movement'].get('start_time')
                        direction = pattern_result['movement'].get('direction', 'UP')
                        
                        # S'assurer que baseline_time est bien un datetime en timezone locale
                        if baseline_time_raw is not None:
                            if isinstance(baseline_time_raw, str):
                                baseline_time = pd.Timestamp(baseline_time_raw)
                            elif isinstance(baseline_time_raw, (pd.Timestamp, datetime)):
                                baseline_time = pd.Timestamp(baseline_time_raw)
                            else:
                                baseline_time = None
                            
                            # Normaliser timezone locale
                            if baseline_time is not None:
                                if baseline_time.tzinfo is None:
                                    baseline_time = baseline_time.tz_localize(tz)
                                else:
                                    baseline_time = baseline_time.tz_convert(tz)
                        else:
                            baseline_time = None
                    elif 'metrics' in pattern_result:
                        direction = pattern_result['metrics'].get('direction', 'UP')
                    
                    # Si baseline_time n'est toujours pas disponible, utiliser l'heure du premier événement
                    # (mais ce n'est qu'un fallback, l'heure du mouvement détecté est préférée)
                    if baseline_time is None and not df_events_enriched.empty:
                        baseline_time = df_events_enriched['ts_bern'].min()
                        st.info("ℹ️ Utilisation de l'heure du premier événement comme baseline (mouvement non détecté)")
                    
                    # Si baseline_price n'est pas disponible, essayer de l'extraire du premier prix
                    if baseline_price is None and not df_prices.empty:
                        # Utiliser le premier prix disponible comme baseline
                        first_price_row = df_prices.iloc[0]
                        baseline_price = (first_price_row['open'] + first_price_row['close']) / 2
                    
                    if baseline_price is not None and baseline_time is not None:
                        phase1_pips = prediction_result.get('phase1_pips', 0)
                        pullback_pips = prediction_result.get('pullback_pips', 0)
                        phase2_pips = prediction_result.get('phase2_pips', 0)
                        prediction_pips = prediction_result.get('prediction_pips', 0)
                        
                        # Calculer les prix selon la direction
                        if direction == 'UP':
                            baseline = baseline_price
                            pic1 = baseline + phase1_pips / 10000
                            pullback = pic1 - pullback_pips / 10000
                            pic2 = baseline + phase2_pips / 10000
                            stabilisation = pic2  # Stabilisation au pic 2
                        else:  # DOWN
                            baseline = baseline_price
                            pic1 = baseline - phase1_pips / 10000
                            pullback = pic1 + pullback_pips / 10000
                            pic2 = baseline - phase2_pips / 10000
                            stabilisation = pic2  # Stabilisation au pic 2
                        
                        # Utiliser les heures réelles détectées depuis les prix (si disponibles)
                        from datetime import timedelta
                        baseline_dt = pd.Timestamp(baseline_time) if isinstance(baseline_time, (str, pd.Timestamp)) else baseline_time
                        if baseline_dt.tz is None:
                            baseline_dt = baseline_dt.tz_localize('Europe/Zurich')
                        else:
                            # S'assurer que c'est en timezone de Berne
                            baseline_dt = baseline_dt.tz_convert('Europe/Zurich')
                        
                        # Afficher l'heure de baseline utilisée (pour debug)
                        st.caption(f"📍 Baseline détectée : {baseline_dt.strftime('%H:%M')} (début du mouvement depuis les prix)")
                        
                        # Essayer d'utiliser les heures réelles détectées
                        pic1_time = baseline_dt
                        pullback_time = baseline_dt
                        pic2_time = baseline_dt
                        stabilisation_time = baseline_dt
                        
                        if 'wave1_peak' in pattern_result:
                            pic1_time = pd.Timestamp(pattern_result['wave1_peak'])
                            if pic1_time.tz is None:
                                pic1_time = pic1_time.tz_localize('Europe/Zurich')
                        
                        if 'pullback_low' in pattern_result:
                            pullback_time = pd.Timestamp(pattern_result['pullback_low'])
                            if pullback_time.tz is None:
                                pullback_time = pullback_time.tz_localize('Europe/Zurich')
                        
                        if 'wave2_peak' in pattern_result:
                            pic2_time = pd.Timestamp(pattern_result['wave2_peak'])
                            if pic2_time.tz is None:
                                pic2_time = pic2_time.tz_localize('Europe/Zurich')
                            # Stabilisation = pic2 + 25 minutes (timing théorique pour stabilisation)
                            stabilisation_time = pic2_time + timedelta(minutes=25)
                        else:
                            # Fallback : timings théoriques si pas de détection
                            pic1_time = baseline_dt + timedelta(minutes=5)   # T+5
                            pullback_time = baseline_dt + timedelta(minutes=11)  # T+11
                            pic2_time = baseline_dt + timedelta(minutes=15)  # T+15
                            stabilisation_time = baseline_dt + timedelta(minutes=40)  # T+40
                        
                        # Calculer les délais réels depuis baseline
                        pic1_delay = int((pic1_time - baseline_dt).total_seconds() / 60)
                        pullback_delay = int((pullback_time - baseline_dt).total_seconds() / 60)
                        pic2_delay = int((pic2_time - baseline_dt).total_seconds() / 60)
                        stabilisation_delay = int((stabilisation_time - baseline_dt).total_seconds() / 60)
                        
                        # Afficher les phases avec prix et heures
                        st.subheader("🌊 Détails du mouvement Double Wave")
                        col_phases = st.columns(5)
                        
                        with col_phases[0]:
                            st.metric(
                                "Baseline",
                                f"{baseline:.5f}",
                                help=f"Prix de départ - {baseline_dt.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {baseline_dt.strftime('%H:%M')}")
                        with col_phases[1]:
                            st.metric(
                                "Pic 1",
                                f"{pic1:.5f}",
                                delta=f"+{phase1_pips:.1f} pips" if direction == 'UP' else f"-{phase1_pips:.1f} pips",
                                help=f"Premier pic (Phase 1) - {pic1_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pic1_time.strftime('%H:%M')} (T+{pic1_delay})")
                        with col_phases[2]:
                            st.metric(
                                "Pullback",
                                f"{pullback:.5f}",
                                delta=f"-{pullback_pips:.1f} pips" if direction == 'UP' else f"+{pullback_pips:.1f} pips",
                                help=f"Point de pullback - {pullback_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pullback_time.strftime('%H:%M')} (T+{pullback_delay})")
                        with col_phases[3]:
                            st.metric(
                                "Pic 2",
                                f"{pic2:.5f}",
                                delta=f"+{phase2_pips:.1f} pips" if direction == 'UP' else f"-{phase2_pips:.1f} pips",
                                help=f"Deuxième pic (Phase 2) - {pic2_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {pic2_time.strftime('%H:%M')} (T+{pic2_delay})")
                        with col_phases[4]:
                            st.metric(
                                "Stabilisation",
                                f"{stabilisation:.5f}",
                                delta=f"+{prediction_pips:.1f} pips" if direction == 'UP' else f"-{prediction_pips:.1f} pips",
                                help=f"Point de stabilisation - {stabilisation_time.strftime('%H:%M')}"
                            )
                            st.caption(f"🕐 {stabilisation_time.strftime('%H:%M')} (T+{stabilisation_delay})")
                    else:
                        # Fallback si baseline_price non disponible
                        col_phases = st.columns(3)
                        with col_phases[0]:
                            st.metric(
                                "Phase 1",
                                f"{prediction_result.get('phase1_pips', 0):.1f} pips"
                            )
                        with col_phases[1]:
                            st.metric(
                                "Pullback",
                                f"{prediction_result.get('pullback_pips', 0):.1f} pips"
                            )
                        with col_phases[2]:
                            st.metric(
                                "Phase 2",
                                f"{prediction_result.get('phase2_pips', 0):.1f} pips"
                            )
                        st.caption("⚠️ Prix non disponibles (baseline_price introuvable)")
                
                if 'amplification' in prediction_result or 'reason' in prediction_result:
                    amplification_base = prediction_result.get('amplification_base', prediction_result.get('amplification', 0))
                    amplification_pred = prediction_result.get('amplification_predicted', amplification_base)
                    amplification_method = prediction_result.get('amplification_method', 'unknown')
                    
                    if amplification_method == 'with_actuals':
                        method_info = "Modèle 'APRÈS' (R²=0.68, plus précis avec actuals)"
                    else:
                        method_info = "Modèle 'AVANT' (R²=0.51, sans actuals)"
                    
                    st.caption(
                        f"{prediction_result.get('reason', '')} | "
                        f"Amplification base: {amplification_base:.2f}x, "
                        f"Amplification prédite: {amplification_pred:.2f}x ({method_info}) | "
                        f"Surprise max: {prediction_result.get('surprise_max', 0):.1f}%"
                    )
            else:
                st.warning(f"⚠️ {prediction_result.get('reason', 'Prédiction non disponible')}")


if __name__ == "__main__":
    main()

