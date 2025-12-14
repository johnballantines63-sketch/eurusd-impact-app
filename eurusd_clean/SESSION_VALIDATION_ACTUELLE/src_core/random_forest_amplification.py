#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random Forest pour prédiction d'amplification

Méthode en 4 étapes :
1. Définir le noyau dur pour le cas à prédire
2. Trouver les dates avec clusters identiques (même noyau dur) dans la DB
3. Pour chaque date trouvée :
   - Calculer la prédiction avec le pipeline complet
   - Calculer l'amplification idéale (amplification qui donnerait la prédiction parfaite)
4. Entraîner Random Forest sur ces amplifications idéales et appliquer au cas initial
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def calculate_ideal_amplification(
    impact_base: float,
    impact_real: float,
    adjustment_factor: float = 1.0
) -> float:
    """
    Calcule l'amplification idéale pour une date historique.
    
    L'amplification idéale est celle qui, appliquée à l'impact de base,
    donnerait exactement l'impact réel observé.
    
    Formule : amplification_ideale = impact_real / (impact_base * adjustment_factor)
    
    Args:
        impact_base: Impact de base calculé (pips)
        impact_real: Impact réel observé (pips)
        adjustment_factor: Facteur d'ajustement S/R appliqué (défaut: 1.0)
    
    Returns:
        Amplification idéale (ratio)
    """
    if impact_base <= 0:
        return 1.0
    
    denominator = impact_base * adjustment_factor
    if denominator <= 0:
        return 1.0
    
    amplification_ideale = impact_real / denominator
    return max(0.1, min(10.0, amplification_ideale))  # Limiter entre 0.1x et 10.0x


def extract_features_for_rf(
    cluster_events: pd.DataFrame,
    trend_r2: float = 0.0,
    trend_duration_h: float = 0.0,
    trend_amplitude_pips: float = 0.0,
    impact_base_pips: float = 0.0,
    num_events: int = 0,
    pattern_impact_pips: float = 0.0,
    pattern_wave1_pips: float = 0.0,
    pattern_wave2_pips: float = 0.0
) -> Dict[str, float]:
    """
    Extrait les features pour Random Forest selon documentation référence.
    
    ✅ RESTAURATION PHASE 1 : Features de référence
    Features :
    - trend_r2 : R² de la tendance
    - trend_duration_h : Durée en heures
    - trend_amplitude_pips : Amplitude en pips
    - impact_base_pips : Impact de base
    - num_events : Nombre d'événements
    - pattern_impact_pips : Impact pattern (si disponible)
    - pattern_wave1_pips : Wave 1 pips (si disponible)
    - pattern_wave2_pips : Wave 2 pips (si disponible)
    
    Args:
        cluster_events: DataFrame des événements du cluster
        trend_r2: R² de la tendance (défaut: 0.0)
        trend_duration_h: Durée tendance en heures (défaut: 0.0)
        trend_amplitude_pips: Amplitude tendance (défaut: 0.0)
        impact_base_pips: Impact de base calculé (défaut: 0.0)
        num_events: Nombre d'événements (défaut: 0)
        pattern_impact_pips: Impact pattern détecté (défaut: 0.0)
        pattern_wave1_pips: Wave 1 pips (défaut: 0.0)
        pattern_wave2_pips: Wave 2 pips (défaut: 0.0)
    
    Returns:
        Dict avec les features pour Random Forest
    """
    features = {
        'trend_r2': trend_r2,
        'trend_duration_h': trend_duration_h,
        'trend_amplitude_pips': trend_amplitude_pips,
        'impact_base_pips': impact_base_pips,
        'num_events': num_events if num_events > 0 else len(cluster_events),
        'pattern_impact_pips': pattern_impact_pips,
        'pattern_wave1_pips': pattern_wave1_pips,
        'pattern_wave2_pips': pattern_wave2_pips
    }
    
    return features


def train_random_forest_amplification(
    features_list: List[Dict[str, float]],
    amplifications_ideales: List[float],
    n_estimators: int = 100,
    max_depth: int = 5,
    min_samples_split: int = 5,
    random_state: int = 42
) -> Tuple[RandomForestRegressor, StandardScaler, List[str]]:
    """
    Entraîne un modèle Random Forest pour prédire l'amplification.
    
    Args:
        features_list: Liste de dictionnaires de features pour chaque cluster historique
        amplifications_ideales: Liste des amplifications idéales correspondantes
        n_estimators: Nombre d'arbres dans la forêt (défaut: 100)
        max_depth: Profondeur maximale des arbres (défaut: 5)
        min_samples_split: Nombre minimum d'échantillons pour split (défaut: 5)
        random_state: Seed pour reproductibilité (défaut: 42)
    
    Returns:
        Tuple (modèle RF entraîné, scaler, liste des noms de features)
    """
    if len(features_list) < 3:
        raise ValueError(f"Pas assez de données pour entraîner RF (minimum 3, reçu {len(features_list)})")
    
    # Convertir en DataFrame
    df_features = pd.DataFrame(features_list)
    
    # Extraire noms de features
    feature_names = list(df_features.columns)
    
    # Préparer données
    X = df_features.values
    y = np.array(amplifications_ideales)
    
    # Standardiser features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Entraîner Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=random_state,
        n_jobs=-1
    )
    
    rf_model.fit(X_scaled, y)
    
    return rf_model, scaler, feature_names


