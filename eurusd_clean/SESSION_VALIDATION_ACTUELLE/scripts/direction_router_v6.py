#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Router Directionnel V6 - Standardisé pour Dates Tradables

Objectif : Fonction unique de vérité pour prédire la direction EURUSD
après actuals connus, pour dates avec clusters d'events historiquement associés à moves forts.

Convention :
- Score S calculé en convention USD (S>0 = USD up, S<0 = USD down)
- Mapping final : S>0 => EURUSD DOWN, S<0 => EURUSD UP
- Modèle triggered : nécessite au moins un event core avec |surprise_z| >= trigger_z

Usage :
    from direction_router_v6 import predict_direction_for_cluster, DirectionResult
    
    result = predict_direction_for_cluster(
        events_actuals=events_df,
        stats_map=stats_map,
        alpha_map=alpha_map,
        trigger_z=0.8,
        theta=0.05
    )
    
    print(f"Direction: {result.direction}")
    print(f"Score S: {result.score}")
    print(f"Trigger activé: {result.has_trigger}")
    print(f"Audit: {result.audit_log}")
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# Ajouter le répertoire racine au path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.event_families import FAMILY_PATTERNS

# ============================================================================
# CONFIGURATION PAR DÉFAUT (basée sur grille optimale)
# ============================================================================

# Noyau rates-core US (sans Other/ECB/PMI)
CORE_FAMILIES_V6 = [
    "CPI", "Jobless Claims", "NFP", "Unemployment",
    "Retail Sales", "GDP", "PPI", "Durable Goods", "FOMC"
]

# Seuils recommandés (basés sur grille)
DEFAULT_TRIGGER_Z = 0.8  # |z| >= 0.8 pour activer triggered
DEFAULT_THETA = 0.05      # Seuil neutralité pour direction
SIGMA_FLOOR = 0.1         # Plancher sigma pour éviter sur-normalisation

# Correction signes inversés (basé sur audit empirique first-leg)
# Ces familles ont un signe économique inversé par rapport aux weights appris
FAMILY_SIGN_FLIP = {
    "Jobless Claims": -1,   # Flip : effet empirique USD dovish quand surprise positive
    "Retail Sales": -1,      # Flip : effet empirique USD hawkish quand surprise positive
}

# Signes empiriques pour first-leg (basé sur audit large n=326 dates)
# Ces signes sont alignés avec l'effet observé sur la première jambe (1h post-release)
EMPIRICAL_SIGN_USD_FIRST_LEG = {
    "CPI": +1,              # Cohérent avec weights
    "NFP": +1,              # Cohérent avec weights
    "Unemployment": +1,     # Cohérent avec weights
    "GDP": +1,              # Cohérent avec weights
    "PPI": +1,              # Cohérent avec weights
    "Durable Goods": +1,   # Cohérent avec weights
    "Retail Sales": +1,     # Flip vs weights (empirique: surprise+ → USD hawkish → EURUSD DOWN)
    "Jobless Claims": -1,  # Flip vs weights (empirique: surprise+ → USD dovish → EURUSD UP)
    "FOMC": +1,            # Cohérent (n faible mais cohérent)
}

# Familles CPI/Jobs pour trigger resserré first-leg
CPI_JOBS_FAMILIES = {"CPI", "Jobless Claims", "NFP", "Unemployment"}

# ============================================================================
# STRUCTURES DE DONNÉES
# ============================================================================

@dataclass
class EventContribution:
    """Contribution d'un event au score directionnel"""
    event_key: str
    family: str
    actual: float
    estimate: float
    surprise: float
    surprise_z: float
    alpha_weight: float
    contribution: float
    is_trigger: bool  # Si |surprise_z| >= trigger_z

