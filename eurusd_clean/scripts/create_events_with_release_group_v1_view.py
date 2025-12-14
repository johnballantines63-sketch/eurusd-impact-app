#!/usr/bin/env python3
"""
Création de la vue events_with_release_group_v1
================================================

Ajoute release_family_v1 et release_group_id_v1 à events_with_ts_local_v1.

Approche:
1. Matérialiser une table release_family_map_v1 depuis les event_key uniques
2. Créer la vue avec LEFT JOIN + fallback
"""

import sys
from pathlib import Path
import duckdb
import hashlib

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

# Import release_family_v1 function
sys.path.insert(0, str(PROJECT_ROOT))
from src.core.release_family_v1 import release_family_v1

EVENTS_VIEW = "events_with_ts_local_v1"
MAP_TABLE = "release_family_map_v1"
VIEW_NAME = "events_with_release_group_v1"


def create_release_family_map(conn):
    """Crée la table release_family_map_v1 depuis les event_key uniques."""
    print("📊 Extraction des event_key uniques...")
    df_keys = conn.execute(f"""
        SELECT DISTINCT 
            event_key,
            MAX(event_title) AS event_title_sample
        FROM {EVENTS_VIEW}
        GROUP BY event_key
        ORDER BY event_key
    """).df()
    
    print(f"  → {len(df_keys)} event_key uniques trouvés\n")
    
    # Calculer release_family pour chaque event_key
    print("🔧 Calcul release_family_v1...")
    df_keys['release_family_v1'] = df_keys.apply(
        lambda row: release_family_v1(row['event_key'], row.get('event_title_sample')),
        axis=1
    )
    
    # Créer/remplacer la table
    print(f"💾 Création table {MAP_TABLE}...")
    conn.execute(f"DROP TABLE IF EXISTS {MAP_TABLE}")
    conn.execute(f"""
        CREATE TABLE {MAP_TABLE} AS
        SELECT 
            event_key,
            release_family_v1
        FROM df_keys
    """)
    
    print(f"  ✅ Table {MAP_TABLE} créée ({len(df_keys)} lignes)\n")
    
    # Stats
    print("📊 Distribution release_family_v1 (top 20):")
    df_stats = conn.execute(f"""
        SELECT 
            release_family_v1,
            COUNT(*) AS n_event_keys
        FROM {MAP_TABLE}
        GROUP BY release_family_v1
        ORDER BY n_event_keys DESC
        LIMIT 20
    """).df()
    print(df_stats.to_string(index=False))
    print()


