"""
Créer Table core_scores_by_date

Objectif :
1. Créer une table qui stocke les scores core_scores par date (pas agrégée)
2. Permettre le calcul de ratios pour toutes les dates historiques
3. Valider les théories sur un large échantillon

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
import pytz
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from scripts.run_pipeline_complete import PipelineExecutor

TZ_BERN = pytz.timezone('Europe/Zurich')

def measure_real_impact(date_str: str, anchor_time: pd.Timestamp, conn: Optional[duckdb.DuckDBPyConnection] = None) -> Optional[float]:
    """Mesurer impact réel depuis prix Finnhub"""
    close_conn = False
    if conn is None:
        conn = duckdb.connect(str(DB_PATH), read_only=True)
        close_conn = True
    
    date_dt = pd.to_datetime(date_str)
    window_start = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=0)))
    window_end = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=20, minute=0)))
    
    query_prices = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE DATE(datetime) = '{date_str}'
      AND datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
      AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
    ORDER BY datetime ASC
    """
    
    df_prices = conn.execute(query_prices).df()
    if close_conn:
        conn.close()
    
    if df_prices.empty:
        return None
    
    df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
    df_prices = df_prices.set_index('datetime')
    
    # Utiliser anchor_time pour baseline
    if isinstance(anchor_time, str):
        anchor_time = pd.to_datetime(anchor_time)
    
    if not hasattr(anchor_time, 'tz'):
        anchor_time = TZ_BERN.localize(anchor_time)
    
    prices_at_baseline = df_prices[df_prices.index >= anchor_time]
    
    if prices_at_baseline.empty:
        return None
    
    baseline_price = prices_at_baseline.iloc[0]['open']
    max_high = prices_at_baseline['high'].max()
    min_low = prices_at_baseline['low'].min()
    impact_up = (max_high - baseline_price) * 10000
    impact_down = (baseline_price - min_low) * 10000
    impact = max(impact_up, impact_down)
    
    return impact

