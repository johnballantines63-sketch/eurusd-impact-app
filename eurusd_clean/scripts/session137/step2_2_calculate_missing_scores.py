"""
ÉTAPE 2.2 - CALCULER SCORES EMPIRIQUES MANQUANTS
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Lire 295 event_keys sans scores
2. Pour chaque event_key : analyser occurrences historiques
3. Mesurer impact réel dans prices_bern (méthodologie Session 98)
4. Calculer score empirique = moyenne impacts
5. Insérer dans event_families

Méthodologie mesure impact (Session 98 validée) :
- Baseline : 5 min AVANT événement (CLOSE)
- Peak : Maximum HIGH dans 60 min APRÈS événement
- Impact : (peak - baseline) × 10000 (pips)

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import time

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
MISSING_SCORES_FILE = Path(__file__).parent / "step2_1_missing_scores.txt"
OUTPUT_LOG = Path(__file__).parent / "step2_2_calculated_scores_log.csv"

# =============================================================================
# FONCTION MESURE IMPACT (Session 98)
# =============================================================================

def measure_impact_for_event(conn, event_timestamp_utc):
    """
    Mesurer impact réel d'un événement dans prices_bern
    
    Méthodologie Session 98 :
    1. Baseline = CLOSE 5 min avant événement
    2. Peak = MAX(HIGH) dans 60 min après événement
    3. Impact = (peak - baseline) × 10000
    
    Args:
        conn: Connexion DuckDB
        event_timestamp_utc: datetime événement (UTC)
    
    Returns:
        float: impact en pips (ou None si données manquantes)
    """
    
    # Convertir UTC → Europe/Zurich
    event_time_bern = pd.to_datetime(event_timestamp_utc).tz_convert('Europe/Zurich')
    
    # Baseline : 5 min avant
    baseline_start = event_time_bern - timedelta(minutes=5)
    
    # Peak window : 0-60 min après
    peak_end = event_time_bern + timedelta(minutes=60)
    
    try:
        # 1. Trouver baseline (dernier CLOSE avant événement)
        query_baseline = """
        SELECT close
        FROM prices_bern
        WHERE datetime >= ?
          AND datetime < ?
        ORDER BY datetime DESC
        LIMIT 1
        """
        
        result_baseline = conn.execute(query_baseline, [baseline_start, event_time_bern]).fetchone()
        
        if not result_baseline:
            return None
        
        baseline_price = result_baseline[0]
        
        # 2. Trouver peak (max HIGH après événement)
        query_peak = """
        SELECT MAX(high) as peak_high
        FROM prices_bern
        WHERE datetime >= ?
          AND datetime <= ?
        """
        
        result_peak = conn.execute(query_peak, [event_time_bern, peak_end]).fetchone()
        
        if not result_peak or result_peak[0] is None:
            return None
        
        peak_price = result_peak[0]
        
        # 3. Calculer impact
        impact_pips = (peak_price - baseline_price) * 10000
        
        # Valeur absolue (direction pas importante pour score empirique)
        return abs(impact_pips)
        
    except Exception as e:
        print(f"      Erreur mesure impact : {e}")
        return None

# =============================================================================
# FONCTION CALCUL SCORE EMPIRIQUE
# =============================================================================

def calculate_empirical_score_for_key(conn, event_key, limit_occurrences=100):
    """
    Calculer score empirique pour un event_key
    
    Args:
        conn: Connexion DuckDB
        event_key: Clé événement
        limit_occurrences: Limiter nombre occurrences (performance)
    
    Returns:
        dict: {
            'event_key': str,
            'score': float,
            'sample_size': int,
            'min_impact': float,
            'max_impact': float,
            'median_impact': float
        }
    """
    
    # 1. Trouver occurrences événement (limiter à période 2020-2025)
    query_events = """
    SELECT ts_utc, country
    FROM events
    WHERE event_key = ?
      AND ts_utc >= '2020-01-01'
      AND ts_utc <= '2025-12-31'
    ORDER BY ts_utc DESC
    LIMIT ?
    """
    
    occurrences = conn.execute(query_events, [event_key, limit_occurrences]).fetchall()
    
    if not occurrences:
        return None
    
    # 2. Mesurer impact pour chaque occurrence
    impacts = []
    
    for ts_utc, country in occurrences:
        impact = measure_impact_for_event(conn, ts_utc)
        
        if impact is not None and impact > 0:  # Exclure impacts nuls
            impacts.append(impact)
    
    if len(impacts) == 0:
        return None
    
    # 3. Calculer statistiques
    impacts_array = np.array(impacts)
    
    result = {
        'event_key': event_key,
        'country': occurrences[0][1] if occurrences else None,
        'empirical_score': float(np.mean(impacts_array)),
        'avg_movement_pips': float(np.mean(impacts_array)),  # Même valeur
        'sample_size': len(impacts),
        'min_impact': float(np.min(impacts_array)),
        'max_impact': float(np.max(impacts_array)),
        'median_impact': float(np.median(impacts_array)),
        'std_impact': float(np.std(impacts_array))
    }
    
    return result

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def calculate_missing_scores():
    """
    Calculer scores pour 295 event_keys manquants
    """
    
    print("=" * 80)
    print("ÉTAPE 2.2 - CALCUL SCORES EMPIRIQUES MANQUANTS")
    print("=" * 80)
    
    # 1. Charger event_keys manquants
    print("\n📊 ÉTAPE 1 : Chargement event_keys manquants")
    print("-" * 80)
    
    with open(MISSING_SCORES_FILE, 'r') as f:
        missing_keys = [line.strip() for line in f if line.strip()]
    
    print(f"   ✅ {len(missing_keys)} event_keys à calculer")
    
    # 2. Connecter DB
    print("\n📊 ÉTAPE 2 : Connexion database")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=False)
    
    print(f"   ✅ Connexion établie (mode écriture)")
    
    # 3. Calculer scores
    print("\n📊 ÉTAPE 3 : Calcul scores empiriques")
    print("-" * 80)
    print(f"   Limite : 100 occurrences max par event_key (performance)")
    print(f"   Méthodologie : Session 98 (baseline -5min, peak +60min)")
    print()
    
    results = []
    failed = []
    start_time = time.time()
    
    for idx, event_key in enumerate(missing_keys):
        try:
            # Progress
            if (idx + 1) % 10 == 0 or idx == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / (idx + 1) if idx > 0 else 0
                remaining = avg_time * (len(missing_keys) - idx - 1)
                
                print(f"   [{idx + 1:3d}/{len(missing_keys)}] {event_key[:50]:50s} | "
                      f"Temps: {elapsed/60:.1f}min | Restant: ~{remaining/60:.1f}min")
            
            # Calculer score
            score_data = calculate_empirical_score_for_key(conn, event_key)
            
            if score_data:
                results.append(score_data)
            else:
                failed.append({'event_key': event_key, 'reason': 'no_valid_impacts'})
                
        except Exception as e:
            print(f"      ❌ Erreur {event_key}: {e}")
            failed.append({'event_key': event_key, 'reason': str(e)})
    
    # 4. Statistiques calcul
    print("\n📊 ÉTAPE 4 : Statistiques calcul")
    print("-" * 80)
    
    total_time = time.time() - start_time
    
    print(f"   Total event_keys traités          : {len(missing_keys)}")
    print(f"   Scores calculés avec succès       : {len(results)}")
    print(f"   Échecs (pas de données)           : {len(failed)}")
    print(f"   Temps total                       : {total_time/60:.1f} minutes")
    print(f"   Temps moyen par event_key         : {total_time/len(missing_keys):.1f} secondes")
    
    if results:
        # Distribution scores calculés
        scores_values = [r['empirical_score'] for r in results]
        
        print(f"\n   Distribution scores calculés :")
        print(f"      Score minimum  : {min(scores_values):.1f} pips")
        print(f"      Score maximum  : {max(scores_values):.1f} pips")
        print(f"      Score moyen    : {np.mean(scores_values):.1f} pips")
        print(f"      Score médian   : {np.median(scores_values):.1f} pips")
        
        # Par catégorie
        low = sum(1 for s in scores_values if s < 20)
        med = sum(1 for s in scores_values if 20 <= s < 40)
        high = sum(1 for s in scores_values if s >= 40)
        
        print(f"\n   Par catégorie :")
        print(f"      LOW (<20)      : {low:3d} ({100.0 * low / len(scores_values):.1f}%)")
        print(f"      MED (20-40)    : {med:3d} ({100.0 * med / len(scores_values):.1f}%)")
        print(f"      HIGH (≥40)     : {high:3d} ({100.0 * high / len(scores_values):.1f}%)")
    
    # 5. Insertion dans event_families
    print("\n📊 ÉTAPE 5 : Insertion dans event_families")
    print("-" * 80)
    
    if results:
        inserted = 0
        
        for score_data in results:
            try:
                # Vérifier si existe déjà
                check_query = "SELECT COUNT(*) FROM event_families WHERE event_key = ?"
                exists = conn.execute(check_query, [score_data['event_key']]).fetchone()[0]
                
                if exists > 0:
                    # UPDATE
                    update_query = """
                    UPDATE event_families
                    SET empirical_score = ?,
                        avg_movement_pips = ?,
                        sample_size = ?
                    WHERE event_key = ?
                    """
                    conn.execute(update_query, [
                        score_data['empirical_score'],
                        score_data['avg_movement_pips'],
                        score_data['sample_size'],
                        score_data['event_key']
                    ])
                else:
                    # INSERT
                    insert_query = """
                    INSERT INTO event_families (
                        event_key, country, empirical_score, 
                        avg_movement_pips, sample_size
                    ) VALUES (?, ?, ?, ?, ?)
                    """
                    conn.execute(insert_query, [
                        score_data['event_key'],
                        score_data['country'],
                        score_data['empirical_score'],
                        score_data['avg_movement_pips'],
                        score_data['sample_size']
                    ])
                
                inserted += 1
                
            except Exception as e:
                print(f"      ❌ Erreur insertion {score_data['event_key']}: {e}")
        
        # Commit
        conn.commit()
        
        print(f"   ✅ {inserted} scores insérés dans event_families")
    
    # 6. Sauvegarder log
    print("\n📊 ÉTAPE 6 : Sauvegarde log")
    print("-" * 80)
    
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(OUTPUT_LOG, index=False)
        print(f"   ✅ Log créé : {OUTPUT_LOG}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 2.2 COMPLÉTÉE")
    print("=" * 80)
    print(f"\n📋 RÉSULTAT : {len(results)}/{len(missing_keys)} scores calculés et insérés")
    
    return len(results), len(failed)

if __name__ == '__main__':
    success, failed = calculate_missing_scores()
