#!/usr/bin/env python3
"""
📊 RE-MESURE FORMULE V2 AVEC DONNÉES PROPRES - SESSION 20

Objectif : Valider que la formule V2 (Session 15) est toujours optimale
maintenant qu'on a les VRAIES données :
- 58,449 événements (+75% vs 33,277)
- Distinction MoM/YoY/QoQ via champ 'comparison'
- 5 nouveaux champs exploitables

Comparaison :
- V1 (Session 14) : Amplification agressive sans plafond
- V2 (Session 15) : Amplification modérée avec plafond 2.5x
- Base (v9-CLEAN) : Pas d'amplification

Date : 19 octobre 2025
Session : 20
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime

# Connexion DB
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*80)
print("🔬 RE-MESURE FORMULE V2 AVEC DONNÉES PROPRES")
print("="*80)

# ============================================================================
# ÉTAPE 1 : RÉCUPÉRATION DES DONNÉES AVEC CALCUL SURPRISE
# ============================================================================

print("\n📊 Récupération des groupes d'événements avec calcul surprise...")

query = """
WITH event_surprises AS (
    SELECT 
        strftime(e.ts_utc, '%Y-%m-%d %H:%M:00') as time_group,
        e.country,
        e.event_key,
        e.actual,
        e.estimate,
        ef.empirical_score,
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate)
            ELSE 0
        END as surprise
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
      AND ef.empirical_score IS NOT NULL
),
group_surprises AS (
    SELECT
        time_group,
        MAX(surprise) as max_surprise,
        MAX(empirical_score) as max_score
    FROM event_surprises
    GROUP BY time_group
)
SELECT 
    egi.time_group,
    egi.mfe_pips,
    egi.num_events,
    egi.event_keys,
    egi.max_empirical_score,
    egi.countries,
    COALESCE(gs.max_surprise, 0) as max_surprise,
    COALESCE(gs.max_score, egi.max_empirical_score) as max_score,
    strftime(egi.time_group, '%Y') as year
FROM event_group_impacts egi
LEFT JOIN group_surprises gs
    ON egi.time_group = gs.time_group
WHERE egi.mfe_pips IS NOT NULL
  AND egi.max_empirical_score IS NOT NULL
  AND egi.max_empirical_score > 0
ORDER BY egi.time_group
"""

df_groups = conn.execute(query).df()

print(f"✅ {len(df_groups)} groupes récupérés")
print(f"   - Période : {df_groups['time_group'].min()} → {df_groups['time_group'].max()}")
print(f"   - Impact moyen : {df_groups['mfe_pips'].mean():.1f} pips")
print(f"   - Surprise moyenne : {df_groups['max_surprise'].mean()*100:.1f}%")
print(f"   - Score moyen : {df_groups['max_score'].mean():.1f}")

# Filtrer les groupes sans surprise calculée (on garde quand même pour statistiques)
df_with_surprise = df_groups[df_groups['max_surprise'] > 0]
print(f"   - Groupes avec surprise calculée : {len(df_with_surprise)} ({len(df_with_surprise)/len(df_groups)*100:.1f}%)")

# ============================================================================
# ÉTAPE 2 : VÉRIFICATION 11 SEPTEMBRE 2025
# ============================================================================

print("\n🔍 Vérification cas 11 septembre 2025...")

query_sept11 = """
SELECT 
    e.ts_utc,
    e.country,
    e.event_key,
    e.event_title,
    e.actual,
    e.estimate,
    e.previous,
    e.comparison,
    e.importance_n,
    ef.empirical_score,
    CASE 
        WHEN e.estimate IS NOT NULL AND e.estimate != 0 
        THEN ABS((e.actual - e.estimate) / e.estimate)
        ELSE 0
    END as surprise
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE strftime(e.ts_utc, '%Y-%m-%d') = '2025-09-11'
  AND e.country = 'US'
  AND e.importance_n = 3
