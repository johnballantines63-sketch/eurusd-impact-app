#!/usr/bin/env python3
"""
Compute Real Prediction (V3.2.1)
=================================

Fonction pour remplacer compute_placeholder_prediction() dans streamlit_app.py.

Cette fonction :
1. Charge les features V3.2.1 depuis daily_pred_score_v3_2_dataset_v1
2. Applique le modèle Ridge (artefact JSON) - déjà fait dans daily_risk_signal_v3_2_1
3. Détecte les clusters d'événements
4. Calcule pattern/direction/impact basé sur les actuals saisis
5. Retourne un DayPrediction validé (Pydantic)

Usage dans streamlit_app.py:
    from app.compute_real_prediction import compute_real_prediction
    
    pred = compute_real_prediction(
        date_str=selected_date,
        actuals=st.session_state[actuals_key],
        conn=conn
    )
"""

from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import sys

import duckdb
import pandas as pd
import numpy as np
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import contracts (optional)
try:
    from scripts.contracts.v3_2_1_contract import (
        DayPrediction, ActualRow, PatternPoint, ExitPlan,
        FEATURE_ORDER_HASH, CONTRACT_NAME, CONTRACT_VERSION
    )
    HAS_CONTRACTS = True
except ImportError:
    HAS_CONTRACTS = False
    DayPrediction = None
    ActualRow = None
    PatternPoint = None
    ExitPlan = None

# Model artifact
MODEL_PATH = PROJECT_ROOT / "models" / "v3_2_1_additive_ridge_alpha0_1.json"

# Family sentiment mapping (pour calcul direction)
FAMILY_SENTIMENT = {
    # Inversé (surprise positive = bad news USD)
    'jobless_claims': -1,
    'unemployment': -1,
    'cpi': -1,
    'inflation': -1,
    # Normal (surprise positive = good news USD)
    'nfp': 1,
    'gdp': 1,
    'retail_sales': 1,
    'ism': 1,
    'pmi': 1,
}


def calculate_surprise(actual: float, forecast: float, previous: Optional[float] = None) -> float:
    """Calcule surprise en %."""
    if pd.isna(actual) or pd.isna(forecast) or forecast == 0:
        return 0.0
    return ((actual - forecast) / forecast) * 100.0


def get_event_direction(event_key: str, surprise: float) -> int:
    """
    Calcule direction EUR/USD selon sentiment de la famille.
    Returns: +1 (EUR/USD UP) ou -1 (EUR/USD DOWN)
    """
    event_lower = event_key.lower()
    sentiment = 1  # Default: normal
    
    for family, sent in FAMILY_SENTIMENT.items():
        if family in event_lower:
            sentiment = sent
            break
    
    # Si sentiment inversé: surprise positive = bad news USD = EUR/USD UP (+1)
    # Si sentiment normal: surprise positive = good news USD = EUR/USD DOWN (-1)
    if sentiment == -1:
        return 1 if surprise > 0 else -1
    else:
        return -1 if surprise > 0 else 1


def detect_clusters(df_events: pd.DataFrame, window_minutes: int = 30):
    """
    Détecte clusters d'événements (fenêtre glissante).
    
    Returns:
        (clusters: List[Dict], df_sorted: pd.DataFrame)
        clusters: List[Dict] avec 'time' (datetime), 'row_ids' (List[int])
        df_sorted: DataFrame trié et réindexé (à utiliser pour slicing)
    """
    if df_events.empty:
        return [], df_events.copy()
    
    df = df_events.sort_values("ts_local").reset_index(drop=True)
    
    if len(df) == 0:
        return [], df
    
    clusters = []
    current = [0]
    last_t = df.loc[0, "ts_local"]
    
    for i in range(1, len(df)):
        t = df.loc[i, "ts_local"]
        delta = (t - last_t).total_seconds() / 60.0
        
        # Fenêtre glissante: comparer au dernier event, pas au start
        if delta <= window_minutes:
            current.append(i)
        else:
            clusters.append({
                "time": df.loc[current[0], "ts_local"],
                "row_ids": current
            })
            current = [i]
        
        last_t = t
    
    if current:
        clusters.append({
            "time": df.loc[current[0], "ts_local"],
            "row_ids": current
        })
    
    return clusters, df


