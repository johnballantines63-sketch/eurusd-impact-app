"""
Explication Détaillée du Calcul des Core Scores - Exemple 2025-09-11

Objectif : Expliquer étape par étape comment le score core_scores pour CPI (US) = 75.06
a été calculé, en utilisant 2025-09-11 comme exemple.

Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
import pytz

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH

TZ_BERN = pytz.timezone('Europe/Zurich')

def explain_core_score_calculation():
    """Explique le calcul du core_score pour CPI (US) avec exemple 2025-09-11"""
    
    print("="*100)
    print("EXPLICATION CALCUL CORE SCORES - EXEMPLE 2025-09-11 (CPI US)")
    print("="*100)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Identifier toutes les dates avec CPI (US) sur 3 ans
    print("ÉTAPE 1 : IDENTIFIER TOUTES LES DATES AVEC CPI (US)")
    print("-"*100)
    print()
    
    query_dates = """
    SELECT DISTINCT DATE(e.ts_utc) as date
    FROM events e
    WHERE e.country = 'US'
      AND (LOWER(e.event_key) LIKE '%cpi%' OR LOWER(e.event_title) LIKE '%cpi%')
      AND DATE(e.ts_utc) >= '2023-01-01'
      AND DATE(e.ts_utc) <= '2025-12-06'
      AND e.importance_n >= 2
    ORDER BY date ASC
    """
    
    df_dates = conn.execute(query_dates).df()
    print(f"✅ {len(df_dates)} dates avec CPI (US) identifiées sur 3 ans")
    print()
    
    # 2. Pour chaque date, détecter mouvement fort et mesurer impact réel
    print("ÉTAPE 2 : DÉTECTER MOUVEMENTS FORTS ET MESURER IMPACTS RÉELS")
    print("-"*100)
    print()
    
    impacts_cpi = []
    
    for idx, row in df_dates.iterrows():
        date_str = str(row['date'])
        
        # Détecter mouvement fort pour cette date
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
        
        if df_prices.empty:
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # Baseline : OPEN première bougie à 14:30
        baseline_time = TZ_BERN.localize(datetime.combine(date_dt.date(), datetime.min.time().replace(hour=14, minute=30)))
        prices_at_baseline = df_prices[df_prices.index >= baseline_time]
        
        if prices_at_baseline.empty:
            continue
        
        baseline_price = prices_at_baseline.iloc[0]['open']
        
        # Détecter mouvement significatif
        current_high = baseline_price
        current_low = baseline_price
        movement_start = None
        peak_time = None
        direction = None
        
        for idx_price, row_price in prices_at_baseline.iterrows():
            high_pips = (row_price['high'] - baseline_price) * 10000
            low_pips = (baseline_price - row_price['low']) * 10000
            
            if movement_start is None:
                if high_pips >= 5.0 or low_pips >= 5.0:
                    movement_start = idx_price
                    if high_pips > low_pips:
                        direction = 'UP'
                        current_high = row_price['high']
                        peak_time = idx_price
                    else:
                        direction = 'DOWN'
                        current_low = row_price['low']
                        peak_time = idx_price
            
            if movement_start is not None:
                if direction == 'UP':
                    if row_price['high'] > current_high:
                        current_high = row_price['high']
                        peak_time = idx_price
                else:
                    if row_price['low'] < current_low:
                        current_low = row_price['low']
                        peak_time = idx_price
        
        if movement_start is not None and peak_time is not None:
            if direction == 'UP':
                impact_pips = (current_high - baseline_price) * 10000
            else:
                impact_pips = (baseline_price - current_low) * 10000
            
            if impact_pips >= 20.0:  # Seuil mouvement fort
                impacts_cpi.append({
                    'date': date_str,
                    'impact_pips': impact_pips,
                    'direction': direction
                })
    
    print(f"✅ {len(impacts_cpi)} mouvements forts détectés pour CPI (US)")
    print()
    
    # Afficher quelques exemples
    print("Exemples d'impacts mesurés :")
    for impact in impacts_cpi[:10]:
        print(f"   {impact['date']} : {impact['impact_pips']:.2f} pips ({impact['direction']})")
    if len(impacts_cpi) > 10:
        print(f"   ... et {len(impacts_cpi) - 10} autres")
    print()
    
    # 3. Calculer statistiques
    print("ÉTAPE 3 : CALCULER STATISTIQUES")
    print("-"*100)
    print()
    
    impacts_array = np.array([i['impact_pips'] for i in impacts_cpi])
    
    avg = np.mean(impacts_array)
    median = np.median(impacts_array)
    p80 = np.percentile(impacts_array, 80)
    std = np.std(impacts_array)
    min_impact = np.min(impacts_array)
    max_impact = np.max(impacts_array)
    sample_size = len(impacts_array)
    
    print(f"Statistiques sur {sample_size} occurrences :")
    print(f"   Moyenne (avg) : {avg:.2f} pips")
    print(f"   Médiane : {median:.2f} pips")
    print(f"   P80 (80ème percentile) : {p80:.2f} pips")
    print(f"   Écart-type : {std:.2f} pips")
    print(f"   Min : {min_impact:.2f} pips")
    print(f"   Max : {max_impact:.2f} pips")
    print()
    
    # 4. Calculer score empirique (formule actuelle)
    print("ÉTAPE 4 : CALCULER SCORE EMPIRIQUE")
    print("-"*100)
    print()
    
    # Formule : base_score = (avg * 0.5 + p80 * 0.5) * robustness
    base_score = (avg * 0.5 + p80 * 0.5)
    print(f"Base score = (avg × 0.5 + p80 × 0.5)")
    print(f"           = ({avg:.2f} × 0.5 + {p80:.2f} × 0.5)")
    print(f"           = {avg * 0.5:.2f} + {p80 * 0.5:.2f}")
    print(f"           = {base_score:.2f}")
    print()
    
    # Facteur de robustesse
    if sample_size >= 20:
        robustness = 1.0
        robustness_desc = "≥ 20 occurrences"
    elif sample_size >= 10:
        robustness = 0.9
        robustness_desc = "10-19 occurrences"
    elif sample_size >= 5:
        robustness = 0.8
        robustness_desc = "5-9 occurrences"
    else:
        robustness = 0.7
        robustness_desc = "< 5 occurrences"
    
    print(f"Facteur de robustesse : {robustness} ({robustness_desc})")
    print(f"   Sample size : {sample_size}")
    print()
    
    # Score final
    score_empirical = base_score * robustness
    score_normalized = min(100.0, score_empirical)
    
    print(f"Score empirique = base_score × robustness")
    print(f"                = {base_score:.2f} × {robustness}")
    print(f"                = {score_empirical:.2f}")
    print()
    print(f"Score normalisé (max 100) = min(100.0, {score_empirical:.2f})")
    print(f"                         = {score_normalized:.2f}")
    print()
    
    # 5. Vérifier avec score dans DB
    print("ÉTAPE 5 : VÉRIFICATION AVEC SCORE DANS DB")
    print("-"*100)
    print()
    
    query_db_score = """
    SELECT empirical_score, avg_impact_pips, p80_impact_pips, sample_size
    FROM core_scores
    WHERE core_type = 'CPI' AND country = 'US'
    """
    
    db_result = conn.execute(query_db_score).fetchone()
    
    if db_result:
        db_score, db_avg, db_p80, db_sample = db_result
        print(f"Score dans DB : {db_score:.2f}")
        print(f"   Avg impact : {db_avg:.2f} pips")
        print(f"   P80 impact : {db_p80:.2f} pips")
        print(f"   Sample size : {db_sample}")
        print()
        
        print(f"✅ Vérification :")
        print(f"   Score calculé : {score_normalized:.2f}")
        print(f"   Score DB : {db_score:.2f}")
        if abs(score_normalized - db_score) < 0.1:
            print(f"   ✅ Correspondance parfaite !")
        else:
            print(f"   ⚠️  Différence : {abs(score_normalized - db_score):.2f}")
    
    # 6. Exemple spécifique 2025-09-11
    print()
    print("="*100)
    print("EXEMPLE SPÉCIFIQUE : 2025-09-11")
    print("="*100)
    print()
    
    # Chercher impact pour 2025-09-11
    impact_2025_09_11 = next((i for i in impacts_cpi if i['date'] == '2025-09-11'), None)
    
    if impact_2025_09_11:
        print(f"Impact réel mesuré pour 2025-09-11 : {impact_2025_09_11['impact_pips']:.2f} pips")
        print()
        print(f"Ce mouvement contribue au calcul du score core_scores CPI (US) :")
        print(f"   - Il fait partie des {sample_size} occurrences utilisées")
        print(f"   - Il contribue à la moyenne : {avg:.2f} pips")
        print(f"   - Il contribue au P80 : {p80:.2f} pips")
        print(f"   - Score final CPI (US) : {score_normalized:.2f}")
        print()
        print(f"📊 Position dans la distribution :")
        impacts_sorted = sorted([i['impact_pips'] for i in impacts_cpi])
        position = impacts_sorted.index(impact_2025_09_11['impact_pips']) + 1
        percentile = (position / len(impacts_sorted)) * 100
        print(f"   Rang : {position}/{len(impacts_sorted)}")
        print(f"   Percentile : {percentile:.1f}%")
    else:
        print("⚠️  2025-09-11 n'a pas été détecté comme mouvement fort (≥ 20 pips)")
        print("   Cela peut être dû à :")
        print("   - Mouvement < 20 pips")
        print("   - Pas de données prix disponibles")
        print("   - Mouvement détecté mais non inclus dans le calcul")
    
    conn.close()
    
    print()
    print("="*100)
    print("EXPLICATION TERMINÉE")
    print("="*100)

if __name__ == '__main__':
    explain_core_score_calculation()




