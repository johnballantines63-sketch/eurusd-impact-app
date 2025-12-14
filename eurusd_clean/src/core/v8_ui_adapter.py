#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptateur V8 pour Interface Utilisateur

Objectif : Interface unique et propre entre le moteur V8 backtesté et l'UI Streamlit.

Cette fonction encapsule :
- Chargement stats_map/alpha_map
- Construction cluster_events au format requis
- Appel calculate_cluster_impact_with_direction
- Formatage résultat UI-friendly

Usage:
    from core.v8_ui_adapter import predict_cluster_v8
    
    result = predict_cluster_v8(
        date=selected_date,
        events_df=events_for_date,
        db_path=DB_PATH,
        conn=conn
    )
    
    if result['success']:
        print(f"Direction: {result['direction']}")
        print(f"Impact: {result['impact_pips']} pips")
        print(f"Pattern: {result['pattern_type']}")
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import duckdb
import warnings

# Ajouter SESSION_VALIDATION_ACTUELLE/scripts au path
PROJECT_ROOT = Path(__file__).parent.parent.parent
SESSION_SCRIPTS = PROJECT_ROOT / "SESSION_VALIDATION_ACTUELLE" / "scripts"
if str(SESSION_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SESSION_SCRIPTS))

try:
    from direction_router_v6 import (
        load_direction_router_dependencies,
        CORE_FAMILIES_V6,
        map_event_to_family,
        V8_MIN_STATS_DATE,
        V8_MAX_STATS_DATE
    )
    from integrate_direction_first_leg import calculate_cluster_impact_with_direction
except ImportError as e:
    raise ImportError(
        f"Impossible d'importer les modules V8. Vérifier que direction_router_v6.py "
        f"et integrate_direction_first_leg.py sont dans SESSION_VALIDATION_ACTUELLE/scripts. "
        f"Erreur: {e}"
    )


# Cache global pour stats_map/alpha_map (évite rechargement à chaque appel)
_stats_map_cache: Optional[Dict[str, Tuple[float, float]]] = None
_alpha_map_cache: Optional[Dict[str, float]] = None
_cache_db_path: Optional[Path] = None


def _load_stats_maps(db_path: Path, force_reload: bool = False) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]:
    """
    Charge stats_map et alpha_map avec cache.
    
    Args:
        db_path: Chemin vers la DB DuckDB
        force_reload: Forcer rechargement même si cache existe
    
    Returns:
        (stats_map, alpha_map)
    """
    global _stats_map_cache, _alpha_map_cache, _cache_db_path
    
    # Utiliser cache si disponible et même DB
    if not force_reload and _stats_map_cache is not None and _cache_db_path == db_path:
        return _stats_map_cache, _alpha_map_cache
    
    # Charger depuis DB
    stats_map, alpha_map = load_direction_router_dependencies(
        db_path=db_path,
        min_date=V8_MIN_STATS_DATE,
        max_date=V8_MAX_STATS_DATE,
        horizon="1h",
        alpha_file=None
    )
    
    # Mettre en cache
    _stats_map_cache = stats_map
    _alpha_map_cache = alpha_map
    _cache_db_path = db_path
    
    return stats_map, alpha_map


