"""
Module normalisation - Mapping JBlanked + EODHD vers structure master

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123 - Double source
"""

from datetime import datetime, timedelta
import re

# ============================================================================
# MAPPINGS STANDARDISÉS
# ============================================================================

# Mapping codes pays 2 lettres → 3 lettres
COUNTRY_MAPPING = {
    'US': 'USD', 'GB': 'GBP', 'EU': 'EUR', 'DE': 'EUR',
    'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
    'CH': 'CHF', 'CA': 'CAD', 'JP': 'JPY',
    'AU': 'AUD', 'NZ': 'NZD', 'UK': 'GBP',
    'CN': 'CNY', 'IN': 'INR', 'BR': 'BRL',
    'MX': 'MXN', 'ZA': 'ZAR', 'SE': 'SEK',
    'NO': 'NOK', 'DK': 'DKK',
    # Déjà 3 lettres
    'USD': 'USD', 'GBP': 'GBP', 'EUR': 'EUR',
    'CHF': 'CHF', 'CAD': 'CAD', 'JPY': 'JPY',
    'AUD': 'AUD', 'NZD': 'NZD'
}

# Mapping noms événements → standardisé
EVENT_NAME_MAPPING = {
    # NFP
    'non-farm employment change': 'nonfarm_payrolls',
    'nonfarm payrolls': 'nonfarm_payrolls',
    'nfp': 'nonfarm_payrolls',
    'employment change': 'employment_change',
    
    # CPI
    'cpi m/m': 'cpi_mom',
    'cpi y/y': 'cpi_yoy',
    'core cpi m/m': 'core_cpi_mom',
    'core cpi y/y': 'core_cpi_yoy',
    'consumer price index': 'cpi',
    'inflation rate': 'cpi_yoy',
    
    # PPI
    'ppi m/m': 'ppi_mom',
    'ppi y/y': 'ppi_yoy',
    'core ppi m/m': 'core_ppi_mom',
    'producer price index': 'ppi',
    
    # Retail Sales
    'retail sales m/m': 'retail_sales_mom',
    'core retail sales m/m': 'core_retail_sales_mom',
    'retail sales': 'retail_sales',
    
    # GDP
    'gdp q/q': 'gdp_qoq',
    'gdp y/y': 'gdp_yoy',
    'gdp': 'gdp',
    'gross domestic product': 'gdp',
    
    # Unemployment
    'unemployment rate': 'unemployment_rate',
    'unemployment claims': 'unemployment_claims',
    'jobless claims': 'unemployment_claims',
    
    # ISM
    'ism manufacturing pmi': 'ism_manufacturing',
    'ism services pmi': 'ism_services',
    'ism manufacturing': 'ism_manufacturing',
    'ism services': 'ism_services',
    
    # Autres
    'fomc': 'fomc_decision',
    'fed funds rate': 'fed_funds_rate',
    'ecb rate': 'ecb_rate'
}

# ============================================================================
# FONCTIONS NORMALISATION
# ============================================================================

def normalize_country(country: str) -> str:
    """
    Normaliser code pays vers 3 lettres
    
    Args:
        country: Code pays (US, USD, etc.)
    
    Returns:
        Code 3 lettres lowercase (usd, gbp, etc.)
    """
    if not country:
        return 'xxx'
    
    country_upper = country.strip().upper()
    
    if country_upper in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[country_upper].lower()
    
    # Si déjà 3 lettres, retourner lowercase
    if len(country_upper) == 3:
        return country_upper.lower()
    
    # Sinon, retourner tel quel lowercase
    return country.strip().lower()


def normalize_event_name(name: str) -> str:
    """
    Normaliser nom événement vers clé standardisée
    
    Args:
        name: Nom événement original
    
    Returns:
        Nom standardisé (nonfarm_payrolls, cpi_mom, etc.)
    """
    if not name:
        return 'unknown'
    
    # Lowercase + strip
    name_lower = name.strip().lower()
    
    # Chercher mapping exact
    if name_lower in EVENT_NAME_MAPPING:
        return EVENT_NAME_MAPPING[name_lower]
    
    # Chercher mapping partiel
    for key, value in EVENT_NAME_MAPPING.items():
        if key in name_lower:
            return value
    
    # Sinon, créer clé depuis nom
    # Enlever caractères spéciaux
    clean = re.sub(r'[^a-z0-9\s]', '', name_lower)
    # Remplacer espaces par underscores
    clean = re.sub(r'\s+', '_', clean)
    # Limiter longueur
    if len(clean) > 50:
        clean = clean[:50]
    
    return clean


