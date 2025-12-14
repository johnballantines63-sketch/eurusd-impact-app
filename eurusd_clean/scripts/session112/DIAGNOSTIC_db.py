#!/usr/bin/env python3
"""
DIAGNOSTIC DB - Colonnes et Données
====================================

Vérifie structure DB et données pour comprendre problème "None"

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path
import sys

eurusd_clean = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean")
sys.path.insert(0, str(eurusd_clean / "src"))

import config
import duckdb

print("="*80)
print("🔍 DIAGNOSTIC BASE DE DONNÉES")
print("="*80)

conn = duckdb.connect(str(config.DB_PATH), read_only=True)

# ══════════════════════════════════════════════════════════════════════
# 1. STRUCTURE TABLE EVENTS
# ══════════════════════════════════════════════════════════════════════

print("\n📊 TABLE EVENTS - Structure")
print("-"*80)

schema = conn.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'events'
    ORDER BY ordinal_position
""").fetchall()

print(f"\nNombre de colonnes: {len(schema)}")
for col, dtype in schema:
    print(f"  {col:25} {dtype}")

# ══════════════════════════════════════════════════════════════════════
# 2. ÉVÉNEMENTS FUTURS US
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📅 ÉVÉNEMENTS FUTURS US (prochain)")
print("-"*80)

events = conn.execute("""
    SELECT 
        event_title,
        country,
        ts_utc,
        importance_n,
        forecast,
        previous,
        actual
    FROM events
    WHERE country = 'US'
    AND ts_utc >= CURRENT_TIMESTAMP
    ORDER BY ts_utc
    LIMIT 10
""").fetchall()

print(f"\nNombre d'événements futurs US: {len(events)}")
print(f"\nDétail premier événement:")
if events:
    for i, row in enumerate(events[:3], 1):
        print(f"\n{i}. Event: {row[0]}")
        print(f"   Pays: {row[1]}")
        print(f"   Date: {row[2]}")
        print(f"   Importance: {row[3]}")
        print(f"   Forecast: {row[4]}")
        print(f"   Previous: {row[5]}")
        print(f"   Actual: {row[6]}")
else:
    print("⚠️ Aucun événement futur trouvé")

# ══════════════════════════════════════════════════════════════════════
# 3. VÉRIFIER VALEURS NULL
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("🔍 ÉVÉNEMENTS AVEC NOM NULL")
print("-"*80)

null_events = conn.execute("""
    SELECT COUNT(*)
    FROM events
    WHERE event_title IS NULL
    AND ts_utc >= CURRENT_TIMESTAMP
""").fetchone()[0]

print(f"Événements futurs avec nom NULL: {null_events}")

if null_events > 0:
    print(f"\n⚠️ PROBLÈME DÉTECTÉ:")
    print(f"   {null_events} événements n'ont pas de nom (NULL)")
    print(f"   → Cela explique affichage 'None'")

# ══════════════════════════════════════════════════════════════════════
# 4. STATISTIQUES GLOBALES
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 STATISTIQUES GLOBALES")
print("-"*80)

stats = conn.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN event_title IS NOT NULL THEN 1 END) as with_name,
        COUNT(CASE WHEN forecast IS NOT NULL THEN 1 END) as with_forecast,
        COUNT(CASE WHEN ts_utc >= CURRENT_TIMESTAMP THEN 1 END) as future
    FROM events
    WHERE country IN ('US', 'EU', 'GB')
""").fetchone()

print(f"Total événements: {stats[0]:,}")
print(f"Avec nom: {stats[1]:,} ({stats[1]/stats[0]*100:.1f}%)")
print(f"Avec forecast: {stats[2]:,} ({stats[2]/stats[0]*100:.1f}%)")
print(f"Futurs: {stats[3]:,}")

conn.close()

# ══════════════════════════════════════════════════════════════════════
# CONCLUSION
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💡 DIAGNOSTIC TERMINÉ")
print("="*80)

if null_events > 0:
    print(f"""
⚠️ PROBLÈME IDENTIFIÉ:
   Des événements ont event=NULL dans la DB
   
🔧 SOLUTIONS:
   1. Vérifier import EODHD (script eodhd_client)
   2. Vérifier que champ 'event' est bien récupéré
   3. Nettoyer DB si nécessaire
""")
else:
    print("""
✅ DB SEMBLE OK
   Tous les événements ont un nom
   
💡 Si "None" s'affiche encore:
   Problème probablement dans code Calendrier Trading
   → Vérifier requête SQL et affichage Streamlit
""")

print("="*80)
