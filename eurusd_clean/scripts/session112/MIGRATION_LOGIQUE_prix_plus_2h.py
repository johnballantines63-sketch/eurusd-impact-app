#!/usr/bin/env python3
"""
MIGRATION LOGIQUE - Ajouter 2h aux PRIX
========================================

OBJECTIF: Aligner les prix sur l'heure réelle

SITUATION:
- Event CPI: 14:30 Bern (correct ✅)
- Prix impact: stocké à 12:30 (décalé de -2h ❌)

SOLUTION LOGIQUE:
- Ajouter 2h à TOUS les prix
- Prix 12:30 → devient 14:30 ✅
- Maintenant: Event 14:30 = Prix 14:30 = Logique pure!

IMPACT:
- Modifie toute la table prices_1m
- Peut prendre 1-2 minutes
- Backup OBLIGATOIRE

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 1
"""

import duckdb
from pathlib import Path
import time

print("="*80)
print("🔧 MIGRATION LOGIQUE - AJOUTER 2H AUX PRIX")
print("="*80)

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

# ══════════════════════════════════════════════════════════════════════
# VÉRIFICATION BACKUP
# ══════════════════════════════════════════════════════════════════════

backup_dir = db_path.parent / "backups"
backups = sorted(backup_dir.glob("warehouse_AVANT_MIGRATION_*.duckdb"))

if not backups:
    print("\n❌ ERREUR: Aucun backup trouvé !")
    print("   Lance d'abord: STEP1_backup_avant_migration.py")
    exit(1)

last_backup = backups[-1]
backup_age = (time.time() - last_backup.stat().st_mtime) / 60

print(f"\n✅ Backup trouvé:")
print(f"   Fichier: {last_backup.name}")
print(f"   Âge: {backup_age:.1f} minutes")

if backup_age > 30:
    print(f"\n⚠️ ATTENTION: Backup > 30 minutes")
    proceed = input("   Continuer quand même ? (oui/non): ").strip().lower()
    if proceed != "oui":
        print("\n❌ Migration annulée")
        exit(0)

# ══════════════════════════════════════════════════════════════════════
# ANALYSE PRÉ-MIGRATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ANALYSE PRÉ-MIGRATION")
print("="*80)

con = duckdb.connect(str(db_path), read_only=True)

# Compter prix
count = con.execute("SELECT COUNT(*) FROM prices_1m").fetchone()[0]
print(f"\n📊 {count:,} prix à migrer")

# Exemple prix avant
sample = con.execute("""
    SELECT datetime, open 
    FROM prices_1m 
    WHERE datetime >= '2025-09-11 12:30:00'
    AND datetime < '2025-09-11 12:31:00'
    LIMIT 1
""").fetchone()

print(f"\n💹 Exemple AVANT migration:")
print(f"   Timestamp: {sample[0]}")
print(f"   Open: {sample[1]:.5f}")
print(f"   → Deviendra: 2025-09-11 14:30:00+02:00 (+ 2h)")

con.close()

# ══════════════════════════════════════════════════════════════════════
# CONFIRMATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("⚠️ CONFIRMATION MIGRATION")
print("="*80)

print(f"\nCette migration va:")
print(f"  ✅ Ajouter 2h à {count:,} prix")
print(f"  ✅ Aligner prix avec events (logique pure)")
print(f"  ⚠️ Modifier toute la table prices_1m")
print(f"  ⚠️ Durée estimée: 1-2 minutes")

print(f"\nAprès migration:")
print(f"  - Event 14:30 → Prix 14:30 (direct)")
print(f"  - Plus besoin de règle -2h")
print(f"  - Logique unifiée pour tous scripts")

confirm = input("\nTaper 'MIGRER' pour lancer: ").strip()

if confirm != "MIGRER":
    print("\n❌ Migration annulée")
    exit(0)

# ══════════════════════════════════════════════════════════════════════
# MIGRATION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🚀 MIGRATION EN COURS...")
print("="*80)

con = duckdb.connect(str(db_path), read_only=False)

try:
    start_time = time.time()
    
    print(f"\n⏳ Ajout de 2h à tous les prix...")
    print(f"   (Cela peut prendre 1-2 minutes)")
    
    # MIGRATION: Ajouter 2h à tous les prix
    con.execute("""
        UPDATE prices_1m
        SET datetime = datetime + INTERVAL '2 hours'
    """)
    
    con.commit()
    
    duration = time.time() - start_time
    
    print(f"\n✅ MIGRATION RÉUSSIE !")
    print(f"   {count:,} prix migrés")
    print(f"   Durée: {duration:.1f} secondes")
    
    # ══════════════════════════════════════════════════════════════════
    # VÉRIFICATION POST-MIGRATION
    # ══════════════════════════════════════════════════════════════════
    
    print("\n" + "="*80)
    print("✅ VÉRIFICATION POST-MIGRATION")
    print("="*80)
    
    # Vérifier exemple
    new_sample = con.execute("""
        SELECT datetime, open 
        FROM prices_1m 
        WHERE datetime >= '2025-09-11 14:30:00'
        AND datetime < '2025-09-11 14:31:00'
        LIMIT 1
    """).fetchone()
    
    print(f"\n💹 Exemple APRÈS migration:")
    print(f"   Ancien: {sample[0]}")
    print(f"   Nouveau: {new_sample[0]}")
    print(f"   Open: {new_sample[1]:.5f}")
    
    if abs(new_sample[1] - sample[1]) < 0.00001:
        print(f"\n✅ Prix préservé (seul timestamp changé)")
    else:
        print(f"\n⚠️ ATTENTION: Prix changé !")
    
    # Vérifier event/prix alignés
    event = con.execute("""
        SELECT ts_utc FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
        AND event_title LIKE '%CPI%'
        LIMIT 1
    """).fetchone()
    
    print(f"\n🔍 Alignement Event/Prix:")
    print(f"   Event: {event[0]}")
    print(f"   Prix:  {new_sample[0]}")
    
    event_time = str(event[0]).split('+')[0].split('.')[0]
    prix_time = str(new_sample[0]).split('+')[0].split('.')[0]
    
    if event_time == prix_time:
        print(f"\n🎉 PARFAIT ! Event et Prix alignés à 14:30 !")
    else:
        print(f"\n⚠️ Décalage détecté")
    
except Exception as e:
    print(f"\n❌ ERREUR MIGRATION: {e}")
    print(f"\n🔄 Rollback en cours...")
    con.rollback()
    print(f"✅ Rollback terminé")
    
    print(f"\n💡 Pour restaurer backup:")
    print(f"   cp '{last_backup}' '{db_path}'")
    
finally:
    con.close()

print("\n" + "="*80)
print("FIN MIGRATION")
print("="*80)

print(f"\n📋 PROCHAINES ÉTAPES:")
print(f"  1. Lance: STEP3_test_apres_migration.py")
print(f"  2. Vérifie impact = ~57 pips")
print(f"  3. Mets à jour impact_measurement.py (enlever -2h)")
