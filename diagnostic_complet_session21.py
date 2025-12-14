#!/usr/bin/env python3
"""
DIAGNOSTIC COMPLET SESSION 21
Objectif : Répondre aux 3 questions critiques AVANT toute implémentation
"""

import duckdb
import pandas as pd
from datetime import datetime
import sys

print("=" * 80)
print("🔍 DIAGNOSTIC COMPLET SESSION 21")
print("=" * 80)
print()

# Connexion à la base de données
DB_PATH = 'fx_impact_app/data/warehouse.duckdb'
print(f"📊 Connexion à : {DB_PATH}")

try:
    conn = duckdb.connect(DB_PATH, read_only=True)
    print("✅ Connexion réussie\n")
except Exception as e:
    print(f"❌ Erreur connexion : {e}")
    sys.exit(1)

# ============================================================================
# PARTIE 1 : VÉRIFICATION STRUCTURE DB
# ============================================================================
print("=" * 80)
print("PARTIE 1 : VÉRIFICATION STRUCTURE BASE DE DONNÉES")
print("=" * 80)
print()

# Question 1a : Les event_key ont-ils les suffixes ?
print("📋 Question 1a : Les event_key ont-ils les suffixes (_mom, _yoy, _qoq) ?")
print("-" * 80)

query_suffixes = """
SELECT 
    event_key,
    comparison,
    COUNT(*) as count
FROM events
WHERE comparison IS NOT NULL
GROUP BY event_key, comparison
ORDER BY count DESC
LIMIT 20
"""

df_suffixes = conn.execute(query_suffixes).fetchdf()
print(df_suffixes.to_string(index=False))
print()

# Analyse
has_suffixes = any('_mom' in str(key) or '_yoy' in str(key) or '_qoq' in str(key) 
                   for key in df_suffixes['event_key'])

if has_suffixes:
    print("✅ RÉSULTAT : Les event_key ont les suffixes (_mom, _yoy, _qoq)")
else:
    print("❌ RÉSULTAT : Les event_key N'ONT PAS les suffixes !")
    print("   → Les event_key sont du type 'inflation_rate' avec comparison='mom'")
print()
print()

# Question 1b : Combien d'événements avec comparison ?
print("📋 Question 1b : Statistiques des événements avec comparison")
print("-" * 80)

query_stats = """
SELECT 
    COUNT(*) as total_events,
    SUM(CASE WHEN comparison IS NOT NULL THEN 1 ELSE 0 END) as with_comparison,
    SUM(CASE WHEN comparison = 'mom' THEN 1 ELSE 0 END) as mom_count,
    SUM(CASE WHEN comparison = 'yoy' THEN 1 ELSE 0 END) as yoy_count,
    SUM(CASE WHEN comparison = 'qoq' THEN 1 ELSE 0 END) as qoq_count
FROM events
"""

df_stats = conn.execute(query_stats).fetchdf()
print(df_stats.to_string(index=False))
print()
print(f"Pourcentage avec comparison : {df_stats['with_comparison'][0] / df_stats['total_events'][0] * 100:.1f}%")
print()
print()

# Question 1c : event_families contient-il les suffixes ?
print("📋 Question 1c : event_families contient-il les event_key avec suffixes ?")
print("-" * 80)

query_families = """
SELECT 
    event_key,
    country,
    empirical_score
FROM event_families
WHERE event_key LIKE '%inflation%'
   OR event_key LIKE '%cpi%'
ORDER BY event_key
LIMIT 10
"""

df_families = conn.execute(query_families).fetchdf()
print(df_families.to_string(index=False))
print()

has_suffixes_families = any('_mom' in str(key) or '_yoy' in str(key) 
                            for key in df_families['event_key'])

if has_suffixes_families:
    print("✅ event_families contient des event_key avec suffixes")
else:
    print("❌ event_families NE contient PAS de suffixes")
    print("   → Les event_key sont du type 'inflation rate' (sans suffixe)")
print()
print()

# Question 1d : Vérifier event_group_impacts
print("📋 Question 1d : event_group_impacts est-il cohérent ?")
print("-" * 80)

