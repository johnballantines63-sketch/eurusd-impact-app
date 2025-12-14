"""
Script de recalcul des scores empiriques avec P80 uniquement (version test)

Référence : REF-005
Date : 2025-12-06
Version : P80 uniquement (alternative à formule actuelle)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
import pytz
import argparse

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

# Paramètres de calcul
LOOKBACK_MINUTES = 5  # Minutes avant événement pour baseline
LOOKAHEAD_MINUTES = 240  # Minutes après événement pour pic maximum
MIN_SAMPLE_SIZE = 3  # Taille minimum d'échantillon

def calculate_empirical_score_p80_only(p80_movement: float, sample_size: int) -> float:
    """
    Calcule le score empirique avec P80 uniquement (version test)
    
    Formule : score = p80_movement * robustness_factor
    
    Args:
        p80_movement: Mouvement au 80e percentile en pips
        sample_size: Taille de l'échantillon
    
    Returns:
        Score empirique normalisé (0-100)
    """
    # Facteur robustesse basé sur sample_size
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = p80_movement * robustness
    
    # Normalisation simplifiée (REF-005)
    normalized = min(100.0, score)
    
    return normalized

def measure_impact_for_event(conn, event_ts: pd.Timestamp, lookback_min: int = 5, lookahead_min: int = 240) -> float:
    """Mesure l'impact réel d'un événement depuis prices_finnhub_m1"""
    try:
        # Convertir en timezone Bern
        if event_ts.tz is None:
            event_ts = TZ_BERN.localize(event_ts)
        else:
            event_ts = event_ts.astimezone(TZ_BERN)
        
        # Fenêtre de mesure
        window_start = event_ts - timedelta(minutes=lookback_min)
        window_end = event_ts + timedelta(minutes=lookahead_min)
        
        # Requête prix
        query = f"""
        SELECT datetime, open, high, low, close
        FROM prices_finnhub_m1
        WHERE datetime >= '{window_start.strftime('%Y-%m-%d %H:%M:%S')}'
          AND datetime <= '{window_end.strftime('%Y-%m-%d %H:%M:%S')}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query).df()
        
        if df_prices.empty:
            return None
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # Baseline : OPEN de la première bougie à ou après l'événement
        prices_at_event = df_prices[df_prices.index >= event_ts]
        if not prices_at_event.empty:
            baseline_price = prices_at_event.iloc[0]['open']
        else:
            # Fallback : CLOSE de la dernière bougie avant l'événement
            prices_before = df_prices[df_prices.index < event_ts]
            if not prices_before.empty:
                baseline_price = prices_before.iloc[-1]['close']
            else:
                return None
        
        # Pic maximum après événement
        prices_after = df_prices[df_prices.index >= event_ts]
        if prices_after.empty:
            return None
        
        max_high = prices_after['high'].max()
        min_low = prices_after['low'].min()
        
        impact_up = (max_high - baseline_price) * 10000
        impact_down = (baseline_price - min_low) * 10000
        
        impact = max(impact_up, impact_down)
        
        return impact
    
    except Exception as e:
        return None

