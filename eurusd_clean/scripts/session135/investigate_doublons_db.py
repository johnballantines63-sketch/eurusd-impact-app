"""
INVESTIGATION DOUBLONS DB - Analyse complète
============================================

Examine si les "doublons" sont vrais doublons ou variantes légitimes
(MoM, YoY, QoQ, s.a., etc.)

Session 135
"""

import duckdb
from pathlib import Path
import sys
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import config
DB_PATH = config.DB_PATH

print("="*80)
print("INVESTIGATION DOUBLONS DB - Analyse détaillée")
print("="*80)
print()

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Dates à investiguer
dates_investigate = [
    ('2025-01-10', 'OUTLIER'),
    ('2025-09-11', 'STANDARD'),
]

for date_str, type_cas in dates_investigate:
    print("="*80)
    print(f"DATE : {date_str} ({type_cas})")
    print("="*80)
    print()
    
    # Charger TOUS les événements HIGH avec TOUTES les colonnes
    query = """
    SELECT 
        e.ts_utc,
        e.country,
        e.event_title,
        e.event_key,
        e.importance_n,
        e.actual,
        e.previous,
        e.estimate,
        e.forecast,
        e.unit,
        e.type,
        e.label,
        e.comparison,
        e.period,
        e.change,
        e.change_percentage,
        e.event_type,
        f.empirical_score
    FROM events e
    LEFT JOIN event_families f
        ON e.event_key = f.event_key
        AND e.country = f.country
    WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
      AND f.empirical_score > 40.0
    ORDER BY e.ts_utc, e.event_title, e.event_key
    """
    
    df = conn.execute(query, [date_str]).df()
    
    print(f"✅ {len(df)} événements HIGH trouvés (score > 40)")
    print()
    
    # Grouper par event_title pour trouver potentiels doublons
    event_groups = df.groupby('event_title')
    
    doublons_trouves = False
    
    for event_title, group in event_groups:
        if len(group) > 1:
            doublons_trouves = True
            print(f"🔍 ÉVÉNEMENT : {event_title} ({len(group)} occurrences)")
            print("-" * 80)
            print()
            
            # Afficher TOUTES les colonnes pour chaque occurrence
            for idx, row in group.iterrows():
                ts_str = row['ts_utc'].strftime('%H:%M:%S') if hasattr(row['ts_utc'], 'strftime') else str(row['ts_utc'])
                
                print(f"  Occurrence #{group.index.get_loc(idx) + 1}:")
                print(f"    Heure       : {ts_str}")
                print(f"    Pays        : {row['country']}")
                print(f"    event_key   : {row['event_key']}")
                print(f"    event_title : {row['event_title']}")
                print(f"    Score       : {row['empirical_score']}")
                print(f"    Actual      : {row['actual']}")
                print(f"    Estimate    : {row['estimate']}")
                print(f"    Forecast    : {row['forecast']}")
                print(f"    Previous    : {row['previous']}")
                print(f"    Unit        : {row['unit']}")
                print(f"    Type        : {row['type']}")
                print(f"    Label       : {row['label']}")
                print(f"    Comparison  : {row['comparison']}")
                print(f"    Period      : {row['period']}")
                print(f"    Change      : {row['change']}")
                print(f"    Change %    : {row['change_percentage']}")
                print(f"    Event type  : {row['event_type']}")
                print()
            
            # Analyse : vrais doublons ou variantes ?
            unique_keys = group['event_key'].nunique()
            unique_actuals = group['actual'].nunique()
            unique_types = group['type'].nunique()
            unique_labels = group['label'].nunique()
            
            print(f"  📊 ANALYSE :")
            print(f"    event_key uniques : {unique_keys}/{len(group)}")
            print(f"    actual uniques    : {unique_actuals}/{len(group)}")
            print(f"    type uniques      : {unique_types}/{len(group)}")
            print(f"    label uniques     : {unique_labels}/{len(group)}")
            
            if unique_keys == 1 and unique_actuals == 1 and unique_types == 1:
                print(f"    ❌ PROBABLE VRAI DOUBLON (toutes colonnes identiques)")
            elif unique_keys > 1:
                print(f"    ✅ VARIANTES LÉGITIMES (event_key différents : {', '.join(group['event_key'].unique())})")
            else:
                print(f"    ⚠️  À INVESTIGUER (colonnes partiellement différentes)")
            
            print()
            print("-" * 80)
            print()
    
    if not doublons_trouves:
        print("✅ Aucun doublon trouvé (tous les event_title uniques)")
    
    print()

conn.close()

print("="*80)
print()
print("💡 LÉGENDE :")
print("   ✅ VARIANTES LÉGITIMES : event_key différents (ex: cpi_mom vs cpi_yoy)")
print("   ❌ VRAIS DOUBLONS      : toutes colonnes identiques, à dédupliquer")
print("   ⚠️  À INVESTIGUER      : colonnes partiellement différentes")
print()
print("="*80)
print("✅ INVESTIGATION TERMINÉE")
print("="*80)
