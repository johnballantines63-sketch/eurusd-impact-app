#!/usr/bin/env python3
"""
SIMULATION PLANIFICATEUR V2.7 - 11 SEPTEMBRE 2025
==================================================

Simule EXACTEMENT ce que le Planificateur V2.7 fait pour calculer
l'impact du 11 septembre 2025.

Utilise:
- La MÊME requête SQL
- La MÊME logique de calcul
- Les MÊMES formules validées

Objectif: Comprendre pourquoi cluster_impact_calculator donne 49.4 pips
alors que le Planificateur devrait donner 37.4 pips.

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import duckdb

# Chemins
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent.parent.parent
src_path = project_root / 'fx_impact_app' / 'src'
db_path = project_root / 'eurusd_clean' / 'app' / 'data' / 'warehouse.duckdb'

sys.path.insert(0, str(src_path))

from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c
)

print("="*80)
print("📊 SIMULATION PLANIFICATEUR V2.7 - 11 SEPTEMBRE 2025")
print("="*80)

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : EXTRAIRE ÉVÉNEMENTS COMME LE PLANIFICATEUR
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("ÉTAPE 1 : EXTRACTION ÉVÉNEMENTS (REQUÊTE PLANIFICATEUR)")
print("="*80)

con = duckdb.connect(str(db_path), read_only=True)

target_date = datetime(2025, 9, 11)
date_str = target_date.strftime('%Y-%m-%d')

# REQUÊTE EXACTE DU PLANIFICATEUR (lignes ~220-245)
query_planificateur = """
SELECT 
    e.ts_utc,
    e.event_key,
    e.country,
    MAX(COALESCE(e.event_title, e.event_key)) as label,
    MAX(e.actual) as actual,
    MAX(e.estimate) as estimate,
    MAX(e.forecast) as forecast,
    MAX(e.previous) as previous,
    MIN(ef.family) as family,
    AVG(ef.empirical_score) as empirical_score,
    AVG(ef.latency_median) as latency_median,
    MAX(e.importance_n) as importance_n
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country IN ('US', 'EU', 'DE', 'FR', 'IT', 'ES', 'GB', 'NL', 'BE', 'AT', 'PT', 'IE', 'GR')
    AND (ef.empirical_score > 20 OR ef.empirical_score IS NULL)
