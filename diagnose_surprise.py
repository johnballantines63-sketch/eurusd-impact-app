#!/usr/bin/env python3
"""Diagnostiquer le problème du surprise_index"""

import duckdb

conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=False)

print("=" * 80)
print("🔍 DIAGNOSTIC SURPRISE INDEX")
print("=" * 80)

# 1. Combien d'événements ont des valeurs actual/forecast ?
query1 = """
SELECT 
    COUNT(*) as total,
    COUNT(actual) as has_actual,
    COUNT(forecast) as has_forecast,
    COUNT(previous) as has_previous,
    SUM(CASE WHEN forecast IS NOT NULL AND forecast != 0 THEN 1 ELSE 0 END) as forecast_usable,
    SUM(CASE WHEN previous IS NOT NULL AND previous != 0 THEN 1 ELSE 0 END) as previous_usable
FROM event_impacts_calculated
"""

result = conn.execute(query1).fetchdf()
print("\n1️⃣ Disponibilité des données:")
print(result.T)

# 2. Distribution des surprise_index
query2 = """
SELECT 
    CASE 
        WHEN actual IS NULL THEN 'actual = NULL'
        WHEN forecast IS NULL OR forecast = 0 THEN 'forecast = NULL/0'
        WHEN ABS((actual - forecast) / forecast) = 0 THEN 'surprise = 0'
        WHEN ABS((actual - forecast) / forecast) < 0.1 THEN 'surprise < 10%'
        WHEN ABS((actual - forecast) / forecast) < 0.5 THEN 'surprise < 50%'
        WHEN ABS((actual - forecast) / forecast) < 1.0 THEN 'surprise < 100%'
        ELSE 'surprise >= 100%'
    END as category,
    COUNT(*) as n_events,
    AVG(mfe_pips) as avg_mfe
FROM event_impacts_calculated
GROUP BY category
ORDER BY category
"""

result2 = conn.execute(query2).fetchdf()
print("\n2️⃣ Distribution des surprises:")
print(result2.to_string(index=False))

# 3. Exemples avec surprise élevé
query3 = """
SELECT 
    strftime(ts_utc, '%Y-%m-%d %H:%M') as datetime,
    event_title,
    actual,
    forecast,
    ABS((actual - forecast) / forecast) as surprise,
    mfe_pips
FROM event_impacts_calculated
WHERE forecast IS NOT NULL 
    AND forecast != 0
    AND ABS((actual - forecast) / forecast) > 0.5
ORDER BY ABS((actual - forecast) / forecast) DESC
LIMIT 10
"""

result3 = conn.execute(query3).fetchdf()
print("\n3️⃣ Top 10 événements avec surprise élevée:")
print(result3.to_string(index=False))

# 4. Corrélation surprise vs MFE pour ceux qui ONT une surprise
query4 = """
SELECT 
    ABS((actual - forecast) / forecast) as surprise,
    mfe_pips
FROM event_impacts_calculated
WHERE forecast IS NOT NULL 
    AND forecast != 0
    AND ABS((actual - forecast) / forecast) > 0
    AND ABS((actual - forecast) / forecast) < 5  -- Filtrer valeurs extrêmes
"""

result4 = conn.execute(query4).fetchdf()
if len(result4) > 10:
    corr = result4[['surprise', 'mfe_pips']].corr().iloc[0, 1]
    print(f"\n4️⃣ Corrélation surprise/MFE (seulement événements avec surprise) : {corr:.3f}")
    print(f"   N = {len(result4)} événements")

conn.close()

print("\n" + "=" * 80)
print("💡 CONCLUSIONS")
print("=" * 80)
