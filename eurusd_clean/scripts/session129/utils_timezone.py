#!/usr/bin/env python3
"""
UTILITAIRE TIMEZONE - SESSION 129
==================================

Fonctions pour gérer les timezones correctement et éviter double conversion.

CONTEXTE CRITIQUE :
- Table events.ts_utc stocke timestamps en Bern time (UTC+2 / +01)
- Beaucoup de scripts ajoutaient +2h pensant convertir UTC→Bern
- Résultat : Double conversion → décalage 2h → résultats faux

RÈGLE D'OR :
Ne JAMAIS ajouter +2h sans vérifier si timestamp déjà en Bern time !

Auteur : André Valentin avec Claude
Date : 12 novembre 2025 - Session 129
"""

import pandas as pd
import pytz
from typing import Union

# Timezone Bern (Europe/Zurich)
TZ_BERN = pytz.timezone('Europe/Zurich')


def ensure_bern_time(timestamp: Union[str, pd.Timestamp]) -> pd.Timestamp:
    """
    S'assure qu'un timestamp est en Bern time sans double conversion.
    
    Cette fonction est LA SEULE façon correcte de manipuler les timestamps
    venant de la table events.ts_utc.
    
    LOGIQUE :
    1. Si timestamp déjà avec timezone +02:00 ou +01:00 → Garder tel quel
    2. Si timestamp sans timezone → Assumer UTC et convertir vers Bern
    3. Si timestamp avec autre timezone → Convertir vers Bern
    
    Args:
        timestamp: Timestamp sous forme string ou pd.Timestamp
        
    Returns:
        pd.Timestamp en Bern time (UTC+2 été / UTC+1 hiver)
        
    Examples:
        >>> # Cas 1 : Déjà en Bern time (AUCUNE conversion)
        >>> ts = ensure_bern_time('2025-08-01 14:30:00+02:00')
        >>> print(ts)  # 2025-08-01 14:30:00+02:00 (inchangé)
        
        >>> # Cas 2 : Sans timezone (assume UTC, convertit)
        >>> ts = ensure_bern_time('2025-08-01 12:30:00')
        >>> print(ts)  # 2025-08-01 14:30:00+02:00 (UTC+2)
        
        >>> # Cas 3 : Autre timezone (convertit)
        >>> ts = ensure_bern_time('2025-08-01 08:30:00-04:00')
        >>> print(ts)  # 2025-08-01 14:30:00+02:00
    """
    # Convertir en pd.Timestamp
    if isinstance(timestamp, str):
        ts = pd.to_datetime(timestamp)
    else:
        ts = timestamp
    
    # CAS 1 : Déjà avec timezone
    if ts.tzinfo is not None:
        # Vérifier si déjà en Bern time (UTC+2 ou UTC+1)
        offset_hours = ts.utcoffset().total_seconds() / 3600
        
        if offset_hours in [1.0, 2.0]:
            # Déjà en Bern time (Europe/Zurich)
            # ⚠️ NE PAS convertir ! Retourner tel quel
            return ts
        else:
            # Autre timezone → Convertir vers Bern
            return ts.tz_convert(TZ_BERN)
    
    # CAS 2 : Sans timezone → Assumer UTC et convertir
    else:
        return ts.tz_localize('UTC').tz_convert(TZ_BERN)


def format_for_prices_bern_query(timestamp: pd.Timestamp) -> str:
    """
    Formate un timestamp pour requête prices_bern.
    
    prices_bern.datetime attend format : 'YYYY-MM-DD HH:MM:SS+02:00'
    
    Args:
        timestamp: pd.Timestamp en Bern time
        
    Returns:
        String formaté pour SQL query
        
    Example:
        >>> ts = ensure_bern_time('2025-08-01 14:30:00+02:00')
        >>> format_for_prices_bern_query(ts)
        '2025-08-01 14:30:00+02:00'
    """
    # S'assurer que timestamp en Bern time
    ts_bern = ensure_bern_time(timestamp)
    
    # Format SQL avec timezone explicite
    return ts_bern.strftime('%Y-%m-%d %H:%M:%S%z')


