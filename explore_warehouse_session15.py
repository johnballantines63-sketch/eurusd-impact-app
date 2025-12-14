"""
EXPLORATION warehouse.duckdb - Session 15
Vérification structure avant extraction données
"""

import duckdb
import pandas as pd

# Connexion
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("="*80)
print("📊 EXPLORATION warehouse.duckdb - SESSION 15")
print("="*80)

# 1. Lister les tables
print("\n" + "─"*80)
print("1. TABLES DISPONIBLES")
print("─"*80)

tables = conn.execute("""
    SELECT table_name, 
           (SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = t.table_name) as nb_colonnes
    FROM information_schema.tables t
    WHERE table_schema = 'main'
    ORDER BY table_name
""").fetchdf()

print(tables.to_string(index=False))

# 2. Structure table events (notre source principale)
print("\n" + "─"*80)
print("2. STRUCTURE TABLE 'events'")
print("─"*80)

events_columns = conn.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'events'
    ORDER BY ordinal_position
""").fetchdf()

print(events_columns.to_string(index=False))

# 3. Compter événements par année
print("\n" + "─"*80)
print("3. ÉVÉNEMENTS PAR ANNÉE")
print("─"*80)

events_by_year = conn.execute("""
    SELECT 
        EXTRACT(YEAR FROM ts_utc) as annee,
        COUNT(*) as nb_events,
        COUNT(DISTINCT event_title) as nb_types_uniques
    FROM events
    GROUP BY annee
    ORDER BY annee DESC
""").fetchdf()

print(events_by_year.to_string(index=False))

# 4. Vérifier colonnes critiques (estimate vs forecast)
print("\n" + "─"*80)
print("4. VÉRIFICATION estimate VS forecast")
print("─"*80)

estimate_check = conn.execute("""
    SELECT 
        COUNT(*) as total_events,
        COUNT(estimate) as estimate_non_null,
        COUNT(forecast) as forecast_non_null,
        ROUND(COUNT(estimate) * 100.0 / COUNT(*), 2) as pct_estimate,
        ROUND(COUNT(forecast) * 100.0 / COUNT(*), 2) as pct_forecast
    FROM events
""").fetchdf()

print(estimate_check.to_string(index=False))

# 5. Distributions des surprises
print("\n" + "─"*80)
print("5. DISTRIBUTION DES SURPRISES (avec estimate)")
print("─"*80)

surprise_dist = conn.execute("""
    WITH surprises AS (
        SELECT 
            CASE 
                WHEN estimate IS NOT NULL AND estimate != 0 
                THEN ABS((actual - estimate) / estimate) * 100
                ELSE NULL
            END as surprise_pct
        FROM events
        WHERE actual IS NOT NULL
    )
    SELECT 
        CASE 
            WHEN surprise_pct < 5 THEN '0-5%'
            WHEN surprise_pct < 10 THEN '5-10%'
            WHEN surprise_pct < 20 THEN '10-20%'
            WHEN surprise_pct < 50 THEN '20-50%'
            ELSE '>50%'
        END as tranche_surprise,
        COUNT(*) as nb_events
    FROM surprises
    WHERE surprise_pct IS NOT NULL
    GROUP BY tranche_surprise
    ORDER BY 
        CASE tranche_surprise
            WHEN '0-5%' THEN 1
            WHEN '5-10%' THEN 2
            WHEN '10-20%' THEN 3
            WHEN '20-50%' THEN 4
            ELSE 5
        END
""").fetchdf()

print(surprise_dist.to_string(index=False))

# 6. Top événements avec surprises extrêmes (> 10%)
print("\n" + "─"*80)
print("6. ÉCHANTILLON ÉVÉNEMENTS SURPRISES > 10%")
print("─"*80)

extreme_events = conn.execute("""
    SELECT 
        e.ts_utc,
        e.event_title,
        e.actual,
        e.estimate,
        ROUND(ABS((e.actual - e.estimate) / e.estimate) * 100, 2) as surprise_pct,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.estimate IS NOT NULL 
      AND e.estimate != 0
      AND ABS((e.actual - e.estimate) / e.estimate) * 100 > 10
    ORDER BY ABS((e.actual - e.estimate) / e.estimate) DESC
    LIMIT 10
""").fetchdf()

print(extreme_events.to_string(index=False))

print("\n" + "="*80)
print("✅ EXPLORATION TERMINÉE")
print("="*80)

conn.close()
