"""
IMPACT MEASUREMENT - MODULE MESURE IMPACTS RÉELS DUKASCOPY
===========================================================

Module pour mesurer les impacts réels EUR/USD depuis les prix Dukascopy.

VERSION 4.0 - AVEC VUE PRICES_BERN (Solution définitive timezone)
==================================================================

LOGIQUE PURE:
- Event à 14:30 Bern → Chercher prix à 14:30 dans prices_bern
- PLUS de conversion timezone
- PLUS de règle -2h
- Logique évidente et impossible à oublier

Version: 4.0
Date: 04 novembre 2025 - Session 112
Utilise: Vue prices_bern (datetime + 2h par rapport à prices_1m)
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import numpy as np


def measure_impact_from_dukascopy(
    db_path: Path,
    event_timestamp: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    debug: bool = False
) -> Dict:
    """
    Mesure l'impact réel EUR/USD depuis prix Dukascopy.
    
    VERSION 4.0 - LOGIQUE PURE (vue prices_bern):
    - Event 14:30 → chercher prix 14:30 (DIRECT)
    - Plus de conversion timezone
    - Plus de règle -2h
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        event_timestamp: Timestamp événement en HEURE BERN (ex: 14:30)
        lookback_minutes: Minutes avant (défaut 5)
        lookahead_minutes: Minutes après (défaut 120)
        debug: Afficher infos debug
    
    Returns:
        dict avec impact_pips, direction, etc. ou None si échec
    
    Examples:
        >>> from datetime import datetime
        >>> # Event 11 sept 2025 14:30 Bern
        >>> event_ts = datetime(2025, 9, 11, 14, 30, 0)
        >>> result = measure_impact_from_dukascopy(db_path, event_ts)
        >>> print(f"Impact: {result['impact_pips']:.1f} pips")
        Impact: 57.1 pips
    """
    if not db_path.exists():
        if debug:
            print(f"❌ DB introuvable: {db_path}")
        return None
    
    con = duckdb.connect(str(db_path), read_only=True)
    
    try:
        # ══════════════════════════════════════════════════════════════
        # LOGIQUE PURE V4.0 - Utilisation vue prices_bern
        # ══════════════════════════════════════════════════════════════
        
        date_str = event_timestamp.strftime('%Y-%m-%d')
        time_str = event_timestamp.strftime('%H:%M:%S')
        event_datetime = f"{date_str} {time_str}"
        
        if debug:
            print(f"\n🔍 Mesure impact pour {event_timestamp.strftime('%Y-%m-%d %H:%M')} Bern")
            print(f"   Version 4.0 - Logique pure (vue prices_bern)")
            print(f"   Query directe: {event_datetime}")
        
        # ══════════════════════════════════════════════════════════════
        # CHARGER PRIX depuis prices_bern (DIRECT, sans conversion)
        # ══════════════════════════════════════════════════════════════
        
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_bern
        WHERE datetime >= '{event_datetime}'::TIMESTAMP - INTERVAL '{lookback_minutes} minutes'
          AND datetime <= '{event_datetime}'::TIMESTAMP + INTERVAL '{lookahead_minutes} minutes'
        ORDER BY datetime ASC
        """
        
        df_prices = con.execute(query).df()
        
        if df_prices.empty:
            if debug:
                print(f"   ❌ Aucun prix trouvé")
            return None
        
        if debug:
            print(f"   ✅ {len(df_prices)} chandeliers chargés")
            print(f"      Premier: {df_prices['datetime'].iloc[0]}")
            print(f"      Dernier: {df_prices['datetime'].iloc[-1]}")
        
        # ══════════════════════════════════════════════════════════════
        # PRIX RÉFÉRENCE = OPEN PREMIÈRE BOUGIE ÉVÉNEMENT
        # ══════════════════════════════════════════════════════════════
        
        event_ts = pd.to_datetime(event_datetime)
        
        # Localiser si nécessaire
        if df_prices['datetime'].dt.tz is not None:
            if event_ts.tz is None:
                event_ts = event_ts.tz_localize(df_prices['datetime'].dt.tz)
        
        prices_at_event = df_prices[df_prices['datetime'] >= event_ts]
        
        if prices_at_event.empty:
            if debug:
                print(f"   ❌ Aucune bougie à l'événement")
            return None
        
        first_candle = prices_at_event.iloc[0]
        start_price = first_candle['open']
        
        if debug:
            print(f"   ✅ Prix référence (OPEN première bougie): {start_price:.5f}")
            print(f"      Timestamp: {first_candle['datetime']}")
        
        # ══════════════════════════════════════════════════════════════
        # CALCUL IMPACT BIDIRECTIONNEL
        # ══════════════════════════════════════════════════════════════
        
        prices_after = prices_at_event.copy()
        prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
        prices_after['pips_low'] = (start_price - prices_after['low']) * 10000
        
        peak_high = prices_after['pips_high'].max()
        peak_low = prices_after['pips_low'].max()
        
        if peak_high > peak_low:
            impact_pips = peak_high
            direction = 1  # UP
            peak_idx = prices_after['pips_high'].idxmax()
            peak_price = prices_after.loc[peak_idx, 'high']
            peak_time = prices_after.loc[peak_idx, 'datetime']
        else:
            impact_pips = peak_low
            direction = -1  # DOWN
            peak_idx = prices_after['pips_low'].idxmax()
            peak_price = prices_after.loc[peak_idx, 'low']
            peak_time = prices_after.loc[peak_idx, 'datetime']
        
        # Convertir en naive pour calculs
        if isinstance(peak_time, pd.Timestamp):
            peak_time_naive = peak_time.to_pydatetime()
            if hasattr(peak_time_naive, 'tzinfo') and peak_time_naive.tzinfo is not None:
                peak_time_naive = peak_time_naive.replace(tzinfo=None)
        else:
            peak_time_naive = peak_time
        
        # Temps au pic
        event_time_dt = event_ts.to_pydatetime() if isinstance(event_ts, pd.Timestamp) else event_ts
        if hasattr(event_time_dt, 'tzinfo') and event_time_dt.tzinfo is not None:
            event_time_dt = event_time_dt.replace(tzinfo=None)
        
        time_to_peak_minutes = (peak_time_naive - event_time_dt).total_seconds() / 60
        
        # ══════════════════════════════════════════════════════════════
        # QUALITÉ MESURE
        # ══════════════════════════════════════════════════════════════
        
        total_candles = len(df_prices)
        expected_candles = lookback_minutes + lookahead_minutes
        
        if total_candles >= expected_candles * 0.9:
            quality = 'high'
        elif total_candles >= expected_candles * 0.7:
            quality = 'medium'
        else:
            quality = 'low'
        
        if debug:
            direction_str = "UP ⬆️" if direction == 1 else "DOWN ⬇️"
            print(f"   📊 Impact: {impact_pips:.1f} pips ({direction_str})")
            print(f"      Prix départ: {start_price:.5f}")
            print(f"      Prix pic: {peak_price:.5f}")
            print(f"      Temps au pic: {time_to_peak_minutes:.1f} min")
            print(f"      Peak high: {peak_high:.1f} pips")
            print(f"      Peak low: {peak_low:.1f} pips")
            print(f"   📈 Qualité: {quality} ({total_candles}/{expected_candles} chandeliers)")
        
        return {
            'impact_pips': float(impact_pips),
            'direction': int(direction),
            'start_price': float(start_price),
            'peak_price': float(peak_price),
            'peak_time': peak_time_naive,
            'time_to_peak_minutes': float(time_to_peak_minutes),
            'peak_high_pips': float(peak_high),
            'peak_low_pips': float(peak_low),
            'num_candles_used': int(total_candles),
            'measurement_quality': quality
        }
        
    except Exception as e:
        if debug:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        return None
        
    finally:
        con.close()


