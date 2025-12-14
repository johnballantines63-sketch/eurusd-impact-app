"""
Utilitaires de conversion timezone pour JBlanked API - Session 123

JBlanked API utilise GMT+3 (UTC+3) fixe toute l'année.
Ce module fournit les fonctions de conversion nécessaires pour l'import.

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

from datetime import datetime, timedelta
import pytz
from typing import Optional


# Timezone JBlanked (GMT+3 fixe)
JBLANKED_TIMEZONE = pytz.timezone('Etc/GMT-3')  # Note: signe inversé dans pytz !


def parse_jblanked_timestamp(date_str: str) -> datetime:
    """
    Parser et convertir timestamp JBlanked vers UTC
    
    JBlanked API utilise GMT+3 (UTC+3) fixe toute l'année, sans ajustement DST.
    Cette fonction parse le timestamp et le convertit en UTC timezone-aware.
    
    Args:
        date_str: Timestamp JBlanked format "YYYY.MM.DD HH:MM:SS"
                  Exemple: "2025.08.01 15:30:00"
    
    Returns:
        datetime: Object datetime UTC timezone-aware
    
    Raises:
        ValueError: Si le format du timestamp est incorrect
    
    Example:
        >>> dt_utc = parse_jblanked_timestamp("2025.08.01 15:30:00")
        >>> print(dt_utc)
        2025-08-01 12:30:00+00:00
        >>> dt_utc.hour
        12
        >>> dt_utc.minute
        30
    
    Validation:
        NFP 1er août 2025:
        - JBlanked: 15:30:00 (GMT+3)
        - UTC:      12:30:00 ✅
        - Décalage: -3h (attendu)
    """
    # Parser timestamp
    try:
        dt_naive = datetime.strptime(date_str, "%Y.%m.%d %H:%M:%S")
    except ValueError as e:
        raise ValueError(
            f"Format timestamp incorrect: '{date_str}'. "
            f"Format attendu: 'YYYY.MM.DD HH:MM:SS'. Erreur: {e}"
        )
    
    # Localiser en GMT+3 (timezone JBlanked)
    dt_gmt3 = JBLANKED_TIMEZONE.localize(dt_naive)
    
    # Convertir UTC
    dt_utc = dt_gmt3.astimezone(pytz.UTC)
    
    return dt_utc


def jblanked_to_utc_simple(date_str: str) -> datetime:
    """
    Conversion simple et rapide JBlanked → UTC (soustraction 3h)
    
    Alternative plus rapide à parse_jblanked_timestamp() sans gestion timezone.
    Utilise simple soustraction de 3 heures.
    
    Args:
        date_str: Timestamp JBlanked format "YYYY.MM.DD HH:MM:SS"
    
    Returns:
        datetime: Object datetime UTC timezone-aware
    
    Example:
        >>> dt_utc = jblanked_to_utc_simple("2025.08.01 15:30:00")
        >>> print(dt_utc)
        2025-08-01 12:30:00+00:00
    """
    # Parser
    dt_naive = datetime.strptime(date_str, "%Y.%m.%d %H:%M:%S")
    
    # Soustraire 3 heures
    dt_utc_naive = dt_naive - timedelta(hours=3)
    
    # Ajouter timezone UTC
    dt_utc = pytz.UTC.localize(dt_utc_naive)
    
    return dt_utc


def validate_jblanked_timezone():
    """
    Valider que la conversion timezone fonctionne correctement
    
    Teste les événements de référence du 1er août 2025.
    
    Returns:
        bool: True si validation réussie, False sinon
    
    Raises:
        AssertionError: Si validation échoue
    """
    # Événements test (NFP 1er août 2025)
    test_cases = [
        {
            'name': 'NFP (Non-Farm Employment)',
            'jblanked': '2025.08.01 15:30:00',
            'utc_expected_hour': 12,
            'utc_expected_minute': 30
        },
        {
            'name': 'ISM Manufacturing PMI',
            'jblanked': '2025.08.01 17:00:00',
            'utc_expected_hour': 14,
            'utc_expected_minute': 0
        }
    ]
    
    print("🔍 VALIDATION TIMEZONE JBLANKED → UTC")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  JBlanked: {test['jblanked']}")
        
        # Convertir
        dt_utc = parse_jblanked_timestamp(test['jblanked'])
        
        print(f"  UTC:      {dt_utc}")
        print(f"  Attendu:  {test['utc_expected_hour']:02d}:{test['utc_expected_minute']:02d}:00")
        
        # Valider
        assert dt_utc.hour == test['utc_expected_hour'], \
            f"Heure incorrecte: {dt_utc.hour} != {test['utc_expected_hour']}"
        assert dt_utc.minute == test['utc_expected_minute'], \
            f"Minute incorrecte: {dt_utc.minute} != {test['utc_expected_minute']}"
        
        print(f"  Résultat: ✅ VALIDE")
    
    print("\n" + "=" * 60)
    print("✅ VALIDATION COMPLÈTE RÉUSSIE")
    print()
    
    return True


def convert_jblanked_to_bern(date_str: str) -> datetime:
    """
    Convertir timestamp JBlanked vers timezone Bern (Europe/Zurich)
    
    Utile pour affichage ou comparaison avec prices_bern.
    
    Args:
        date_str: Timestamp JBlanked format "YYYY.MM.DD HH:MM:SS"
    
    Returns:
        datetime: Object datetime timezone Bern (Europe/Zurich)
    
    Example:
        >>> dt_bern = convert_jblanked_to_bern("2025.08.01 15:30:00")
        >>> print(dt_bern)
        2025-08-01 14:30:00+02:00  (CEST en été)
    """
    # Convertir UTC d'abord
    dt_utc = parse_jblanked_timestamp(date_str)
    
    # Convertir Bern
    tz_bern = pytz.timezone('Europe/Zurich')
    dt_bern = dt_utc.astimezone(tz_bern)
    
    return dt_bern


if __name__ == '__main__':
    # Exécuter validation si script lancé directement
    validate_jblanked_timezone()
    
    # Exemples d'utilisation
    print("\n📝 EXEMPLES D'UTILISATION")
    print("=" * 60)
    
    # NFP 1er août 2025
    jb_timestamp = "2025.08.01 15:30:00"
    
    print(f"\nTimestamp JBlanked : {jb_timestamp}")
    
    # Conversion UTC
    dt_utc = parse_jblanked_timestamp(jb_timestamp)
    print(f"UTC                : {dt_utc}")
    
    # Conversion Bern
    dt_bern = convert_jblanked_to_bern(jb_timestamp)
    print(f"Bern (CEST)        : {dt_bern}")
    
    # Conversion simple
    dt_utc_simple = jblanked_to_utc_simple(jb_timestamp)
    print(f"UTC (simple)       : {dt_utc_simple}")
    
    # Vérifier équivalence
    assert dt_utc == dt_utc_simple, "Méthodes devraient donner même résultat"
    print(f"\n✅ Conversions validées identiques")
