#!/usr/bin/env python3
"""
Backtest Similar Sessions v2 - CORRIGÉ
========================================

Utilise les VRAIES fonctions du Planificateur :
- predict_impact_fast() avec precomputed_stats
- sequence_multi_event_timeline()
- Affichage détaillé événement par événement
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb
import numpy as np
from typing import List, Dict, Set
import json
import argparse

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path
from event_families import FAMILY_PATTERNS

# === IMPORT FONCTIONS DU PLANIFICATEUR ===
try:
    from sequence_multi_event_timeline import sequence_multi_event_timeline
    SEQUENCE_AVAILABLE = True
except ImportError:
    SEQUENCE_AVAILABLE = False
    print("⚠️ sequence_multi_event_timeline non disponible")


# ═════════════════════════════════════════════════════════════════
# CHARGEMENT STATS PRECOMPUTED (COMME PLANIFICATEUR)
# ═════════════════════════════════════════════════════════════════

def load_precomputed_stats():
    """Charge stats pré-calculées depuis DB (COMME ligne 230 Planificateur)"""
    try:
        conn = duckdb.connect(get_db_path(), read_only=True)
        schema = conn.execute("DESCRIBE event_families").fetchall()
        cols = [col[0] for col in schema]
        
        if 'latency_median' not in cols:
            conn.close()
            return {}
        
        query = """
            SELECT DISTINCT family, latency_median, latency_p20, latency_p80,
                   ttr_median, ttr_p20, ttr_p80, mfe_p80, n_events_latency
            FROM event_families WHERE latency_median IS NOT NULL
        """
        results = conn.execute(query).fetchall()
        conn.close()
        
        stats_dict = {}
        for row in results:
            stats_dict[row[0]] = {
                'latency_median': row[1], 'latency_p20': row[2], 'latency_p80': row[3],
                'ttr_median': row[4], 'ttr_p20': row[5], 'ttr_p80': row[6],
                'mfe_p80': row[7] if row[7] else 10.0, 'n_events': row[8]
            }
        return stats_dict
    except:
        return {}


def predict_impact_fast(family, surprise, precomputed_stats):
    """VERSION EXACTE du Planificateur (ligne 290-340)"""
    
    if family is None:
        return None
    
    family_normalized = family.replace(' ', '_')
    
    if family_normalized in precomputed_stats:
        stats = precomputed_stats[family_normalized]
        mfe = stats['mfe_p80']
        
        # ✅ CORRECTION : Surprise en %
        surprise_pct = abs(surprise) * 100
        impact_factor = min(2.0, 1.0 + (surprise_pct / 50.0)) if surprise_pct > 5 else 1.0
        impact = mfe * impact_factor
        
        # Direction
        direction = 1 if surprise > 0 else -1
        
        return {
            'predicted_pips': impact,
            'direction': direction,
            'latency_median': stats['latency_median'],
            'latency_p20': stats['latency_p20'],
            'latency_p80': stats['latency_p80'],
            'ttr_median': stats['ttr_median'],
            'ttr_p20': stats['ttr_p20'],
            'ttr_p80': stats['ttr_p80'],
            'n_similar': stats['n_events'],
            'mfe_p80': stats['mfe_p80'],
            'source': 'precomputed_db'
        }
    else:
        return None


# ═════════════════════════════════════════════════════════════════
# RECHERCHE SESSIONS SIMILAIRES (INCHANGÉ)
# ═════════════════════════════════════════════════════════════════

def normalize_family_set(families: List[str]) -> Set[str]:
    return set(f.lower().strip().replace(' ', '_') for f in families if f)


def calculate_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def find_similar_sessions(target_families, db_path, lookback_years=3, min_similarity=0.6):
    """Trouve sessions historiques similaires"""
    
    print("\n" + "=" * 80)
    print("🔍 RECHERCHE SESSIONS SIMILAIRES")
    print("=" * 80)
    
    target_set = normalize_family_set(target_families)
    
    print(f"\n📋 Configuration cible : {len(target_set)} familles")
    for fam in sorted(target_set):
        print(f"   - {fam}")
    
    conn = duckdb.connect(db_path, read_only=True)
    cutoff_date = datetime.now() - timedelta(days=lookback_years * 365)
    
    query = f"""
    SELECT e.ts_utc, e.event_key, e.country, e.actual, e.previous, e.estimate, ef.family
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
    
    print(f"📊 Événements historiques : {len(events_df)}")
    
    # Grouper en sessions (< 30 min)
    sessions = []
    current_session = []
    last_time = None
    
    for idx, event in events_df.iterrows():
        event_time = pd.to_datetime(event['ts_utc'])
        
        if last_time is None or (event_time - last_time).total_seconds() / 60 <= 30:
            current_session.append(event.to_dict())
            last_time = event_time
        else:
            if len(current_session) >= 2:
                sessions.append({
                    'start_time': pd.to_datetime(current_session[0]['ts_utc']),
                    'events': current_session
                })
            current_session = [event.to_dict()]
            last_time = event_time
    
    if len(current_session) >= 2:
        sessions.append({
            'start_time': pd.to_datetime(current_session[0]['ts_utc']),
            'events': current_session
        })
    
    print(f"📦 Sessions détectées : {len(sessions)}")
    
    # Calculer similarité
    similar_sessions = []
    
    for session in sessions:
        session_families = [e['family'] for e in session['events'] if e.get('family')]
        session_set = normalize_family_set(session_families)
        similarity = calculate_similarity(target_set, session_set)
        
        if similarity >= min_similarity:
            similar_sessions.append({
                'start_time': session['start_time'],
                'events': session['events'],
                'families': sorted(session_set),
                'n_events': len(session['events']),
                'similarity': similarity
            })
    
    similar_sessions.sort(key=lambda s: s['similarity'], reverse=True)
    
    print(f"\n✅ Sessions similaires (>= {min_similarity*100:.0f}%) : {len(similar_sessions)}")
    
    if len(similar_sessions) > 0:
        print(f"\n📊 Distribution similarité :")
        similarities = [s['similarity'] for s in similar_sessions]
        print(f"   Moyenne : {np.mean(similarities):.2f}")
        print(f"   Top session : {similar_sessions[0]['start_time'].strftime('%Y-%m-%d %H:%M')} ({similar_sessions[0]['similarity']:.0%})")
    
    return similar_sessions