def measure_impacts_batch(
    db_path: Path,
    cluster_timestamps: list,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    show_progress: bool = True
) -> pd.DataFrame:
    """
    Mesure impacts pour une liste de clusters.
    
    Args:
        db_path: Chemin DB
        cluster_timestamps: Liste timestamps événements (heure Bern)
        lookback_minutes: Minutes lookback
        lookahead_minutes: Minutes lookahead
        show_progress: Afficher progression
    
    Returns:
        DataFrame avec impacts mesurés
    """
    results = []
    
    total = len(cluster_timestamps)
    
    for i, ts in enumerate(cluster_timestamps, 1):
        if show_progress and i % 10 == 0:
            print(f"   Progression: {i}/{total} ({i/total*100:.1f}%)")
        
        result = measure_impact_from_dukascopy(
            db_path, 
            ts, 
            lookback_minutes, 
            lookahead_minutes,
            debug=False
        )
        
        if result:
            results.append({
                'timestamp': ts,
                'impact_pips': result['impact_pips'],
                'direction': result['direction'],
                'start_price': result['start_price'],
                'peak_price': result['peak_price'],
                'peak_time': result['peak_time'],
                'time_to_peak_minutes': result['time_to_peak_minutes'],
                'measurement_quality': result['measurement_quality']
            })
        else:
            results.append({
                'timestamp': ts,
                'impact_pips': np.nan,
                'direction': 0,
                'start_price': np.nan,
                'peak_price': np.nan,
                'peak_time': None,
                'time_to_peak_minutes': np.nan,
                'measurement_quality': 'failed'
            })
    
    return pd.DataFrame(results)


def validate_measurement_accuracy(
    db_path: Path,
    reference_cases: list
) -> pd.DataFrame:
    """
    Valide la précision sur cas de référence.
    
    Args:
        db_path: Chemin DB
        reference_cases: Liste de dict avec 'timestamp' (Bern) et 'expected_impact'
    
    Returns:
        DataFrame avec comparaisons
    """
    results = []
    
    for ref in reference_cases:
        ts = ref['timestamp']
        expected = ref['expected_impact']
        
        measured = measure_impact_from_dukascopy(db_path, ts, debug=False)
        
        if measured:
            error = measured['impact_pips'] - expected
            results.append({
                'timestamp': ts,
                'expected_impact': expected,
                'measured_impact': measured['impact_pips'],
                'error': error,
                'abs_error': abs(error),
                'pct_error': (error / expected * 100) if expected != 0 else 0,
                'direction': measured['direction'],
                'quality': measured['measurement_quality']
            })
        else:
            results.append({
                'timestamp': ts,
                'expected_impact': expected,
                'measured_impact': np.nan,
                'error': np.nan,
                'abs_error': np.nan,
                'pct_error': np.nan,
                'direction': 0,
                'quality': 'failed'
            })
    
    return pd.DataFrame(results)
