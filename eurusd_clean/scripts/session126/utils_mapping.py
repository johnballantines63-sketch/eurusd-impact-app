#!/usr/bin/env python3
"""
SESSION 126 - FONCTIONS UTILITAIRES MAPPING
============================================
Fonctions normalisation pour mapping event_key ↔ scores

Basé sur : Réponses Session 125 (Question 3)

Problème résolu :
- Table events      : event_key='retail sales', country='US'
- Fichier scores    : event_name='retail_sales', country='usd'
"""
import pandas as pd
from typing import Optional


# ============================================================================
# MAPPING COUNTRY → CURRENCY
# ============================================================================

# Mapping code PAYS → code DEVISE
COUNTRY_TO_CURRENCY = {
    'US': 'usd',   # États-Unis → Dollar
    'GB': 'gbp',   # Royaume-Uni → Livre
    'JP': 'jpy',   # Japon → Yen
    'CH': 'chf',   # Suisse → Franc
    'DE': 'eur',   # Allemagne → Euro
    'FR': 'eur',   # France → Euro
    'IT': 'eur',   # Italie → Euro
    'ES': 'eur',   # Espagne → Euro
    'CA': 'cad',   # Canada → Dollar canadien
    'AU': 'aud',   # Australie → Dollar australien
    'NZ': 'nzd',   # Nouvelle-Zélande → Dollar néo-zélandais
}


def map_country_to_currency(country_code: str) -> str:
    """
    Convertir code PAYS (majuscules) → code DEVISE (minuscules)
    
    Args:
        country_code: Code pays (ex: 'US', 'GB', 'JP')
    
    Returns:
        Code devise (ex: 'usd', 'gbp', 'jpy')
    
    Examples:
        >>> map_country_to_currency('US')
        'usd'
        >>> map_country_to_currency('GB')
        'gbp'
        >>> map_country_to_currency('DE')
        'eur'
    """
    return COUNTRY_TO_CURRENCY.get(country_code, country_code.lower())


# ============================================================================
# NORMALISATION EVENT_KEY → EVENT_NAME
# ============================================================================

def normalize_event_key_to_name(event_key: str) -> str:
    """
    Convertir event_key (espaces) → event_name (underscores)
    
    Règle : Remplacer espaces par underscores
    
    Args:
        event_key: Clé événement table events (ex: 'retail sales')
    
    Returns:
        Nom événement fichier scores (ex: 'retail_sales')
    
    Examples:
        >>> normalize_event_key_to_name('retail sales')
        'retail_sales'
        >>> normalize_event_key_to_name('fed interest rate decision')
        'fed_interest_rate_decision'
        >>> normalize_event_key_to_name('non farm payrolls')
        'non_farm_payrolls'
    """
    return event_key.replace(' ', '_')


# ============================================================================
# RÉCUPÉRATION SCORE EMPIRIQUE (wrapper tout-en-un)
# ============================================================================

def get_empirical_score(
    event_key: str,
    country_code: str,
    df_scores: pd.DataFrame
) -> Optional[float]:
    """
    Récupérer score empirique avec mapping automatique
    
    Gère automatiquement :
    - Conversion event_key (espaces) → event_name (underscores)
    - Conversion country_code (majuscules) → currency (minuscules)
    - Recherche dans DataFrame scores
    
    Args:
        event_key: Clé événement table events (ex: 'retail sales')
        country_code: Code pays table events (ex: 'US')
        df_scores: DataFrame scores (event_families_eodhd_empirical.csv)
    
    Returns:
        Score empirique (float) ou None si introuvable
    
    Examples:
        >>> df_scores = pd.read_csv('event_families_eodhd_empirical.csv')
        >>> get_empirical_score('retail sales', 'US', df_scores)
        45.2
        >>> get_empirical_score('non farm payrolls', 'US', df_scores)
        61.6
    
    Notes:
        - Retourne None si event_name ou country introuvable
        - Affiche warning si score manquant (optionnel debug)
    """
    # Normaliser event_key → event_name
    event_name = normalize_event_key_to_name(event_key)
    
    # Convertir country → currency
    currency_code = map_country_to_currency(country_code)
    
    # Chercher dans scores
    score_row = df_scores[
        (df_scores['event_name'] == event_name) & 
        (df_scores['country'] == currency_code)
    ]
    
    if len(score_row) > 0:
        return float(score_row.iloc[0]['empirical_score'])
    else:
        # Score introuvable
        return None


# ============================================================================
# FONCTION AJUSTEMENT SURPRISE (Session 125)
# ============================================================================

def calculate_adjusted_empirical_score(base_score: float, surprise_pct: float) -> float:
    """
    Ajuster score empirique selon magnitude surprise
    
    Règles Session 125 :
    - surprise ≤ 10%  : score × 1.00 (pas d'ajustement)
    - surprise ≤ 20%  : score × 1.15 (+15%)
    - surprise > 20%  : score × 1.30 (+30%)
    
    Args:
        base_score: Score empirique de base
        surprise_pct: Magnitude surprise en % = |actual - estimate| / |estimate| × 100
    
    Returns:
        Score ajusté
    
    Examples:
        >>> calculate_adjusted_empirical_score(50.0, 5.0)
        50.0
        >>> calculate_adjusted_empirical_score(50.0, 15.0)
        57.5
        >>> calculate_adjusted_empirical_score(50.0, 25.0)
        65.0
    """
    if surprise_pct <= 10:
        return base_score
    elif surprise_pct <= 20:
        return base_score * 1.15
    else:
        return base_score * 1.30


