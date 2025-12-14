"""
Comparaison Événements 11 Septembre - AVANT/APRÈS
==================================================

Compare les événements du 11 septembre 2025 entre:
- AVANT: table 'events' (structure validée)
- APRÈS: table 'economic_events' (EODHD)
"""

import duckdb
from pathlib import Path
import pandas as pd

# Chemins
DB_BACKUP = Path(__file__).parent.parent / 'session123' / 'backups' / 'warehouse_backup_20251109_201627.duckdb'
DB_ACTUELLE = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

print("\n" + "="*80)
print("COMPARAISON 11 SEPTEMBRE 2025 - AVANT/APRÈS")
print("="*80)
print()

# Fenêtre: 12:00 - 14:30 UTC (14:00 - 16:30 Bern)
start_utc = '2025-09-11 12:00:00'
end_utc = '2025-09-11 14:30:00'

# ============================================================================
# AVANT (table events)
# ============================================================================

print("="*80)
print("AVANT - Table 'events' (structure validée)")
print("="*80)
print()

conn_backup = duckdb.connect(str(DB_BACKUP), read_only=True)

query_avant = """
SELECT 
    ts_utc,
    country,
    event_key,
    event_title,
    importance_n,
    actual,
    estimate,
    forecast,
    previous
FROM events
WHERE ts_utc BETWEEN ? AND ?
  AND LOWER(country) IN ('usd', 'eur', 'de', 'eu')
  AND importance_n >= 2
ORDER BY ts_utc, importance_n DESC
"""

events_avant = conn_backup.execute(query_avant, [start_utc, end_utc]).df()

print(f"📊 Événements HIGH/MEDIUM: {len(events_avant)}")
print()

if len(events_avant) > 0:
    print("Liste complète:")
    print()
    for idx, event in events_avant.iterrows():
        imp_label = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}.get(event['importance_n'], "?")
        
        print(f"{idx+1}. {event['ts_utc']} | {event['country'].upper()} | {imp_label}")
        print(f"   {event['event_title']}")
        print(f"   Actual: {event['actual']}")
        print(f"   Estimate: {event['estimate']}")
        print(f"   Forecast: {event['forecast']}")
        print(f"   Previous: {event['previous']}")
        
        # Calculer surprise
        ref = event['estimate'] if pd.notna(event['estimate']) else event['forecast']
        if pd.notna(event['actual']) and pd.notna(ref) and abs(ref) > 0.001:
            surprise = ((event['actual'] - ref) / abs(ref)) * 100
            print(f"   Surprise: {surprise:+.2f}%")
        
        print()

conn_backup.close()

# ============================================================================
# APRÈS (table economic_events)
# ============================================================================

print("="*80)
print("APRÈS - Table 'economic_events' (EODHD)")
print("="*80)
print()

conn_actuelle = duckdb.connect(str(DB_ACTUELLE), read_only=True)

query_apres = """
SELECT 
    datetime_utc,
    country,
    event_name,
    importance,
    actual,
    forecast,
    previous
FROM economic_events
WHERE datetime_utc BETWEEN ? AND ?
  AND LOWER(country) IN ('usd', 'eur', 'de', 'eu')
  AND importance IN ('HIGH', 'MEDIUM')
ORDER BY datetime_utc, importance DESC
"""

events_apres = conn_actuelle.execute(query_apres, [start_utc, end_utc]).df()

print(f"📊 Événements HIGH/MEDIUM: {len(events_apres)}")
print()

if len(events_apres) > 0:
    print("Liste complète:")
    print()
    for idx, event in events_apres.iterrows():
        print(f"{idx+1}. {event['datetime_utc']} | {event['country'].upper()} | {event['importance']}")
        print(f"   {event['event_name']}")
        print(f"   Actual: {event['actual']}")
        print(f"   Forecast: {event['forecast']}")
        print(f"   Previous: {event['previous']}")
        
        # Calculer surprise
        ref = event['forecast']
        if pd.notna(event['actual']) and pd.notna(ref) and abs(ref) > 0.001:
            surprise = ((event['actual'] - ref) / abs(ref)) * 100
            print(f"   Surprise: {surprise:+.2f}%")
        
        print()

conn_actuelle.close()

# ============================================================================
# ANALYSE
# ============================================================================

print("="*80)
print("ANALYSE")
print("="*80)
print()

print(f"Nombre événements HIGH/MEDIUM:")
print(f"  AVANT:  {len(events_avant)}")
print(f"  APRÈS:  {len(events_apres)}")
print(f"  Diff:   {len(events_apres) - len(events_avant):+d}")
print()

if len(events_avant) > 0 and len(events_apres) > 0:
    # Événements HIGH seulement
    if 'importance_n' in events_avant.columns:
        high_avant = events_avant[events_avant['importance_n'] == 3]
    else:
        high_avant = pd.DataFrame()
    
    high_apres = events_apres[events_apres['importance'] == 'HIGH']
    
    print(f"Événements HIGH seulement:")
    print(f"  AVANT:  {len(high_avant)}")
    print(f"  APRÈS:  {len(high_apres)}")
    print()
    
    # Chercher CPI events
    print("Recherche CPI:")
    
    cpi_avant = events_avant[events_avant['event_title'].str.contains('cpi|consumer price|inflation', case=False, na=False)]
    print(f"  AVANT:  {len(cpi_avant)} événements CPI")
    
    cpi_apres = events_apres[events_apres['event_name'].str.contains('cpi|consumer_price|inflation', case=False, na=False)]
    print(f"  APRÈS:  {len(cpi_apres)} événements CPI")
    print()

print("="*80)
print("CONCLUSION")
print("="*80)
print()

print("📊 STRUCTURES DIFFÉRENTES:")
print("  AVANT:  ts_utc (WITH TZ), event_title, importance_n, estimate+forecast")
print("  APRÈS:  datetime_utc (NO TZ), event_name, importance (text), forecast only")
print()

print("⚠️  IMPACT SUR FORMULES:")
print("  1. Timezone handling différent (WITH TZ vs sans)")
print("  2. Noms colonnes changés (event_title → event_name)")
print("  3. Format importance changé (INT → VARCHAR)")
print("  4. Estimate manquant (utilisé comme fallback dans formules)")
print()

print("💡 SOLUTION:")
print("  Option A: Convertir formules pour utiliser nouvelle structure EODHD")
print("  Option B: Créer vue compatibilité (alias colonnes)")
print("  Option C: Réimporter ancienne structure events (si meilleure qualité)")
