"""
Définition des familles d'événements économiques
Patterns regex pour classification et importance par famille
Version complète avec sensibilités calibrées
"""

# Patterns de reconnaissance des familles d'événements (case insensitive)
FAMILY_PATTERNS = {
    # Emploi US
    'NFP': '(?i)(non farm payrolls|nonfarm)',
    'Unemployment': '(?i)(unemployment rate)',
    'Jobless Claims': '(?i)(initial jobless claims|continuing jobless claims|jobless claims)',
    'Employment Change': '(?i)(employment change)',
    
    # Inflation (fusionné CPI + Inflation + variantes)
    'CPI': '(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)',
    'PPI': '(?i)(ppi|producer price)',
    'PCE': '(?i)(pce|personal consumption)',
    
    # Banques centrales
    'FOMC': '(?i)(fomc|fed (interest )?rate|federal funds rate)',
    'ECB': '(?i)(ecb|european central bank rate)',
    'BOE': '(?i)(boe|bank of england rate)',
    'Fed Rate': '(?i)(fed interest rate decision)',
    'ECB Rate': '(?i)(ecb interest rate decision)',
    
    # PIB et croissance
    'GDP': '(?i)(gdp|gross domestic product)',
    'Retail Sales': '(?i)(retail sales)',
    'Industrial Production': '(?i)(industrial production)',
    
    # Confiance et sentiment
    'Consumer Confidence': '(?i)(consumer confidence|consumer sentiment)',
    'Business Confidence': '(?i)(business confidence|zew)',
    'PMI': '(?i)(pmi|purchasing managers|manufacturing pmi|services pmi)',
    
    # Commerce extérieur
    'Trade Balance': '(?i)(trade balance|balance of trade)',
    'Current Account': '(?i)(current account)',
    
    # Immobilier
    'Housing Starts': '(?i)(housing starts)',
    'Building Permits': '(?i)(building permits)',
    'Home Sales': '(?i)(home sales|existing home|new home)',
    
    # Autres indicateurs importants
    'Durable Goods': '(?i)(durable goods)',
    'Factory Orders': '(?i)(factory orders)',
    'ISM': '(?i)(ism manufacturing|ism services|ism non-manufacturing)',
}

# Importance par défaut de chaque famille (1=Low, 2=Medium, 3=High)
FAMILY_IMPORTANCE = {
    # Haute importance (3)
    'NFP': 3,
    'CPI': 3,
    'Unemployment': 3,
    'FOMC': 3,
    'ECB': 3,
    'BOE': 3,
    'Fed Rate': 3,
    'ECB Rate': 3,
    'GDP': 3,
    
    # Importance moyenne (2)
    'Jobless Claims': 2,
    'Employment Change': 2,
    'PPI': 2,
    'PCE': 2,
    'Retail Sales': 2,
    'Consumer Confidence': 2,
    'PMI': 2,
    'Trade Balance': 2,
    'ISM': 2,
    
    # Importance basse (1)
    'Industrial Production': 1,
    'Business Confidence': 1,
    'Current Account': 1,
    'Housing Starts': 1,
    'Building Permits': 1,
    'Home Sales': 1,
    'Durable Goods': 1,
    'Factory Orders': 1,
}

# Sensibilités par défaut (pips/écart-type de surprise)
# Calibrées sur historique EUR/USD
FAMILY_SENSITIVITIES = {
    'NFP': 2.5,              # Très fort impact
    'CPI': 2.3,
    'Unemployment': 2.0,
    'FOMC': 3.0,             # Maximum impact
    'ECB': 2.8,
    'BOE': 2.2,
    'Fed Rate': 3.0,
    'ECB Rate': 2.8,
    'GDP': 1.8,
    'Jobless Claims': 1.5,
    'Employment Change': 1.4,
    'PPI': 1.3,
    'PCE': 1.7,
    'Retail Sales': 1.4,
    'Consumer Confidence': 1.0,
    'PMI': 1.2,
    'Trade Balance': 0.8,
    'ISM': 1.3,
    'Industrial Production': 0.9,
    'Business Confidence': 0.7,
    'Current Account': 0.6,
    'Housing Starts': 0.8,
    'Building Permits': 0.7,
    'Home Sales': 0.9,
    'Durable Goods': 1.0,
    'Factory Orders': 0.8,
}