def predict_amplification_with_rf(
    rf_model: RandomForestRegressor,
    scaler: StandardScaler,
    feature_names: List[str],
    features: Dict[str, float]
) -> float:
    """
    Prédit l'amplification avec un modèle Random Forest entraîné.
    
    Args:
        rf_model: Modèle Random Forest entraîné
        scaler: StandardScaler utilisé pour l'entraînement
        feature_names: Liste des noms de features (dans l'ordre)
        features: Dict avec les features pour la prédiction
    
    Returns:
        Amplification prédite (ratio)
    """
    # Créer DataFrame avec features dans le bon ordre
    features_df = pd.DataFrame([features])
    
    # S'assurer que toutes les features sont présentes
    for feat_name in feature_names:
        if feat_name not in features_df.columns:
            features_df[feat_name] = 0.0
    
    # Réordonner selon feature_names
    X = features_df[feature_names].values
    
    # Standardiser
    X_scaled = scaler.transform(X)
    
    # Prédire
    amplification_predite = rf_model.predict(X_scaled)[0]
    
    # Limiter entre 0.1x et 10.0x
    return max(0.1, min(10.0, amplification_predite))


def get_feature_importance(
    rf_model: RandomForestRegressor,
    feature_names: List[str]
) -> pd.DataFrame:
    """
    Retourne l'importance des features du modèle Random Forest.
    
    Args:
        rf_model: Modèle Random Forest entraîné
        feature_names: Liste des noms de features
    
    Returns:
        DataFrame avec feature et importance
    """
    importances = rf_model.feature_importances_
    
    df_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    return df_importance


def train_rf_from_identical_clusters(
    identical_clusters: List[Dict],
    results_df: Optional[pd.DataFrame],
    executor,  # PipelineExecutor instance
    min_clusters: int = 5
) -> Optional[Tuple[RandomForestRegressor, StandardScaler, List[str]]]:
    """
    Implémente la méthode en 4 étapes pour entraîner Random Forest :
    
    1. Noyau dur déjà défini (dans cluster_info)
    2. Clusters identiques déjà trouvés (identical_clusters)
    3. Pour chaque cluster identique :
       - Recalculer impact_base avec pipeline complet (méthode Session 88)
       - Obtenir impact_real depuis résultats étape 6
       - Calculer amplification_ideale
       - Extraire features (tendance, surprises, etc.)
    4. Entraîner Random Forest sur amplifications idéales
    
    Args:
        identical_clusters: Liste des clusters identiques trouvés
        results_df: DataFrame avec résultats étape 6 (impact_base, impact_reel, amplification_parfaite)
        executor: Instance de PipelineExecutor pour recalculer impacts
        min_clusters: Nombre minimum de clusters pour entraîner RF (défaut: 5)
    
    Returns:
        Tuple (modèle RF, scaler, feature_names) ou None si pas assez de données
    """
    if len(identical_clusters) < min_clusters:
        return None
    
    if results_df is None or results_df.empty:
        return None
    
    # Vérifier que results_df contient les colonnes nécessaires
    required_cols = ['impact_base', 'impact_reel', 'cluster_date']
    if not all(col in results_df.columns for col in required_cols):
        return None
    
    # Filtrer clusters avec impact réel valide
    valid_results = results_df[results_df['impact_reel'] > 0].copy()
    if len(valid_results) < min_clusters:
        return None
    
    features_list = []
    amplifications_ideales = []
    
    # Pour chaque cluster historique valide
    for _, row in valid_results.iterrows():
        cluster_date = row['cluster_date']
        impact_base = row['impact_base']
        impact_real = row['impact_reel']
        adjustment_factor = 1.0  # Pas d'ajustement S/R pour historique (simplifié)
        
        # Trouver le cluster correspondant dans identical_clusters
        cluster_hist = None
        for cluster in identical_clusters:
            if cluster.get('date') == cluster_date:
                cluster_hist = cluster
                break
        
        if cluster_hist is None:
            continue
        
        cluster_events = cluster_hist['cluster']['events']
        
        # Calculer amplification idéale
        amplification_ideale = calculate_ideal_amplification(
            impact_base=impact_base,
            impact_real=impact_real,
            adjustment_factor=adjustment_factor
        )
        
        # Obtenir tendance pour ce cluster (si disponible dans results_df)
        # Note: results_df contient les colonnes de trends_df fusionnées dans etape7
        trend_r2 = row.get('r2', 0.0) if 'r2' in results_df.columns else 0.0
        trend_duration_h = row.get('duration_hours', 0.0) if 'duration_hours' in results_df.columns else 0.0
        trend_amplitude_pips = row.get('amplitude_pips', 0.0) if 'amplitude_pips' in results_df.columns else 0.0
        
        # Extraire features (features de référence)
        features = extract_features_for_rf(
            cluster_events=cluster_events,
            trend_r2=trend_r2,
            trend_duration_h=trend_duration_h,
            trend_amplitude_pips=trend_amplitude_pips,
            impact_base_pips=impact_base,
            num_events=len(cluster_events),
            pattern_impact_pips=0.0,  # Patterns non disponibles pour historique
            pattern_wave1_pips=0.0,
            pattern_wave2_pips=0.0
        )
        
        features_list.append(features)
        amplifications_ideales.append(amplification_ideale)
    
    # Vérifier qu'on a assez de données
    if len(features_list) < min_clusters:
        return None
    
    # Entraîner Random Forest
    try:
        rf_model, scaler, feature_names = train_random_forest_amplification(
            features_list=features_list,
            amplifications_ideales=amplifications_ideales,
            n_estimators=100,
            max_depth=5,
            min_samples_split=5,
            random_state=42
        )
        
        return rf_model, scaler, feature_names
    except Exception as e:
        # En cas d'erreur, retourner None
        return None
