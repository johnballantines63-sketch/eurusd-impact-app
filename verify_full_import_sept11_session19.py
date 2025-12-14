#!/usr/bin/env python3
"""
Vérification finale : 11 septembre 2025 avec TOUS les champs
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fx_impact_app.src.config import get_db_path

print("\n" + "="*90)
print("VÉRIFICATION FINALE : 11 septembre 2025 avec TOUS les champs")
print("="*90)

db_path = get_db_path()
conn = duckdb.connect(str(db_path))

# Tous les événements US du 11 septembre
print("\n[1] TOUS les événements US du 11 septembre 2025 :")
print("-"*90)

result = conn.execute("""
    SELECT 
        strftime(ts_utc, '%H:%M') as time,
        event_key,
        actual,
        estimate,
        comparison,
        period,
        event_type
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND country = 'US'
    ORDER BY ts_utc, event_key
""").fetchall()

print(f"Total événements : {len(result)}")
print(f"\n{'Time':<7} {'Event Key':<40} {'Actual':>8} {'Est':>8} {'Comp':>6} {'Period':<6} {'Type':<30}")
print("-"*130)

for time, event_key, actual, estimate, comparison, period, event_type in result:
    act_str = f"{actual:.2f}" if actual else "N/A"
    est_str = f"{estimate:.2f}" if estimate else "N/A"
    comp_str = comparison or "-"
    per_str = period or "-"
    type_str = (event_type or "-")[:30]
    
    print(f"{time:<7} {event_key:<40} {act_str:>8} {est_str:>8} {comp_str:>6} {per_str:<6} {type_str:<30}")

# Focus sur inflation
print("\n[2] Focus INFLATION RATE 11 septembre :")
print("-"*90)

inflation = conn.execute("""
    SELECT 
        event_key,
        actual,
        estimate,
        previous,
        comparison,
        period,
        change,
        change_percentage,
        event_type,
        CASE 
            WHEN estimate IS NOT NULL AND estimate != 0 
            THEN ABS((actual - estimate) / estimate) * 100
            ELSE 0
        END as surprise_pct
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
      AND country = 'US'
      AND event_key LIKE '%inflation%rate%'
    ORDER BY event_key
""").fetchall()

if inflation:
    print(f"\n{'Event Key':<45} {'Actual':>8} {'Est':>8} {'Surp':>6} {'Comp':>6} {'Period':<6}")
    print("-"*90)
    
    has_mom = False
    has_yoy = False
    significant_surprise = False
    
    for row in inflation:
        event_key, actual, estimate, previous, comparison, period, change, change_pct, event_type, surprise = row
        
        act_str = f"{actual:.2f}" if actual else "N/A"
        est_str = f"{estimate:.2f}" if estimate else "N/A"
        surp_str = f"{surprise:.1f}%" if surprise else "0%"
        comp_str = comparison or "-"
        per_str = period or "-"
        
        print(f"{event_key:<45} {act_str:>8} {est_str:>8} {surp_str:>6} {comp_str:>6} {per_str:<6}")
        
        if '_mom' in event_key.lower():
            has_mom = True
            if surprise and surprise > 20:
                significant_surprise = True
        
        if '_yoy' in event_key.lower():
            has_yoy = True
    
    print("\n[3] Validation :")
    print("-"*90)
    
    if has_mom:
        print("   ✅ Version MoM détectée")
    else:
        print("   ❌ Version MoM MANQUANTE")
    
    if has_yoy:
        print("   ✅ Version YoY détectée")
    else:
        print("   ❌ Version YoY MANQUANTE")
    
    if significant_surprise:
        print("   ✅ Surprise significative (>20%) détectée sur MoM")
    else:
        print("   ⚠️  Pas de surprise significative")
    
    if has_mom and has_yoy and significant_surprise:
        print("\n   🎉 SUCCÈS COMPLET : Données correctes avec distinction MoM/YoY !")
    
else:
    print("   ❌ Aucun événement inflation trouvé")

# Stats globales sur comparison
print("\n[4] Statistiques globales MoM/YoY/QoQ :")
print("-"*90)

comp_stats = conn.execute("""
    SELECT 
        comparison,
        COUNT(*) as count
    FROM events
    WHERE comparison IS NOT NULL
    GROUP BY comparison
    ORDER BY count DESC
""").fetchall()

for comp, count in comp_stats:
    print(f"   {comp:<10} : {count:>5} événements")

# Events avec inflation et comparison
inflation_comp = conn.execute("""
    SELECT 
        comparison,
        COUNT(*) as count
    FROM events
    WHERE event_key LIKE '%inflation%'
      AND comparison IS NOT NULL
    GROUP BY comparison
    ORDER BY count DESC
""").fetchall()

print("\n   Dans événements 'inflation' :")
for comp, count in inflation_comp:
    print(f"   {comp:<10} : {count:>5} événements")

conn.close()

print("\n" + "="*90)
print("Fin de la vérification")
print("="*90)
