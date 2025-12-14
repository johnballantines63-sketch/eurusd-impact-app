#!/usr/bin/env python3
"""
Backtest final CPI/NFP uniquement
Test sur événements majeurs à fort impact
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import duckdb
import numpy as np
from typing import List, Dict
import json

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path

# Importer les fonctions de séquençage
try:
    from sequence_multi_event_timeline import sequence_multi_event_timeline
    SEQUENCE_AVAILABLE = True
except ImportError:
    SEQUENCE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'target_events': {
        'CPI': ['%cpi%', '%inflation rate%'],
        'NFP': ['%nfp%', '%payroll%', '%employment change%']
    },
    'date_range': {
        'start': '2023-01-01',
        'end': '2024-12-31'
    },
    'countries': ['US'],  # Focus sur US uniquement
    'time_gap_minutes': 5,
    'min_importance': 2,
    'max_sessions': 50
}


# ═══════════════════════════════════════════════════════════════
# FONCTIONS
# ═══════════════════════════════════════════════════════════════

def find_major_event_sessions(db_path: str) -> List[Dict]:
    """Trouve les sessions CPI/NFP uniquement"""
    
    conn = duckdb.connect(db_path, read_only=True)
    
    # Build WHERE clause for CPI and NFP
    cpi_conditions = " OR ".join([f"LOWER(event_key) LIKE '{pattern}'" 
                                  for pattern in CONFIG['target_events']['CPI']])
    nfp_conditions = " OR ".join([f"LOWER(event_key) LIKE '{pattern}'" 
                                  for pattern in CONFIG['target_events']['NFP']])
    
    where_clause = f"({cpi_conditions} OR {nfp_conditions})"
    
    query = f"""
    SELECT 
        ts_utc,
        event_key,
        country,
        importance_n,
        actual,
        previous,
        estimate
    FROM events
    WHERE DATE(ts_utc) >= '{CONFIG['date_range']['start']}'
      AND DATE(ts_utc) <= '{CONFIG['date_range']['end']}'
      AND country = 'US'
      AND importance_n >= {CONFIG['min_importance']}
      AND actual IS NOT NULL
      AND {where_clause}
    ORDER BY ts_utc
    """
    
    events = conn.execute(query).fetchdf()
    conn.close()
    
    if len(events) == 0:
        return []
    
    print(f"\n✅ {len(events)} événements CPI/NFP trouvés")
    print(f"   Période : {events['ts_utc'].min()} → {events['ts_utc'].max()}")
    
    # Grouper par date (sessions)
    sessions = []
    events_by_date = events.groupby(events['ts_utc'].dt.date)
    
    for date, day_events in events_by_date:
        # Grouper par heure (fenêtre de 30 min)
        day_events = day_events.sort_values('ts_utc')
        current_session = []
        last_time = None
        
        for idx, event in day_events.iterrows():
            event_time = pd.to_datetime(event['ts_utc'])
            
            if last_time is None or (event_time - last_time).total_seconds() / 60 <= 30:
                current_session.append(event.to_dict())
                last_time = event_time
            else:
                if len(current_session) > 0:
                    sessions.append({
                        'start_time': pd.to_datetime(current_session[0]['ts_utc']),
                        'events': current_session,
                        'type': identify_session_type(current_session)
                    })
                current_session = [event.to_dict()]
                last_time = event_time
        
        if len(current_session) > 0:
            sessions.append({
                'start_time': pd.to_datetime(current_session[0]['ts_utc']),
                'events': current_session,
                'type': identify_session_type(current_session)
            })
    
    print(f"\n✅ {len(sessions)} sessions identifiées")
    
    return sessions[:CONFIG['max_sessions']]


def identify_session_type(events: List[Dict]) -> str:
    """Identifie le type de session (CPI, NFP, ou mixte)"""
    
    has_cpi = any('cpi' in e['event_key'].lower() or 'inflation' in e['event_key'].lower() 
                  for e in events)
    has_nfp = any('nfp' in e['event_key'].lower() or 'payroll' in e['event_key'].lower() 
                  for e in events)
    
    if has_cpi and has_nfp:
        return 'CPI+NFP'
    elif has_cpi:
        return 'CPI'
    elif has_nfp:
        return 'NFP'
    else:
        return 'Other'


def predict_impact_major_event(event: Dict) -> Dict:
    """Prédiction d'impact pour événements majeurs (CPI/NFP)"""
    
    actual = event.get('actual', 0)
    estimate = event.get('estimate')
    previous = event.get('previous', 0)
    
    reference = estimate if estimate is not None else previous
    
    if reference == 0:
        reference = previous if previous != 0 else 1.0
    
    surprise = actual - reference
    
    if abs(surprise) < 0.01:
        return None
    
    # Surprise en %
    surprise_pct = (abs(surprise) / abs(reference)) * 100 if reference != 0 else 0
    
    # Impact plus élevé pour CPI/NFP (événements majeurs)
    event_type = identify_session_type([event])
    
    if event_type == 'CPI':
        base_impact = 60.0  # CPI a impact fort
    elif event_type == 'NFP':
        base_impact = 80.0  # NFP a impact très fort
    else:
        base_impact = 50.0
    
    # Formule : impact proportionnel à la surprise en %
    impact_pips = base_impact * min(surprise_pct / 5.0, 3.0)
    
    # Direction (CPI est inversé)
    if event_type == 'CPI':
        direction = 1 if surprise > 0 else -1
    else:
        direction = -1 if surprise > 0 else 1
    
    # TTR plus long pour événements majeurs
    ttr_base = 40.0 if event_type == 'NFP' else 35.0
    
    return {
        'predicted_pips': impact_pips,
        'direction': direction,
        'latency_median': 3.0,  # Réaction rapide
        'ttr_median': ttr_base,
        'surprise': surprise,
        'surprise_pct': surprise_pct,
        'family': event_type
    }