def calculate_cluster_direction_impact(
    cluster_events: pd.DataFrame,
    actuals: Dict[str, float]
) -> Dict:
    """
    Calcule direction et impact d'un cluster basé sur actuals.
    
    Uses event_uid = event_key|ts_local_iso as key (stable, portable).
    
    Returns:
        {'direction': int (+1/-1), 'impact_pips': float, 'max_surprise': float}
    """
    contributions = []
    max_surprise = 0.0
    
    for _, event in cluster_events.iterrows():
        # Construire event_uid unique (event_key|ts_local_iso|row=idx)
        ts = pd.to_datetime(event["ts_local"]).isoformat()
        event_key = str(event.get("event_key") or event.get("event_title") or "UNKNOWN")
        
        # Clé unique (nouvelle avec row=)
        event_uid = f"{event_key}|{ts}|row={event.name}"
        actual_val = actuals.get(event_uid)
        
        # Fallback compat (anciennes sessions sans row=)
        if actual_val is None:
            actual_val = actuals.get(f"{event_key}|{ts}")
        
        if actual_val is None:
            continue
        
        # Calculer surprise
        forecast = event.get('forecast')
        previous = event.get('previous')
        
        if pd.isna(forecast) or forecast == 0:
            continue
        
        surprise = calculate_surprise(actual_val, forecast, previous)
        max_surprise = max(max_surprise, abs(surprise))
        
        # Calculer direction
        direction = get_event_direction(event_key, surprise)
        
        # Impact simplifié (basé sur importance et surprise)
        importance = event.get('importance_n', 1)
        impact_base = importance * 10.0  # Base: 10 pips par point d'importance
        impact = impact_base * (1 + abs(surprise) / 100.0)  # Amplification par surprise
        
        contributions.append(impact * direction)
    
    if not contributions:
        return {'direction': 0, 'impact_pips': 0.0, 'max_surprise': 0.0}
    
    # Direction nette = signe de la somme
    direction_net = 1 if sum(contributions) > 0 else -1
    impact_net = abs(sum(contributions))
    
    return {
        'direction': direction_net,
        'impact_pips': impact_net,
        'max_surprise': max_surprise
    }


def detect_pattern(clusters: List[Dict], cluster_impacts: List[Dict]) -> str:
    """
    Détecte pattern basé sur nombre et timing des clusters.
    
    Returns:
        'single_wave', 'double_wave', 'zigzag', ou 'unknown'
    """
    n_clusters = len(clusters)
    
    if n_clusters == 0:
        return 'unknown'
    elif n_clusters == 1:
        return 'single_wave'
    elif n_clusters == 2:
        # Vérifier timing entre clusters
        delay = (clusters[1]['time'] - clusters[0]['time']).total_seconds() / 60.0
        if delay < 60:
            return 'double_wave'  # Clusters proches
        else:
            return 'zigzag'  # Clusters séparés
    else:
        return 'zigzag'  # 3+ clusters = zigzag