query_impacts = """
SELECT COUNT(*) as total_groups
FROM event_group_impacts
"""

df_impacts = conn.execute(query_impacts).fetchdf()
print(f"Nombre de groupes dans event_group_impacts : {df_impacts['total_groups'][0]}")
print()

# Vérifier un échantillon
query_sample = """
SELECT 
    time_group,
    event_keys,
    mfe_pips,
    num_events
FROM event_group_impacts
WHERE strftime(time_group, '%Y-%m-%d') = '2025-09-11'
ORDER BY time_group
LIMIT 5
"""

df_sample = conn.execute(query_sample).fetchdf()
if len(df_sample) > 0:
    print("Échantillon 11 septembre 2025 :")
    print(df_sample.to_string(index=False))
else:
    print("⚠️ Aucune donnée pour le 11 septembre dans event_group_impacts")
print()
print()

# ============================================================================
# PARTIE 2 : ANALYSE 11 SEPTEMBRE 2025
# ============================================================================
print("=" * 80)
print("PARTIE 2 : ANALYSE DÉTAILLÉE 11 SEPTEMBRE 2025")
print("=" * 80)
print()

# Question 2a : Quels événements US à 14:30 ?
print("📋 Question 2a : Événements US le 11 septembre 2025 à 14:30")
print("-" * 80)

query_sept11 = """
SELECT 
    strftime(ts_utc, '%H:%M:%S') as time,
    event_key,
    event_title,
    comparison,
    period,
    actual,
    estimate,
    previous,
    CASE 
        WHEN estimate IS NOT NULL AND estimate != 0 
        THEN ABS((actual - estimate) / estimate) * 100
        ELSE NULL
    END as surprise_pct
FROM events
WHERE strftime(ts_utc, '%Y-%m-%d') = '2025-09-11'
  AND country = 'US'
  AND strftime(ts_utc, '%H:%M') = '14:30'
  AND actual IS NOT NULL
ORDER BY surprise_pct DESC NULLS LAST
"""

df_sept11 = conn.execute(query_sept11).fetchdf()
print(df_sept11.to_string(index=False))
print()

# Trouver l'événement avec surprise max
if len(df_sept11) > 0 and 'surprise_pct' in df_sept11.columns:
    max_surprise_row = df_sept11.loc[df_sept11['surprise_pct'].idxmax()]
    print(f"🔥 SURPRISE MAXIMALE : {max_surprise_row['surprise_pct']:.1f}%")
    print(f"   Événement : {max_surprise_row['event_key']}")
    print(f"   Titre : {max_surprise_row['event_title']}")
    print(f"   Comparison : {max_surprise_row['comparison']}")
    print(f"   Actual : {max_surprise_row['actual']}, Estimate : {max_surprise_row['estimate']}")
    print()
else:
    print("⚠️ Aucune surprise calculable pour ces événements")
    print()

print()

# Question 2b : Matching avec event_families
print("📋 Question 2b : Matching avec event_families pour événements 11 sept")
print("-" * 80)

query_matching = """
SELECT 
    e.event_key,
    e.comparison,
    e.actual,
    e.estimate,
    ef.empirical_score,
    ef.avg_movement_pips,
    CASE 
        WHEN estimate IS NOT NULL AND estimate != 0 
        THEN ABS((actual - estimate) / estimate) * 100
        ELSE NULL
    END as surprise_pct
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE strftime(e.ts_utc, '%Y-%m-%d') = '2025-09-11'
  AND e.country = 'US'
  AND strftime(e.ts_utc, '%H:%M') = '14:30'
  AND e.actual IS NOT NULL
ORDER BY surprise_pct DESC NULLS LAST
"""

df_matching = conn.execute(query_matching).fetchdf()
print(df_matching.to_string(index=False))
print()

# Analyser le matching
matched = df_matching[df_matching['empirical_score'].notna()]
not_matched = df_matching[df_matching['empirical_score'].isna()]

print(f"✅ Événements matchés : {len(matched)}")
print(f"❌ Événements NON matchés : {len(not_matched)}")
if len(not_matched) > 0:
    print("   Événements non matchés :")
    for _, row in not_matched.iterrows():
        print(f"     - {row['event_key']} (comparison={row['comparison']})")
