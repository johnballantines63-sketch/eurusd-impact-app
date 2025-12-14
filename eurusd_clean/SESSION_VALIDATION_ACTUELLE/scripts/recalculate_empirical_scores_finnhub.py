"""
RECALCUL SCORES EMPIRIQUES DEPUIS FINNHUB

Version : 1.0
Date : 2025-12-06
Référence : REF-003

Ce script recalcule les scores empiriques en utilisant :
- Source événements : events (Finnhub)
- Source prix : prices_finnhub_m1 (Finnhub)
- Méthode : Mesure impact réel pour chaque événement historique

Formule validée :
empirical_score = (avg_movement * 0.5 + p80_movement * 0.5) * robustness

Auteur : André Valentin avec Claude
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from collections import defaultdict
import pytz

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

# Paramètres de calcul
LOOKBACK_MINUTES = 5  # Minutes avant événement pour baseline
LOOKAHEAD_MINUTES = 240  # Minutes après événement pour pic maximum
MIN_SAMPLE_SIZE = 3  # Taille minimum d'échantillon pour calculer score

def calculate_empirical_score(avg_movement: float, p80_movement: float, sample_size: int) -> float:
    """
    Calcule le score empirique normalisé 0-100
    
    Formule validée (Session 123) :
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    robustness = facteur basé sur sample_size
    score = base_score * robustness
    normalized = min(100.0, (score / 100.0) * 100.0)
    
    Args:
        avg_movement: Mouvement moyen en pips
        p80_movement: Mouvement au 80e percentile en pips
        sample_size: Taille de l'échantillon
    
    Returns:
        Score empirique normalisé (0-100)
    """
    # Score de base : moyenne pondérée avg + p80
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    # Facteur robustesse basé sur sample_size
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    
    # ⚠️ CORRECTION : Normalisation simplifiée (REF-005)
    # Ancien : (score / 100.0) * 100.0 = score (redondant)
    # Nouveau : min(100.0, score) - plus simple et clair
    normalized = min(100.0, score)
    
    return normalized

def measure_impact_for_event(
    conn: duckdb.DuckDBPyConnection,
    event_timestamp: pd.Timestamp,
    lookback_minutes: int = LOOKBACK_MINUTES,
    lookahead_minutes: int = LOOKAHEAD_MINUTES
) -> dict:
    """
    Mesure l'impact réel d'un événement depuis prices_finnhub_m1
    
    Méthode :
    1. Baseline : OPEN de la première bougie à ou après l'événement
       (Fallback : CLOSE de la dernière bougie avant l'événement)
    2. Pic : HIGH maximum (ou LOW minimum) dans fenêtre lookahead
    3. Impact = abs((peak_price - baseline_price) * 10000)
    
    Args:
        conn: Connexion DuckDB
        event_timestamp: Timestamp de l'événement (timezone-aware)
        lookback_minutes: Minutes avant événement pour baseline
        lookahead_minutes: Minutes après événement pour pic
    
    Returns:
        dict avec :
            - impact_pips: Impact en pips (float)
            - baseline_price: Prix baseline (float)
            - peak_price: Prix du pic (float)
            - direction: 'UP' ou 'DOWN' (str)
            - success: True si mesure réussie (bool)
    """
    try:
        # S'assurer que event_timestamp est timezone-aware (Bern)
        if event_timestamp.tzinfo is None:
            event_timestamp = TZ_BERN.localize(event_timestamp)
        elif str(event_timestamp.tzinfo) != str(TZ_BERN):
            event_timestamp = event_timestamp.astimezone(TZ_BERN)
        
        # Formater pour SQL (naive)
        event_time_naive = event_timestamp.replace(tzinfo=None)
        window_start = event_time_naive - timedelta(minutes=lookback_minutes)
        window_end = event_time_naive + timedelta(minutes=lookahead_minutes)
        
        # Charger prix dans la fenêtre
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= TIMESTAMP '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime <= TIMESTAMP '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query).df()
        
        if df_prices.empty:
            return {'success': False, 'reason': 'no_prices'}
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        # S'assurer que l'index est timezone-naive pour comparaison
        if df_prices['datetime'].dt.tz is not None:
            df_prices['datetime'] = df_prices['datetime'].dt.tz_localize(None)
        df_prices = df_prices.set_index('datetime')
        
        # 1. Baseline : OPEN de la première bougie à ou après l'événement
        prices_at_or_after = df_prices[df_prices.index >= event_time_naive]
        if not prices_at_or_after.empty:
            baseline_price = prices_at_or_after.iloc[0]['open']
        else:
            # Fallback : CLOSE de la dernière bougie avant l'événement
            prices_before = df_prices[df_prices.index < event_time_naive]
            if not prices_before.empty:
                baseline_price = prices_before.iloc[-1]['close']
            else:
                return {'success': False, 'reason': 'no_baseline'}
        
        # 2. Chercher pic dans fenêtre après événement
        prices_after_event = df_prices[df_prices.index >= event_time_naive]
        if prices_after_event.empty:
            return {'success': False, 'reason': 'no_prices_after_event'}
        
        # Pic maximum (UP) et minimum (DOWN)
        peak_high = prices_after_event['high'].max()
        peak_low = prices_after_event['low'].min()
        
        # Calculer impacts
        impact_up = (peak_high - baseline_price) * 10000
        impact_down = (baseline_price - peak_low) * 10000
        
        # Prendre le maximum
        if impact_up >= impact_down:
            impact_pips = abs(impact_up)
            peak_price = peak_high
            direction = 'UP'
        else:
            impact_pips = abs(impact_down)
            peak_price = peak_low
            direction = 'DOWN'
        
        return {
            'success': True,
            'impact_pips': impact_pips,
            'baseline_price': baseline_price,
            'peak_price': peak_price,
            'direction': direction
        }
        
    except Exception as e:
        return {'success': False, 'reason': f'error: {str(e)}'}

def calculate_scores_for_event_family(
    conn: duckdb.DuckDBPyConnection,
    event_key: str,
    country: str,
    events_df: pd.DataFrame,
    verbose: bool = False
) -> dict:
    """
    Calcule les statistiques et score empirique pour une famille d'événements
    
    Args:
        conn: Connexion DuckDB
        event_key: Clé de l'événement
        country: Pays
        events_df: DataFrame avec événements de cette famille
        verbose: Afficher détails
    
    Returns:
        dict avec statistiques et score empirique
    """
    if len(events_df) < MIN_SAMPLE_SIZE:
        return None
    
    impacts = []
    latencies = []
    
    if verbose:
        print(f"   Calcul pour {event_key} ({country}): {len(events_df)} événements")
    
    for _, event in events_df.iterrows():
        event_timestamp = pd.to_datetime(event['ts_utc'])
        
        # Mesurer impact
        result = measure_impact_for_event(conn, event_timestamp)
        
        if result.get('success'):
            impacts.append(result['impact_pips'])
            
            # Calculer latence (simplifié : temps jusqu'au pic)
            # Pour l'instant, on utilise une estimation basée sur la fenêtre
            # TODO: Calculer latence réelle depuis les prix
            latencies.append(5.0)  # Estimation par défaut
    
    if len(impacts) < MIN_SAMPLE_SIZE:
        return None
    
    # Calculer statistiques
    impacts_array = np.array(impacts)
    
    avg_movement = np.mean(impacts_array)
    median_movement = np.median(impacts_array)
    p80_movement = np.percentile(impacts_array, 80)
    p20_movement = np.percentile(impacts_array, 20)
    
    # Calculer score empirique
    empirical_score = calculate_empirical_score(avg_movement, p80_movement, len(impacts))
    
    # Latence médiane
    latency_median = np.median(latencies) if latencies else 5.0
    latency_p20 = np.percentile(latencies, 20) if latencies else 3.0
    latency_p80 = np.percentile(latencies, 80) if latencies else 10.0
    
    return {
        'event_key': event_key,
        'country': country,
        'empirical_score': empirical_score,
        'avg_movement_pips': avg_movement,
        'median_movement_pips': median_movement,
        'p80_movement_pips': p80_movement,
        'p20_movement_pips': p20_movement,
        'sample_size': len(impacts),
        'latency_median': latency_median,
        'latency_p20': latency_p20,
        'latency_p80': latency_p80,
        'n_events_total': len(events_df),
        'n_events_measured': len(impacts)
    }

def recalculate_empirical_scores_finnhub(
    db_path: Path = DB_PATH,
    start_date: str = '2020-01-01',
    end_date: str = None,
    countries: list = ['US', 'EU', 'DE', 'GB'],
    min_events: int = MIN_SAMPLE_SIZE,
    verbose: bool = True,
    dry_run: bool = False
):
    """
    Recalcule les scores empiriques depuis Finnhub
    
    Args:
        db_path: Chemin vers warehouse.duckdb
        start_date: Date de début (format 'YYYY-MM-DD')
        end_date: Date de fin (format 'YYYY-MM-DD', None = aujourd'hui)
        countries: Liste des pays à traiter
        min_events: Nombre minimum d'événements pour calculer score
        verbose: Afficher détails
        dry_run: Mode test (ne pas mettre à jour la DB)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print("="*100)
    print("RECALCUL SCORES EMPIRIQUES DEPUIS FINNHUB")
    print("="*100)
    print(f"Date début : {start_date}")
    print(f"Date fin : {end_date}")
    print(f"Pays : {', '.join(countries)}")
    print(f"Mode : {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(db_path), read_only=False)
    
    try:
        # 1. Charger tous les événements depuis events (Finnhub)
        print("1. Chargement événements depuis events (Finnhub)...")
        countries_str = "', '".join(countries)
        query_events = f"""
        SELECT 
            event_key,
            country,
            ts_utc,
            importance_n
        FROM events
        WHERE DATE(ts_utc) >= '{start_date}'
          AND DATE(ts_utc) <= '{end_date}'
          AND country IN ('{countries_str}')
        ORDER BY event_key, country, ts_utc
        """
        
        df_all_events = conn.execute(query_events).df()
        
        if df_all_events.empty:
            print("❌ Aucun événement trouvé")
            return
        
        print(f"✅ {len(df_all_events):,} événements chargés")
        print()
        
        # 2. Grouper par (event_key, country)
        print("2. Groupement par famille d'événements...")
        grouped = df_all_events.groupby(['event_key', 'country'])
        
        results = []
        total_groups = len(grouped)
        
        print(f"✅ {total_groups} familles d'événements identifiées")
        print()
        
        # 3. Calculer scores pour chaque famille
        print("3. Calcul des scores empiriques...")
        print()
        
        for (event_key, country), events_df in tqdm(grouped, total=total_groups, desc="Calcul scores"):
            if len(events_df) < min_events:
                continue
            
            result = calculate_scores_for_event_family(
                conn, event_key, country, events_df, verbose=False
            )
            
            if result:
                results.append(result)
        
        print()
        print(f"✅ {len(results)} scores calculés")
        print()
        
        # 4. Créer DataFrame résultats
        if not results:
            print("❌ Aucun score calculé")
            return
        
        df_results = pd.DataFrame(results)
        
        # Statistiques
        print("4. Statistiques des scores calculés...")
        print()
        print(f"   Score moyen : {df_results['empirical_score'].mean():.2f}")
        print(f"   Score médian : {df_results['empirical_score'].median():.2f}")
        print(f"   Score min : {df_results['empirical_score'].min():.2f}")
        print(f"   Score max : {df_results['empirical_score'].max():.2f}")
        print(f"   Échantillon moyen : {df_results['sample_size'].mean():.1f} événements")
        print()
        
        # 5. Sauvegarder ou mettre à jour DB
        if dry_run:
            print("5. Mode DRY RUN - Aucune modification de la DB")
            print()
            print("Top 10 scores calculés :")
            print(df_results.nlargest(10, 'empirical_score')[['event_key', 'country', 'empirical_score', 'sample_size']])
        else:
            print("5. Mise à jour de la table event_families...")
            print()
            
            # Sauvegarder ancienne table
            conn.execute("CREATE TABLE IF NOT EXISTS event_families_backup AS SELECT * FROM event_families")
            print("✅ Backup créé : event_families_backup")
            
            # Mettre à jour ou insérer
            for _, row in df_results.iterrows():
                # Vérifier si existe
                query_check = """
                SELECT COUNT(*) as n
                FROM event_families
                WHERE event_key = ? AND country = ?
                """
                exists = conn.execute(query_check, [row['event_key'], row['country']]).fetchone()[0] > 0
                
                if exists:
                    # UPDATE
                    query_update = """
                    UPDATE event_families
                    SET empirical_score = ?,
                        avg_movement_pips = ?,
                        sample_size = ?,
                        latency_median = ?,
                        latency_p20 = ?,
                        latency_p80 = ?
                    WHERE event_key = ? AND country = ?
                    """
                    conn.execute(query_update, [
                        row['empirical_score'],
                        row['avg_movement_pips'],
                        row['sample_size'],
                        row['latency_median'],
                        row['latency_p20'],
                        row['latency_p80'],
                        row['event_key'],
                        row['country']
                    ])
                else:
                    # INSERT
                    query_insert = """
                    INSERT INTO event_families 
                    (event_key, country, empirical_score, avg_movement_pips, sample_size, 
                     latency_median, latency_p20, latency_p80, family)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """
                    conn.execute(query_insert, [
                        row['event_key'],
                        row['country'],
                        row['empirical_score'],
                        row['avg_movement_pips'],
                        row['sample_size'],
                        row['latency_median'],
                        row['latency_p20'],
                        row['latency_p80']
                    ])
            
            print(f"✅ {len(df_results)} scores mis à jour dans event_families")
            print()
        
        print("="*100)
        print("✅ RECALCUL TERMINÉ")
        print("="*100)
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Recalcul scores empiriques depuis Finnhub')
    parser.add_argument('--start-date', type=str, default='2020-01-01', help='Date début (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None, help='Date fin (YYYY-MM-DD)')
    parser.add_argument('--countries', type=str, nargs='+', default=['US'], help='Pays à traiter')
    parser.add_argument('--min-events', type=int, default=MIN_SAMPLE_SIZE, help='Min événements par famille')
    parser.add_argument('--dry-run', action='store_true', help='Mode test (ne pas modifier DB)')
    parser.add_argument('--verbose', action='store_true', help='Afficher détails')
    
    args = parser.parse_args()
    
    recalculate_empirical_scores_finnhub(
        db_path=DB_PATH,
        start_date=args.start_date,
        end_date=args.end_date,
        countries=args.countries,
        min_events=args.min_events,
        verbose=args.verbose,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    main()

