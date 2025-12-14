#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug Détection Noyau Dur

Vérifie pourquoi le noyau dur n'est pas détecté correctement pour le 1er août 2025.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import duckdb

# Ajouter chemins
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import get_db_path
from core.event_loader import load_high_impact_events

print("=" * 80)
print("🔍 DEBUG DÉTECTION NOYAU DUR - 1er août 2025")
print("=" * 80)
print()

# Charger événements pour le 1er août 2025
date_str = '2025-08-01'
db_path = Path(get_db_path())

print(f"📅 Date : {date_str}")
print(f"📂 DB : {db_path}")
print()

# Charger événements (pour chaque pays séparément)
all_events = []
for country in ['US', 'EU', 'DE']:
    try:
        events_country = load_high_impact_events(
            db_path,
            datetime(2025, 8, 1),
            country=country,
            min_empirical_score=29.0 if country != 'DE' else 20.0,
            verbose=False
        )
        if not events_country.empty:
            events_country['country'] = country
            all_events.append(events_country)
    except Exception as e:
        print(f"Erreur chargement {country}: {e}")

if all_events:
    events = pd.concat(all_events, ignore_index=True)
else:
    events = pd.DataFrame()

if events.empty:
    print("❌ Aucun événement trouvé")
    sys.exit(1)

print()
print("=" * 80)
print("📊 ÉVÉNEMENTS CHARGÉS")
print("=" * 80)
print()

# Afficher tous les événements avec leurs event_keys
for idx, (_, event) in enumerate(events.iterrows(), 1):
    event_key = str(event.get('event_key', 'N/A') or 'N/A')
    event_title = str(event.get('event_title', 'N/A') or 'N/A')
    family = str(event.get('family', 'N/A') or 'N/A')
    country = str(event.get('country', 'N/A') or 'N/A')
    importance = event.get('importance_n', 'N/A')
    score = event.get('empirical_score', 'N/A')
    
    print(f"{idx:2d}. {event_key[:60]:<60} | Family: {family:<20} | Score: {score}")
    if event_title != 'N/A' and event_title != event_key:
        print(f"    Title: {event_title[:80]}")

print()
print("=" * 80)
print("🔍 TEST PATTERNS")
print("=" * 80)
print()

# Patterns utilisés dans le code
CPI_PATTERN = r'(?i)(cpi|consumer price|inflation rate|core inflation|harmonised inflation)'
NFP_PATTERN = r'(?i)(non farm payrolls|nonfarm)'

print(f"Pattern CPI : {CPI_PATTERN}")
print(f"Pattern NFP : {NFP_PATTERN}")
print()

cpi_matches = []
nfp_matches = []

for idx, (_, event) in enumerate(events.iterrows(), 1):
    event_key = str(event.get('event_key', '')).lower()
    event_title = str(event.get('event_title', '')).lower()
    
    # Tester pattern CPI
    if re.search(CPI_PATTERN, event_key) or re.search(CPI_PATTERN, event_title):
        cpi_matches.append({
            'idx': idx,
            'event_key': event.get('event_key', 'N/A'),
            'event_title': event.get('event_title', 'N/A'),
            'family': event.get('family', 'N/A')
        })
    
    # Tester pattern NFP
    if re.search(NFP_PATTERN, event_key) or re.search(NFP_PATTERN, event_title):
        nfp_matches.append({
            'idx': idx,
            'event_key': event.get('event_key', 'N/A'),
            'event_title': event.get('event_title', 'N/A'),
            'family': event.get('family', 'N/A')
        })

print(f"✅ Événements CPI détectés : {len(cpi_matches)}")
for match in cpi_matches:
    print(f"   - {match['idx']:2d}. {match['event_key'][:60]}")
    print(f"     Family: {match['family']}")

print()
print(f"✅ Événements NFP détectés : {len(nfp_matches)}")
for match in nfp_matches:
    print(f"   - {match['idx']:2d}. {match['event_key'][:60]}")
    print(f"     Family: {match['family']}")

print()
print("=" * 80)
print("📋 CLUSTER À 14:30")
print("=" * 80)
print()

# Simuler détection cluster (fenêtre 30 min autour de 14:30)
from datetime import timedelta
import pytz

tz_bern = pytz.timezone('Europe/Zurich')
anchor_time = tz_bern.localize(datetime(2025, 8, 1, 14, 30, 0))

events['ts_utc'] = pd.to_datetime(events['ts_utc'])
window_start = anchor_time
window_end = anchor_time + timedelta(minutes=30)

mask = (
    (events['ts_utc'] >= window_start) &
    (events['ts_utc'] < window_end)
)
cluster_events = events[mask].copy()

print(f"⏰ Fenêtre : {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}")
print(f"📊 Événements dans cluster : {len(cluster_events)}")
print()

if not cluster_events.empty:
    print("Événements du cluster :")
    for idx, (_, event) in enumerate(cluster_events.iterrows(), 1):
        event_key = event.get('event_key', 'N/A')
        event_title = event.get('event_title', 'N/A')
        family = event.get('family', 'N/A')
        ts = event.get('ts_utc', 'N/A')
        
        print(f"{idx:2d}. {ts.strftime('%H:%M') if hasattr(ts, 'strftime') else ts} | {event_key[:50]:<50} | Family: {family}")
    
    print()
    print("Test détection noyau dur sur ce cluster :")
    
    # Simuler la détection comme dans le code
    event_keys_normalized = []
    for _, event in cluster_events.iterrows():
        event_key = event.get('event_key', '')
        event_key_norm = str(event_key).lower().strip() if pd.notna(event_key) else ''
        event_keys_normalized.append(event_key_norm)
    
    cpi_count = 0
    nfp_count = 0
    
    for event_key_norm in event_keys_normalized:
        if event_key_norm:
            if re.search(CPI_PATTERN, event_key_norm):
                cpi_count += 1
            if re.search(NFP_PATTERN, event_key_norm):
                nfp_count += 1
    
    print(f"   CPI count : {cpi_count}")
    print(f"   NFP count : {nfp_count}")
    
    if cpi_count >= 2:
        print(f"   → Noyau dur CPI détecté")
    elif nfp_count >= 1:
        print(f"   → Noyau dur NFP détecté")
    else:
        print(f"   → Aucun noyau dur détecté (GENERIC)")
        print()
        print("   ⚠️ PROBLÈME : Le noyau dur devrait être détecté !")
        print()
        print("   Vérification manuelle des event_keys :")
        for event_key_norm in event_keys_normalized:
            print(f"      - '{event_key_norm}'")
            if 'payroll' in event_key_norm or 'nonfarm' in event_key_norm or 'nfp' in event_key_norm:
                print(f"        → Contient 'payroll'/'nonfarm'/'nfp' mais pattern ne matche pas !")
else:
    print("❌ Aucun événement dans la fenêtre 14:30-15:00")

print()
print("=" * 80)

