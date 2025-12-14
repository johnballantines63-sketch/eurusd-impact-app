"""
Core Data Models - EUR/USD Impact Calculator

Ce module contient les modèles de données et patterns pour la classification
des événements économiques.

Version migrée et refactorisée depuis event_families.py

Auteur : Session 29 (Migration clean)
Date : 22 octobre 2025
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class EventFamily:
    """Représente une famille d'événements économiques"""
    
    name: str
    pattern: str
    importance: int  # 1=Low, 2=Medium, 3=High
    sensitivity: float  # pips/écart-type de surprise
    unit: str  # %, K, Index, B
    description: str
    
    def __post_init__(self):
        """Validation après initialisation"""
        if self.importance not in [1, 2, 3]:
            raise ValueError(f"Importance doit être 1, 2 ou 3, pas {self.importance}")
        if self.sensitivity < 0:
            raise ValueError(f"Sensibilité doit être positive, pas {self.sensitivity}")


# ============================================================================
# PATTERNS REGEX FAMILLES D'ÉVÉNEMENTS
# ============================================================================

FAMILY_PATTERNS: Dict[str, str] = {
    # ===== EMPLOI US =====
    'NFP': r'(?i)(non farm payrolls|nonfarm)',
    'Unemployment': r'(?i)(unemployment rate)',
    'Jobless Claims': r'(?i)(initial jobless claims|continuing jobless claims|jobless claims)',
    'Employment Change': r'(?i)(employment change)',
    
    # ===== INFLATION =====
    'CPI': r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)',
    'PPI': r'(?i)(ppi|producer price)',
    'PCE': r'(?i)(pce|personal consumption)',
    
    # ===== BANQUES CENTRALES =====
    'FOMC': r'(?i)(fomc|fed (interest )?rate|federal funds rate)',
    'ECB': r'(?i)(ecb|european central bank rate)',
    'BOE': r'(?i)(boe|bank of england rate)',
    'Fed Rate': r'(?i)(fed interest rate decision)',
    'ECB Rate': r'(?i)(ecb interest rate decision)',
    
    # ===== PIB ET CROISSANCE =====
    'GDP': r'(?i)(gdp|gross domestic product)',
    'Retail Sales': r'(?i)(retail sales)',
    'Industrial Production': r'(?i)(industrial production)',
    
    # ===== CONFIANCE ET SENTIMENT =====
    'Consumer Confidence': r'(?i)(consumer confidence|consumer sentiment)',
    'Business Confidence': r'(?i)(business confidence|zew)',
    'PMI': r'(?i)(pmi|purchasing managers|manufacturing pmi|services pmi)',
    
    # ===== COMMERCE EXTÉRIEUR =====
    'Trade Balance': r'(?i)(trade balance|balance of trade)',
    'Current Account': r'(?i)(current account)',
    
    # ===== IMMOBILIER =====
    'Housing Starts': r'(?i)(housing starts)',
    'Building Permits': r'(?i)(building permits)',
    'Home Sales': r'(?i)(home sales|existing home|new home)',
    
    # ===== AUTRES INDICATEURS =====
    'Durable Goods': r'(?i)(durable goods)',
    'Factory Orders': r'(?i)(factory orders)',
    'ISM': r'(?i)(ism manufacturing|ism services|ism non-manufacturing)',
    
    # ===== MICHIGAN CONSUMER SENTIMENT (Composantes) =====
    'Michigan_Inflation_Expectations': r'(?i)michigan.*inflation.*expectation(?!.*5.*year)',
    'Michigan_5Y_Inflation_Expectations': r'(?i)michigan.*(5|five).*year.*inflation',
    'Michigan_Consumer_Expectations': r'(?i)michigan.*consumer.*expectation',
    'Michigan_Current_Conditions': r'(?i)michigan.*current.*condition',
    
    # ===== AUTRES =====
    'Inflation_Expectations': r'(?i)^inflation.*expectation(?!.*michigan)',
    'Baker_Hughes_Rig_Count': r'(?i)baker.*hughes.*(rig|oil).*count',
    'Federal_Budget': r'(?i)federal.*budget',
    'Monthly_Budget_Statement': r'(?i)monthly.*budget.*statement',
}


# ============================================================================
# IMPORTANCE PAR FAMILLE
# ============================================================================

FAMILY_IMPORTANCE: Dict[str, int] = {
    # ===== HAUTE IMPORTANCE (3) =====
    'NFP': 3,
    'CPI': 3,
    'Unemployment': 3,
    'FOMC': 3,
    'ECB': 3,
    'BOE': 3,
    'Fed Rate': 3,
    'ECB Rate': 3,
    'GDP': 3,
    
    # ===== IMPORTANCE MOYENNE (2) =====
    'Jobless Claims': 2,
    'Employment Change': 2,
    'PPI': 2,
    'PCE': 2,
    'Retail Sales': 2,
    'Consumer Confidence': 2,
    'PMI': 2,
    'Trade Balance': 2,
    'ISM': 2,
    
    # ===== BASSE IMPORTANCE (1) =====
    'Industrial Production': 1,
    'Business Confidence': 1,
    'Current Account': 1,
    'Housing Starts': 1,
    'Building Permits': 1,
    'Home Sales': 1,
    'Durable Goods': 1,
    'Factory Orders': 1,
}


