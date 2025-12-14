#!/usr/bin/env python3
"""
Création de la vue daily_pred_score_v3_2_dataset_v1
====================================================

Dataset V3.2 : V3.1 + densité informationnelle (n_us_events_day).
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

V3_1_DATASET_VIEW = "daily_pred_score_v3_1_dataset_v1"
EVENTS_VIEW = "events_with_ts_local_v1"
VIEW_NAME = "daily_pred_score_v3_2_dataset_v1"


def create_view(conn):
    """Crée la vue daily_pred_score_v3_2_dataset_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    WITH density_features AS (
        SELECT
            DATE(ts_local) AS date,
            COUNT(CASE WHEN country = 'US' THEN 1 END) AS n_us_events_day,
            COUNT(*) AS n_events_day,
            COUNT(DISTINCT ts_local || '|' || country) AS n_ts_country_groups_day
        FROM {EVENTS_VIEW}
        GROUP BY DATE(ts_local)
    )
    SELECT
        v3_1.*,
        -- Densité informationnelle
        COALESCE(d.n_us_events_day, 0) AS n_us_events_day,
        COALESCE(d.n_events_day, 0) AS n_events_day,
        COALESCE(d.n_ts_country_groups_day, 0) AS n_ts_country_groups_day
    FROM {V3_1_DATASET_VIEW} v3_1
    LEFT JOIN density_features d ON v3_1.date = d.date
    ORDER BY v3_1.date
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. COUNT(*) identique à V3.1
    n_v3_1 = conn.execute(f"SELECT COUNT(*) FROM {V3_1_DATASET_VIEW}").fetchone()[0]
    n_v3_2 = conn.execute(f"SELECT COUNT(*) FROM {VIEW_NAME}").fetchone()[0]
    
    if n_v3_1 == n_v3_2:
        print(f"✅ Nombre de lignes identique à V3.1: {n_v3_2}")
    else:
        print(f"❌ ERREUR: V3.1={n_v3_1} vs V3.2={n_v3_2}")
        return False
    
    # 2. Pas de NULL sur n_us_events_day
    n_null = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE n_us_events_day IS NULL
    """).fetchone()[0]
    
    if n_null == 0:
        print(f"✅ Pas de NULL sur n_us_events_day")
    else:
        print(f"❌ ERREUR: {n_null} lignes avec n_us_events_day IS NULL")
        return False
    
    # 3. Stats n_us_events_day
    print("\n📊 Statistiques n_us_events_day:")
    df_stats = conn.execute(f"""
        SELECT
            COUNT(*) AS n_days,
            ROUND(MIN(n_us_events_day), 0) AS min_us_events,
            ROUND(MEDIAN(n_us_events_day), 1) AS p50_us_events,
            ROUND(MAX(n_us_events_day), 0) AS max_us_events,
            ROUND(AVG(n_us_events_day), 1) AS avg_us_events
        FROM {VIEW_NAME}
    """).df()
    print(df_stats.to_string(index=False))
    
    print("\n" + "=" * 100)
    return True


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    # Gérer lock DuckDB avec retry
    import time
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = duckdb.connect(str(DB_PATH), read_only=False)
            break
        except Exception as e:
            if "lock" in str(e).lower() and i < max_retries - 1:
                print(f"⚠️  Lock détecté, attente 3s... (tentative {i+1}/{max_retries})")
                time.sleep(3)
            else:
                raise
    
    try:
        print("=" * 100)
        print("CRÉATION DAILY_PRED_SCORE_V3_2_DATASET_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # Créer vue
        create_view(conn)
        
        # Sanity checks
        if not sanity_checks(conn):
            print("\n❌ SANITY CHECKS ÉCHOUÉS")
            sys.exit(1)
        
        print("\n✅ Vue daily_pred_score_v3_2_dataset_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

