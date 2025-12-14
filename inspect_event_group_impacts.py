"""
INSPECTION TABLE event_group_impacts
Comprendre la structure avant Session 17
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("=" * 80)
print("🔍 INSPECTION TABLE event_group_impacts")
print("=" * 80)
print()

# Schéma de la table
print("📋 SCHÉMA DE LA TABLE :")
schema = conn.execute("PRAGMA table_info(event_group_impacts)").fetchdf()
print(schema.to_string(index=False))
print()

# Statistiques
print("📊 STATISTIQUES :")
stats = conn.execute("""
    SELECT 
        COUNT(*) as total_groups,
        COUNT(DISTINCT time_group) as unique_time_groups,
        MIN(time_group) as first_date,
        MAX(time_group) as last_date,
        AVG(num_events) as avg_events_per_group,
        AVG(mfe_pips) as avg_mfe_pips,
        AVG(max_empirical_score) as avg_max_score,
        AVG(mean_empirical_score) as avg_mean_score
    FROM event_group_impacts
""").fetchdf()
print(stats.to_string(index=False))
print()

# Échantillon de données
print("📄 ÉCHANTILLON (5 premières lignes) :")
sample = conn.execute("""
    SELECT *
    FROM event_group_impacts
    ORDER BY time_group DESC
    LIMIT 5
""").fetchdf()
print(sample.to_string(index=False))
print()

# Distribution par nombre d'événements
print("📈 DISTRIBUTION PAR NOMBRE D'ÉVÉNEMENTS :")
dist = conn.execute("""
    SELECT 
        num_events,
        COUNT(*) as count,
        AVG(mfe_pips) as avg_mfe
    FROM event_group_impacts
    GROUP BY num_events
    ORDER BY num_events
""").fetchdf()
print(dist.to_string(index=False))
print()

# Distribution par année
print("📅 DISTRIBUTION PAR ANNÉE :")
years = conn.execute("""
    SELECT 
        CAST(strftime(time_group, '%Y') AS INTEGER) as year,
        COUNT(*) as count,
        AVG(mfe_pips) as avg_mfe
    FROM event_group_impacts
    GROUP BY year
    ORDER BY year
""").fetchdf()
print(years.to_string(index=False))
print()

# Vérifier si on a les données nécessaires pour calculer la surprise
print("🔍 VÉRIFICATION DONNÉES SURPRISE :")
print("Colonnes nécessaires : actual, estimate, event_keys")
print()

conn.close()

print("=" * 80)
print("✅ INSPECTION TERMINÉE")
print("=" * 80)
