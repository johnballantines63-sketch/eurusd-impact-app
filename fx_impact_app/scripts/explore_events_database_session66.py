"""
Script exploratoire de la base de données events
Session 66
Date: 24 octobre 2025

Objectif: Comprendre la structure réelle des données pour ajuster les requêtes
"""

import duckdb
import sys
from pathlib import Path
import pandas as pd

# Chemin base de données
DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"

def explore_events_structure():
    """Explore la structure de la table events."""
    
    conn = duckdb.connect(str(DB_PATH))
    
    print("="*80)
    print("EXPLORATION TABLE EVENTS")
    print("="*80)
    print()
    
    # 1. Schéma table
    print("1. Schéma de la table events:")
    schema = conn.execute("PRAGMA table_info(events)").fetchdf()
    print(schema.to_string())
    print()
    
    # 2. Nombre total événements
    print("2. Statistiques générales:")
    total = conn.execute("SELECT COUNT(*) as total FROM events").fetchdf()
    print(f"   Total événements: {total['total'][0]:,}")
    
    # 3. Événements US
    us_events = conn.execute("SELECT COUNT(*) as total FROM events WHERE country = 'US'").fetchdf()
    print(f"   Événements US: {us_events['total'][0]:,}")
    
    # 4. Événements avec actual/estimate non NULL
    with_data = conn.execute("""
        SELECT COUNT(*) as total 
        FROM events 
        WHERE country = 'US' 
          AND actual IS NOT NULL 
          AND estimate IS NOT NULL
    """).fetchdf()
    print(f"   Événements US avec actual+estimate: {with_data['total'][0]:,}")
    print()
    
    # 5. Labels uniques (top 50)
    print("3. Top 50 labels événements US:")
    labels = conn.execute("""
        SELECT label, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND actual IS NOT NULL
        GROUP BY label
        ORDER BY count DESC
        LIMIT 50
    """).fetchdf()
    print(labels.to_string(index=False))
    print()
    
    # 6. Labels contenant "CPI"
    print("4. Labels contenant 'CPI':")
    cpi_labels = conn.execute("""
        SELECT label, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND label LIKE '%CPI%'
          AND actual IS NOT NULL
        GROUP BY label
        ORDER BY count DESC
    """).fetchdf()
    if len(cpi_labels) > 0:
        print(cpi_labels.to_string(index=False))
    else:
        print("   ⚠️ AUCUN label contenant 'CPI'")
    print()
    
    # 7. Labels contenant "Consumer Price"
    print("5. Labels contenant 'Consumer Price':")
    consumer_labels = conn.execute("""
        SELECT label, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND label LIKE '%Consumer Price%'
          AND actual IS NOT NULL
        GROUP BY label
        ORDER BY count DESC
    """).fetchdf()
    if len(consumer_labels) > 0:
        print(consumer_labels.to_string(index=False))
    else:
        print("   ⚠️ AUCUN label contenant 'Consumer Price'")
    print()
    
    # 8. Labels contenant "Payroll" ou "NFP"
    print("6. Labels contenant 'Payroll' ou 'NFP':")
    nfp_labels = conn.execute("""
        SELECT label, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (label LIKE '%Payroll%' OR label LIKE '%NFP%')
          AND actual IS NOT NULL
        GROUP BY label
        ORDER BY count DESC
    """).fetchdf()
    if len(nfp_labels) > 0:
        print(nfp_labels.to_string(index=False))
    else:
        print("   ⚠️ AUCUN label contenant 'Payroll' ou 'NFP'")
    print()
    
    # 9. Labels contenant "Fed" ou "FOMC"
    print("7. Labels contenant 'Fed' ou 'FOMC':")
    fed_labels = conn.execute("""
        SELECT label, COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND (label LIKE '%Fed%' OR label LIKE '%FOMC%')
          AND actual IS NOT NULL
        GROUP BY label
        ORDER BY count DESC
        LIMIT 20
    """).fetchdf()
    if len(fed_labels) > 0:
        print(fed_labels.to_string(index=False))
    else:
        print("   ⚠️ AUCUN label contenant 'Fed' ou 'FOMC'")
    print()
    
    # 10. Distribution importance
    print("8. Distribution importance_n:")
    importance = conn.execute("""
        SELECT 
            importance_n,
            COUNT(*) as count
        FROM events
        WHERE country = 'US'
          AND actual IS NOT NULL
        GROUP BY importance_n
        ORDER BY importance_n
    """).fetchdf()
    print(importance.to_string(index=False))
    print()
    
    # 11. Exemple événements 11 septembre 2025
    print("9. Événements 11 septembre 2025 (cas référence):")
    sept11 = conn.execute("""
        SELECT 
            label,
            ts_utc,
            actual,
            estimate,
            forecast,
            previous,
            importance_n
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND country = 'US'
        ORDER BY ts_utc
    """).fetchdf()
    if len(sept11) > 0:
        print(sept11.to_string(index=False))
        print(f"\n   Total: {len(sept11)} événements")
    else:
        print("   ⚠️ AUCUN événement le 11 septembre 2025")
    print()
    
    # 12. Dates avec clusters importants (≥5 événements même heure)
    print("10. Dates avec clusters ≥5 événements (2022-2025):")
    clusters = conn.execute("""
        SELECT 
            DATE(ts_utc) as event_date,
            ts_utc,
            COUNT(*) as num_events,
            STRING_AGG(DISTINCT label, ' | ') as labels
        FROM events
        WHERE country = 'US'
          AND DATE(ts_utc) BETWEEN '2022-01-01' AND '2025-12-31'
          AND actual IS NOT NULL
        GROUP BY DATE(ts_utc), ts_utc
        HAVING COUNT(*) >= 5
        ORDER BY num_events DESC
        LIMIT 20
    """).fetchdf()
    if len(clusters) > 0:
        print(clusters.to_string(index=False))
    else:
        print("   ⚠️ AUCUN cluster trouvé")
    print()
    
    # 13. Calcul surprise sur quelques événements
    print("11. Exemples calcul surprise (échantillon):")
    surprise_sample = conn.execute("""
        SELECT 
            label,
            DATE(ts_utc) as date,
            actual,
            estimate,
            ROUND(ABS((actual - estimate) / NULLIF(estimate, 0)) * 100, 2) as surprise_pct,
            importance_n
        FROM events
        WHERE country = 'US'
          AND actual IS NOT NULL
          AND estimate IS NOT NULL
          AND estimate != 0
          AND DATE(ts_utc) BETWEEN '2024-01-01' AND '2025-12-31'
        ORDER BY surprise_pct DESC
        LIMIT 20
    """).fetchdf()
    if len(surprise_sample) > 0:
        print(surprise_sample.to_string(index=False))
    else:
        print("   ⚠️ AUCUN événement avec surprise calculable")
    
    conn.close()
    
    print()
    print("="*80)
    print("EXPLORATION TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    explore_events_structure()
