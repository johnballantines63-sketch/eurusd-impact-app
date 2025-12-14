"""
Script de diagnostic pour identifier le problème
"""

import duckdb
import sys
from pathlib import Path

project_root = Path(__file__).parent
fx_app_src = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(fx_app_src))

try:
    from config import get_db_path
except ImportError:
    def get_db_path():
        return str(project_root / "fx_impact_app" / "data" / "warehouse.duckdb")

try:
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    print("=" * 80)
    print("DIAGNOSTIC - Événements dans la base de données")
    print("=" * 80)
    print()
    
    # 1. Total événements
    total = conn.execute("SELECT COUNT(*) as total FROM events").df()
    print(f"1. Total événements : {total['total'].iloc[0]}")
    
    # 2. Événements avec actual non NULL
    with_actual = conn.execute("""
        SELECT COUNT(*) as total FROM events 
        WHERE actual IS NOT NULL
    """).df()
    print(f"2. Événements avec actual non NULL : {with_actual['total'].iloc[0]}")
    
    # 3. Événements EUR/USD pertinents
    eur_usd = conn.execute("""
        SELECT COUNT(*) as total FROM events 
        WHERE actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
    """).df()
    print(f"3. Événements EUR/USD avec actual : {eur_usd['total'].iloc[0]}")
    
    # 4. Événements avec importance >= 2
    important = conn.execute("""
        SELECT COUNT(*) as total FROM events 
        WHERE actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        AND importance_n >= 2
    """).df()
    print(f"4. Événements importance >= 2 : {important['total'].iloc[0]}")
    
    # 5. Événements avec forecast ou estimate disponible (pour calculer surprise)
    with_forecast = conn.execute("""
        SELECT COUNT(*) as total FROM events 
        WHERE actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        AND importance_n >= 2
        AND (forecast IS NOT NULL OR estimate IS NOT NULL)
    """).df()
    print(f"5. Événements avec forecast/estimate : {with_forecast['total'].iloc[0]}")
    print()
    
    # 6. Distribution des importance_n
    print("=" * 80)
    print("Distribution des importance_n :")
    print("=" * 80)
    distrib = conn.execute("""
        SELECT 
            importance_n, 
            COUNT(*) as count
        FROM events 
        WHERE actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        GROUP BY importance_n
        ORDER BY importance_n
    """).df()
    print(distrib)
    print()
    
    # 7. Exemples d'événements récents
    print("=" * 80)
    print("Exemples d'événements récents (10 derniers) :")
    print("=" * 80)
    recent = conn.execute("""
        SELECT 
            ts_utc,
            event_title,
            country,
            importance_n,
            actual,
            forecast,
            estimate
        FROM events 
        WHERE actual IS NOT NULL
        AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        ORDER BY ts_utc DESC
        LIMIT 10
    """).df()
    print(recent.to_string())
    print()
    
    # 8. Chercher des événements proches (gap <= 60 min pour voir)
    print("=" * 80)
    print("Paires d'événements proches (gap <= 60 min) :")
    print("=" * 80)
    pairs = conn.execute("""
    WITH events_with_lag AS (
        SELECT 
            ts_utc,
            event_title,
            country,
            importance_n,
            LAG(ts_utc) OVER (ORDER BY ts_utc) as prev_time,
            EXTRACT(EPOCH FROM (ts_utc - LAG(ts_utc) OVER (ORDER BY ts_utc))) / 60 as gap_minutes
        FROM events
        WHERE actual IS NOT NULL
            AND (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
            AND (forecast IS NOT NULL OR estimate IS NOT NULL)
        ORDER BY ts_utc DESC
        LIMIT 1000
    )
    SELECT 
        prev_time,
        ts_utc,
        gap_minutes,
        event_title,
        country,
        importance_n
    FROM events_with_lag
    WHERE gap_minutes <= 60
        AND gap_minutes > 0
    ORDER BY ts_utc DESC
    LIMIT 20
    """).df()
    
    if len(pairs) > 0:
        print(pairs.to_string())
        print()
        print(f"✅ Trouvé {len(pairs)} paires d'événements proches")
        
        # Analyser les gaps
        gaps_15 = len(pairs[pairs['gap_minutes'] <= 15])
        gaps_30 = len(pairs[(pairs['gap_minutes'] > 15) & (pairs['gap_minutes'] <= 30)])
        gaps_60 = len(pairs[(pairs['gap_minutes'] > 30) & (pairs['gap_minutes'] <= 60)])
        
        print(f"   - Gap <= 15 min : {gaps_15}")
        print(f"   - Gap 15-30 min : {gaps_30}")
        print(f"   - Gap 30-60 min : {gaps_60}")
    else:
        print("❌ Aucune paire d'événements trouvée avec gap <= 60 min")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
