"""
PHASE 2 BIS : RE-MESURE IMPACTS AVEC FORMULE V2 - SESSION 15
Compare formule V1 (Session 14) vs V2 (Session 15) sur les 30 événements

Objectif : Valider que V2 améliore la précision
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import numpy as np
from datetime import datetime, timedelta

print("="*80)
print("📊 PHASE 2 BIS : RE-MESURE AVEC FORMULE V2 - SESSION 15")
print("="*80)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Chargement données
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 1 : Chargement données")
print("─"*80)

# Charger événements extraits
events_df = pd.read_csv('extracted_events_session15.csv')
events_df['ts_utc'] = pd.to_datetime(events_df['ts_utc'])

# Charger résultats V1 (déjà calculés)
results_v1 = pd.read_csv('impacts_comparison_session15.csv')

print(f"✅ {len(events_df)} événements chargés")
print(f"✅ Résultats V1 chargés pour comparaison")

# Connexion DB pour prix
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Définition formules
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 2 : Définition formules V1 et V2")
print("─"*80)

def calculate_amplification_factor_v1(surprise_pct):
    """Formule V1 (Session 14) - ANCIENNE"""
    surprise_abs = abs(surprise_pct)
    
    if surprise_abs < 5.0:
        return 1.0
    elif surprise_abs < 10.0:
        return 1.0 + (surprise_abs - 5.0) * 0.4
    else:
        return 3.0 + np.log1p(surprise_abs - 10.0) * 2.0

def calculate_amplification_factor_v2(surprise_pct, empirical_score=None):
    """Formule V2 (Session 15) - NOUVELLE"""
    surprise_abs = abs(surprise_pct)
    
    # Plafond surprises aberrantes
    if surprise_abs > 30:
        surprise_abs = 30.0
    
    # Filtrage score empirique faible
    if empirical_score is not None and empirical_score < 40:
        return 1.0
    
    # Zone 1 (0-5%) : Pas d'amplification
    if surprise_abs < 5.0:
        return 1.0
    
    # Zone 2 (5-15%) : Amplification linéaire
    elif surprise_abs < 15.0:
        return 1.0 + (surprise_abs - 5.0) * 0.15
    
    # Zone 3 (>15%) : Plafond à ×2.5
    else:
        return 2.5

def predict_impact_v9_clean(empirical_score, num_events=1):
    """Formule v9-CLEAN (sans amplification)"""
    if num_events >= 2:
        return -10.47 + 0.477 * empirical_score
    else:
        return -7.08 + 0.419 * empirical_score

def calculate_surprise_percentage(actual, estimate):
    """Calcule le pourcentage de surprise"""
    if estimate is None or estimate == 0:
        return 0.0
    return abs((actual - estimate) / estimate) * 100

print("✅ Formule V1 : Amplification jusqu'à ×10+")
print("✅ Formule V2 : Amplification plafonnée à ×2.5")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Calcul impacts avec V2
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 3 : Calcul impacts avec formule V2")
print("─"*80)

results_v2 = []

for idx, row in events_df.iterrows():
    print(f"🔄 [{idx+1}/{len(events_df)}] {row['event_title']}")
    
    # Impact prédit v8.7 (SANS amplification) - identique
    impact_v87_brut = predict_impact_v9_clean(row['empirical_score'], num_events=1)
    impact_v87_corrige = abs(impact_v87_brut) * 0.758
    
    # Calculer surprise
    surprise_pct = calculate_surprise_percentage(row['actual'], row['estimate'])
    
    # Impact prédit v8.7.2 (AVEC amplification V2)
    amplification_factor_v2 = calculate_amplification_factor_v2(
        surprise_pct, 
        empirical_score=row['empirical_score']
    )
    
    impact_v872_amplifie = abs(impact_v87_brut) * amplification_factor_v2
    impact_v872_corrige = impact_v872_amplifie * 0.758
    
    print(f"   📊 V2 amplif ×{amplification_factor_v2:.2f} → {impact_v872_corrige:.2f} pips")
    
    # Récupérer impact réel depuis résultats V1
    impact_reel = results_v1.loc[idx, 'impact_reel']
    
    if pd.notna(impact_reel):
        # Calcul écarts
        ecart_v87 = abs(impact_v87_corrige - impact_reel)
        ecart_v872 = abs(impact_v872_corrige - impact_reel)
        
        ecart_pct_v87 = (ecart_v87 / impact_reel * 100) if impact_reel > 0 else 0
        ecart_pct_v872 = (ecart_v872 / impact_reel * 100) if impact_reel > 0 else 0
        
        # Amélioration
        amelioration_pct = ecart_pct_v87 - ecart_pct_v872
        
        print(f"   ✅ Écart V2 : {ecart_pct_v872:.1f}% (vs {ecart_pct_v87:.1f}% V1)")
        print(f"   {'🎯' if amelioration_pct > 0 else '⚠️'} Amélioration : {amelioration_pct:+.1f} points")
    else:
        ecart_pct_v872 = None
        amelioration_pct = None
    
    # Stocker résultats
    results_v2.append({
        'ts_utc': row['ts_utc'],
        'event_title': row['event_title'],
        'country': row['country'],
        'tranche': row['tranche'],
        'surprise_pct': surprise_pct,
        'empirical_score': row['empirical_score'],
        'amplification_factor_v2': amplification_factor_v2,
        'impact_v87': impact_v87_corrige,
        'impact_v872': impact_v872_corrige,
        'impact_reel': impact_reel,
        'ecart_pct_v87': results_v1.loc[idx, 'ecart_pct_v87'],
        'ecart_pct_v872': ecart_pct_v872,
        'amelioration_pct': amelioration_pct
    })

# ════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Création DataFrame et comparaison
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 4 : Comparaison V1 vs V2")
print("─"*80)

results_v2_df = pd.DataFrame(results_v2)
results_v2_valides = results_v2_df[results_v2_df['impact_reel'].notna()].copy()

print(f"\n✅ {len(results_v2_valides)} événements avec données réelles")

# Arrondir
for col in ['surprise_pct', 'amplification_factor_v2', 'impact_v87', 'impact_v872', 'impact_reel']:
    if col in results_v2_valides.columns:
        results_v2_valides[col] = results_v2_valides[col].round(2)

for col in ['ecart_pct_v87', 'ecart_pct_v872', 'amelioration_pct']:
    if col in results_v2_valides.columns:
        results_v2_valides[col] = results_v2_valides[col].round(1)

# ════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Statistiques comparatives
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 5 : STATISTIQUES COMPARATIVES V1 vs V2")
print("─"*80)

print("\n📊 STATISTIQUES GLOBALES :")
print(f"\n{'Métrique':<40} {'V1 (Session 14)':<20} {'V2 (Session 15)':<20} {'Delta':<15}")
print("─" * 95)

mae_v1 = results_v1['ecart_pct_v871'].mean()
mae_v2 = results_v2_valides['ecart_pct_v872'].mean()
delta_mae = mae_v2 - mae_v1
emoji_mae = "✅" if delta_mae < 0 else "❌"
print(f"{'MAE (écart moyen %)':<40} {mae_v1:<20.1f} {mae_v2:<20.1f} {emoji_mae} {delta_mae:+.1f}")

amelioration_v1 = results_v1['amelioration_pct'].mean()
amelioration_v2 = results_v2_valides['amelioration_pct'].mean()
delta_amelioration = amelioration_v2 - amelioration_v1
emoji_amelioration = "✅" if delta_amelioration > 0 else "❌"
print(f"{'Amélioration moyenne (points)':<40} {amelioration_v1:<20.1f} {amelioration_v2:<20.1f} {emoji_amelioration} {delta_amelioration:+.1f}")

amplif_v1 = results_v1['amplification_factor'].mean()
amplif_v2 = results_v2_valides['amplification_factor_v2'].mean()
delta_amplif = amplif_v2 - amplif_v1
emoji_amplif = "📉"
print(f"{'Amplification moyenne':<40} ×{amplif_v1:<19.2f} ×{amplif_v2:<19.2f} {emoji_amplif} {delta_amplif:+.2f}")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 6 : Statistiques par tranche
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 6 : COMPARAISON PAR TRANCHE")
print("─"*80)

print("\n📊 AMÉLIORATION MOYENNE PAR TRANCHE :")
print(f"\n{'Tranche':<15} {'V1 (pts)':<15} {'V2 (pts)':<15} {'Delta':<15} {'Statut':<10}")
print("─" * 70)

for tranche in ['0-5%', '5-10%', '10-50%']:
    v1_tranche = results_v1[results_v1['tranche'] == tranche]['amelioration_pct'].mean()
    v2_tranche = results_v2_valides[results_v2_valides['tranche'] == tranche]['amelioration_pct'].mean()
    delta = v2_tranche - v1_tranche
    statut = "✅ Mieux" if delta > 0 else ("⚠️ Pire" if delta < -10 else "≈ Neutre")
    print(f"{tranche:<15} {v1_tranche:<15.1f} {v2_tranche:<15.1f} {delta:+<15.1f} {statut:<10}")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 7 : Top améliorations / régressions
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 7 : CHANGEMENTS MAJEURS V1 → V2")
print("─"*80)

# Calculer différence amélioration V2 vs V1
comparison_df = results_v2_valides.copy()
comparison_df['amelioration_v1'] = results_v1['amelioration_pct']
comparison_df['delta_amelioration'] = comparison_df['amelioration_pct'] - comparison_df['amelioration_v1']

print("\n📈 TOP 5 PLUS GRANDES AMÉLIORATIONS (V2 mieux que V1) :")
top_improvements = comparison_df.nlargest(5, 'delta_amelioration')[
    ['event_title', 'tranche', 'surprise_pct', 'amelioration_v1', 'amelioration_pct', 'delta_amelioration']
]
print(top_improvements.to_string(index=False))

print("\n📉 TOP 5 PLUS GRANDES RÉGRESSIONS (V2 pire que V1) :")
top_regressions = comparison_df.nsmallest(5, 'delta_amelioration')[
    ['event_title', 'tranche', 'surprise_pct', 'amelioration_v1', 'amelioration_pct', 'delta_amelioration']
]
print(top_regressions.to_string(index=False))

# ════════════════════════════════════════════════════════════════
# ÉTAPE 8 : Sauvegarde
# ════════════════════════════════════════════════════════════════

print("\n" + "─"*80)
print("ÉTAPE 8 : Sauvegarde résultats")
print("─"*80)

csv_path = 'impacts_comparison_v2_session15.csv'
results_v2_valides.to_csv(csv_path, index=False)

comparison_path = 'comparison_v1_v2_session15.csv'
comparison_df.to_csv(comparison_path, index=False)

print(f"✅ Fichier V2 sauvegardé : {csv_path}")
print(f"✅ Fichier comparaison sauvegardé : {comparison_path}")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 9 : VERDICT FINAL
# ════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🎯 VERDICT FINAL : V2 EST-ELLE MEILLEURE QUE V1 ?")
print("="*80)

if delta_amelioration > 50:
    verdict = "✅ SUCCÈS MAJEUR - V2 nettement meilleure"
elif delta_amelioration > 0:
    verdict = "✅ SUCCÈS - V2 légèrement meilleure"
elif delta_amelioration > -50:
    verdict = "⚠️ NEUTRE - Pas de différence significative"
else:
    verdict = "❌ ÉCHEC - V2 pire que V1"

print(f"\n{verdict}")
print(f"\nMAE V1 : {mae_v1:.1f}%")
print(f"MAE V2 : {mae_v2:.1f}%")
print(f"Delta  : {delta_mae:+.1f}% ({abs(delta_mae/mae_v1*100):.1f}% de variation)")

print(f"\nAmélioration moyenne V1 : {amelioration_v1:.1f} points")
print(f"Amélioration moyenne V2 : {amelioration_v2:.1f} points")
print(f"Delta                   : {delta_amelioration:+.1f} points")

print("\n" + "="*80)
print("✅ PHASE 2 BIS TERMINÉE")
print("="*80)

conn.close()
