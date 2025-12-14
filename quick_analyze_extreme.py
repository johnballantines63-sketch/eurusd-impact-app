import duckdb
import pandas as pd

# Connexion à la base
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=True)

print("\n" + "=" * 100)
print("🔍 ANALYSE DES ÉVÉNEMENTS EXTRÊMES (Surprise > 5%)")
print("=" * 100)

# Requête pour événements extrêmes (sans la colonne family)
query = """
SELECT 
    event_title,
    event_key,
    ts_utc,
    country,
    actual,
    estimate,
    previous,
    unit,
    importance_n,
    (actual - estimate) AS surprise_abs,
    ABS((actual - estimate) / NULLIF(estimate, 0) * 100) as surprise_pct
FROM events
WHERE estimate IS NOT NULL
  AND estimate != 0
  AND ABS((actual - estimate) / NULLIF(estimate, 0) * 100) > 5.0
  AND country = 'US'
  AND ts_utc >= '2024-01-01'
ORDER BY surprise_pct DESC
LIMIT 30;
"""

try:
    df = conn.execute(query).fetchdf()
    
    print(f"\n✅ Trouvé {len(df)} événements extrêmes (surprise > 5%)")
    print()
    print("📋 TOP 30 ÉVÉNEMENTS PAR SURPRISE :")
    print("-" * 100)
    print(f"{'#':3s} | {'Événement':45s} | {'Date':16s} | {'Forecast':>10s} | {'Actual':>10s} | {'Surprise':>8s}")
    print("-" * 100)
    
    for idx, row in df.iterrows():
        print(f"{idx+1:3d} | {row['event_title'][:45]:45s} | {str(row['ts_utc'])[:16]:16s} | "
              f"{row['estimate']:>10.2f} | {row['actual']:>10.2f} | {row['surprise_pct']:>7.1f}%")
    
    # Distribution par tranche
    print("\n📊 DISTRIBUTION PAR TRANCHE DE SURPRISE :")
    print("-" * 100)
    tranche_5_10 = len(df[(df['surprise_pct'] >= 5) & (df['surprise_pct'] < 10)])
    tranche_10_20 = len(df[(df['surprise_pct'] >= 10) & (df['surprise_pct'] < 20)])
    tranche_20_50 = len(df[(df['surprise_pct'] >= 20) & (df['surprise_pct'] < 50)])
    tranche_50_plus = len(df[df['surprise_pct'] >= 50])
    
    print(f"  🟢 5-10%    : {tranche_5_10:3d} événements (amplification modérée)")
    print(f"  🟡 10-20%   : {tranche_10_20:3d} événements (amplification forte)")
    print(f"  🟠 20-50%   : {tranche_20_50:3d} événements (amplification très forte)")
    print(f"  🔴 > 50%    : {tranche_50_plus:3d} événements (amplification extrême)")
    
    # Recherche cas 11 septembre 2025
    print("\n🎯 RECHERCHE CAS 11 SEPTEMBRE 2025 :")
    print("-" * 100)
    cas_sept = df[
        (df['ts_utc'].astype(str).str.contains('2025-09-11')) &
        (df['event_title'].str.contains('Jobless', case=False))
    ]
    
    if len(cas_sept) > 0:
        print("✅ Cas 11 septembre trouvé !")
        for idx, row in cas_sept.iterrows():
            print(f"  • {row['event_title']}")
            print(f"    Date: {row['ts_utc']}")
            print(f"    Forecast: {row['estimate']:.0f}, Actual: {row['actual']:.0f}")
            print(f"    Surprise: {row['surprise_pct']:.1f}%")
    else:
        print("⚠️ Cas 11 septembre non trouvé dans ces résultats")
        print("   Vérifions avec une requête spécifique...")
        
        query_sept = """
        SELECT 
            event_title,
            ts_utc,
            actual,
            estimate,
            ABS((actual - estimate) / NULLIF(estimate, 0) * 100) as surprise_pct
        FROM events
        WHERE ts_utc >= '2025-09-11 14:00:00'
          AND ts_utc <= '2025-09-11 15:00:00'
          AND country = 'US'
          AND estimate IS NOT NULL
        ORDER BY surprise_pct DESC;
        """
        
        df_sept = conn.execute(query_sept).fetchdf()
        if len(df_sept) > 0:
            print(f"\n  Trouvé {len(df_sept)} événements le 11 septembre 2025 à 14h:")
            for idx, row in df_sept.iterrows():
                print(f"    {row['event_title']:50s} | Surprise: {row['surprise_pct']:.1f}%")
    
    # Distribution par type d'événement (basé sur event_title)
    print("\n📊 TOP 10 TYPES D'ÉVÉNEMENTS (par event_key) :")
    print("-" * 100)
    
    event_counts = df['event_key'].value_counts().head(10)
    for event_key, count in event_counts.items():
        pct = count / len(df) * 100
        print(f"  {event_key[:60]:60s} : {count:2d} fois ({pct:4.1f}%)")
    
    # Sauvegarder pour référence
    output_file = "validation_extreme_events.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Dataset sauvegardé : {output_file}")
    
    print("\n" + "=" * 100)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 100)
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()

conn.close()
