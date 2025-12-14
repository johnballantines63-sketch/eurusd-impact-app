#!/usr/bin/env python3
"""
Création de la vue daily_pred_score_v3_1_dataset_v1
====================================================

Dataset combiné V3.1 : score V2.1 + calendrier + régime + target.
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

V2_VIEW = "daily_pred_score_release_group_v1"
CAL_VIEW = "daily_calendar_features_v1"
REGIME_VIEW = "daily_vol_regime_features_v1"
VOL_VIEW = "daily_eurusd_volatility_v1"
VIEW_NAME = "daily_pred_score_v3_1_dataset_v1"


def create_view(conn):
    """Crée la vue daily_pred_score_v3_1_dataset_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    SELECT
        v2.date,
        -- Score V2.1 (production)
        v2.pred_daily_release_top20_sum_top2 AS score_v2_1,
        -- Target
        vol.daily_volatility_pips_v1 AS target_vol_pips,
        -- Features calendrier
        cal.dow,
        cal.is_mon,
        cal.is_fri,
        cal.day_of_month,
        cal.month,
        cal.is_month_start,
        cal.is_month_end,
        cal.week_of_month,
        -- Features régime (sauf vol_pips debug)
        regime.vol_pips_lag1,
        regime.vol_mean_20_lag1,
        regime.vol_std_20_lag1,
        regime.vol_mean_60_lag1,
        regime.vol_std_60_lag1,
        regime.vol_z_20_lag1,
        regime.vol_z_60_lag1,
        regime.regime_high_60_lag1,
        regime.regime_low_60_lag1
    FROM {V2_VIEW} v2
    INNER JOIN {CAL_VIEW} cal ON v2.date = cal.date
    INNER JOIN {REGIME_VIEW} regime ON v2.date = regime.date
    INNER JOIN {VOL_VIEW} vol ON v2.date = vol.date
    ORDER BY v2.date
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. COUNT(*) > 600 (attendu ~714)
    n_rows = conn.execute(f"SELECT COUNT(*) FROM {VIEW_NAME}").fetchone()[0]
    if n_rows > 600:
        print(f"✅ Nombre de lignes: {n_rows} (attendu ~714)")
    else:
        print(f"❌ ERREUR: {n_rows} lignes (attendu > 600)")
        return False
    
    # 2. Pas de NULL sur (date, score_v2_1, target_vol_pips)
    n_null_date = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE date IS NULL
    """).fetchone()[0]
    
    n_null_score = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE score_v2_1 IS NULL
    """).fetchone()[0]
    
    n_null_target = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE target_vol_pips IS NULL
    """).fetchone()[0]
    
    if n_null_date == 0 and n_null_score == 0 and n_null_target == 0:
        print(f"✅ Pas de NULL sur (date, score_v2_1, target_vol_pips)")
    else:
        print(f"❌ ERREUR: NULL détectés (date={n_null_date}, score={n_null_score}, target={n_null_target})")
        return False
    
    # 3. Stats score_v2_1 et target_vol_pips
    print("\n📊 Statistiques score_v2_1 et target_vol_pips:")
    df_stats = conn.execute(f"""
        SELECT
            COUNT(*) AS n_days,
            ROUND(MIN(score_v2_1), 2) AS min_score,
            ROUND(MEDIAN(score_v2_1), 2) AS p50_score,
            ROUND(MAX(score_v2_1), 2) AS max_score,
            ROUND(AVG(score_v2_1), 2) AS avg_score,
            ROUND(MIN(target_vol_pips), 2) AS min_vol,
            ROUND(MEDIAN(target_vol_pips), 2) AS p50_vol,
            ROUND(MAX(target_vol_pips), 2) AS max_vol,
            ROUND(AVG(target_vol_pips), 2) AS avg_vol
        FROM {VIEW_NAME}
    """).df()
    print(df_stats.to_string(index=False))
    
    # 4. Cohérence dates min/max
    df_dates = conn.execute(f"""
        SELECT 
            MIN(date) AS min_date,
            MAX(date) AS max_date,
            COUNT(DISTINCT date) AS n_dates
        FROM {VIEW_NAME}
    """).df()
    
    df_vol_dates = conn.execute(f"""
        SELECT 
            MIN(date) AS min_date_vol,
            MAX(date) AS max_date_vol
        FROM {VOL_VIEW}
        WHERE date IN (SELECT date FROM {VIEW_NAME})
    """).df()
    
    print("\n📊 Cohérence dates:")
    print(f"  Dataset: {df_dates.iloc[0]['min_date']} → {df_dates.iloc[0]['max_date']} ({df_dates.iloc[0]['n_dates']} dates)")
    if not df_vol_dates.empty:
        print(f"  Vol view: {df_vol_dates.iloc[0]['min_date_vol']} → {df_vol_dates.iloc[0]['max_date_vol']}")
    
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
        print("CRÉATION DAILY_PRED_SCORE_V3_1_DATASET_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # Créer vue
        create_view(conn)
        
        # Sanity checks
        if not sanity_checks(conn):
            print("\n❌ SANITY CHECKS ÉCHOUÉS")
            sys.exit(1)
        
        print("\n✅ Vue daily_pred_score_v3_1_dataset_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

