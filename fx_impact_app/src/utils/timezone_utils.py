"""
TIMEZONE UTILITIES - SOLUTION DÉFINITIVE
========================================

Résout DÉFINITIVEMENT les problèmes timezone Sessions 77-79.

PROBLÈME :
- Database : events.ts_utc est en UTC pur
- Dataset : datetime contient timezone (+01:00 ou +02:00)
- Scripts : Faisaient double conversion → 0 événements trouvés

SOLUTION :
- Parse dataset (contient déjà timezone)
- Convertir DIRECTEMENT en UTC pour query
- Fonction centralisée pour éviter erreurs

Date : 25 octobre 2025
Session : 79
"""

import pytz
from datetime import datetime, timedelta
import dateutil.parser
from typing import Tuple

# Timezones
TZ_BERNE = pytz.timezone('Europe/Zurich')
TZ_UTC = pytz.UTC


def parse_dataset_datetime(datetime_str: str) -> datetime:
    """
    Parse datetime depuis dataset (contient déjà timezone)
    
    Le dataset movements_strong_session75_v3.csv contient des datetimes
    avec timezone explicite :
    - Hiver : '2024-12-18 19:35:00+01:00' (UTC+1)
    - Été   : '2024-06-07 14:26:00+02:00' (UTC+2)
    
    dateutil.parser détecte automatiquement le timezone.
    
    Args:
        datetime_str: Format 'YYYY-MM-DD HH:MM:SS+HH:MM'
    
    Returns:
        datetime: Objet datetime avec timezone correct
    
    Examples:
        >>> dt = parse_dataset_datetime('2024-12-18 19:35:00+01:00')
        >>> dt.hour
        19
        >>> dt.tzinfo
        tzoffset(None, 3600)  # UTC+1
    """
    return dateutil.parser.parse(datetime_str)


def to_utc_for_db_query(dt: datetime) -> datetime:
    """
    Convertit datetime en UTC pour requête database
    
    La colonne events.ts_utc dans warehouse.duckdb est stockée
    en UTC pur. Toutes les requêtes doivent donc utiliser UTC.
    
    Args:
        dt: datetime avec timezone
    
    Returns:
        datetime: En UTC pur pour query WHERE ts_utc
    
    Examples:
        >>> dt = parse_dataset_datetime('2024-12-18 19:35:00+01:00')
        >>> dt_utc = to_utc_for_db_query(dt)
        >>> dt_utc.strftime('%Y-%m-%d %H:%M:%S')
        '2024-12-18 18:35:00'  # -1 heure (hiver)
        
        >>> dt = parse_dataset_datetime('2024-06-07 14:26:00+02:00')
        >>> dt_utc = to_utc_for_db_query(dt)
        >>> dt_utc.strftime('%Y-%m-%d %H:%M:%S')
        '2024-06-07 12:26:00'  # -2 heures (été)
    """
    return dt.astimezone(TZ_UTC)


def format_for_sql(dt: datetime) -> str:
    """
    Formate datetime pour clause SQL WHERE
    
    Args:
        dt: datetime (any timezone)
    
    Returns:
        str: Format SQL 'YYYY-MM-DD HH:MM:SS' en UTC
    
    Examples:
        >>> dt = parse_dataset_datetime('2024-12-18 19:35:00+01:00')
        >>> format_for_sql(dt)
        '2024-12-18 18:35:00'
    """
    dt_utc = to_utc_for_db_query(dt)
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')


