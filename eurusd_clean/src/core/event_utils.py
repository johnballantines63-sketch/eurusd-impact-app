"""
Utilitaires pour normalisation et matching d'événements
========================================================

Fonctions pour normaliser event_keys et améliorer le matching
entre CSV, DB et différents formats.
"""

import re
from typing import List, Set, Optional


def strip_variant_suffix(event_key: str) -> str:
    """
    Enlève les suffixes de variantes (_mom, _yoy, _qoq, etc.)
    
    Args:
        event_key: Clé événement (ex: "cpi_mom", "retail_sales_yoy")
    
    Returns:
        Base sans suffixe (ex: "cpi", "retail_sales")
    """
    suffixes = ['_mom', '_yoy', '_qoq', '_mtd', '_ytd', '_sa', '_nsa']
    
    for suffix in suffixes:
        if event_key.lower().endswith(suffix):
            return event_key[:-len(suffix)]
    
    return event_key


def normalize_event_key_basic(event_key: str) -> str:
    """
    Normalisation basique : lowercase + strip
    
    Args:
        event_key: Clé événement originale
    
    Returns:
        Clé normalisée
    """
    if not event_key:
        return ''
    return event_key.lower().strip()


def normalize_event_key_with_variants(event_key: str) -> str:
    """
    Normalisation avec gestion variantes (_mom, _yoy, etc.)
    
    Enlève les suffixes de variantes pour comparer la base.
    Utile pour matcher "cpi_mom" avec "cpi_yoy" ou "cpi".
    
    Args:
        event_key: Clé événement originale
    
    Returns:
        Base normalisée sans suffixe variante
    """
    normalized = normalize_event_key_basic(event_key)
    base = strip_variant_suffix(normalized)
    return base


def normalize_event_key_flexible(event_key: str) -> str:
    """
    Normalisation flexible : gère espaces, tirets, underscores
    
    Convertit "Non Farm Payrolls", "non-farm-payrolls", "non_farm_payrolls"
    en "nonfarm payrolls" (sans séparateurs).
    
    Args:
        event_key: Clé événement originale
    
    Returns:
        Clé normalisée sans séparateurs
    """
    if not event_key:
        return ''
    
    # Lowercase + strip
    normalized = event_key.lower().strip()
    
    # Remplacer tous séparateurs par espaces
    normalized = re.sub(r'[-_\s]+', ' ', normalized)
    
    # Enlever espaces multiples
    normalized = ' '.join(normalized.split())
    
    # Enlever espaces (pour comparaison exacte)
    normalized = normalized.replace(' ', '')
    
    return normalized


def match_event_keys(
    event_key_source: str,
    event_keys_target: List[str],
    method: str = 'with_variants'
) -> Optional[str]:
    """
    Trouve le meilleur match d'un event_key dans une liste
    
    Args:
        event_key_source: Clé à matcher
        event_keys_target: Liste de clés cibles
        method: Méthode de normalisation ('basic', 'with_variants', 'flexible')
    
    Returns:
        Clé matchée ou None si aucun match
    """
    if method == 'basic':
        normalize_func = normalize_event_key_basic
    elif method == 'with_variants':
        normalize_func = normalize_event_key_with_variants
    elif method == 'flexible':
        normalize_func = normalize_event_key_flexible
    else:
        normalize_func = normalize_event_key_with_variants
    
    source_normalized = normalize_func(event_key_source)
    
    # Essayer match exact d'abord
    for target_key in event_keys_target:
        target_normalized = normalize_func(target_key)
        if source_normalized == target_normalized:
            return target_key
    
    # Essayer match partiel (contient)
    for target_key in event_keys_target:
        target_normalized = normalize_func(target_key)
        if source_normalized in target_normalized or target_normalized in source_normalized:
            return target_key
    
    return None


def normalize_event_keys_list(
    event_keys: List[str],
    method: str = 'with_variants'
) -> List[str]:
    """
    Normalise une liste d'event_keys
    
    Args:
        event_keys: Liste de clés événements
        method: Méthode de normalisation
    
    Returns:
        Liste de clés normalisées
    """
    if method == 'basic':
        normalize_func = normalize_event_key_basic
    elif method == 'with_variants':
        normalize_func = normalize_event_key_with_variants
    elif method == 'flexible':
        normalize_func = normalize_event_key_flexible
    else:
        normalize_func = normalize_event_key_with_variants
    
    return [normalize_func(key) for key in event_keys if key]


def create_event_key_set(
    event_keys: List[str],
    method: str = 'with_variants'
) -> Set[str]:
    """
    Crée un set d'event_keys normalisés pour comparaison Jaccard
    
    Args:
        event_keys: Liste de clés événements
        method: Méthode de normalisation
    
    Returns:
        Set de clés normalisées
    """
    normalized = normalize_event_keys_list(event_keys, method)
    return set(normalized)