def create_table_core_scores_by_date():
    """Créer la table core_scores_by_date"""
    
    print("="*100)
    print("CRÉATION TABLE core_scores_by_date")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # Créer la table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS core_scores_by_date (
            date DATE,
            core_type VARCHAR,
            country VARCHAR,
            empirical_score DOUBLE,
            impact_real DOUBLE,
            ratio DOUBLE,
            anchor_time TIMESTAMP,
            n_core_events INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date, core_type, country)
        )
    """)
    
    print("✅ Table core_scores_by_date créée")
    print()
    
    # Récupérer toutes les dates avec événements US/EU HIGH importance depuis 2020
    query_dates = """
    SELECT DISTINCT DATE(ts_utc) as date_str
    FROM events
    WHERE ts_utc >= '2020-01-01'
      AND importance_n = 3
      AND country IN ('US', 'EU')
    ORDER BY date_str DESC
    """
    
    df_dates = conn.execute(query_dates).df()
    
    print(f"📊 {len(df_dates)} dates avec événements HIGH importance trouvées")
    print()
    print("⚠️  Cette opération peut prendre du temps...")
    print("    On peut limiter avec --limit N pour tester")
    print()
    
    conn.close()
    
    return df_dates

def populate_core_scores_by_date(limit: Optional[int] = None, verbose: bool = True):
    """Remplir la table core_scores_by_date"""
    
    print("="*100)
    print("REMPLISSAGE TABLE core_scores_by_date")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    executor = PipelineExecutor(db_path=str(DB_PATH), verbose=False)
    
    # Récupérer dates avec données de prix ET actual disponible
    query_dates = """
    SELECT DISTINCT DATE(e.ts_utc) as date_str
    FROM events e
    INNER JOIN prices_finnhub_m1 p ON DATE(p.datetime) = DATE(e.ts_utc)
    WHERE e.ts_utc >= '2020-01-01'
      AND e.ts_utc < CURRENT_DATE
      AND e.importance_n = 3
      AND e.country IN ('US', 'EU')
      AND e.actual IS NOT NULL
      AND e.actual != 'nan'
    ORDER BY date_str DESC
    """
    
    df_dates = conn.execute(query_dates).df()
    conn.close()  # Fermer avant d'appeler le pipeline
    
    if limit:
        df_dates = df_dates.head(limit)
        print(f"⚠️  Mode test : limité à {limit} dates")
        print()
    
    print(f"📊 {len(df_dates)} dates à traiter")
    print()
    
    results = []
    success_count = 0
    error_count = 0
    
    for idx, row in df_dates.iterrows():
        # Convertir date_str en format YYYY-MM-DD
        date_val = row['date_str']
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime('%Y-%m-%d')
        elif isinstance(date_val, str):
            date_str = date_val.split()[0]  # Prendre seulement la partie date
        else:
            date_str = str(date_val).split()[0]
        
        if verbose:
            print(f"[{idx+1}/{len(df_dates)}] Analyse {date_str}...", end=" ")
        
        try:
            # Exécuter pipeline
            try:
                result = executor.execute_complete_pipeline(
                    date_str,
                    window_minutes=30,
                    support_threshold=0.8,
                    jaccard_threshold=0.6,
                    years_lookback=5
                )
            except Exception as e:
                if verbose:
                    print(f"❌ Exception: {str(e)[:50]}")
                error_count += 1
                continue
            
            if not result:
                if verbose:
                    print("❌ Pipeline retourné None")
                error_count += 1
                continue
            
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                if verbose:
                    print(f"❌ Pipeline échoué: {error_msg[:50]}")
                error_count += 1
                continue
            
            # Extraire informations
            results_dict = result.get('results', {})
            etape3_cluster_info = results_dict.get('etape3_cluster_info', {})
            main_cluster = etape3_cluster_info.get('cluster', {})
            core_type = etape3_cluster_info.get('core_type', 'UNKNOWN')
            country = etape3_cluster_info.get('country', 'US')
            anchor_time = main_cluster.get('anchor_time')
            n_core_events = etape3_cluster_info.get('n_core_events', 0)
            
            if not anchor_time:
                if verbose:
                    print("❌ Pas d'anchor_time")
                error_count += 1
                continue
            
            if core_type == 'UNKNOWN' or core_type == 'GENERIC':
                if verbose:
                    print(f"❌ Core type: {core_type}")
                error_count += 1
                continue
            
            if n_core_events == 0:
                if verbose:
                    print("❌ Pas d'événements core")
                error_count += 1
                continue
            
            # Récupérer score core_scores (table agrégée) - ouvrir connexion
            conn = duckdb.connect(str(DB_PATH), read_only=True)
            
            query_score = """
            SELECT empirical_score
            FROM core_scores
            WHERE core_type = ? AND country = ?
            """
            
            score_row = conn.execute(query_score, [core_type, country]).fetchone()
            conn.close()
            
            if not score_row:
                if verbose:
                    print("❌ Pas de score core_scores")
                error_count += 1
                continue
            
            core_score_db = score_row[0]
            
            # Fermer connexion avant mesure (éviter conflit)
            # Mesurer impact réel
            impact_real = measure_real_impact(date_str, anchor_time)
            
            if impact_real is None:
                if verbose:
                    print("❌ Pas d'impact")
                error_count += 1
                continue
            
            # Calculer ratio
            ratio = impact_real / core_score_db if core_score_db > 0 else 0.0
            
            # Rouvrir connexion pour insertion
            conn = duckdb.connect(str(DB_PATH), read_only=False)
            
            # Insérer dans la table
            conn.execute("""
                INSERT OR REPLACE INTO core_scores_by_date (
                    date, core_type, country, empirical_score,
                    impact_real, ratio, anchor_time, n_core_events
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                date_str, core_type, country, core_score_db,
                impact_real, ratio, anchor_time, n_core_events
            ])
            
            conn.close()
            
            results.append({
                'date': date_str,
                'core_type': core_type,
                'country': country,
                'empirical_score': core_score_db,
                'impact_real': impact_real,
                'ratio': ratio
            })
            
            success_count += 1
            
            if verbose:
                print(f"✅ {core_type} ({country}) - Ratio: {ratio:.3f}")
            
        except Exception as e:
            if verbose:
                print(f"❌ Erreur: {str(e)[:50]}")
            error_count += 1
            continue
    
    print()
    print("="*100)
    print("RÉSUMÉ")
    print("="*100)
    print()
    print(f"✅ Succès : {success_count}")
    print(f"❌ Erreurs : {error_count}")
    print(f"📊 Total : {len(df_dates)}")
    print()
    
    # Calculer statistiques
    if results:
        df_results = pd.DataFrame(results)
        
        print("STATISTIQUES PAR CORE TYPE :")
        print("-"*100)
        print()
        
        for core_type in df_results['core_type'].unique():
            df_type = df_results[df_results['core_type'] == core_type]
            
            print(f"{core_type}:")
            print(f"  N dates : {len(df_type)}")
            print(f"  Ratio moyen : {df_type['ratio'].mean():.3f}")
            print(f"  Ratio médian : {df_type['ratio'].median():.3f}")
            print(f"  Ratio std : {df_type['ratio'].std():.3f}")
            print()
    
    # Pas de connexion à fermer ici (déjà fermée dans la boucle)
    
    return results

