#!/usr/bin/env python3
"""
Création de la vue daily_vol_regime_features_v1
================================================

Features régime de volatilité (strictement ex-ante avec lag 1 jour).
Toutes les features basées sur vol_pips_lag1 = LAG(daily_volatility_pips_v1, 1).
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

VOL_VIEW = "daily_eurusd_volatility_v1"
VIEW_NAME = "daily_vol_regime_features_v1"


def create_view(conn):
    """Crée la vue daily_vol_regime_features_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    WITH vol_lagged AS (
        SELECT
            date,
            daily_volatility_pips_v1 AS vol_pips,
            LAG(daily_volatility_pips_v1, 1) OVER (ORDER BY date) AS vol_pips_lag1
        FROM {VOL_VIEW}
        ORDER BY date
    ),
    vol_stats AS (
        SELECT
            date,
            vol_pips,
            vol_pips_lag1,
            -- Moyennes rolling 20 jours (lag1)
            AVG(vol_pips_lag1) OVER (
                ORDER BY date 
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) AS vol_mean_20_lag1,
            -- Std rolling 20 jours (lag1)
            STDDEV_SAMP(vol_pips_lag1) OVER (
                ORDER BY date 
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) AS vol_std_20_lag1,
            -- Moyennes rolling 60 jours (lag1)
            AVG(vol_pips_lag1) OVER (
                ORDER BY date 
                ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING
            ) AS vol_mean_60_lag1,
            -- Std rolling 60 jours (lag1)
            STDDEV_SAMP(vol_pips_lag1) OVER (
                ORDER BY date 
                ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING
            ) AS vol_std_60_lag1
        FROM vol_lagged
    )
    SELECT
        date,
        vol_pips,  -- Du jour, pour debug
        vol_pips_lag1,
        vol_mean_20_lag1,
        vol_std_20_lag1,
        vol_mean_60_lag1,
        vol_std_60_lag1,
        -- Z-scores (lag1)
        (vol_pips_lag1 - vol_mean_20_lag1) / NULLIF(vol_std_20_lag1, 0) AS vol_z_20_lag1,
        (vol_pips_lag1 - vol_mean_60_lag1) / NULLIF(vol_std_60_lag1, 0) AS vol_z_60_lag1,
        -- Régimes (lag1)
        CASE 
            WHEN (vol_pips_lag1 - vol_mean_60_lag1) / NULLIF(vol_std_60_lag1, 0) >= 1.0 
            THEN 1 
            ELSE 0 
        END AS regime_high_60_lag1,
        CASE 
            WHEN (vol_pips_lag1 - vol_mean_60_lag1) / NULLIF(vol_std_60_lag1, 0) <= -1.0 
            THEN 1 
            ELSE 0 
        END AS regime_low_60_lag1
    FROM vol_stats
    ORDER BY date
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. vol_pips_lag1 est NULL uniquement sur la première date
    df_first = conn.execute(f"""
        SELECT 
            date,
            vol_pips_lag1
        FROM {VIEW_NAME}
        ORDER BY date
        LIMIT 5
    """).df()
    
    print("📊 Premières dates (vérification lag):")
    print(df_first.to_string(index=False))
    
    n_null_lag1 = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE vol_pips_lag1 IS NULL
    """).fetchone()[0]
    
    if n_null_lag1 <= 1:
        print(f"\n✅ vol_pips_lag1 NULL uniquement sur première date ({n_null_lag1} lignes)")
    else:
        print(f"\n⚠️  {n_null_lag1} lignes avec vol_pips_lag1 IS NULL (attendu ≤ 1)")
    
    # 2. vol_mean_20_lag1 est NULL sur les ~21 premières dates (normal)
    n_null_mean20 = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE vol_mean_20_lag1 IS NULL
    """).fetchone()[0]
    
    if 20 <= n_null_mean20 <= 25:
        print(f"✅ vol_mean_20_lag1 NULL sur {n_null_mean20} premières dates (attendu ~21)")
    else:
        print(f"⚠️  vol_mean_20_lag1 NULL sur {n_null_mean20} dates (attendu ~21)")
    
    # 3. vol_z_60_lag1 est NULL quand vol_pips_lag1 est NULL
    n_null_z60 = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE vol_z_60_lag1 IS NULL AND vol_pips_lag1 IS NOT NULL
    """).fetchone()[0]
    
    if n_null_z60 == 0:
        print(f"✅ vol_z_60_lag1 NULL uniquement quand vol_pips_lag1 NULL")
    else:
        print(f"⚠️  {n_null_z60} lignes avec vol_z_60_lag1 NULL mais vol_pips_lag1 NOT NULL")
    
    # 4. Head/Tail
    print("\n📊 Head 5:")
    df_head = conn.execute(f"""
        SELECT 
            date,
            vol_pips,
            vol_pips_lag1,
            ROUND(vol_mean_20_lag1, 2) AS vol_mean_20,
            ROUND(vol_z_60_lag1, 2) AS vol_z_60,
            regime_high_60_lag1,
            regime_low_60_lag1
        FROM {VIEW_NAME}
        ORDER BY date
        LIMIT 5
    """).df()
    print(df_head.to_string(index=False))
    
    print("\n📊 Tail 5:")
    df_tail = conn.execute(f"""
        SELECT 
            date,
            vol_pips,
            vol_pips_lag1,
            ROUND(vol_mean_20_lag1, 2) AS vol_mean_20,
            ROUND(vol_z_60_lag1, 2) AS vol_z_60,
            regime_high_60_lag1,
            regime_low_60_lag1
        FROM {VIEW_NAME}
        ORDER BY date DESC
        LIMIT 5
    """).df()
    print(df_tail.to_string(index=False))
    
    # 5. Count NULLs
    print("\n📊 Comptage NULLs:")
    df_nulls = conn.execute(f"""
        SELECT
            COUNT(*) AS n_total,
            COUNT(vol_pips_lag1) AS n_vol_lag1,
            COUNT(vol_mean_20_lag1) AS n_mean_20,
            COUNT(vol_mean_60_lag1) AS n_mean_60,
            COUNT(vol_z_60_lag1) AS n_z_60,
            COUNT(regime_high_60_lag1) AS n_regime_high
        FROM {VIEW_NAME}
    """).df()
    print(df_nulls.to_string(index=False))
    
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
        print("CRÉATION DAILY_VOL_REGIME_FEATURES_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # Créer vue
        create_view(conn)
        
        # Sanity checks
        if not sanity_checks(conn):
            print("\n❌ SANITY CHECKS ÉCHOUÉS")
            sys.exit(1)
        
        print("\n✅ Vue daily_vol_regime_features_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