print()
print()

# Question 2c : Quel est le score MAX utilisé par V2 ?
print("📋 Question 2c : Score MAX et Surprise MAX (méthode V2)")
print("-" * 80)

if len(matched) > 0:
    max_score = matched['empirical_score'].max()
    max_surprise = matched['surprise_pct'].max()
    
    print(f"Score MAX : {max_score:.1f}")
    print(f"Surprise MAX : {max_surprise:.1f}%")
    
    # Événement avec score max
    max_score_event = matched.loc[matched['empirical_score'].idxmax()]
    print(f"\nÉvénement score MAX :")
    print(f"  - event_key : {max_score_event['event_key']}")
    print(f"  - comparison : {max_score_event['comparison']}")
    print(f"  - surprise : {max_score_event['surprise_pct']:.1f}%")
    
    # Événement avec surprise max
    if not pd.isna(max_surprise):
        max_surprise_event = matched.loc[matched['surprise_pct'].idxmax()]
        print(f"\nÉvénement surprise MAX :")
        print(f"  - event_key : {max_surprise_event['event_key']}")
        print(f"  - comparison : {max_surprise_event['comparison']}")
        print(f"  - surprise : {max_surprise_event['surprise_pct']:.1f}%")
        print(f"  - score : {max_surprise_event['empirical_score']:.1f}")
else:
    print("❌ Aucun événement matché avec event_families !")
    max_score = None
    max_surprise = None

print()
print()

# Question 2d : Impact réel depuis event_group_impacts
print("📋 Question 2d : Impact réel mesuré dans event_group_impacts")
print("-" * 80)

query_impact = """
SELECT 
    time_group,
    event_keys,
    mfe_pips,
    num_events,
    max_empirical_score
FROM event_group_impacts
WHERE strftime(time_group, '%Y-%m-%d %H:%M') = '2025-09-11 14:30'
"""

df_impact = conn.execute(query_impact).fetchdf()
if len(df_impact) > 0:
    print(df_impact.to_string(index=False))
    impact_real_db = df_impact['mfe_pips'].iloc[0]
    print(f"\n📊 Impact réel (DB) : {impact_real_db:.1f} pips")
else:
    print("⚠️ Aucune donnée dans event_group_impacts pour 11 sept 14:30")
    impact_real_db = None

print()
print()

# ============================================================================
# PARTIE 3 : TEST FORMULES V3
# ============================================================================
print("=" * 80)
print("PARTIE 3 : TEST FORMULES V3 SUR 11 SEPTEMBRE")
print("=" * 80)
print()

# Impact réel MT5 (depuis ANALYSE_MT5_11SEPT2025_SESSION20.md)
IMPACT_REAL_MT5 = 522.0  # Phase 1

print(f"📊 Impact RÉEL (MT5) : {IMPACT_REAL_MT5} pips (Phase 1)")
if impact_real_db:
    print(f"📊 Impact DB : {impact_real_db} pips")
print()

