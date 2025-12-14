#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGATION IMPACT DE BASE - ÉTAPE 8.1
==========================================

Trace en détail le calcul de l'impact de base dans l'étape 8.1
pour comprendre pourquoi il est 250.82 pips.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import pytz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from run_pipeline_complete import PipelineExecutor
from core.formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d
)

TZ_BERN = pytz.timezone('Europe/Zurich')

def investiguer_impact_base():
    """Investigation détaillée du calcul de l'impact de base"""
    
    date_str = '2025-08-01'
    
    print("\n" + "=" * 80)
    print(f"  INVESTIGATION IMPACT DE BASE - ÉTAPE 8.1 - {date_str}")
    print("=" * 80)
    print()
    
    executor = PipelineExecutor(DB_PATH, verbose=False)
    
    # Charger les événements
    events = executor.etape1_charger_evenements(date_str)
    
    # Détecter le cluster
    clusters = executor.etape2_detecter_clusters(events, window_minutes=30)
    
    if not clusters:
        print("❌ Aucun cluster détecté")
        return
    
    cluster_cible = clusters[0]
    cluster_events = cluster_cible['events']
    
    print(f"📊 Cluster cible :")
    print(f"   Nombre événements : {len(cluster_events)}")
    print(f"   Anchor time : {cluster_cible.get('anchor_time', 'N/A')}")
    print()
    
    print("=" * 80)
    print("  CALCUL DÉTAILLÉ IMPACT DE BASE (ÉTAPE 8.1)")
    print("=" * 80)
    print()
    
    # Reproduire exactement le calcul de l'étape 8.1
    total_impact_base = 0.0
    num_events = len(cluster_events)
    
    print("📋 CALCUL POUR CHAQUE ÉVÉNEMENT :")
    print()
    print(f"{'Event':<50} {'Score':<8} {'Actual':<12} {'Estimate':<12} {'Surprise':<10} {'Score Adj':<10} {'Impact Indiv':<12}")
    print("-" * 120)
    
    impacts_individuels = []
    
    for idx, (_, event) in enumerate(cluster_events.iterrows(), 1):
        base_score = event.get('empirical_score', 44.0)
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        
        # Calculer surprise
        surprise_pct = 0.0
        if actual is not None and estimate is not None and estimate != 0:
            surprise_pct = abs(actual - estimate) / abs(estimate) * 100
        
        # Ajuster score selon surprise
        adjusted_score = calculate_adjusted_empirical_score(
            base_empirical_score=base_score,
            surprise_pct=surprise_pct
        )
        
        # Calculer impact individuel (événement isolé)
        impact_individuel = calculate_impact_d(
            empirical_score=adjusted_score,
            num_events=1,  # Impact individuel
            amplification=1.0,  # Pas d'amplification ici
            correction_factor=1.0  # Pas de correction vectorielle ici
        )
        
        impacts_individuels.append({
            'event': event.get('event_title', 'N/A')[:48],
            'base_score': base_score,
            'actual': actual,
            'estimate': estimate,
            'surprise_pct': surprise_pct,
            'adjusted_score': adjusted_score,
            'impact_individuel': impact_individuel
        })
        
        total_impact_base += impact_individuel
        
        # Afficher
        event_name = event.get('event_title', 'N/A')[:48]
        actual_str = f"{actual:.2f}" if actual is not None else "N/A"
        estimate_str = f"{estimate:.2f}" if estimate is not None else "N/A"
        
        print(f"{event_name:<50} {base_score:<8.1f} {actual_str:<12} {estimate_str:<12} {surprise_pct:<10.1f} {adjusted_score:<10.1f} {impact_individuel:<12.2f}")
    
    print("-" * 120)
    print(f"{'TOTAL AVANT CORRECTION VECTORIELLE':<50} {'':<8} {'':<12} {'':<12} {'':<10} {'':<10} {total_impact_base:<12.2f}")
    print()
    
    # Appliquer correction vectorielle
    if num_events >= 2:
        impact_base_avant_correction = total_impact_base
        total_impact_base = total_impact_base * 0.758  # Correction vectorielle
        
        print("=" * 80)
        print("  CORRECTION VECTORIELLE")
        print("=" * 80)
        print()
        print(f"Nombre d'événements : {num_events}")
        print(f"Impact avant correction : {impact_base_avant_correction:.2f} pips")
        print(f"Facteur de correction : 0.758")
        print(f"Impact après correction : {total_impact_base:.2f} pips")
        print(f"Réduction : {impact_base_avant_correction - total_impact_base:.2f} pips ({((impact_base_avant_correction - total_impact_base) / impact_base_avant_correction * 100):.1f}%)")
        print()
    
    impact_base = total_impact_base
    
    print("=" * 80)
    print("  RÉSULTAT FINAL")
    print("=" * 80)
    print()
    print(f"Impact de base final : {impact_base:.2f} pips")
    print()
    
    # Analyse
    print("=" * 80)
    print("  ANALYSE")
    print("=" * 80)
    print()
    
    # Comparer avec impact réel
    impact_reel = 188.4  # Valeur connue
    
    # Pour obtenir 188.4 pips avec amplification 6.223x
    impact_base_attendu = impact_reel / 6.223
    print(f"Impact réel : {impact_reel:.1f} pips")
    print(f"Amplification utilisée : 6.223x")
    print(f"Impact de base attendu : {impact_reel:.1f} / 6.223 = {impact_base_attendu:.2f} pips")
    print()
    
    print(f"Impact de base calculé : {impact_base:.2f} pips")
    print(f"Impact de base attendu : {impact_base_attendu:.2f} pips")
    print(f"Différence : {impact_base - impact_base_attendu:.2f} pips")
    print(f"Ratio : {impact_base / impact_base_attendu:.2f}x trop élevé")
    print()
    
    # Analyse par événement
    print("=" * 80)
    print("  TOP 5 ÉVÉNEMENTS PAR IMPACT INDIVIDUEL")
    print("=" * 80)
    print()
    
    impacts_sorted = sorted(impacts_individuels, key=lambda x: x['impact_individuel'], reverse=True)
    
    print(f"{'Event':<50} {'Score':<8} {'Surprise':<10} {'Impact':<12} {'% du total':<10}")
    print("-" * 90)
    
    for i, item in enumerate(impacts_sorted[:5], 1):
        pct_du_total = (item['impact_individuel'] / impact_base_avant_correction * 100) if num_events >= 2 else (item['impact_individuel'] / total_impact_base * 100)
        print(f"{item['event']:<50} {item['base_score']:<8.1f} {item['surprise_pct']:<10.1f} {item['impact_individuel']:<12.2f} {pct_du_total:<10.1f}%")
    
    print()
    
    # Vérifier formule calculate_impact_d
    print("=" * 80)
    print("  VÉRIFICATION FORMULE calculate_impact_d")
    print("=" * 80)
    print()
    
    # Test avec un score moyen
    score_moyen = sum([item['adjusted_score'] for item in impacts_individuels]) / len(impacts_individuels)
    impact_test = calculate_impact_d(
        empirical_score=score_moyen,
        num_events=1,
        amplification=1.0,
        correction_factor=1.0
    )
    
    print(f"Score moyen ajusté : {score_moyen:.2f}")
    print(f"Impact pour 1 événement (score moyen) : {impact_test:.2f} pips")
    print(f"Impact si on multiplie par {num_events} événements : {impact_test * num_events:.2f} pips")
    print(f"Impact réel obtenu (somme) : {impact_base_avant_correction:.2f} pips")
    print()
    
    if abs(impact_test * num_events - impact_base_avant_correction) < 1.0:
        print("✅ La somme des impacts individuels est cohérente avec la formule")
    else:
        print("⚠️  La somme des impacts individuels diffère de la formule × nombre d'événements")
        print(f"   → Différence : {abs(impact_test * num_events - impact_base_avant_correction):.2f} pips")
    print()
    
    print("=" * 80)
    print()

if __name__ == "__main__":
    investiguer_impact_base()




