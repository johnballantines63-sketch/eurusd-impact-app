"""
Script de diagnostic rapide de la structure DB
Session 63 - Identifier colonnes et tables réelles
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))

from config import get_db_path
import duckdb

def main():
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path), read_only=True)
    
    print("=" * 70)
    print("🔍 DIAGNOSTIC STRUCTURE DB")
    print("=" * 70)
    
    # 1. Colonnes table events
    print("\n📋 Colonnes table 'events':")
    cols = conn.execute("DESCRIBE events").fetchdf()
    for _, row in cols.iterrows():
        print(f"   - {row['column_name']}: {row['column_type']}")
    
    # 2. Exemples événements CPI
    print("\n📊 Exemples événements avec 'CPI' dans event_key:")
    query = """
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        actual,
        forecast,
        previous
    FROM events
    WHERE event_key LIKE '%CPI%'
        AND country = 'US'
    ORDER BY ts_utc DESC
    LIMIT 5
    """
    results = conn.execute(query).fetchdf()
    print(results.to_string(index=False))
    
    # 3. Dates CPI disponibles
    print("\n📅 Dates avec événements CPI (US):")
    query = """
    SELECT DISTINCT 
        DATE(ts_utc) as date,
        COUNT(*) as num_events
    FROM events
    WHERE event_key LIKE '%CPI%'
        AND country = 'US'
    GROUP BY DATE(ts_utc)
    ORDER BY date DESC
    LIMIT 10
    """
    dates = conn.execute(query).fetchdf()
    print(dates.to_string(index=False))
    
    # 4. Tables de prix disponibles
    print("\n💹 Tables de prix disponibles:")
    tables = conn.execute("SHOW TABLES").fetchdf()
    price_tables = tables[tables['name'].str.contains('price', case=False)]
    for _, row in price_tables.iterrows():
        table_name = row['name']
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            cols_info = conn.execute(f"DESCRIBE {table_name}").fetchdf()
            col_names = ', '.join(cols_info['column_name'].tolist()[:5])
            print(f"   ✅ {table_name}: {count:,} lignes")
            print(f"      Colonnes: {col_names}...")
        except:
            print(f"   ❌ {table_name}: erreur lecture")
    
    conn.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
