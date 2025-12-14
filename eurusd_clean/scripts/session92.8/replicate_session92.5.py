#!/usr/bin/env python3
"""
RÉPLICATION EXACTE SESSION 92.5
Extract 11.09.2025 14:20-15:30 (70 minutes)
Comparaison avec résultats Session 92.5
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Chemins
DB_PATH = Path(__file__).parent.parent.parent.parent / "fx_impact_app" / "data" / "warehouse.duckdb"
OUTPUT_CSV = Path(__file__).parent / "replication_session92.5_11sept.csv"

print("="*80)
print("RÉPLICATION SESSION 92.5 - 11.09.2025 14:20-15:30")
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

# Période EXACTE Session 92.5 (timezone +02:00)
tz_bern = timezone(timedelta(hours=2))
start_time = datetime(2025, 9, 11, 14, 20, 0, tzinfo=tz_bern)
end_time = datetime(2025, 9, 11, 15, 30, 0, tzinfo=tz_bern)

print(f"\nPériode extraction:")
print(f"  Début : {start_time}")
print(f"  Fin   : {end_time}")
print(f"  Durée : 70 minutes (comme Session 92.5)")

# Extraction (query simple comme Session 92.5)
query = """
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime >= ?
  AND datetime <= ?
ORDER BY datetime ASC
"""

df = conn.execute(query, [start_time, end_time]).df()
conn.close()

print(f"\n✅ Lignes extraites : {len(df)}")
print(f"   Attendu Session 92.5 : 71 lignes")

if len(df) == 0:
    print(f"\n❌ ERREUR : Aucune donnée trouvée !")
    exit(1)

# Sauvegarder CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV sauvegardé : {OUTPUT_CSV}")

# Comparaison avec résultats Session 92.5
print(f"\n" + "="*80)
print(f"COMPARAISON AVEC SESSION 92.5:")
print(f"="*80)

# Chercher ligne 14:30 (CPI)
row_1430 = df[df['datetime'] == datetime(2025, 9, 11, 14, 30, 0, tzinfo=tz_bern)]

if len(row_1430) > 0:
    row = row_1430.iloc[0]
    print(f"\n📊 LIGNE 14:30:00 (CPI):")
    print(f"  Open  : {row['open']:.5f}")
    print(f"  High  : {row['high']:.5f}")
    print(f"  Low   : {row['low']:.5f}")
    print(f"  Close : {row['close']:.5f}")
    
    print(f"\n🔍 COMPARAISON SESSION 92.5:")
    print(f"  HIGH DB   : {row['high']:.5f}")
    print(f"  HIGH S92.5: 1.17100")
    print(f"  Écart     : {abs(row['high'] - 1.17100) * 10000:.1f} pips")
    
    print(f"\n  LOW DB    : {row['low']:.5f}")
    print(f"  LOW S92.5 : 1.16615")
    print(f"  Écart     : {abs(row['low'] - 1.16615) * 10000:.1f} pips")
else:
    print(f"\n❌ Ligne 14:30:00 introuvable !")

# Chercher peak 15:09
row_1509 = df[df['datetime'] == datetime(2025, 9, 11, 15, 9, 0, tzinfo=tz_bern)]

if len(row_1509) > 0:
    row = row_1509.iloc[0]
    print(f"\n📊 LIGNE 15:09:00 (Peak):")
    print(f"  Open  : {row['open']:.5f}")
    print(f"  High  : {row['high']:.5f}")
    print(f"  Low   : {row['low']:.5f}")
    print(f"  Close : {row['close']:.5f}")
    
    print(f"\n🔍 COMPARAISON SESSION 92.5:")
    print(f"  HIGH DB   : {row['high']:.5f}")
    print(f"  HIGH S92.5: 1.17391")
    print(f"  Écart     : {abs(row['high'] - 1.17391) * 10000:.1f} pips")
else:
    print(f"\n❌ Ligne 15:09:00 introuvable !")

# Trouver high maximum période
idx_max = df['high'].idxmax()
row_max = df.loc[idx_max]

print(f"\n📊 HIGH MAXIMUM PÉRIODE:")
print(f"  Datetime : {row_max['datetime']}")
print(f"  High     : {row_max['high']:.5f}")
print(f"  Attendu S92.5 : 15:09 à 1.17391")

# Afficher premières lignes
print(f"\n" + "="*80)
print(f"PREMIÈRES LIGNES (14:20-14:30):")
print(f"="*80)
print(f"\n{'Datetime':<25} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
print("-"*80)

for _, row in df.head(11).iterrows():
    print(f"{str(row['datetime']):<25} {row['open']:>10.5f} {row['high']:>10.5f} {row['low']:>10.5f} {row['close']:>10.5f}")

# Verdict final
print(f"\n" + "="*80)
print(f"VERDICT:")
print(f"="*80)

# Vérifier si on a les mêmes valeurs que Session 92.5
if len(row_1430) > 0:
    high_1430 = row_1430.iloc[0]['high']
    low_1430 = row_1430.iloc[0]['low']
    
    ecart_high = abs(high_1430 - 1.17100) * 10000
    ecart_low = abs(low_1430 - 1.16615) * 10000
    
    if ecart_high < 2.0 and ecart_low < 2.0:
        print(f"✅ DONNÉES IDENTIQUES Session 92.5")
        print(f"   → DB warehouse.duckdb est CORRECTE")
        print(f"   → Le problème est dans les AUTRES scripts")
    else:
        print(f"❌ DONNÉES DIFFÉRENTES Session 92.5")
        print(f"   Écart HIGH : {ecart_high:.1f} pips")
        print(f"   Écart LOW  : {ecart_low:.1f} pips")
        print(f"   → DB a peut-être changé depuis Session 92.5")

print(f"\n✅ CSV complet : {OUTPUT_CSV.name}")
print(f"="*80)
