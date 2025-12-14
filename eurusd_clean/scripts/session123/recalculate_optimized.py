"""
RECALCUL SCORES EMPIRIQUES - VERSION OPTIMISÉE

Période : 2022-10 → 2025-11 (overlap events + prix)
Méthode : Agrégation simple, pas de jointures lourdes

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Version optimisée overlap
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm import tqdm

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'

def calculate_empirical_score(avg_movement, p80_movement, sample_size):
    """Calculer score empirique normalisé 0-100"""
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    if sample_size >= 20:
        robustness = 1.0
    elif sample_size >= 10:
        robustness = 0.9
    elif sample_size >= 5:
        robustness = 0.8
    else:
        robustness = 0.7
    
    score = base_score * robustness
    return min(100.0, (score / 100.0) * 100.0)


def recalculate_optimized():
    """Recalcul optimisé sur période overlap uniquement"""
    
    print("=" * 80)
    print("RECALCUL SCORES EMPIRIQUES OPTIMISÉ")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. PÉRIODE OVERLAP
    # ========================================================================
    
    print("PÉRIODE OVERLAP (events + prix) :")
    print("-" * 80)
    print("   2022-10-23 → 2025-11-05 (3 ans)")
    print()
    
    # ========================================================================
    # 2. IDENTIFIER FAMILLES
    # ========================================================================
    
    print("IDENTIFICATION FAMILLES :")
    print("-" * 80)
    print()
    
    query_families = """
    SELECT 
        event_name,
        country,
        COUNT(*) as occurrences
    FROM economic_events
    WHERE datetime_utc >= '2022-10-23'
      AND datetime_utc <= '2025-11-05'
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    GROUP BY event_name, country
    HAVING COUNT(*) >= 3
    ORDER BY occurrences DESC
    """
    
    families = conn.execute(query_families).df()
    
    print(f"✅ {len(families)} familles identifiées (min 3 occurrences)")
    print()
    
    # ========================================================================
    # 3. CALCULER IMPACTS - VERSION SIMPLIFIÉE
    # ========================================================================
    
    print("CALCUL IMPACTS :")
    print("-" * 80)
    print()
    print("Méthode : Lookup Python (évite jointures SQL lourdes)")
    print()
    
    results = []
    
    # Charger tous les prix une fois (mémoire ~10MB)
    print("Chargement prix en mémoire...")
    query_prices = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= '2022-10-23'
      AND datetime <= '2025-11-05'
    ORDER BY datetime
    """
    
    prices_df = conn.execute(query_prices).df()
    prices_df['datetime'] = pd.to_datetime(prices_df['datetime'])
    prices_df = prices_df.set_index('datetime')
    
    print(f"✅ {len(prices_df):,} bars chargés")
    print()
    
    # Pour chaque famille
    for idx, family in tqdm(families.iterrows(), total=len(families), desc="Familles"):
        event_name = family['event_name']
        country = family['country']
        
        # Charger occurrences
        query_occ = """
        SELECT datetime_utc
        FROM economic_events
        WHERE event_name = ?
          AND country = ?
          AND datetime_utc >= '2022-10-23'
          AND datetime_utc <= '2025-11-05'
        ORDER BY datetime_utc
        """
        
        occurrences = conn.execute(query_occ, [event_name, country]).df()
        
        impacts = []
        
        for _, occ in occurrences.iterrows():
            # Timestamp événement (UTC)
            event_dt_utc = pd.to_datetime(occ['datetime_utc']).tz_localize('UTC')
            event_dt_bern = event_dt_utc.tz_convert('Europe/Zurich')
            
            # Baseline (1 min avant)
            baseline_dt = event_dt_bern - pd.Timedelta(minutes=1)
            
            try:
                # Lookup baseline dans prices
                if baseline_dt not in prices_df.index:
                    # Chercher prix le plus proche avant
                    before_prices = prices_df.loc[:baseline_dt]
                    if len(before_prices) == 0:
                        continue
                    baseline_price = before_prices.iloc[-1]['close']
                else:
                    baseline_price = prices_df.loc[baseline_dt, 'close']
                
                # Fenêtre post-événement (60 min)
                post_start = event_dt_bern
                post_end = event_dt_bern + pd.Timedelta(minutes=60)
                
                post_prices = prices_df.loc[post_start:post_end]
                
                if len(post_prices) < 5:  # Minimum 5 bars
                    continue
                
                # Calculer impact max
                high_movement = (post_prices['high'].max() - baseline_price) * 10000
                low_movement = (baseline_price - post_prices['low'].min()) * 10000
                
                max_movement = max(abs(high_movement), abs(low_movement))
                
                if max_movement > 0:
                    impacts.append(max_movement)
                    
            except Exception:
                continue
        
        # Statistiques famille
        if len(impacts) >= 3:
            avg_movement = np.mean(impacts)
            median_movement = np.median(impacts)
            p80_movement = np.percentile(impacts, 80)
            
            empirical_score = calculate_empirical_score(
                avg_movement, p80_movement, len(impacts)
            )
            
            results.append({
                'event_name': event_name,
                'country': country,
                'empirical_score': empirical_score,
                'avg_movement_pips': avg_movement,
                'median_movement_pips': median_movement,
                'p80_movement_pips': p80_movement,
                'sample_size': len(impacts)
            })
    
    print()
    print(f"✅ {len(results)} familles analysées avec succès")
    print()
    
    # ========================================================================
    # 4. SAUVEGARDER
    # ========================================================================
    
    df_results = pd.DataFrame(results)
    
    csv_file = OUTPUT_DIR / 'event_families_eodhd_empirical.csv'
    df_results.to_csv(csv_file, index=False)
    
    print(f"✅ Sauvegardé : {csv_file}")
    print(f"   {len(df_results)} familles")
    print()
    
    # ========================================================================
    # 5. STATISTIQUES
    # ========================================================================
    
    print("DISTRIBUTION SCORES :")
    print("-" * 80)
    print()
    
    high = len(df_results[df_results['empirical_score'] >= 40])
    med = len(df_results[(df_results['empirical_score'] >= 20) & (df_results['empirical_score'] < 40)])
    low = len(df_results[df_results['empirical_score'] < 20])
    
    print(f"   HIGH (>=40)  : {high:3d} ({high/len(df_results)*100:.1f}%)")
    print(f"   MEDIUM (>=20): {med:3d} ({med/len(df_results)*100:.1f}%)")
    print(f"   LOW (<20)    : {low:3d} ({low/len(df_results)*100:.1f}%)")
    print()
    
    # TOP 20
    print("TOP 20 ÉVÉNEMENTS :")
    print("-" * 80)
    print()
    
    top20 = df_results.nlargest(20, 'empirical_score')[
        ['event_name', 'country', 'empirical_score', 'avg_movement_pips', 'sample_size']
    ]
    print(top20.to_string(index=False))
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECALCUL TERMINÉ")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python reclassify_from_empirical_csv.py")
    print("   python validate_cluster_sept11.py")
    print()


if __name__ == '__main__':
    recalculate_optimized()
