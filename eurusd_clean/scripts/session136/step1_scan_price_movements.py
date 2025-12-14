"""
ÉTAPE 1 - SCANNER MOUVEMENTS FORTS DANS PRICES_BERN
Session 136 - Workflow LOO-CV DoubleWave_Overlap

Workflow exact (doublewave_loo_validation.mermaid):
┌─────────────────────────────────────────────────┐
│ ÉTAPE 1: Rechercher mouvements forts            │
│          dans prices_bern                       │
│          Critère: impact > X pips               │
│          Période: 3 dernières années            │
│                                                 │
│ Output: Liste mouvements forts trouvés:        │
│         - date                                  │
│         - heure                                 │
│         - impact_pips                           │
│         - direction                             │
└─────────────────────────────────────────────────┘

PAS de référence aux événements ici.
PAS de détection pattern ici.
Juste: scanner prix, trouver pics.

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# =============================================================================
# PARAMÈTRES
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
PERIOD_START = "2023-01-01 00:00:00"
PERIOD_END = "2025-12-31 23:59:59"
MIN_IMPACT_PIPS = 40.0
WINDOW_MINUTES = 60  # Fenêtre d'observation pour pic
BASELINE_LOOKBACK = 10  # Minutes pour baseline
MIN_HOURS_BETWEEN_MOVEMENTS = 2  # Minimum 2h entre 2 mouvements

# =============================================================================
# FONCTION PRINCIPALE - SCAN PRIX
# =============================================================================

def scan_price_movements(conn, start_date, end_date, min_impact):
    """
    Scanner prices_bern pour mouvements forts.
    
    Méthode:
    1. Charger tous les prix période (minute par minute)
    2. Pour chaque bougie: calculer baseline (moyenne 10 min avant)
    3. Calculer impact max dans les 60 min suivantes
    4. Si impact ≥ min_impact: stocker mouvement
    
    Args:
        conn: Connexion DuckDB
        start_date: Début période (str ISO)
        end_date: Fin période (str ISO)
        min_impact: Impact minimum en pips
    
    Returns:
        List[Dict]: Mouvements trouvés
            {
                'datetime': datetime du début mouvement,
                'impact_pips': float,
                'direction': 'UP' | 'DOWN',
                'baseline_price': float,
                'peak_price': float,
                'peak_time': datetime du pic,
                'minutes_to_peak': float
            }
    """
    print(f"\n📊 Chargement prix {start_date} → {end_date}...")
    
    # Charger TOUS les prix période
    query = """
    SELECT datetime, open, high, low, close
    FROM prices_bern
    WHERE datetime >= ?
      AND datetime <= ?
    ORDER BY datetime
    """
    
    df_prices = conn.execute(query, [start_date, end_date]).df()
    
    print(f"   ✅ {len(df_prices):,} bougies chargées")
    
    if len(df_prices) == 0:
        print("   ❌ AUCUN prix trouvé dans la période")
        return []
    
    # Convertir timezone si nécessaire
    if df_prices['datetime'].dt.tz is None:
        df_prices['datetime'] = df_prices['datetime'].dt.tz_localize('Europe/Zurich')
    
    print(f"   Première bougie : {df_prices['datetime'].iloc[0]}")
    print(f"   Dernière bougie : {df_prices['datetime'].iloc[-1]}")
    
    movements = []
    
    print(f"\n🔍 Scanning mouvements ≥{min_impact} pips...")
    print(f"   Fenêtre observation: {WINDOW_MINUTES} min")
    print(f"   Baseline lookback: {BASELINE_LOOKBACK} min")
    
    # Scanner chaque bougie comme point de départ potentiel
    total_candles = len(df_prices) - WINDOW_MINUTES
    
    for i in range(total_candles):
        
        # Progress bar tous les 10000 points
        if i % 10000 == 0 and i > 0:
            progress = (i / total_candles) * 100
            print(f"   Progression: {progress:.1f}% ({i:,}/{total_candles:,}) - {len(movements)} mouvements trouvés")
        
        current_time = df_prices.iloc[i]['datetime']
        
        # Baseline = moyenne BASELINE_LOOKBACK min AVANT (filtrer par temps)
        baseline_start = current_time - timedelta(minutes=BASELINE_LOOKBACK)
        baseline_df = df_prices[
            (df_prices['datetime'] >= baseline_start) & 
            (df_prices['datetime'] < current_time)
        ]
        
        if len(baseline_df) < 5:  # Besoin minimum données pour baseline
            continue
        
        baseline_price = baseline_df['close'].mean()
        
        # Chercher pic dans les WINDOW_MINUTES min APRÈS (filtrer par temps, pas index !)
        future_end = current_time + timedelta(minutes=WINDOW_MINUTES)
        future_window = df_prices[
            (df_prices['datetime'] >= current_time) & 
            (df_prices['datetime'] <= future_end)
        ]
        
        if len(future_window) < 10:  # Besoin minimum données
            continue
        
        # Calculer impacts UP et DOWN
        max_high = future_window['high'].max()
        min_low = future_window['low'].min()
        
        impact_up = (max_high - baseline_price) * 10000  # pips
        impact_down = (baseline_price - min_low) * 10000
        
        # Déterminer direction et impact dominant
        if impact_up >= impact_down:
            impact_pips = impact_up
            direction = 'UP'
            peak_price = max_high
            # Trouver timestamp du peak (pas index)
            peak_time = future_window.loc[future_window['high'].idxmax(), 'datetime']
        else:
            impact_pips = impact_down
            direction = 'DOWN'
            peak_price = min_low
            # Trouver timestamp du peak (pas index)
            peak_time = future_window.loc[future_window['low'].idxmin(), 'datetime']
        
        # Si impact suffisant: vérifier si pas doublon récent
        if impact_pips >= min_impact:
            
            # Vérifier que pas déjà un mouvement récent (éviter doublons)
            if movements:
                last_movement_time = movements[-1]['datetime']
                minutes_since_last = (current_time - last_movement_time).total_seconds() / 60
                
                # Si mouvement < MIN_HOURS_BETWEEN_MOVEMENTS du précédent
                if minutes_since_last < (MIN_HOURS_BETWEEN_MOVEMENTS * 60):
                    # Garder le plus fort
                    if impact_pips > movements[-1]['impact_pips']:
                        # Remplacer le dernier par celui-ci (plus fort)
                        movements[-1] = {
                            'datetime': current_time,
                            'impact_pips': impact_pips,
                            'direction': direction,
                            'baseline_price': baseline_price,
                            'peak_price': peak_price,
                            'peak_time': peak_time,
                            'minutes_to_peak': (peak_time - current_time).total_seconds() / 60
                        }
                    # Sinon skip (moins fort)
                    continue
            
            # Ajouter mouvement
            movements.append({
                'datetime': current_time,
                'impact_pips': impact_pips,
                'direction': direction,
                'baseline_price': baseline_price,
                'peak_price': peak_price,
                'peak_time': peak_time,
                'minutes_to_peak': (peak_time - current_time).total_seconds() / 60
            })
    
    print(f"\n   ✅ {len(movements)} mouvements ≥{min_impact} pips trouvés")
    
    return movements


def calculate_statistics(movements):
    """
    Calculer statistiques des mouvements trouvés.
    
    Args:
        movements: Liste mouvements
    
    Returns:
        dict: Statistiques
    """
    if not movements:
        return {
            'count': 0,
            'impact_mean': 0,
            'impact_median': 0,
            'impact_min': 0,
            'impact_max': 0,
            'direction_up_pct': 0,
            'direction_down_pct': 0
        }
    
    impacts = [m['impact_pips'] for m in movements]
    directions = [m['direction'] for m in movements]
    
    n_up = directions.count('UP')
    n_down = directions.count('DOWN')
    
    return {
        'count': len(movements),
        'impact_mean': np.mean(impacts),
        'impact_median': np.median(impacts),
        'impact_min': min(impacts),
        'impact_max': max(impacts),
        'direction_up_count': n_up,
        'direction_down_count': n_down,
        'direction_up_pct': (n_up / len(movements)) * 100,
        'direction_down_pct': (n_down / len(movements)) * 100
    }


def main():
    """
    Workflow principal ÉTAPE 1.
    """
    print("=" * 80)
    print("ÉTAPE 1 : SCANNER MOUVEMENTS FORTS DANS PRICES_BERN")
    print("Session 136 - Workflow LOO-CV")
    print("=" * 80)
    
    # Vérifier DB existe
    if not DB_PATH.exists():
        print(f"\n❌ ERREUR : Base de données introuvable")
        print(f"   Chemin : {DB_PATH}")
        return
    
    # Connexion DB
    print(f"\n📂 Connexion base de données...")
    print(f"   Chemin : {DB_PATH}")
    
    conn = duckdb.connect(str(DB_PATH))
    
    # Vérifier table prices_bern existe
    tables = conn.execute("SHOW TABLES").df()
    if 'prices_bern' not in tables['name'].values:
        print(f"\n❌ ERREUR : Table prices_bern introuvable")
        conn.close()
        return
    
    print(f"   ✅ Table prices_bern trouvée")
    
    # 1. Scanner prix
    print(f"\n1️⃣ SCAN PRIX")
    print(f"   Période : {PERIOD_START} → {PERIOD_END}")
    print(f"   Critère : Impact ≥ {MIN_IMPACT_PIPS} pips")
    print(f"   Espacement minimum : {MIN_HOURS_BETWEEN_MOVEMENTS}h entre mouvements")
    
    movements = scan_price_movements(
        conn=conn,
        start_date=PERIOD_START,
        end_date=PERIOD_END,
        min_impact=MIN_IMPACT_PIPS
    )
    
    conn.close()
    
    # 2. Statistiques
    print(f"\n2️⃣ STATISTIQUES")
    
    stats = calculate_statistics(movements)
    
    if stats['count'] == 0:
        print(f"   ❌ AUCUN mouvement trouvé")
        print(f"   Critère trop strict ? Essayer MIN_IMPACT_PIPS < 40")
        return
    
    print(f"   Total mouvements : {stats['count']}")
    print(f"   Impact moyen     : {stats['impact_mean']:.1f} pips")
    print(f"   Impact médian    : {stats['impact_median']:.1f} pips")
    print(f"   Impact min       : {stats['impact_min']:.1f} pips")
    print(f"   Impact max       : {stats['impact_max']:.1f} pips")
    print(f"   Direction UP     : {stats['direction_up_count']} ({stats['direction_up_pct']:.1f}%)")
    print(f"   Direction DOWN   : {stats['direction_down_count']} ({stats['direction_down_pct']:.1f}%)")
    
    # 3. Sauvegarder résultats
    print(f"\n3️⃣ SAUVEGARDE")
    
    output_path = Path(__file__).parent / "step1_price_movements.csv"
    df_results = pd.DataFrame(movements)
    
    # Convertir datetime en string pour CSV
    df_results['datetime'] = df_results['datetime'].astype(str)
    df_results['peak_time'] = df_results['peak_time'].astype(str)
    
    df_results.to_csv(output_path, index=False)
    
    print(f"   💾 Fichier : {output_path}")
    print(f"   📊 Lignes : {len(df_results)}")
    
    # 4. Afficher échantillon
    if len(movements) > 0:
        print(f"\n4️⃣ ÉCHANTILLON (10 premiers mouvements)")
        print(f"   {'Date/Heure':<20} {'Impact':>10} {'Direction':>10} {'Peak (min)':>12}")
        print(f"   {'-'*20} {'-'*10} {'-'*10} {'-'*12}")
        
        for i, m in enumerate(movements[:10], 1):
            # Parser datetime depuis string si nécessaire
            if isinstance(m['datetime'], str):
                dt = pd.to_datetime(m['datetime'])
            else:
                dt = m['datetime']
            
            dt_str = dt.strftime('%Y-%m-%d %H:%M')
            print(f"   {dt_str:<20} {m['impact_pips']:>10.1f} {m['direction']:>10} {m['minutes_to_peak']:>12.1f}")
    
    print(f"\n✅ ÉTAPE 1 TERMINÉE")
    print(f"   Fichier prêt pour ÉTAPE 2 (matching clusters)")
    
    # 5. Validation automatique
    print(f"\n5️⃣ VALIDATION AUTOMATIQUE")
    
    if stats['count'] >= 10:
        print(f"   ✅ N≥10 mouvements → Objectif atteint !")
    elif stats['count'] >= 3:
        print(f"   ⚠️  N<10 mais N≥3 → Workflow possible (sous-optimal)")
    else:
        print(f"   ❌ N<3 → Workflow LOO-CV impossible")
    
    return movements


if __name__ == "__main__":
    movements = main()