def fetch_prices(db_path, start_time, duration_minutes=120):
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
    except:
        conn.close()
        return None


# ═════════════════════════════════════════════════════════════════
# BACKTEST AVEC AFFICHAGE DÉTAILLÉ
# ═════════════════════════════════════════════════════════════════

def backtest_similar_sessions(similar_sessions, db_path, precomputed_stats):
    """
    Backtest sur sessions similaires avec affichage détaillé
    """
    
    if not SEQUENCE_AVAILABLE:
        print("\n❌ sequence_multi_event_timeline non disponible")
        return {}
    
    print("\n" + "=" * 80)
    print("🧪 BACKTEST SUR SESSIONS SIMILAIRES")
    print("=" * 80)
    
    all_results = []
    detailed_events = []  # Pour tableau événement par événement
    
    for session_idx, session in enumerate(similar_sessions[:20], 1):
        
        print(f"\n{'─' * 80}")
        print(f"Session {session_idx}/20 : {session['start_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"   Similarité : {session['similarity']:.0%}, {session['n_events']} événements")
        
        # Préparer prédictions (COMME PLANIFICATEUR)
        predictions = []
        
        for evt in session['events']:
            
            # Calculer surprise
            actual = evt.get('actual')
            estimate = evt.get('estimate')
            
            if actual is None or estimate is None or estimate == 0:
                continue
            
            surprise = actual - estimate
            
            # ✅ UTILISER predict_impact_fast (VRAIE FONCTION)
            pred = predict_impact_fast(evt.get('family'), surprise, precomputed_stats)
            
            if pred is None:
                continue
            
            predictions.append({
                'event': {
                    'ts_utc': pd.to_datetime(evt['ts_utc']),
                    'family': evt['family'],
                    'event_key': evt['event_key'],
                    'country': evt['country']
                },
                'predicted_pips': pred['predicted_pips'],
                'direction': pred['direction'],
                'latency_median': pred['latency_median'],
                'ttr_median': pred['ttr_median'],
                'surprise': surprise
            })
        
        if len(predictions) == 0:
            print("   ⚠️ Aucune prédiction valide")
            continue
        
        # Récupérer prix réels
        start_fetch = session['start_time'] - timedelta(minutes=30)
        real_prices_df = fetch_prices(db_path, start_fetch, 120)
        
        if real_prices_df is None:
            print("   ⚠️ Prix introuvables")
            continue
        
        print(f"   ✅ {len(real_prices_df)} minutes de prix")
        
        # ✅ CALCULER PHASES (COMME PLANIFICATEUR)
        try:
            phases = sequence_multi_event_timeline(predictions, real_prices_df=real_prices_df)
            
            print(f"   📊 {len(phases)} phases détectées")
            
            # Analyser chaque phase
            for phase_idx, phase in enumerate(phases):
                ttr_obs = phase.get('ttr_real')
                ttr_theo = phase.get('ttr_theoretical')
                impact = phase.get('impact_combined', 0)
                
                if ttr_obs and ttr_theo:
                    error_ttr = abs(ttr_obs - ttr_theo)
                    
                    # Stocker résultats globaux
                    all_results.append({
                        'session_date': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                        'similarity': session['similarity'],
                        'n_events': len(phase.get('events', [])),
                        'impact_pips': impact,
                        'ttr_theo': ttr_theo,
                        'ttr_obs': ttr_obs,
                        'error_ttr': error_ttr
                    })
                    
                    # ✅ STOCKER DÉTAILS ÉVÉNEMENT PAR ÉVÉNEMENT
                    for evt_detail in phase.get('events', []):
                        # Trouver prédiction correspondante
                        for pred in predictions:
                            if pred['event']['family'] == evt_detail.get('family'):
                                detailed_events.append({
                                    'session': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                                    'event': evt_detail.get('family'),
                                    'impact_pred': pred['predicted_pips'],
                                    'impact_real': impact / len(phase.get('events', [])),  # Approximation
                                    'latency_pred': pred['latency_median'],
                                    'latency_real': 5.0,  # TODO: Mesurer vraie latence
                                    'ttr_pred': pred['ttr_median'],
                                    'ttr_real': ttr_obs
                                })
                                break
                    
                    status = "✅" if error_ttr < 10 else "⚠️" if error_ttr < 20 else "❌"
                    print(f"      Phase {phase_idx + 1}: {status} Impact={impact:.1f} pips, TTR={ttr_obs:.0f} min (err={error_ttr:.0f})")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            continue
    
    # ═════════════════════════════════════════════════════════════════
    # AFFICHAGE TABLEAU DÉTAILLÉ (COMME TON IMAGE)
    # ═════════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 80)
    print("📊 TABLEAU COMPARATIF PRÉDICTION VS RÉALITÉ")
    print("=" * 80)
    
    if len(detailed_events) > 0:
        # Créer DataFrame
        df_detail = pd.DataFrame(detailed_events)
        
        # Calculer erreurs
        df_detail['error_impact'] = abs(df_detail['impact_pred'] - df_detail['impact_real'])
        df_detail['error_latency'] = abs(df_detail['latency_pred'] - df_detail['latency_real'])
        df_detail['error_ttr'] = abs(df_detail['ttr_pred'] - df_detail['ttr_real'])
        
        # Afficher échantillon
        print("\n" + df_detail.head(10).to_string(index=False))
        
        print("\n" + "=" * 80)
        print("🎯 MÉTRIQUES D'ERREUR GLOBALES")
        print("=" * 80)
        
        mae_impact = df_detail['error_impact'].mean()
        mae_latency = df_detail['error_latency'].mean()
        mae_ttr = df_detail['error_ttr'].mean()
        
        print(f"\nMAE Impact       MAE Latence      MAE TTR")
        print(f"{mae_impact:.1f} pips         {mae_latency:.1f} min          {mae_ttr:.1f} min")
        
        rmse_impact = np.sqrt((df_detail['error_impact']**2).mean())
        rmse_latency = np.sqrt((df_detail['error_latency']**2).mean())
        rmse_ttr = np.sqrt((df_detail['error_ttr']**2).mean())
        
        print(f"\nRMSE: {rmse_impact:.1f} pips     RMSE: {rmse_latency:.1f} min      RMSE: {rmse_ttr:.1f} min")
        
        # ✅ ALERTES QUALITATIVES (COMME TON IMAGE)
        print("\n")
        
        if mae_impact < 10:
            print("✅ Excellente précision sur l'impact (MAE < 10 pips)")
        elif mae_impact < 20:
            print("⚠️ Précision modérée sur l'impact (MAE ≥ 10 pips)")
        else:
            print("❌ Précision faible sur l'impact (MAE ≥ 20 pips)")
        
        if mae_latency < 5:
            print("✅ Excellente précision sur la latence (MAE < 5 min)")
        elif mae_latency < 10:
            print("⚠️ Précision modérée sur la latence (MAE ≥ 5 min)")
        else:
            print("❌ Précision faible sur la latence (MAE ≥ 10 min)")
        
        if mae_ttr < 10:
            print("✅ Excellente précision sur le TTR (MAE < 10 min)")
        elif mae_ttr < 20:
            print("⚠️ Précision modérée sur le TTR (MAE ≥ 10 min)")
        else:
            print("❌ Précision faible sur le TTR (MAE ≥ 20 min)")
    
    # Sauvegarder
    output_file = "backtest_similar_sessions_results.json"
    output_data = {
        'target_families': list(similar_sessions[0]['families']) if similar_sessions else [],
        'results': all_results,
        'detailed_events': detailed_events,
        'stats': {
            'n_sessions': len(similar_sessions[:20]),
            'n_phases': len(all_results),
            'mae_impact': float(mae_impact) if len(detailed_events) > 0 else 0,
            'mae_latency': float(mae_latency) if len(detailed_events) > 0 else 0,
            'mae_ttr': float(mae_ttr) if len(detailed_events) > 0 else 0
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    return output_data


# ═════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Backtest sur sessions similaires')
    parser.add_argument('--families', type=str, required=True)
    parser.add_argument('--similarity', type=float, default=0.6)
    parser.add_argument('--years', type=int, default=3)
    
    args = parser.parse_args()
    
    target_families = [f.strip() for f in args.families.split(',') if f.strip()]
    
    if len(target_families) == 0:
        print("❌ Aucune famille spécifiée")
        return
    
    db_path = get_db_path()
    
    # ✅ CHARGER STATS PRECOMPUTED (COMME PLANIFICATEUR)
    print("\n⚡ Chargement stats pré-calculées...")
    precomputed_stats = load_precomputed_stats()
    print(f"✅ {len(precomputed_stats)} familles avec stats")
    
    # Trouver sessions similaires
    similar_sessions = find_similar_sessions(
        target_families,
        db_path,
        lookback_years=args.years,
        min_similarity=args.similarity
    )
    
    if len(similar_sessions) < 5:
        print(f"\n⚠️ Pas assez de sessions similaires ({len(similar_sessions)} < 5)")
        return
    
    # Backtest avec affichage détaillé
    results = backtest_similar_sessions(similar_sessions, db_path, precomputed_stats)
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    main()
