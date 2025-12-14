#!/usr/bin/env python3
"""
MIGRATION TIMEZONE - Ajouter 2h aux events
===========================================

OBJECTIF: Unifier timezones events et prices
- Events actuellement: 14:30+02:00 (heure affichée)
- Prices: 12:30 correspond à event 14:30
- SOLUTION: Ajouter 2h aux events pour aligner

APRÈS MIGRATION:
- Event 14:30 → devient 16:30
- Prix 14:30 correspond maintenant à event old 12:30
- NON ! C'est l'inverse !

CORRECTION LOGIQUE:
Pour qu'un event à 14:30 corresponde aux prix 14:30,
il faut que le timestamp event POINTE vers 14:30.
Actuellement il pointe vers 12:30 (avec affichage 14:30+02:00).

Donc: PAS ajouter 2h, mais RETIRER le +02:00 ou ajuster...

ATTENDS, relisons la situation:
- Event DB: 14:30+02:00
- Prix pour cet event: 12:30
- Pour que event 14:30 → prix 14:30, il faut... hmm

En fait le problème est l'interprétation:
- Si event est 14:30+02:00 et prix 12:30 marche
- C'est que le 14:30+02:00 est en fait 12:30 UTC+02 = 12:30 local
- Donc ajouter 2h ferait: 14:30+02:00 → 16:30+02:00

Clarifions avec André d'abord !

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

import duckdb
from pathlib import Path
import pandas as pd

print("="*80)
print("🔧 MIGRATION TIMEZONE - UNIFICATION")
print("="*80)

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

# ══════════════════════════════════════════════════════════════════════
# ANALYSE PRÉ-MIGRATION
# ══════════════════════════════════════════════════════════════════════

print("\n📊 ANALYSE PRÉ-MIGRATION")
print("-"*80)

con = duckdb.connect(str(db_path), read_only=True)

# Event exemple
event = con.execute("""
    SELECT ts_utc, event_title
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    AND event_title LIKE '%CPI%'
    LIMIT 1
""").fetchone()

print(f"\nEvent CPI 11 sept:")
print(f"  Timestamp actuel: {event[0]}")

# Prix correspondant (actuellement -2h)
price_minus_2h = con.execute("""
    SELECT datetime, open
    FROM prices_1m
    WHERE datetime >= '2025-09-11 12:30:00'
    AND datetime < '2025-09-11 12:31:00'
    LIMIT 1
""").fetchone()

print(f"\nPrix correspondant actuel (event - 2h):")
print(f"  Timestamp: {price_minus_2h[0]}")
print(f"  Open: {price_minus_2h[1]:.5f}")

# Prix à la même heure que event
price_same_time = con.execute("""
    SELECT datetime, open
    FROM prices_1m
    WHERE datetime >= '2025-09-11 14:30:00'
    AND datetime < '2025-09-11 14:31:00'
    LIMIT 1
""").fetchone()

if price_same_time:
    print(f"\nPrix à la même heure que event:")
    print(f"  Timestamp: {price_same_time[0]}")
    print(f"  Open: {price_same_time[1]:.5f}")

con.close()

# ══════════════════════════════════════════════════════════════════════
# QUESTION: Quelle transformation ?
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("❓ QUELLE TRANSFORMATION ?")
print("="*80)

print("\n📋 OPTION A1: Ajouter 2h aux timestamps events")
print(f"   {event[0]} → (ajouter 2h) → 2025-09-11 16:30:00+02:00")
print(f"   Résultat: Event 16:30 correspondrait à prix 14:30")
print(f"   ⚠️ Mais on veut event 14:30 → prix 14:30 !")

print("\n📋 OPTION A2: Soustraire 2h aux timestamps events")
print(f"   {event[0]} → (soustraire 2h) → 2025-09-11 12:30:00+02:00")
print(f"   Résultat: Event 12:30 correspondrait à prix 12:30")
print(f"   ✅ Event affiché 14:30 devient stocké 12:30 (= prix)")

print("\n💡 CLARIFICATION NÉCESSAIRE:")
print("\nSituation actuelle:")
print(f"  - Event stocké: {event[0]}")
print(f"  - Prix correspondant: {price_minus_2h[0]} (open: {price_minus_2h[1]:.5f})")
print(f"  - Pour trouver prix, on fait: event - 2h")

print("\nAprès migration souhaitée:")
print(f"  - Event devrait pointer vers: {price_minus_2h[0]}")
print(f"  - Pour trouver prix, on fait: event (direct, sans -2h)")

print("\n" + "="*80)
print("⚠️ CONFIRMATION REQUISE")
print("="*80)

print("\nPour unifier les timestamps, il faut:")
print("[1] AJOUTER 2h aux events (event 14:30 → 16:30)")
print("[2] SOUSTRAIRE 2h aux events (event 14:30 → 12:30)")

choice = input("\nQuel changement veux-tu ? (1 ou 2): ").strip()

if choice == "2":
    print("\n✅ SOUSTRAIRE 2h aux events")
    print(f"   Event {event[0]} deviendra: 2025-09-11 12:30:00+02:00")
    print(f"   Correspondra directement aux prix 12:30")
    
    confirm = input("\nTaper 'MIGRER' pour confirmer: ").strip()
    
    if confirm == "MIGRER":
        print("\n🔄 MIGRATION EN COURS...")
        
        con = duckdb.connect(str(db_path), read_only=False)
        
        try:
            # Compter events
            count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            print(f"\n📊 {count:,} events à migrer")
            
            # MIGRATION: Soustraire 2h
            con.execute("""
                UPDATE events
                SET ts_utc = ts_utc - INTERVAL '2 hours'
            """)
            
            con.commit()
            
            print(f"\n✅ MIGRATION RÉUSSIE !")
            print(f"   {count:,} events migrés")
            
            # Vérification
            new_event = con.execute("""
                SELECT ts_utc FROM events
                WHERE DATE(ts_utc) = '2025-09-11'
                AND event_title LIKE '%CPI%'
                LIMIT 1
            """).fetchone()
            
            print(f"\n✅ Vérification:")
            print(f"   Ancien: {event[0]}")
            print(f"   Nouveau: {new_event[0]}")
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            con.rollback()
        finally:
            con.close()
            
elif choice == "1":
    print("\n✅ AJOUTER 2h aux events")
    print(f"   Event {event[0]} deviendra: 2025-09-11 16:30:00+02:00")
    
    confirm = input("\nTaper 'MIGRER' pour confirmer: ").strip()
    
    if confirm == "MIGRER":
        print("\n🔄 MIGRATION EN COURS...")
        
        con = duckdb.connect(str(db_path), read_only=False)
        
        try:
            count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            print(f"\n📊 {count:,} events à migrer")
            
            # MIGRATION: Ajouter 2h
            con.execute("""
                UPDATE events
                SET ts_utc = ts_utc + INTERVAL '2 hours'
            """)
            
            con.commit()
            
            print(f"\n✅ MIGRATION RÉUSSIE !")
            print(f"   {count:,} events migrés")
            
            new_event = con.execute("""
                SELECT ts_utc FROM events
                WHERE DATE(ts_utc) = '2025-09-11'
                AND event_title LIKE '%CPI%'
                LIMIT 1
            """).fetchone()
            
            print(f"\n✅ Vérification:")
            print(f"   Ancien: {event[0]}")
            print(f"   Nouveau: {new_event[0]}")
            
        except Exception as e:
            print(f"\n❌ ERREUR: {e}")
            con.rollback()
        finally:
            con.close()
else:
    print("\n❌ Choix invalide - Migration annulée")

print("\n" + "="*80)
print("FIN MIGRATION")
print("="*80)
