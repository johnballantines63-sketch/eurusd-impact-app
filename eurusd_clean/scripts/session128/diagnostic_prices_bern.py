"""
DIAGNOSTIC URGENT : TABLE prices_bern
=====================================

Vérifier si données prix 1er août 2025 complètes.
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
conn = duckdb.connect(str(DB_PATH), read_only=True)

print("="*80)
print("DIAGNOSTIC TABLE prices_bern - 1er AOÛT 2025")
print("="*80)
print()

# Test 1 : Table existe ?
print("TEST 1 : Table prices_bern existe ?")
print("-"*80)
try:
    result = conn.execute("SELECT COUNT(*) FROM prices_bern").fetchone()
    print(f"✅ Table existe : {result[0]:,} lignes")
except:
    print("❌ Table prices_bern introuvable !")
    conn.close()
    exit(1)

print()

# Test 2 : Plage dates complète
print("TEST 2 : Plage dates dans prices_bern")
print("-"*80)
result = conn.execute("""
    SELECT 
        MIN(datetime) as min_date,
        MAX(datetime) as max_date
    FROM prices_bern
""").fetchone()
print(f"Date min : {result[0]}")
print(f"Date max : {result[1]}")
print()

# Test 3 : Données 1er août 2025
print("TEST 3 : Données 1er août 2025")
print("-"*80)
result = conn.execute("""
    SELECT COUNT(*)
    FROM prices_bern
    WHERE DATE(datetime) = '2025-08-01'
""").fetchone()
print(f"Points 1er août 2025 : {result[0]:,}")
print()

if result[0] == 0:
    print("❌ AUCUNE DONNÉE 1er août 2025 !")
    conn.close()
    exit(1)

# Test 4 : Données AVANT 14h30
print("TEST 4 : Données AVANT 14h30 (cluster NFP)")
print("-"*80)
result = conn.execute("""
    SELECT COUNT(*)
    FROM prices_bern
    WHERE datetime >= '2025-08-01 00:00:00+02:00'
      AND datetime < '2025-08-01 14:30:00+02:00'
""").fetchone()
print(f"Points avant 14h30 : {result[0]:,}")
print()

if result[0] == 0:
    print("❌ AUCUNE DONNÉE AVANT 14h30 !")
    print("   → Explique pourquoi baseline fausse")
    print()

# Test 5 : Prix autour 14h30
print("TEST 5 : Prix autour 14h30 (±1h)")
print("-"*80)
df = conn.execute("""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime >= '2025-08-01 13:30:00+02:00'
      AND datetime <= '2025-08-01 15:30:00+02:00'
    ORDER BY datetime
""").fetchdf()

print(f"Points récupérés : {len(df)}")
print()

if len(df) > 0:
    print("Premiers prix :")
    print(df.head(10).to_string(index=False))
    print()
    print("Derniers prix :")
    print(df.tail(10).to_string(index=False))
    print()
    
    # Prix min/max
    min_price = df['close'].min()
    max_price = df['close'].max()
    range_pips = (max_price - min_price) * 10000
    
    print(f"📊 Résumé fenêtre 13h30-15h30 :")
    print(f"   Prix min : {min_price:.5f}")
    print(f"   Prix max : {max_price:.5f}")
    print(f"   Range : {range_pips:.1f} pips")
else:
    print("❌ AUCUNE DONNÉE autour 14h30")

print()

# Test 6 : Prix juste AVANT 14h30
print("TEST 6 : Dernier prix AVANT 14h30:00")
print("-"*80)
result = conn.execute("""
    SELECT datetime, close
    FROM prices_bern
    WHERE datetime < '2025-08-01 14:30:00+02:00'
    ORDER BY datetime DESC
    LIMIT 5
""").fetchall()

if result:
    print("5 derniers prix avant 14h30 :")
    for dt, price in result:
        print(f"   {dt} : {price:.5f}")
    print()
    print(f"→ Baseline devrait être : {result[0][1]:.5f}")
else:
    print("❌ Aucun prix avant 14h30 !")

print()

# Test 7 : Vérifier 11 septembre (référence validée)
print("TEST 7 : Données 11 septembre 2025 (référence)")
print("-"*80)
result = conn.execute("""
    SELECT COUNT(*)
    FROM prices_bern
    WHERE DATE(datetime) = '2025-09-11'
""").fetchone()
print(f"Points 11 septembre : {result[0]:,}")

if result[0] > 0:
    result2 = conn.execute("""
        SELECT COUNT(*)
        FROM prices_bern
        WHERE datetime >= '2025-09-11 00:00:00+02:00'
          AND datetime < '2025-09-11 14:30:00+02:00'
    """).fetchone()
    print(f"Points avant 14h30 : {result2[0]:,}")
    print()
    
    # VÉRIFICATION CRITIQUE : Prix réels vs prices_bern
    print("   🔍 VÉRIFICATION PRIX 11 SEPTEMBRE :")
    print("   " + "-"*76)
    
    # Récupérer prix autour 14:30
    df_sept = conn.execute("""
        SELECT datetime, close, high, low
        FROM prices_bern
        WHERE datetime >= '2025-09-11 14:25:00+02:00'
          AND datetime <= '2025-09-11 15:30:00+02:00'
        ORDER BY datetime
    """).fetchdf()
    
    if len(df_sept) > 10:
        # Baseline avant cluster
        baseline_sept = conn.execute("""
            SELECT close
            FROM prices_bern
            WHERE datetime < '2025-09-11 14:30:00+02:00'
            ORDER BY datetime DESC
            LIMIT 1
        """).fetchone()[0]
        
        # Max mouvement après 14:30
        after_sept = df_sept[df_sept['datetime'] >= '2025-09-11 14:30:00+02:00']
        max_high_sept = after_sept['high'].max()
        min_low_sept = after_sept['low'].min()
        
        impact_up_sept = (max_high_sept - baseline_sept) * 10000
        impact_down_sept = (baseline_sept - min_low_sept) * 10000
        impact_measured_sept = max(impact_up_sept, impact_down_sept)
        
        print(f"   Baseline : {baseline_sept:.5f}")
        print(f"   Max high : {max_high_sept:.5f} (+{impact_up_sept:.1f} pips)")
        print(f"   Min low  : {min_low_sept:.5f} (-{impact_down_sept:.1f} pips)")
        print(f"   Impact mesuré : {impact_measured_sept:.1f} pips")
        print()
        print(f"   ✅ ATTENDU (Session 115) : ~56-60 pips")
        
        # Vérifier cohérence
        if 50 <= impact_measured_sept <= 70:
            print(f"   ✅✅ COHÉRENT ! Données prices_bern valides")
        else:
            print(f"   ❌❌ INCOHÉRENT ! Données prices_bern suspectes")
            print(f"   → Validation croisée NFP INVALIDE !")
    else:
        print("   ❌ Pas assez de données 11 septembre")
else:
    print("   ❌ Aucune donnée 11 septembre !")

print()

conn.close()

print("="*80)
print("FIN DIAGNOSTIC")
print("="*80)