ORDER BY e.ts_utc, e.event_key
"""

sept11_events = conn.execute(query_sept11).df()

print(f"✅ {len(sept11_events)} événements HIGH importance le 11 sept")
print("\nDétail des événements :")
for idx, row in sept11_events.iterrows():
    comp_str = str(row['comparison']) if pd.notna(row['comparison']) else 'N/A'
    score_str = f"{row['empirical_score']:.0f}" if pd.notna(row['empirical_score']) else 'N/A'
    print(f"  - {row['event_key']:<30} | comparison: {comp_str:<5} | "
          f"surprise: {row['surprise']*100:5.1f}% | score: {score_str}")

# Trouver le groupe correspondant
sept11_group = df_groups[df_groups['time_group'] == '2025-09-11 14:30:00']
if len(sept11_group) > 0:
    print(f"\n📊 Groupe 14:30 trouvé :")
    print(f"   - Impact réel (MFE) : {sept11_group.iloc[0]['mfe_pips']:.1f} pips")
    print(f"   - Nombre événements : {sept11_group.iloc[0]['num_events']}")
    print(f"   - Max score : {sept11_group.iloc[0]['max_score']}")
    print(f"   - Max surprise : {sept11_group.iloc[0]['max_surprise']*100:.1f}%")
    sept11_real_impact = sept11_group.iloc[0]['mfe_pips']
    sept11_max_score = sept11_group.iloc[0]['max_score']
    sept11_max_surprise = sept11_group.iloc[0]['max_surprise']
else:
    print("⚠️ PROBLÈME : Groupe 14:30 non trouvé dans event_group_impacts")
    sept11_real_impact = 119.5  # Valeur de la KNOWLEDGE_BASE
    sept11_max_score = 65
    sept11_max_surprise = 0.33

# ============================================================================
# ÉTAPE 3 : DÉFINITION DES FORMULES
# ============================================================================

def calc_base_impact(score):
    """Formule Base v9-CLEAN (pas d'amplification)"""
    return abs(-7.08 + 0.419 * score)

def calc_amplification_v1(surprise, score):
    """
    Amplification V1 (Session 14) - Agressive
    """
    if surprise < 0.05:
        return 1.0
    elif surprise < 0.10:
        return 1.0 + (surprise - 0.05) * 0.4
    else:
        return 3.0 + np.log(surprise - 0.10 + 1) * 2.0

def calc_amplification_v2(surprise, score):
    """
    Amplification V2 (Session 15) - Modérée avec plafond
    - Filtrage : score < 40 → pas d'amplification
    - Plafond surprise : 30%
    - Rampe douce : 5-15% → facteur 1.0 à 2.5
    - Plafond : 2.5x max
    """
    # Filtrage événements faible importance
    if score < 40:
        return 1.0
    
    # Plafond surprise à 30%
    surprise_capped = min(surprise, 0.30)
    
    # Amplification progressive
    if surprise_capped < 0.05:
        return 1.0
    elif surprise_capped < 0.15:
        # Rampe de 1.0 à 2.5 entre 5% et 15%
        return 1.0 + (surprise_capped - 0.05) * 0.15
    else:
        return 2.5  # Plafond

def predict_impact_v1(score, surprise):
    """Prédiction V1"""
    base = calc_base_impact(score)
    amp = calc_amplification_v1(surprise, score)
    return base * amp * 0.758  # Calibration MT5

def predict_impact_v2(score, surprise):
    """Prédiction V2"""
    base = calc_base_impact(score)
    amp = calc_amplification_v2(surprise, score)
    return base * amp * 0.758  # Calibration MT5

def predict_impact_base(score):
    """Prédiction Base (sans amplification)"""
    return calc_base_impact(score) * 0.758

# ============================================================================
# ÉTAPE 4 : CALCUL DES PRÉDICTIONS
# ============================================================================

print("\n🔮 Calcul des prédictions...")

# Utiliser seulement les groupes avec surprise calculée pour comparaison V1/V2
df_eval = df_with_surprise.copy()

df_eval['pred_base'] = df_eval.apply(
    lambda row: predict_impact_base(row['max_score']), 
    axis=1
)

df_eval['pred_v1'] = df_eval.apply(
    lambda row: predict_impact_v1(row['max_score'], row['max_surprise']), 
    axis=1
)

df_eval['pred_v2'] = df_eval.apply(
    lambda row: predict_impact_v2(row['max_score'], row['max_surprise']), 
    axis=1
)

# Calcul des erreurs absolues
df_eval['error_base'] = abs(df_eval['pred_base'] - df_eval['mfe_pips'])
df_eval['error_v1'] = abs(df_eval['pred_v1'] - df_eval['mfe_pips'])
df_eval['error_v2'] = abs(df_eval['pred_v2'] - df_eval['mfe_pips'])

# Calcul des erreurs relatives
df_eval['error_rel_base'] = (df_eval['error_base'] / df_eval['mfe_pips']) * 100
df_eval['error_rel_v1'] = (df_eval['error_v1'] / df_eval['mfe_pips']) * 100
df_eval['error_rel_v2'] = (df_eval['error_v2'] / df_eval['mfe_pips']) * 100

print("✅ Prédictions calculées")
print(f"   - {len(df_eval)} groupes évalués (avec surprise)")

# ============================================================================
# ÉTAPE 5 : MÉTRIQUES GLOBALES
# ============================================================================

print("\n" + "="*80)
print("📊 MÉTRIQUES GLOBALES (GROUPES AVEC SURPRISE)")
print("="*80)

mae_base = df_eval['error_rel_base'].mean()
mae_v1 = df_eval['error_rel_v1'].mean()
mae_v2 = df_eval['error_rel_v2'].mean()

print(f"\n{'Formule':<15} {'MAE':<15} {'Gain vs V1':<20} {'Verdict'}")
print("-" * 80)
print(f"{'BASE':<15} {mae_base:>10.1f}% {'-':>19} {'⚪ Baseline'}")
print(f"{'V1 (Sess 14)':<15} {mae_v1:>10.1f}% {'-':>19} {'⚠️ Agressive'}")

gain_v2_vs_v1 = mae_v1 - mae_v2
pct_reduction = (gain_v2_vs_v1 / mae_v1) * 100 if mae_v1 > 0 else 0
verdict_v2 = "✅✅✅ EXCELLENTE" if gain_v2_vs_v1 > 300 else "✅✅ TRÈS BONNE" if gain_v2_vs_v1 > 100 else "✅ BONNE" if gain_v2_vs_v1 > 0 else "⚠️ PROBLÈME"

print(f"{'V2 (Sess 15)':<15} {mae_v2:>10.1f}% {f'+{gain_v2_vs_v1:.1f} pts':>19} {verdict_v2}")

print(f"\n💡 V2 réduit l'erreur de {pct_reduction:.1f}% par rapport à V1")

# Comparaison avec Session 17
print("\n📊 Comparaison avec Session 17 (validation sur 120 groupes) :")
print(f"   Session 17 : MAE V1 = 593.6%, MAE V2 = 174.9%, gain = -418.7 pts (-70.5%)")
print(f"   Session 20 : MAE V1 = {mae_v1:.1f}%, MAE V2 = {mae_v2:.1f}%, gain = {gain_v2_vs_v1:.1f} pts ({pct_reduction:.1f}%)")

if abs(mae_v2 - 174.9) < 50:
    print(f"   ✅ MAE V2 cohérente avec Session 17 (écart {abs(mae_v2 - 174.9):.1f} pts)")
else:
    print(f"   ⚠️ MAE V2 DIFFÉRENTE de Session 17 (écart {abs(mae_v2 - 174.9):.1f} pts)")
    print(f"   → Impact des nouvelles données (MoM/YoY distingués)")

# ============================================================================
# ÉTAPE 6 : TEST CAS 11 SEPTEMBRE
# ============================================================================

print("\n" + "="*80)
print("🔍 TEST CAS 11 SEPTEMBRE 2025")
print("="*80)

# Prédictions pour 11 sept
pred_base_sept11 = predict_impact_base(sept11_max_score)
pred_v1_sept11 = predict_impact_v1(sept11_max_score, sept11_max_surprise)
pred_v2_sept11 = predict_impact_v2(sept11_max_score, sept11_max_surprise)

error_base_sept11 = abs(pred_base_sept11 - sept11_real_impact)
error_v1_sept11 = abs(pred_v1_sept11 - sept11_real_impact)
error_v2_sept11 = abs(pred_v2_sept11 - sept11_real_impact)

error_rel_base_sept11 = (error_base_sept11 / sept11_real_impact) * 100
error_rel_v1_sept11 = (error_v1_sept11 / sept11_real_impact) * 100
error_rel_v2_sept11 = (error_v2_sept11 / sept11_real_impact) * 100

print(f"\n📌 Contexte :")
print(f"   - Impact réel (MFE 60 min) : {sept11_real_impact:.1f} pips")
print(f"   - Max score : {sept11_max_score}")
print(f"   - Max surprise : {sept11_max_surprise*100:.1f}%")

print(f"\n{'Formule':<15} {'Prédiction':<15} {'Erreur abs':<15} {'Erreur rel':<15} {'Verdict'}")
print("-" * 90)
print(f"{'BASE':<15} {pred_base_sept11:>10.1f} pips {error_base_sept11:>10.1f} pips {error_rel_base_sept11:>10.1f}% {'⚪'}")
print(f"{'V1':<15} {pred_v1_sept11:>10.1f} pips {error_v1_sept11:>10.1f} pips {error_rel_v1_sept11:>10.1f}% {'⚠️'}")
print(f"{'V2':<15} {pred_v2_sept11:>10.1f} pips {error_v2_sept11:>10.1f} pips {error_rel_v2_sept11:>10.1f}% {'✅' if error_rel_v2_sept11 < 20 else '⚠️'}")

print("\n📊 Comparaison avec graphiques MT5 :")
print(f"   Graphiques MT5 : Mouvement Phase 1 = 522 pips (analysé Session 20)")
print(f"   Base données MFE : {sept11_real_impact:.1f} pips")
print(f"   Ratio MT5/DB : {522 / sept11_real_impact:.2f}x")

if sept11_real_impact < 522:
    print(f"   💡 La DB mesure probablement sur fenêtre plus courte (<60 min)")
    print(f"      → Le vrai mouvement (522 pips) est BEAUCOUP plus élevé que V2 prédit ({pred_v2_sept11:.0f} pips)")
    print(f"      → Sous-estimation réelle : {(1 - pred_v2_sept11/522)*100:.0f}%")

# ============================================================================
# ÉTAPE 7 : ANALYSE PAR TRANCHE DE SURPRISE
# ============================================================================

print("\n" + "="*80)
print("📈 ANALYSE PAR TRANCHE DE SURPRISE")
print("="*80)

# Définir les tranches
df_eval['surprise_bin'] = pd.cut(
    df_eval['max_surprise'] * 100,
    bins=[0, 5, 10, 15, 20, 100],
    labels=['0-5%', '5-10%', '10-15%', '15-20%', '20%+']
)

for bin_label in ['0-5%', '5-10%', '10-15%', '15-20%', '20%+']:
    bin_data = df_eval[df_eval['surprise_bin'] == bin_label]
    
    if len(bin_data) == 0:
        continue
    
    mae_base_bin = bin_data['error_rel_base'].mean()
    mae_v1_bin = bin_data['error_rel_v1'].mean()
    mae_v2_bin = bin_data['error_rel_v2'].mean()
    
    gain = mae_v1_bin - mae_v2_bin
    
    print(f"\n{bin_label} (n={len(bin_data)}) :")
    print(f"   BASE : {mae_base_bin:>6.1f}%")
    print(f"   V1   : {mae_v1_bin:>6.1f}%")
    print(f"   V2   : {mae_v2_bin:>6.1f}%  (gain: {gain:+.1f} pts)")

# ============================================================================
# ÉTAPE 8 : TOP/FLOP
# ============================================================================

print("\n" + "="*80)
print("🏆 TOP 5 AMÉLIORATIONS V2 vs V1")
print("="*80)

df_eval['gain_v2_vs_v1'] = df_eval['error_rel_v1'] - df_eval['error_rel_v2']
top5 = df_eval.nlargest(5, 'gain_v2_vs_v1')

for idx, row in top5.iterrows():
    print(f"\n{row['time_group']} ({row['countries']})")
    print(f"   Events : {row['event_keys'][:80]}")
    print(f"   Surprise : {row['max_surprise']*100:.1f}%, Score : {row['max_score']}, Impact : {row['mfe_pips']:.1f} pips")
    print(f"   V1 : {row['error_rel_v1']:.1f}%, V2 : {row['error_rel_v2']:.1f}% → Gain : +{row['gain_v2_vs_v1']:.0f} pts ✅")

print("\n" + "="*80)
print("⚠️ TOP 5 RÉGRESSIONS V2 vs V1")
print("="*80)

bottom5 = df_eval.nsmallest(5, 'gain_v2_vs_v1')

for idx, row in bottom5.iterrows():
    print(f"\n{row['time_group']} ({row['countries']})")
    print(f"   Events : {row['event_keys'][:80]}")
    print(f"   Surprise : {row['max_surprise']*100:.1f}%, Score : {row['max_score']}, Impact : {row['mfe_pips']:.1f} pips")
    print(f"   V1 : {row['error_rel_v1']:.1f}%, V2 : {row['error_rel_v2']:.1f}% → Perte : {row['gain_v2_vs_v1']:.0f} pts ⚠️")

# ============================================================================
# ÉTAPE 9 : VERDICT FINAL
# ============================================================================

print("\n" + "="*80)
print("🎯 VERDICT FINAL")
print("="*80)

# Conditions de succès
success_mae = mae_v2 < 200  # MAE V2 raisonnable
success_gain = gain_v2_vs_v1 > 100  # Gain significatif vs V1
success_sept11 = error_rel_v2_sept11 < 50  # Erreur acceptable sur 11 sept (en tenant compte sous-estimation DB)

print(f"\n✅ Critères de validation :")
print(f"   {'MAE V2 < 200%':<30} : {mae_v2:.1f}% {'✅' if success_mae else '⚠️'}")
print(f"   {'Gain V2 vs V1 > 100 pts':<30} : {gain_v2_vs_v1:.1f} pts {'✅' if success_gain else '⚠️'}")
print(f"   {'Erreur 11 sept < 50%':<30} : {error_rel_v2_sept11:.1f}% {'✅' if success_sept11 else '⚠️'}")

if success_mae and success_gain:
    print(f"\n🎉 VALIDATION RÉUSSIE : V2 est meilleure que V1 avec les données propres !")
    print(f"   → MAE réduite de {pct_reduction:.1f}% vs V1")
elif success_gain:
    print(f"\n✅ VALIDATION PARTIELLE : V2 reste meilleure que V1 (+{gain_v2_vs_v1:.1f} pts)")
    print(f"   ⚠️ Mais MAE élevée ({mae_v2:.1f}%)")
    print(f"   → Nécessite exploration des nouveaux champs pour améliorer")
else:
    print(f"\n⚠️ ATTENTION : V2 ne performe PAS mieux que V1 avec les données propres")
    print(f"   → Investigation urgente nécessaire")

# Analyse spécifique 11 sept
print(f"\n💡 Analyse spécifique 11 septembre :")
print(f"   - V2 prédit : {pred_v2_sept11:.0f} pips")
print(f"   - DB mesure : {sept11_real_impact:.0f} pips (erreur {error_rel_v2_sept11:.0f}%)")
print(f"   - MT5 réel  : 522 pips Phase 1 + 480 pips Phase 2 = 1002 pips total")
print(f"   - Sous-estimation réelle : {(1 - pred_v2_sept11/522)*100:.0f}% (Phase 1 seulement)")

# Sauvegarde résultats
output_path = 'ANALYSIS_V2_CLEAN_DATA_SESSION20.csv'
df_eval[['time_group', 'mfe_pips', 'max_score', 'max_surprise', 
         'pred_base', 'pred_v1', 'pred_v2',
         'error_rel_base', 'error_rel_v1', 'error_rel_v2',
         'gain_v2_vs_v1']].to_csv(output_path, index=False)

print(f"\n💾 Résultats sauvegardés : {output_path}")
print(f"   - {len(df_eval)} groupes analysés")

print("\n" + "="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80)

conn.close()
