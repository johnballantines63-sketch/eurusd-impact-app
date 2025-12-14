"""
RECHERCHE DATE ALTERNATIVE - Remplacement 2025-02-03
======================================================

Chercher dates 2024-2025 avec événements HIGH (score > 40)
pour remplacer 2025-02-03 qui n'a plus d'événements.
"""

import duckdb
from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import config
DB_PATH = config.DB_PATH

print("="*80)
print("RECHERCHE DATES ALTERNATIVES 2024-2025 (score > 40)")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Chercher toutes les dates 2024-2025 avec events HIGH
query = """
SELECT 
    DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') as date,
    COUNT(*) as num_events,
    SUM(f.empirical_score) as total_score,
    STRING_AGG(DISTINCT e.country, ', ') as countries
FROM events e
LEFT JOIN event_families f 
    ON e.event_key = f.event_key 
    AND e.country = f.country
WHERE e.ts_utc >= '2024-01-01'
  AND e.ts_utc < '2026-01-01'
  AND f.empirical_score > 40.0
GROUP BY DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich')
HAVING COUNT(*) >= 5  -- Au moins 5 events HIGH
ORDER BY total_score DESC
LIMIT 20
"""

df = conn.execute(query).df()

print(f"📊 TOP 20 DATES 2024-2025 (avec ≥5 events HIGH, score > 40)")
print()
print(f"{'Date':<12} {'Events':<8} {'Score Total':<12} {'Pays':<30}")
print("-" * 80)

for idx, row in df.iterrows():
    date_str = row['date'].strftime('%Y-%m-%d')
    print(f"{date_str:<12} {row['num_events']:<8} {row['total_score']:<12.1f} {row['countries'][:30]}")

print()
print("="*80)

# Vérifier spécifiquement quelques dates alternatives
print("🔍 VÉRIFICATION DATES ALTERNATIVES SUGGÉRÉES")
print("="*80)
print()

suggested_dates = [
    ('2024-06-12', 'NFP/CPI possible'),
    ('2024-08-02', 'NFP + emploi'),
    ('2024-12-18', 'Fed Decision'),
    ('2025-01-10', 'NFP possible'),
]

for date_str, description in suggested_dates:
    query_detail = """
    SELECT 
        e.ts_utc, e.country, e.event_title,
        f.empirical_score as score
    FROM events e
    LEFT JOIN event_families f 
        ON e.event_key = f.event_key 
        AND e.country = f.country
    WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
      AND f.empirical_score > 40.0
    ORDER BY f.empirical_score DESC, e.ts_utc
    """
    
    df_detail = conn.execute(query_detail, [date_str]).df()
    
    if len(df_detail) > 0:
        total_score = df_detail['score'].sum()
        print(f"📅 {date_str} ({description})")
        print(f"   Events HIGH : {len(df_detail)}, Score total : {total_score:.1f}")
        
        # Afficher top 3 events
        for i in range(min(3, len(df_detail))):
            row = df_detail.iloc[i]
            ts_str = row['ts_utc'].strftime('%H:%M') if hasattr(row['ts_utc'], 'strftime') else str(row['ts_utc'])
            print(f"   {ts_str} - {row['event_title'][:35]:35} ({row['country']}) score={row['score']:.1f}")
        if len(df_detail) > 3:
            print(f"   ... et {len(df_detail)-3} autres")
    else:
        print(f"📅 {date_str} ({description})")
        print(f"   ❌ Aucun événement HIGH")
    
    print()

conn.close()

print("="*80)
print("✅ RECHERCHE TERMINÉE")
print("="*80)
print()
print("💡 SUGGESTION: Choisir une date avec:")
print("   - Score total 150-350 (Overlap standard)")
print("   - 5-10 events HIGH")
print("   - Pays majeurs (US, EU, UK, CA)")
