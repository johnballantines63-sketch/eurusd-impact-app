"""
RECALCUL COMPLET SCORES EMPIRIQUES POUR EODHD

Méthodologie scientifique rigoureuse :
1. Identifier toutes familles d'événements (event_name + country)
2. Pour chaque famille, analyser impact historique sur EUR/USD
3. Calculer statistiques empiriques (avg, median, p80)
4. Calculer empirical_score normalisé (0-100)
5. Stocker dans event_families_eodhd

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Recalcul scientifique complet
"""

import duckdb
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta
from tqdm import tqdm

DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'

def calculate_impact_for_event(conn, event_dt, lookforward_minutes=60):
    """
    Calculer impact EUR/USD pour un événement
    
    Args:
        conn: Connexion DuckDB
        event_dt: Timestamp événement
        lookforward_minutes: Durée analyse post-event
    
    Returns:
        Dict avec métriques impact
    """
    
    # Charger prix ±60 min
    start = event_dt - timedelta(minutes=5)
    end = event_dt + timedelta(minutes=lookforward_minutes)
    
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    try:
        prices = conn.execute(query, [start, end]).df()
        
        if len(prices) < 10:  # Pas assez de données
            return None
        
        # Baseline = close avant événement (ou premier open)
        baseline_prices = prices[prices['datetime'] < event_dt]
        if len(baseline_prices) > 0:
            baseline = baseline_prices.iloc[-1]['close']
        else:
            baseline = prices.iloc[0]['open']
        
        # Prix post-événement
        post_prices = prices[prices['datetime'] >= event_dt]
        
        if len(post_prices) == 0:
            return None
        
        # Calculer mouvements en pips (1 pip = 0.0001)
        high_movement = (post_prices['high'].max() - baseline) * 10000
        low_movement = (baseline - post_prices['low'].min()) * 10000
        
        # Maximum Favorable Excursion (plus grand mouvement)
        mfe = max(abs(high_movement), abs(low_movement))
        
        # Direction dominante
        if abs(high_movement) > abs(low_movement):
            direction = 'UP'
            movement = high_movement
        else:
            direction = 'DOWN'
            movement = low_movement
        
        # Time to peak
        if direction == 'UP':
            peak_idx = post_prices['high'].idxmax()
        else:
            peak_idx = post_prices['low'].idxmin()
        
        peak_time = post_prices.loc[peak_idx, 'datetime']
        time_to_peak = (peak_time - event_dt).total_seconds() / 60.0
        
        return {
            'mfe_pips': mfe,
            'movement_pips': abs(movement),
            'direction': direction,
            'time_to_peak': time_to_peak,
            'baseline': baseline,
            'peak_price': post_prices.loc[peak_idx, 'high' if direction == 'UP' else 'low']
        }
        
    except Exception as e:
        print(f"Erreur calcul impact: {e}")
        return None


