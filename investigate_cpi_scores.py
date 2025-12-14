"""
Investigation scores CPI - 11 septembre 2025
"""
import sys
from pathlib import Path
import pandas as pd

src_path = Path(__file__).parent / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
import duckdb

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

print("=" * 80)
print("🔍 INVESTIGATION SCORES CPI - 11 SEPTEMBRE 2025")
print("=" * 80)
print()

# Récupérer TOUS les détails des événements du 11 septembre
query = """
SELECT 
    e.event_key,
    e.label,
    e.ts_utc,
    e.actual,
    e.estimate,
    e.previous,
    e.importance_n,
    ef.family,
    ef.empirical_score,
    ef.avg_movement_pips,
    ef.sample_size
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = '2025-09-11'
    AND e.country = 'US'
ORDER BY e.ts_utc, ef.empirical_score DESC
"""

df = conn.execute(query).df()

print(f"Total événements US 11 sept : {len(df)}")
print()

# Afficher tous les événements avec leurs scores
print("📋 TOUS LES ÉVÉNEMENTS DU 11 SEPTEMBRE:")
print()
print(df[['label', 'ts_utc', 'actual', 'estimate', 'family', 'empirical_score', 'avg_movement_pips']].to_string())
print()

# Focus sur CPI
print("=" * 80)
print("🔍 FOCUS SUR ÉVÉNEMENTS CPI")
print("=" * 80)
print()

cpi_events = df[df['label'].str.contains('CPI', case=False, na=False) | 
                df['family'].str.contains('CPI', case=False, na=False)]

print(f"Nombre d'événements CPI : {len(cpi_events)}")
print()

for idx, row in cpi_events.iterrows():
    surprise_pct = 0
    if pd.notna(row['actual']) and pd.notna(row['estimate']) and row['estimate'] != 0:
        surprise_pct = ((row['actual'] - row['estimate']) / row['estimate']) * 100
    
    print(f"{row['label']}:")
    print(f"   Event key       : {row['event_key']}")
    print(f"   Family          : {row['family']}")
    print(f"   Actual          : {row['actual']}")
    print(f"   Estimate        : {row['estimate']}")
    print(f"   Previous        : {row['previous']}")
    print(f"   Surprise        : {surprise_pct:+.1f}%")
    print(f"   Empirical Score : {row['empirical_score']}")
    print(f"   Avg Movement    : {row['avg_movement_pips']} pips")
    print(f"   Sample Size     : {row['sample_size']}")
    print()

# Statistiques
print("=" * 80)
print("📊 STATISTIQUES CPI 11 SEPTEMBRE")
print("=" * 80)
print()

if len(cpi_events) > 0:
    print(f"Score moyen         : {cpi_events['empirical_score'].mean():.1f}")
    print(f"Score médian        : {cpi_events['empirical_score'].median():.1f}")
    print(f"Score min           : {cpi_events['empirical_score'].min():.1f}")
    print(f"Score max           : {cpi_events['empirical_score'].max():.1f}")
    print()
    print(f"Avg movement moyen  : {cpi_events['avg_movement_pips'].mean():.1f} pips")
    print(f"Avg movement médian : {cpi_events['avg_movement_pips'].median():.1f} pips")

print()

# Comparer avec d'autres événements CPI historiques
print("=" * 80)
print("📊 COMPARAISON AVEC AUTRES CPI HISTORIQUES")
print("=" * 80)
print()

query_hist = """
SELECT 
    ef.family,
    ef.empirical_score,
    ef.avg_movement_pips,
    ef.sample_size
FROM event_families ef
WHERE ef.family LIKE '%CPI%'
    AND ef.country = 'US'
ORDER BY ef.empirical_score DESC
"""

df_hist = conn.execute(query_hist).df()
print("Autres familles CPI dans la base :")
print()
print(df_hist.to_string())

conn.close()

print()
print("=" * 80)
print("🔍 ANALYSE:")
print("   - Vérifier si les scores 44-46 sont cohérents")
print("   - Comparer avg_movement_pips avec impact réel MT5 (+56.2 pips)")
print("   - Comprendre pourquoi empirical_score si bas")
print("=" * 80)
