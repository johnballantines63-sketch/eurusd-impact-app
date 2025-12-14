#!/usr/bin/env python3
"""
RÉPLICATION EXACTE SESSION 92.5 - AVEC BONS TIMESTAMPS
Extract 11.09.2025 12:20-13:30 +02:00 (pas 14:20-15:30 !)
"""

import duckdb
import pandas as pd
from pathlib import Path

# Chemins
DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "replication_session92.5_CORRECT.csv"

print("="*80)
print("RÉPLICATION SESSION 92.5 - TIMESTAMPS CORRECTS")
print("="*80)

# Vérifier DB
print(f"\nChemin DB : {DB_PATH}")
print(f"Existe    : {DB_PATH.exists()}")

if not DB_PATH.exists():
    print(f"\n❌ ERREUR : DB introuvable")
    exit(1)

# Connexion
conn = duckdb.connect(str(DB_PATH), read_only=True)
print(f"✅ DB connectée")

# Query EXACTE Session 92.5 (timestamps en string)
query = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:20:00+02:00'::TIMESTAMP
  AND datetime <= '2025-09-11 13:30:00+02:00'::TIMESTAMP
ORDER BY datetime
"""

print(f"\nQuery SQL:")
print(query)

df = conn.execute(query).df()
conn.close()

print(f"\n✅ Lignes extraites : {len(df)}")
print(f"   Attendu Session 92.5 : 71 lignes")

if len(df) == 0:
    print(f"\n❌ ERREUR : Aucune donnée trouvée !")
    exit(1)

# Sauvegarder CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV sauvegardé : {OUTPUT_CSV}")

# Chercher ligne 14:30 Bern (12:30:00+02:00 dans DB)
print(f"\n" + "="*80)
print(f"COMPARAISON AVEC SESSION 92.5:")
print(f"="*80)

# La ligne CPI est à 12:30:00+02:00 (= 14:30 Bern time)
row_1430 = df[df['datetime'].astype(str).str.contains('12:30:00')]

if len(row_1430) > 0:
    row = row_1430.iloc[0]
    print(f"\n📊 LIGNE 14:30 BERN (12:30:00+02:00 dans DB):")
    print(f"  Datetime : {row['datetime']}")
    print(f"  Open     : {row['open']:.5f}")
    print(f"  High     : {row['high']:.5f}")
    print(f"  Low      : {row['low']:.5f}")
    print(f"  Close    : {row['close']:.5f}")
    
    print(f"\n🔍 COMPARAISON SESSION 92.5:")
    print(f"  HIGH DB    : {row['high']:.5f}")
    print(f"  HIGH S92.5 : 1.17100")
    print(f"  Écart      : {abs(row['high'] - 1.17100) * 10000:.2f} pips")
    
    print(f"\n  LOW DB     : {row['low']:.5f}")
    print(f"  LOW S92.5  : 1.16615")
    print(f"  Écart      : {abs(row['low'] - 1.16615) * 10000:.2f} pips")
    
    # Verdict
    ecart_high = abs(row['high'] - 1.17100) * 10000
    ecart_low = abs(row['low'] - 1.16615) * 10000
    
    print(f"\n" + "="*80)
    print(f"VERDICT:")
    print(f"="*80)
    
    if ecart_high < 2.0 and ecart_low < 2.0:
        print(f"✅✅✅ DONNÉES IDENTIQUES Session 92.5 !")
        print(f"   → DB warehouse.duckdb est CORRECTE")
        print(f"   → MES AUTRES SCRIPTS utilisaient MAUVAIS TIMESTAMPS")
    else:
        print(f"❌ DONNÉES DIFFÉRENTES")
        print(f"   Écart HIGH : {ecart_high:.2f} pips")
        print(f"   Écart LOW  : {ecart_low:.2f} pips")
else:
    print(f"\n❌ Ligne 12:30:00+02:00 introuvable !")

# Peak 15:09 Bern (13:09:00+02:00 dans DB)
row_1509 = df[df['datetime'].astype(str).str.contains('13:09:00')]

if len(row_1509) > 0:
    row = row_1509.iloc[0]
    print(f"\n📊 LIGNE 15:09 BERN (13:09:00+02:00 dans DB):")
    print(f"  Datetime : {row['datetime']}")
    print(f"  High     : {row['high']:.5f}")
    
    print(f"\n🔍 COMPARAISON SESSION 92.5:")
    print(f"  HIGH DB    : {row['high']:.5f}")
    print(f"  HIGH S92.5 : 1.17391")
    print(f"  Écart      : {abs(row['high'] - 1.17391) * 10000:.2f} pips")

print(f"\n✅ CSV : {OUTPUT_CSV.name}")
print(f"="*80)
