"""
VERSION ULTRA-SIMPLE - Pas besoin de config.py
"""

import duckdb

# Chemin DIRECT vers la DB
db_path = "/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb"

print(f"Connexion à : {db_path}")

try:
    conn = duckdb.connect(db_path, read_only=True)
    print("✅ Connexion réussie !\n")
    
    print("=" * 80)
    print("ÉVÉNEMENTS 11.09.2025 - 13:00 à 15:00 UTC")
    print("=" * 80)
    
    query = """
    SELECT 
        ts_utc,
        event_key,
        country,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
        AND TIME(ts_utc) BETWEEN '13:00:00' AND '15:00:00'
    ORDER BY ts_utc, country
    """
    
    results = conn.execute(query).fetchdf()
    
    print(f"\n✅ {len(results)} événement(s) trouvé(s)\n")
    
    for idx, row in results.iterrows():
        surprise = ""
        if row['actual'] and row['estimate'] and row['estimate'] != 0:
            surprise_pct = abs((row['actual'] - row['estimate']) / row['estimate']) * 100
            surprise = f" | Surprise: {surprise_pct:.1f}%"
        
        print(f"{row['ts_utc']} | {row['country']:3s} | {row['event_key'][:70]}{surprise}")
    
    # Recherche spécifique Current Account
    print("\n" + "=" * 80)
    print("RECHERCHE 'CURRENT' OU 'ACCOUNT'")
    print("=" * 80)
    
    query2 = """
    SELECT 
        ts_utc,
        event_key,
        country,
        actual,
        estimate
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
        AND (LOWER(event_key) LIKE '%current%' OR LOWER(event_key) LIKE '%account%')
    ORDER BY ts_utc
    """
    
    results2 = conn.execute(query2).fetchdf()
    
    if results2.empty:
        print("\n❌ AUCUN événement 'current' ou 'account' trouvé pour le 11.09.2025")
    else:
        print(f"\n✅ {len(results2)} événement(s) trouvé(s) :\n")
        for _, row in results2.iterrows():
            print(f"\n{row['ts_utc']} | {row['country']} | {row['event_key']}")
            print(f"  Actual: {row['actual']} | Estimate: {row['estimate']}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()