# ============================================================================
# CALCUL SURPRISE % (helper)
# ============================================================================

def calculate_surprise_pct(actual: float, estimate: float) -> float:
    """
    Calculer magnitude surprise en %
    
    Formule : |actual - estimate| / |estimate| × 100
    
    Args:
        actual: Valeur réelle publiée
        estimate: Valeur estimée/consensus
    
    Returns:
        Surprise en % (toujours positif)
    
    Examples:
        >>> calculate_surprise_pct(150000, 140000)  # NFP
        7.14
        >>> calculate_surprise_pct(3.5, 3.0)  # CPI %
        16.67
    
    Notes:
        - Retourne 0 si estimate = 0 (évite division par zéro)
        - Retourne 0 si actual ou estimate = None/NaN
    """
    # Vérifier valeurs valides
    if pd.isna(actual) or pd.isna(estimate) or estimate == 0:
        return 0.0
    
    # Calcul surprise
    surprise = abs((actual - estimate) / estimate) * 100
    
    return surprise


# ============================================================================
# VALIDATION / DEBUG
# ============================================================================

def validate_mapping(event_key: str, country_code: str, df_scores: pd.DataFrame) -> dict:
    """
    Valider mapping complet event_key → score (debug)
    
    Args:
        event_key: 'retail sales'
        country_code: 'US'
        df_scores: DataFrame scores
    
    Returns:
        {
            'event_key': 'retail sales',
            'event_name': 'retail_sales',
            'country_code': 'US',
            'currency_code': 'usd',
            'score_found': True/False,
            'empirical_score': 45.2 ou None
        }
    """
    event_name = normalize_event_key_to_name(event_key)
    currency_code = map_country_to_currency(country_code)
    score = get_empirical_score(event_key, country_code, df_scores)
    
    return {
        'event_key': event_key,
        'event_name': event_name,
        'country_code': country_code,
        'currency_code': currency_code,
        'score_found': score is not None,
        'empirical_score': score
    }


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS UNITAIRES - UTILS_MAPPING")
    print("=" * 80)
    print()
    
    # Test 1 : Mapping country → currency
    print("[TEST 1] map_country_to_currency()")
    print("-" * 80)
    
    test_countries = [
        ('US', 'usd'),
        ('GB', 'gbp'),
        ('JP', 'jpy'),
        ('DE', 'eur'),
        ('CH', 'chf')
    ]
    
    for country, expected in test_countries:
        result = map_country_to_currency(country)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{country}' → '{result}' (attendu: '{expected}')")
    
    print()
    
    # Test 2 : Normalisation event_key → event_name
    print("[TEST 2] normalize_event_key_to_name()")
    print("-" * 80)
    
    test_events = [
        ('retail sales', 'retail_sales'),
        ('fed interest rate decision', 'fed_interest_rate_decision'),
        ('non farm payrolls', 'non_farm_payrolls'),
        ('cpi', 'cpi')
    ]
    
    for event_key, expected in test_events:
        result = normalize_event_key_to_name(event_key)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{event_key}' → '{result}'")
    
    print()
    
    # Test 3 : Ajustement surprise
    print("[TEST 3] calculate_adjusted_empirical_score()")
    print("-" * 80)
    
    base_score = 50.0
    test_surprises = [
        (5.0, 50.0),    # ≤10% → ×1.00
        (15.0, 57.5),   # ≤20% → ×1.15
        (25.0, 65.0)    # >20% → ×1.30
    ]
    
    for surprise, expected in test_surprises:
        result = calculate_adjusted_empirical_score(base_score, surprise)
        status = "✅" if abs(result - expected) < 0.01 else "❌"
        print(f"  {status} base={base_score}, surprise={surprise}% → {result:.1f} (attendu: {expected:.1f})")
    
    print()
    
    # Test 4 : Calcul surprise %
    print("[TEST 4] calculate_surprise_pct()")
    print("-" * 80)
    
    test_surprise_calc = [
        (150000, 140000, 7.14),  # NFP
        (3.5, 3.0, 16.67),       # CPI
        (100, 100, 0.0),         # Pas de surprise
    ]
    
    for actual, estimate, expected in test_surprise_calc:
        result = calculate_surprise_pct(actual, estimate)
        status = "✅" if abs(result - expected) < 0.1 else "❌"
        print(f"  {status} actual={actual}, estimate={estimate} → {result:.2f}% (attendu: {expected:.2f}%)")
    
    print()
    
    # Test 5 : Mapping complet (nécessite CSV)
    print("[TEST 5] get_empirical_score() - Nécessite CSV")
    print("-" * 80)
    
    from pathlib import Path
    scores_path = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    
    if scores_path.exists():
        df_scores = pd.read_csv(scores_path)
        
        test_mappings = [
            ('non farm payrolls', 'US'),
            ('retail sales', 'US'),
            ('fed interest rate decision', 'US')
        ]
        
        for event_key, country in test_mappings:
            score = get_empirical_score(event_key, country, df_scores)
            status = "✅" if score is not None else "❌"
            score_str = f"{score:.2f}" if score else "INTROUVABLE"
            print(f"  {status} '{event_key}' (US) → score={score_str}")
    else:
        print(f"  ⚠️  Fichier scores introuvable : {scores_path}")
    
    print()
    print("=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
