#!/usr/bin/env python3
"""
Création de la vue daily_calendar_features_v1
==============================================

Features calendrier (jour de semaine, jour du mois, etc.)
Source : daily_eurusd_volatility_v1 (garantit couverture cohérente)
"""

import sys
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"

VOL_VIEW = "daily_eurusd_volatility_v1"
VIEW_NAME = "daily_calendar_features_v1"


def create_view(conn):
    """Crée la vue daily_calendar_features_v1."""
    print(f"🔧 Création vue {VIEW_NAME}...")
    
    CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW {VIEW_NAME} AS
    SELECT
        date,
        EXTRACT('dow' FROM date) AS dow,  -- 0=Sunday, 1=Monday, ..., 6=Saturday
        CASE WHEN EXTRACT('dow' FROM date) = 1 THEN 1 ELSE 0 END AS is_mon,
        CASE WHEN EXTRACT('dow' FROM date) = 5 THEN 1 ELSE 0 END AS is_fri,
        EXTRACT('day' FROM date) AS day_of_month,
        EXTRACT('month' FROM date) AS month,
        CASE WHEN EXTRACT('day' FROM date) <= 3 THEN 1 ELSE 0 END AS is_month_start,
        CASE WHEN EXTRACT('day' FROM date) >= 28 THEN 1 ELSE 0 END AS is_month_end,
        1 + FLOOR((EXTRACT('day' FROM date) - 1) / 7) AS week_of_month
    FROM {VOL_VIEW}
    ORDER BY date
    """
    
    conn.execute(CREATE_VIEW_SQL)
    print(f"  ✅ Vue {VIEW_NAME} créée\n")


def sanity_checks(conn):
    """Vérifications de cohérence."""
    print("=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)
    
    # 1. COUNT(*) > 0
    n_rows = conn.execute(f"SELECT COUNT(*) FROM {VIEW_NAME}").fetchone()[0]
    if n_rows > 0:
        print(f"✅ Nombre de lignes: {n_rows}")
    else:
        print(f"❌ ERREUR: Aucune ligne dans {VIEW_NAME}")
        return False
    
    # 2. Pas de NULL sur date
    n_null_date = conn.execute(f"""
        SELECT COUNT(*) 
        FROM {VIEW_NAME} 
        WHERE date IS NULL
    """).fetchone()[0]
    
    if n_null_date == 0:
        print(f"✅ Pas de NULL sur date")
    else:
        print(f"❌ ERREUR: {n_null_date} lignes avec date IS NULL")
        return False
    
    # 3. Stats simples
    print("\n📊 Statistiques descriptives:")
    df_stats = conn.execute(f"""
        SELECT
            COUNT(*) AS n_days,
            COUNT(DISTINCT dow) AS n_dow_values,
            COUNT(DISTINCT month) AS n_months,
            SUM(is_mon) AS n_mondays,
            SUM(is_fri) AS n_fridays,
            SUM(is_month_start) AS n_month_starts,
            SUM(is_month_end) AS n_month_ends
        FROM {VIEW_NAME}
    """).df()
    print(df_stats.to_string(index=False))
    
    # 4. Head 10
    print("\n📊 Head 10:")
    df_head = conn.execute(f"""
        SELECT *
        FROM {VIEW_NAME}
        ORDER BY date
        LIMIT 10
    """).df()
    print(df_head.to_string(index=False))
    
    print("\n" + "=" * 100)
    return True


def main():
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    try:
        print("=" * 100)
        print("CRÉATION DAILY_CALENDAR_FEATURES_V1")
        print("=" * 100)
        print(f"DB : {DB_PATH}\n")
        
        # Créer vue
        create_view(conn)
        
        # Sanity checks
        if not sanity_checks(conn):
            print("\n❌ SANITY CHECKS ÉCHOUÉS")
            sys.exit(1)
        
        print("\n✅ Vue daily_calendar_features_v1 prête")
        print("=" * 100)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