def calculate_empirical_score(avg_movement, median_movement, p80_movement, sample_size):
    """
    Calculer score empirique normalisé 0-100
    
    Formule : score = (avg_movement * 0.5 + p80_movement * 0.5) * robustness_factor
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
    
    # Normaliser 0-100 (score max observé ~80-100 pips)
    normalized = min(100.0, (score / 100.0) * 100.0)
    
    return normalized


def recalculate_empirical_scores():
    """Recalcul complet scores empiriques EODHD"""
    
    print("=" * 80)
    print("RECALCUL SCORES EMPIRIQUES EODHD")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    # ========================================================================
    # 1. IDENTIFIER FAMILLES D'ÉVÉNEMENTS
    # ========================================================================
    
    print("1. IDENTIFICATION FAMILLES ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    query_families = """
    SELECT 
        event_name,
        country,
        COUNT(*) as occurrences,
        MIN(datetime_utc) as first_occurrence,
        MAX(datetime_utc) as last_occurrence
    FROM economic_events
    WHERE country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    GROUP BY event_name, country
    HAVING COUNT(*) >= 3
    ORDER BY occurrences DESC
    """
    
    families = conn.execute(query_families).df()
    
    print(f"Familles identifiées : {len(families)}")
    print(f"Critère minimum : 3 occurrences")
    print()
    
    print("TOP 10 familles par occurrences :")
    for idx, row in families.head(10).iterrows():
        print(f"   {row['event_name'][:40]:40s} {row['country']:3s} : {row['occurrences']:4d} occurrences")
    print()
    
    # ========================================================================
    # 2. CALCULER IMPACTS POUR CHAQUE FAMILLE
    # ========================================================================
    
    print("2. CALCUL IMPACTS EMPIRIQUES")
    print("=" * 80)
    print()
    
    print(f"Analyse de {len(families)} familles...")
    print("(Cela peut prendre 30-60 minutes)")
    print()
    
    results = []
    
    for idx, family in tqdm(families.iterrows(), total=len(families), desc="Familles"):
        event_name = family['event_name']
        country = family['country']
        
        # Charger toutes occurrences
        query_occurrences = """
        SELECT datetime_utc, actual, forecast, previous
        FROM economic_events
        WHERE event_name = ?
          AND country = ?
        ORDER BY datetime_utc
        """
        
        occurrences = conn.execute(query_occurrences, [event_name, country]).df()
        
        # Calculer impact pour chaque occurrence
        impacts = []
        
        for _, occ in occurrences.iterrows():
            event_dt = pd.to_datetime(occ['datetime_utc'])
            
            impact = calculate_impact_for_event(conn, event_dt, lookforward_minutes=60)
            
            if impact is not None:
                impacts.append(impact)
        
        # Statistiques
        if len(impacts) >= 3:  # Minimum 3 mesures valides
            movements = [imp['movement_pips'] for imp in impacts]
            mfes = [imp['mfe_pips'] for imp in impacts]
            ttps = [imp['time_to_peak'] for imp in impacts]
            
            avg_movement = np.mean(movements)
            median_movement = np.median(movements)
            p80_movement = np.percentile(movements, 80)
            
            avg_mfe = np.mean(mfes)
            median_ttp = np.median(ttps)
            
            empirical_score = calculate_empirical_score(
                avg_movement, median_movement, p80_movement, len(impacts)
            )
            
            results.append({
                'event_name': event_name,
                'country': country,
                'empirical_score': empirical_score,
                'avg_movement_pips': avg_movement,
                'median_movement_pips': median_movement,
                'p80_movement_pips': p80_movement,
                'avg_mfe_pips': avg_mfe,
                'median_time_to_peak': median_ttp,
                'sample_size': len(impacts),
                'total_occurrences': len(occurrences)
            })
    
    print()
    print(f"✅ {len(results)} familles analysées avec succès")
    print()
    
    # ========================================================================
    # 3. STOCKER RÉSULTATS
    # ========================================================================
    
    print("3. STOCKAGE RÉSULTATS")
    print("=" * 80)
    print()
    
    # Créer DataFrame
    df_results = pd.DataFrame(results)
    
    # Drop ancienne table si existe
    conn.execute("DROP TABLE IF EXISTS event_families_eodhd")
    
    # Créer nouvelle table
    conn.execute("""
    CREATE TABLE event_families_eodhd AS 
    SELECT * FROM df_results
    """)
    
    print(f"✅ Table event_families_eodhd créée ({len(df_results)} familles)")
    print()
    
    # ========================================================================
    # 4. STATISTIQUES FINALES
    # ========================================================================
    
    print("4. STATISTIQUES DISTRIBUTION SCORES")
    print("=" * 80)
    print()
    
    query_dist = """
    SELECT 
        CASE 
            WHEN empirical_score >= 60 THEN 'HIGH (60-100)'
            WHEN empirical_score >= 40 THEN 'MEDIUM+ (40-60)'
            WHEN empirical_score >= 20 THEN 'MEDIUM (20-40)'
            ELSE 'LOW (0-20)'
        END as score_range,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM event_families_eodhd) as pct
    FROM event_families_eodhd
    GROUP BY score_range
    ORDER BY score_range DESC
    """
    
    dist = conn.execute(query_dist).df()
    print(dist.to_string())
    print()
    
    # ========================================================================
    # 5. TOP ÉVÉNEMENTS PAR SCORE
    # ========================================================================
    
    print("5. TOP 20 ÉVÉNEMENTS PAR SCORE EMPIRIQUE")
    print("=" * 80)
    print()
    
    query_top = """
    SELECT 
        event_name,
        country,
        empirical_score,
        avg_movement_pips,
        sample_size
    FROM event_families_eodhd
    ORDER BY empirical_score DESC
    LIMIT 20
    """
    
    top = conn.execute(query_top).df()
    print(top.to_string())
    print()
    
    # ========================================================================
    # 6. RECLASSIFICATION IMPORTANCE
    # ========================================================================
    
    print("6. RECLASSIFICATION IMPORTANCE")
    print("=" * 80)
    print()
    
    print("Application seuils :")
    print("   HIGH   >= 40")
    print("   MEDIUM >= 20")
    print("   LOW    < 20")
    print()
    
    # Reset
    conn.execute("UPDATE economic_events SET importance = 'MEDIUM'")
    
    # Reclassifier
    query_reclassify = """
    UPDATE economic_events
    SET importance = (
        SELECT 
            CASE 
                WHEN f.empirical_score >= 40 THEN 'HIGH'
                WHEN f.empirical_score >= 20 THEN 'MEDIUM'
                ELSE 'LOW'
            END
        FROM event_families_eodhd f
        WHERE economic_events.event_name = f.event_name
          AND economic_events.country = f.country
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1
        FROM event_families_eodhd f
        WHERE economic_events.event_name = f.event_name
          AND economic_events.country = f.country
    )
    """
    
    conn.execute(query_reclassify)
    
    print("✅ Reclassification terminée")
    print()
    
    # Distribution finale
    query_final_dist = """
    SELECT 
        importance,
        COUNT(*) as count,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM economic_events) as pct
    FROM economic_events
    GROUP BY importance
    ORDER BY 
        CASE importance 
            WHEN 'HIGH' THEN 1 
            WHEN 'MEDIUM' THEN 2 
            WHEN 'LOW' THEN 3 
        END
    """
    
    final_dist = conn.execute(query_final_dist).df()
    print("Distribution finale importance :")
    print(final_dist.to_string())
    print()
    
    # ========================================================================
    # 7. VÉRIFICATION 11 SEPTEMBRE
    # ========================================================================
    
    print("7. VÉRIFICATION 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    query_sept11 = """
    SELECT 
        e.datetime_utc,
        e.event_name,
        e.country,
        e.importance,
        f.empirical_score,
        f.avg_movement_pips
    FROM economic_events e
    LEFT JOIN event_families_eodhd f
        ON e.event_name = f.event_name
        AND e.country = f.country
    WHERE DATE(e.datetime_utc) = '2025-09-11'
      AND e.importance = 'HIGH'
    ORDER BY e.datetime_utc
    """
    
    sept11 = conn.execute(query_sept11).df()
    
    print(f"Événements HIGH 11 septembre : {len(sept11)}")
    print()
    
    if len(sept11) > 0:
        for idx, row in sept11.iterrows():
            dt = pd.to_datetime(row['datetime_utc'])
            print(f"   {dt.strftime('%H:%M')} - {row['country'].upper()} - {row['event_name']}")
            print(f"      Score: {row['empirical_score']:.1f} | Avg impact: {row['avg_movement_pips']:.1f} pips")
        print()
        print("✅✅✅ SUCCESS !")
    else:
        print("⚠️  Aucun HIGH détecté")
    
    print()
    
    conn.close()
    
    print("=" * 80)
    print("✅ RECALCUL COMPLET TERMINÉ")
    print("=" * 80)
    print()
    print("Prochaines étapes :")
    print("   python validate_cluster_sept11.py")
    print("   python validate_formula_s115_complete.py")
    print()


if __name__ == '__main__':
    recalculate_empirical_scores()
