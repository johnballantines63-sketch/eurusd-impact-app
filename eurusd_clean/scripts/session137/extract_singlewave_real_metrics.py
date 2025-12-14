"""
EXTRACTION MÉTRIQUES RÉELLES SINGLE WAVE FORT
Session 137 - Recalibration Formules V1.2

Mission:
- Extraire métriques réelles pour tous les mouvements SINGLE_WAVE_FORT
- Calculer: impact, latence, durée jusqu'à pic, pullback (si présent), stabilisation
- Sauvegarder dans CSV pour calibration formules V1.2

Auteur: André Valentin avec Claude
Date: 2025-01-XX
"""

import pandas as pd
import numpy as np
import duckdb
from pathlib import Path
from datetime import timedelta
from typing import Dict, Optional, Tuple
import sys

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
MOVEMENTS_CSV = Path(__file__).parent / "step3_movements_with_patterns_v2.csv"
OUTPUT_CSV = Path(__file__).parent / "singlewave_real_metrics.csv"

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def pips_diff(price1: float, price2: float) -> float:
    """Calcule différence en pips entre deux prix"""
    return abs(price1 - price2) * 10000


def find_first_movement_candle(
    df_prices: pd.DataFrame,
    event_time: pd.Timestamp,
    baseline_price: float,
    direction: str,
    threshold_pips: float = 5.0
) -> Optional[Tuple[pd.Timestamp, float, float]]:
    """
    Trouve la première bougie où le mouvement commence (latence).
    
    Args:
        df_prices: DataFrame avec colonnes datetime, open, high, low, close
        event_time: Timestamp de l'événement
        baseline_price: Prix de référence (baseline)
        direction: 'UP' ou 'DOWN'
        threshold_pips: Seuil minimum en pips pour considérer un mouvement
    
    Returns:
        (timestamp, price, latency_minutes) ou None
    """
    prices_after = df_prices[df_prices['datetime'] >= event_time].copy()
    
    if len(prices_after) == 0:
        return None
    
    for idx, row in prices_after.iterrows():
        if direction == 'UP':
            # Vérifier si high dépasse le seuil
            if row['high'] > baseline_price + (threshold_pips / 10000):
                latency = (row['datetime'] - event_time).total_seconds() / 60
                return (row['datetime'], row['high'], latency)
        else:  # DOWN
            # Vérifier si low dépasse le seuil
            if row['low'] < baseline_price - (threshold_pips / 10000):
                latency = (row['datetime'] - event_time).total_seconds() / 60
                return (row['datetime'], row['low'], latency)
    
    return None


def find_peak(
    df_prices: pd.DataFrame,
    start_time: pd.Timestamp,
    end_time: pd.Timestamp,
    direction: str
) -> Optional[Tuple[pd.Timestamp, float, float]]:
    """
    Trouve le pic (maximum ou minimum) dans une fenêtre temporelle.
    
    Returns:
        (timestamp, price, minutes_from_start) ou None
    """
    window = df_prices[
        (df_prices['datetime'] >= start_time) & 
        (df_prices['datetime'] <= end_time)
    ].copy()
    
    if len(window) == 0:
        return None
    
    if direction == 'UP':
        idx = window['high'].idxmax()
        peak_price = window.loc[idx, 'high']
    else:  # DOWN
        idx = window['low'].idxmin()
        peak_price = window.loc[idx, 'low']
    
    peak_time = window.loc[idx, 'datetime']
    minutes_from_start = (peak_time - start_time).total_seconds() / 60
    
    return (peak_time, peak_price, minutes_from_start)


def find_pullback(
    df_prices: pd.DataFrame,
    peak_time: pd.Timestamp,
    peak_price: float,
    direction: str,
    max_window_minutes: int = 60
) -> Optional[Dict]:
    """
    Trouve le pullback après un pic.
    
    Returns:
        Dict avec 'low_time', 'low_price', 'pullback_pips', 'pullback_ratio', 'pullback_minutes'
        ou None si pas de pullback significatif
    """
    end_time = peak_time + timedelta(minutes=max_window_minutes)
    window = df_prices[
        (df_prices['datetime'] > peak_time) & 
        (df_prices['datetime'] <= end_time)
    ].copy()
    
    if len(window) == 0:
        return None
    
    if direction == 'UP':
        # Chercher le minimum après le pic
        idx = window['low'].idxmin()
        pullback_price = window.loc[idx, 'low']
        pullback_time = window.loc[idx, 'datetime']
    else:  # DOWN
        # Chercher le maximum après le pic
        idx = window['high'].idxmax()
        pullback_price = window.loc[idx, 'high']
        pullback_time = window.loc[idx, 'datetime']
    
    pullback_pips = pips_diff(peak_price, pullback_price)
    peak_amplitude = pips_diff(peak_price, df_prices[df_prices['datetime'] < peak_time]['close'].iloc[-1] if len(df_prices[df_prices['datetime'] < peak_time]) > 0 else df_prices['close'].iloc[0])
    pullback_ratio = pullback_pips / peak_amplitude if peak_amplitude > 0 else 0.0
    pullback_minutes = (pullback_time - peak_time).total_seconds() / 60
    
    # Ne retourner que si pullback > 10% (significatif)
    if pullback_ratio < 0.10:
        return None
    
    return {
        'low_time': pullback_time,
        'low_price': pullback_price,
        'pullback_pips': pullback_pips,
        'pullback_ratio': pullback_ratio,
        'pullback_minutes': pullback_minutes
    }


