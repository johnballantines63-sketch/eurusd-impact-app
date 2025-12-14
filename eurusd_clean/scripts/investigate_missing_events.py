"""
Script pour investiguer pourquoi les événements ne sont pas trouvés pour certaines dates
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from datetime import datetime
import pytz

# Ajouter le chemin du projet
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Utiliser le chemin DB standard
DB_PATH = PROJECT_ROOT / 'data' / 'warehouse.duckdb'
if not DB_PATH.exists():
    # Essayer un autre chemin
    DB_PATH = PROJECT_ROOT / 'warehouse.duckdb'

conn = duckdb.connect(str(DB_PATH), read_only=True)

# Dates à vérifier
dates = ['2025-11-26', '2025-10-10', '2025-09-11', '2025-06-23']

for date_str in dates:
    print(f'\n{"="*80}')
    print(f'📅 DATE : {date_str}')
    print(f'{"="*80}')
    
    # Chercher tous les événements (sans seuil) - Utiliser la même structure que load_high_impact_events
    query = f"""
    SELECT 
        e.event_key, 
        e.country, 
        e.importance_n, 
        ef.empirical_score, 
        e.ts_utc,
        e.actual,
        e.estimate,
        e.forecast
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = DATE '{date_str}'
    ORDER BY ef.empirical_score DESC NULLS LAST
    LIMIT 20
    """
    
    try:
        df = conn.execute(query).df()
        print(f'\n✅ Événements trouvés dans la base: {len(df)}')
        
        if not df.empty:
            print(f'\n📊 Distribution des scores empiriques:')
            print(f'   Scores >= 40.0: {len(df[df["empirical_score"] >= 40.0])}')
            print(f'   Scores >= 20.0: {len(df[df["empirical_score"] >= 20.0])}')
            print(f'   Scores < 20.0: {len(df[df["empirical_score"] < 20.0])}')
            print(f'   Scores NULL: {len(df[df["empirical_score"].isna()])}')
            
            print(f'\n📋 Top 10 événements:')
            print(df[['event_key', 'country', 'importance_n', 'empirical_score']].head(10).to_string(index=False))
            
            # Vérifier avec load_high_impact_events
            from src.core.event_loader import load_high_impact_events
            from datetime import datetime
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Test avec seuil 40.0 (US/EU)
            events_us = load_high_impact_events(
                db_path=DB_PATH,
                target_date=date_obj,
                country='US',
                min_empirical_score=40.0,
                verbose=False
            )
            events_eu = load_high_impact_events(
                db_path=DB_PATH,
                target_date=date_obj,
                country='EU',
                min_empirical_score=40.0,
                verbose=False
            )
            events_de = load_high_impact_events(
                db_path=DB_PATH,
                target_date=date_obj,
                country='DE',
                min_empirical_score=20.0,
                verbose=False
            )
            
            print(f'\n🔍 Résultats load_high_impact_events:')
            print(f'   US (seuil 40.0): {len(events_us)} événements')
            print(f'   EU (seuil 40.0): {len(events_eu)} événements')
            print(f'   DE (seuil 20.0): {len(events_de)} événements')
            print(f'   TOTAL: {len(events_us) + len(events_eu) + len(events_de)} événements')
            
            if len(events_us) + len(events_eu) + len(events_de) == 0:
                print(f'\n⚠️ PROBLÈME : Aucun événement trouvé avec les seuils actuels')
                print(f'   → Score max disponible: {df["empirical_score"].max():.2f}')
                print(f'   → Suggestion: Réduire le seuil à {max(20.0, df["empirical_score"].max() - 5):.1f} pour cette date')
        else:
            print(f'\n❌ Aucun événement dans la base pour cette date')
            print(f'   → Date peut-être dans le futur (pas encore arrivée)')
            print(f'   → Ou événements non importés')
            
    except Exception as e:
        print(f'\n❌ Erreur: {e}')
        import traceback
        traceback.print_exc()

conn.close()

