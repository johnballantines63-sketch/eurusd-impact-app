#!/usr/bin/env python3
"""
ANALYSER SCORES JOBLESS CLAIMS
================================

Trouver le score minimum réel des Jobless Claims
pour définir un seuil basé sur les données, pas au hasard
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemins
project_root = Path(__file__).resolve().parents[2]
fx_impact_app = project_root.parent / "fx_impact_app"
sys.path.insert(0, str(fx_impact_app / "src"))

from config import get_db_path

print("=" * 100)
print("ANALYSER SCORES JOBLESS CLAIMS")
print("=" * 100)
print()

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

# ============================================================================
# TOUS LES ÉVÉNEMENTS JOBLESS CLAIMS
# ============================================================================

query = """
SELECT DISTINCT
    ef.event_key,
    ef.family,
    ef.empirical_score
FROM event_families ef
WHERE ef.country = 'US'
    AND ef.family = 'Jobless Claims'
ORDER BY ef.empirical_score DESC
"""

df_jobless = conn.execute(query).fetchdf()

print("=" * 100)
print(f"ÉVÉNEMENTS JOBLESS CLAIMS : {len(df_jobless)}")
print("=" * 100)
print()

if len(df_jobless) > 0:
    for idx, row in df_jobless.iterrows():
        print(f"{idx+1}. {row['event_key']:45s} | Score: {row['empirical_score']:.1f}")
    
    print()
    print("=" * 100)
    print("STATISTIQUES")
    print("=" * 100)
    print()
    
    min_score = df_jobless['empirical_score'].min()
    max_score = df_jobless['empirical_score'].max()
    mean_score = df_jobless['empirical_score'].mean()
    
    print(f"Score minimum : {min_score:.1f}")
    print(f"Score maximum : {max_score:.1f}")
    print(f"Score moyen   : {mean_score:.1f}")
    
    # Compter combien seraient inclus avec différents seuils
    print()
    print("=" * 100)
    print("SEUILS POSSIBLES")
    print("=" * 100)
    print()
    
    seuils = [15, 20, 25, 26, 27, 30, 35, 40]
    
    print(f"{'Seuil':>8} {'Inclus':>10} {'Exclus':>10} {'% Inclus':>12}")
    print("-" * 50)
    
    for seuil in seuils:
        inclus = (df_jobless['empirical_score'] > seuil).sum()
        exclus = len(df_jobless) - inclus
        pct = 100.0 * inclus / len(df_jobless)
        print(f"{seuil:>8} {inclus:>10} {exclus:>10} {pct:>11.1f}%")
    
    # Recommandation
    print()
    print("=" * 100)
    print("RECOMMANDATION")
    print("=" * 100)
    print()
    
    print(f"Score minimum des Jobless Claims : {min_score:.1f}")
    print()
    
    if min_score >= 40:
        print("✅ AUCUNE EXCEPTION NÉCESSAIRE !")
        print("   Tous les Jobless Claims ont score > 40")
        print("   Filtre actuel suffit :")
        print("   WHERE (importance_n = 1) OR (empirical_score > 40)")
    elif min_score >= 30:
        print(f"✅ SEUIL OPTIMAL : {min_score:.0f}")
        print(f"   Tous les Jobless Claims ont score > {min_score:.0f}")
        print(f"   Exception cohérente :")
        print(f"   WHERE ... OR (family = 'Jobless Claims' AND empirical_score > {min_score:.0f})")
    else:
        print(f"⚠️  SEUIL SUGGÉRÉ : {min_score:.0f}")
        print(f"   Inclut TOUS les Jobless Claims (score min = {min_score:.1f})")
        print()
        print("   MAIS ATTENTION :")
        print(f"   - Score {min_score:.1f} << 40 (seuil principal)")
        print("   - Impact réel sur EUR/USD probablement faible")
        print("   - Risque de triple comptage (continuing + initial + 4-week)")
        print()
        print("   ALTERNATIVES :")
        print()
        print(f"   A. Seuil strict = {min_score:.0f} (inclut tous)")
        print(f"      WHERE ... OR (family = 'Jobless Claims' AND empirical_score > {min_score:.0f})")
        print()
        print(f"   B. Seuil conservateur = {mean_score:.0f} (inclut moyenne et plus)")
        print(f"      WHERE ... OR (family = 'Jobless Claims' AND empirical_score > {mean_score:.0f})")
        print()
        print("   C. Pas d'exception (garde seuil 40)")
        print("      WHERE (importance_n = 1) OR (empirical_score > 40)")

else:
    print("❌ Aucun Jobless Claims trouvé dans event_families !")

# ============================================================================
# VÉRIFIER 11.09.2025 AVEC DIFFÉRENTS SEUILS
# ============================================================================

print()
print("=" * 100)
print("TEST SUR 11.09.2025 : ÉVÉNEMENTS INCLUS SELON SEUIL")
print("=" * 100)
print()

TEST_DATE = '2025-09-11'
TEST_HOUR = '2025-09-11 14:00:00'

seuils_test = [0, 20, 25, 26, 40]

for seuil in seuils_test:
    query_test = f"""
    SELECT 
        e.event_key,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND DATE_TRUNC('hour', e.ts_utc) = ?
        AND e.country = 'US'
        AND (
            e.importance_n = 1
            OR ef.empirical_score > 40
            OR (ef.family = 'Jobless Claims' AND ef.empirical_score > {seuil})
        )
    ORDER BY e.ts_utc
    """
    
    df_test = conn.execute(query_test, [TEST_DATE, pd.Timestamp(TEST_HOUR)]).fetchdf()
    
    # Compter jobless
    jobless_count = (df_test['family'] == 'Jobless Claims').sum()
    total_count = len(df_test)
    
    print(f"Seuil Jobless > {seuil:>2} : {total_count:>2} événements dont {jobless_count} Jobless Claims")

conn.close()

print()
print("=" * 100)
print("CONCLUSION")
print("=" * 100)
print()

print("Utiliser le score minimum réel pour définir l'exception Jobless Claims.")
print("Cela garantit que TOUS les vrais Jobless Claims sont inclus,")
print("sans choisir un seuil arbitraire.")
