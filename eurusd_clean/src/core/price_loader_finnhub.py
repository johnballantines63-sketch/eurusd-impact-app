"""
PRICE LOADER FINNHUB - Module Simplifié
========================================

Chargement de prix Finnhub avec gestion correcte des timezones.
Les événements et prix sont tous deux en Europe/Zurich (Bern time),
donc pas de conversion nécessaire : Event 14:30 = Prix 14:30

Version: 2.0 (Refondu pour utiliser calculate_impact_unified)
Date: 2025-12-11
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
import pytz

# Import de la fonction unifiée
from core.impact_unified import calculate_impact_unified

# Timezone de référence
TZ_BERN = pytz.timezone('Europe/Zurich')


def get_finnhub_prices_at_event_time(
    db_path: Path,
    event_timestamp_bern: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    table_name: str = 'prices_finnhub_m1',
    conn: Optional[duckdb.DuckDBPyConnection] = None
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
    
    # ⚠️ CORRECTION : Formater pour requête SQL en format simple (YYYY-MM-DD HH:MM:SS)
    # DuckDB gère mieux les timestamps sans offset explicite si la colonne est déjà en timezone
    event_timestamp_naive = event_timestamp_bern.replace(tzinfo=None)
    event_timestamp_str = event_timestamp_naive.strftime('%Y-%m-%d %H:%M:%S')
    
    # Requête SQL - Les colonnes datetime sont déjà en Europe/Zurich
    # Utiliser format simple car DuckDB gère automatiquement la timezone de la colonne
    query = f"""
    SELECT datetime, open, high, low, close, volume
    FROM {table_name}
    WHERE datetime >= TIMESTAMP '{event_timestamp_str}' - INTERVAL '{lookback_minutes} minutes'
      AND datetime <= TIMESTAMP '{event_timestamp_str}' + INTERVAL '{lookahead_minutes} minutes'
    ORDER BY datetime ASC
    """
    
    # Utiliser la connexion fournie si disponible, sinon en créer une nouvelle
    should_close = False
    if conn is None:
        conn = duckdb.connect(str(db_path), read_only=True)
        should_close = True
    
    try:
        df = conn.execute(query).df()
        return df
    except Exception as e:
        # Si erreur (table n'existe pas, etc.), retourner DataFrame vide
        return pd.DataFrame()
    finally:
        if should_close:
            conn.close()


def measure_impact_from_finnhub(
    db_path: Path,
    event_timestamp: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120,
    debug: bool = False,
    use_unified: bool = True,  # 🆕 Flag pour utiliser calculate_impact_unified (défaut: True)
    conn: Optional[duckdb.DuckDBPyConnection] = None  # Connexion optionnelle pour éviter les conflits
) -> Optional[Dict]:
    """
    Mesure l'impact réel EUR/USD depuis prix Finnhub.
    
    ⚠️ VERSION 2.0 – IMPACT CANONIQUE (IMPACT_SPEC_V1)
    ---------------------------------------------------
    - Si use_unified=True (défaut):
        -> Utilise calculate_impact_unified() (IMPACT_SPEC_V1)
        -> impact_pips = impact_unified_pips (baseline=event_open, horizon=lookahead_minutes)
    - Si use_unified=False:
        -> Utilise l'ancienne logique legacy (pré-refonte), qui a été validée
           comme équivalente à calculate_impact_unified() dans l'audit V2.
    
    Références:
    - src/core/impact_unified.py
    - docs/RAPPORT_AUDIT_IMPACT_V2_FINAL.md
    
    Compatible avec l'interface existante (même signature de retour).
    Les événements et prix sont en Europe/Zurich (Bern time).
    DST géré automatiquement.
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        event_timestamp: Timestamp événement (peut être naive ou avec timezone)
        lookback_minutes: Minutes avant (défaut 5) - utilisé pour le chargement des prix
        lookahead_minutes: Minutes après (défaut 120) - utilisé comme horizon_minutes
        debug: Afficher infos debug
        use_unified: Si True (défaut), utilise calculate_impact_unified(). Sinon, utilise l'ancienne logique.
    
    Returns:
        dict avec impact_pips, direction, etc. ou None si échec
        
        Format de retour (compatible avec l'ancienne version):
        {
            'impact_pips': float,
            'direction': int,  # +1 = UP, -1 = DOWN
            'start_price': float,
            'peak_price': float,
            'peak_time': datetime,
            'time_to_peak_minutes': float,
            'peak_high_pips': float,
            'peak_low_pips': float,
            'num_candles_used': int,
            'measurement_quality': str  # 'high', 'medium', 'low'
        }
    
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
        lookahead_minutes=lookahead_minutes,
        conn=conn  # Passer la connexion si disponible
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
    
    # 🆕 NOUVELLE VERSION : Utiliser calculate_impact_unified() selon IMPACT_SPEC_V1
    if use_unified:
        try:
            # S'assurer que event_timestamp est en Bern time
            if event_timestamp.tzinfo is None:
                event_timestamp = TZ_BERN.localize(event_timestamp)
            elif str(event_timestamp.tzinfo) != str(TZ_BERN):
                event_timestamp = event_timestamp.replace(tzinfo=None)
                event_timestamp = TZ_BERN.localize(event_timestamp)
            
            # Appeler calculate_impact_unified()
            unified_result = calculate_impact_unified(
                df_prices=df_prices,
                event_timestamp=event_timestamp,
                baseline_method="event_open",
                horizon_minutes=lookahead_minutes,
                lookback_minutes=lookback_minutes,
                min_pips=None,  # Pas de filtre
                timezone_str="Europe/Zurich",
                debug=debug,
            )
            
            if unified_result is None:
                if debug:
                    print("   ❌ calculate_impact_unified() a retourné None")
                return None
            
            # Convertir ImpactResult en format de retour compatible avec l'ancienne version
            peak_time_naive = unified_result.peak_time
            if hasattr(peak_time_naive, 'tzinfo') and peak_time_naive.tzinfo is not None:
                peak_time_naive = peak_time_naive.replace(tzinfo=None)
            
            event_time_dt = unified_result.event_timestamp
            if hasattr(event_time_dt, 'tzinfo') and event_time_dt.tzinfo is not None:
                event_time_dt = event_time_dt.replace(tzinfo=None)
            
            # QUALITÉ MESURE (basée sur le nombre de bougies)
            total_candles = unified_result.meta.get('n_candles_window', len(df_prices))
            expected_candles = lookback_minutes + lookahead_minutes
            
            if total_candles >= expected_candles * 0.9:
                quality = 'high'
            elif total_candles >= expected_candles * 0.7:
                quality = 'medium'
            else:
                quality = 'low'
            
            if debug:
                direction_str = "UP ⬆️" if unified_result.direction == 1 else "DOWN ⬇️"
                print(f"   📊 Impact (unifié): {unified_result.impact_pips:.1f} pips ({direction_str})")
                print(f"      Prix départ: {unified_result.baseline_price:.5f}")
                print(f"      Prix pic: {unified_result.peak_price:.5f}")
                print(f"      Temps au pic: {unified_result.time_to_peak_minutes:.1f} min")
                print(f"      Peak high: {unified_result.meta.get('peak_high_pips', 0):.1f} pips")
                print(f"      Peak low: {unified_result.meta.get('peak_low_pips', 0):.1f} pips")
                print(f"   📈 Qualité: {quality} ({total_candles}/{expected_candles} chandeliers)")
            
            return {
                'impact_pips': unified_result.impact_pips,
                'direction': unified_result.direction,
                'start_price': unified_result.baseline_price,
                'peak_price': unified_result.peak_price,
                'peak_time': peak_time_naive,
                'time_to_peak_minutes': unified_result.time_to_peak_minutes,
                'peak_high_pips': unified_result.meta.get('peak_high_pips', 0.0),
                'peak_low_pips': unified_result.meta.get('peak_low_pips', 0.0),
                'num_candles_used': total_candles,
                'measurement_quality': quality
            }
        
        except Exception as e:
            if debug:
                print(f"   ⚠️ Erreur calculate_impact_unified(): {e}")
                import traceback
                traceback.print_exc()
            # Fallback vers l'ancienne logique si erreur
            if debug:
                print("   ⚠️ Fallback vers ancienne logique...")
            use_unified = False
    
    # ⚠️ ANCIENNE VERSION (legacy) - Conservée pour compatibilité
    if not use_unified:
        # S'assurer que event_timestamp est correctement en Bern time
        if event_timestamp.tzinfo is None:
            event_timestamp = TZ_BERN.localize(event_timestamp)
        else:
            event_timestamp = event_timestamp.replace(tzinfo=None)
            event_timestamp = TZ_BERN.localize(event_timestamp)
        
        # Normaliser timezones pour comparaison avec pandas Timestamps
        event_ts_pd = pd.Timestamp(event_timestamp)
        
        # Obtenir la timezone du DataFrame (première valeur)
        tz_df = None
        if len(df_prices) > 0:
            first_dt = df_prices['datetime'].iloc[0]
            if isinstance(first_dt, pd.Timestamp) and first_dt.tz is not None:
                tz_df = first_dt.tz
        
        # S'assurer que event_ts_pd a la même timezone que le DataFrame
        if tz_df is not None:
            if event_ts_pd.tz is None:
                event_ts_pd = event_ts_pd.tz_localize(tz_df)
            elif str(event_ts_pd.tz) != str(tz_df):
                event_ts_pd = event_ts_pd.tz_convert(tz_df)
        else:
            if event_ts_pd.tz is not None:
                event_ts_pd = event_ts_pd.tz_localize(None)
        
        # Trouver prix à l'événement
        prices_at_event = df_prices[df_prices['datetime'] >= event_ts_pd].copy()
        prices_before_event = df_prices[df_prices['datetime'] < event_ts_pd].copy()
        
        # PRIX RÉFÉRENCE = OPEN PREMIÈRE BOUGIE ÉVÉNEMENT
        if not prices_at_event.empty:
            first_candle = prices_at_event.iloc[0]
            start_price = first_candle['open']
            baseline_time = first_candle['datetime']
        elif not prices_before_event.empty:
            last_candle_before = prices_before_event.iloc[-1]
            start_price = last_candle_before['close']
            baseline_time = last_candle_before['datetime']
        else:
            if debug:
                print(f"   ❌ Aucune bougie trouvée")
            return None
        
        if debug:
            if not prices_at_event.empty:
                print(f"   ✅ Prix référence (OPEN première bougie événement): {start_price:.5f}")
            else:
                print(f"   ✅ Prix référence (CLOSE dernière bougie avant événement): {start_price:.5f}")
            print(f"      Timestamp: {baseline_time}")
        
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
        event_time_dt = event_ts_pd.to_pydatetime() if isinstance(event_ts_pd, pd.Timestamp) else event_timestamp
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
            print(f"   📊 Impact (legacy): {impact_pips:.1f} pips ({direction_str})")
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
    
    return None