def compute_real_prediction(
    date_str: str,
    actuals: Dict[str, float],
    conn: duckdb.DuckDBPyConnection,
    model_path: Optional[Path] = None,
) -> Dict:
    """
    Calcule la prédiction réelle V3.2.1 pour une date donnée.
    
    Args:
        date_str: Date au format YYYY-MM-DD
        actuals: Dict des actuals saisis (format: {date::idx: value})
        conn: Connection DuckDB
        model_path: Chemin vers l'artefact modèle (optionnel, non utilisé car déjà appliqué)
    
    Returns:
        Dict compatible avec DayPrediction
    """
    # 1. Charger prédiction vol (déjà calculée par apply script)
    df_vol = conn.execute(f"""
        SELECT pred_vol_pips, pred_log_vol
        FROM daily_risk_signal_v3_2_1
        WHERE date = DATE '{date_str}'
    """).df()
    
    if df_vol.empty:
        raise ValueError(f"Aucune prédiction trouvée pour {date_str}")
    
    pred_vol_pips = float(df_vol.iloc[0]['pred_vol_pips'])
    pred_log_vol = float(df_vol.iloc[0]['pred_log_vol'])
    
    # 2. Charger événements
    df_events = conn.execute(f"""
        SELECT
            ts_local,
            country,
            event_key,
            event_title,
            importance_n,
            previous,
            forecast
        FROM events_with_ts_local_v1
        WHERE DATE(ts_local) = DATE '{date_str}'
        ORDER BY ts_local ASC
    """).df()
    
    if df_events.empty:
        # Pas d'événements = NO_TRADE
        return {
            "date": date_str,
            "pred_vol_pips": pred_vol_pips,
            "pred_log_vol": pred_log_vol,
            "direction": "NO_TRADE",
            "pattern": "unknown",
            "impact_pred_pips": 0.0,
            "risk_score": 0.0,
            "entry_window": {"start": None, "end": None},
            "exit_window": {"start": None, "end": None},
            "pips_target": 0.0,
            "stop_loss_pips": 0.0,
        }
    
    df_events['ts_local'] = pd.to_datetime(df_events['ts_local'])
    
    # 3. Détecter clusters (fenêtre glissante, retourne df trié)
    clusters, df_sorted = detect_clusters(df_events, window_minutes=30)
    
    # Ajouter is_core au df_sorted (après tri/réindexation)
    df_sorted['is_core'] = (df_sorted['importance_n'].fillna(0) >= 4) | (df_sorted['country'] == 'US')
    
    if not clusters:
        return {
            "date": date_str,
            "pred_vol_pips": pred_vol_pips,
            "pred_log_vol": pred_log_vol,
            "direction": "NO_TRADE",
            "pattern": "unknown",
            "impact_pred_pips": 0.0,
            "risk_score": 0.0,
            "entry_window": {"start": None, "end": None},
            "exit_window": {"start": None, "end": None},
            "pips_target": 0.0,
            "stop_loss_pips": 0.0,
        }
    
    # 4. Calculer impact par cluster (utiliser df_sorted avec row_ids)
    cluster_impacts = []
    for cluster in clusters:
        cluster_events = df_sorted.iloc[cluster['row_ids']]
        impact = calculate_cluster_direction_impact(cluster_events, actuals)
        cluster_impacts.append(impact)
    
    # 5. Détecter pattern
    pattern = detect_pattern(clusters, cluster_impacts)
    
    # 6. Calculer direction globale (cluster principal ou somme vectorielle)
    primary_cluster_idx = 0
    if len(cluster_impacts) > 1:
        # Cluster avec plus grand impact
        max_impact = max(c['impact_pips'] for c in cluster_impacts)
        primary_cluster_idx = next(i for i, c in enumerate(cluster_impacts) if c['impact_pips'] == max_impact)
    
    primary_impact = cluster_impacts[primary_cluster_idx]
    direction_net = primary_impact['direction']
    impact_pips = primary_impact['impact_pips']
    
    # Si impact=0 mais qu'on a des clusters, vérifier si c'est vraiment neutre ou si actuals manquants
    # Si au moins 1 actual saisi mais impact=0, c'est suspect (log un warning)
    n_actuals_saisis = len([uid for uid in actuals.keys() if actuals.get(uid) is not None])
    if impact_pips == 0 and n_actuals_saisis > 0:
        import warnings
        warnings.warn(f"Impact=0 malgré {n_actuals_saisis} actual(s) saisi(s). Vérifier event_uid matching.")
    
    # Convertir direction en BUY/SELL/NO_TRADE
    if impact_pips == 0 or direction_net == 0:
        direction = "NO_TRADE"
    elif direction_net > 0:
        direction = "BUY"
    else:
        direction = "SELL"
    
    # 7. Calculer fenêtres (basé sur cluster principal - utiliser df_sorted)
    primary_cluster = clusters[primary_cluster_idx]
    # t0 = heure du premier core event du cluster principal
    primary_events = df_sorted.iloc[primary_cluster['row_ids']]
    primary_core = primary_events[primary_events['is_core']]
    if not primary_core.empty:
        t0 = primary_core.iloc[0]['ts_local']
    else:
        t0 = primary_cluster['time']  # Fallback
    
    entry = {
        "start": (t0 + pd.Timedelta(minutes=15)),
        "end": (t0 + pd.Timedelta(minutes=45))
    }
    
    # Exit window selon pattern
    if pattern == "single_wave":
        exit_w = {
            "start": (t0 + pd.Timedelta(minutes=60)),
            "end": (t0 + pd.Timedelta(minutes=180))
        }
    elif pattern == "double_wave":
        exit_w = {
            "start": (t0 + pd.Timedelta(minutes=90)),
            "end": (t0 + pd.Timedelta(minutes=240))
        }
    else:  # zigzag
        exit_w = {
            "start": (t0 + pd.Timedelta(minutes=120)),
            "end": (t0 + pd.Timedelta(minutes=300))
        }
    
    # 8. Targets conservateurs
    pips_target = float(np.clip(0.55 * impact_pips, 20, 80))
    stop_loss = float(np.clip(0.35 * impact_pips, 15, 60))
    
    # 9. Risk score (basé sur vol prédite et impact)
    risk_score = float(np.clip((pred_vol_pips - 30) / 120, 0, 1))
    
    # 10. Construire résultat
    result = {
        "date": date_str,
        "timezone": "Europe/Madrid",
        "direction": direction,
        "risk_score": risk_score,
        "pattern": pattern,
        "impact_pred_pips": float(impact_pips),
        "points": [],  # TODO: calculer PatternPoint
        "exit_plan": {
            "method": "hybrid",
            "exit_t_min_minutes": int((exit_w["start"] - t0).total_seconds() / 60),
            "exit_t_max_minutes": int((exit_w["end"] - t0).total_seconds() / 60),
            "take_profit_pips": pips_target,
            "stop_loss_pips": stop_loss,
        },
        "core_cluster_id": f"CLUSTER_{date_str}_{primary_cluster_idx}",
        "core_events": [],  # Construit ci-dessous (dicts ou ActualRow)
        "optional_events": [],
        "model_version": "V3.2.1",
        "contract_name": CONTRACT_NAME if HAS_CONTRACTS else "V3.2.1_TRADING_PAYLOAD",
        "contract_version": CONTRACT_VERSION if HAS_CONTRACTS else "1.0.0",
        "feature_order_hash": FEATURE_ORDER_HASH if HAS_CONTRACTS else "",
        "pred_vol_pips": pred_vol_pips,
        "pred_log_vol": pred_log_vol,
        # Compatibilité UI
        "entry_window": entry,
        "exit_window": exit_w,
        "pips_target": pips_target,
        "stop_loss_pips": stop_loss,
    }
    
    # 11. Construire core_events (ActualRow avec event_uid stable)
    core_events_list = []
    core_df = df_sorted[df_sorted['is_core']].copy()
    
    for _, event in core_df.iterrows():
        # Utiliser event_uid unique pour récupérer actual
        ts = pd.to_datetime(event["ts_local"]).isoformat()
        event_key = str(event.get("event_key") or event.get("event_title") or "UNKNOWN")
        
        # Clé unique (nouvelle avec row=)
        event_uid = f"{event_key}|{ts}|row={event.name}"
        actual_val = actuals.get(event_uid)
        
        # Fallback compat (anciennes sessions sans row=)
        if actual_val is None:
            actual_val = actuals.get(f"{event_key}|{ts}")
        
        # Construire dict pour ActualRow
        event_dict = {
            "event_id": event.get('event_key', event_key),
            "ts_local": event['ts_local'],
            "name": event.get('event_title', ''),
            "country": event.get('country', 'US'),
            "is_core": True,
            "previous": float(event.get('previous')) if pd.notna(event.get('previous')) else None,
            "forecast": float(event.get('forecast')) if pd.notna(event.get('forecast')) else None,
            "actual": float(actual_val) if actual_val is not None else None,
            "unit": None,
        }
        
        if HAS_CONTRACTS:
            try:
                actual_row = ActualRow(**event_dict)
                core_events_list.append(actual_row.model_dump())  # Convertir en dict
            except Exception as e:
                # Log l'erreur mais continue (ne pas swaller silencieusement)
                import warnings
                warnings.warn(f"Validation ActualRow échouée pour {event_key}: {e}")
                # Ajouter quand même le dict brut (compatibilité)
                core_events_list.append(event_dict)
        else:
            core_events_list.append(event_dict)
    
    result["core_events"] = core_events_list
    
    # 12. Valider avec DayPrediction si disponible
    if HAS_CONTRACTS:
        try:
            # Construire ExitPlan
            exit_plan = ExitPlan(
                method="hybrid",
                exit_t_min_minutes=result["exit_plan"]["exit_t_min_minutes"],
                exit_t_max_minutes=result["exit_plan"]["exit_t_max_minutes"],
                take_profit_pips=result["exit_plan"]["take_profit_pips"],
                stop_loss_pips=result["exit_plan"]["stop_loss_pips"],
            )
            
            # Convertir core_events (déjà en dicts) en ActualRow si nécessaire
            core_events_validated = []
            for event_dict in result["core_events"]:
                try:
                    actual_row = ActualRow(**event_dict)
                    core_events_validated.append(actual_row.model_dump())
                except Exception as e:
                    import warnings
                    warnings.warn(f"Validation ActualRow échouée: {e}")
                    core_events_validated.append(event_dict)
            
            # Construire DayPrediction
            day_pred = DayPrediction(
                date=pd.to_datetime(date_str).date(),
                timezone=result["timezone"],
                direction=result["direction"],
                risk_score=result["risk_score"],
                pattern=result["pattern"],
                impact_pred_pips=result["impact_pred_pips"],
                points=result["points"],
                exit_plan=exit_plan,
                core_cluster_id=result["core_cluster_id"],
                core_events=[ActualRow(**e) for e in core_events_validated],  # Reconvertir en objets
                optional_events=result["optional_events"],
                model_version=result["model_version"],
                contract_name=result["contract_name"],
                contract_version=result["contract_version"],
                feature_order_hash=result["feature_order_hash"],
                pred_vol_pips=result["pred_vol_pips"],
                pred_log_vol=result["pred_log_vol"],
            )
            
            # Convertir en dict pour compatibilité UI
            result = day_pred.model_dump()
            result["entry_window"] = entry
            result["exit_window"] = exit_w
            result["pips_target"] = pips_target
            result["stop_loss_pips"] = stop_loss
            
        except Exception as e:
            # Si validation échoue, log l'erreur mais retourner dict brut (ne pas swaller silencieusement)
            import warnings
            warnings.warn(f"Validation DayPrediction échouée: {e}")
            # Retourner dict brut (compatibilité)
    
    return result

