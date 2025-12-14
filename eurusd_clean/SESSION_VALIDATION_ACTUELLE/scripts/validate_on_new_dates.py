#!/usr/bin/env python3
"""
Validation sur Nouvelles Dates - Conditions Réelles

Objectif :
1. Identifier dates récentes non utilisées pour entraînement
2. Tester pipeline complet avec formule linéaire
3. Comparer prédictions avec impacts réels
4. Générer rapport de validation

Date : 2025-12-07
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import math
import duckdb
from typing import Dict, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

from src.core.cluster_impact_calculator import calculate_cluster_impact
from src.core.impact_measurement import measure_impact_from_dukascopy
from src.core.trend_detection_pre_event_s107 import detect_trend_by_inversion_s107  # ⭐ Détection tendance pré-événement
from src.core.formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_linear,
    calculate_impact_d,
    get_event_direction  # ⭐ Pour prédire la direction (fallback)
)

# ════════════════════════════════════════════════════════════════
# FONCTIONS PATCH : Direction empirique V2/V3 (alpha · surprise_z)
# ════════════════════════════════════════════════════════════════

# Chemins des fichiers de calibration
ALPHA_WEIGHTS_FILE = Path(__file__).parent.parent / 'outputs' / 'alpha_weights.csv'
EVENTS_FILE = Path(__file__).parent.parent / 'outputs' / 'events.csv'
DIRECTION_THRESHOLDS_FILE = Path(__file__).parent.parent / 'outputs' / 'direction_thresholds.json'
AMPLITUDE_CALIBRATION_FILE = Path(__file__).parent.parent / 'outputs' / 'amplitude_calibration.json'

def load_alpha_map(alpha_csv_path=None, horizon='1h'):
    """
    Charge les poids alpha appris walk-forward.
    Format attendu: colonnes [horizon, event_key, weight, intercept]
    Retourne dict {event_key: weight} pour l'horizon spécifié.
    """
    if alpha_csv_path is None:
        alpha_csv_path = ALPHA_WEIGHTS_FILE
    
    try:
        df = pd.read_csv(alpha_csv_path)
        # Filtrer par horizon
        df_horizon = df[df['horizon'] == horizon].copy()
        if len(df_horizon) == 0:
            return {}
        
        # Créer mapping event_key -> weight
        alpha_map = {}
        for _, row in df_horizon.iterrows():
            event_key = str(row['event_key']).strip()
            weight = float(row['weight'])
            alpha_map[event_key] = weight
        
        return alpha_map
    except (FileNotFoundError, KeyError, ValueError) as e:
        return {}


def load_surprise_stats(events_csv_path=None):
    """
    Calcule (mu, sigma) des surprises (actual-estimate) par event_key.
    Utilisé pour standardiser en z-score.
    """
    if events_csv_path is None:
        events_csv_path = EVENTS_FILE
    
    try:
        ev = pd.read_csv(events_csv_path)
    except FileNotFoundError:
        return {}
    
    # Colonnes attendues
    if "event_key" not in ev.columns or "actual" not in ev.columns or "estimate" not in ev.columns:
        return {}
    
    ev["event_key"] = (
        ev["event_key"].astype(str).str.strip().str.lower()
        .str.replace(r"\s+", " ", regex=True).str.replace("-", " ")
    )
    ev["actual"] = pd.to_numeric(ev["actual"], errors="coerce")
    ev["estimate"] = pd.to_numeric(ev["estimate"], errors="coerce")
    
    ev = ev.dropna(subset=["actual", "estimate"])
    ev["surprise"] = ev["actual"] - ev["estimate"]
    
    stats = {}
    g = ev.groupby("event_key")["surprise"]
    mu = g.mean()
    sigma = g.std(ddof=0)
    for k in mu.index:
        s = float(sigma.loc[k])
        if s == 0 or np.isnan(s):
            continue
        stats[k] = (float(mu.loc[k]), s)
    return stats


def predict_direction_empirical(events_df, alpha_map, stats_map, theta=0.0):
    """
    Direction finale basée sur:
        S = sum(alpha_e * z_e)
    où z_e est surprise standardisée par event_key,
    et alpha_e est appris sur events V2: family_surp_pos/neg
    
    Retour: (direction, score_S, method)
        direction in {"UP","DOWN","UNKNOWN"}
    """
    S_raw = 0.0
    contributions = []  # Stocker les contributions pour calculer n_active
    
    for _, row in events_df.iterrows():
        actual = row.get("actual")
        estimate = row.get("estimate")
        family = str(row.get("family", "Other")).strip()
        event_key = str(row.get("event_key", "")).strip().lower()
        
        # Pas d'actual -> pas de direction finale possible
        if pd.isna(actual):
            continue
        
        # Estimate obligatoire en V2/V3 (sinon NO_SIGNAL)
        if pd.isna(estimate):
            continue
        
        actual = float(actual)
        estimate = float(estimate)
        surprise = actual - estimate
        
        mu_sigma = stats_map.get(event_key)
        if mu_sigma is None:
            continue
        mu, sigma = mu_sigma
        if sigma == 0:
            continue
        
        z = (surprise - mu) / sigma
        sign = "pos" if z > 0 else "neg"
        
        alpha_key = f"{family}_surp_{sign}"
        alpha = float(alpha_map.get(alpha_key, 0.0))
        
        contribution = alpha * z
        S_raw += contribution
        contributions.append(contribution)
    
    if len(contributions) == 0:
        return "UNKNOWN", 0.0, "no_signal"
    
    # --- F2: Normaliser S par √n_active (normalisation plus douce) ---
    # n_active = nombre d'alphas avec contribution non-nulle
    n_active = sum(1 for c in contributions if abs(c) > 1e-10)
    
    # F2: normalisation par racine carrée (moins agressive que division par n_active)
    S = S_raw / math.sqrt(max(1, n_active))
    
    # Convention USD -> EURUSD :
    # S>0 = USD up = EURUSD DOWN
    # S<0 = USD down = EURUSD UP
    if S > theta:
        return "DOWN", S, "alpha_surprise"
    elif S < -theta:
        return "UP", S, "alpha_surprise"
    else:
        return "UNKNOWN", S, "alpha_neutral"


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent.parent.parent.parent / 'fx_impact_app' / 'data' / 'warehouse.duckdb'
TRAINING_DB = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.csv'

# Dates à tester (None = automatique : dates récentes non dans entraînement)
TEST_DATES = None  # Sera déterminé automatiquement
MAX_TEST_DATES = 50  # Limiter nombre de dates pour test rapide

# Option : Charger dates avec mouvements significatifs depuis fichier
LOAD_STRONG_MOVEMENTS_DATES = True
STRONG_MOVEMENTS_FILE = Path(__file__).parent.parent / 'outputs' / 'dates_with_strong_movements.csv'


# ════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ════════════════════════════════════════════════════════════════

def load_training_dates() -> set:
    """Charge les dates utilisées pour entraînement"""
    if not TRAINING_DB.exists():
        return set()
    
    df = pd.read_csv(TRAINING_DB)
    return set(df['date'].unique())


def find_new_dates(max_dates: int = 20) -> List[str]:
    """
    Trouve des dates récentes non utilisées pour entraînement
    """
    training_dates = load_training_dates()
    
    if not DB_PATH.exists():
        print(f"⚠️  Base de données introuvable : {DB_PATH}")
        return []
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Vérifier plage de dates avec prix disponibles (utiliser prices_1m_v - la plus complète)
        price_range = conn.execute("SELECT MIN(ts_utc) as min_date, MAX(ts_utc) as max_date FROM prices_1m_v").df()
        max_price_date = price_range.iloc[0]['max_date']
        min_price_date = price_range.iloc[0]['min_date']
        
        # Convertir en string pour requête
        max_price_date_str = str(max_price_date).split()[0] if max_price_date else '2025-10-20'
        min_price_date_str = str(min_price_date).split()[0] if min_price_date else '2022-01-01'
        
        # Trouver dates avec événements HIGH US ET prix disponibles
        query = f"""
        SELECT DISTINCT DATE(e.ts_utc) as date
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
            AND DATE(e.ts_utc) >= '{min_price_date_str}'
            AND DATE(e.ts_utc) <= '{max_price_date_str}'
        ORDER BY date DESC
        LIMIT 100
        """
        
        df_dates = conn.execute(query).df()
        # Convertir dates en strings (gérer format datetime)
        all_dates = []
        for d in df_dates['date'].tolist():
            if isinstance(d, str):
                date_only = d.split()[0]  # Prendre juste la date
            elif hasattr(d, 'date'):
                date_only = str(d.date())
            else:
                date_only = str(d).split()[0]
            all_dates.append(date_only)
        
        # Filtrer dates non dans entraînement
        new_dates = [d for d in all_dates if d not in training_dates]
        
        # Prendre les N plus récentes
        return new_dates[:max_dates]
    
    finally:
        conn.close()


def load_events_for_date(date_str: str) -> pd.DataFrame:
    """Charge événements HIGH IMPACT pour une date"""
    if not DB_PATH.exists():
        return pd.DataFrame()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        query = """
        SELECT 
            e.event_key,
            e.event_title,
            e.ts_utc,
            e.actual,
            e.estimate,
            e.previous,
            e.forecast,
            e.country,
            ef.family,
            ef.empirical_score,
            ef.latency_median
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE DATE(e.ts_utc) = ?
            AND e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
        ORDER BY e.ts_utc
        """
        
        df = conn.execute(query, [date_str]).df()
        return df
    
    except Exception as e:
        print(f"⚠️  Erreur chargement {date_str}: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def detect_movement_for_date(date_str: str, event_time: datetime) -> Optional[Dict]:
    """
    Détecte mouvement réel pour une date donnée
    Charge prix directement depuis prices_finnhub_m1
    """
    try:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        
        # Chercher prix autour de l'événement
        start_time = event_time - timedelta(minutes=5)
        end_time = event_time + timedelta(minutes=120)
        
        # Utiliser prices_1m_v (table la plus complète avec données jusqu'à octobre 2025)
        # Cette table a ts_utc et close
        query = """
        SELECT 
            ts_utc,
            close
        FROM prices_1m_v
        WHERE ts_utc >= ? AND ts_utc <= ?
        ORDER BY ts_utc
        """
        
        prices_df = conn.execute(query, [start_time, end_time]).df()
        conn.close()
        
        if len(prices_df) < 10:
            return None
        
        # Convertir ts_utc et normaliser timezone
        prices_df['ts_utc'] = pd.to_datetime(prices_df['ts_utc'])
        # Normaliser timezone (enlever timezone pour comparaison)
        if prices_df['ts_utc'].dt.tz is not None:
            prices_df['ts_utc'] = prices_df['ts_utc'].dt.tz_localize(None)
        prices_df = prices_df.set_index('ts_utc')
        
        # Créer open/high/low depuis close (approximation pour calcul mouvement)
        prices_df['open'] = prices_df['close'].shift(1).fillna(prices_df['close'].iloc[0])
        prices_df['high'] = prices_df[['open', 'close']].max(axis=1)
        prices_df['low'] = prices_df[['open', 'close']].min(axis=1)
        
        # Normaliser event_time (enlever timezone)
        if hasattr(event_time, 'tzinfo') and event_time.tzinfo is not None:
            event_time_naive = event_time.replace(tzinfo=None)
        else:
            event_time_naive = event_time
        
        # Trouver prix de départ (juste avant événement)
        # Chercher la ligne la plus proche de l'événement
        event_idx = prices_df.index.get_indexer([event_time_naive], method='nearest')[0]
        if event_idx < 0 or event_idx >= len(prices_df):
            return None
        
        # Prix de départ (close de la bougie juste avant l'événement, ou open de la bougie à l'événement)
        if event_idx > 0:
            start_price = prices_df.iloc[event_idx - 1]['close']
        else:
            start_price = prices_df.iloc[event_idx]['open']
        
        # Chercher pic dans les 120 minutes suivantes
        window_df = prices_df.iloc[event_idx:event_idx+120]
        
        if len(window_df) == 0:
            return None
        
        # Pic haut et bas
        peak_high = window_df['high'].max()
        peak_low = window_df['low'].min()
        
        # Direction
        move_up = peak_high - start_price
        move_down = start_price - peak_low
        
        if move_up > move_down:
            direction = 'UP'
            peak_pips = move_up * 10000
            peak_time = window_df['high'].idxmax()
        else:
            direction = 'DOWN'
            peak_pips = move_down * 10000
            peak_time = window_df['low'].idxmin()
        
        # Classifier le mouvement
        if peak_pips < 20.0:
            movement_class = 'FAIBLE'
        elif peak_pips < 50.0:
            movement_class = 'MOYEN'
        elif peak_pips < 100.0:
            movement_class = 'FORT'
        else:
            movement_class = 'TRÈS_FORT'
        
        return {
            'date': date_str,
            'peak_pips': peak_pips,
            'direction': direction,
            'peak_time': peak_time,
            'start_price': start_price,
            'movement_class': movement_class
        }
    
    except Exception as e:
        print(f"⚠️  Erreur détection mouvement {date_str}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_prices_for_trend(event_time: datetime) -> Optional[pd.Series]:
    """Charge les prix pour détection tendance pré-événement"""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Query time = event - 2h (comme dans detect_trend_by_inversion_s107)
        query_dt = event_time - timedelta(hours=2)
        start_dt = query_dt - timedelta(days=14)
        
        # Charger prix depuis prices_1m_v
        query = f"""
        SELECT ts_utc, close
        FROM prices_1m_v
        WHERE ts_utc >= '{start_dt}'::TIMESTAMP
          AND ts_utc < '{query_dt}'::TIMESTAMP
        ORDER BY ts_utc ASC
        """
        
        df = conn.execute(query).df()
        
        if len(df) < 1000:  # Minimum pour détection
            return None
        
        # Convertir en Series avec index datetime
        df['ts_utc'] = pd.to_datetime(df['ts_utc'])
        df = df.set_index('ts_utc')
        
        prices = df['close']
        
        # Ajouter high/low pour compatibilité (utiliser close comme approximation)
        prices.high = df['close']
        prices.low = df['close']
        
        return prices
    
    except Exception as e:
        return None
    finally:
        conn.close()


def calculate_prediction_pipeline(events_df: pd.DataFrame, event_time: Optional[datetime] = None) -> Dict:
    """
    Pipeline principal de prédiction pour une date/cluster donnée.
    Retourne un dict avec impact, direction, latence, etc.
    
    ⭐ PATCH V3 : Priorise direction empirique V2/V3 (alpha · surprise_z)
                  Tendance pré-événement utilisée uniquement pour info de régime
    """
    if events_df.empty:
        return {
            'impact_pips': 0.0,
            'direction': 'UNKNOWN',
            'direction_score': 0.0,
            'direction_method': 'none',
            'formula_used': 'none',
            'n_events': 0
        }
    
    try:
        # 1) Calcul impact (amplitude) existant
        result = calculate_cluster_impact(
            cluster_events=events_df,
            use_linear_formula=True
        )
        
        # 2) Détection de tendance conservée uniquement pour info de régime
        regime = 'UNKNOWN'
        trend_r2 = None
        
        if event_time is not None:
            try:
                prices = load_prices_for_trend(event_time)
                if prices is not None and len(prices) > 0:
                    query_dt = event_time - timedelta(hours=2)
                    if event_time.tzinfo:
                        query_dt = query_dt.replace(tzinfo=None)
                    
                    time_diffs = abs(prices.index - query_dt)
                    time_diffs_series = pd.Series(time_diffs.values, index=prices.index)
                    closest_idx = time_diffs_series.idxmin()
                    event_time_idx = prices.index.get_loc(closest_idx)
                    
                    # Tester scénario default pour régime
                    trend_info = detect_trend_by_inversion_s107(
                        prices=prices,
                        event_time_idx=event_time_idx,
                        lookback_days=14,
                        segment_hours=12,
                        min_r2_for_trend=0.3,
                        min_hours_before_event=24,
                        timeframe='M1'
                    )
                    
                    if trend_info and trend_info.get('trend_exists'):
                        regime = trend_info.get('direction', 'UNKNOWN')
                        trend_r2 = trend_info.get('r2', trend_info.get('r2_linear', None))
            except Exception:
                pass  # Régime reste UNKNOWN en cas d'erreur
        
        # 3) Direction finale empirique (si actuals présents)
        alpha_map = load_alpha_map(horizon='1h')
        stats_map = load_surprise_stats()
        
        # Charger seuil θ calibré
        try:
            import json
            if DIRECTION_THRESHOLDS_FILE.exists():
                with open(DIRECTION_THRESHOLDS_FILE, 'r') as f:
                    direction_thresholds = json.load(f)
                theta_calibrated = direction_thresholds.get('1h', 0.0)
            else:
                theta_calibrated = 0.0
        except Exception:
            theta_calibrated = 0.0
        
        direction_predicted, direction_score, direction_method = predict_direction_empirical(
            events_df, alpha_map, stats_map, theta=theta_calibrated
        )
        
        # 4) Pré-release fallback si aucun actual
        if direction_method == "no_signal":
            # Fallback sur surprise simple si disponible
            try:
                weighted_direction_contributions = []
                for _, row in events_df.iterrows():
                    family = row.get('family', 'Unknown')
                    empirical_score = row.get('empirical_score', 0.0)
                    actual = row.get('actual')
                    estimate = row.get('estimate')
                    previous = row.get('previous')
                    event_key = row.get('event_key', '')
                    
                    if pd.isna(actual):
                        continue
                    
                    reference = estimate if pd.notna(estimate) else previous
                    if pd.isna(reference) or abs(reference) < 0.001:
                        continue
                    
                    rate_keywords = ['rate', 'inflation', 'yield', 'interest']
                    is_rate_event = any(keyword in str(event_key).lower() for keyword in rate_keywords)
                    
                    if is_rate_event:
                        surprise = actual - reference
                    else:
                        surprise = ((actual - reference) / abs(reference)) * 100
                    
                    surprise = max(min(surprise, 100.0), -100.0)
                    if abs(surprise) < 0.1:
                        continue
                    
                    direction = get_event_direction(family=family, surprise=surprise)
                    weight = empirical_score if pd.notna(empirical_score) and empirical_score > 0 else 1.0
                    weighted_contribution = direction * abs(surprise) * weight
                    weighted_direction_contributions.append(weighted_contribution)
                
                if len(weighted_direction_contributions) > 0:
                    direction_sum_weighted = sum(weighted_direction_contributions)
                    if direction_sum_weighted > 0:
                        direction_predicted = 'UP'
                        direction_method = 'pre_release_surprise'
                    elif direction_sum_weighted < 0:
                        direction_predicted = 'DOWN'
                        direction_method = 'pre_release_surprise'
                    direction_score = 0.0
                else:
                    direction_predicted = 'UNKNOWN'
                    direction_method = 'pre_release_none'
                    direction_score = 0.0
            except Exception:
                direction_predicted = 'UNKNOWN'
                direction_method = 'pre_release_none'
                direction_score = 0.0
        
        # Appliquer calibration amplitude (k)
        impact_pips_raw = result['impact_pips']
        try:
            import json
            if AMPLITUDE_CALIBRATION_FILE.exists():
                with open(AMPLITUDE_CALIBRATION_FILE, 'r') as f:
                    amplitude_calibration = json.load(f)
                k_global = amplitude_calibration.get('k_global', 1.0)
                impact_pips_calibrated = impact_pips_raw * k_global
            else:
                impact_pips_calibrated = impact_pips_raw
        except Exception:
            impact_pips_calibrated = impact_pips_raw
        
        return {
            # impact avec calibration
            'impact_pips': impact_pips_calibrated,
            'impact_pips_raw': impact_pips_raw,  # Pour comparaison
            'base_score': result.get('base_score', 0.0),
            'adjusted_score': result.get('adjusted_score', 0.0),
            'surprise_max': result.get('max_surprise', 0.0),
            'surprise_net': result.get('calculation_details', {}).get('surprise_net', 0.0),
            'formula_used': 'linear',
            'n_events': result.get('num_events', 0),
            
            # direction avec score
            'direction': direction_predicted,
            'direction_score': direction_score,
            'direction_method': direction_method,
            
            # info contexte (non décisionnelle)
            'regime_pre_event': regime,
            'trend_r2': trend_r2,
        }
    except Exception as e:
        print(f"⚠️  Erreur calcul pipeline: {e}")
        import traceback
        traceback.print_exc()
        return {
            'impact_pips': 0.0,
            'direction': 'UNKNOWN',
            'direction_score': 0.0,
            'direction_method': 'error',
            'formula_used': 'error',
            'n_events': 0,
            'regime_pre_event': 'UNKNOWN',
            'trend_r2': None
        }


# ════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ════════════════════════════════════════════════════════════════

def validate_on_new_dates():
    """
    Valide pipeline sur nouvelles dates
    """
    print("=" * 80)
    print("VALIDATION SUR NOUVELLES DATES - CONDITIONS RÉELLES")
    print("=" * 80)
    print()
    print("🎯 FOCUS : Mouvements MOYEN, FORT et TRÈS_FORT uniquement")
    print("   (Mouvements FAIBLE < 20 pips exclus)")
    print()
    
    # 1. Trouver nouvelles dates
    print("📊 ÉTAPE 1 : Identification nouvelles dates")
    print("-" * 80)
    
    if TEST_DATES:
        test_dates = TEST_DATES
        print(f"✅ Dates fournies manuellement : {len(test_dates)}")
    elif LOAD_STRONG_MOVEMENTS_DATES and STRONG_MOVEMENTS_FILE.exists():
        # Charger dates avec mouvements significatifs
        df_strong = pd.read_csv(STRONG_MOVEMENTS_FILE)
        test_dates = df_strong['date'].astype(str).tolist()[:MAX_TEST_DATES]
        print(f"✅ Dates avec mouvements significatifs chargées : {len(test_dates)}")
        print(f"   Source : {STRONG_MOVEMENTS_FILE.name}")
    else:
        test_dates = find_new_dates(max_dates=MAX_TEST_DATES)
        print(f"✅ Dates nouvelles trouvées : {len(test_dates)}")
    
    if not test_dates:
        print("❌ Aucune nouvelle date trouvée")
        return
    
    print(f"   Dates à tester : {test_dates[:10]}")
    print()
    
    # 2. Tester chaque date
    print("📊 ÉTAPE 2 : Test pipeline sur nouvelles dates")
    print("-" * 80)
    print("   (Cela peut prendre quelques minutes...)")
    print()
    
    results = []
    errors = []
    
    for date_str in test_dates:
        try:
            # Charger événements
            events_df = load_events_for_date(date_str)
            
            if len(events_df) == 0:
                errors.append({
                    'date': date_str,
                    'error': 'No events found'
                })
                continue
            
            # Obtenir heure événement pour détection tendance
            event_ts_str = events_df['ts_utc'].iloc[0]
            if isinstance(event_ts_str, str):
                event_time = pd.to_datetime(event_ts_str)
            else:
                event_time = event_ts_str
            
            # S'assurer que c'est un datetime Python
            if isinstance(event_time, pd.Timestamp):
                event_time = event_time.to_pydatetime()
            
            # Calculer prédiction (avec event_time pour détection tendance)
            prediction = calculate_prediction_pipeline(events_df, event_time=event_time)
            
            if prediction['impact_pips'] == 0.0:
                errors.append({
                    'date': date_str,
                    'error': 'Prediction failed'
                })
                continue
            
            # Détecter mouvement réel (event_time déjà défini ci-dessus)
            movement_real = detect_movement_for_date(date_str, event_time)
            
            if movement_real is None:
                errors.append({
                    'date': date_str,
                    'error': 'No movement detected'
                })
                continue
            
            # ⚠️ FILTRER : Ne garder que MOYEN, FORT, TRÈS_FORT (exclure FAIBLE < 20 pips)
            movement_class = movement_real.get('movement_class', 'FAIBLE')
            if movement_class == 'FAIBLE':
                errors.append({
                    'date': date_str,
                    'error': f'Movement too weak ({movement_real["peak_pips"]:.1f} pips) - skipped (focus on MOYEN/FORT/TRÈS_FORT)'
                })
                continue
            
            # Comparer amplitude
            error_abs = abs(prediction['impact_pips'] - movement_real['peak_pips'])
            error_pct = (error_abs / movement_real['peak_pips']) * 100 if movement_real['peak_pips'] > 0 else 0
            
            # ⭐ NOUVEAU : Comparer direction
            direction_real = movement_real['direction']
            direction_predicted = prediction.get('direction', 'UNKNOWN')
            direction_correct = (direction_predicted == direction_real)
            
            # ⭐ NOUVEAU : Calculer impact avec signe selon direction
            # Pour affichage : +48.2 pips (UP) ou -48.2 pips (DOWN)
            # UP = mouvement positif (hausse EURUSD) = +pips
            # DOWN = mouvement négatif (baisse EURUSD) = -pips
            impact_real_signed = movement_real['peak_pips'] if direction_real == 'UP' else -movement_real['peak_pips']
            if direction_predicted == 'UP':
                impact_predicted_signed = prediction['impact_pips']
            elif direction_predicted == 'DOWN':
                impact_predicted_signed = -prediction['impact_pips']
            else:  # UNKNOWN
                impact_predicted_signed = 0.0  # Pas de direction prédite
            
            results.append({
                'date': date_str,
                'impact_real': movement_real['peak_pips'],
                'impact_predicted': prediction['impact_pips'],
                'impact_real_signed': impact_real_signed,  # ⭐ Avec signe
                'impact_predicted_signed': impact_predicted_signed,  # ⭐ Avec signe
                'error_abs': error_abs,
                'error_pct': error_pct,
                'direction_real': direction_real,
                'direction_predicted': direction_predicted,
                'direction_method': prediction.get('direction_method', 'unknown'),  # ⭐ Méthode utilisée
                'direction_correct': direction_correct,
                'movement_class': movement_class,
                'n_events': prediction['n_events'],
                'base_score': prediction.get('base_score', 0.0),
                'adjusted_score': prediction.get('adjusted_score', 0.0),
                'surprise_max': prediction.get('surprise_max', 0.0),
                'trend_r2': prediction.get('trend_r2'),  # ⭐ R² pour analyse
                'formula_used': prediction['formula_used']
            })
            
            if len(results) % 5 == 0:
                print(f"   Traité {len(results)} dates...")
        
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            errors.append({
                'date': date_str,
                'error': error_msg
            })
            if len(errors) <= 3:  # Afficher seulement les 3 premières erreurs
                print(f"   ⚠️  Erreur {date_str}: {str(e)}")
            continue
    
    print(f"✅ {len(results)} dates testées avec succès")
    if errors:
        print(f"⚠️  {len(errors)} erreurs rencontrées")
    print()
    
    if len(results) == 0:
        print("❌ Aucun résultat valide")
        return
    
    # 3. Analyser résultats
    print("=" * 80)
    print("📊 ANALYSE RÉSULTATS")
    print("=" * 80)
    print()
    
    df_results = pd.DataFrame(results)
    
    # Métriques globales (amplitude)
    mae = df_results['error_abs'].mean()
    mae_median = df_results['error_abs'].median()
    ratio_median = np.median(df_results['impact_predicted'] / df_results['impact_real'])
    corr = np.corrcoef(df_results['impact_predicted'], df_results['impact_real'])[0, 1]
    
    # ⭐ NOUVEAU : Métriques directionnelles
    direction_accuracy = df_results['direction_correct'].mean() * 100 if 'direction_correct' in df_results.columns else 0.0
    direction_correct_count = df_results['direction_correct'].sum() if 'direction_correct' in df_results.columns else 0
    
    # MAE selon direction correcte ou non
    if 'direction_correct' in df_results.columns:
        mae_correct_direction = df_results[df_results['direction_correct']]['error_abs'].mean() if len(df_results[df_results['direction_correct']]) > 0 else 0.0
        mae_wrong_direction = df_results[~df_results['direction_correct']]['error_abs'].mean() if len(df_results[~df_results['direction_correct']]) > 0 else 0.0
    else:
        mae_correct_direction = 0.0
        mae_wrong_direction = 0.0
    
    print(f"{'Métrique':<30} {'Valeur':<20}")
    print("-" * 50)
    print(f"{'Nombre de dates testées':<30} {len(df_results):<20}")
    print()
    print("📊 AMPLITUDE (Pips) :")
    print(f"{'MAE moyen':<30} {mae:>18.2f} pips")
    print(f"{'MAE médian':<30} {mae_median:>18.2f} pips")
    print(f"{'Ratio médian (prédit/réel)':<30} {ratio_median:>18.3f}")
    print(f"{'Corrélation':<30} {corr:>18.3f}")
    print()
    
    # ⭐ NOUVEAU : Direction
    print("🧭 DIRECTION :")
    print(f"{'Accuracy directionnelle':<30} {direction_accuracy:>18.1f}%")
    print(f"{'Directions correctes':<30} {direction_correct_count:>18d} / {len(df_results)}")
    if mae_correct_direction > 0 or mae_wrong_direction > 0:
        print(f"{'MAE (direction correcte)':<30} {mae_correct_direction:>18.2f} pips")
        print(f"{'MAE (direction incorrecte)':<30} {mae_wrong_direction:>18.2f} pips")
    
            # ⭐ NOUVEAU : Méthode utilisée
    if 'direction_method' in df_results.columns:
        method_counts = df_results['direction_method'].value_counts()
        print()
        print(f"{'Méthode direction utilisée':<30}")
        for method, count in method_counts.items():
            pct = (count / len(df_results)) * 100
            print(f"   {method:<25} : {count:>3} cas ({pct:>5.1f}%)")
        
        # Afficher R² moyen par méthode
        if 'trend_r2' in df_results.columns:
            print()
            print(f"{'R² moyen par méthode':<30}")
            for method in method_counts.index:
                method_data = df_results[df_results['direction_method'] == method]
                r2_values = method_data['trend_r2'].dropna()
                if len(r2_values) > 0:
                    r2_mean = r2_values.mean()
                    print(f"   {method:<25} : R² = {r2_mean:>6.3f} ({len(r2_values)} cas)")
    print()
    
    # Erreur relative moyenne
    error_pct_mean = df_results['error_pct'].mean()
    print(f"{'Erreur relative moyenne':<30} {error_pct_mean:>18.1f}%")
    print()
    
    # Top meilleures et pires prédictions
    # ⭐ AMÉLIORATION : Afficher avec signe (+/-) selon direction pour lecture plus claire
    print("📊 Top 5 meilleures prédictions :")
    print()
    top5 = df_results.nsmallest(5, 'error_abs')[['date', 'impact_real_signed', 'impact_predicted_signed', 'error_abs', 'error_pct', 'direction_real', 'direction_predicted']]
    for idx, row in top5.iterrows():
        real_signed = f"{row['impact_real_signed']:+.1f}" if 'impact_real_signed' in row and pd.notna(row['impact_real_signed']) else f"{row['impact_real']:>6.1f}"
        pred_signed = f"{row['impact_predicted_signed']:+.1f}" if 'impact_predicted_signed' in row and pd.notna(row['impact_predicted_signed']) else f"{row['impact_predicted']:>6.1f}"
        dir_info = f" [{row['direction_real']}→{row['direction_predicted']}]" if 'direction_real' in row and 'direction_predicted' in row else ""
        print(f"   {row['date']:12s} : Réel={real_signed:>8s} | Prédit={pred_signed:>8s} | Erreur={row['error_abs']:>5.1f} pips ({row['error_pct']:>5.1f}%){dir_info}")
    print()
    
    print("📊 Top 5 pires prédictions :")
    print()
    worst5 = df_results.nlargest(5, 'error_abs')[['date', 'impact_real_signed', 'impact_predicted_signed', 'error_abs', 'error_pct', 'direction_real', 'direction_predicted']]
    for idx, row in worst5.iterrows():
        real_signed = f"{row['impact_real_signed']:+.1f}" if 'impact_real_signed' in row and pd.notna(row['impact_real_signed']) else f"{row['impact_real']:>6.1f}"
        pred_signed = f"{row['impact_predicted_signed']:+.1f}" if 'impact_predicted_signed' in row and pd.notna(row['impact_predicted_signed']) else f"{row['impact_predicted']:>6.1f}"
        dir_info = f" [{row['direction_real']}→{row['direction_predicted']}]" if 'direction_real' in row and 'direction_predicted' in row else ""
        print(f"   {row['date']:12s} : Réel={real_signed:>8s} | Prédit={pred_signed:>8s} | Erreur={row['error_abs']:>5.1f} pips ({row['error_pct']:>5.1f}%){dir_info}")
    print()
    
    # ⭐ NOUVEAU : Matrice de confusion directionnelle
    if 'direction_correct' in df_results.columns:
        print("📊 Matrice de Confusion Directionnelle :")
        print()
        confusion = pd.crosstab(
            df_results['direction_real'],
            df_results['direction_predicted'],
            margins=True
        )
        print(confusion)
        print()
        
        # Détails par direction
        print("📊 Détails par Direction :")
        print()
        for direction in ['UP', 'DOWN']:
            df_dir = df_results[df_results['direction_real'] == direction]
            if len(df_dir) > 0:
                correct = df_dir['direction_correct'].sum()
                total = len(df_dir)
                accuracy = (correct / total) * 100 if total > 0 else 0.0
                print(f"   {direction:5s} réel : {correct:3d}/{total:3d} corrects ({accuracy:5.1f}%)")
        print()
    
    # Distribution erreurs
    print("📊 Distribution erreurs (amplitude) :")
    print()
    error_ranges = [
        (0, 5, "0-5 pips"),
        (5, 10, "5-10 pips"),
        (10, 20, "10-20 pips"),
        (20, 50, "20-50 pips"),
        (50, float('inf'), "> 50 pips")
    ]
    
    for min_err, max_err, label in error_ranges:
        count = len(df_results[(df_results['error_abs'] >= min_err) & (df_results['error_abs'] < max_err)])
        pct = count / len(df_results) * 100
        print(f"   {label:15s} : {count:3d} dates ({pct:5.1f}%)")
    print()
    
    # 4. Sauvegarder
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_dir / 'validation_new_dates_results.csv', index=False)
    
    summary = {
        'n_dates_tested': [len(df_results)],
        'mae_mean': [mae],
        'mae_median': [mae_median],
        'ratio_median': [ratio_median],
        'correlation': [corr],
        'error_pct_mean': [error_pct_mean]
    }
    pd.DataFrame(summary).to_csv(output_dir / 'validation_new_dates_summary.csv', index=False)
    
    if errors:
        pd.DataFrame(errors).to_csv(output_dir / 'validation_new_dates_errors.csv', index=False)
    
    print(f"💾 Fichiers sauvegardés dans : {output_dir}")
    print()
    
    print("=" * 80)
    print("✅ VALIDATION TERMINÉE")
    print("=" * 80)
    print()
    print("💡 CONCLUSION :")
    print(f"   - {len(df_results)} dates testées avec succès")
    print(f"   - MAE moyen (amplitude) : {mae:.2f} pips")
    print(f"   - Ratio médian : {ratio_median:.3f}")
    print(f"   - Corrélation : {corr:.3f}")
    if 'direction_correct' in df_results.columns:
        print(f"   - ⭐ Accuracy directionnelle : {direction_accuracy:.1f}%")
    print()
    
    # Comparaison avec performance entraînement
    print("📊 Comparaison avec performance entraînement :")
    print(f"   Entraînement (1,147 mouvements) : MAE 13.98 pips, Ratio 1.091")
    print(f"   Validation ({len(df_results)} dates) : MAE {mae:.2f} pips, Ratio {ratio_median:.3f}")
    if 'direction_correct' in df_results.columns:
        print(f"   ⭐ Direction : {direction_accuracy:.1f}% accuracy")
    print()
    
    if mae <= 20.0 and ratio_median >= 0.8:
        print("✅✅✅ EXCELLENT : Performance validation proche de l'entraînement !")
        if 'direction_correct' in df_results.columns and direction_accuracy >= 80.0:
            print("✅✅✅ Direction : Accuracy directionnelle excellente !")
    elif mae <= 30.0:
        print("✅✅ BON : Performance validation acceptable")
        if 'direction_correct' in df_results.columns and direction_accuracy >= 70.0:
            print("✅✅ Direction : Accuracy directionnelle bonne")
    else:
        print("⚠️  ATTENTION : Performance validation dégradée, investigation nécessaire")
    print()


if __name__ == '__main__':
    validate_on_new_dates()


