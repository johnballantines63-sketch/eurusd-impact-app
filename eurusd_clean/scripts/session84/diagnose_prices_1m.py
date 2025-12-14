"""
Diagnostic table prices_1m pour Session 84
Vérifier schéma et données disponibles
"""
import duckdb
from pathlib import Path

DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

print("="*80)
print("🔍 DIAGNOSTIC TABLE prices_1m")
print("="*80)

conn = duckdb.connect(str(DB_PATH), read_only=True)

# 1. Schéma table
print("\n1️⃣ SCHÉMA TABLE prices_1m :")
print("-"*80)
schema = conn.execute("DESCRIBE prices_1m").df()
print(schema.to_string(index=False))

# 2. Count total
print("\n\n2️⃣ COUNT TOTAL :")
print("-"*80)
count = conn.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
print(f"Total lignes : {count:,}")

# 3. Plage temporelle
print("\n\n3️⃣ PLAGE TEMPORELLE :")
print("-"*80)
time_range = conn.execute("""
    SELECT 
        MIN(datetime) as min_date,
        MAX(datetime) as max_date
    FROM prices_1m
""").fetchone()
print(f"Min : {time_range[0]}")
print(f"Max : {time_range[1]}")

# 4. Sample données 11 septembre 2025
print("\n\n4️⃣ SAMPLE 11 SEPTEMBRE 2025 (14:25-14:35 UTC) :")
print("-"*80)
sample = conn.execute("""
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        volume
    FROM prices_1m
    WHERE datetime >= '2025-09-11 14:25:00'
        AND datetime <= '2025-09-11 14:35:00'
    ORDER BY datetime
""").df()
print(sample.to_string(index=False))

# 5. Check 01 août 2025
print("\n\n5️⃣ SAMPLE 01 AOÛT 2025 (14:25-14:50 UTC) :")
print("-"*80)
sample_aug = conn.execute("""
    SELECT 
        datetime,
        open,
        high,
        low,
        close,
        volume
    FROM prices_1m
    WHERE datetime >= '2025-08-01 14:25:00'
        AND datetime <= '2025-08-01 14:50:00'
    ORDER BY datetime
""").df()
print(sample_aug.to_string(index=False))

# 6. Stats générales
print("\n\n6️⃣ STATS GÉNÉRALES :")
print("-"*80)
stats = conn.execute("""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT DATE(datetime)) as unique_days,
        AVG(high - low) as avg_range,
        MAX(high - low) as max_range
    FROM prices_1m
    WHERE datetime >= '2025-01-01'
""").fetchone()
print(f"Lignes 2025 : {stats[0]:,}")
print(f"Jours uniques 2025 : {stats[1]:,}")
print(f"Range moyen : {stats[2]:.5f}")
print(f"Range max : {stats[3]:.5f}")

conn.close()
print("\n" + "="*80)
print("✅ Diagnostic terminé")