def fetch_prices_batch(db_path: str, start_time: datetime, duration_minutes: int = 120) -> pd.DataFrame:
    """Récupère les prix"""
    
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
# BACKTEST PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def run_cpi_nfp_backtest() -> Dict:
    """Backtest final sur CPI/NFP uniquement"""
    
    print("=" * 80)
    print("🧪 BACKTEST FINAL - CPI/NFP UNIQUEMENT")
    print("=" * 80)
    
    if not SEQUENCE_AVAILABLE:
        print("\n❌ sequence_multi_event_timeline non disponible")
        return {}
    
    db_path = get_db_path()
    
    # 1. Trouver sessions CPI/NFP
    print("\n📥 Recherche des sessions CPI/NFP majeures...")
    print(f"   Période : {CONFIG['date_range']['start']} → {CONFIG['date_range']['end']}")
    print(f"   Pays : US uniquement")
    
    sessions = find_major_event_sessions(db_path)
    
    if len(sessions) == 0:
        print("\n❌ Aucune session trouvée")
        return {}
    
    # Afficher répartition
    cpi_count = sum(1 for s in sessions if s['type'] == 'CPI')
    nfp_count = sum(1 for s in sessions if s['type'] == 'NFP')
    mixed_count = sum(1 for s in sessions if s['type'] == 'CPI+NFP')
    
    print(f"\n📊 Répartition :")
    print(f"   CPI : {cpi_count}")
    print(f"   NFP : {nfp_count}")
    print(f"   Mixtes : {mixed_count}")
    
    # Afficher exemples
    print("\n📋 Exemples de sessions :")
    for i, session in enumerate(sessions[:5]):
        print(f"\n   Session {i+1} : {session['start_time'].strftime('%Y-%m-%d %H:%M')} ({session['type']})")
        for evt in session['events'][:3]:
            print(f"      - {evt['event_key']}")
    
    # 2. Tester chaque session
    print("\n" + "=" * 80)
    print("🔬 TEST DES SESSIONS")
    print("=" * 80)
    
    results = []
    
    for session_idx, session in enumerate(sessions):
        print(f"\n{'─' * 80}")
        print(f"Session {session_idx + 1}/{len(sessions)} : {session['start_time'].strftime('%Y-%m-%d %H:%M')} ({session['type']})")
        print(f"   {len(session['events'])} événements")
        
        # Préparer prédictions
        predictions = []
        
        for evt in session['events']:
            pred = predict_impact_major_event(evt)
            
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
        
        # Récupérer prix réels
        start_fetch = session['start_time'] - timedelta(minutes=30)
        real_prices_df = fetch_prices_batch(db_path, start_fetch, duration_minutes=120)
        
        if real_prices_df is None:
            print("   ⚠️ Prix introuvables")
            continue
        
        print(f"   ✅ {len(real_prices_df)} minutes de prix")
        
        # Calculer phases
        try:
            phases = sequence_multi_event_timeline(
                predictions,
                real_prices_df=real_prices_df,
                time_gap_minutes=CONFIG['time_gap_minutes']
            )
            
            print(f"   📊 {len(phases)} phases détectées")
            
            # Analyser chaque phase
            for phase_idx, phase in enumerate(phases):
                ttr_obs = phase.get('ttr_real')
                ttr_theo = phase.get('ttr_theoretical')
                ttr_source = phase.get('ttr_source')
                
                if ttr_obs and ttr_theo:
                    error = abs(ttr_obs - ttr_theo)
                    
                    result = {
                        'session_date': session['start_time'].strftime('%Y-%m-%d %H:%M'),
                        'session_type': session['type'],
                        'n_events': len(phase.get('events', [])),
                        'phase_idx': phase_idx,
                        'impact_pips': phase.get('impact_combined', 0),
                        'direction': phase.get('direction', 'UP'),
                        'ttr_theoretical': ttr_theo,
                        'ttr_observed': ttr_obs,
                        'ttr_source': ttr_source,
                        'error': error,
                        'metadata': phase.get('ttr_metadata', {})
                    }
                    
                    results.append(result)
                    
                    status = "✅" if error < 10 else "⚠️" if error < 20 else "❌"
                    print(f"      Phase {phase_idx + 1}: {status} TTR obs={ttr_obs:.0f} min, theo={ttr_theo:.0f} min, err={error:.0f} min")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            continue
    
    # 3. Statistiques globales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES GLOBALES")
    print("=" * 80)
    
    if len(results) == 0:
        print("\n❌ Aucun résultat valide")
        return {}
    
    errors = [r['error'] for r in results]
    
    print(f"\n   Sessions testées : {len(sessions)}")
    print(f"   Phases analysées : {len(results)}")
    
    print(f"\n   📊 Précision TTR :")
    print(f"      MAE : {np.mean(errors):.1f} min")
    print(f"      RMSE : {np.sqrt(np.mean(np.array(errors)**2)):.1f} min")
    print(f"      Médiane : {np.median(errors):.1f} min")
    print(f"      Min : {np.min(errors):.1f} min")
    print(f"      Max : {np.max(errors):.1f} min")
    
    # Par type d'événement
    print("\n   📊 Par type d'événement :")
    for event_type in ['CPI', 'NFP', 'CPI+NFP']:
        type_results = [r for r in results if r['session_type'] == event_type]
        if len(type_results) > 0:
            type_errors = [r['error'] for r in type_results]
            mae = np.mean(type_errors)
            print(f"      {event_type:<10} : {len(type_results):2} phases, MAE = {mae:.1f} min")
    
    # Distribution
    bins = [0, 5, 10, 15, 20, 30, 100]
    labels = ['< 5 min', '5-10 min', '10-15 min', '15-20 min', '20-30 min', '> 30 min']
    
    print(f"\n   📊 Distribution des erreurs :")
    for i, label in enumerate(labels):
        count = sum(1 for e in errors if bins[i] <= e < bins[i+1])
        pct = count / len(errors) * 100
        bar = "█" * int(pct / 2)
        print(f"      {label:<12} : {count:3} ({pct:5.1f}%) {bar}")
    
    # 4. Sauvegarder
    output_file = "backtest_cpi_nfp_results.json"
    output_data = {
        'config': CONFIG,
        'results': results,
        'stats': {
            'n_sessions': len(sessions),
            'n_phases': len(results),
            'mae': float(np.mean(errors)),
            'rmse': float(np.sqrt(np.mean(np.array(errors)**2)))
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ BACKTEST TERMINÉ")
    print("=" * 80)
    
    return output_data


if __name__ == "__main__":
    run_cpi_nfp_backtest()
