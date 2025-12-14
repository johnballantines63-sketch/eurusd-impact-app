"""
Script de validation systématique des dates Double Wave
Session 66
Date: 24 octobre 2025

Objectif:
---------
Pour chaque date candidate:
1. Récupérer les événements
2. Déterminer si Double Wave ou Single Wave
3. Calculer prédictions (via formules validées)
4. Récupérer données réelles (prices_1m)
5. Calculer métriques (MAE impact, MAE timing)
6. Documenter résultats

Output:
-------
CSV avec résultats validation + rapport statistique
"""

import duckdb
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Imports modules internes
sys.path.append(str(Path(__file__).parent.parent / "src"))
from double_wave import detect_double_wave_conditions, predict_double_wave_timeline
from formulas_validated import calculate_impact_d, calculate_adjusted_empirical_score

# Chemin base de données
DB_PATH = Path(__file__).parent.parent / "data" / "warehouse.duckdb"


def get_events_for_date(target_date: str):
    """
    Récupère les événements US pour une date donnée.
    
    Parameters:
    -----------
    target_date : str
        Date au format 'YYYY-MM-DD'
    
    Returns:
    --------
    list of dict : Événements avec tous les champs nécessaires
    """
    conn = duckdb.connect(str(DB_PATH))
    
    query = f"""
    SELECT 
        event_key,
        label,
        ts_utc,
        actual,
        estimate,
        forecast,
        previous,
        importance_n,
        country
    FROM events
    WHERE DATE(ts_utc) = '{target_date}'
      AND country = 'US'
      AND actual IS NOT NULL
    ORDER BY ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    return df.to_dict('records')


def get_real_prices(event_time: datetime, duration_minutes: int = 60):
    """
    Récupère les prix réels EUR/USD minute par minute.
    
    Parameters:
    -----------
    event_time : datetime
        Timestamp de publication événement
    duration_minutes : int
        Durée en minutes après événement
    
    Returns:
    --------
    DataFrame avec colonnes: datetime, open, high, low, close
    """
    conn = duckdb.connect(str(DB_PATH))
    
    start_time = event_time
    end_time = event_time + timedelta(minutes=duration_minutes)
    
    query = f"""
    SELECT 
        datetime,
        open,
        high,
        low,
        close
    FROM prices_1m
    WHERE datetime BETWEEN '{start_time}' AND '{end_time}'
    ORDER BY datetime
    """
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    return df


def calculate_real_metrics(prices_df, start_price: float, event_time: datetime):
    """
    Calcule les métriques réelles à partir des prix.
    
    Returns:
    --------
    dict avec:
    - peak_time : datetime du pic absolu
    - peak_pips : amplitude max en pips
    - phase1_peak_time : datetime pic Phase 1 (dans 10 premières min)
    - phase1_pips : amplitude Phase 1
    - pullback_low_time : datetime creux pullback
    - pullback_pips : amplitude pullback
    - phase2_peak_time : datetime pic Phase 2
    - phase2_pips : amplitude Phase 2
    """
    
    if len(prices_df) == 0:
        return None
    
    # Convertir en pips (1 pip = 0.0001 pour EUR/USD)
    prices_df['pips_from_start'] = (prices_df['close'] - start_price) / 0.0001
    
    # Trouver pic absolu
    peak_idx = prices_df['pips_from_start'].idxmax()
    peak_time = prices_df.loc[peak_idx, 'datetime']
    peak_pips = prices_df.loc[peak_idx, 'pips_from_start']
    
    # Analyser structure Double Wave potentielle
    # Phase 1: 10 premières minutes
    phase1_df = prices_df[prices_df['datetime'] <= event_time + timedelta(minutes=10)]
    if len(phase1_df) > 0:
        phase1_peak_idx = phase1_df['pips_from_start'].idxmax()
        phase1_peak_time = phase1_df.loc[phase1_peak_idx, 'datetime']
        phase1_pips = phase1_df.loc[phase1_peak_idx, 'pips_from_start']
    else:
        phase1_peak_time = None
        phase1_pips = 0
    
    # Pullback: entre T+5 et T+15
    pullback_df = prices_df[
        (prices_df['datetime'] > event_time + timedelta(minutes=5)) &
        (prices_df['datetime'] <= event_time + timedelta(minutes=15))
    ]
    if len(pullback_df) > 0:
        pullback_low_idx = pullback_df['pips_from_start'].idxmin()
        pullback_low_time = pullback_df.loc[pullback_low_idx, 'datetime']
        pullback_pips = pullback_df.loc[pullback_low_idx, 'pips_from_start']
    else:
        pullback_low_time = None
        pullback_pips = phase1_pips
    
    # Phase 2: pic absolu si après pullback
    phase2_df = prices_df[prices_df['datetime'] > pullback_low_time] if pullback_low_time else prices_df
    if len(phase2_df) > 0:
        phase2_peak_idx = phase2_df['pips_from_start'].idxmax()
        phase2_peak_time = phase2_df.loc[phase2_peak_idx, 'datetime']
        phase2_pips = phase2_df.loc[phase2_peak_idx, 'pips_from_start']
    else:
        phase2_peak_time = peak_time
        phase2_pips = peak_pips
    
    return {
        'peak_time': peak_time,
        'peak_pips': float(peak_pips),
        'phase1_peak_time': phase1_peak_time,
        'phase1_pips': float(phase1_pips),
        'pullback_low_time': pullback_low_time,
        'pullback_pips': float(pullback_pips),
        'phase2_peak_time': phase2_peak_time,
        'phase2_pips': float(phase2_pips)
    }


def calculate_mae(predicted, actual):
    """Calcule Mean Absolute Error."""
    return abs(predicted - actual)


def calculate_timing_error_minutes(pred_time, actual_time):
    """Calcule erreur timing en minutes."""
    if pred_time is None or actual_time is None:
        return None
    delta = abs((pred_time - actual_time).total_seconds() / 60)
    return delta


def validate_single_date(target_date: str, start_price: float = None):
    """
    Valide une date complète : prédictions vs réel.
    
    Returns:
    --------
    dict avec tous les résultats de validation
    """
    
    print(f"\n{'='*80}")
    print(f"VALIDATION DATE : {target_date}")
    print(f"{'='*80}\n")
    
    # 1. Récupérer événements
    print("1. Récupération événements...")
    events = get_events_for_date(target_date)
    print(f"   ✅ {len(events)} événements trouvés")
    
    if len(events) == 0:
        print("   ⚠️ Aucun événement - abandon")
        return None
    
    # Afficher événements
    for ev in events[:5]:  # Top 5
        print(f"      - {ev['label']} (importance: {ev['importance_n']})")
    
    # 2. Détection Double Wave
    print("\n2. Détection Double Wave...")
    is_double_wave = detect_double_wave_conditions(events)
    print(f"   Résultat: {'✅ DOUBLE WAVE' if is_double_wave else '❌ SINGLE WAVE'}")
    
    # Calculer surprise max
    max_surprise = 0
    for ev in events:
        if ev['estimate'] and ev['estimate'] != 0:
            surprise = abs(ev['actual'] - ev['estimate']) / abs(ev['estimate']) * 100
            max_surprise = max(max_surprise, surprise)
    
    print(f"   Surprise max: {max_surprise:.1f}%")
    print(f"   Cluster size: {len(events)}")
    has_high = any(ev['importance_n'] == 3 for ev in events)
    print(f"   HIGH importance: {'✅' if has_high else '❌'}")
    
    # 3. Calculer prédictions
    print("\n3. Calcul prédictions...")
    
    # Temps événement (premier événement du cluster)
    event_time = events[0]['ts_utc']
    if isinstance(event_time, str):
        event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
    
    # Calculer impact base (Formule D)
    # Simplification: utiliser surprise max et cluster size
    base_impact = max_surprise * 1.5 + len(events) * 2  # Approximation Formule D
    
    print(f"   Impact base (Formule D): {base_impact:.2f} pips")
    
    if is_double_wave:
        timeline = predict_double_wave_timeline(
            base_impact=base_impact,
            surprise_pct=max_surprise,
            cluster_size=len(events),
            start_time=event_time
        )
        print(f"   Phase 1: {timeline['phase1']['impact_pips']} pips @ {timeline['phase1']['peak_time'].strftime('%H:%M')}")
        print(f"   Pullback: {timeline['pullback']['retrace_pips']} pips @ {timeline['pullback']['low_time'].strftime('%H:%M')}")
        print(f"   Phase 2: {timeline['phase2']['impact_pips']} pips @ {timeline['phase2']['peak_time'].strftime('%H:%M')}")
    else:
        timeline = None
        print(f"   Impact prédit: {base_impact:.2f} pips")
    
    # 4. Récupérer prix réels
    print("\n4. Récupération prix réels...")
    prices_df = get_real_prices(event_time, duration_minutes=60)
    print(f"   ✅ {len(prices_df)} bougies 1min récupérées")
    
    if len(prices_df) == 0:
        print("   ⚠️ Aucun prix - abandon")
        return None
    
    # Prix départ (si non fourni, utiliser open première bougie)
    if start_price is None:
        start_price = float(prices_df.iloc[0]['open'])
    
    print(f"   Prix départ: {start_price:.5f}")
    
    # 5. Calculer métriques réelles
    print("\n5. Calcul métriques réelles...")
    real_metrics = calculate_real_metrics(prices_df, start_price, event_time)
    
    if real_metrics is None:
        print("   ⚠️ Impossible calculer métriques")
        return None
    
    print(f"   Pic absolu: {real_metrics['peak_pips']:.2f} pips @ {real_metrics['peak_time'].strftime('%H:%M:%S')}")
    print(f"   Phase 1: {real_metrics['phase1_pips']:.2f} pips @ {real_metrics['phase1_peak_time'].strftime('%H:%M:%S')}")
    print(f"   Pullback: {real_metrics['pullback_pips']:.2f} pips @ {real_metrics['pullback_low_time'].strftime('%H:%M:%S')}")
    print(f"   Phase 2: {real_metrics['phase2_pips']:.2f} pips @ {real_metrics['phase2_peak_time'].strftime('%H:%M:%S')}")
    
    # 6. Calculer erreurs
    print("\n6. Calcul métriques validation...")
    
    if is_double_wave and timeline:
        mae_phase1 = calculate_mae(timeline['phase1']['impact_pips'], real_metrics['phase1_pips'])
        mae_pullback = calculate_mae(timeline['pullback']['retrace_pips'], abs(real_metrics['pullback_pips'] - real_metrics['phase1_pips']))
        mae_phase2 = calculate_mae(timeline['phase2']['impact_pips'], real_metrics['phase2_pips'])
        mae_impact = (mae_phase1 + mae_phase2) / 2
        
        timing_error_phase1 = calculate_timing_error_minutes(timeline['phase1']['peak_time'], real_metrics['phase1_peak_time'])
        timing_error_pullback = calculate_timing_error_minutes(timeline['pullback']['low_time'], real_metrics['pullback_low_time'])
        timing_error_phase2 = calculate_timing_error_minutes(timeline['phase2']['peak_time'], real_metrics['phase2_peak_time'])
        mae_timing = np.mean([timing_error_phase1, timing_error_pullback, timing_error_phase2])
        
        print(f"   MAE Phase 1: {mae_phase1:.2f} pips")
        print(f"   MAE Pullback: {mae_pullback:.2f} pips")
        print(f"   MAE Phase 2: {mae_phase2:.2f} pips")
        print(f"   MAE Impact: {mae_impact:.2f} pips")
        print(f"   MAE Timing: {mae_timing:.2f} minutes")
        
    else:
        mae_impact = calculate_mae(base_impact, real_metrics['peak_pips'])
        mae_timing = None
        mae_phase1 = None
        mae_pullback = None
        mae_phase2 = None
        
        print(f"   MAE Impact: {mae_impact:.2f} pips")
    
    # 7. Résultat consolidé
    result = {
        'date': target_date,
        'event_time': event_time.strftime('%Y-%m-%d %H:%M:%S'),
        'num_events': len(events),
        'max_surprise_pct': round(max_surprise, 2),
        'has_high_importance': has_high,
        'is_double_wave': is_double_wave,
        'base_impact_predicted': round(base_impact, 2),
        'peak_pips_real': round(real_metrics['peak_pips'], 2),
        'mae_impact': round(mae_impact, 2),
        'mae_timing': round(mae_timing, 2) if mae_timing else None,
    }
    
    if is_double_wave and timeline:
        result.update({
            'phase1_predicted': round(timeline['phase1']['impact_pips'], 2),
            'phase1_real': round(real_metrics['phase1_pips'], 2),
            'mae_phase1': round(mae_phase1, 2),
            'pullback_predicted': round(timeline['pullback']['retrace_pips'], 2),
            'pullback_real': round(abs(real_metrics['pullback_pips'] - real_metrics['phase1_pips']), 2),
            'mae_pullback': round(mae_pullback, 2),
            'phase2_predicted': round(timeline['phase2']['impact_pips'], 2),
            'phase2_real': round(real_metrics['phase2_pips'], 2),
            'mae_phase2': round(mae_phase2, 2),
        })
    
    return result


def main():
    """
    Exécution principale : validation de toutes les dates candidates.
    """
    
    print("="*80)
    print("VALIDATION DOUBLE WAVE - SESSION 66")
    print("="*80)
    print()
    
    # Lire dates candidates
    candidates_path = Path(__file__).parent.parent / "data" / "double_wave_candidates_session66.csv"
    
    if not candidates_path.exists():
        print(f"❌ ERREUR: Fichier non trouvé: {candidates_path}")
        print("   Exécuter d'abord: python3 scripts/find_double_wave_candidates_session66.py")
        return
    
    candidates_df = pd.read_csv(candidates_path)
    print(f"✅ {len(candidates_df)} dates candidates chargées\n")
    
    # Filtrer dates prioritaires (meets_double_wave = True)
    priority_dates = candidates_df[candidates_df['meets_double_wave'] == True]
    print(f"Dates prioritaires (critères stricts): {len(priority_dates)}")
    
    if len(priority_dates) == 0:
        print("⚠️ Aucune date prioritaire - utilisation critères élargis")
        priority_dates = candidates_df.head(10)
    
    # Valider chaque date
    results = []
    
    for idx, row in priority_dates.head(10).iterrows():
        target_date = row['event_date']
        result = validate_single_date(target_date)
        
        if result:
            results.append(result)
    
    # Export résultats
    if len(results) > 0:
        results_df = pd.DataFrame(results)
        output_path = Path(__file__).parent.parent / "data" / "double_wave_validation_results_session66.csv"
        results_df.to_csv(output_path, index=False)
        print(f"\n✅ Résultats exportés: {output_path}")
        
        # Statistiques
        print("\n" + "="*80)
        print("STATISTIQUES VALIDATION")
        print("="*80)
        print(f"Dates testées: {len(results)}")
        print(f"Double Wave détecté: {results_df['is_double_wave'].sum()}")
        print(f"Single Wave: {len(results) - results_df['is_double_wave'].sum()}")
        print()
        print("MAE Impact:")
        print(f"  Moyenne: {results_df['mae_impact'].mean():.2f} pips")
        print(f"  Médiane: {results_df['mae_impact'].median():.2f} pips")
        print(f"  Min: {results_df['mae_impact'].min():.2f} pips")
        print(f"  Max: {results_df['mae_impact'].max():.2f} pips")
        
        if 'mae_timing' in results_df.columns:
            timing_data = results_df[results_df['mae_timing'].notna()]['mae_timing']
            if len(timing_data) > 0:
                print()
                print("MAE Timing:")
                print(f"  Moyenne: {timing_data.mean():.2f} minutes")
                print(f"  Médiane: {timing_data.median():.2f} minutes")
    else:
        print("\n⚠️ Aucun résultat - vérifier données")


if __name__ == "__main__":
    main()