def create_view(conn):
    """Crée la vue events_with_release_group_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    SELECT
        e.*,
        COALESCE(m.release_family_v1, e.event_key) AS release_family_v1,
        -- release_group_id_v1 = md5(country || '|' || ts_local || '|' || release_family_v1)
        MD5(
            COALESCE(e.country, '') || '|' || 
            CAST(e.ts_local AS VARCHAR) || '|' || 
            COALESCE(m.release_family_v1, e.event_key)
        ) AS release_group_id_v1
    FROM {EVENTS_VIEW} e
    LEFT JOIN {MAP_TABLE} m
        ON e.event_key = m.event_key
    ORDER BY e.ts_local, e.country, e.event_key
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. Nombre de lignes identique
    n_events = conn.execute(f"SELECT COUNT(*) FROM {EVENTS_VIEW}").fetchone()[0]
    n_release = conn.execute(f"SELECT COUNT(*) FROM {VIEW_NAME}").fetchone()[0]
    
    if n_events == n_release:
        print(f"✅ Nombre de lignes identique: {n_events}")
    else:
        print(f"❌ ERREUR: {EVENTS_VIEW}={n_events} vs {VIEW_NAME}={n_release}")
        return False
    
    # 2. release_family_v1 IS NOT NULL pour 100%
    n_null = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE release_family_v1 IS NULL
    """).fetchone()[0]
    
    if n_null == 0:
        print(f"✅ release_family_v1 IS NOT NULL: 100%")
    else:
        print(f"❌ ERREUR: {n_null} lignes avec release_family_v1 IS NULL")
        return False
    
    # 3. Dates repères: n_events vs n_release_groups
    print("\n📊 Dates repères (n_events vs n_release_groups):")
    test_dates = [
        ("2025-09-11", "14:30"),  # CPI US
        ("2025-08-01", "14:30"),  # NFP US
        ("2024-09-11", "14:30"),  # CPI US
        ("2024-08-02", "14:30"),  # NFP US
    ]
    
    for date_str, hour_str in test_dates:
        ts_pattern = f"{date_str} {hour_str}%"
        
        df_before = conn.execute(f"""
            SELECT COUNT(*) AS n_events
            FROM {EVENTS_VIEW}
            WHERE CAST(ts_local AS VARCHAR) LIKE '{ts_pattern}'
        """).df()
        
        df_after = conn.execute(f"""
            SELECT 
                COUNT(*) AS n_events,
                COUNT(DISTINCT release_group_id_v1) AS n_release_groups
            FROM {VIEW_NAME}
            WHERE CAST(ts_local AS VARCHAR) LIKE '{ts_pattern}'
        """).df()
        
        if not df_before.empty and not df_after.empty:
            n_evt = df_before.iloc[0]['n_events']
            n_evt_after = df_after.iloc[0]['n_events']
            n_groups = df_after.iloc[0]['n_release_groups']
            
            if n_evt == n_evt_after:
                ratio = n_groups / n_evt if n_evt > 0 else 0
                print(f"  {date_str} {hour_str}: {n_evt} events → {n_groups} groups (ratio: {ratio:.2f})")
                
                if n_groups > n_evt:
                    print(f"    ⚠️  WARNING: n_groups > n_events")
            else:
                print(f"  ❌ ERREUR: {date_str} {hour_str} - comptage incohérent")
    
    # 4. Unicité release_group_id_v1 pour (country, ts_local, release_family_v1)
    print("\n🔍 Vérification unicité release_group_id_v1...")
    df_dup = conn.execute(f"""
        SELECT 
            country,
            ts_local,
            release_family_v1,
            COUNT(DISTINCT release_group_id_v1) AS n_ids
        FROM {VIEW_NAME}
        GROUP BY country, ts_local, release_family_v1
        HAVING COUNT(DISTINCT release_group_id_v1) > 1
        LIMIT 10
    """).df()
    
    if df_dup.empty:
        print("  ✅ Unicité release_group_id_v1 validée")
    else:
        print(f"  ❌ ERREUR: {len(df_dup)} violations d'unicité")
        print(df_dup.to_string(index=False))
        return False
    
    # 5. Top 20 dates avec plus de lignes (avant/après)
    print("\n📊 Top 20 dates par nombre d'événements (avant/après regroupement):")
    df_top = conn.execute(f"""
        SELECT 
            DATE(ts_local) AS date,
            country,
            COUNT(*) AS n_events,
            COUNT(DISTINCT release_group_id_v1) AS n_release_groups,
            ROUND(COUNT(*)::DOUBLE / NULLIF(COUNT(DISTINCT release_group_id_v1), 0), 2) AS ratio
        FROM {VIEW_NAME}
        GROUP BY DATE(ts_local), country
        ORDER BY n_events DESC
        LIMIT 20
    """).df()
    print(df_top.to_string(index=False))
    
    print("\n" + "=" * 100)
    return True


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    try:
        print("=" * 100)
        print("CRÉATION EVENTS_WITH_RELEASE_GROUP_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # 1. Créer table mapping
        create_release_family_map(conn)
        
        # 2. Créer vue
        create_view(conn)
        
        # 3. Sanity checks
        if not sanity_checks(conn):
            print("\n❌ SANITY CHECKS ÉCHOUÉS")
            sys.exit(1)
        
        print("\n✅ Vue events_with_release_group_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
