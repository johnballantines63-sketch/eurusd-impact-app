"""
DIAGNOSTIC PLANIFICATEUR - SESSION 80
=====================================

Script de diagnostic pour comprendre pourquoi le planificateur
fonctionne uniquement sur le 11.09.2025 et pas sur d'autres dates.

Teste:
1. Événements disponibles dans la DB pour plusieurs dates
2. Fonction du planificateur sur ces dates
3. Comparaison 11.09.2025 (fonctionne) vs autres dates
4. Identification problème exact (timezone, query, données manquantes)

Auteur: Session 80
Date: 25 octobre 2025
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


# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

# Dates à tester
DATES_TEST = [
    '2025-09-11',  # Référence qui fonctionne
    '2025-02-12',  # Date graphique fourni
    '2024-12-18',  # Dataset Session 75
    '2024-04-10',  # Dataset Session 75
    '2025-08-01',  # NFP extrême Session 72
]


# ══════════════════════════════════════════════════════════════════════
# FONCTIONS DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════

def get_db_connection():
    """Connexion DB"""
    db_path = get_db_path()
    return duckdb.connect(str(db_path), read_only=True)


def test_events_for_date_raw(date_str: str, conn) -> pd.DataFrame:
    """
    Test 1: Quels événements existent dans la DB pour cette date ?
    Query SIMPLE sans filtre complexe
    """
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
    
    df = conn.execute(query, [date_str]).df()
    return df


def test_events_planificateur_logic(date_str: str, conn) -> pd.DataFrame:
    """
    Test 2: Query EXACTE du planificateur
    (lignes 124-155 de 5_Planificateur_V2_FORMULES_VALIDEES_backup_session_72_copie.py)
    """
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
    
    df = conn.execute(query, [date_str]).df()
    return df


def test_events_around_time(date_str: str, time_str: str, conn) -> pd.DataFrame:
    """
    Test 3: Événements dans une fenêtre temporelle
    Simule ce que ferait le planificateur si on clique sur un timestamp précis
    """
    datetime_str = f"{date_str} {time_str}"
    
    # Fenêtre ±30 minutes
    query = """
    SELECT 
        e.event_title,
        e.ts_utc,
        strftime(e.ts_utc, '%H:%M:%S') as heure_berne,
        e.country,
        e.actual,
        e.estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= (TIMESTAMP ? - INTERVAL '30' MINUTE)
        AND e.ts_utc <= (TIMESTAMP ? + INTERVAL '30' MINUTE)
        AND e.country = 'US'
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [datetime_str, datetime_str]).df()
    return df


def analyze_date(date_str: str, conn):
    """
    Analyse complète d'une date
    """
    print(f"\n{'='*80}")
    print(f"📅 DATE: {date_str}")
    print(f"{'='*80}")
    
    # Test 1: Tous les événements de la date
    df_raw = test_events_for_date_raw(date_str, conn)
    print(f"\n1️⃣  ÉVÉNEMENTS BRUTS DANS LA DB (tous pays, toutes importances)")
    print(f"   Total événements: {len(df_raw)}")
    
    if len(df_raw) > 0:
        print(f"\n   Échantillon (premiers 10):")
        print(df_raw[['heure_berne', 'event_title', 'country', 'importance_n']].head(10).to_string(index=False))
        
        # Stats par pays
        print(f"\n   Distribution par pays:")
        print(df_raw['country'].value_counts().to_string())
        
        # Stats par importance
        print(f"\n   Distribution par importance_n:")
        print(df_raw['importance_n'].value_counts(dropna=False).to_string())
    else:
        print("   ❌ AUCUN ÉVÉNEMENT TROUVÉ DANS LA DB POUR CETTE DATE")
    
    # Test 2: Query planificateur
    df_planner = test_events_planificateur_logic(date_str, conn)
    print(f"\n2️⃣  ÉVÉNEMENTS SELON LOGIQUE PLANIFICATEUR")
    print(f"   (US uniquement, score > 40)")
    print(f"   Total événements: {len(df_planner)}")
    
    if len(df_planner) > 0:
        print(f"\n   Détails:")
        print(df_planner[['heure_berne', 'label', 'empirical_score', 'importance_n']].to_string(index=False))
    else:
        print("   ❌ AUCUN ÉVÉNEMENT HIGH IMPACT US TROUVÉ")
        
        # Diagnostic pourquoi
        df_us = df_raw[df_raw['country'] == 'US']
        if len(df_us) == 0:
            print("      Cause: Pas d'événements US ce jour")
        else:
            print(f"      Il y a {len(df_us)} événements US, mais:")
            print("      - Peut-être score < 40")
            print("      - Peut-être pas dans event_families")
            print("      - Peut-être importance_n incorrect")
    
    # Test 3: Si on a des événements US, tester autour d'une heure typique
    if len(df_raw[df_raw['country'] == 'US']) > 0:
        # Prendre l'heure du premier événement US
        first_us = df_raw[df_raw['country'] == 'US'].iloc[0]
        time_str = first_us['heure_berne']
        
        print(f"\n3️⃣  TEST FENÊTRE TEMPORELLE (±30 min autour {time_str})")
        df_window = test_events_around_time(date_str, time_str, conn)
        print(f"   Événements trouvés: {len(df_window)}")
        
        if len(df_window) > 0:
            print(f"\n   Détails:")
            print(df_window[['heure_berne', 'event_title', 'empirical_score']].to_string(index=False))
    
    print(f"\n{'='*80}\n")


