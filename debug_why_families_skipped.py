#!/usr/bin/env python3
"""
Debug : Pourquoi tant de familles sont ignorées ?
Compte les événements réels pour chaque pattern
"""

import sys
from pathlib import Path
import duckdb
import re

project_root = Path(__file__).parent
src_path = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
from event_families import FAMILY_PATTERNS

DB_PATH = get_db_path()

print("=" * 80)
print("DEBUG : NOMBRE D'ÉVÉNEMENTS PAR FAMILLE")
print("=" * 80)
print()

conn = duckdb.connect(DB_PATH, read_only=True)

# Pour chaque famille, compter événements dans prices_1m
results = []

for family_name, pattern in FAMILY_PATTERNS.items():
    # Nettoyer pattern
    clean_pattern = pattern.replace('(?i)', '')
    
    # Trouver event_keys qui matchent
    query_keys = """
    SELECT DISTINCT event_key, country
    FROM event_families
    """
    all_keys = conn.execute(query_keys).fetchall()
    
    matched_keys = []
    for event_key, country in all_keys:
        if re.search(clean_pattern, event_key, re.IGNORECASE):
            matched_keys.append((event_key, country))
    
    if not matched_keys:
        results.append({
            'family': family_name,
            'n_event_keys': 0,
            'n_events_total': 0,
            'status': '❌ Aucun event_key'
        })
        continue
    
    # Compter événements dans events table
    # (événements historiques disponibles pour calcul)
    event_keys_str = "', '".join([ek[0] for ek in matched_keys])
    
    query_count = f"""
    SELECT COUNT(DISTINCT ts_utc) as n_events
    FROM events
    WHERE event_key IN ('{event_keys_str}')
    """
    
    try:
        n_events = conn.execute(query_count).fetchone()[0]
        
        if n_events >= 5:
            status = f"✅ OK ({n_events} événements)"
        elif n_events > 0:
            status = f"⚠️  Insuffisant ({n_events} événements < 5)"
        else:
            status = "❌ Aucun événement"
        
        results.append({
            'family': family_name,
            'n_event_keys': len(matched_keys),
            'n_events_total': n_events,
            'status': status
        })
    except Exception as e:
        results.append({
            'family': family_name,
            'n_event_keys': len(matched_keys),
            'n_events_total': 0,
            'status': f"❌ Erreur: {e}"
        })

conn.close()

# Afficher résultats
print("Famille                              | Event_Keys | Événements | Status")
print("-" * 80)

results.sort(key=lambda x: x['n_events_total'], reverse=True)

for r in results:
    print(f"{r['family']:<35} | {r['n_event_keys']:>10} | {r['n_events_total']:>10} | {r['status']}")

print()
print("=" * 80)
print("ANALYSE")
print("=" * 80)
print()

ok_count = len([r for r in results if '✅' in r['status']])
insufficient_count = len([r for r in results if '⚠️' in r['status']])
no_data_count = len([r for r in results if '❌' in r['status']])

print(f"✅ Familles OK (>= 5 événements)      : {ok_count}/35")
print(f"⚠️  Familles insuffisantes (1-4 evt)   : {insufficient_count}/35")
print(f"❌ Familles sans données               : {no_data_count}/35")
print()

if ok_count < 10:
    print("🔍 PROBLÈME DÉTECTÉ !")
    print()
    print("Seulement", ok_count, "familles avec >= 5 événements, mais beaucoup")
    print("d'event_keys matchés. Cela signifie probablement que :")
    print()
    print("1. LatencyAnalyzer utilise un seuil trop strict")
    print("2. Ou les événements ne sont pas dans la table events")
    print("3. Ou le calcul de latence échoue pour ces familles")
    print()
    print("💡 SOLUTION : Vérifier pourquoi LatencyAnalyzer retourne 0 événements")
    print("              alors que la table events en contient.")
else:
    print(f"✅ {ok_count} familles devraient être pré-calculées !")
    print()
    print("   Si le script en ignore quand même, le problème est dans")
    print("   LatencyAnalyzer.calculate_family_latency_stats()")

print()
print("=" * 80)
