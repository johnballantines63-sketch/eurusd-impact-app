#!/usr/bin/env python3
"""
EXTRACTION SIMPLE - CSV COMPLET 24H AVANT 2025-09-11 14:30
Session 92.9 - Vérification données DB
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Chemins
DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "prices_24h_2025-09-11_COMPLET.csv"

print("="*80)
print("EXTRACTION CSV COMPLET 24H AVANT 2025-09-11 14:30:00")
print("="*80)

# Vérifier DB existe
print(f"\nVérification DB...")
print(f"Chemin : {DB_PATH}")
print(f"Existe : {DB_PATH.exists()}")

if not DB_PATH.exists():
    print(f"\n❌ ERREUR : DB introuvable à {DB_PATH}")
    exit(1)

# Connexion
print(f"\nConnexion DB...")
conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"✅ Connecté")

# Période (timezone +02:00 comme dans DB)
tz_bern = timezone(timedelta(hours=2))
event_time = datetime(2025, 9, 11, 14, 30, 0, tzinfo=tz_bern)
start_time = event_time - timedelta(hours=24)

print(f"\nPériode extraction:")
print(f"  Début : {start_time}")
print(f"  Fin   : {event_time}")

# Extraction
print(f"\nExtraction données...")
query = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= ?
  AND datetime < ?
ORDER BY datetime ASC
"""

df = conn.execute(query, [start_time, event_time]).df()
conn.close()

print(f"✅ {len(df)} lignes extraites")

if len(df) == 0:
    print(f"\n❌ ERREUR : Aucune donnée trouvée !")
    exit(1)

# Sauvegarder CSV IMMÉDIATEMENT
print(f"\nSauvegarde CSV...")
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV sauvegardé : {OUTPUT_CSV}")

# Statistiques simples
print(f"\n" + "="*80)
print(f"STATISTIQUES RAPIDES:")
print(f"="*80)
print(f"Lignes              : {len(df)}")
print(f"High maximum        : {df['high'].max():.5f}")
print(f"Low minimum         : {df['low'].min():.5f}")
print(f"Range               : {(df['high'].max() - df['low'].min()) * 10000:.1f} pips")

# Trouver ligne avec high max
idx_high = df['high'].idxmax()
print(f"\nLigne avec HIGH maximum:")
print(f"  Index    : {idx_high}")
print(f"  Datetime : {df.loc[idx_high, 'datetime']}")
print(f"  High     : {df.loc[idx_high, 'high']:.5f}")
print(f"  Open     : {df.loc[idx_high, 'open']:.5f}")
print(f"  Close    : {df.loc[idx_high, 'close']:.5f}")
print(f"  Low      : {df.loc[idx_high, 'low']:.5f}")

# Chercher 1.17445
print(f"\n" + "="*80)
print(f"RECHERCHE PRIX 1.17445:")
print(f"="*80)
rows_17445 = df[(df['high'] >= 1.17440) & (df['high'] <= 1.17450)]
print(f"Trouvé {len(rows_17445)} ligne(s)")

if len(rows_17445) > 0:
    for idx, row in rows_17445.iterrows():
        print(f"\n  Ligne {idx}:")
        print(f"    Datetime : {row['datetime']}")
        print(f"    Open     : {row['open']:.5f}")
        print(f"    High     : {row['high']:.5f}")
        print(f"    Low      : {row['low']:.5f}")
        print(f"    Close    : {row['close']:.5f}")

# Chercher prix autour de 14:07
print(f"\n" + "="*80)
print(f"PRIX AUTOUR DE 11.09.2025 14:07 (±5 minutes):")
print(f"="*80)

# Convertir datetime en aware pour comparaison
df_copy = df.copy()
check_time = datetime(2025, 9, 11, 14, 7, 0, tzinfo=tz_bern)
start_check = check_time - timedelta(minutes=5)
end_check = check_time + timedelta(minutes=5)

# Filtrer
rows_1407 = df_copy[
    (df_copy['datetime'] >= start_check) & 
    (df_copy['datetime'] <= end_check)
]

print(f"Trouvé {len(rows_1407)} ligne(s) entre 14:02 et 14:12")

if len(rows_1407) > 0:
    print(f"\n{'Datetime':<25} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
    print("-"*80)
    for _, row in rows_1407.iterrows():
        print(f"{str(row['datetime']):<25} {row['open']:>10.5f} {row['high']:>10.5f} {row['low']:>10.5f} {row['close']:>10.5f}")

print(f"\n" + "="*80)
print(f"✅ CSV COMPLET CRÉÉ : {OUTPUT_CSV.name}")
print(f"   Ouvre-le dans Excel/Numbers pour analyse complète")
print(f"="*80)