def compare_reference_vs_others(conn):
    """
    Comparaison 11.09.2025 (référence) vs autres dates
    """
    print(f"\n{'#'*80}")
    print(f"📊 COMPARAISON 11.09.2025 (RÉFÉRENCE) VS AUTRES DATES")
    print(f"{'#'*80}")
    
    results = []
    
    for date_str in DATES_TEST:
        df_raw = test_events_for_date_raw(date_str, conn)
        df_planner = test_events_planificateur_logic(date_str, conn)
        
        results.append({
            'date': date_str,
            'events_total': len(df_raw),
            'events_us': len(df_raw[df_raw['country'] == 'US']) if len(df_raw) > 0 else 0,
            'events_high_impact': len(df_planner),
            'planificateur_ok': '✅' if len(df_planner) > 0 else '❌'
        })
    
    df_comparison = pd.DataFrame(results)
    print("\n")
    print(df_comparison.to_string(index=False))
    
    print(f"\n{'#'*80}\n")


def test_timezone_hypothesis(conn):
    """
    Test hypothèse timezone: Les timestamps sont-ils vraiment en UTC+2 ?
    """
    print(f"\n{'='*80}")
    print(f"🕐 TEST HYPOTHÈSE TIMEZONE")
    print(f"{'='*80}")
    
    # Cas connu: 11 septembre 2025, 14:30 Berne (12:30 UTC)
    # Selon documentation, événements CPI stockés à 14:30 dans ts_utc
    
    query_1430 = """
    SELECT 
        event_title,
        ts_utc,
        strftime(ts_utc, '%H:%M:%S') as heure_affichee,
        country
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
        AND strftime(ts_utc, '%H:%M') = '14:30'
        AND country = 'US'
    LIMIT 5
    """
    
    query_1230 = """
    SELECT 
        event_title,
        ts_utc,
        strftime(ts_utc, '%H:%M:%S') as heure_affichee,
        country
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
        AND strftime(ts_utc, '%H:%M') = '12:30'
        AND country = 'US'
    LIMIT 5
    """
    
    print("\n1️⃣  Test à 14:30 (heure Berne, UTC+2):")
    df_1430 = conn.execute(query_1430).df()
    print(f"   Événements trouvés: {len(df_1430)}")
    if len(df_1430) > 0:
        print("   ✅ CONFIRMATION: Les timestamps sont bien stockés en heure Berne (UTC+2)")
        print(f"\n   Échantillon:")
        print(df_1430.to_string(index=False))
    
    print("\n2️⃣  Test à 12:30 (heure UTC):")
    df_1230 = conn.execute(query_1230).df()
    print(f"   Événements trouvés: {len(df_1230)}")
    if len(df_1230) > 0:
        print("   ⚠️  ATTENTION: Des événements trouvés aussi à 12:30")
    else:
        print("   ✅ CONFIRMATION: Pas d'événements à 12:30 UTC")
    
    print(f"\n{'='*80}\n")


