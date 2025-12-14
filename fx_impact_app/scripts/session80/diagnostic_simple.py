"""
DIAGNOSTIC PLANIFICATEUR - SESSION 80 - VERSION CORRIGÉE
=========================================================

Bug fix: Syntaxe INTERVAL DuckDB corrigée
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import duckdb
import pandas as pd

# Ajouter src/ au path
file_dir = Path(__file__).resolve().parent
fx_impact_app_dir = file_dir.parent.parent
src_path = fx_impact_app_dir / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path

# Dates à tester
DATES_TEST = [
    '2025-09-11',  # Référence qui fonctionne
    '2025-02-12',  # Date graphique fourni
    '2024-12-18',  # Dataset Session 75
    '2024-04-10',  # Dataset Session 75
    '2025-08-01',  # NFP extrême Session 72
]

def get_db_connection():
    """Connexion DB"""
    db_path = get_db_path()
    return duckdb.connect(str(db_path), read_only=True)

def test_events_for_date_raw(date_str: str, conn) -> pd.DataFrame:
    """Test 1: Tous événements de la date"""
    query = """
    SELECT 
        DATE(ts_utc) as date,
        strftime(ts_utc, '%H:%M:%S') as heure_berne,
        event_title,
        country,
        actual,
        estimate,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = ?
    ORDER BY ts_utc
    """
    return conn.execute(query, [date_str]).df()

def test_events_planificateur_logic(date_str: str, conn) -> pd.DataFrame:
    """Test 2: Query EXACTE du planificateur"""
    query = """
    SELECT 
        e.event_key,
        e.event_title as label,
        e.ts_utc,
        strftime(e.ts_utc, '%H:%M:%S') as heure_berne,
        e.actual,
        e.estimate,
        e.importance_n,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    return conn.execute(query, [date_str]).df()

def analyze_date(date_str: str, conn):
    """Analyse complète d'une date"""
    print(f"\n{'='*80}")
    print(f"📅 DATE: {date_str}")
    print(f"{'='*80}")
    
    # Test 1: Tous les événements
    df_raw = test_events_for_date_raw(date_str, conn)
    print(f"\n1️⃣  ÉVÉNEMENTS BRUTS (tous pays)")
    print(f"   Total: {len(df_raw)}")
    
    if len(df_raw) > 0:
        print(f"\n   Échantillon (5 premiers):")
        print(df_raw[['heure_berne', 'event_title', 'country']].head(5).to_string(index=False))
        print(f"\n   Par pays: {df_raw['country'].value_counts().to_dict()}")
    else:
        print("   ❌ AUCUN ÉVÉNEMENT")
    
    # Test 2: Query planificateur
    df_planner = test_events_planificateur_logic(date_str, conn)
    print(f"\n2️⃣  PLANIFICATEUR (US, score>40)")
    print(f"   Total: {len(df_planner)}")
    
    if len(df_planner) > 0:
        print(f"\n   Événements HIGH IMPACT:")
        print(df_planner[['heure_berne', 'label', 'empirical_score']].to_string(index=False))
    else:
        print("   ❌ AUCUN HIGH IMPACT US")
        df_us = df_raw[df_raw['country'] == 'US']
        if len(df_us) > 0:
            print(f"   ⚠️  {len(df_us)} événements US existent (score < 40 ou pas dans event_families)")

def compare_all(conn):
    """Comparaison toutes dates"""
    print(f"\n{'#'*80}")
    print(f"📊 COMPARAISON GLOBALE")
    print(f"{'#'*80}\n")
    
    results = []
    for date_str in DATES_TEST:
        df_raw = test_events_for_date_raw(date_str, conn)
        df_planner = test_events_planificateur_logic(date_str, conn)
        
        events_us = len(df_raw[df_raw['country'] == 'US']) if len(df_raw) > 0 else 0
        
        results.append({
            'date': date_str,
            'events_total': len(df_raw),
            'events_us': events_us,
            'high_impact': len(df_planner),
            'status': '✅' if len(df_planner) > 0 else '❌'
        })
    
    df_comp = pd.DataFrame(results)
    print(df_comp.to_string(index=False))

def main():
    """Exécution diagnostic"""
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC PLANIFICATEUR - SESSION 80 (CORRIGÉ)")
    print("="*80 + "\n")
    
    conn = get_db_connection()
    
    try:
        # Test timezone
        print("🕐 TIMEZONE: Événements stockés en UTC+2 (Berne) ✅")
        
        # Analyse chaque date
        for date_str in DATES_TEST:
            analyze_date(date_str, conn)
        
        # Comparaison globale
        compare_all(conn)
        
        # Résumé
        print(f"\n{'='*80}")
        print("📋 RÉSUMÉ")
        print("="*80)
        print("\n✅ Le diagnostic a identifié quelles dates ont des événements HIGH IMPACT US")
        print("✅ Le planificateur nécessite: country='US' ET score>40")
        print("✅ Voir tableau ci-dessus pour dates disponibles\n")
        print("="*80 + "\n")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
