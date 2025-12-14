"""
DIAGNOSTIC APPROFONDI 05.09.2025 - Session 90
Comprendre pourquoi MAE = 75.1 pips (outlier)
"""

import duckdb
import sys
from pathlib import Path

# Ajouter path pour imports
sys.path.insert(0, str(Path(__file__).parent.parent / "session89"))
from surprise_utils import calculate_surprise_robust, get_surprise_source

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*80)
print("🔍 DIAGNOSTIC APPROFONDI 05.09.2025 - Outlier NFP")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Charger événements 05.09.2025
query = """
SELECT 
    e.event_key,
    e.event_title,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.forecast,
    e.previous,
    ef.family,
    ef.empirical_score,
    ef.latency_median
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-05'
    AND e.country = 'US'
    AND ef.empirical_score > 40
ORDER BY e.ts_utc
"""

events = conn.execute(query).df()

print(f"\n📊 ÉVÉNEMENTS 05.09.2025 :")
print(f"   Total événements HIGH : {len(events)}")

if len(events) == 0:
    print("\n❌ AUCUN ÉVÉNEMENT TROUVÉ !")
    print("   Causes possibles :")
    print("   1. Date sans événements HIGH (score > 40)")
    print("   2. Problème jointure event_families")
    print("   3. Pas d'événements US ce jour")
    conn.close()
    sys.exit(1)

# 2. Analyser chaque événement
print("\n" + "="*80)
print("📋 DÉTAIL ÉVÉNEMENTS :")
print("="*80)

for idx, row in events.iterrows():
    print(f"\n{'='*80}")
    print(f"Événement #{idx+1} : {row['event_title']}")
    print(f"{'='*80}")
    print(f"   Timestamp    : {row['ts_utc']}")
    print(f"   Family       : {row['family']}")
    print(f"   Score        : {row['empirical_score']:.1f}")
    print(f"   Latence      : {row['latency_median']:.1f} min")
    
    print(f"\n   Valeurs économiques :")
    print(f"      actual   : {row['actual']}")
    print(f"      estimate : {row['estimate']}")
    print(f"      forecast : {row['forecast']}")
    print(f"      previous : {row['previous']}")
    
    # Calculer surprise avec fallback robuste
    surprise = calculate_surprise_robust(
        row['actual'],
        row['estimate'],
        row['forecast'],
        row['previous']
    )
    
    source = get_surprise_source(
        row['estimate'],
        row['forecast'],
        row['previous']
    )
    
    print(f"\n   Surprise calculée : {surprise:.1f}%")
    print(f"   Source utilisée   : {source}")
    
    # Vérifier si surprise = 0 (problème potentiel)
    if surprise == 0.0:
        print(f"   ⚠️ PROBLÈME : Surprise = 0% (aucune référence disponible)")
    elif source != "estimate":
        print(f"   ℹ️ INFO : Fallback utilisé ({source})")

# 3. Statistiques globales
print("\n" + "="*80)
print("📊 STATISTIQUES GLOBALES :")
print("="*80)

total = len(events)
with_estimate = events['estimate'].notna().sum()
with_forecast = events['forecast'].notna().sum()
with_previous = events['previous'].notna().sum()
with_actual = events['actual'].notna().sum()

print(f"\n   Total événements    : {total}")
print(f"   Avec actual         : {with_actual} ({with_actual/total*100:.0f}%)")
print(f"   Avec estimate       : {with_estimate} ({with_estimate/total*100:.0f}%)")
print(f"   Avec forecast       : {with_forecast} ({with_forecast/total*100:.0f}%)")
print(f"   Avec previous       : {with_previous} ({with_previous/total*100:.0f}%)")

# Coverage (au moins une référence)
with_any_ref = events.apply(
    lambda r: r['estimate'] is not None or r['forecast'] is not None or r['previous'] is not None,
    axis=1
).sum()

print(f"   Avec ≥1 référence    : {with_any_ref}/{total} ({with_any_ref/total*100:.0f}%)")

if with_any_ref < total:
    print(f"\n   ⚠️ {total - with_any_ref} événements SANS référence (surprise = 0%)")

# 4. Calcul surprises théoriques
print("\n" + "="*80)
print("📈 SURPRISES THÉORIQUES :")
print("="*80)

surprises = []
for idx, row in events.iterrows():
    surprise = calculate_surprise_robust(
        row['actual'],
        row['estimate'],
        row['forecast'],
        row['previous']
    )
    surprises.append(surprise)
    
    source = get_surprise_source(
        row['estimate'],
        row['forecast'],
        row['previous']
    )
    
    print(f"   {row['event_title'][:40]:40s} : {surprise:6.1f}% [{source}]")

surprise_max = max(surprises) if surprises else 0
surprise_cumule = sum(surprises)

print(f"\n   Surprise MAX        : {surprise_max:.1f}%")
print(f"   Surprise cumulée    : {surprise_cumule:.1f}%")

# 5. Comparaison avec dates réussies
print("\n" + "="*80)
print("📊 COMPARAISON AVEC DATES RÉUSSIES :")
print("="*80)

comparison_dates = [
    ('2025-08-01', 'Succès (0.3 pips)'),
    ('2025-09-17', 'Succès (0.3 pips)')
]

print(f"\n   {'Date':<12} {'Événements':>11} {'Score Moy':>10} {'Surprise Max':>13} {'Status':>20}")
print(f"   {'-'*12} {'-'*11} {'-'*10} {'-'*13} {'-'*20}")
print(f"   {'2025-09-05':<12} {total:>11} {events['empirical_score'].mean():>10.1f} {surprise_max:>13.1f}% {'PROBLÈME (75.1 pips)':>20}")

for date, status in comparison_dates:
    query_comp = f"""
    SELECT 
        COUNT(*) as total,
        AVG(ef.empirical_score) as score_avg
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '{date}'
        AND e.country = 'US'
        AND ef.empirical_score > 40
    """
    
    result = conn.execute(query_comp).fetchone()
    if result and result[0] > 0:
        print(f"   {date:<12} {result[0]:>11} {result[1]:>10.1f} {'N/A':>13} {status:>20}")

conn.close()

print("\n" + "="*80)
print("✅ Diagnostic terminé")
print("="*80)
print("\n💡 ANALYSE À FAIRE :")
print("   1. Si surprise_max faible (<15%) → Normal que précision moindre")
print("   2. Si événements sans référence → Surprise=0 fausse prédictions")
print("   3. Si score moyen bas (<50) → Impact réel peut varier")
print("   4. Comparer structure vs 01.08 (17 événements, surprise 500%)")