def find_stabilization(
    df_prices: pd.DataFrame,
    peak_time: pd.Timestamp,
    peak_price: float,
    direction: str,
    max_window_minutes: int = 120
) -> Optional[Tuple[pd.Timestamp, float]]:
    """
    Trouve le moment de stabilisation (prix revient à ±5% du pic).
    
    Returns:
        (timestamp, minutes_from_peak) ou None
    """
    end_time = peak_time + timedelta(minutes=max_window_minutes)
    window = df_prices[
        (df_prices['datetime'] > peak_time) & 
        (df_prices['datetime'] <= end_time)
    ].copy()
    
    if len(window) == 0:
        return None
    
    threshold = abs(peak_price) * 0.05  # 5% du pic
    
    for idx, row in window.iterrows():
        if direction == 'UP':
            # Stabilisation si close descend sous peak - threshold
            if row['close'] < peak_price - threshold:
                minutes_from_peak = (row['datetime'] - peak_time).total_seconds() / 60
                return (row['datetime'], minutes_from_peak)
        else:  # DOWN
            # Stabilisation si close remonte au-dessus de peak + threshold
            if row['close'] > peak_price + threshold:
                minutes_from_peak = (row['datetime'] - peak_time).total_seconds() / 60
                return (row['datetime'], minutes_from_peak)
    
    return None


# =============================================================================
# FONCTION PRINCIPALE D'EXTRACTION
# =============================================================================

