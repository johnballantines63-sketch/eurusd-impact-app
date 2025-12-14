#!/usr/bin/env python3
"""
CRÉATION VUE PRICES_BERN - Solution définitive timezone
========================================================

Crée une vue qui affiche les prix à l'heure Bern (réelle).

AVANT:
- Event: 14:30 Bern
- Prix: chercher à 12:30 dans prices_1m (décalé -2h)

APRÈS:
- Event: 14:30 Bern  
- Prix: chercher à 14:30 dans prices_bern (direct!)

LOGIQUE PURE = Plus jamais de confusion!

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 1
"""

import duckdb
from pathlib import Path

print("="*80)
print("🔧 CRÉATION VUE PRICES_BERN")
print("="*80)

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

if not db_path.exists():
    print(f"\n❌ DB introuvable: {db_path}")
    exit(1)

con = duckdb.connect(str(db_path), read_only=False)

# ══════════════════════════════════════════════════════════════════════
# VÉRIFIER SI VUE EXISTE DÉJÀ
# ══════════════════════════════════════════════════════════════════════

print("\n📊 Vérification...")

try:
    existing = con.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'prices_bern'
    """).fetchone()[0]
    
    if existing > 0:
        print(f"\n⚠️ Vue 'prices_bern' existe déjà")
        choice = input("   Supprimer et recréer ? (oui/non): ").strip().lower()
        
        if choice == "oui":
            con.execute("DROP VIEW IF EXISTS prices_bern")
            print(f"   ✅ Ancienne vue supprimée")
        else:
            print(f"\n❌ Opération annulée")
            con.close()
            exit(0)
except:
    # Table information_schema peut ne pas exister, on continue
    pass

# ══════════════════════════════════════════════════════════════════════
# CRÉER LA VUE
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🚀 CRÉATION DE LA VUE")
print("="*80)

try:
    con.execute("""
        CREATE VIEW prices_bern AS
        SELECT 
            datetime + INTERVAL '2 hours' as datetime,
            open,
            high,
            low,
            close,
            volume
        FROM prices_1m
    """)
    
    print(f"\n✅ VUE CRÉÉE !")
    print(f"   Nom: prices_bern")
    print(f"   Transformation: datetime + 2 heures")
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    con.close()
    exit(1)

# ══════════════════════════════════════════════════════════════════════
# VÉRIFICATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("✅ VÉRIFICATION")
print("="*80)

# 1. Compter lignes
count_original = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
count_vue = con.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]

print(f"\n📊 Nombre de lignes:")
print(f"   prices_1m:   {count_original:,}")
print(f"   prices_bern: {count_vue:,}")

if count_original == count_vue:
    print(f"   ✅ Même nombre de lignes")
else:
    print(f"   ⚠️ Différence détectée !")

# 2. Tester cas de référence (11 sept)
print(f"\n🔍 Test cas de référence (11 sept 2025):")

# Prix original à 12:30
original = con.execute("""
    SELECT datetime, open
    FROM prices_1m
    WHERE datetime >= '2025-09-11 12:30:00'
    AND datetime < '2025-09-11 12:31:00'
    LIMIT 1
""").fetchone()

print(f"\n   prices_1m (original):")
print(f"     Timestamp: {original[0]}")
print(f"     Open: {original[1]:.5f}")

# Prix dans vue à 14:30 (doit être le même)
vue = con.execute("""
    SELECT datetime, open
    FROM prices_bern
    WHERE datetime >= '2025-09-11 14:30:00'
    AND datetime < '2025-09-11 14:31:00'
    LIMIT 1
""").fetchone()

print(f"\n   prices_bern (vue +2h):")
print(f"     Timestamp: {vue[0]}")
print(f"     Open: {vue[1]:.5f}")

# Vérifier que c'est le même prix
if abs(original[1] - vue[1]) < 0.00001:
    print(f"\n   🎉 PARFAIT ! Même prix, timestamp +2h !")
    print(f"   ✅ Prix 12:30 dans prices_1m = Prix 14:30 dans prices_bern")
else:
    print(f"\n   ⚠️ Prix différents !")

# 3. Vérifier event aligné
event = con.execute("""
    SELECT ts_utc
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    AND event_title LIKE '%CPI%'
    LIMIT 1
""").fetchone()

print(f"\n🎯 Alignement Event/Prix:")
print(f"   Event: {event[0]}")
print(f"   Prix (vue): {vue[0]}")

event_time = str(event[0]).split('+')[0].split('.')[0]
prix_time = str(vue[0]).split('+')[0].split('.')[0]

if event_time == prix_time:
    print(f"\n   🎉🎉🎉 ALIGNEMENT PARFAIT !")
    print(f"   Event 14:30 = Prix 14:30 dans prices_bern")
    print(f"   ✅ LOGIQUE PURE RÉALISÉE !")
else:
    print(f"\n   ⚠️ Décalage détecté")

con.close()

print("\n" + "="*80)
print("✅ VUE PRICES_BERN CRÉÉE AVEC SUCCÈS")
print("="*80)

print(f"\n📋 PROCHAINES ÉTAPES:")
print(f"  1. Tester la vue avec impact_measurement")
print(f"  2. Mettre à jour tous les scripts")
print(f"  3. Documenter la nouvelle structure")

print(f"\n💡 UTILISATION:")
print(f"  # Ancienne façon (NE PLUS UTILISER)")
print(f"  SELECT * FROM prices_1m WHERE datetime = '2025-09-11 12:30:00'")
print(f"  ")
print(f"  # Nouvelle façon (TOUJOURS UTILISER)")
print(f"  SELECT * FROM prices_bern WHERE datetime = '2025-09-11 14:30:00'")
