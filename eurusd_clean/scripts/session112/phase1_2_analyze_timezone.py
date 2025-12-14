#!/usr/bin/env python3
"""
MIGRATION TIMEZONE - Unification events → Bern time
====================================================

Corrige les timestamps de la table events pour qu'ils correspondent
aux timestamps de prices_1m (Bern time).

PROBLÈME ACTUEL:
- Events: Stockés à 14:30+02:00 (avec offset mais décalé de -2h)
- Prices: Stockés à 14:30+02:00 (temps réel Bern)
- Pour un événement 14:30 Bern, events pointe vers prix 12:30

SOLUTION:
- Ne rien changer (events déjà en Bern selon vérification)
- OU ajuster si décalage confirmé

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 1
"""

import duckdb
from pathlib import Path
import pandas as pd

print("="*80)
print("🔧 MIGRATION TIMEZONE - ANALYSE")
print("="*80)

db_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb")

if not db_path.exists():
    print(f"❌ DB introuvable: {db_path}")
    exit(1)

con = duckdb.connect(str(db_path), read_only=False)

# ══════════════════════════════════════════════════════════════════════
# ANALYSE SITUATION ACTUELLE
# ══════════════════════════════════════════════════════════════════════

print("\n📊 ANALYSE SITUATION 11 SEPTEMBRE 2025:")
print("-"*80)

# Events
events = con.execute("""
SELECT ts_utc, event_title
FROM events
WHERE DATE(ts_utc) = '2025-09-11'
    AND event_title LIKE '%CPI%'
    AND country = 'US'
LIMIT 1
""").df()

if len(events) > 0:
    event_ts = events.iloc[0]['ts_utc']
    print(f"\n✅ Event CPI stocké à: {event_ts}")
else:
    print(f"\n❌ Aucun événement CPI trouvé")
    con.close()
    exit(1)

# Prix à cette heure exacte
prices_event_time = con.execute(f"""
SELECT datetime, open, close
FROM prices_1m
WHERE datetime >= '{event_ts}'
    AND datetime < '{event_ts}'::TIMESTAMP + INTERVAL '1 minute'
""").df()

# Prix 2h avant
event_ts_minus_2h = pd.to_datetime(event_ts) - pd.Timedelta(hours=2)
prices_minus_2h = con.execute(f"""
SELECT datetime, open, close
FROM prices_1m
WHERE datetime >= '{event_ts_minus_2h}'
    AND datetime < '{event_ts_minus_2h}'::TIMESTAMP + INTERVAL '1 minute'
""").df()

print(f"\n💹 Prix à l'heure événement ({event_ts}):")
if len(prices_event_time) > 0:
    print(f"   Open: {prices_event_time['open'].iloc[0]:.5f}")
else:
    print(f"   ❌ Aucun prix trouvé")

print(f"\n💹 Prix 2h avant ({event_ts_minus_2h}):")
if len(prices_minus_2h) > 0:
    print(f"   Open: {prices_minus_2h['open'].iloc[0]:.5f}")
    print(f"   (Devrait être ~1.16874 selon Session 106)")
else:
    print(f"   ❌ Aucun prix trouvé")

# ══════════════════════════════════════════════════════════════════════
# DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🔍 DIAGNOSTIC")
print("="*80)

if len(prices_minus_2h) > 0:
    price_minus_2h = prices_minus_2h['open'].iloc[0]
    
    # Vérifier si c'est le bon prix (environ 1.16874)
    if 1.168 < price_minus_2h < 1.170:
        print(f"\n✅ CONFIRMATION: Le bon prix est 2h AVANT le timestamp event")
        print(f"   Prix -2h: {price_minus_2h:.5f} (proche de 1.16874)")
        print(f"\n💡 CONCLUSION:")
        print(f"   Les events sont stockés avec un DÉCALAGE de +2h")
        print(f"   Il faut chercher les prix à: event_time - 2h")
        print(f"\n⚠️ MAIS cela veut dire que les events sont déjà CORRECTS !")
        print(f"   Car ils ont le offset +02:00 qui indique Bern time")
        print(f"   Le problème est dans notre INTERPRÉTATION")
        
        needs_migration = False
    else:
        print(f"\n⚠️ Prix -2h = {price_minus_2h:.5f} (inattendu)")
        needs_migration = None

# ══════════════════════════════════════════════════════════════════════
# DÉCISION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📋 DÉCISION")
print("="*80)

if needs_migration == False:
    print(f"\n✅ PAS DE MIGRATION NÉCESSAIRE !")
    print(f"\n📖 NOUVELLE RÈGLE SIMPLE:")
    print(f"   Pour un événement stocké à: {event_ts}")
    print(f"   Chercher les prix à: {event_ts_minus_2h} (soustraire 2h)")
    print(f"\n💡 Raison:")
    print(f"   - Events: Stockés avec l'heure AFFICHÉE (14:30+02:00)")
    print(f"   - Prices: Stockés avec l'heure RÉELLE à laquelle le prix existait")
    print(f"   - L'événement à 14:30 impacte les prix à partir de 12:30 dans la DB")
    print(f"\n🔧 Solution: Garder DB telle quelle, ajuster les scripts")
    
else:
    print(f"\n⚠️ Situation ambiguë - investigation manuelle nécessaire")

con.close()

print("\n" + "="*80)
print("FIN ANALYSE")
print("="*80)