def normalize_datetime_jblanked(date_str: str) -> datetime:
    """
    Convertir timestamp JBlanked GMT+3 vers UTC
    
    Args:
        date_str: Format "2025.08.01 15:30:00" (GMT+3)
    
    Returns:
        datetime UTC
    """
    # Parse format JBlanked
    dt = datetime.strptime(date_str, '%Y.%m.%d %H:%M:%S')
    
    # Convertir GMT+3 → UTC (enlever 3 heures)
    dt_utc = dt - timedelta(hours=3)
    
    return dt_utc


def normalize_datetime_eodhd(date_str: str) -> datetime:
    """
    Parser timestamp EODHD (déjà UTC)
    
    Args:
        date_str: Format "2025-08-01 15:30:00" (UTC)
    
    Returns:
        datetime UTC
    """
    # EODHD déjà en UTC
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    
    return dt


def parse_value(value) -> float:
    """
    Parser valeur numérique (gère string, float, None)
    
    Args:
        value: Valeur à parser
    
    Returns:
        float ou None
    """
    if value is None or value == '':
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Enlever espaces
        value = value.strip()
        
        # Gérer pourcentages
        if '%' in value:
            value = value.replace('%', '')
        
        # Gérer K, M, B
        multiplier = 1
        if value.endswith('K'):
            multiplier = 1000
            value = value[:-1]
        elif value.endswith('M'):
            multiplier = 1000000
            value = value[:-1]
        elif value.endswith('B'):
            multiplier = 1000000000
            value = value[:-1]
        
        try:
            return float(value) * multiplier
        except:
            return None
    
    return None


def create_event_key(country: str, event_name: str, datetime_utc: datetime) -> str:
    """
    Créer clé unique pour événement
    
    Args:
        country: Code pays normalisé (usd, gbp, etc.)
        event_name: Nom événement normalisé
        datetime_utc: Datetime UTC
    
    Returns:
        Clé unique (usd_nonfarm_payrolls_20250801_1230)
    """
    dt_str = datetime_utc.strftime('%Y%m%d_%H%M')
    return f"{country}_{event_name}_{dt_str}"


# ============================================================================
# NORMALISATION ÉVÉNEMENTS
# ============================================================================

def normalize_jblanked_event(event: dict) -> dict:
    """
    Normaliser événement JBlanked vers structure master
    
    Args:
        event: Événement JBlanked brut
    
    Returns:
        Événement normalisé
    """
    # Extraire champs
    country_raw = event.get('Currency', '')
    name_raw = event.get('Name', '')
    date_raw = event.get('Date', '')
    
    # Normaliser
    country = normalize_country(country_raw)
    event_name = normalize_event_name(name_raw)
    datetime_utc = normalize_datetime_jblanked(date_raw)
    
    # Créer clé
    event_key = create_event_key(country, event_name, datetime_utc)
    
    # Structure master
    return {
        'event_key': event_key,
        'event_name': event_name,
        'event_name_original': name_raw,
        'country': country,
        'datetime_utc': datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
        'actual': parse_value(event.get('Actual')),
        'forecast': parse_value(event.get('Forecast')),
        'previous': parse_value(event.get('Previous')),
        'source': 'JBLANKED',
        'raw_data': event
    }


def normalize_eodhd_event(event: dict) -> dict:
    """
    Normaliser événement EODHD vers structure master
    
    Args:
        event: Événement EODHD brut
    
    Returns:
        Événement normalisé
    """
    # Extraire champs
    country_raw = event.get('country', '')
    name_raw = event.get('type', '')
    date_raw = event.get('date', '')
    
    # Normaliser
    country = normalize_country(country_raw)
    event_name = normalize_event_name(name_raw)
    datetime_utc = normalize_datetime_eodhd(date_raw)
    
    # Créer clé
    event_key = create_event_key(country, event_name, datetime_utc)
    
    # Structure master
    return {
        'event_key': event_key,
        'event_name': event_name,
        'event_name_original': name_raw,
        'country': country,
        'datetime_utc': datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
        'actual': parse_value(event.get('actual')),
        'forecast': parse_value(event.get('estimate')),  # EODHD: "estimate"
        'previous': parse_value(event.get('previous')),
        'source': 'EODHD',
        'raw_data': event
    }
