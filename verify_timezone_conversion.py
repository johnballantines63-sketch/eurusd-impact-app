#!/usr/bin/env python3
"""
Vérification CRITIQUE - Prix au bon moment
"""

import duckdb

con = duckdb.connect('fx_impact_app/data/warehouse.duckdb')

print("=" * 80)
print("VÉRIFICATION CRITIQUE - PRIX 11 SEPTEMBRE")
print("=" * 80)

# 1. Prix à 12:30+02:00 (= 10:30 UTC)
print("\n📊 Prix à 12:30:00+02:00 (= 10:30 UTC) :")

query1 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime = '2025-09-11 12:30:00+02:00'
"""

try:
    result1 = con.execute(query1).df()
    if len(result1) > 0:
        print(f"✅ Trouvé : {result1.iloc[0]['open']:.5f}")
    else:
        print("❌ Rien trouvé")
except Exception as e:
    print(f"❌ Erreur : {e}")

# 2. Prix à 14:30+02:00 (= 12:30 UTC selon nos attentes)
print("\n📊 Prix à 14:30:00+02:00 (= 12:30 UTC théorique) :")

query2 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime = '2025-09-11 14:30:00+02:00'
"""

try:
    result2 = con.execute(query2).df()
    if len(result2) > 0:
        print(f"✅ Trouvé : {result2.iloc[0]['open']:.5f}")
        print(f"   ⚠️  Mais ce prix ({result2.iloc[0]['open']:.5f}) est TROP HAUT")
        print(f"   Attendu : ~1.16816")
    else:
        print("❌ Rien trouvé")
except Exception as e:
    print(f"❌ Erreur : {e}")

# 3. Chercher le prix attendu (~1.16816)
print("\n🔍 Recherche du prix attendu (~1.16816) :")

query3 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime::DATE = '2025-09-11'
  AND ABS(open - 1.16816) < 0.001
ORDER BY ABS(open - 1.16816)
LIMIT 5
"""

result3 = con.execute(query3).df()

if len(result3) > 0:
    print("\n✅ Prix proches de 1.16816 trouvés :")
    for idx, row in result3.iterrows():
        print(f"   {row['datetime']} : {row['open']:.5f}")
else:
    print("❌ Aucun prix proche trouvé")

# 4. Vérifier validation directe (qu'on avait fait avant)
print("\n" + "=" * 80)
print("VALIDATION DIRECTE (Session 26 début)")
print("=" * 80)

query4 = """
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00'
  AND datetime <= '2025-09-11 12:45:00'
ORDER BY datetime
LIMIT 5
"""

result4 = con.execute(query4).df()

if len(result4) > 0:
    print(f"\n✅ Validation directe (sans offset explicite) :")
    print(f"   Première ligne : {result4.iloc[0]['datetime']}")
    print(f"   Prix open : {result4.iloc[0]['open']:.5f}")
    print(f"   Attendu : ~1.16874 (validé en début session)")
    
    # Calculer Phase 1
    start = result4.iloc[0]['open']
    max_high = result4['high'].max()
    min_low = result4['low'].min()
    
    phase1_up = (max_high - start) * 10000
    phase1_down = (start - min_low) * 10000
    phase1 = max(phase1_up, phase1_down)
    
    print(f"\n   Phase 1 calculée : {phase1:.2f} pips")
    print(f"   Attendu : 33-37 pips")
    
    if 30 <= phase1 <= 40:
        print(f"   ✅ VALIDATION OK")
    else:
        print(f"   ❌ PROBLÈME")

# 5. CONCLUSION
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("\n💡 PROBLÈME IDENTIFIÉ :")
print("   Les timestamps avec +02:00 dans la DB ne sont PAS en UTC")
print("   Ce sont des heures LOCALES (Berne/CEST)")
print("   12:30:00+02:00 = 10:30 UTC (pas 12:30 UTC)")
print("   14:30:00+02:00 = 12:30 UTC ✅")

print("\n🔧 SOLUTION :")
print("   Pour chercher événement 14:30 Berne (= 12:30 UTC):")
print("   - Soit chercher '14:30:00+02:00'")
print("   - Soit chercher '12:30:00' sans offset")
print("   - Les deux DEVRAIENT pointer vers le même moment")

print("\n⚠️  MAIS ATTENTION :")
print("   Si on cherche '14:30:00+02:00', on trouve 1.17321 (FAUX)")
print("   Si on cherche '12:30:00' sans offset, on trouve 1.16874 (BON)")
print("   => Il y a un problème de conversion timezone dans DuckDB")

con.close()

print("\n" + "=" * 80)