def get_event_window_utc(
    movement_datetime_str: str, 
    window_minutes: int
) -> Tuple[str, str]:
    """
    Crée fenêtre temporelle en UTC pour query events
    
    ⭐ FONCTION PRINCIPALE À UTILISER PARTOUT ⭐
    
    Cette fonction fait TOUT correctement :
    1. Parse datetime du CSV (avec timezone)
    2. Convertit en UTC
    3. Crée fenêtre ±N minutes
    4. Retourne strings SQL-ready
    
    Args:
        movement_datetime_str: datetime depuis CSV avec timezone
                              Ex: '2024-12-18 19:35:00+01:00'
        window_minutes: Fenêtre ±X minutes
    
    Returns:
        tuple: (start_utc_str, end_utc_str) pour SQL WHERE
    
    Examples:
        >>> start, end = get_event_window_utc('2024-12-18 19:35:00+01:00', 15)
        >>> start
        '2024-12-18 18:20:00'
        >>> end
        '2024-12-18 18:50:00'
        
        >>> # Usage typique dans query
        >>> query = f"SELECT ... WHERE ts_utc >= '{start}' AND ts_utc <= '{end}'"
    
    Usage Pattern:
        ```python
        from src.utils.timezone_utils import get_event_window_utc
        
        for _, row in df_movements.iterrows():
            start_utc, end_utc = get_event_window_utc(
                row['datetime'], 
                window_minutes=30
            )
            
            query = f'''
            SELECT ... FROM events
            WHERE ts_utc >= '{start_utc}'
              AND ts_utc <= '{end_utc}'
            '''
        ```
    """
    # Parse datetime du dataset (contient timezone)
    dt = parse_dataset_datetime(movement_datetime_str)
    
    # Convertir en UTC
    dt_utc = to_utc_for_db_query(dt)
    
    # Créer fenêtre ±window_minutes
    start_utc = dt_utc - timedelta(minutes=window_minutes)
    end_utc = dt_utc + timedelta(minutes=window_minutes)
    
    # Formater pour SQL
    start_str = start_utc.strftime('%Y-%m-%d %H:%M:%S')
    end_str = end_utc.strftime('%Y-%m-%d %H:%M:%S')
    
    return (start_str, end_str)


# ════════════════════════════════════════════════════════════════
# TESTS UNITAIRES (si exécuté directement)
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 TESTS TIMEZONE_UTILS")
    print("=" * 70)
    print()
    
    # Test 1 : Hiver UTC+1
    print("📋 TEST 1 : Hiver (UTC+1)")
    print("-" * 70)
    datetime_winter = '2024-12-18 19:35:00+01:00'
    start, end = get_event_window_utc(datetime_winter, 15)
    print(f"Input  : {datetime_winter}")
    print(f"Window : ±15 min")
    print(f"Start  : {start} (attendu: 2024-12-18 18:20:00)")
    print(f"End    : {end} (attendu: 2024-12-18 18:50:00)")
    assert start == '2024-12-18 18:20:00', f"Start incorrect: {start}"
    assert end == '2024-12-18 18:50:00', f"End incorrect: {end}"
    print("✅ Test hiver OK")
    print()
    
    # Test 2 : Été UTC+2
    print("📋 TEST 2 : Été (UTC+2)")
    print("-" * 70)
    datetime_summer = '2024-06-07 14:26:00+02:00'
    start, end = get_event_window_utc(datetime_summer, 15)
    print(f"Input  : {datetime_summer}")
    print(f"Window : ±15 min")
    print(f"Start  : {start} (attendu: 2024-06-07 12:11:00)")
    print(f"End    : {end} (attendu: 2024-06-07 12:41:00)")
    assert start == '2024-06-07 12:11:00', f"Start incorrect: {start}"
    assert end == '2024-06-07 12:41:00', f"End incorrect: {end}"
    print("✅ Test été OK")
    print()
    
    # Test 3 : Cas référence 11 septembre
    print("📋 TEST 3 : 11 septembre 2025")
    print("-" * 70)
    datetime_ref = '2025-09-11 14:30:00+02:00'
    start, end = get_event_window_utc(datetime_ref, 30)
    print(f"Input  : {datetime_ref}")
    print(f"Window : ±30 min")
    print(f"Start  : {start} (attendu: 2025-09-11 12:00:00)")
    print(f"End    : {end} (attendu: 2025-09-11 13:00:00)")
    assert start == '2025-09-11 12:00:00', f"Start incorrect: {start}"
    assert end == '2025-09-11 13:00:00', f"End incorrect: {end}"
    print("✅ Test 11 sept OK")
    print()
    
    # Test 4 : Fenêtre large
    print("📋 TEST 4 : Fenêtre large (±60 min)")
    print("-" * 70)
    start, end = get_event_window_utc('2024-01-05 14:30:00+01:00', 60)
    print(f"Input  : 2024-01-05 14:30:00+01:00")
    print(f"Window : ±60 min")
    print(f"Start  : {start} (attendu: 2024-01-05 12:30:00)")
    print(f"End    : {end} (attendu: 2024-01-05 14:30:00)")
    assert start == '2024-01-05 12:30:00', f"Start incorrect: {start}"
    assert end == '2024-01-05 14:30:00', f"End incorrect: {end}"
    print("✅ Test fenêtre large OK")
    print()
    
    print("=" * 70)
    print("✅ TOUS LES TESTS SONT PASSÉS")
    print("=" * 70)
    print()
    print("📋 UTILISATION :")
    print("   from src.utils.timezone_utils import get_event_window_utc")
    print("   start, end = get_event_window_utc(row['datetime'], 30)")
    print()
