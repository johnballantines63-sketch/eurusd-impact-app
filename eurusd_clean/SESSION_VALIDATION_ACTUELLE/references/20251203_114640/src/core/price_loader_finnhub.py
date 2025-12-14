"""
PRICE LOADER FINNHUB - Module Simplifié
========================================

Chargement de prix Finnhub avec gestion correcte des timezones.
Les événements et prix sont tous deux en Europe/Zurich (Bern time),
donc pas de conversion nécessaire : Event 14:30 = Prix 14:30

Version: 1.0
Date: 2025-01-XX
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import pytz

# Timezone de référence
TZ_BERN = pytz.timezone('Europe/Zurich')


def get_finnhub_prices_at_event_time(
    db_path: Path,
    event_timestamp_bern: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    table_name: str = 'prices_finnhub_m1'
) -> pd.DataFrame:
    """
    Charge prix Finnhub correspondant à un événement.
    
    Les événements et prix sont tous deux stockés en Europe/Zurich (Bern time),
    donc pas de conversion nécessaire : même heure, même timezone.
    DST (heure d'hiver/été) est géré automatiquement par DuckDB.
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        event_timestamp_bern: Timestamp événement en Bern time (peut être naive ou aware)
        lookback_minutes: Minutes avant l'événement (défaut: 5)
        lookahead_minutes: Minutes après l'événement (défaut: 120)
        table_name: Table à utiliser (défaut: prices_finnhub_m1)
    
    Returns:
        DataFrame avec colonnes : datetime, open, high, low, close, volume
        DataFrame vide si aucune donnée trouvée
    
    Examples:
        >>> from datetime import datetime
        >>> import pytz
        >>> 
        >>> tz_bern = pytz.timezone('Europe/Zurich')
        >>> event_time = tz_bern.localize(datetime(2025, 9, 11, 14, 30))
        >>> 
        >>> prices = get_finnhub_prices_at_event_time(db_path, event_time)
        >>> print(f"Prix trouvés: {len(prices)} chandeliers")
    """
    if not db_path.exists():
        return pd.DataFrame()
    
    # S'assurer que le timestamp a la timezone Bern
    if event_timestamp_bern.tzinfo is None:
        # Naive timestamp - localiser en Bern
        event_timestamp_bern = TZ_BERN.localize(event_timestamp_bern)
    elif str(event_timestamp_bern.tzinfo) != str(TZ_BERN):
        # Autre timezone - convertir vers Bern
        event_timestamp_bern = event_timestamp_bern.astimezone(TZ_BERN)
    
    # Formater pour requête SQL (format ISO avec timezone)
    event_timestamp_str = event_timestamp_bern.isoformat()
    
    # Requête SQL - Utiliser TIMESTAMP WITH TIME ZONE pour gérer correctement
    query = f"""
    SELECT datetime, open, high, low, close, volume
    FROM {table_name}
    WHERE datetime >= '{event_timestamp_str}'::TIMESTAMP WITH TIME ZONE - INTERVAL '{lookback_minutes} minutes'
      AND datetime <= '{event_timestamp_str}'::TIMESTAMP WITH TIME ZONE + INTERVAL '{lookahead_minutes} minutes'
    ORDER BY datetime ASC
    """
    
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        df = conn.execute(query).df()
        return df
    except Exception as e:
        # Si erreur (table n'existe pas, etc.), retourner DataFrame vide
        return pd.DataFrame()
    finally:
        conn.close()


def measure_impact_from_finnhub(
    db_path: Path,
    event_timestamp: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    debug: bool = False
) -> Dict:
    """
    Mesure l'impact réel EUR/USD depuis prix Finnhub.
    
    VERSION 1.0 - FINNHUB NATIF:
    - Utilise prices_finnhub_m1 directement
    - Les événements et prix sont en Europe/Zurich (Bern time)
    - Pas de conversion nécessaire : même heure, même timezone
    - DST géré automatiquement
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        event_timestamp: Timestamp événement (peut être naive ou avec timezone)
        lookback_minutes: Minutes avant (défaut 5)
        lookahead_minutes: Minutes après (défaut 120)
        debug: Afficher infos debug
    
    Returns:
        dict avec impact_pips, direction, etc. ou None si échec
    
    Examples:
        >>> from datetime import datetime
        >>> import pytz
        >>> 
        >>> tz_bern = pytz.timezone('Europe/Zurich')
        >>> event_ts = tz_bern.localize(datetime(2025, 9, 11, 14, 30))
        >>> 
        >>> result = measure_impact_from_finnhub(db_path, event_ts)
        >>> print(f"Impact: {result['impact_pips']:.1f} pips")
    """
    if not db_path.exists():
        if debug:
            print(f"❌ DB introuvable: {db_path}")
        return None
    
    # Charger prix autour de l'événement
    df_prices = get_finnhub_prices_at_event_time(
        db_path=db_path,
        event_timestamp_bern=event_timestamp,
        lookback_minutes=lookback_minutes,
        lookahead_minutes=lookahead_minutes
    )
    
    if df_prices.empty:
        if debug:
            print(f"   ❌ Aucun prix trouvé")
        return None
    
    # Convertir datetime en pandas Timestamp si nécessaire
    if 'datetime' in df_prices.columns:
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    
    if debug:
        print(f"   ✅ {len(df_prices)} chandeliers chargés")
        print(f"      Premier: {df_prices['datetime'].iloc[0]}")
        print(f"      Dernier: {df_prices['datetime'].iloc[-1]}")
    
    # S'assurer que event_timestamp est en Bern time pour comparaison
    if event_timestamp.tzinfo is None:
        event_timestamp = TZ_BERN.localize(event_timestamp)
    elif str(event_timestamp.tzinfo) != str(TZ_BERN):
        event_timestamp = event_timestamp.astimezone(TZ_BERN)
    
    # Normaliser timezones pour comparaison
    if df_prices['datetime'].dt.tz is not None:
        # Les deux ont timezone - les normaliser en Bern
        event_ts = event_timestamp
        if str(event_timestamp.tzinfo) != str(TZ_BERN):
            event_ts = event_timestamp.astimezone(TZ_BERN)
    else:
        # Prix sans timezone - supprimer timezone de event pour comparaison
        event_ts = event_timestamp.replace(tzinfo=None)
    
    # Trouver prix à l'événement
    prices_at_event = df_prices[df_prices['datetime'] >= event_ts]
    
    if prices_at_event.empty:
        if debug:
            print(f"   ❌ Aucune bougie à l'événement")
        return None
    
    # PRIX RÉFÉRENCE = OPEN PREMIÈRE BOUGIE ÉVÉNEMENT
    first_candle = prices_at_event.iloc[0]
    start_price = first_candle['open']
    
    if debug:
        print(f"   ✅ Prix référence (OPEN première bougie): {start_price:.5f}")
        print(f"      Timestamp: {first_candle['datetime']}")
    
    # CALCUL IMPACT BIDIRECTIONNEL
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
    
    # QUALITÉ MESURE
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