def predict_cluster_v8(
    date: pd.Timestamp,
    events_df: pd.DataFrame,
    db_path: Path,
    conn: Optional[duckdb.DuckDBPyConnection] = None,
    movement_start_time: Optional[pd.Timestamp] = None,
    trigger_z: float = 1.0,
    theta: float = 0.05
) -> Dict:
    """
    Prédiction cluster V8 pour UI.
    
    Cette fonction encapsule toute la logique V8 et retourne un format UI-friendly.
    
    Args:
        date: Date du cluster (pour logging)
        events_df: DataFrame avec colonnes :
            - event_key (requis)
            - actual (requis pour prédiction)
            - estimate (requis pour prédiction)
            - country (requis pour lookup stats_map)
            - family (optionnel, sera mappé si absent)
            - empirical_score (optionnel, défaut 10.0)
            - latency_median (optionnel, défaut 2.0)
        db_path: Chemin vers DB DuckDB (pour charger stats_map)
        conn: Connexion DuckDB (optionnel, pour pattern detection)
        movement_start_time: Timestamp début mouvement (optionnel, pour pattern detection)
        trigger_z: Seuil trigger |z| (défaut: 1.0)
        theta: Seuil neutralité direction (défaut: 0.05)
    
    Returns:
        {
            'success': bool,                    # Si prédiction réussie
            'direction': str,                  # 'UP' | 'DOWN' | 'UNKNOWN' | None
            'impact_pips': float,              # Impact prédit (pips)
            'pattern_type': Optional[str],     # 'single_wave' | 'double_wave' | 'zig_zag' | None
            'trigger_strength': float,         # max|z| des triggers
            'has_trigger': bool,               # Si trigger activé
            'direction_score': float,          # Score directionnel S_cluster
            'cluster_type': Optional[str],     # CPI/Jobs/CPI+Jobs
            'leg1': Optional[dict],            # Détails jambe 1 (si multi-wave)
            'leg2': Optional[dict],            # Détails jambe 2 (si multi-wave)
            'warnings': List[str],             # Warnings SAFE runtime
            'skipped': bool,                   # Si calcul sauté
            'skip_reason': Optional[str],      # Raison si skipped
            'error': Optional[str]             # Message erreur si success=False
        }
    """
    result = {
        'success': False,
        'direction': None,
        'impact_pips': 0.0,
        'pattern_type': None,
        'trigger_strength': 0.0,
        'has_trigger': False,
        'direction_score': 0.0,
        'cluster_type': None,
        'leg1': None,
        'leg2': None,
        'warnings': [],
        'skipped': False,
        'skip_reason': None,
        'error': None
    }
    
    try:
        # 1) Vérifier inputs
        if events_df.empty:
            result['error'] = "DataFrame events_df vide"
            return result
        
        required_cols = ['event_key', 'actual', 'estimate', 'country']
        missing_cols = [col for col in required_cols if col not in events_df.columns]
        if missing_cols:
            result['error'] = f"Colonnes manquantes: {', '.join(missing_cols)}"
            return result
        
        # 2) Charger stats_map/alpha_map (avec cache)
        try:
            stats_map, alpha_map = _load_stats_maps(db_path)
        except Exception as e:
            result['error'] = f"Erreur chargement stats_map: {str(e)}"
            return result
        
        # 3) Préparer cluster_events au format requis
        cluster_events = events_df.copy()
        
        # Mapper vers familles si absent
        if 'family' not in cluster_events.columns:
            cluster_events['family'] = cluster_events['event_key'].apply(map_event_to_family)
        
        # Filtrer seulement core events
        core_events = cluster_events[cluster_events['family'].isin(CORE_FAMILIES_V6)].copy()
        
        if len(core_events) == 0:
            result['error'] = "Aucun event core dans le cluster"
            return result
        
        # Colonnes minimales si absentes
        if 'empirical_score' not in core_events.columns:
            core_events['empirical_score'] = 10.0
        if 'latency_median' not in core_events.columns:
            core_events['latency_median'] = 2.0
        
        # ⚠️ SAFE RUNTIME : Vérifier % events core sans stats
        # Note: Utiliser même normalisation que V8 (normalize_event_key) pour cohérence
        from direction_router_v6 import normalize_event_key
        
        n_core = len(core_events)
        n_without_stats = 0
        for _, row in core_events.iterrows():
            event_key_raw = str(row['event_key']).strip()
            event_key_norm = normalize_event_key(event_key_raw)  # ⭐ Même normalisation que V8
            country = str(row.get('country', '')).strip()
            lookup_key = f"{event_key_norm}_{country}" if country else event_key_norm
            if lookup_key not in stats_map:
                # Fallback sans country
                if country and event_key_norm in stats_map:
                    continue
                n_without_stats += 1
        
        if n_core > 0:
            pct_missing = (n_without_stats / n_core) * 100.0
            if pct_missing > 10.0:
                result['warnings'].append(
                    f"⚠️ {pct_missing:.1f}% events core sans stats ({n_without_stats}/{n_core}). "
                    f"Prédiction peut être moins fiable."
                )
        
        # 4) Appeler moteur V8
        pred = calculate_cluster_impact_with_direction(
            cluster_events=core_events,
            stats_map=stats_map,
            alpha_map=alpha_map,
            trigger_z=trigger_z,
            theta=theta,
            first_leg_mode=True,
            use_linear_formula=True,
            core_families=CORE_FAMILIES_V6,
            movement_start_time=movement_start_time,
            conn=conn
        )
        
        # 5) Vérifier si skipped
        if pred.get('skipped', False):
            result['skipped'] = True
            result['skip_reason'] = pred.get('skip_reason', 'Unknown')
            result['warnings'].append(f"⚠️ Prédiction non disponible: {result['skip_reason']}")
            return result
        
        # 6) Formater résultat UI-friendly
        result['success'] = True
        result['direction'] = pred.get('direction_first_leg', 'UNKNOWN')
        result['impact_pips'] = float(pred.get('impact_pips', 0.0))
        result['pattern_type'] = pred.get('pattern_type')
        result['trigger_strength'] = float(pred.get('trigger_strength', 0.0))
        result['has_trigger'] = bool(pred.get('has_trigger', False))
        result['direction_score'] = float(pred.get('direction_score', 0.0))
        result['cluster_type'] = pred.get('cluster_type')
        
        # Legs si multi-wave
        if pred.get('leg1') and pred.get('leg2'):
            result['leg1'] = {
                'direction': pred['leg1'].get('direction'),
                'amp_pips': float(pred['leg1'].get('amp_pips', 0.0)),
                't_peak_min': float(pred['leg1'].get('t_peak_min', 0.0))
            }
            result['leg2'] = {
                'direction': pred['leg2'].get('direction'),
                'amp_pips': float(pred['leg2'].get('amp_pips', 0.0)),
                't_peak_min': float(pred['leg2'].get('t_peak_min', 0.0))
            }
        
        return result
        
    except Exception as e:
        result['error'] = f"Erreur prédiction V8: {str(e)}"
        import traceback
        warnings.warn(f"Erreur predict_cluster_v8: {traceback.format_exc()}")
        return result


def clear_cache():
    """Efface le cache stats_map/alpha_map (utile pour tests ou rechargement)."""
    global _stats_map_cache, _alpha_map_cache, _cache_db_path
    _stats_map_cache = None
    _alpha_map_cache = None
    _cache_db_path = None

