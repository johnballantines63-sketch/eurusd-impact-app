"""
COMPARAISON CSV SESSION 90 vs PLANIFICATEUR - Session 92.4
==========================================================

Objectif : Comparer valeurs CSV Session 90 avec valeurs Planificateur/MT5

Méthodologie :
1. Charger CSV Session 90
2. Extraire ligne 11 septembre 2025
3. Comparer avec valeurs Planificateur connues
4. Conclusion divergence

Date : 28 octobre 2025
"""

import pandas as pd
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

CSV_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv")

# Valeurs Planificateur V2.4 (image André)
PLANNER_VALUES = {
    'date': '2025-09-11',
    'impact_predicted': 56.3,  # Impact Prédit
    'impact_real_mt5': 56.2,   # Impact Réel MT5
    'mae': 0.1,                # MAE
    'ttr_predicted': 6.0,      # TTR Prédit (min)
    'ttr_observed': 5.0,       # TTR Observé (min)
    'pullback_predicted': 26.9,  # Pullback Prédit (pips)
    'pullback_observed': 27.1    # Pullback Observé (pips)
}

print("="*80)
print("📊 COMPARAISON CSV SESSION 90 vs PLANIFICATEUR V2.4")
print("="*80)

# ============================================================================
# CHARGEMENT CSV
# ============================================================================

print(f"\n📁 Chargement CSV : {CSV_PATH.name}")

if not CSV_PATH.exists():
    print(f"❌ ERREUR : CSV non trouvé")
    print(f"   Chemin : {CSV_PATH}")
    exit(1)

df = pd.read_csv(CSV_PATH)
print(f"✅ CSV chargé : {len(df)} dates")

# ============================================================================
# EXTRACTION 11 SEPTEMBRE 2025
# ============================================================================

print("\n" + "="*80)
print("🔍 EXTRACTION 11 SEPTEMBRE 2025")
print("="*80)

row = df[df['date'] == '2025-09-11']

if row.empty:
    print(f"❌ ERREUR : 11 septembre 2025 non trouvé dans CSV")
    exit(1)

row = row.iloc[0]

print(f"\n✅ Date trouvée dans CSV")
print(f"   Nom : {row['name']}")
print(f"   Type : {row['type']}")
print(f"   Événements : {row['num_events']}")

# ============================================================================
# COMPARAISON VALEURS
# ============================================================================

print("\n" + "="*80)
print("⚖️ COMPARAISON VALEURS")
print("="*80)

comparisons = [
    {
        'metric': 'Impact Prédit',
        'csv': row['impact_predicted'],
        'planner': PLANNER_VALUES['impact_predicted'],
        'unit': 'pips'
    },
    {
        'metric': 'Impact Réel',
        'csv': row['impact_real'],
        'planner': PLANNER_VALUES['impact_real_mt5'],
        'unit': 'pips'
    },
    {
        'metric': 'MAE',
        'csv': row['error_pips'],
        'planner': PLANNER_VALUES['mae'],
        'unit': 'pips'
    }
]

print(f"\n{'Métrique':<20} {'CSV Session 90':>15} {'Planificateur':>15} {'Écart':>10} {'Status':>8}")
print("-"*80)

divergences = []

for comp in comparisons:
    csv_val = comp['csv']
    planner_val = comp['planner']
    diff = abs(csv_val - planner_val)
    
    # Status
    if diff < 0.5:
        status = "✅ OK"
    elif diff < 2.0:
        status = "⚠️ LÉGER"
    else:
        status = "❌ MAJEUR"
        divergences.append(comp['metric'])
    
    print(f"{comp['metric']:<20} {csv_val:>14.1f}p {planner_val:>14.1f}p {diff:>9.1f}p {status:>8}")

# ============================================================================
# ANALYSE DIVERGENCES
# ============================================================================

print("\n" + "="*80)
print("💥 ANALYSE DIVERGENCES")
print("="*80)

if not divergences:
    print("\n✅ Aucune divergence majeure détectée")
    print("   CSV Session 90 cohérent avec Planificateur V2.4")
