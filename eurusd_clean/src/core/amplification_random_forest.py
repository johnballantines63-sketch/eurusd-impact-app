#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random Forest Global pour Prédiction d'Amplification

✅ RESTAURATION PHASE 1 : Module RF global selon documentation référence

Utilisé comme fallback si pas assez de clusters identiques (< 5) pour RF par date.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def predict_amplification_random_forest(
    trend_r2: float = 0.0,
    trend_duration_h: float = 0.0,
    trend_amplitude_pips: float = 0.0,
    impact_base_pips: float = 0.0,
    num_events: int = 0,
    pattern_impact_pips: float = 0.0,
    pattern_wave1_pips: float = 0.0,
    pattern_wave2_pips: float = 0.0,
    core_score: float = 0.0,  # ✅ AJOUT : Feature core_score (REF-020)
    results_df: Optional[pd.DataFrame] = None
) -> float:
    """
    Prédit l'amplification avec Random Forest global.
    
    ✅ RESTAURATION PHASE 1 : RF global selon documentation référence
    
    Méthode :
    - Entraîne un modèle RF sur toutes les données historiques disponibles
    - Utilise les features de référence
    - Fallback vers moyenne si pas assez de données
    
    Args:
        trend_r2: R² de la tendance
        trend_duration_h: Durée tendance en heures
        trend_amplitude_pips: Amplitude tendance (pips)
        impact_base_pips: Impact de base calculé
        num_events: Nombre d'événements
        pattern_impact_pips: Impact pattern détecté (si disponible)
        pattern_wave1_pips: Wave 1 pips (si disponible)
        pattern_wave2_pips: Wave 2 pips (si disponible)
        results_df: DataFrame avec résultats historiques (trends + impacts)
    
    Returns:
        Amplification prédite (ratio)
    """
    # Si pas assez de données historiques, utiliser moyenne
    if results_df is None or results_df.empty:
        return 1.0
    
    # Filtrer données valides (avec impact réel et tendance)
    valid_data = results_df[
        (results_df['impact_reel'] > 0) &
        (results_df['impact_base'] > 0)
    ].copy()
    
    if len(valid_data) < 3:
        # Pas assez de données pour RF, utiliser moyenne
        if 'amplification_parfaite' in results_df.columns:
            return results_df['amplification_parfaite'].mean()
        return 1.0
    
    # Préparer features historiques
    features_list = []
    amplifications_list = []
    
    for _, row in valid_data.iterrows():
        # Extraire features depuis results_df
        feat_r2 = row.get('r2', 0.0) if 'r2' in row else 0.0
        feat_duration_h = row.get('duration_hours', 0.0) if 'duration_hours' in row else 0.0
        feat_amplitude = row.get('amplitude_pips', 0.0) if 'amplitude_pips' in row else 0.0
        feat_impact_base = row.get('impact_base', 0.0)
        feat_num_events = row.get('num_events', 0)
        
        # Patterns non disponibles dans results_df historique (mettre à 0)
        feat_pattern_impact = 0.0
        feat_pattern_wave1 = 0.0
        feat_pattern_wave2 = 0.0
        
        features = {
            'trend_r2': feat_r2,
            'trend_duration_h': feat_duration_h,
            'trend_amplitude_pips': feat_amplitude,
            'impact_base_pips': feat_impact_base,
            'num_events': feat_num_events,
            'pattern_impact_pips': feat_pattern_impact,
            'pattern_wave1_pips': feat_pattern_wave1,
            'pattern_wave2_pips': feat_pattern_wave2,
            'core_score': 0.0  # ✅ AJOUT : Feature core_score (0.0 pour historique, sera amélioré)
        }
        
        amplification_parfaite = row.get('amplification_parfaite', 1.0)
        
        features_list.append(features)
        amplifications_list.append(amplification_parfaite)
    
    # Entraîner Random Forest global
    try:
        from core.random_forest_amplification import train_random_forest_amplification
        
        rf_model, scaler, feature_names = train_random_forest_amplification(
            features_list=features_list,
            amplifications_ideales=amplifications_list,
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            random_state=42
        )
        
        # Features pour prédiction
        features_target = {
            'trend_r2': trend_r2,
            'trend_duration_h': trend_duration_h,
            'trend_amplitude_pips': trend_amplitude_pips,
            'impact_base_pips': impact_base_pips,
            'num_events': num_events,
            'pattern_impact_pips': pattern_impact_pips,
            'pattern_wave1_pips': pattern_wave1_pips,
            'pattern_wave2_pips': pattern_wave2_pips,
            'core_score': core_score  # ✅ AJOUT : Feature core_score (REF-020)
        }
        
        # Prédire
        from core.random_forest_amplification import predict_amplification_with_rf
        
        amplification_predite = predict_amplification_with_rf(
            rf_model=rf_model,
            scaler=scaler,
            feature_names=feature_names,
            features=features_target
        )
        
        return amplification_predite
        
    except Exception as e:
        # En cas d'erreur, utiliser moyenne
        if 'amplification_parfaite' in results_df.columns:
            return results_df['amplification_parfaite'].mean()
        return 1.0