# ============================================================================
# SENSIBILITÉS PAR FAMILLE
# ============================================================================

FAMILY_SENSITIVITIES: Dict[str, float] = {
    # Banques centrales (impact maximum)
    'FOMC': 3.0,
    'Fed Rate': 3.0,
    'ECB': 2.8,
    'ECB Rate': 2.8,
    
    # Emploi US (très fort impact)
    'NFP': 2.5,
    'CPI': 2.3,
    'BOE': 2.2,
    'Unemployment': 2.0,
    
    # Croissance et inflation (impact fort)
    'GDP': 1.8,
    'PCE': 1.7,
    
    # Indicateurs secondaires (impact moyen)
    'Jobless Claims': 1.5,
    'Employment Change': 1.4,
    'Retail Sales': 1.4,
    'PPI': 1.3,
    'ISM': 1.3,
    'PMI': 1.2,
    
    # Indicateurs tertiaires (impact faible)
    'Durable Goods': 1.0,
    'Consumer Confidence': 1.0,
    'Industrial Production': 0.9,
    'Home Sales': 0.9,
    'Trade Balance': 0.8,
    'Factory Orders': 0.8,
    'Housing Starts': 0.8,
    'Business Confidence': 0.7,
    'Building Permits': 0.7,
    'Current Account': 0.6,
}


# ============================================================================
# UNITÉS TYPIQUES PAR FAMILLE
# ============================================================================

FAMILY_UNITS: Dict[str, str] = {
    # Taux en pourcentage
    'Unemployment': '%',
    'CPI': '%',
    'PPI': '%',
    'PCE': '%',
    'FOMC': '%',
    'ECB': '%',
    'BOE': '%',
    'Fed Rate': '%',
    'ECB Rate': '%',
    'GDP': '%',
    'Retail Sales': '%',
    'Industrial Production': '%',
    'Durable Goods': '%',
    'Factory Orders': '%',
    
    # Milliers (K)
    'NFP': 'K',
    'Jobless Claims': 'K',
    'Employment Change': 'K',
    'Housing Starts': 'K',
    'Building Permits': 'K',
    'Home Sales': 'K',
    
    # Milliards (B)
    'Trade Balance': 'B',
    'Current Account': 'B',
    
    # Index
    'Consumer Confidence': 'Index',
    'Business Confidence': 'Index',
    'PMI': 'Index',
    'ISM': 'Index',
}


# ============================================================================
# DESCRIPTIONS LISIBLES
# ============================================================================

