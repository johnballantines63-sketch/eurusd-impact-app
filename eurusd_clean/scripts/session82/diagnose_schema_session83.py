import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*80)
print("🔍 DIAGNOSTIC SCHÉMA events")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Schéma table events
print("\n1️⃣ SCHÉMA TABLE events :")
print("-"*80)
schema = conn.execute("DESCRIBE events").df()
print(schema.to_string(index=False))

# 2. Valeurs importance_n
print("\n\n2️⃣ VALEURS UNIQUES importance_n :")
print("-"*80)
imp_values = conn.execute("""
    SELECT DISTINCT importance_n, COUNT(*) as count
    FROM events
    GROUP BY importance_n
    ORDER BY importance_n
""").df()
print(imp_values.to_string(index=False))

# 3. Test avec importance_n = 3
print("\n\n3️⃣ TEST importance_n = 3 :")
print("-"*80)
test_high = conn.execute("""
    SELECT COUNT(*) as count_high
    FROM events
    WHERE importance_n = 3
""").fetchone()
print(f"Événements HIGH (importance_n = 3) : {test_high[0]}")

# 4. Test événements US HIGH
print("\n\n4️⃣ TEST US + HIGH :")
print("-"*80)
test_us_high = conn.execute("""
    SELECT COUNT(*) as count
    FROM events
    WHERE country = 'US' AND importance_n = 3
""").fetchone()
print(f"Événements US HIGH : {test_us_high[0]}")

# 5. Test avec dates 2024-2025
print("\n\n5️⃣ TEST DATES 2024-2025 :")
print("-"*80)
test_dates = conn.execute("""
    SELECT COUNT(*) as count
    FROM events
    WHERE DATE(ts_utc) >= '2024-01-01'
        AND DATE(ts_utc) <= '2025-12-31'
""").fetchone()
print(f"Événements 2024-2025 : {test_dates[0]}")

# 6. Test combinaison complète
print("\n\n6️⃣ TEST COMBINAISON COMPLÈTE (US + HIGH + 2024-2025) :")
print("-"*80)
test_all = conn.execute("""
    SELECT COUNT(*) as count
    FROM events
    WHERE country = 'US' 
        AND importance_n = 3
        AND DATE(ts_utc) >= '2024-01-01'
        AND DATE(ts_utc) <= '2025-12-31'
""").fetchone()
print(f"Événements correspondants : {test_all[0]}")

# 7. Sample événements US
print("\n\n7️⃣ SAMPLE 5 ÉVÉNEMENTS US :")
print("-"*80)
sample = conn.execute("""
    SELECT 
        ts_utc,
        event_title,
        country,
        importance_n
    FROM events
    WHERE country = 'US'
    ORDER BY ts_utc DESC
    LIMIT 5
""").df()
print(sample.to_string(index=False))

conn.close()
print("\n" + "="*80)