if max_score is not None and max_surprise is not None:
    print("🧪 TEST DES FORMULES")
    print("-" * 80)
    print()
    
    # Formule V2 baseline (actuelle)
    print("📐 V2 BASELINE (actuelle)")
    print("-" * 40)
    
    # Base impact
    impact_base = -7.08 + 0.419 * max_score
    print(f"Impact base : -7.08 + 0.419 × {max_score:.1f} = {impact_base:.1f} pips")
    
    # Amplification surprise
    surprise_decimal = max_surprise / 100
    if surprise_decimal < 0.05:
        amp = 1.0
    elif surprise_decimal < 0.15:
        amp = 1.0 + (surprise_decimal - 0.05) * 15
    else:
        amp = 2.5  # PLAFOND
    
    print(f"Surprise : {max_surprise:.1f}% → Amplification : {amp:.2f}×")
    
    # Impact final V2
    impact_v2 = abs(impact_base) * amp * 0.758
    erreur_v2 = abs(impact_v2 - IMPACT_REAL_MT5) / IMPACT_REAL_MT5 * 100
    
    print(f"Impact V2 : {abs(impact_base):.1f} × {amp:.2f} × 0.758 = {impact_v2:.1f} pips")
    print(f"Erreur V2 : {erreur_v2:.1f}%")
    print()
    
    # Formule V3a : Plafond 4.0×
    print("📐 V3a : PLAFOND 4.0× (au lieu de 2.5×)")
    print("-" * 40)
    
    if surprise_decimal < 0.05:
        amp_v3a = 1.0
    elif surprise_decimal < 0.15:
        amp_v3a = 1.0 + (surprise_decimal - 0.05) * 15
    elif surprise_decimal < 0.30:
        amp_v3a = 2.5 + (surprise_decimal - 0.15) * 10  # Continue jusqu'à 4.0
    else:
        amp_v3a = 4.0  # NOUVEAU PLAFOND
    
    impact_v3a = abs(impact_base) * amp_v3a * 0.758
    erreur_v3a = abs(impact_v3a - IMPACT_REAL_MT5) / IMPACT_REAL_MT5 * 100
    
    print(f"Amplification V3a : {amp_v3a:.2f}×")
    print(f"Impact V3a : {impact_v3a:.1f} pips")
    print(f"Erreur V3a : {erreur_v3a:.1f}%")
    print()
    
    # Formule V3b : Plafond 10× si score>70 et surprise>30%
    print("📐 V3b : PLAFOND 10× si score>70 ET surprise>30%")
    print("-" * 40)
    
    if max_score > 70 and surprise_decimal > 0.30:
        amp_v3b = 10.0
        print(f"✅ Conditions remplies (score={max_score:.1f}, surprise={max_surprise:.1f}%)")
    elif max_score > 70:
        amp_v3b = 4.0
        print(f"⚠️ Score>70 mais surprise≤30% → amp 4.0×")
    else:
        amp_v3b = 2.5
        print(f"⚠️ Conditions non remplies → amp standard 2.5×")
    
    impact_v3b = abs(impact_base) * amp_v3b * 0.758
    erreur_v3b = abs(impact_v3b - IMPACT_REAL_MT5) / IMPACT_REAL_MT5 * 100
    
    print(f"Amplification V3b : {amp_v3b:.2f}×")
    print(f"Impact V3b : {impact_v3b:.1f} pips")
    print(f"Erreur V3b : {erreur_v3b:.1f}%")
    print()
    
    # Formule V3c : Synergie ×2 pour multi-événements
    print("📐 V3c : SYNERGIE ×2 pour 5+ événements HIGH")
    print("-" * 40)
    
    num_events = len(matched)
    if num_events >= 5 and max_score > 70:
        synergy = 2.0
        print(f"✅ {num_events} événements, score MAX {max_score:.1f} → synergie 2.0×")
    elif num_events >= 3 and max_score > 60:
        synergy = 1.5
        print(f"⚠️ {num_events} événements, score MAX {max_score:.1f} → synergie 1.5×")
    elif num_events >= 2:
        synergy = 1.2
        print(f"⚠️ {num_events} événements → synergie 1.2×")
    else:
        synergy = 1.0
        print(f"1 événement → pas de synergie")
    
    impact_v3c = impact_v2 * synergy
    erreur_v3c = abs(impact_v3c - IMPACT_REAL_MT5) / IMPACT_REAL_MT5 * 100
    
    print(f"Impact V3c : {impact_v2:.1f} × {synergy:.1f} = {impact_v3c:.1f} pips")
    print(f"Erreur V3c : {erreur_v3c:.1f}%")
    print()
    
    # Formule V3d : Combinaison optimale
    print("📐 V3d : COMBINAISON OPTIMALE (V3b + V3c)")
    print("-" * 40)
    
    impact_v3d = abs(impact_base) * amp_v3b * 0.758 * synergy
    erreur_v3d = abs(impact_v3d - IMPACT_REAL_MT5) / IMPACT_REAL_MT5 * 100
    
    print(f"Impact base : {abs(impact_base):.1f} pips")
    print(f"× Amplification V3b : {amp_v3b:.2f}×")
    print(f"× Atténuation : 0.758")
    print(f"× Synergie V3c : {synergy:.1f}×")
    print(f"Impact V3d : {impact_v3d:.1f} pips")
    print(f"Erreur V3d : {erreur_v3d:.1f}%")
    print()
    
    # Tableau récapitulatif
    print()
    print("=" * 80)
    print("📊 TABLEAU RÉCAPITULATIF")
    print("=" * 80)
    print()
    
    results = pd.DataFrame({
        'Formule': ['V2 (baseline)', 'V3a (plafond 4.0×)', 'V3b (plafond 10×)', 'V3c (synergie)', 'V3d (combinaison)'],
        'Impact prédit (pips)': [impact_v2, impact_v3a, impact_v3b, impact_v3c, impact_v3d],
        'Erreur (%)': [erreur_v2, erreur_v3a, erreur_v3b, erreur_v3c, erreur_v3d]
    })
    
    results = results.sort_values('Erreur (%)')
    print(results.to_string(index=False))
    print()
    print(f"Impact RÉEL (MT5) : {IMPACT_REAL_MT5} pips")
    print()
    
    # Meilleure formule
    best_formula = results.iloc[0]
    print(f"🏆 MEILLEURE FORMULE : {best_formula['Formule']}")
    print(f"   Impact : {best_formula['Impact prédit (pips)']:.1f} pips")
    print(f"   Erreur : {best_formula['Erreur (%)']:.1f}%")
    