FAMILY_DESCRIPTIONS: Dict[str, str] = {
    # Emploi
    'NFP': 'Non-Farm Payrolls (emploi US)',
    'Unemployment': 'Taux de chômage',
    'Jobless Claims': 'Inscriptions chômage hebdomadaire',
    'Employment Change': 'Variation emploi',
    
    # Inflation
    'CPI': 'Indice prix consommateurs + inflation',
    'PPI': 'Prix à la production',
    'PCE': 'Dépenses consommation personnelle',
    
    # Banques centrales
    'FOMC': 'Réunions Fed + décisions taux',
    'ECB': 'Banque Centrale Européenne',
    'BOE': "Banque d'Angleterre",
    'Fed Rate': 'Décisions taux Fed uniquement',
    'ECB Rate': 'Décisions taux BCE uniquement',
    
    # Croissance
    'GDP': 'Produit Intérieur Brut',
    'Retail Sales': 'Ventes au détail',
    'Industrial Production': 'Production industrielle',
    
    # Confiance
    'Consumer Confidence': 'Confiance des consommateurs',
    'Business Confidence': 'Confiance des entreprises',
    'PMI': 'Indices directeurs achats',
    
    # Commerce
    'Trade Balance': 'Balance commerciale',
    'Current Account': 'Compte courant',
    
    # Immobilier
    'Housing Starts': 'Mises en chantier',
    'Building Permits': 'Permis de construire',
    'Home Sales': 'Ventes immobilières',
    
    # Autres
    'Durable Goods': 'Biens durables',
    'Factory Orders': 'Commandes industrielles',
    'ISM': 'Institute for Supply Management',
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_family_info(family_name: str) -> Dict:
    """
    Retourne toutes les informations d'une famille d'événements.
    
    Args:
        family_name: Nom de la famille (ex: 'NFP', 'CPI')
    
    Returns:
        Dict contenant:
            - pattern: Pattern regex
            - importance: 1-3
            - sensitivity: pips/σ
            - unit: Unité ('%', 'K', 'Index', 'B')
            - description: Description lisible
    
    Example:
        >>> info = get_family_info('NFP')
        >>> print(info['description'])
        'Non-Farm Payrolls (emploi US)'
        >>> print(info['importance'])
        3
    """
    return {
        'pattern': FAMILY_PATTERNS.get(family_name, ''),
        'importance': FAMILY_IMPORTANCE.get(family_name, 1),
        'sensitivity': FAMILY_SENSITIVITIES.get(family_name, 1.0),
        'unit': FAMILY_UNITS.get(family_name, ''),
        'description': FAMILY_DESCRIPTIONS.get(family_name, ''),
    }


def create_event_family(family_name: str) -> Optional[EventFamily]:
    """
    Crée un objet EventFamily à partir d'un nom de famille.
    
    Args:
        family_name: Nom de la famille
    
    Returns:
        EventFamily object ou None si famille inconnue
    
    Example:
        >>> nfp = create_event_family('NFP')
        >>> print(f"{nfp.name}: importance {nfp.importance}")
        NFP: importance 3
    """
    if family_name not in FAMILY_PATTERNS:
        return None
    
    info = get_family_info(family_name)
    
    return EventFamily(
        name=family_name,
        pattern=info['pattern'],
        importance=info['importance'],
        sensitivity=info['sensitivity'],
        unit=info['unit'],
        description=info['description']
    )


def get_pattern(family_name: str) -> str:
    """
    Retourne le pattern regex pour une famille.
    
    Args:
        family_name: Nom de la famille
    
    Returns:
        Pattern regex (str), vide si famille inconnue
    """
    return FAMILY_PATTERNS.get(family_name, '')


def get_importance(family_name: str) -> int:
    """
    Retourne l'importance d'une famille (1-3).
    
    Args:
        family_name: Nom de la famille
    
    Returns:
        Importance (1=Low, 2=Medium, 3=High), défaut=1
    """
    return FAMILY_IMPORTANCE.get(family_name, 1)


def get_sensitivity(family_name: str) -> float:
    """
    Retourne la sensibilité d'une famille en pips/σ.
    
    Args:
        family_name: Nom de la famille
    
    Returns:
        Sensibilité (float), défaut=1.0
    """
    return FAMILY_SENSITIVITIES.get(family_name, 1.0)


def list_all_families() -> List[str]:
    """
    Liste toutes les familles disponibles (noms triés).
    
    Returns:
        Liste des noms de familles (sorted)
    
    Example:
        >>> families = list_all_families()
        >>> print(len(families))
        28
        >>> print(families[:3])
        ['Baker_Hughes_Rig_Count', 'BOE', 'Building Permits']
    """
    return sorted(FAMILY_PATTERNS.keys())


def get_families_by_importance(importance: int) -> List[str]:
    """
    Retourne les familles d'une importance donnée.
    
    Args:
        importance: 1 (Low), 2 (Medium), ou 3 (High)
    
    Returns:
        Liste des noms de familles
    
    Example:
        >>> high_impact = get_families_by_importance(3)
        >>> print('NFP' in high_impact)
        True
    """
    return sorted([
        family 
        for family, imp in FAMILY_IMPORTANCE.items() 
        if imp == importance
    ])


def get_high_importance_families() -> List[str]:
    """Retourne les familles haute importance (3)"""
    return get_families_by_importance(3)


def get_medium_importance_families() -> List[str]:
    """Retourne les familles importance moyenne (2)"""
    return get_families_by_importance(2)


def get_low_importance_families() -> List[str]:
    """Retourne les familles basse importance (1)"""
    return get_families_by_importance(1)


def get_all_families() -> Dict[str, str]:
    """
    Retourne toutes les familles avec leurs patterns.
    
    Returns:
        Dict {family_name: regex_pattern}
    
    Example:
        >>> families = get_all_families()
        >>> print(families['CPI'])
        '(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
    """
    return FAMILY_PATTERNS.copy()


# ============================================================================
# CONSTANTES STATISTIQUES
# ============================================================================

# Nombre total de familles définies
N_FAMILIES = len(FAMILY_PATTERNS)

# Statistiques d'importance
N_HIGH_IMPORTANCE = len([f for f in FAMILY_IMPORTANCE.values() if f == 3])
N_MEDIUM_IMPORTANCE = len([f for f in FAMILY_IMPORTANCE.values() if f == 2])
N_LOW_IMPORTANCE = len([f for f in FAMILY_IMPORTANCE.values() if f == 1])


# ============================================================================
# VALIDATION
# ============================================================================

def validate_families() -> Dict[str, List[str]]:
    """
    Valide la cohérence des définitions de familles.
    
    Returns:
        Dict avec:
            - 'missing_importance': Familles sans importance définie
            - 'missing_sensitivity': Familles sans sensibilité définie
            - 'missing_unit': Familles sans unité définie
            - 'missing_description': Familles sans description définie
    
    Example:
        >>> validation = validate_families()
        >>> if any(validation.values()):
        ...     print("⚠️  Certaines familles ont des données manquantes")
    """
    all_families = set(FAMILY_PATTERNS.keys())
    
    return {
        'missing_importance': sorted(all_families - set(FAMILY_IMPORTANCE.keys())),
        'missing_sensitivity': sorted(all_families - set(FAMILY_SENSITIVITIES.keys())),
        'missing_unit': sorted(all_families - set(FAMILY_UNITS.keys())),
        'missing_description': sorted(all_families - set(FAMILY_DESCRIPTIONS.keys()))
    }