def diagnostic_12_fevrier_special(conn):
    """
    Diagnostic spécial pour le 12 février 2025
    (Date du graphique fourni par l'utilisateur)
    """
    print(f"\n{'='*80}")
    print(f"🔍 DIAGNOSTIC SPÉCIAL: 12 FÉVRIER 2025")
    print(f"{'='*80}")
    
    print("\nD'après le graphique fourni:")
    print("- Date: Feb 12, 2025")
    print("- Heure: 14:41 (annotation sur graphique)")
    print("- Mouvement: Phase 1 +32 pips / 5 min")
    print("- Type détecté: Double Wave Momentum")
    
    # Test 1: Événements à 14:30 (heure économique standard)
    print("\n1️⃣  Recherche événements à 14:30 Berne:")
    query_1430 = """
    SELECT 
        event_title,
        strftime(ts_utc, '%H:%M:%S') as heure_berne,
        country,
        actual,
        estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(ts_utc) = '2025-02-12'
        AND strftime(ts_utc, '%H:%M') BETWEEN '14:25' AND '14:35'
        AND country = 'US'
    ORDER BY ts_utc
    """
    df = conn.execute(query_1430).df()
    print(f"   Événements trouvés: {len(df)}")
    if len(df) > 0:
        print(df.to_string(index=False))
    
    # Test 2: Événements autour de 14:41
    print("\n2️⃣  Recherche événements autour de 14:41 (±10 min):")
    query_1441 = """
    SELECT 
        event_title,
        strftime(ts_utc, '%H:%M:%S') as heure_berne,
        country,
        actual,
        estimate,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(ts_utc) = '2025-02-12'
        AND strftime(ts_utc, '%H:%M') BETWEEN '14:31' AND '14:51'
        AND country = 'US'
    ORDER BY ts_utc
    """
    df = conn.execute(query_1441).df()
    print(f"   Événements trouvés: {len(df)}")
    if len(df) > 0:
        print(df.to_string(index=False))
    
    # Test 3: Tous événements US ce jour
    print("\n3️⃣  Tous événements US du 12 février 2025:")
    query_all = """
    SELECT 
        strftime(ts_utc, '%H:%M:%S') as heure_berne,
        event_title,
        ef.empirical_score,
        importance_n
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(ts_utc) = '2025-02-12'
        AND country = 'US'
    ORDER BY ts_utc
    """
    df = conn.execute(query_all).df()
    print(f"   Total événements US: {len(df)}")
    if len(df) > 0:
        print(df.to_string(index=False))
    else:
        print("   ❌ AUCUN ÉVÉNEMENT US TROUVÉ POUR LE 12 FÉVRIER 2025")
        print("   → Peut expliquer pourquoi le planificateur ne fonctionne pas")
    
    print(f"\n{'='*80}\n")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    """
    Exécution diagnostic complet
    """
    print("\n" + "="*80)
    print("🔍 DIAGNOSTIC PLANIFICATEUR - SESSION 80")
    print("="*80)
    print("\nObjectif: Comprendre pourquoi le planificateur fonctionne")
    print("uniquement sur le 11.09.2025 et pas sur d'autres dates\n")
    
    conn = get_db_connection()
    
    try:
        # Test 1: Hypothèse timezone
        test_timezone_hypothesis(conn)
        
        # Test 2: Diagnostic chaque date
        for date_str in DATES_TEST:
            analyze_date(date_str, conn)
        
        # Test 3: Comparaison globale
        compare_reference_vs_others(conn)
        
        # Test 4: Focus 12 février
        diagnostic_12_fevrier_special(conn)
        
        # Résumé
        print("\n" + "="*80)
        print("📋 RÉSUMÉ DIAGNOSTIC")
        print("="*80)
        print("\nLe diagnostic a testé:")
        print("✅ 1. Hypothèse timezone (événements stockés en UTC+2 Berne)")
        print("✅ 2. Événements disponibles pour chaque date test")
        print("✅ 3. Logique query planificateur (filtres score > 40, US only)")
        print("✅ 4. Fenêtres temporelles (±30 min)")
        print("✅ 5. Comparaison 11.09 (référence) vs autres dates")
        print("✅ 6. Focus spécial 12 février 2025 (graphique utilisateur)")
        print("\nVoir résultats ci-dessus pour identifier le problème exact.")
        print("="*80 + "\n")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