def recalculate_empirical_scores_p80_only(
    start_date: str = '2020-01-01',
    end_date: str = '2025-12-06',
    countries: list = ['US'],
    min_events: int = 3,
    dry_run: bool = False
):
    """
    Recalcule les scores empiriques avec P80 uniquement
    
    Args:
        start_date: Date de début (YYYY-MM-DD)
        end_date: Date de fin (YYYY-MM-DD)
        countries: Liste des pays à traiter
        min_events: Nombre minimum d'occurrences pour calculer un score
        dry_run: Si True, ne pas mettre à jour la DB
    """
    print("="*100)
    print("RECALCUL SCORES EMPIRIQUES - P80 UNIQUEMENT (VERSION TEST)")
    print("="*100)
    print()
    print(f"⚠️  VERSION TEST : Utilise P80 uniquement au lieu de 50% avg + 50% p80")
    print(f"   Référence : REF-005")
    print()
    print(f"Paramètres :")
    print(f"  Période : {start_date} à {end_date}")
    print(f"  Pays : {', '.join(countries)}")
    print(f"  Minimum occurrences : {min_events}")
    print(f"  Mode : {'DRY RUN' if dry_run else 'PRODUCTION'}")
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # Grouper les événements par event_key et country
    print("1. IDENTIFICATION DES FAMILLES D'ÉVÉNEMENTS")
    print("-"*100)
    print()
    
    countries_str = "', '".join(countries)
    query_families = f"""
    SELECT 
        event_key,
        country,
        COUNT(*) as n_occurrences
    FROM events
    WHERE country IN ('{countries_str}')
      AND DATE(ts_utc) >= '{start_date}'
      AND DATE(ts_utc) <= '{end_date}'
      AND event_key IS NOT NULL
    GROUP BY event_key, country
    HAVING COUNT(*) >= {min_events}
    ORDER BY n_occurrences DESC
    """
    
    df_families = conn.execute(query_families).df()
    
    print(f"✅ {len(df_families)} familles d'événements identifiées")
    print()
    
    if df_families.empty:
        print("❌ Aucune famille trouvée")
        conn.close()
        return
    
    # Calculer scores pour chaque famille
    print("2. CALCUL DES SCORES EMPIRIQUES (P80 UNIQUEMENT)")
    print("-"*100)
    print()
    
    results = []
    total_families = len(df_families)
    
    for idx, family_row in df_families.iterrows():
        event_key = family_row['event_key']
        country = family_row['country']
        n_occurrences = family_row['n_occurrences']
        
        print(f"[{idx+1}/{total_families}] {event_key[:50]:50s} ({country}, n={n_occurrences})", end=' ... ')
        
        # Charger toutes les occurrences de cette famille
        query_events = f"""
        SELECT ts_utc
        FROM events
        WHERE event_key = '{event_key}'
          AND country = '{country}'
          AND DATE(ts_utc) >= '{start_date}'
          AND DATE(ts_utc) <= '{end_date}'
        ORDER BY ts_utc
        """
        
        df_events = conn.execute(query_events).df()
        
        # Mesurer impacts pour chaque occurrence
        impacts = []
        for _, event_row in df_events.iterrows():
            event_ts = pd.to_datetime(event_row['ts_utc'])
            impact = measure_impact_for_event(conn, event_ts)
            if impact is not None and impact > 0:
                impacts.append(impact)
        
        if len(impacts) < min_events:
            print(f"⚠️  Pas assez d'impacts ({len(impacts)}/{n_occurrences})")
            continue
        
        impacts = np.array(impacts)
        
        # Calculer statistiques
        avg = np.mean(impacts)
        median = np.median(impacts)
        p80 = np.percentile(impacts, 80)
        std = np.std(impacts)
        
        # Calculer score avec P80 uniquement
        score_p80 = calculate_empirical_score_p80_only(p80, len(impacts))
        
        print(f"✅ Score P80: {score_p80:.2f} (p80={p80:.2f} pips, n={len(impacts)})")
        
        results.append({
            'event_key': event_key,
            'country': country,
            'empirical_score': score_p80,
            'avg_movement_pips': avg,
            'p80_movement_pips': p80,
            'median_movement_pips': median,
            'std_movement_pips': std,
            'sample_size': len(impacts),
            'n_occurrences': n_occurrences
        })
    
    print()
    print(f"✅ {len(results)} scores calculés")
    print()
    
    if not results:
        print("❌ Aucun score calculé")
        conn.close()
        return
    
    # Afficher statistiques
    print("3. STATISTIQUES")
    print("-"*100)
    print()
    
    df_results = pd.DataFrame(results)
    
    print(f"Scores calculés :")
    print(f"  Moyenne : {df_results['empirical_score'].mean():.2f}")
    print(f"  Médiane : {df_results['empirical_score'].median():.2f}")
    print(f"  Min : {df_results['empirical_score'].min():.2f}")
    print(f"  Max : {df_results['empirical_score'].max():.2f}")
    print()
    
    print(f"P80 movements :")
    print(f"  Moyenne : {df_results['p80_movement_pips'].mean():.2f} pips")
    print(f"  Médiane : {df_results['p80_movement_pips'].median():.2f} pips")
    print()
    
    # Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / f'empirical_scores_p80_only_{start_date}_{end_date}.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    # Mettre à jour DB si pas dry_run
    if not dry_run:
        print("4. MISE À JOUR BASE DE DONNÉES")
        print("-"*100)
        print()
        
        print("⚠️  ATTENTION : Cette version utilise P80 uniquement")
        print("   Les scores seront différents de la formule actuelle (~13% plus élevés)")
        print()
        
        # Insérer ou mettre à jour dans event_families
        for _, row in df_results.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO event_families (
                    event_key, country, family, empirical_score,
                    avg_movement_pips, sample_size,
                    latency_median, latency_p20, latency_p80,
                    ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                row['event_key'],
                row['country'],
                None,  # family
                round(row['empirical_score'], 6),
                round(row['avg_movement_pips'], 6),
                row['sample_size'],
                None, None, None,  # latency
                None, None, None,  # ttr
                round(row['p80_movement_pips'], 6),  # mfe_p80
                None  # n_events_latency
            ])
        
        print(f"✅ {len(df_results)} scores mis à jour dans event_families")
        print()
        print("⚠️  NOTE : Ces scores utilisent P80 uniquement (version test)")
        print("   Pour revenir à la formule actuelle, utiliser recalculate_empirical_scores_finnhub.py")
    else:
        print("4. DRY RUN - Pas de mise à jour DB")
        print("-"*100)
        print()
        print("✅ Mode dry run : aucune modification de la DB")
    
    conn.close()
    
    print()
    print("="*100)
    print("TERMINÉ")
    print("="*100)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recalcul scores empiriques avec P80 uniquement')
    parser.add_argument('--start-date', type=str, default='2020-01-01', help='Date début (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-12-06', help='Date fin (YYYY-MM-DD)')
    parser.add_argument('--countries', type=str, nargs='+', default=['US'], help='Pays à traiter')
    parser.add_argument('--min-events', type=int, default=3, help='Minimum occurrences')
    parser.add_argument('--dry-run', action='store_true', help='Mode dry run (pas de mise à jour DB)')
    
    args = parser.parse_args()
    
    recalculate_empirical_scores_p80_only(
        start_date=args.start_date,
        end_date=args.end_date,
        countries=args.countries,
        min_events=args.min_events,
        dry_run=args.dry_run
    )




