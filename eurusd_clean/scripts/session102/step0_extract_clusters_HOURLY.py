#!/usr/bin/env python3
"""
STEP0 CORRIGÉ - EXTRACTION CLUSTERS PAR DATE+HEURE
===================================================

CORRECTION CRITIQUE : Grouper par DATE **ET HEURE** !

Un "cluster" = événements qui arrivent EN MÊME TEMPS
- 11.09.2025 à 12:30 UTC = un cluster (CPI + Jobless)
- 11.09.2025 à 16:30 UTC = un AUTRE cluster (Bill Auctions)

Méthode : Arrondir ts_utc à l'heure la plus proche
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

print("=" * 80)
print("STEP0 CORRIGÉ - CLUSTERS PAR DATE+HEURE")
print("=" * 80)
print()

# ============================================================================
# PARAMÈTRES
# ============================================================================

MIN_EVENTS = 5
MAX_EVENTS = 15
MIN_AVG_SCORE = 40
MIN_SCORE_EVENT = 40
TARGET_CLUSTERS = 30

START_DATE = '2024-01-01'
END_DATE = '2025-10-31'

print(f"📋 CRITÈRES :")
print(f"   Événements : {MIN_EVENTS}-{MAX_EVENTS}")
print(f"   Score min  : {MIN_SCORE_EVENT}")
print(f"   Target     : {TARGET_CLUSTERS} clusters")
print()

# ============================================================================
# EXTRACTION
# ============================================================================

db_path = get_db_path()
conn = duckdb.connect(str(db_path), read_only=True)

query = """
WITH hourly_clusters AS (
    SELECT 
        DATE(e.ts_utc) as event_date,
        DATE_TRUNC('hour', e.ts_utc) as event_hour,
        COUNT(*) as num_events,
        AVG(ef.empirical_score) as avg_score,
        MIN(ef.empirical_score) as min_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= ?
        AND e.ts_utc < ?
        AND e.country = 'US'
        AND ef.empirical_score > ?
    GROUP BY DATE(e.ts_utc), DATE_TRUNC('hour', e.ts_utc)
    HAVING COUNT(*) >= ?
        AND COUNT(*) <= ?
        AND MIN(ef.empirical_score) >= ?
)
SELECT 
    event_date,
    event_hour,
    num_events,
    avg_score,
    min_score
FROM hourly_clusters
ORDER BY event_date DESC
LIMIT ?
"""

df_clusters = conn.execute(query, [
    START_DATE,
    END_DATE,
    MIN_SCORE_EVENT,
    MIN_EVENTS,
    MAX_EVENTS,
    MIN_SCORE_EVENT,
    TARGET_CLUSTERS
]).fetchdf()

conn.close()

print(f"✅ Trouvé {len(df_clusters)} clusters\n")

# ============================================================================
# AFFICHER
# ============================================================================

print("=" * 80)
print("CLUSTERS SÉLECTIONNÉS")
print("=" * 80)
print()

for idx, row in df_clusters.iterrows():
    print(f"{idx+1:2d}. {row['event_date']} {row['event_hour'].strftime('%H:%M')} : "
          f"{int(row['num_events'])} events, score={row['avg_score']:.1f}")

# ============================================================================
# SAUVEGARDER
# ============================================================================

data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

output_path = data_dir / "step0_clusters_HOURLY.csv"
df_clusters.to_csv(output_path, index=False)

print()
print("=" * 80)
print(f"✅ Sauvegardé : {output_path.name}")
print("=" * 80)
print()
print("⚠️  ATTENTION : Les étapes suivantes doivent utiliser")
print("   event_date ET event_hour pour filtrer correctement !")
