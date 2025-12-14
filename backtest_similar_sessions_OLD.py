#!/usr/bin/env python3
"""
Backtest Similar Sessions - Validation contextuelle
====================================================

Pour une configuration d'événements donnée (ex: 5 Michigan),
trouve des sessions historiques similaires et valide la précision
du modèle SPÉCIFIQUEMENT pour cette configuration.

Usage:
    python3 backtest_similar_sessions.py --families "Michigan_Current_Conditions,Michigan_Inflation_Expectations"
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb
import numpy as np
from typing import List, Dict, Set
import json
from collections import Counter
import argparse

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path

try:
    from sequence_multi_event_timeline import sequence_multi_event_timeline
    SEQUENCE_AVAILABLE = True
except ImportError:
    SEQUENCE_AVAILABLE = False
    print("⚠️ sequence_multi_event_timeline non disponible")


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'lookback_years': 3,
    'min_similarity': 0.6,  # 60% de familles communes minimum
    'max_time_gap_minutes': 30,  # Événements considérés simultanés si < 30 min
    'min_sessions': 5  # Minimum de sessions similaires requises
}


# ═══════════════════════════════════════════════════════════════
# FONCTIONS DE RECHERCHE DE SESSIONS SIMILAIRES
# ═══════════════════════════════════════════════════════════════

def normalize_family_set(families: List[str]) -> Set[str]:
    """Normalise une liste de familles en set trié"""
    return set(f.lower().strip().replace(' ', '_') for f in families if f)


def calculate_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calcule similarité Jaccard entre deux ensembles de familles
    
    Similarité = |intersection| / |union|
    
    Exemples:
    - {A, B, C} vs {A, B, C} → 1.0 (identique)
    - {A, B, C} vs {A, B} → 0.67 (2/3)
    - {A, B} vs {C, D} → 0.0 (aucune commune)
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def find_similar_sessions(
    target_families: List[str],
    db_path: str,
    lookback_years: int = 3,
    min_similarity: float = 0.6
) -> List[Dict]:
    """
    Trouve sessions historiques avec composition similaire
    
    Args:
        target_families: Liste familles cible (ex: ['Michigan_Current_Conditions', ...])
        db_path: Chemin base de données
        lookback_years: Nombre d'années historique
        min_similarity: Seuil similarité minimum (0-1)
    
    Returns:
        Liste de sessions avec métadonnées et score similarité
    """
    
    print("\n" + "=" * 80)
    print("🔍 RECHERCHE SESSIONS SIMILAIRES")
    print("=" * 80)
    
    target_set = normalize_family_set(target_families)
    
    print(f"\n📋 Configuration cible :")
    print(f"   Familles : {len(target_set)}")
    for fam in sorted(target_set):
        print(f"      - {fam}")
    
    # Récupérer toutes les sessions historiques
    conn = duckdb.connect(db_path, read_only=True)
    
    cutoff_date = datetime.now() - timedelta(days=lookback_years * 365)
    
    query = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country,
        e.actual,
        e.previous,
        e.estimate,
        ef.family
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key
    WHERE e.ts_utc >= '{cutoff_date.strftime('%Y-%m-%d')}'
      AND e.ts_utc < NOW()
      AND e.country IN ('US', 'EU', 'DE', 'FR', 'GB')
      AND e.importance_n >= 1
      AND e.actual IS NOT NULL
      AND e.estimate IS NOT NULL
      AND ef.family IS NOT NULL
    ORDER BY e.ts_utc
    """
    
    events_df = conn.execute(query).fetchdf()
    conn.close()
    
    print(f"\n📊 Événements historiques : {len(events_df)}")
    
    # Grouper événements en sessions (< max_time_gap)
    sessions = []
    current_session = []
    last_time = None
    
    for idx, event in events_df.iterrows():
        event_time = pd.to_datetime(event['ts_utc'])
        
        if last_time is None or (event_time - last_time).total_seconds() / 60 <= CONFIG['max_time_gap_minutes']:
            current_session.append(event.to_dict())
            last_time = event_time
        else:
            if len(current_session) >= 2:  # Au moins 2 événements
                sessions.append({
                    'start_time': pd.to_datetime(current_session[0]['ts_utc']),
                    'events': current_session
                })
            
            current_session = [event.to_dict()]
            last_time = event_time
    
    # Dernière session
    if len(current_session) >= 2:
        sessions.append({
            'start_time': pd.to_datetime(current_session[0]['ts_utc']),
            'events': current_session
        })
    
    print(f"📦 Sessions détectées : {len(sessions)}")
    
    # Calculer similarité pour chaque session
    similar_sessions = []
    
    for session in sessions:
        # Extraire familles de la session
        session_families = [e['family'] for e in session['events'] if e.get('family')]
        session_set = normalize_family_set(session_families)
        
        # Calculer similarité
        similarity = calculate_similarity(target_set, session_set)
        
        if similarity >= min_similarity:
            similar_sessions.append({
                'start_time': session['start_time'],
                'events': session['events'],
                'families': sorted(session_set),
                'n_events': len(session['events']),
                'similarity': similarity
            })
    
    # Trier par similarité décroissante
    similar_sessions.sort(key=lambda s: s['similarity'], reverse=True)
    
    print(f"\n✅ Sessions similaires (>= {min_similarity*100:.0f}%) : {len(similar_sessions)}")
    
    if len(similar_sessions) > 0:
        print(f"\n📊 Distribution similarité :")
        similarities = [s['similarity'] for s in similar_sessions]
        print(f"   Moyenne : {np.mean(similarities):.2f}")
        print(f"   Médiane : {np.median(similarities):.2f}")
        print(f"   Min : {np.min(similarities):.2f}")
        print(f"   Max : {np.max(similarities):.2f}")
        
        # Top 5
        print(f"\n🏆 Top 5 sessions les plus similaires :")
        for i, session in enumerate(similar_sessions[:5], 1):
            print(f"\n   {i}. {session['start_time'].strftime('%Y-%m-%d %H:%M')} - Similarité {session['similarity']:.0%}")
            print(f"      {session['n_events']} événements")
            for fam in session['families'][:3]:
                print(f"         - {fam}")
            if len(session['families']) > 3:
                print(f"         ... et {len(session['families']) - 3} autres")
    
    return similar_sessions


