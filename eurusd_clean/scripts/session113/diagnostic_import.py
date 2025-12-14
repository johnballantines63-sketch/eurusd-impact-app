"""
DIAGNOSTIC IMPORT - Session 113
================================

Analyse la distribution des événements importés pour comprendre
pourquoi seulement 1,250 événements.

Session 113 - André Valentin
"""
import sys
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import DB_PATH

print("=" * 80)
print("DIAGNOSTIC IMPORT - DISTRIBUTION ÉVÉNEMENTS")
print("=" * 80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Total
total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
print(f"\nTotal événements: {total:,}")

# Par année
print("\n📅 DISTRIBUTION PAR ANNÉE:")
print("-" * 80)

years = conn.execute("""
    SELECT 
        date_part('year', ts_utc) as year,
        COUNT(*) as count
    FROM events
    GROUP BY year
    ORDER BY year
""").fetchdf()

for _, row in years.iterrows():
    year = int(row['year'])
    count = row['count']
    print(f"  {year}: {count:4d} événements")

# Par pays
print("\n🌍 DISTRIBUTION PAR PAYS:")
print("-" * 80)

countries = conn.execute("""
    SELECT 
        country,
        COUNT(*) as count
    FROM events
    GROUP BY country
    ORDER BY count DESC
    LIMIT 15
""").fetchdf()

for _, row in countries.iterrows():
    country = row['country']
    count = row['count']
    print(f"  {country:3s}: {count:4d} événements")

# Par mois
print("\n📆 DISTRIBUTION PAR MOIS (2025):")
print("-" * 80)

months = conn.execute("""
    SELECT 
        date_part('month', ts_utc) as month,
        COUNT(*) as count
    FROM events
    WHERE date_part('year', ts_utc) = 2025
    GROUP BY month
    ORDER BY month
""").fetchdf()

for _, row in months.iterrows():
    month = int(row['month'])
    count = row['count']
    month_name = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                  'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'][month-1]
    print(f"  {month_name}: {count:3d} événements")

# Exemples événements
print("\n📋 EXEMPLES ÉVÉNEMENTS (5 premiers):")
print("-" * 80)

samples = conn.execute("""
    SELECT 
        ts_utc,
        country,
        event_key,
        type,
        actual,
        estimate,
        period
    FROM events
    ORDER BY ts_utc
    LIMIT 5
""").fetchdf()

print(samples.to_string())

# 11 septembre spécifiquement
print("\n🎯 ÉVÉNEMENTS 11 SEPTEMBRE 2025:")
print("-" * 80)

sept11 = conn.execute("""
    SELECT 
        ts_utc,
        country,
        event_key,
        actual,
        estimate
    FROM events
    WHERE ts_utc >= '2025-09-11 14:25:00+02:00'
        AND ts_utc < '2025-09-11 15:00:00+02:00'
    ORDER BY ts_utc
""").fetchdf()

print(f"\nNombre: {len(sept11)}")
if not sept11.empty:
    print(sept11.to_string())
else:
    print("⚠️  AUCUN événement trouvé !")

# Vérifier si importance_n est rempli
print("\n🔍 ANALYSE CHAMP IMPORTANCE:")
print("-" * 80)

imp_stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(importance_n) as with_importance,
        COUNT(*) - COUNT(importance_n) as without_importance
    FROM events
""").fetchdf()

print(imp_stats.to_string())

conn.close()

print("\n" + "=" * 80)
print("DIAGNOSTIC TERMINÉ")
print("=" * 80)

print(f"""
ANALYSE:

Si très peu d'événements (< 2000 pour 3 ans):
  → Le filtre importance=[2,3] est peut-être le problème
  → EODHD ne fournit pas ce champ
  → Réimporter SANS filtre importance

Si événements concentrés sur certains pays:
  → Certains pays ont peu de données EODHD
  → Normal

Si 11 septembre = 0 événements:
  → Problème de timezone ou filtre trop agressif
  → Vérifier déduplication

Si 11 septembre = 10 événements:
  → ✅ Import correct mais volume faible normal avec filtre importance
""")