else:
    print("⚠️ Impossible de tester les formules (données manquantes)")

print()
print()

# ============================================================================
# SYNTHÈSE FINALE
# ============================================================================
print("=" * 80)
print("📋 SYNTHÈSE DES DIAGNOSTICS")
print("=" * 80)
print()

print("✅ RÉPONSES AUX QUESTIONS CRITIQUES :")
print("-" * 80)
print()

print("❓ Question 1 : Les event_key ont-ils les suffixes ?")
if has_suffixes:
    print("   ✅ OUI - Les event_key ont les suffixes (_mom, _yoy, _qoq)")
else:
    print("   ❌ NON - Les event_key n'ont PAS les suffixes")
    print("      → Solution : Utiliser le champ 'comparison' pour distinguer")
print()

print("❓ Question 2 : Quelle est la VRAIE surprise du 11 septembre ?")
if len(df_sept11) > 0 and not pd.isna(max_surprise):
    print(f"   ✅ {max_surprise:.1f}% sur {max_surprise_event['event_key']}")
else:
    print("   ⚠️ Données insuffisantes pour calculer")
print()

print("❓ Question 3 : Pourquoi V2 sous-estime autant ?")
if max_score is not None:
    print(f"   📊 Avec surprise {max_surprise:.1f}% et score {max_score:.1f} :")
    print(f"      - V2 prédit : {impact_v2:.1f} pips")
    print(f"      - Réel MT5 : {IMPACT_REAL_MT5} pips")
    print(f"      - Écart : ×{IMPACT_REAL_MT5/impact_v2:.1f}")
    print(f"   🔍 Cause probable : Plafond 2.5× trop conservateur")
    print(f"   💡 Meilleure formule : {best_formula['Formule']} (erreur {best_formula['Erreur (%)']:.1f}%)")
print()

print("❓ Question 4 : Faut-il re-importer ou adapter le code ?")
if not has_suffixes:
    print("   💡 RECOMMANDATION : Adapter le code")
    print("      - Utiliser le champ 'comparison' pour distinguer MoM/YoY")
    print("      - Créer une jointure flexible avec event_families")
    print("      - Pas besoin de re-importer (données déjà présentes)")
else:
    print("   💡 RECOMMANDATION : Mettre à jour event_families")
    print("      - Dupliquer les entrées avec suffixes _mom, _yoy, _qoq")
    print("      - Ou adapter event_families pour gérer comparison")
print()

print()
print("=" * 80)
print("✅ DIAGNOSTIC COMPLET TERMINÉ")
print("=" * 80)

conn.close()