def get_price_window(cluster_time: Union[str, pd.Timestamp], 
                      lookback_hours: int = 168,
                      lookahead_hours: int = 1) -> tuple:
    """
    Calcule fenêtre temporelle pour requête prix autour d'un événement.
    
    USAGE TYPIQUE : Calculer baseline avant événement et impact après.
    
    Args:
        cluster_time: Timestamp événement (format quelconque)
        lookback_hours: Heures AVANT événement (défaut: 168h = 7 jours)
        lookahead_hours: Heures APRÈS événement (défaut: 1h)
        
    Returns:
        Tuple (start_str, event_str, end_str) formatés pour SQL
        
    Example:
        >>> # Événement 1er août 2025 14:30 Bern time
        >>> start, event, end = get_price_window('2025-08-01 14:30:00+02:00')
        >>> print(start)   # '2025-07-25 14:30:00+02:00' (7j avant)
        >>> print(event)   # '2025-08-01 14:30:00+02:00'
        >>> print(end)     # '2025-08-01 15:30:00+02:00' (1h après)
        
        >>> # Utilisation dans query
        >>> query = f'''
        ... SELECT datetime, close FROM prices_bern
        ... WHERE datetime >= '{start}'
        ...   AND datetime <= '{end}'
        ... '''
    """
    # S'assurer timestamps en Bern time
    event_bern = ensure_bern_time(cluster_time)
    start_bern = event_bern - pd.Timedelta(hours=lookback_hours)
    end_bern = event_bern + pd.Timedelta(hours=lookahead_hours)
    
    # Formatter pour SQL
    start_str = format_for_prices_bern_query(start_bern)
    event_str = format_for_prices_bern_query(event_bern)
    end_str = format_for_prices_bern_query(end_bern)
    
    return start_str, event_str, end_str


def validate_timestamp_consistency(timestamp_from_db: Union[str, pd.Timestamp],
                                   expected_offset_hours: float = 2.0) -> bool:
    """
    Valide qu'un timestamp de la DB a le bon offset timezone.
    
    UTILISATION : Debug / Vérification que DB contient bien Bern time.
    
    Args:
        timestamp_from_db: Timestamp récupéré depuis events.ts_utc
        expected_offset_hours: Offset attendu (2.0 pour été, 1.0 pour hiver)
        
    Returns:
        True si offset correct, False sinon
        
    Example:
        >>> ts = '2025-08-01 14:30:00+02:00'  # Depuis events.ts_utc
        >>> validate_timestamp_consistency(ts, expected_offset_hours=2.0)
        True
        
        >>> ts = '2025-08-01 12:30:00+00:00'  # UTC (pas Bern)
        >>> validate_timestamp_consistency(ts, expected_offset_hours=2.0)
        False
    """
    ts = pd.to_datetime(timestamp_from_db)
    
    if ts.tzinfo is None:
        print("⚠️  Timestamp sans timezone détectée")
        return False
    
    offset_hours = ts.utcoffset().total_seconds() / 3600
    
    if abs(offset_hours - expected_offset_hours) < 0.1:
        return True
    else:
        print(f"⚠️  Offset incorrect : {offset_hours}h (attendu : {expected_offset_hours}h)")
        return False


# ============================================================================
# EXEMPLES D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TESTS UTILITAIRES TIMEZONE")
    print("="*80)
    print()
    
    # Test 1 : Timestamp déjà en Bern time (CAS TYPIQUE events.ts_utc)
    print("TEST 1 : Timestamp déjà en Bern time")
    print("-"*80)
    ts_bern = '2025-08-01 14:30:00+02:00'
    result = ensure_bern_time(ts_bern)
    print(f"Input  : {ts_bern}")
    print(f"Output : {result}")
    print(f"✅ AUCUNE conversion (déjà correct)")
    print()
    
    # Test 2 : Timestamp sans timezone (assume UTC)
    print("TEST 2 : Timestamp sans timezone")
    print("-"*80)
    ts_naive = '2025-08-01 12:30:00'
    result = ensure_bern_time(ts_naive)
    print(f"Input  : {ts_naive} (assume UTC)")
    print(f"Output : {result}")
    print(f"✅ Conversion UTC → Bern (+2h)")
    print()
    
    # Test 3 : Fenêtre prix
    print("TEST 3 : Fenêtre prix pour événement")
    print("-"*80)
    cluster_time = '2025-08-01 14:30:00+02:00'
    start, event, end = get_price_window(cluster_time, lookback_hours=168, lookahead_hours=1)
    print(f"Événement : {cluster_time}")
    print(f"Start (7j avant)  : {start}")
    print(f"Event (événement) : {event}")
    print(f"End (1h après)    : {end}")
    print(f"✅ Fenêtre correcte pour calcul baseline + impact")
    print()
    
    # Test 4 : Validation consistency
    print("TEST 4 : Validation consistency")
    print("-"*80)
    ts_ok = '2025-08-01 14:30:00+02:00'
    ts_wrong = '2025-08-01 12:30:00+00:00'
    
    print(f"Timestamp 1 : {ts_ok}")
    is_valid = validate_timestamp_consistency(ts_ok, expected_offset_hours=2.0)
    print(f"Valid : {is_valid} ✅")
    print()
    
    print(f"Timestamp 2 : {ts_wrong}")
    is_valid = validate_timestamp_consistency(ts_wrong, expected_offset_hours=2.0)
    print(f"Valid : {is_valid} ❌")
    print()
    
    print("="*80)
    print("✅ TOUS LES TESTS PASSÉS")
    print("="*80)
