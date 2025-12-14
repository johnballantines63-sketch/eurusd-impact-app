#!/usr/bin/env python3
"""
Investigation : Pourquoi les mouvements FORT/TRÈS_FORT sont-ils si sous-estimés ?

Objectif :
1. Analyser en détail les composantes des prédictions pour mouvements forts
2. Comparer avec les mouvements MOYEN/FAIBLE
3. Identifier les facteurs manquants ou mal calibrés
4. Proposer des corrections

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src' / 'core'))

# Imports des formules validées
try:
    from src.core.formulas_validated import (
        calculate_adjusted_empirical_score,
        calculate_impact_d,
        calculate_amplification_extended
    )
except ImportError:
    def calculate_adjusted_empirical_score(base_score: float, surprise_pct: float) -> float:
        if surprise_pct < 5.0:
            factor = 1.0
        elif surprise_pct < 15.0:
            factor = 1.0 + (surprise_pct - 5.0) / 10.0 * 0.5
        elif surprise_pct < 30.0:
            factor = 1.5 + (surprise_pct - 15.0) / 15.0 * 0.4
        else:
            factor = 1.9
        return base_score * factor
    
    def calculate_impact_d(empirical_score: float, num_events: int = 1, 
                          amplification: float = 1.0, correction_factor: float = 0.758) -> float:
        if num_events >= 2:
            intercept = -10.47
            coefficient = 0.477
        else:
            intercept = -7.08
            coefficient = 0.419
        impact_brut = intercept + (coefficient * empirical_score)
        impact_amplifie = abs(impact_brut) * amplification
        return impact_amplifie * correction_factor
    
    def calculate_amplification_extended(surprise_pct: float) -> float:
        abs_surprise = abs(surprise_pct)
        if abs_surprise < 5.0:
            return 1.0
        elif abs_surprise < 15.0:
            return 1.0 + (abs_surprise - 5.0) / 10.0 * 0.5
        elif abs_surprise < 30.0:
            return 1.5 + (abs_surprise - 15.0) / 15.0 * 0.4
        elif abs_surprise < 100.0:
            return 1.9 + (abs_surprise - 30.0) / 70.0 * 1.1
        elif abs_surprise < 200.0:
            return 3.0 + (abs_surprise - 100.0) / 100.0 * 1.0
        else:
            return min(5.5 + 0.371 * np.log10(abs_surprise - 199), 10.0)


def calculate_prediction_detailed(row: pd.Series) -> Dict:
    """
    Calcule la prédiction avec tous les détails intermédiaires
    """
    base_score = row['avg_base_empirical_score']
    adjusted_score = row['avg_adjusted_empirical_score']
    surprise_pct = row['avg_surprise_pct']
    num_events = row['n_events_total']
    
    # Score ajusté
    if pd.notna(adjusted_score) and adjusted_score > 0:
        empirical_score = adjusted_score
        score_adjusted_manually = False
    elif pd.notna(base_score) and base_score > 0:
        empirical_score = calculate_adjusted_empirical_score(base_score, surprise_pct)
        score_adjusted_manually = True
    else:
        empirical_score = 0.0
        score_adjusted_manually = False
    
    # Amplification
    amplification = 1.0
    if pd.notna(surprise_pct) and surprise_pct > 15.0:
        amplification = calculate_amplification_extended(surprise_pct)
        amplification = min(amplification, 3.0)  # Limité à 3.0
    
    # Impact brut (avant amplification)
    if num_events >= 2:
        intercept = -10.47
        coefficient = 0.477
    else:
        intercept = -7.08
        coefficient = 0.419
    
    impact_brut = intercept + (coefficient * empirical_score)
    impact_amplifie = abs(impact_brut) * amplification
    impact_final = impact_amplifie * 0.758  # Correction vectorielle
    
    return {
        'base_score': base_score,
        'empirical_score_used': empirical_score,
        'surprise_pct': surprise_pct,
        'amplification': amplification,
        'num_events': num_events,
        'impact_brut': impact_brut,
        'impact_amplifie': impact_amplifie,
        'impact_final': impact_final,
        'impact_real': row['peak_pips'],
        'ratio': impact_final / row['peak_pips'] if row['peak_pips'] > 0 else 0.0
    }


def investigate_strong_movements():
    """
    Investigation principale
    """
    
    print("=" * 80)
    print("INVESTIGATION : SOUS-ESTIMATION MOUVEMENTS FORT/TRÈS_FORT")
    print("=" * 80)
    print()
    
    # 1. Charger données
    db_file = Path(__file__).parent.parent / 'outputs' / 'predictable_movements_database.csv'
    df = pd.read_csv(db_file)
    
    # Filtrer mouvements FORT/TRÈS_FORT avec US
    df_strong = df[
        (df['movement_class'].isin(['FORT', 'TRÈS_FORT'])) &
        (df['n_events_us'] > 0) & 
        (df['avg_base_empirical_score'] > 0)
    ].copy()
    
    print(f"📊 {len(df_strong)} mouvements FORT/TRÈS_FORT analysés")
    print()
    
    # 2. Calculer prédictions détaillées
    print("📊 ÉTAPE 1 : Calcul prédictions détaillées")
    print("-" * 80)
    
    details = []
    for idx, row in df_strong.iterrows():
        detail = calculate_prediction_detailed(row)
        detail['movement_class'] = row['movement_class']
        detail['date'] = row['date']
        details.append(detail)
    
    df_details = pd.DataFrame(details)
    
    # 3. Comparer avec mouvements MOYEN/FAIBLE
    print("📊 ÉTAPE 2 : Comparaison avec mouvements MOYEN/FAIBLE")
    print("-" * 80)
    
    df_weak = df[
        (df['movement_class'].isin(['MOYEN', 'FAIBLE'])) &
        (df['n_events_us'] > 0) & 
        (df['avg_base_empirical_score'] > 0)
    ].copy()
    
    details_weak = []
    for idx, row in df_weak.iterrows():
        detail = calculate_prediction_detailed(row)
        detail['movement_class'] = row['movement_class']
        details_weak.append(detail)
    
    df_details_weak = pd.DataFrame(details_weak)
    
    # 4. Analyse comparative
    print("📊 ÉTAPE 3 : Analyse comparative")
    print("-" * 80)
    print()
    
    print("🔍 COMPARAISON FACTEURS D'ENTRÉE :")
    print()
    print(f"{'Facteur':<30} {'FORT/TRÈS_FORT':<20} {'MOYEN/FAIBLE':<20} {'Ratio':<15}")
    print("-" * 85)
    
    # Scores
    score_strong = df_strong['avg_base_empirical_score'].mean()
    score_weak = df_weak['avg_base_empirical_score'].mean()
    print(f"{'Score empirique base':<30} {score_strong:>18.2f}   {score_weak:>18.2f}   {score_strong/score_weak:>13.2f}x")
    
    score_adj_strong = df_strong['avg_adjusted_empirical_score'].mean()
    score_adj_weak = df_weak['avg_adjusted_empirical_score'].mean()
    print(f"{'Score empirique ajusté':<30} {score_adj_strong:>18.2f}   {score_adj_weak:>18.2f}   {score_adj_strong/score_adj_weak:>13.2f}x")
    
    # Surprises
    surprise_strong = df_strong['avg_surprise_pct'].mean()
    surprise_weak = df_weak['avg_surprise_pct'].mean()
    print(f"{'Surprise moyenne %':<30} {surprise_strong:>18.2f}   {surprise_weak:>18.2f}   {surprise_strong/surprise_weak:>13.2f}x")
    
    # Nombre d'événements
    events_strong = df_strong['n_events_total'].mean()
    events_weak = df_weak['n_events_total'].mean()
    print(f"{'Nombre événements':<30} {events_strong:>18.1f}   {events_weak:>18.1f}   {events_strong/events_weak:>13.2f}x")
    
    # Impact réel
    impact_strong = df_strong['peak_pips'].mean()
    impact_weak = df_weak['peak_pips'].mean()
    print(f"{'Impact réel moyen':<30} {impact_strong:>18.1f}   {impact_weak:>18.1f}   {impact_strong/impact_weak:>13.2f}x")
    print()
    
    print("🔍 COMPARAISON COMPOSANTES PRÉDICTION :")
    print()
    print(f"{'Composante':<30} {'FORT/TRÈS_FORT':<20} {'MOYEN/FAIBLE':<20} {'Ratio':<15}")
    print("-" * 85)
    
    # Scores utilisés
    score_used_strong = df_details['empirical_score_used'].mean()
    score_used_weak = df_details_weak['empirical_score_used'].mean()
    print(f"{'Score utilisé (ajusté)':<30} {score_used_strong:>18.2f}   {score_used_weak:>18.2f}   {score_used_strong/score_used_weak:>13.2f}x")
    
    # Amplification
    amp_strong = df_details['amplification'].mean()
    amp_weak = df_details_weak['amplification'].mean()
    print(f"{'Amplification moyenne':<30} {amp_strong:>18.2f}   {amp_weak:>18.2f}   {amp_strong/amp_weak:>13.2f}x")
    
    # Impact brut
    impact_brut_strong = df_details['impact_brut'].abs().mean()
    impact_brut_weak = df_details_weak['impact_brut'].abs().mean()
    print(f"{'Impact brut (avant amplif)':<30} {impact_brut_strong:>18.2f}   {impact_brut_weak:>18.2f}   {impact_brut_strong/impact_brut_weak:>13.2f}x")
    
    # Impact amplifié
    impact_amp_strong = df_details['impact_amplifie'].mean()
    impact_amp_weak = df_details_weak['impact_amplifie'].mean()
    print(f"{'Impact amplifié':<30} {impact_amp_strong:>18.2f}   {impact_amp_weak:>18.2f}   {impact_amp_strong/impact_amp_weak:>13.2f}x")
    
    # Impact final
    impact_final_strong = df_details['impact_final'].mean()
    impact_final_weak = df_details_weak['impact_final'].mean()
    print(f"{'Impact final (prédit)':<30} {impact_final_strong:>18.2f}   {impact_final_weak:>18.2f}   {impact_final_strong/impact_final_weak:>13.2f}x")
    print()
    
    # 5. Identifier le problème
    print("🔍 DIAGNOSTIC :")
    print("-" * 80)
    print()
    
    # Ratio impact réel
    ratio_impact_real = impact_strong / impact_weak
    print(f"1️⃣ Impact réel FORT/FAIBLE = {ratio_impact_real:.2f}x")
    
    # Ratio impact prédit
    ratio_impact_pred = impact_final_strong / impact_final_weak
    print(f"2️⃣ Impact prédit FORT/FAIBLE = {ratio_impact_pred:.2f}x")
    
    # Ratio scores
    ratio_scores = score_used_strong / score_used_weak
    print(f"3️⃣ Score utilisé FORT/FAIBLE = {ratio_scores:.2f}x")
    
    # Ratio amplification
    ratio_amp = amp_strong / amp_weak
    print(f"4️⃣ Amplification FORT/FAIBLE = {ratio_amp:.2f}x")
    print()
    
    # Calculer ce qui manque
    print("⚠️  PROBLÈME IDENTIFIÉ :")
    print()
    
    # Si l'impact réel est 5x plus fort mais la prédiction seulement 1.5x plus forte
    # Il manque un facteur de ~3.3x
    missing_factor = ratio_impact_real / ratio_impact_pred
    print(f"   Impact réel FORT est {ratio_impact_real:.2f}x plus fort que FAIBLE")
    print(f"   Mais prédiction FORT est seulement {ratio_impact_pred:.2f}x plus forte que FAIBLE")
    print(f"   → Il manque un facteur de {missing_factor:.2f}x dans la prédiction")
    print()
    
    # Analyser pourquoi
    print("🔍 CAUSES POSSIBLES :")
    print()
    
    # Vérifier si l'amplification est suffisante
    max_amp_strong = df_details['amplification'].max()
    print(f"   1. Amplification max FORT : {max_amp_strong:.2f}x (limité à 3.0)")
    if max_amp_strong >= 2.9:
        print("      ⚠️  Amplification plafonnée à 3.0x - peut-être insuffisant pour surprises extrêmes")
    
    # Vérifier si le nombre d'événements est bien pris en compte
    print(f"   2. Nombre événements FORT : {events_strong:.1f} vs FAIBLE : {events_weak:.1f}")
    print(f"      → Ratio : {events_strong/events_weak:.2f}x")
    print(f"      → Impact réel ratio : {ratio_impact_real:.2f}x")
    if (events_strong/events_weak) < (ratio_impact_real / 2):
        print("      ⚠️  Le nombre d'événements ne semble pas expliquer l'écart")
    
    # Vérifier la formule d'impact
    print(f"   3. Formule impact : intercept={-10.47 if events_strong >= 2 else -7.08}, coeff=0.477")
    print(f"      → Pour score {score_used_strong:.1f} : impact brut = {-10.47 + 0.477*score_used_strong:.1f} pips")
    print(f"      → Après amplif {amp_strong:.2f}x : {(-10.47 + 0.477*score_used_strong)*amp_strong:.1f} pips")
    print(f"      → Après correction 0.758 : {(-10.47 + 0.477*score_used_strong)*amp_strong*0.758:.1f} pips")
    print(f"      → Impact réel moyen : {impact_strong:.1f} pips")
    print(f"      ⚠️  La formule donne {(-10.47 + 0.477*score_used_strong)*amp_strong*0.758:.1f} pips mais réel = {impact_strong:.1f} pips")
    print(f"      → Facteur manquant : {impact_strong / ((-10.47 + 0.477*score_used_strong)*amp_strong*0.758):.2f}x")
    print()
    
    # 6. Corrélations
    print("📊 ÉTAPE 4 : Analyse corrélations")
    print("-" * 80)
    print()
    
    # Corrélation impact réel vs prédit
    corr = df_details['impact_final'].corr(df_details['impact_real'])
    print(f"Corrélation prédit vs réel : {corr:.3f}")
    
    # Corrélation par facteur
    print()
    print("Corrélations impact réel avec :")
    print(f"  - Score empirique ajusté : {df_details['empirical_score_used'].corr(df_details['impact_real']):.3f}")
    print(f"  - Amplification : {df_details['amplification'].corr(df_details['impact_real']):.3f}")
    print(f"  - Nombre événements : {df_details['num_events'].corr(df_details['impact_real']):.3f}")
    print(f"  - Surprise % : {df_details['surprise_pct'].corr(df_details['impact_real']):.3f}")
    print()
    
    # 7. Sauvegarder analyse
    output_dir = Path(__file__).parent.parent / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df_details.to_csv(output_dir / 'investigation_strong_movements_detailed.csv', index=False)
    
    # Créer rapport
    report = {
        'n_strong_movements': len(df_strong),
        'n_weak_movements': len(df_weak),
        'impact_real_strong': impact_strong,
        'impact_real_weak': impact_weak,
        'impact_pred_strong': impact_final_strong,
        'impact_pred_weak': impact_final_weak,
        'ratio_impact_real': ratio_impact_real,
        'ratio_impact_pred': ratio_impact_pred,
        'missing_factor': missing_factor,
        'correlation': corr,
        'avg_score_strong': score_used_strong,
        'avg_score_weak': score_used_weak,
        'avg_amplification_strong': amp_strong,
        'avg_amplification_weak': amp_weak
    }
    
    pd.DataFrame([report]).to_csv(output_dir / 'investigation_strong_movements_report.csv', index=False)
    
    print("💾 Fichiers sauvegardés :")
    print(f"   - {output_dir / 'investigation_strong_movements_detailed.csv'}")
    print(f"   - {output_dir / 'investigation_strong_movements_report.csv'}")
    print()
    
    print("=" * 80)
    print("✅ INVESTIGATION TERMINÉE")
    print("=" * 80)


if __name__ == '__main__':
    investigate_strong_movements()