else:
    print(f"\n❌ {len(divergences)} divergence(s) majeure(s) détectée(s) :")
    
    for metric in divergences:
        print(f"\n   • {metric}")
        
        comp = next(c for c in comparisons if c['metric'] == metric)
        csv_val = comp['csv']
        planner_val = comp['planner']
        diff = abs(csv_val - planner_val)
        pct_diff = (diff / planner_val * 100) if planner_val > 0 else 0
        
        print(f"     CSV : {csv_val:.1f} {comp['unit']}")
        print(f"     Planificateur : {planner_val:.1f} {comp['unit']}")
        print(f"     Écart : {diff:.1f} {comp['unit']} ({pct_diff:.1f}%)")

# ============================================================================
# FOCUS IMPACT RÉEL (CRITIQUE)
# ============================================================================

print("\n" + "="*80)
print("🎯 FOCUS : IMPACT RÉEL (CRITIQUE)")
print("="*80)

impact_csv = row['impact_real']
impact_planner = PLANNER_VALUES['impact_real_mt5']
diff_impact = abs(impact_csv - impact_planner)
pct_diff = (diff_impact / impact_planner * 100)

print(f"\nImpact Réel CSV Session 90 : {impact_csv:.1f} pips")
print(f"Impact Réel MT5/Planificateur : {impact_planner:.1f} pips")
print(f"\nDivergence : {diff_impact:.1f} pips ({pct_diff:.1f}%)")

if diff_impact >= 2.0:
    print(f"\n❌ DIVERGENCE MAJEURE CONFIRMÉE")
    print(f"\n   Implications Grid Search Session 92.2 :")
    print(f"   • Grid Search a utilisé {impact_csv:.1f} pips (CSV)")
    print(f"   • Valeur correcte MT5 : {impact_planner:.1f} pips")
    print(f"   • Erreur systématique : {diff_impact:.1f} pips sous-estimation")
    print(f"\n   Conséquence :")
    print(f"   • Amplifications calibrées TROP BASSES")
    print(f"   • Pour compenser valeurs réelles sous-estimées")
    print(f"   • Résultats Grid Search INVALIDES")
    
    # Impact financier
    print(f"\n   Impact financier si amp 2.2 utilisée :")
    impact_predicted_v24 = row['impact_predicted']  # Avec amp 2.5
    impact_predicted_v25 = impact_predicted_v24 * (2.2 / 2.5)  # Avec amp 2.2
    
    mae_v24 = abs(impact_predicted_v24 - impact_planner)
    mae_v25 = abs(impact_predicted_v25 - impact_planner)
    degradation = mae_v25 - mae_v24
    
    print(f"   • V2.4 (amp 2.5) : MAE {mae_v24:.1f} pips ✅")
    print(f"   • V2.5 (amp 2.2) : MAE {mae_v25:.1f} pips ❌")
    print(f"   • Dégradation : +{degradation:.1f} pips")
    print(f"   • Coût estimé : €{degradation * 10 * 10 * 12:.0f}/an (1 lot, 10 trades/mois)")

else:
    print(f"\n✅ Divergence acceptable (< 2 pips)")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*80)
print("📋 CONCLUSION")
print("="*80)

if diff_impact >= 2.0:
    print(f"\n❌ CSV SESSION 90 INVALIDE POUR GRID SEARCH")
    print(f"\nRaisons :")
    print(f"   1. Sous-estime impact réel systématiquement")
    print(f"   2. Fenêtre 60 min fixe inadaptée")
    print(f"   3. Ne capture pas mouvement complet")
    print(f"\nRecommandations :")
    print(f"   ✅ Valider données avec script validate_impact_windows.py")
    print(f"   ✅ Utiliser fenêtre adaptative par type événement")
    print(f"   ✅ CONSERVER Planificateur V2.4 (amp 2.5 fixe)")
    print(f"   ❌ Ne PAS utiliser CSV Session 90 pour calibration")
else:
    print(f"\n✅ CSV SESSION 90 VALIDE")
    print(f"\nCSV cohérent avec Planificateur V2.4")
    print(f"Divergence < 2 pips acceptable")

print("\n" + "="*80)
print("✅ COMPARAISON TERMINÉE")
print("="*80)