# ═══════════════════════════════════════════════════════════════
# PRÉDICTION POUR SESSION HISTORIQUE (comme en production)
# ═══════════════════════════════════════════════════════════════

def predict_impact_simple(event: Dict) -> Dict:
    """Calcul d'impact simplifié (comme dans backtest_FIXED.py)"""
    
    actual = event.get('actual')
    estimate = event.get('estimate')
    
    if actual is None or estimate is None or estimate == 0:
        return None
    
    # ✅ Calcul en pourcentage (comme corrigé)
    surprise_pct = abs((actual - estimate) / estimate) * 100
    
    if surprise_pct < 0.1:
        return None
    
    base_impact = 50.0
    impact_pips = base_impact * min(surprise_pct / 10.0, 3.0)
    
    # Direction
    surprise = actual - estimate
    direction = 1 if surprise > 0 else -1
    
    return {
        'predicted_pips': impact_pips,
        'direction': direction,
        'latency_median': 5.0,  # Valeur par défaut
        'ttr_median': 30.0,
        'surprise': surprise,
        'surprise_pct': surprise_pct,
        'family': event.get('family', 'Unknown')
    }


def fetch_prices_for_session(db_path: str, start_time: datetime, duration_minutes: int = 120) -> pd.DataFrame:
    """Récupère prix pour une session"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    if isinstance(start_time, pd.Timestamp):
        start_time = start_time.to_pydatetime()
    if hasattr(start_time, 'tz') and start_time.tz is not None:
        start_time = start_time.tz_convert('UTC').tz_localize(None)
    
    start_epoch = int(start_time.timestamp())
    end_epoch = start_epoch + (duration_minutes * 60)
    
    query = f"""
    SELECT timestamp, close as price
    FROM prices_1m
    WHERE timestamp >= {start_epoch} AND timestamp <= {end_epoch}
    ORDER BY timestamp ASC
    """
    
    try:
        prices = conn.execute(query).fetchall()
        conn.close()
        
        if len(prices) > 0:
            times = [datetime.fromtimestamp(r[0]) for r in prices]
            values = [r[1] for r in prices]
            return pd.DataFrame({'time': times, 'price': values})
        return None
    except Exception as e:
        conn.close()
        return None


# ═══════════════════════════════════════════════════════════════
# BACKTEST SUR SESSIONS SIMILAIRES
# ═══════════════════════════════════════════════════════════════

def backtest_similar_sessions(
    similar_sessions: List[Dict],
    db_path: str
) -> Dict:
    """
    Teste le modèle sur sessions similaires
    
    Pour chaque session :
    1. Recréer calcul vectoriel (comme en production)
    2. Comparer avec réalité observée
    3. Calculer erreurs
    """
    
    if not SEQUENCE_AVAILABLE:
        print("\n❌ sequence_multi_event_timeline non disponible")
        return {}
    
    print("\n" + "=" * 80)
    print("🧪 BACKTEST SUR SESSIONS SIMILAIRES")
    print("=" * 80)
    
    results = []
    
    for session_idx, session in enumerate(similar_sessions[:20], 1):  # Max 20
        
        print(f"\n{'─' * 80}")
        print(f"Session {session_idx}/{min(len(similar_sessions), 20)} : {session['start_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Similarité : {session['similarity']:.0%}")
        print(f"   {session['n_events']} événements")
        
        # Préparer prédictions (comme en production)
        predictions = []
        
        for evt in session['events']:
            pred = predict_impact_simple(evt)
            
            if pred is None:
                continue
            
            predictions.append({
                'event': {
                    'ts_utc': pd.to_datetime(evt['ts_utc']),
                    'family': pred['family'],
                    'event_key': evt['event_key'],
                    'country': evt['country']
                },
                'predicted_pips': pred['predicted_pips'],
                'direction': pred['direction'],
                'latency_median': pred['latency_median'],
                'ttr_median': pred['ttr_median'],
                'surprise': pred['surprise']
            })
        
        if len(predictions) == 0:
            print("   ⚠️ Aucune prédiction valide")
            continue
        
        # Calculer impact vectoriel combiné
        total_impact = sum(abs(p['predicted_pips']) for p in predictions)
        print(f"   💥 Impact total prédit : {total_impact:.1f} pips")
        
        # Récupérer prix réels
        start_fetch = session['start_time'] - timedelta(minutes=30)
        real_prices_df = fetch_prices_for_session(db_path, start_fetch, duration_minutes=120)
        
        if real_prices_df is None:
            print("   ⚠️ Prix introuvables")
            continue
        
        print(f"   ✅ {len(real_prices_df)} minutes de prix")
        
        # Calculer phases avec sequence_multi_event_timeline
        try:
            phases = sequence_multi_event_timeline(
                predictions,
                real_prices_df=real_prices_df,
                time_gap_minutes=CONFIG['max_time_gap_minutes']
            )
            
            print(f"   📊 {len(phases)} phases détectées")
            
            # Analyser chaque phase
            for phase_idx, phase in enumerate(phases):
                ttr_obs = phase.get('ttr_real')
                ttr_theo = phase.get('ttr_theoretical')
                ttr_source = phase.get('ttr_source')
                impact = phase.get('impact_combined', 0)
                
                if ttr_obs and ttr_theo:
                    error = abs(ttr_obs - ttr_theo)
                    
                    result = {
                        'session_date': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                        'similarity': session['similarity'],
                        'n_events': len(phase.get('events', [])),
                        'phase_idx': phase_idx,
                        'impact_pips': impact,
                        'direction': phase.get('direction', 'UP'),
                        'ttr_theoretical': ttr_theo,
                        'ttr_observed': ttr_obs,
                        'ttr_source': ttr_source,
                        'error': error,
                        'families': session['families']
                    }
                    
                    results.append(result)
                    
                    status = "✅" if error < 10 else "⚠️" if error < 20 else "❌"
                    print(f"      Phase {phase_idx + 1}: {status} Impact={impact:.1f} pips, TTR obs={ttr_obs:.0f} min, theo={ttr_theo:.0f} min, err={error:.0f} min")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            continue
    
    # Statistiques finales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES CONTEXTUELLES")
    print("=" * 80)
    
    if len(results) == 0:
        print("\n❌ Aucun résultat valide")
        return {}
    
    errors = [r['error'] for r in results]
    impacts = [r['impact_pips'] for r in results]
    similarities = [r['similarity'] for r in results]
    
    print(f"\n   Sessions testées : {len(similar_sessions[:20])}")
    print(f"   Phases analysées : {len(results)}")
    print(f"   Similarité moyenne : {np.mean(similarities):.0%}")
    
    print(f"\n   💥 Impacts :")
    print(f"      Impact moyen : {np.mean(impacts):.1f} pips")
    print(f"      Impact médian : {np.median(impacts):.1f} pips")
    print(f"      Min : {np.min(impacts):.1f} pips")
    print(f"      Max : {np.max(impacts):.1f} pips")
    
    print(f"\n   📊 Précision TTR :")
    print(f"      MAE : {np.mean(errors):.1f} min")
    print(f"      RMSE : {np.sqrt(np.mean(np.array(errors)**2)):.1f} min")
    print(f"      Médiane : {np.median(errors):.1f} min")
    print(f"      Min : {np.min(errors):.1f} min")
    print(f"      Max : {np.max(errors):.1f} min")
    
    # Distribution des erreurs
    bins = [0, 5, 10, 15, 20, 30, 100]
    labels = ['< 5 min', '5-10 min', '10-15 min', '15-20 min', '20-30 min', '> 30 min']
    
    print(f"\n   📊 Distribution des erreurs :")
    for i, label in enumerate(labels):
        count = sum(1 for e in errors if bins[i] <= e < bins[i+1])
        pct = count / len(errors) * 100
        bar = "█" * int(pct / 2)
        print(f"      {label:<12} : {count:3} ({pct:5.1f}%) {bar}")
    
    # Sauvegarder
    output_file = "backtest_similar_sessions_results.json"
    output_data = {
        'target_families': list(similar_sessions[0]['families']) if similar_sessions else [],
        'config': CONFIG,
        'results': results,
        'stats': {
            'n_sessions': len(similar_sessions[:20]),
            'n_phases': len(results),
            'mae': float(np.mean(errors)),
            'rmse': float(np.sqrt(np.mean(np.array(errors)**2))),
            'median_error': float(np.median(errors)),
            'mean_impact': float(np.mean(impacts)),
            'median_impact': float(np.median(impacts)),
            'mean_similarity': float(np.mean(similarities))
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    return output_data


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='Backtest sur sessions similaires'
    )
    parser.add_argument(
        '--families',
        type=str,
        required=True,
        help='Liste familles séparées par virgule (ex: Michigan_Current_Conditions,Michigan_Inflation_Expectations)'
    )
    parser.add_argument(
        '--similarity',
        type=float,
        default=0.6,
        help='Seuil similarité minimum (0-1, défaut: 0.6)'
    )
    parser.add_argument(
        '--years',
        type=int,
        default=3,
        help='Années historique (défaut: 3)'
    )
    
    args = parser.parse_args()
    
    # Parser familles
    target_families = [f.strip() for f in args.families.split(',') if f.strip()]
    
    if len(target_families) == 0:
        print("❌ Aucune famille spécifiée")
        return
    
    CONFIG['min_similarity'] = args.similarity
    CONFIG['lookback_years'] = args.years
    
    db_path = get_db_path()
    
    # 1. Trouver sessions similaires
    similar_sessions = find_similar_sessions(
        target_families,
        db_path,
        lookback_years=CONFIG['lookback_years'],
        min_similarity=CONFIG['min_similarity']
    )
    
    if len(similar_sessions) < CONFIG['min_sessions']:
        print(f"\n⚠️ Pas assez de sessions similaires ({len(similar_sessions)} < {CONFIG['min_sessions']})")
        print("   Essayez de réduire --similarity ou --years")
        return
    
    # 2. Backtest sur sessions similaires
    results = backtest_similar_sessions(similar_sessions, db_path)
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    main()
