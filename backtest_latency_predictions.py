#!/usr/bin/env python3
"""
Backtest Latency Predictions
Valide les prédictions de latence vs réactions réelles du marché
Version corrigée avec fix timezone robuste
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import timedelta
import numpy as np

# Ajouter le répertoire parent au path pour imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fx_impact_app.src.latency_analyzer import LatencyAnalyzer


def get_db_path():
    """Retourne le chemin vers la base de données"""
    return project_root / 'fx_impact_app' / 'data' / 'warehouse.duckdb'


def measure_actual_market_reaction(event_ts, threshold_pips=5.0, window_minutes=60):
    """
    Mesure la réaction réelle du marché après un événement.
    Fix: Gestion robuste des timestamps pandas avec timezone.
    
    Args:
        event_ts: Timestamp de l'événement (peut être pandas Timestamp avec tz)
        threshold_pips: Seuil de mouvement considéré comme réaction (défaut 5.0)
        window_minutes: Fenêtre d'observation en minutes (défaut 60)
    
    Returns:
        dict avec latency_minutes, peak_pips, etc. ou None si pas de données
    """
    conn = duckdb.connect(str(get_db_path()))
    
    # === FIX TIMEZONE - Conversion robuste ===
    try:
        # Si c'est un Timestamp pandas avec timezone
        if hasattr(event_ts, 'tz') and event_ts.tz is not None:
            # Convertir en UTC puis enlever timezone pour éviter ambiguïté
            event_ts = event_ts.tz_convert('UTC').tz_localize(None)
        elif isinstance(event_ts, str):
            # Si c'est une string, parser en UTC
            event_ts = pd.to_datetime(event_ts, utc=True).tz_localize(None)
        
        # Forcer conversion via pd.Timestamp pour garantir type cohérent
        event_ts = pd.Timestamp(event_ts)
        
        # Calculer fin de fenêtre
        end_time = event_ts + timedelta(minutes=window_minutes)
        
        # Conversion epoch maintenant safe (timestamps naive UTC)
        event_epoch = int(event_ts.timestamp())
        end_epoch = int(end_time.timestamp())
        
    except Exception as e:
        print(f"❌ ERREUR conversion timestamp: {e}")
        print(f"   event_ts reçu: {event_ts} (type: {type(event_ts)})")
        conn.close()
        return None
    
    # === Requête prices_1m ===
    query = f"""
    SELECT timestamp, close
    FROM prices_1m
    WHERE timestamp >= {event_epoch}
        AND timestamp <= {end_epoch}
    ORDER BY timestamp ASC
    """
    
    try:
        prices = conn.execute(query).fetchall()
        conn.close()
        
        if len(prices) == 0:
            print(f"⚠️  Aucun prix trouvé pour event_epoch={event_epoch} ({event_ts})")
            return None
        
        # Prix de référence (premier prix après événement)
        ref_price = prices[0][1]
        
        # Calculer mouvement max et latence
        max_movement = 0
        max_movement_idx = 0
        latency = None
        direction = None
        
        for i, (ts, price) in enumerate(prices):
            movement_pips = abs(price - ref_price) * 10000
            
            # Tracker mouvement maximum
            if movement_pips > max_movement:
                max_movement = movement_pips
                max_movement_idx = i
            
            # Détecter première réaction significative
            if latency is None and movement_pips >= threshold_pips:
                latency = i  # Latence en minutes
                direction = 'UP' if (price - ref_price) > 0 else 'DOWN'
        
        # Si aucune réaction détectée, latence = durée fenêtre
        if latency is None:
            latency = window_minutes
        
        return {
            'latency_minutes': latency,
            'peak_minutes': max_movement_idx,
            'peak_pips': max_movement,
            'direction': direction if direction else 'NONE',
            'had_reaction': latency < window_minutes,
            'bars_analyzed': len(prices)
        }
        
    except Exception as e:
        print(f"❌ ERREUR requête prices: {e}")
        print(f"   Query: {query}")
        conn.close()
        return None


def detect_event_family(event_key):
    """
    Détecte la famille d'un événement via patterns multi-mots
    
    Args:
        event_key: Libellé de l'événement
    
    Returns:
        Tuple (family_name, pattern) ou (None, None)
    """
    family_patterns = {
        'CPI': 'cpi|consumer price',
        'NFP': 'non farm|nonfarm|payroll',
        'GDP': 'gdp|gross domestic',
        'PMI': 'pmi|purchasing managers',
        'Unemployment': 'unemployment rate',
        'Retail': 'retail sales',
        'FOMC': 'fomc|federal open market',
        'Fed': 'fed|federal reserve|interest rate decision',
        'Jobless': 'jobless claims|initial claims',
        'Inflation': 'inflation rate|ppi|producer price',
        'Confidence': 'confidence|sentiment',
        'Trade': 'trade balance',
        'Manufacturing': 'manufacturing|industrial production',
        'Housing': 'housing|building permits|home sales'
    }
    
    event_lower = event_key.lower()
    
    for family, pattern in family_patterns.items():
        # Split pattern par | pour tester chaque terme
        terms = pattern.split('|')
        for term in terms:
            if term.strip() in event_lower:
                return family, pattern
    
    return None, None


def calculate_surprise(actual, previous):
    """
    Calcule l'effet de surprise d'un événement
    
    Args:
        actual: Valeur réelle
        previous: Valeur précédente
    
    Returns:
        Pourcentage de surprise ou None
    """
    if actual is None or previous is None:
        return None
    
    if previous == 0:
        return None
    
    surprise = ((actual - previous) / abs(previous)) * 100
    return surprise


def run_backtest(num_events=200, min_empirical_score=60):
    """
    Lance le backtest complet sur les événements récents
    
    Args:
        num_events: Nombre d'événements à analyser
        min_empirical_score: Score empirique minimum
    
    Returns:
        DataFrame avec résultats
    """
    print(f"\n{'='*60}")
    print("🔍 BACKTESTING PRÉDICTIONS DE LATENCE")
    print(f"{'='*60}\n")
    
    # Connexion DB
    conn = duckdb.connect(str(get_db_path()))
    
    # Charger événements récents avec bon score empirique
    print(f"Chargement événements récents avec score empirique ≥ {min_empirical_score}...")
    
    query = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.actual,
        e.previous,
        e.forecast,
        ef.empirical_score,
        ef.avg_movement_pips,
        ef.avg_latency_min
    FROM events e
    JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE ef.empirical_score >= {min_empirical_score}
        AND e.actual IS NOT NULL
        AND e.previous IS NOT NULL
        AND e.country IN ('US', 'EU', 'GB', 'JP')
        AND e.ts_utc >= CURRENT_DATE - INTERVAL '90 days'
    ORDER BY e.ts_utc DESC
    LIMIT {num_events}
    """
    
    events_df = conn.execute(query).df()
    conn.close()
    
    print(f"✅ {len(events_df)} événements chargés\n")
    
    if len(events_df) == 0:
        print("❌ Aucun événement trouvé avec ces critères")
        return None
    
    # Initialiser LatencyAnalyzer
    analyzer = LatencyAnalyzer()
    
    # Résultats
    results = []
    
    print("Analyse des réactions réelles...\n")
    
    for idx, event in events_df.iterrows():
        # Détecter famille
        family, pattern = detect_event_family(event['event_key'])
        
        if not family:
            continue
        
        # Calculer surprise
        surprise = calculate_surprise(event['actual'], event['previous'])
        
        # Obtenir stats prédites de latence
        with analyzer:
            stats = analyzer.calculate_family_latency_stats(
                pattern,  # event_pattern (argument positionnel)
                5.0,      # threshold_pips
                5,        # min_occurrences
                730       # days_back
            )
        
        if not stats or stats['events_analyzed'] == 0:
            continue
        
        # Mesurer réaction réelle
        actual_reaction = measure_actual_market_reaction(
            event['ts_utc'],
            threshold_pips=5.0,
            window_minutes=60
        )
        
        if actual_reaction is None:
            continue
        
        # Prédiction latence
        predicted_latency = stats['initial_reaction']['mean_minutes']
        actual_latency = actual_reaction['latency_minutes']
        
        # Affichage progression
        if idx % 10 == 0:
            print(f"Event {idx}: {event['event_key']}, {event['ts_utc']}")
            print(f"  → Bars analyzed: {actual_reaction['bars_analyzed']}")
            print(f"  → Peak: {actual_reaction['peak_pips']:.1f} pips @ {actual_reaction['peak_minutes']} min")
            print(f"  → Latency: {actual_latency} min (pred: {predicted_latency:.1f} min)\n")
        
        # Stocker résultat
        results.append({
            'timestamp': event['ts_utc'],
            'event_key': event['event_key'],
            'country': event['country'],
            'family': family,
            'empirical_score': event['empirical_score'],
            'surprise_pct': surprise,
            'predicted_latency': predicted_latency,
            'actual_latency': actual_latency,
            'error_minutes': abs(predicted_latency - actual_latency),
            'predicted_movement': event['avg_movement_pips'],
            'actual_movement': actual_reaction['peak_pips'],
            'had_reaction': actual_reaction['had_reaction']
        })
    
    # Créer DataFrame résultats
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("❌ Aucune réaction mesurable détectée")
        return None
    
    # Calculer métriques globales
    print(f"\n{'='*60}")
    print("📊 RÉSULTATS BACKTESTING")
    print(f"{'='*60}\n")
    
    print(f"Événements analysés: {len(results_df)}")
    print(f"Événements avec réaction: {results_df['had_reaction'].sum()}")
    print(f"Taux de réaction: {results_df['had_reaction'].mean()*100:.1f}%\n")
    
    # Métriques erreur latence
    mae_latency = results_df['error_minutes'].mean()
    rmse_latency = np.sqrt((results_df['error_minutes']**2).mean())
    
    print("LATENCE:")
    print(f"  MAE (Mean Absolute Error): {mae_latency:.2f} minutes")
    print(f"  RMSE (Root Mean Square Error): {rmse_latency:.2f} minutes")
    print(f"  Latence moyenne prédite: {results_df['predicted_latency'].mean():.2f} min")
    print(f"  Latence moyenne réelle: {results_df['actual_latency'].mean():.2f} min\n")
    
    # Métriques mouvement
    movement_error = abs(results_df['predicted_movement'] - results_df['actual_movement'])
    mae_movement = movement_error.mean()
    
    print("MOUVEMENT:")
    print(f"  MAE mouvement: {mae_movement:.2f} pips")
    print(f"  Mouvement moyen prédit: {results_df['predicted_movement'].mean():.2f} pips")
    print(f"  Mouvement moyen réel: {results_df['actual_movement'].mean():.2f} pips\n")
    
    # Breakdown par famille
    print("BREAKDOWN PAR FAMILLE:")
    family_stats = results_df.groupby('family').agg({
        'error_minutes': 'mean',
        'actual_latency': 'mean',
        'predicted_latency': 'mean',
        'event_key': 'count'
    }).round(2)
    family_stats.columns = ['MAE_latency', 'Latence_réelle', 'Latence_prédite', 'Count']
    print(family_stats.to_string())
    print()
    
    # Sauvegarder résultats
    output_file = project_root / f'backtest_results_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
    results_df.to_csv(output_file, index=False)
    print(f"✅ Résultats sauvegardés: {output_file}\n")
    
    return results_df


if __name__ == "__main__":
    # Lancer backtesting
    results = run_backtest(num_events=200, min_empirical_score=60)
    
    if results is not None:
        print("✅ Backtesting terminé avec succès!")
    else:
        print("❌ Backtesting échoué")
    
