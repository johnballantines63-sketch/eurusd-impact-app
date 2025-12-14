#!/usr/bin/env python3
"""
Backtest Engine V1 - Validation Empirique
==========================================

Module Python réutilisable pour valider scientifiquement le moteur sur des dates panel.
Aucune dépendance à Streamlit.

Fonctions principales:
- load_events_enriched: Charge et standardise les événements depuis DB
- compute_direction_impact_from_surprises: Calcule direction/impact depuis surprises
- compute_pred_vol_pips: Charge la volatilité prédite
- detect_pattern_from_prices: Détecte pattern depuis les prix réels
- compute_day_prediction: Pipeline complète pour une date
"""

import warnings
from typing import Dict, Optional, List, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
import pandas as pd
import numpy as np


def normalize_text(text: pd.Series) -> pd.Series:
    """
    Normalise un texte pour matching (lowercase, alphanumeric only).
    
    Args:
        text: Series pandas avec textes à normaliser
        
    Returns:
        Series normalisée
    """
    return (
        text.astype(str)
        .str.lower()
        .str.replace(r"[^a-z0-9 ]", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def load_events_enriched(date_str: str, conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Charge et enrichit les événements d'une date avec colonnes standardisées.
    
    Colonnes retournées:
    - ts_utc, ts_local
    - country
    - event_key (ou event_title si absent)
    - actual
    - consensus = COALESCE(estimate, forecast)
    - previous = COALESCE(previous, prev)
    - importance_n
    - is_core (importance_n >= 4 OR country='US')
    
    La fonction:
    1. Charge depuis events_with_ts_local_v1 (base)
    2. Joint economic_events si consensus manquant
    3. Join robuste: (country, ts_utc arrondi) + fallback texte normalisé
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        conn: Connexion DuckDB (read-only)
        
    Returns:
        DataFrame avec colonnes standardisées
    """
    warnings.warn(f"Chargement événements enrichis pour {date_str}")
    
    # 1. Charger depuis events_with_ts_local_v1 (source principale)
    # Note: events_with_ts_local_v1 a 'previous' mais pas 'prev'
    query_base = """
        SELECT
            ts_utc,
            ts_local,
            country,
            COALESCE(event_key, event_title, 'UNKNOWN') as event_key,
            event_title,
            actual,
            estimate,
            forecast,
            previous,
            importance_n
        FROM events_with_ts_local_v1
        WHERE DATE(ts_local) = CAST(? AS DATE)
        ORDER BY ts_local
    """
    
    df_base = conn.execute(query_base, [date_str]).df()
    
    if df_base.empty:
        warnings.warn(f"Aucun événement trouvé dans events_with_ts_local_v1 pour {date_str}")
        return pd.DataFrame()
    
    # Standardiser les colonnes
    # Note: events_with_ts_local_v1 n'a pas 'prev', seulement 'previous'
    df_base["consensus"] = df_base["estimate"].fillna(df_base.get("forecast", pd.Series(dtype=float)))
    # previous existe déjà, pas besoin de fillna avec prev
    df_base["is_core"] = (df_base["importance_n"] >= 4) | (df_base["country"] == "US")
    
    # Compter stats avant enrichissement
    n_events = len(df_base)
    pct_consensus = (df_base["consensus"].notna().sum() / n_events) * 100 if n_events > 0 else 0
    pct_actual = (df_base["actual"].notna().sum() / n_events) * 100 if n_events > 0 else 0
    
    warnings.warn(f"Base: {n_events} événements | consensus: {pct_consensus:.1f}% | actual: {pct_actual:.1f}%")
    
    # 2. Enrichir depuis economic_events si consensus manquant
    missing_consensus = df_base["consensus"].isna()
    if missing_consensus.sum() > 0:
        warnings.warn(f"Tentative enrichissement depuis economic_events pour {missing_consensus.sum()} événements")
        
        # Charger economic_events pour cette date
        query_econ = """
            SELECT
                datetime_utc,
                country,
                event_name,
                forecast as forecast_econ,
                previous as previous_econ
            FROM economic_events
            WHERE DATE(datetime_utc) = CAST(? AS DATE)
        """
        df_econ = conn.execute(query_econ, [date_str]).df()
        
        if not df_econ.empty:
            # Convertir datetime_utc en ts_utc pour join
            df_econ["ts_utc"] = pd.to_datetime(df_econ["datetime_utc"])
            df_base["ts_utc"] = pd.to_datetime(df_base["ts_utc"])
            
            # Normaliser pour matching texte
            df_base["event_title_norm"] = normalize_text(df_base["event_title"])
            df_econ["event_name_norm"] = normalize_text(df_econ["event_name"])
            
            # Join 1: par (country, ts_utc arrondi à la minute)
            df_base["ts_utc_minute"] = df_base["ts_utc"].dt.floor("T")
            df_econ["ts_utc_minute"] = df_econ["ts_utc"].dt.floor("T")
            
            merged_time = df_base.loc[missing_consensus].merge(
                df_econ[["country", "ts_utc_minute", "forecast_econ", "previous_econ"]],
                on=["country", "ts_utc_minute"],
                how="left",
                suffixes=("", "_econ")
            )
            
            # Remplir consensus manquant
            idx_filled_time = merged_time["forecast_econ"].notna()
            if idx_filled_time.any():
                filled_indices = df_base.loc[missing_consensus].index[idx_filled_time]
                df_base.loc[filled_indices, "consensus"] = merged_time.loc[idx_filled_time, "forecast_econ"].values
                df_base.loc[filled_indices, "previous"] = df_base.loc[filled_indices, "previous"].fillna(
                    merged_time.loc[idx_filled_time, "previous_econ"].values
                )
                warnings.warn(f"  → {idx_filled_time.sum()} enrichis par join temporel")
            
            # Join 2: fallback par (country, texte normalisé)
            still_missing = df_base["consensus"].isna()
            if still_missing.sum() > 0:
                merged_text = df_base.loc[still_missing].merge(
                    df_econ[["country", "event_name_norm", "forecast_econ", "previous_econ"]],
                    left_on=["country", "event_title_norm"],
                    right_on=["country", "event_name_norm"],
                    how="left"
                )
                
                idx_filled_text = merged_text["forecast_econ"].notna()
                if idx_filled_text.any():
                    filled_indices = df_base.loc[still_missing].index[idx_filled_text]
                    df_base.loc[filled_indices, "consensus"] = merged_text.loc[idx_filled_text, "forecast_econ"].values
                    df_base.loc[filled_indices, "previous"] = df_base.loc[filled_indices, "previous"].fillna(
                        merged_text.loc[idx_filled_text, "previous_econ"].values
                    )
                    warnings.warn(f"  → {idx_filled_text.sum()} enrichis par matching texte")
    
    # Colonnes finales standardisées
    df_result = df_base[[
        "ts_utc", "ts_local", "country", "event_key", "event_title",
        "actual", "consensus", "previous", "importance_n", "is_core"
    ]].copy()
    
    # Stats finales
    pct_consensus_final = (df_result["consensus"].notna().sum() / len(df_result)) * 100
    warnings.warn(f"Final: {len(df_result)} événements | consensus: {pct_consensus_final:.1f}%")
    
    return df_result


def compute_direction_impact_from_surprises(df_events_enriched: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule direction et impact prédits depuis les surprises.
    
    Utilise une somme vectorielle pondérée par importance.
    
    Args:
        df_events_enriched: DataFrame avec colonnes actual, consensus, importance_n, is_core
        
    Returns:
        Dict avec:
        - direction_pred: +1 (EUR/USD UP), -1 (EUR/USD DOWN), 0 (NO_TRADE)
        - impact_pred: pips prédits (positif)
        - n_events_with_surprise: nombre d'événements avec surprise calculable
    """
    df = df_events_enriched.copy()
    
    # Calculer surprises
    df["surprise_value"] = df["actual"] - df["consensus"]
    df["surprise_pct"] = (df["surprise_value"] / df["consensus"].abs()) * 100
    df.loc[df["consensus"] == 0, "surprise_pct"] = np.nan
    
    # Filtrer événements avec surprise calculable
    has_surprise = df["surprise_value"].notna()
    df_valid = df[has_surprise].copy()
    
    if df_valid.empty:
        warnings.warn("Aucune surprise calculable")
        return {
            "direction_pred": 0,
            "impact_pred": 0.0,
            "n_events_with_surprise": 0
        }
    
    # Direction: somme vectorielle pondérée
    # Pour l'instant, simplifié: surprise positive → direction selon country/event_type
    # TODO: intégrer sentiment mapping si nécessaire
    weights = df_valid["importance_n"].fillna(1).values
    surprises = df_valid["surprise_value"].values
    
    # Approximation: surprise > 0 → EUR/USD DOWN (USD strong), surprise < 0 → EUR/USD UP
    # Pondérer par importance
    direction_sum = np.sum(weights * np.sign(surprises))
    
    if abs(direction_sum) < 1e-6:
        direction_pred = 0
    else:
        direction_pred = 1 if direction_sum < 0 else -1
    
    # Impact: moyenne pondérée des surprises absolues (simplifié)
    impact_pred = np.average(np.abs(surprises), weights=weights) if len(surprises) > 0 else 0.0
    
    warnings.warn(f"Direction: {direction_pred} | Impact: {impact_pred:.2f} | N events: {len(df_valid)}")
    
    return {
        "direction_pred": direction_pred,
        "impact_pred": impact_pred,
        "n_events_with_surprise": len(df_valid)
    }


def compute_pred_vol_pips(date_str: str, conn: duckdb.DuckDBPyConnection) -> float:
    """
    Charge la volatilité prédite en pips pour une date.
    
    Essaie d'abord daily_risk_signal_v3_2_1, puis fallback sur daily_eurusd_volatility_v1 (realized).
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        conn: Connexion DuckDB
        
    Returns:
        Volatilité prédite en pips
    """
    # 1. Essayer daily_risk_signal_v3_2_1
    query_pred = """
        SELECT pred_vol_pips
        FROM daily_risk_signal_v3_2_1
        WHERE date = CAST(? AS DATE)
    """
    
    df_pred = conn.execute(query_pred, [date_str]).df()
    
    if not df_pred.empty and df_pred["pred_vol_pips"].notna().any():
        vol = float(df_pred["pred_vol_pips"].iloc[0])
        warnings.warn(f"Vol prédite (daily_risk_signal_v3_2_1): {vol:.2f} pips")
        return vol
    
    # 2. Fallback: daily_eurusd_volatility_v1 (realized)
    warnings.warn("pred_vol_pips non trouvé dans daily_risk_signal_v3_2_1, fallback sur realized volatility")
    
    query_real = """
        SELECT realized_vol_pips
        FROM daily_eurusd_volatility_v1
        WHERE date = CAST(? AS DATE)
    """
    
    df_real = conn.execute(query_real, [date_str]).df()
    
    if not df_real.empty and df_real["realized_vol_pips"].notna().any():
        vol = float(df_real["realized_vol_pips"].iloc[0])
        warnings.warn(f"Vol réalisée (fallback): {vol:.2f} pips")
        return vol
    
    # 3. Fallback final: moyenne historique (approximative)
    warnings.warn("Aucune vol trouvée, utilisation valeur par défaut: 80 pips")
    return 80.0


def detect_pattern_from_prices(
    prices_df: pd.DataFrame,
    t0: datetime,
    min_movement_pips: float = 15.0,
    atr_multiplier: float = 0.35,
    **kwargs
) -> Dict[str, Any]:
    """
    Détecte le pattern réel depuis les prix.
    
    Classification:
    - single_wave: 1 impulsion dominante, <= 1 retournement significatif
    - double_wave: 2 impulsions dans même direction séparées par pullback significatif
    - zigzag: >= 2 retournements alternés significatifs
    
    Args:
        prices_df: DataFrame avec colonnes 'ts_utc' (ou 'datetime') et 'close'
        t0: Timestamp de l'événement
        min_movement_pips: Seuil minimal pour un mouvement significatif (pips)
        atr_multiplier: Multiplicateur ATR pour seuil adaptatif
        
    Returns:
        Dict avec:
        - pattern_type: 'single_wave', 'double_wave', 'zigzag', 'none'
        - turning_points: Liste de (timestamp, price, type) des turning points
        - max_movement_pips: Mouvement maximum en pips
    """
    if prices_df.empty:
        warnings.warn("DataFrame prix vide")
        return {
            "pattern_type": "none",
            "turning_points": [],
            "max_movement_pips": 0.0
        }
    
    # Normaliser colonnes
    if "datetime" in prices_df.columns:
        prices_df = prices_df.rename(columns={"datetime": "ts_utc"})
    
    prices_df["ts_utc"] = pd.to_datetime(prices_df["ts_utc"])
    prices_df = prices_df.sort_values("ts_utc").reset_index(drop=True)
    
    # Prix après t0
    prices_after = prices_df[prices_df["ts_utc"] >= t0].copy()
    
    if len(prices_after) < 2:
        warnings.warn("Pas assez de prix après t0")
        return {
            "pattern_type": "none",
            "turning_points": [],
            "max_movement_pips": 0.0
        }
    
    # Baseline = prix juste avant t0 (ou premier prix après)
    baseline_idx = prices_df[prices_df["ts_utc"] <= t0].index
    if len(baseline_idx) > 0:
        baseline_price = prices_df.loc[baseline_idx[-1], "close"]
    else:
        baseline_price = prices_after.iloc[0]["close"]
    
    # Calculer ATR intraday (approximatif: range haut-bas moyen)
    if "high" in prices_df.columns and "low" in prices_df.columns:
        # Utiliser high-low si disponible
        daily_ranges = (prices_df["high"] - prices_df["low"]) * 10000  # en pips
        atr = daily_ranges.mean()
    else:
        # Approximation depuis close-to-close (mouvement moyen)
        returns = prices_df["close"].diff().abs() * 10000  # en pips
        atr = returns.mean() * 3  # Multiplier par 3 pour approximation range
    
    threshold_pips = max(min_movement_pips, atr * atr_multiplier)
    
    # Calculer returns en pips depuis baseline
    prices_after["pips_from_baseline"] = (prices_after["close"] - baseline_price) * 10000
    
    # Détecter turning points (extrema locaux simplifiés)
    turning_points = []
    prices_vals = prices_after["pips_from_baseline"].values
    prices_times = prices_after["ts_utc"].values
    prices_prices = prices_after["close"].values
    
    # Algorithme simple: peak si valeur > voisins ET > threshold
    for i in range(1, len(prices_vals) - 1):
        val = prices_vals[i]
        if abs(val) < threshold_pips:
            continue
        
        if val > prices_vals[i-1] and val > prices_vals[i+1] and val > threshold_pips:
            turning_points.append((prices_times[i], prices_prices[i], "peak"))
        elif val < prices_vals[i-1] and val < prices_vals[i+1] and abs(val) > threshold_pips:
            turning_points.append((prices_times[i], prices_prices[i], "trough"))
    
    # Classifier pattern
    max_movement = abs(prices_vals).max()
    
    if len(turning_points) == 0:
        # Pas de turning point clair → single wave ou none
        if max_movement < threshold_pips:
            pattern_type = "none"
        else:
            pattern_type = "single_wave"
    elif len(turning_points) == 1:
        pattern_type = "single_wave"
    elif len(turning_points) == 2:
        # Vérifier si double wave (2 pics même direction)
        tp1_type = turning_points[0][2]
        tp2_type = turning_points[1][2]
        if tp1_type == tp2_type:
            pattern_type = "double_wave"
        else:
            pattern_type = "zigzag"
    else:
        pattern_type = "zigzag"
    
    return {
        "pattern_type": pattern_type,
        "turning_points": turning_points,
        "max_movement_pips": float(max_movement),
        "baseline_price": float(baseline_price),
        "threshold_pips": float(threshold_pips)
    }


def compute_day_prediction(
    date_str: str,
    conn: duckdb.DuckDBPyConnection,
    pattern_params: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Pipeline complète pour calculer la prédiction d'une journée.
    
    Args:
        date_str: Date au format 'YYYY-MM-DD'
        conn: Connexion DuckDB
        pattern_params: Paramètres pour detect_pattern_from_prices (optionnel)
        
    Returns:
        Dict avec toutes les prédictions et métriques
    """
    if pattern_params is None:
        pattern_params = {}
    
    warnings.warn(f"=== Compute Day Prediction: {date_str} ===")
    
    # 1. Charger événements enrichis
    df_events = load_events_enriched(date_str, conn)
    
    if df_events.empty:
        warnings.warn(f"Aucun événement pour {date_str}")
        return {
            "date": date_str,
            "error": "no_events"
        }
    
    # 2. Calculer direction/impact depuis surprises
    direction_impact = compute_direction_impact_from_surprises(df_events)
    
    # 3. Charger vol prédite
    pred_vol_pips = compute_pred_vol_pips(date_str, conn)
    
    # 4. Charger prix et détecter pattern
    query_prices = """
        SELECT datetime as ts_utc, close, high, low
        FROM prices_finnhub_m5
        WHERE datetime >= CAST(? AS TIMESTAMP)
          AND datetime < CAST(? AS TIMESTAMP) + INTERVAL '1 day'
        ORDER BY datetime
    """
    df_prices = conn.execute(query_prices, [f"{date_str} 00:00:00", f"{date_str} 00:00:00"]).df()
    
    if df_prices.empty:
        warnings.warn(f"Aucun prix pour {date_str}")
        return {
            "date": date_str,
            "error": "no_prices",
            **direction_impact
        }
    
    # Trouver t0 (premier événement core, ou premier événement si aucun core)
    core_events = df_events[df_events["is_core"]]
    if not core_events.empty:
        t0 = pd.to_datetime(core_events.iloc[0]["ts_utc"])
    else:
        t0 = pd.to_datetime(df_events.iloc[0]["ts_utc"])
    
    # Détecter pattern
    pattern_result = detect_pattern_from_prices(df_prices, t0, **pattern_params)
    
    # 5. Résultat final
    return {
        "date": date_str,
        "t0": t0.isoformat(),
        "n_events": len(df_events),
        "n_core_events": df_events["is_core"].sum(),
        "pred_vol_pips": pred_vol_pips,
        **direction_impact,
        **pattern_result
    }


if __name__ == "__main__":
    # Test rapide
    DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        result = compute_day_prediction("2025-08-01", conn)
        print("\n=== RÉSULTAT ===")
        for k, v in result.items():
            print(f"{k}: {v}")
    finally:
        conn.close()