@dataclass
class DirectionResult:
    """Résultat de prédiction directionnelle"""
    direction: str  # "UP", "DOWN", "UNKNOWN"
    score: float    # Score S_cluster (convention USD)
    has_trigger: bool  # Si au moins un trigger activé
    n_active: int   # Nombre d'events actifs dans le score
    audit_log: List[EventContribution] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Export pour logging/JSON"""
        return {
            'direction': self.direction,
            'score': self.score,
            'has_trigger': self.has_trigger,
            'n_active': self.n_active,
            'contributions': [
                {
                    'event_key': c.event_key,
                    'family': c.family,
                    'surprise_z': c.surprise_z,
                    'contribution': c.contribution,
                    'is_trigger': c.is_trigger
                }
                for c in self.audit_log
            ]
        }

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def map_event_to_family(event_key: str) -> str:
    """Mappe event_key vers famille"""
    event_key_lower = str(event_key).lower()
    
    for family, pattern in FAMILY_PATTERNS.items():
        import re
        if re.search(pattern, event_key_lower):
            return family
    
    return 'Other'

def normalize_event_key(event_key: str) -> str:
    """Normalise event_key pour lookup stats (même logique que pipeline)"""
    return (
        str(event_key).strip().lower()
        .replace('-', ' ')
        .replace('  ', ' ')
        .strip()
    )

# ============================================================================
# ROUTER DIRECTIONNEL PRINCIPAL
# ============================================================================

def predict_direction_for_cluster(
    events_actuals: pd.DataFrame,
    stats_map: Dict[str, Tuple[float, float]],  # {event_key_normalized: (mu, sigma)}
    alpha_map: Dict[str, float],  # {family_surp_pos/neg: weight}
    core_families: Optional[List[str]] = None,
    trigger_z: float = DEFAULT_TRIGGER_Z,
    theta: float = DEFAULT_THETA,
    use_fallback_always_on: bool = False,
    first_leg_mode: bool = False  # Si True, utilise score empirique sans alpha_weights
) -> DirectionResult:
    """
    Prédit la direction EURUSD pour un cluster d'events après actuals connus.
    
    Args:
        events_actuals: DataFrame avec colonnes ['event_key', 'actual', 'estimate', 'family'?]
        stats_map: Map stats surprises (mu, sigma) par event_key normalisé
        alpha_map: Map alpha weights (family_surp_pos/neg -> weight)
        core_families: Liste familles core (défaut: CORE_FAMILIES_V6)
        trigger_z: Seuil |z| pour activer triggered (défaut: 0.8)
        theta: Seuil neutralité direction (défaut: 0.05)
        use_fallback_always_on: Si True, utilise always-on si pas de trigger
    
    Returns:
        DirectionResult avec direction, score, audit_log
    """
    if core_families is None:
        core_families = CORE_FAMILIES_V6
    
    # Ajouter colonne family si absente
    if 'family' not in events_actuals.columns:
        events_actuals = events_actuals.copy()
        events_actuals['family'] = events_actuals['event_key'].apply(map_event_to_family)
    
    contributions = []
    audit_log = []
    has_trigger = False
    has_cpi_jobs_trigger = False  # Pour trigger resserré first-leg
    
    # 1) Calculer surprise_z et contributions pour chaque event core
    for _, event_row in events_actuals.iterrows():
        event_key_raw = str(event_row['event_key']).strip()
        family = event_row.get('family', map_event_to_family(event_key_raw))
        
        # Filtrer seulement le noyau
        if family not in core_families:
            continue
        
        # Vérifier actual/estimate
        actual = event_row.get('actual')
        estimate = event_row.get('estimate')
        
        if pd.isna(actual) or pd.isna(estimate):
            continue
        
        actual = float(actual)
        estimate = float(estimate)
        surprise = actual - estimate
        
        # Normaliser event_key pour lookup stats
        event_key_normalized = normalize_event_key(event_key_raw)
        
        # ⚠️ V8 SAFE : Format de clé officiel pour stats_map
        # Clé = normalize_event_key(event_key) + "_" + country
        # Cette normalisation garantit la cohérence entre construction stats_map et lookup
        country = str(event_row.get('country', '')).strip()
        if country:
            lookup_key = f"{event_key_normalized}_{country}"
        else:
            # Fallback : essayer sans country (compatibilité V7)
            lookup_key = event_key_normalized
        
        # Récupérer stats depuis stats_map
        mu_sigma = stats_map.get(lookup_key)
            if mu_sigma is None:
                # Fallback V7 : essayer sans country si pas trouvé
                if country:
                    mu_sigma = stats_map.get(event_key_normalized)
                if mu_sigma is None:
                    # ⚠️ V8 DIAGNOSTIC : core event sans stats (peut indiquer format event_key changé)
                    n_core_without_stats += 1
                    # Si pas de stats, skip (pas d'invention)
                    continue
        
        mu, sigma = mu_sigma
        if sigma == 0:
            continue
        
        # Appliquer sigma_floor
        sigma = max(sigma, SIGMA_FLOOR)
        
        # Calculer surprise_z standardisé
        surprise_z = (surprise - mu) / sigma
        
        # Vérifier si trigger activé
        is_trigger = abs(surprise_z) >= trigger_z
        if is_trigger:
            has_trigger = True
            # Pour first-leg mode : trigger resserré sur CPI/Jobs uniquement
            if first_leg_mode and family in CPI_JOBS_FAMILIES:
                has_cpi_jobs_trigger = True
        
        # Calculer contribution selon le mode
        if first_leg_mode:
            # Mode first-leg : score empirique sans alpha_weights
            if family in EMPIRICAL_SIGN_USD_FIRST_LEG:
                sign_empirical = EMPIRICAL_SIGN_USD_FIRST_LEG[family]
                contribution = sign_empirical * surprise_z
                weight = sign_empirical  # Pour l'audit log
            else:
                # Famille non dans le mapping empirique → skip
                continue
        else:
            # Mode standard : utilise alpha_weights
            alpha_key_pos = f"{family}_surp_pos"
            alpha_key_neg = f"{family}_surp_neg"
            
            if surprise_z > 0 and alpha_key_pos in alpha_map:
                weight = alpha_map[alpha_key_pos]
            elif surprise_z < 0 and alpha_key_neg in alpha_map:
                weight = alpha_map[alpha_key_neg]
            else:
                weight = 0.0
            
            # Calculer contribution de base
            contribution_base = weight * surprise_z
            
            # Appliquer flip de signe si nécessaire (correction empirique)
            contribution = contribution_base
            if family in FAMILY_SIGN_FLIP:
                contribution *= FAMILY_SIGN_FLIP[family]
        
        contributions.append(contribution)
        
        # Audit log (avec contribution finale après flip)
        audit_log.append(EventContribution(
            event_key=event_key_raw,
            family=family,
            actual=actual,
            estimate=estimate,
            surprise=surprise,
            surprise_z=surprise_z,
            alpha_weight=weight,  # Weight original (avant flip)
            contribution=contribution,  # Contribution finale (après flip)
            is_trigger=is_trigger
        ))
    
    # ⚠️ V8 DIAGNOSTIC : Log si % core events sans stats > 10%
    if n_core_events > 0:
        pct_missing = (n_core_without_stats / n_core_events) * 100
        if pct_missing > 10.0:
            import warnings
            warnings.warn(
                f"V8 DIAGNOSTIC: {pct_missing:.1f}% core events sans stats ({n_core_without_stats}/{n_core_events}). "
                f"Vérifier format event_key ou étendre stats_map.",
                UserWarning
            )
    
    # 2) Calculer score S_cluster (convention USD)
    if len(contributions) == 0:
        return DirectionResult(
            direction='UNKNOWN',
            score=0.0,
            has_trigger=False,
            n_active=0,
            audit_log=audit_log
        )
    
    score_raw = sum(contributions)
    
    # Normalisation par sqrt(n_active) comme F2
    n_active = len([c for c in contributions if abs(c) > 1e-10])
    if n_active > 0:
        score = score_raw / np.sqrt(max(1, n_active))
    else:
        score = score_raw
    
    # 3) Déterminer trigger actif (resserré pour first-leg)
    # En mode first-leg : trigger resserré sur CPI/Jobs uniquement
    trigger_active = has_trigger
    if first_leg_mode:
        trigger_active = has_cpi_jobs_trigger
    
    # 4) Déterminer direction (convention USD -> EURUSD)
    # Si pas de trigger et fallback désactivé → UNKNOWN
    if not trigger_active and not use_fallback_always_on:
        return DirectionResult(
            direction='UNKNOWN',
            score=score,
            has_trigger=False,
            n_active=n_active,
            audit_log=audit_log
        )
    
    # Direction avec seuil theta (convention USD -> EURUSD)
    # S>0 = USD up = EURUSD DOWN
    # S<0 = USD down = EURUSD UP
    if abs(score) < theta:
        direction = 'UNKNOWN'
    elif score > 0:
        direction = 'DOWN'  # USD up => EURUSD down
    else:
        direction = 'UP'    # USD down => EURUSD up
    
    return DirectionResult(
        direction=direction,
        score=score,
        has_trigger=has_trigger,
        n_active=n_active,
        audit_log=audit_log
    )

# ============================================================================
# FONCTION DE CHARGEMENT STATS/ALPHA (pour intégration)
# ============================================================================

def load_direction_router_dependencies(
    db_path: Optional[Path] = None,
    alpha_file: Optional[Path] = None,
    horizon: str = '1h',
    min_date: str = V8_MIN_STATS_DATE,
    max_date: str = V8_MAX_STATS_DATE
) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]:
    """
    Charge stats_map et alpha_map depuis fichiers/DB.
    
    V8 SAFE extension:
    - calcule stats_map sur une fenêtre large pour inclure event_keys historiques
    - aucune modification logique V7, seulement plus de matière stats
    
    Args:
        db_path: Chemin vers la DB
        alpha_file: Fichier CSV avec alpha weights (optionnel)
        horizon: Horizon temporel ('1h', etc.)
        min_date: Date min pour calcul stats (V8: étendre à 2022)
        max_date: Date max pour calcul stats
    
    Returns:
        (stats_map, alpha_map)
        stats_map: dict avec clé "event_key_country" -> (mean, std)
    """
    import duckdb
    
    # Stats depuis DB
    stats_map = {}
    if db_path and db_path.exists():
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            # ⚠️ V8 : ajouter filtre par date pour étendre période historique
            query = """
            SELECT 
                event_key,
                country,
                actual,
                estimate
            FROM events
            WHERE actual IS NOT NULL 
              AND estimate IS NOT NULL
              AND country IN ('US', 'EU', 'GB', 'DE')
              AND ts_utc >= ?
              AND ts_utc <= ?
            """
            df = conn.execute(query, [min_date, max_date]).df()
            
            if len(df) > 0:
                # ⚠️ V8 SAFE : Utiliser normalize_event_key pour cohérence avec lookup
                # Cette normalisation garantit que les clés dans stats_map matchent
                # exactement celles utilisées dans predict_direction_for_cluster
                df['event_key_normalized'] = df['event_key'].apply(normalize_event_key)
                df['actual'] = pd.to_numeric(df['actual'], errors='coerce')
                df['estimate'] = pd.to_numeric(df['estimate'], errors='coerce')
                df = df.dropna(subset=['actual', 'estimate'])
                df['surprise'] = df['actual'] - df['estimate']
                
                # ⚠️ V8 SAFE : Format de clé officiel = normalize_event_key(event_key) + "_" + country
                # Groupby sur cette clé garantit stats précises par event_key+country
                df['key'] = df['event_key_normalized'] + '_' + df['country']
                g = df.groupby('key')['surprise']
                mu = g.mean()
                sigma = g.std(ddof=0)
                n = g.count()
                
                for k in mu.index:
                    s = float(sigma.loc[k])
                    n_events = int(n.loc[k])
                    if s == 0 or np.isnan(s) or n_events < 5:
                        continue
                    s = max(s, SIGMA_FLOOR)
                    stats_map[k] = (float(mu.loc[k]), s)
        finally:
            conn.close()
    
    # Alpha weights depuis CSV
    alpha_map = {}
    if alpha_file and alpha_file.exists():
        df_alpha = pd.read_csv(alpha_file)
        df_horizon = df_alpha[df_alpha['horizon'] == horizon]
        for _, row in df_horizon.iterrows():
            event_key = str(row['event_key']).strip()
            weight = float(row['weight'])
            alpha_map[event_key] = weight
    
    return stats_map, alpha_map

# ============================================================================
# EXPORT POUR USAGE
# ============================================================================

if __name__ == '__main__':
    # Test rapide
    print("Router Directionnel V6 - Module standardisé")
    print(f"Familles core: {', '.join(CORE_FAMILIES_V6)}")
    print(f"Seuils par défaut: trigger_z={DEFAULT_TRIGGER_Z}, theta={DEFAULT_THETA}")

