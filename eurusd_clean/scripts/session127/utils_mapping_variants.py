#!/usr/bin/env python3
"""
SESSION 127 - EXTENSION UTILS_MAPPING AVEC VARIANTES (CORRIGÉE)
================================================================
Extension utils_mapping.py Session 126 avec support variantes

Nouveau : Mapping 49 variantes (MoM/YoY/QoQ/Advance)
Correction : strip_variant_suffix() pour mapper DB → CSV scores

Auteur : André Valentin
Date : 11 novembre 2025
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple


# ============================================================================
# CHARGEMENT TABLE MAPPING VARIANTES (Session 127)
# ============================================================================

def load_variant_mapping() -> pd.DataFrame:
    """
    Charger table mapping variantes Session 127
    
    Returns:
        DataFrame avec colonnes :
        - event_name (CSV)
        - event_key_principal (DB)
        - empirical_score
        - importance
    """
    mapping_path = Path(__file__).parent / 'event_mapping_rules_complete.csv'
    
    if not mapping_path.exists():
        # Fallback : chercher dans parent
        mapping_path = Path(__file__).parents[1] / 'session127' / 'event_mapping_rules_complete.csv'
    
    if not mapping_path.exists():
        raise FileNotFoundError(
            f"Table mapping variantes introuvable : {mapping_path}\n"
            "Assurez-vous que event_mapping_rules_complete.csv existe."
        )
    
    return pd.read_csv(mapping_path)


# ============================================================================
# STRIP SUFFIXES VARIANTES (Session 127 - CORRECTION)
# ============================================================================

def strip_variant_suffix(event_name: str) -> str:
    """
    Retirer suffixes variantes pour chercher score base dans CSV
    
    Problème résolu :
    - DB events a : 'inflation rate_mom', 'gdp growth rate_qoq', etc.
    - CSV scores a : 'inflation_rate', 'gdp_growth_rate', etc. (BASE uniquement)
    
    Cette fonction strip les suffixes pour mapper event_key → event_name_base
    
    Args:
        event_name: Nom événement avec potentiel suffixe (ex: 'inflation_rate_mom')
    
    Returns:
        Nom événement BASE sans suffixe (ex: 'inflation_rate')
    
    Examples:
        >>> strip_variant_suffix('inflation_rate_mom')
        'inflation_rate'
        >>> strip_variant_suffix('gdp_growth_rate_qoq')
        'gdp_growth_rate'
        >>> strip_variant_suffix('retail_sales_yoy')
        'retail_sales'
        >>> strip_variant_suffix('gdp_sales_qoq_adv')
        'gdp_sales'
        >>> strip_variant_suffix('cpi')
        'cpi'
    
    Notes:
        - Ordre des suffixes important : tester les plus longs d'abord
        - _qoq_adv avant _qoq pour éviter strip partiel
    """
    # Suffixes possibles (ordre important : plus long → plus court)
    suffixes = [
        '_qoq_adv',  # 8 caractères - Le plus long
        '_mom',      # 4 caractères
        '_yoy',      # 4 caractères
        '_qoq',      # 4 caractères
        ' mom',      # Avec espace (au cas où)
        ' yoy',
        ' qoq'
    ]
    
    # Tester chaque suffixe
    for suffix in suffixes:
        if event_name.endswith(suffix):
            return event_name[:-len(suffix)]
    
    # Pas de suffixe trouvé, retourner tel quel
    return event_name


# ============================================================================
# MAPPING EVENT_NAME → EVENT_KEY AVEC VARIANTES
# ============================================================================

def map_event_name_to_key_variant(
    event_name: str,
    df_mapping: Optional[pd.DataFrame] = None
) -> Optional[str]:
    """
    Mapper event_name (CSV) → event_key principal (DB) avec support variantes
    
    Gère 3 cas :
    1. Mapping direct (ex: 'cpi' → 'cpi')
    2. Mapping variante (ex: 'inflation_rate' → 'inflation rate_mom')
    3. Doublon résolu (ex: 'gross_domestic_product' → 'gdp growth rate_qoq')
    
    Args:
        event_name: Nom événement CSV (ex: 'inflation_rate')
        df_mapping: DataFrame mapping (optionnel, chargé auto si None)
    
    Returns:
        event_key principal DB ou None si introuvable
    
    Examples:
        >>> map_event_name_to_key_variant('inflation_rate')
        'inflation rate_mom'
        >>> map_event_name_to_key_variant('gross_domestic_product')
        'gdp growth rate_qoq'
        >>> map_event_name_to_key_variant('cpi')
        None
    """
    # Charger mapping si non fourni
    if df_mapping is None:
        try:
            df_mapping = load_variant_mapping()
        except FileNotFoundError:
            # Fallback : pas de mapping variantes disponible
            return None
    
    # Chercher mapping
    match = df_mapping[df_mapping['event_name'] == event_name]
    
    if len(match) > 0:
        return match.iloc[0]['event_key_principal']
    else:
        return None


# ============================================================================
# FONCTION PRINCIPALE : GET_SCORE AVEC VARIANTES (CORRIGÉE)
# ============================================================================

def get_empirical_score_with_variants(
    event_key: str,
    country_code: str,
    df_scores: pd.DataFrame,
    df_mapping: Optional[pd.DataFrame] = None,
    verbose: bool = False
) -> Tuple[Optional[float], str]:
    """
    Récupérer score empirique avec support mapping variantes (VERSION CORRIGÉE)
    
    Workflow :
    1. Normaliser event_key → event_name (espaces → underscores)
    2. Chercher mapping variante (Session 127)
    3. Si trouvé : utiliser event_key_principal
    4. Sinon : utiliser event_key normalisé direct
    5. **STRIP suffixe variante** (_mom, _yoy, _qoq)
    6. Chercher score dans CSV
    
    Args:
        event_key: Clé événement table events (ex: 'retail sales')
        country_code: Code pays table events (ex: 'US')
        df_scores: DataFrame scores (event_families_eodhd_empirical.csv)
        df_mapping: DataFrame mapping variantes (optionnel)
        verbose: Afficher détails recherche (debug)
    
    Returns:
        Tuple (score, source) :
        - score: float ou None
        - source: 'direct' | 'variant' | 'not_found'
    
    Examples:
        >>> df_scores = pd.read_csv('event_families_eodhd_empirical.csv')
        >>> get_empirical_score_with_variants('inflation rate', 'US', df_scores)
        (48.84, 'variant')  # Mapped via inflation rate_mom
        
        >>> get_empirical_score_with_variants('cpi', 'US', df_scores)
        (45.48, 'direct')  # Direct match
    """
    # Import ici pour éviter circular imports
    import sys
    from pathlib import Path
    
    # Ajouter session126 au path pour importer utils_mapping
    session126_path = Path(__file__).parents[1] / 'session126'
    if str(session126_path) not in sys.path:
        sys.path.insert(0, str(session126_path))
    
    from utils_mapping import (
        normalize_event_key_to_name,
        map_country_to_currency
    )
    
    # Étape 1 : Normaliser event_key → event_name
    event_name = normalize_event_key_to_name(event_key)
    currency_code = map_country_to_currency(country_code)
    
    if verbose:
        print(f"[DEBUG] event_key='{event_key}' → event_name='{event_name}'")
        print(f"[DEBUG] country='{country_code}' → currency='{currency_code}'")
    
    # Étape 2 : Chercher mapping variante
    event_key_principal = map_event_name_to_key_variant(event_name, df_mapping)
    
    source_type = 'direct'  # Par défaut
    
    if event_key_principal:
        # Mapping variante trouvé
        if verbose:
            print(f"[DEBUG] Mapping variante : '{event_name}' → '{event_key_principal}'")
        
        # Utiliser event_key_principal pour recherche
        event_name_search = normalize_event_key_to_name(event_key_principal)
        source_type = 'variant'
    else:
        # Pas de mapping, utiliser direct
        if verbose:
            print(f"[DEBUG] Pas de mapping variante, recherche directe")
        
        event_name_search = event_name
    
    if verbose:
        print(f"[DEBUG] event_name_search (avant strip) : '{event_name_search}'")
    
    # Étape 3 : **STRIP SUFFIXE VARIANTE** (CORRECTION Session 127)
    event_name_base = strip_variant_suffix(event_name_search)
    
    if verbose:
        print(f"[DEBUG] event_name_base (après strip) : '{event_name_base}'")
    
    # Étape 4 : Chercher dans CSV scores
    score_row = df_scores[
        (df_scores['event_name'] == event_name_base) & 
        (df_scores['country'] == currency_code)
    ]
    
    if len(score_row) > 0:
        score = float(score_row.iloc[0]['empirical_score'])
        if verbose:
            print(f"[DEBUG] Score trouvé : {score:.2f} (source: {source_type})")
        return (score, source_type)
    else:
        if verbose:
            print(f"[DEBUG] Score introuvable")
        return (None, 'not_found')


# ============================================================================
# FONCTION HELPER : LISTER TOUTES LES VARIANTES
# ============================================================================

def get_all_variants_for_event(event_name: str, df_mapping: Optional[pd.DataFrame] = None) -> dict:
    """
    Récupérer toutes les informations de mapping pour un event_name
    
    Args:
        event_name: Nom événement CSV
        df_mapping: DataFrame mapping (optionnel)
    
    Returns:
        {
            'event_name': str,
            'event_key_principal': str,
            'empirical_score': float,
            'importance': str,
            'num_variants': int,
            'justification': str,
            'all_variants': str
        }
        ou None si introuvable
    """
    if df_mapping is None:
        try:
            df_mapping = load_variant_mapping()
        except FileNotFoundError:
            return None
    
    match = df_mapping[df_mapping['event_name'] == event_name]
    
    if len(match) > 0:
        return match.iloc[0].to_dict()
    else:
        return None


# ============================================================================
# VALIDATION : TESTER MAPPING COMPLET
# ============================================================================

def validate_variant_mapping(
    event_key: str,
    country_code: str,
    df_scores: pd.DataFrame,
    df_mapping: Optional[pd.DataFrame] = None
) -> dict:
    """
    Valider mapping complet avec variantes (debug détaillé)
    
    Returns:
        {
            'event_key': str,
            'event_name': str,
            'event_key_principal': str ou None,
            'score': float ou None,
            'source': 'direct' | 'variant' | 'not_found',
            'variant_info': dict ou None
        }
    """
    import sys
    from pathlib import Path
    
    session126_path = Path(__file__).parents[1] / 'session126'
    if str(session126_path) not in sys.path:
        sys.path.insert(0, str(session126_path))
    
    from utils_mapping import normalize_event_key_to_name, map_country_to_currency
    
    event_name = normalize_event_key_to_name(event_key)
    currency_code = map_country_to_currency(country_code)
    
    # Chercher mapping variante
    event_key_principal = map_event_name_to_key_variant(event_name, df_mapping)
    
    # Récupérer score
    score, source = get_empirical_score_with_variants(
        event_key, country_code, df_scores, df_mapping
    )
    
    # Récupérer infos variantes
    variant_info = get_all_variants_for_event(event_name, df_mapping) if event_key_principal else None
    
    return {
        'event_key': event_key,
        'event_name': event_name,
        'country_code': country_code,
        'currency_code': currency_code,
        'event_key_principal': event_key_principal,
        'score': score,
        'source': source,
        'variant_info': variant_info
    }


# ============================================================================
# TESTS UNITAIRES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TESTS UNITAIRES - UTILS_MAPPING_VARIANTS (SESSION 127 - CORRIGÉ)")
    print("=" * 80)
    print()
    
    # Test fonction strip_variant_suffix
    print("[TEST 1] strip_variant_suffix()")
    print("-" * 80)
    
    test_cases_strip = [
        ('inflation_rate_mom', 'inflation_rate'),
        ('gdp_growth_rate_qoq', 'gdp_growth_rate'),
        ('retail_sales_yoy', 'retail_sales'),
        ('gdp_sales_qoq_adv', 'gdp_sales'),
        ('cpi', 'cpi'),
        ('ppi_mom', 'ppi')
    ]
    
    for input_name, expected in test_cases_strip:
        result = strip_variant_suffix(input_name)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{input_name}' → '{result}' (attendu: '{expected}')")
    
    print()
    print()
    
    # Charger données pour tests complets
    from pathlib import Path
    
    scores_path = Path(__file__).parents[1] / "session123" / "validation_results" / "event_families_eodhd_empirical.csv"
    
    if not scores_path.exists():
        print(f"❌ Fichier scores introuvable : {scores_path}")
        print("   Tests complets annulés.")
        exit(1)
    
    df_scores = pd.read_csv(scores_path)
    
    try:
        df_mapping = load_variant_mapping()
        print(f"✅ Mapping variantes chargé : {len(df_mapping)} lignes\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("   Tests complets annulés.")
        exit(1)
    
    # Test 2 : Cas avec variante (inflation_rate)
    print("[TEST 2] Mapping variante : inflation_rate")
    print("-" * 80)
    
    score, source = get_empirical_score_with_variants('inflation rate', 'US', df_scores, df_mapping, verbose=True)
    print(f"\n  Résultat : score={score}, source={source}")
    
    if score and abs(score - 48.84) < 1.0:
        print("  ✅ Score correct !")
    else:
        print(f"  ❌ Score incorrect (attendu ~48.84)")
    
    print()
    
    # Test 3 : Cas direct (cpi)
    print("[TEST 3] Mapping direct : cpi")
    print("-" * 80)
    
    score, source = get_empirical_score_with_variants('cpi', 'US', df_scores, df_mapping, verbose=True)
    print(f"\n  Résultat : score={score}, source={source}")
    
    if score and abs(score - 45.48) < 1.0:
        print("  ✅ Score correct !")
    else:
        print(f"  ❌ Score incorrect (attendu ~45.48)")
    
    print()
    
    # Test 4 : GDP avec variante
    print("[TEST 4] GDP avec variante : gdp growth rate_qoq")
    print("-" * 80)
    
    score, source = get_empirical_score_with_variants('gdp growth rate', 'US', df_scores, df_mapping, verbose=True)
    print(f"\n  Résultat : score={score}, source={source}")
    
    if score and abs(score - 38.52) < 1.0:
        print("  ✅ Score correct !")
    else:
        print(f"  ❌ Score incorrect (attendu ~38.52)")
    
    print()
    print("=" * 80)
    print("TESTS TERMINÉS")
    print("=" * 80)
