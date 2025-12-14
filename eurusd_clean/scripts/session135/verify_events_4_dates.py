"""
VÉRIFICATION RAPIDE - Événements HIGH (score > 40) pour 4 dates
================================================================
"""

import duckdb
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import config
DB_PATH = config.DB_PATH

dates_test = [
    ('2025-09-11', 'OUTLIER'),
    ('2023-02-03', 'STANDARD'),
    ('2023-03-22', 'STANDARD'),
    ('2025-02-03', 'STANDARD')
]

print("="*80)
print("VÉRIFICATION ÉVÉNEMENTS HIGH (score > 40) - 4 DATES")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

for date_str, type_cas in dates_test:
    query = """
    SELECT 
        e.ts_utc, e.country, e.event_title, e.event_key,
        e.actual, e.estimate, e.previous,
        f.empirical_score
    FROM events e
    LEFT JOIN event_families f 
        ON e.event_key = f.event_key 
        AND e.country = f.country
    WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
      AND f.empirical_score > 40.0
    ORDER BY f.empirical_score DESC, e.ts_utc
    """
    
    df = conn.execute(query, [date_str]).df()
    
    print(f"📅 {date_str} ({type_cas})")
    print(f"   Events HIGH (score > 40) : {len(df)}")
    
    if len(df) > 0:
        total_score = df['empirical_score'].sum()
        print(f"   Score total : {total_score:.1f}")
        print()
        # Afficher tous les events HIGH
        for idx in range(len(df)):
            row = df.iloc[idx]
            ts_str = row['ts_utc'].strftime('%H:%M') if hasattr(row['ts_utc'], 'strftime') else str(row['ts_utc'])
            print(f"   {ts_str} - {row['event_title'][:40]:40} ({row['country']}) score={row['empirical_score']:.1f}")
    else:
        print(f"   ❌ AUCUN ÉVÉNEMENT HIGH TROUVÉ")
        
        # Vérifier si événements MEDIUM existent
        query_all = """
        SELECT COUNT(*) as count
        FROM events
        WHERE DATE(ts_utc AT TIME ZONE 'Europe/Zurich') = ?
        """
        count_all = conn.execute(query_all, [date_str]).fetchone()[0]
        print(f"   ℹ️  Mais {count_all} événements MEDIUM (tous scores) existent")
    
    print()

conn.close()

print("="*80)
print("✅ VÉRIFICATION TERMINÉE")
print("="*80)