GROUP BY e.ts_utc, e.event_key, e.country
ORDER BY e.ts_utc
"""

print(f"\n📋 Requête SQL du Planificateur:")
print(f"   - Date: {date_str}")
print(f"   - Pays: US, EU, DE, FR, IT, ES, GB, etc.")
print(f"   - Score min: > 20")
print(f"   - GROUP BY: ts_utc, event_key, country")

df_events = con.execute(query_planificateur, [date_str]).df()

print(f"\n✅ Événements extraits (avant déduplication): {len(df_events)}")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : DÉDUPLICATION (COMME LE PLANIFICATEUR)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("ÉTAPE 2 : DÉDUPLICATION (LOGIQUE PLANIFICATEUR)")
print("="*80)

if not df_events.empty:
    # Normaliser labels pour détection doublons
    df_events['label_normalized'] = df_events['label'].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
    
    print(f"\n📊 Avant déduplication: {len(df_events)} lignes")
    
    # Trier par score (desc) pour garder meilleure ligne
    df_events = df_events.sort_values('empirical_score', ascending=False, na_position='last')
    
    # Dédupliquer sur (ts_utc, label_normalized, country)
    df_events = df_events.drop_duplicates(subset=['ts_utc', 'label_normalized', 'country'], keep='first')
    
    print(f"📊 Après déduplication: {len(df_events)} lignes")
    
    # Retirer colonne temporaire
    df_events = df_events.drop(columns=['label_normalized'])
    
    # Retrier par ts_utc pour ordre chronologique
    df_events = df_events.sort_values('ts_utc')
    df_events = df_events.reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : FILTRER ÉVÉNEMENTS 14:30 (CLUSTER PRINCIPAL)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("ÉTAPE 3 : FILTRAGE CLUSTER 14:30")
print("="*80)

df_events['ts_utc'] = pd.to_datetime(df_events['ts_utc'])
df_cluster_1430 = df_events[df_events['ts_utc'].dt.strftime('%H:%M') == '14:30'].copy()

print(f"\n✅ Événements à 14:30: {len(df_cluster_1430)}")

if len(df_cluster_1430) > 0:
    print("\n📋 Liste des événements:")
    print("-"*80)
    for i, row in df_cluster_1430.iterrows():
        print(f"{i+1}. {row['label']}")
        print(f"   event_key: {row['event_key']}")
        print(f"   country: {row['country']}")
        print(f"   score: {row['empirical_score']:.2f}")
        print(f"   actual: {row['actual']}, estimate: {row['estimate']}")
        print()

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : CALCUL IMPACT (LOGIQUE PLANIFICATEUR)
# ══════════════════════════════════════════════════════════════════════

print("="*80)
print("ÉTAPE 4 : CALCUL IMPACT (MÉTHODE PLANIFICATEUR V2.7)")
print("="*80)

if len(df_cluster_1430) == 0:
    print("\n❌ Aucun événement à 14:30 !")
    con.close()
    sys.exit(1)

# 1. Score base moyen
base_score_avg = df_cluster_1430['empirical_score'].mean()
print(f"\n1️⃣ Score base moyen: {base_score_avg:.2f}")

# 2. Surprise max
surprises = []
max_surprise = 0

for _, event in df_cluster_1430.iterrows():
    if pd.notna(event['actual']) and pd.notna(event['estimate']) and abs(event['estimate']) > 0.01:
        surprise_pct = abs((event['actual'] - event['estimate']) / event['estimate']) * 100
        surprises.append(surprise_pct)
        if surprise_pct > max_surprise:
            max_surprise = surprise_pct
            max_surprise_event = event['label']

print(f"\n2️⃣ Surprises:")
print(f"   Nombre: {len(surprises)}")
print(f"   Moyenne: {np.mean(surprises):.2f}%")
print(f"   Max: {max_surprise:.2f}% ({max_surprise_event})")

# 3. Score ajusté
adjusted_score = calculate_adjusted_empirical_score(
    base_empirical_score=base_score_avg,
    surprise_pct=max_surprise
)

print(f"\n3️⃣ Score ajusté (avec surprise max):")
print(f"   Base: {base_score_avg:.2f}")
print(f"   Surprise: {max_surprise:.2f}%")
print(f"   Ajusté: {adjusted_score:.2f}")
print(f"   Factor: {adjusted_score / base_score_avg:.2f}x")

# 4. Impact avec formule D (amplification par défaut = 2.5)
amplification_default = 2.5
num_events = len(df_cluster_1430)

impact_pips = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=num_events,
    amplification=amplification_default
)

print(f"\n4️⃣ Impact calculé (Formule D):")
print(f"   Score ajusté: {adjusted_score:.2f}")
print(f"   Nombre événements: {num_events}")
print(f"   Amplification: {amplification_default}")
print(f"   → Impact: {impact_pips:.1f} pips")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : VALIDATION VS RÉFÉRENCE MT5
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("ÉTAPE 5 : VALIDATION VS RÉFÉRENCE MT5")
print("="*80)

expected_impact_mt5 = 37.4
tolerance = 5.0

ecart = abs(impact_pips - expected_impact_mt5)
ecart_pct = (ecart / expected_impact_mt5) * 100

print(f"\n📊 Comparaison:")
print(f"   Impact calculé:    {impact_pips:.1f} pips")
print(f"   Impact MT5:        {expected_impact_mt5:.1f} pips")
print(f"   Écart:             {ecart:.1f} pips ({ecart_pct:.1f}%)")
print(f"   Tolérance:         ±{tolerance:.1f} pips")

if ecart <= tolerance:
    print(f"\n✅ VALIDATION OK: Impact dans tolérance")
else:
    print(f"\n❌ VALIDATION KO: Impact hors tolérance")
    
    # Calculer amplification nécessaire
    amp_needed = (expected_impact_mt5 / impact_pips) * amplification_default
    print(f"\n💡 Amplification nécessaire: {amp_needed:.2f} (au lieu de {amplification_default})")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 6 : TESTS AVEC DIFFÉRENTES AMPLIFICATIONS
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("ÉTAPE 6 : SIMULATION AMPLIFICATIONS DIFFÉRENTES")
print("="*80)

print(f"\n{'Amplification':<15} {'Impact':<10} {'Écart vs MT5':<15} {'Status'}")
print("-"*55)

for amp in [1.5, 1.89, 2.0, 2.5, 3.0, 3.5]:
    impact_test = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=num_events,
        amplification=amp
    )
    ecart_test = abs(impact_test - expected_impact_mt5)
    status = "✅" if ecart_test <= tolerance else "❌"
    
    print(f"{amp:<15.2f} {impact_test:<10.1f} {ecart_test:<15.1f} {status}")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 RÉSUMÉ FINAL")
print("="*80)

print(f"\n🎯 Configuration Planificateur:")
print(f"   Événements extraits: {len(df_cluster_1430)}")
print(f"   Score moyen: {base_score_avg:.2f}")
print(f"   Surprise max: {max_surprise:.2f}%")
print(f"   Score ajusté: {adjusted_score:.2f}")
print(f"   Amplification: {amplification_default}")

print(f"\n📈 Résultats:")
print(f"   Impact calculé: {impact_pips:.1f} pips")
print(f"   Impact attendu: {expected_impact_mt5:.1f} pips")
print(f"   Différence: {ecart:.1f} pips")

if ecart > tolerance:
    print(f"\n⚠️  CONCLUSION:")
    print(f"   Le Planificateur avec amplification {amplification_default} donne {impact_pips:.1f} pips")
    print(f"   Ce qui est {ecart:.1f} pips ({ecart_pct:.1f}%) au-dessus de la référence MT5")
    print(f"   ")
    print(f"   Solutions possibles:")
    print(f"   A. Amplification à ajuster: ~{amp_needed:.2f} au lieu de {amplification_default}")
    print(f"   B. Filtrer différemment les événements")
    print(f"   C. Revoir le calcul vectoriel")

con.close()

print("\n" + "="*80)
print("FIN DE LA SIMULATION")
print("="*80)