# Unités typiques par famille (pour validation)
FAMILY_UNITS = {
    'NFP': 'K',
    'Unemployment': '%',
    'Jobless Claims': 'K',
    'Employment Change': 'K',
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
    'Consumer Confidence': 'Index',
    'Business Confidence': 'Index',
    'PMI': 'Index',
    'Trade Balance': 'B',
    'Current Account': 'B',
    'ISM': 'Index',
    'Housing Starts': 'K',
    'Building Permits': 'K',
    'Home Sales': 'K',
    'Durable Goods': '%',
    'Factory Orders': '%',
}

# Descriptions pour l'UI
FAMILY_DESCRIPTIONS = {
    'NFP': 'Non-Farm Payrolls (emploi US)',
    'Unemployment': 'Taux de chômage',
    'Jobless Claims': 'Inscriptions chômage hebdo',
    'Employment Change': 'Variation emploi',
    'CPI': 'Indice prix consommateurs + inflation',
    'PPI': 'Prix à la production',
    'PCE': 'Dépenses consommation personnelle',
    'FOMC': 'Réunions Fed + décisions taux',
    'ECB': 'Banque Centrale Européenne',
    'BOE': 'Banque d\'Angleterre',
    'Fed Rate': 'Décisions taux Fed uniquement',
    'ECB Rate': 'Décisions taux BCE uniquement',
    'GDP': 'Produit Intérieur Brut',
    'Retail Sales': 'Ventes au détail',
    'Industrial Production': 'Production industrielle',
    'Consumer Confidence': 'Confiance des consommateurs',
    'Business Confidence': 'Confiance des entreprises',
    'PMI': 'Indices directeurs achats',
    'Trade Balance': 'Balance commerciale',
    'Current Account': 'Compte courant',
    'Housing Starts': 'Mises en chantier',
    'Building Permits': 'Permis de construire',
    'Home Sales': 'Ventes immobilières',
    'Durable Goods': 'Biens durables',
    'Factory Orders': 'Commandes industrielles',
    'ISM': 'Institute for Supply Management',
}

def get_family_info(family_name):
    """
    Retourne toutes les infos d'une famille
    
    Args:
        family_name: Nom de la famille
        
    Returns:
        dict avec pattern, importance, sensibilité, unité, description
    """
    return {
        'pattern': FAMILY_PATTERNS.get(family_name, ''),
        'importance': FAMILY_IMPORTANCE.get(family_name, 1),
        'sensitivity': FAMILY_SENSITIVITIES.get(family_name, 1.0),
        'unit': FAMILY_UNITS.get(family_name, ''),
        'description': FAMILY_DESCRIPTIONS.get(family_name, ''),
    }

def get_pattern(family_name):
    """Retourne le pattern regex pour une famille"""
    return FAMILY_PATTERNS.get(family_name, '')

def get_importance(family_name):
    """Retourne l'importance d'une famille (1-3)"""
    return FAMILY_IMPORTANCE.get(family_name, 2)

def get_all_families():
    """Retourne toutes les familles disponibles"""
    return FAMILY_PATTERNS

def list_all_families():
    """Liste toutes les familles disponibles (noms)"""
    return sorted(FAMILY_PATTERNS.keys())

def get_high_importance_families():
    """Retourne les familles haute importance (3)"""
    return [f for f, imp in FAMILY_IMPORTANCE.items() if imp == 3]

def get_medium_importance_families():
    """Retourne les familles importance moyenne (2)"""
    return [f for f, imp in FAMILY_IMPORTANCE.items() if imp == 2]

def get_low_importance_families():
    """Retourne les familles basse importance (1)"""
    return [f for f, imp in FAMILY_IMPORTANCE.items() if imp == 1]
