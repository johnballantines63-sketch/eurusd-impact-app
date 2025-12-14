#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic de l'impact de base pour le 1er août 2025
"""

import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path('scripts').parent / 'src'))
sys.path.insert(0, str(Path('scripts').parent / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor
from core.formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    get_event_direction,
    infer_family_from_event_key
)

executor = PipelineExecutor(DB_PATH, verbose=False)

# Étape 1 : Charger événements
events = executor.etape1_charger_evenements('2025-08-01')
print(f'Événements chargés: {len(events)}')
print()

# Étape 2 : Détecter cluster
clusters = executor.etape2_detecter_clusters(events, window_minutes=30)
print(f'Clusters détectés: {len(clusters)}')
print()

if not clusters:
    print('Aucun cluster détecté')
    sys.exit(1)

cluster = clusters[0]
cluster_events = cluster['events']

print(f'Événements dans le cluster: {len(cluster_events)}')
print()

# Calculer somme vectorielle comme dans le pipeline
scores_vectoriels = []
num_events = len(cluster_events)

for _, event in cluster_events.iterrows():
    base_score = event.get('empirical_score', 44.0)
    actual = event.get('actual')
    
    # Utiliser fallback estimate → forecast → previous
    estimate_raw = event.get('estimate')
    forecast_raw = event.get('forecast')
    previous_raw = event.get('previous')
    estimate = estimate_raw if pd.notna(estimate_raw) and estimate_raw != 0 else (forecast_raw if pd.notna(forecast_raw) and forecast_raw != 0 else (previous_raw if pd.notna(previous_raw) and previous_raw != 0 else None))
    
    # Déterminer famille
    family = event.get('family')
    if not family or pd.isna(family):
        event_key = event.get('event_key', '')
        event_title = event.get('event_title') or event.get('label', '')
        family = infer_family_from_event_key(event_key, event_title)
    
    # Calculer surprise
    surprise_pct = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_pct = abs(actual - estimate) / abs(estimate) * 100
    
    # Ajuster score
    adjusted_score = calculate_adjusted_empirical_score(
        base_empirical_score=base_score,
        surprise_pct=surprise_pct
    )
    
    # Calculer surprise signée
    surprise_signed = 0.0
    if actual is not None and estimate is not None and estimate != 0:
        surprise_signed = actual - estimate
    
    # Direction
    direction = get_event_direction(family, surprise_signed)
    
    # Score vectoriel
    score_vectoriel = adjusted_score * direction
    scores_vectoriels.append(score_vectoriel)

# Somme vectorielle
score_vectoriel_total = sum(scores_vectoriels)
score_vectoriel_moyen = score_vectoriel_total / num_events if num_events > 0 else 0.0

print('=' * 100)
print('CALCUL IMPACT DE BASE')
print('=' * 100)
print()
print(f'Score vectoriel total: {score_vectoriel_total:.2f}')
print(f'Score vectoriel moyen: {score_vectoriel_moyen:.2f}')
print(f'Nombre événements: {num_events}')
print()

# Calculer impact avec num_events=10
impact_base_10 = calculate_impact_d(
    empirical_score=abs(score_vectoriel_moyen),
    num_events=num_events,
    amplification=1.0,
    correction_factor=0.758
)

# Calculer impact avec num_events=1
impact_base_1 = calculate_impact_d(
    empirical_score=abs(score_vectoriel_moyen),
    num_events=1,
    amplification=1.0,
    correction_factor=0.758
)

print(f'Impact de base (num_events={num_events}): {impact_base_10:.2f} pips')
print(f'Impact de base (num_events=1): {impact_base_1:.2f} pips')
print()

# Vérifier ce qui est utilisé dans le pipeline
print('Dans le pipeline (ligne 1023): num_events du cluster est utilisé')
print(f'Donc impact de base attendu: {impact_base_10:.2f} pips')
print()

# Vérifier l'amplification
amplification = 6.223  # Session 88 pour surprise 266.7%
impact_amplifie = impact_base_10 * amplification
print(f'Avec amplification {amplification:.3f}x: {impact_amplifie:.2f} pips')
print()

# Vérifier l'ajustement S/R
adjustment_factor = 1.15  # +15%
impact_ajuste = impact_amplifie * adjustment_factor
print(f'Avec ajustement S/R {adjustment_factor:.3f}x: {impact_ajuste:.2f} pips')
print()

print('Impact réel: 188.4 pips')
print(f'Erreur: {abs(impact_ajuste - 188.4):.2f} pips')