def extract_singlewave_metrics(
    movement_id: int,
    movement_datetime: pd.Timestamp,
    direction: str,
    baseline_price: Optional[float],
    conn: duckdb.DuckDBPyConnection
) -> Optional[Dict]:
    """
    Extrait toutes les métriques réelles pour un mouvement Single Wave Fort.
    
    Returns:
        Dict avec toutes les métriques ou None si erreur
    """
    # Fenêtre: -10 min avant → +120 min après
    start_time = movement_datetime - timedelta(minutes=10)
    end_time = movement_datetime + timedelta(minutes=120)
    
    # Charger prix
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_time, end_time]).df()
    
    if len(df_prices) == 0:
        return None
    
    # Convertir datetime en timezone-aware si nécessaire
    if df_prices['datetime'].dtype == 'object':
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    # S'assurer que movement_datetime est dans le même format
    if isinstance(movement_datetime, str):
        movement_datetime = pd.to_datetime(movement_datetime)
    
    # Baseline (dernier close avant événement, ou premier si pas de données avant)
    prices_before = df_prices[df_prices['datetime'] < movement_datetime]
    if baseline_price is None:
        if len(prices_before) > 0:
            baseline_price = prices_before['close'].iloc[-1]
        else:
            baseline_price = df_prices['close'].iloc[0]
    
    # Vérifier que baseline_price est valide
    if baseline_price is None or pd.isna(baseline_price):
        return None
    
    # 1. Latence (première bougie avec mouvement > 5 pips)
    # Essayer d'abord avec seuil 5 pips, puis 3 pips si aucun mouvement
    movement_start = find_first_movement_candle(df_prices, movement_datetime, baseline_price, direction, threshold_pips=5.0)
    
    if movement_start is None:
        # Essayer avec seuil plus bas (3 pips)
        movement_start = find_first_movement_candle(df_prices, movement_datetime, baseline_price, direction, threshold_pips=3.0)
    
    if movement_start is None:
        return None
    
    movement_start_time, movement_start_price, latency_minutes = movement_start
    
    # 2. Pic (maximum dans les 120 min après début mouvement)
    peak_window_end = movement_start_time + timedelta(minutes=120)
    peak_result = find_peak(df_prices, movement_start_time, peak_window_end, direction)
    
    if peak_result is None:
        return None
    
    peak_time, peak_price, peak_minutes_from_start = peak_result
    
    # Vérifier que peak_price est valide
    if peak_price is None or pd.isna(peak_price):
        return None
    
    # Impact total (baseline → pic)
    if direction == 'UP':
        impact_pips = (peak_price - baseline_price) * 10000
    else:  # DOWN
        impact_pips = (baseline_price - peak_price) * 10000
    
    # 3. Pullback (optionnel, seulement si significatif)
    pullback_info = find_pullback(df_prices, peak_time, peak_price, direction, max_window_minutes=60)
    
    # 4. Stabilisation (optionnel)
    stabilization_info = find_stabilization(df_prices, peak_time, peak_price, direction, max_window_minutes=120)
    
    # Construire résultat
    result = {
        'movement_id': movement_id,
        'datetime': movement_datetime,
        'direction': direction,
        'baseline_price': baseline_price,
        'latency_minutes': latency_minutes,
        'movement_start_time': movement_start_time,
        'peak_time': peak_time,
        'peak_price': peak_price,
        'peak_minutes_from_start': peak_minutes_from_start,
        'impact_pips': impact_pips,
    }
    
    if pullback_info:
        result.update({
            'has_pullback': True,
            'pullback_time': pullback_info['low_time'],
            'pullback_price': pullback_info['low_price'],
            'pullback_pips': pullback_info['pullback_pips'],
            'pullback_ratio': pullback_info['pullback_ratio'],
            'pullback_minutes_from_peak': pullback_info['pullback_minutes']
        })
    else:
        result.update({
            'has_pullback': False,
            'pullback_time': None,
            'pullback_price': None,
            'pullback_pips': None,
            'pullback_ratio': None,
            'pullback_minutes_from_peak': None
        })
    
    if stabilization_info:
        result['stabilization_time'] = stabilization_info[0]
        result['stabilization_minutes_from_peak'] = stabilization_info[1]
    else:
        result['stabilization_time'] = None
        result['stabilization_minutes_from_peak'] = None
    
    return result


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("EXTRACTION MÉTRIQUES RÉELLES SINGLE WAVE FORT")
    print("=" * 80)
    
    # Charger mouvements
    print("\n📊 Chargement mouvements...")
    df = pd.read_csv(MOVEMENTS_CSV)
    df['movement_datetime'] = pd.to_datetime(df['movement_datetime'])
    
    # Filtrer Single Wave Fort
    df_sw = df[df['pattern_type'].str.startswith('SINGLE_WAVE_FORT', na=False)].copy()
    
    print(f"   ✅ {len(df)} mouvements totaux")
    print(f"   🎯 {len(df_sw)} SINGLE_WAVE_FORT détectés")
    
    # Séparer UP et DOWN
    df_sw_up = df_sw[df_sw['pattern_type'] == 'SINGLE_WAVE_FORT_UP'].copy()
    df_sw_down = df_sw[df_sw['pattern_type'] == 'SINGLE_WAVE_FORT_DOWN'].copy()
    
    print(f"      - SINGLE_WAVE_FORT_UP   : {len(df_sw_up)}")
    print(f"      - SINGLE_WAVE_FORT_DOWN : {len(df_sw_down)}")
    
    # Connexion DB
    print("\n🔌 Connexion DB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Extraire métriques pour chaque mouvement
    print("\n📈 Extraction métriques...")
    results = []
    
    for idx, row in df_sw.iterrows():
        movement_id = row['movement_id']
        movement_datetime = row['movement_datetime']
        direction = row['direction']
        baseline_price = row.get('baseline_price', None)
        pattern_type = row['pattern_type']
        
        if idx % 10 == 0:
            print(f"   Traitement {idx+1}/{len(df_sw)}...")
        
        try:
            metrics = extract_singlewave_metrics(
                movement_id,
                movement_datetime,
                direction,
                baseline_price,
                conn
            )
            
            if metrics:
                metrics['pattern_type'] = pattern_type
                metrics['total_score'] = row.get('total_score', None)
                metrics['num_events'] = row.get('num_events', None)
                results.append(metrics)
            else:
                # Debug: pourquoi None?
                if idx < 5:  # Seulement pour les 5 premiers
                    print(f"   ⚠️  Mouvement {movement_id}: metrics=None (pas de mouvement détecté?)")
        except Exception as e:
            print(f"   ⚠️  Erreur mouvement {movement_id}: {e}")
            import traceback
            if idx < 3:  # Seulement pour les 3 premiers
                traceback.print_exc()
            continue
    
    conn.close()
    
    # Sauvegarder résultats
    if len(results) == 0:
        print("\n❌ Aucune métrique extraite")
        return
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ {len(results)} métriques extraites")
    print(f"   Sauvegardé dans: {OUTPUT_CSV}")
    
    # Statistiques rapides
    print("\n📊 Statistiques rapides:")
    print(f"   Impact médian (UP)   : {df_results[df_results['direction']=='UP']['impact_pips'].median():.1f} pips")
    print(f"   Impact médian (DOWN) : {df_results[df_results['direction']=='DOWN']['impact_pips'].median():.1f} pips")
    print(f"   Latence médiane      : {df_results['latency_minutes'].median():.2f} min")
    print(f"   Durée pic médiane    : {df_results['peak_minutes_from_start'].median():.1f} min")
    print(f"   Pullback présent     : {df_results['has_pullback'].sum()}/{len(df_results)} ({100.0*df_results['has_pullback'].sum()/len(df_results):.1f}%)")


if __name__ == "__main__":
    main()