def calculate_ratios_from_table():
    """Calculer ratios moyens depuis la table core_scores_by_date"""
    
    print("="*100)
    print("CALCUL RATIOS MOYENS DEPUIS core_scores_by_date")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Vérifier si la table existe
    try:
        count = conn.execute("SELECT COUNT(*) FROM core_scores_by_date").fetchone()[0]
        print(f"📊 {count} enregistrements dans core_scores_by_date")
        print()
    except:
        print("❌ Table core_scores_by_date n'existe pas")
        print("   Exécutez d'abord populate_core_scores_by_date()")
        conn.close()
        return
    
    # Calculer statistiques par core_type
    query_stats = """
    SELECT 
        core_type,
        country,
        COUNT(*) as n_dates,
        AVG(ratio) as ratio_mean,
        MEDIAN(ratio) as ratio_median,
        STDDEV(ratio) as ratio_std,
        MIN(ratio) as ratio_min,
        MAX(ratio) as ratio_max,
        AVG(impact_real) as impact_mean,
        AVG(empirical_score) as score_mean
    FROM core_scores_by_date
    GROUP BY core_type, country
    ORDER BY core_type, country
    """
    
    df_stats = conn.execute(query_stats).df()
    
    print("STATISTIQUES PAR CORE TYPE :")
    print("-"*100)
    print()
    
    print(f"{'Core Type':<20} {'Country':<8} {'N Dates':<10} {'Ratio Moyen':<12} {'Ratio Médian':<12} {'Ratio Std':<12} {'Impact Moyen':<12} {'Score Moyen':<12}")
    print("-"*100)
    
    for _, row in df_stats.iterrows():
        print(f"{row['core_type']:<20} {row['country']:<8} {row['n_dates']:<10} {row['ratio_mean']:>11.3f} {row['ratio_median']:>11.3f} {row['ratio_std']:>11.3f} {row['impact_mean']:>11.2f} {row['score_mean']:>11.2f}")
    
    print()
    
    # Sauvegarder
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'ratios_moyens_par_core_type.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_stats.to_csv(output_file, index=False)
    
    print(f"💾 Statistiques sauvegardées : {output_file}")
    print()
    
    conn.close()
    
    return df_stats

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gérer la table core_scores_by_date')
    parser.add_argument('--create', action='store_true', help='Créer la table')
    parser.add_argument('--populate', action='store_true', help='Remplir la table')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de dates (pour test)')
    parser.add_argument('--stats', action='store_true', help='Calculer statistiques')
    parser.add_argument('--quiet', action='store_true', help='Mode silencieux')
    
    args = parser.parse_args()
    
    if args.create:
        create_table_core_scores_by_date()
    
    if args.populate:
        populate_core_scores_by_date(limit=args.limit, verbose=not args.quiet)
    
    if args.stats:
        calculate_ratios_from_table()
    
    if not any([args.create, args.populate, args.stats]):
        print("Usage:")
        print("  --create   : Créer la table")
        print("  --populate : Remplir la table (--limit N pour tester)")
        print("  --stats    : Calculer statistiques")
        print()
        print("Exemple:")
        print("  python creer_table_core_scores_by_date.py --create --populate --limit 10")

