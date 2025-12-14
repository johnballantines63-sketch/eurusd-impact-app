"""
Validation cluster 11 septembre 2025

Méthodologie :
1. Identifier events 11 septembre (cas référence)
2. Chercher autres dates avec cluster similaire
3. Vérifier Double Wave sur ces dates
4. Valider formule S115 sur cluster homogène

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - Méthodologie scientifique rigoureuse
"""

import sys
from pathlib import Path
import json
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import pytz
from typing import List, Dict

# Ajouter session120 au path
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
session120_dir = scripts_dir / 'session120'

if str(session120_dir) not in sys.path:
    sys.path.insert(0, str(session120_dir))

from double_wave_detector_rev12 import detect_for_date_duckdb_rev12

# DB unifiée
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'


def get_events_for_date(conn, date_str: str, lookback=150, lookforward=10):
    """Charger events pour une date spécifique"""
    
    # Baseline time standard (14:29 Bern)
    dt = pd.to_datetime(date_str).tz_localize('Europe/Zurich')
    baseline_time = dt.replace(hour=14, minute=29, second=0)
    
    # ✅ FIX: datetime_utc dans DB est en UTC !
    # Convertir baseline Bern → UTC pour comparaison
    baseline_utc = baseline_time.tz_convert('UTC')
    start_utc = baseline_utc - timedelta(minutes=lookback)
    end_utc = baseline_utc + timedelta(minutes=lookforward)
    
    # Retirer timezone pour comparaison SQL (DuckDB TIMESTAMP sans TZ)
    start = start_utc.replace(tzinfo=None)
    end = end_utc.replace(tzinfo=None)
    
    query = """
    SELECT 
        datetime_utc,
        event_name,
        country,
        importance,
        actual,
        forecast,
        previous
    FROM economic_events
    WHERE datetime_utc >= ?
      AND datetime_utc <= ?
      AND country IN ('usd', 'eur', 'gbp', 'jpy', 'cad', 'aud', 'chf')
    ORDER BY datetime_utc
    """
    
    results = conn.execute(query, [start, end]).fetchall()
    
    events = []
    for row in results:
        # datetime_utc dans DB est en UTC (pas Bern !)
        dt_event_utc = pd.to_datetime(row[0]).tz_localize('UTC')
        dt_event_bern = dt_event_utc.tz_convert('Europe/Zurich')
        delta = (dt_event_bern - baseline_time).total_seconds() / 60.0
        
        events.append({
            'datetime_bern': str(dt_event_bern),
            'datetime_utc': str(dt_event_bern),  # En réalité Bern time
            'event_name': row[1],  # event_title de la DB
            'country': row[2],
            'importance': row[3] if row[3] else 'MEDIUM',
            'actual': row[4],
            'forecast': row[5],
            'previous': row[6],
            'delta_minutes': delta
        })
    
    return events


def create_cluster_fingerprint(events: List[Dict]) -> tuple:
    """
    Créer empreinte unique du cluster
    
    Returns:
        (set des event_names normalisés, count HIGH, count MED)
    """
    
    # Filtrer HIGH importance
    high_events = [e for e in events if e.get('importance') in ['HIGH', 'high', '3']]
    
    # Normaliser noms
    normalized = set()
    for event in high_events:
        name = event.get('event_name', '').lower()
        country = event.get('country', '').upper()
        
        # Normalisation simple
        key = f"{country}_{name}"
        normalized.add(key)
    
    count_high = len(high_events)
    count_med = len([e for e in events if e.get('importance') in ['MEDIUM', 'medium', '2']])
    
    return (frozenset(normalized), count_high, count_med)


def clusters_similar(fp1: tuple, fp2: tuple, tolerance=1) -> bool:
    """
    Vérifier si deux clusters sont similaires
    
    tolerance=1 : accepte ±1 event différent
    """
    
    events1, high1, med1 = fp1
    events2, high2, med2 = fp2
    
    # Différence symétrique
    diff = events1.symmetric_difference(events2)
    
    # Accepter si ≤ tolerance events différents
    return len(diff) <= tolerance


def main():
    """Validation cluster 11 septembre"""
    
    print("=" * 80)
    print("VALIDATION CLUSTER 11 SEPTEMBRE 2025")
    print("=" * 80)
    print()
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # ========================================================================
    # ÉTAPE 1 : IDENTIFIER CLUSTER 11 SEPTEMBRE
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 1 : IDENTIFIER EVENTS 11 SEPTEMBRE")
    print("=" * 80)
    print()
    
    ref_date = '2025-09-11'
    ref_events = get_events_for_date(conn, ref_date, lookback=30, lookforward=10)
    
    print(f"📅 Date référence : {ref_date}")
    print(f"📊 Events détectés : {len(ref_events)}")
    print()
    
    if len(ref_events) == 0:
        print("❌ Aucun event trouvé pour le 11 septembre")
        print("   Vérifier DB ou ajuster fenêtre temporelle")
        conn.close()
        return
    
    # Afficher events
    print("Events HIGH importance :")
    high_events_ref = [e for e in ref_events if e.get('importance') in ['HIGH', 'high', '3']]
    
    for i, event in enumerate(high_events_ref, 1):
        dt = pd.to_datetime(event['datetime_bern'])
        print(f"\n   [{i}] {dt.strftime('%H:%M')} Bern")
        print(f"       {event['country'].upper()} - {event['event_name']}")
        print(f"       Actual: {event.get('actual')} | Forecast: {event.get('forecast')} | Previous: {event.get('previous')}")
        print(f"       Delta: {event['delta_minutes']:+.1f} min")
    
    print()
    print(f"Total HIGH : {len(high_events_ref)}")
    print()
    
    # Créer empreinte
    ref_fingerprint = create_cluster_fingerprint(ref_events)
    print(f"Empreinte cluster : {len(ref_fingerprint[0])} events HIGH uniques")
    print()
    
    # ========================================================================
    # ÉTAPE 2 : CHERCHER DATES AVEC CLUSTER SIMILAIRE
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 2 : CHERCHER RÉPÉTITIONS CLUSTER")
    print("=" * 80)
    print()
    
    print("🔍 Scanning 2024-2025...")
    print()
    
    similar_dates = []
    
    # Scanner 2024-2025
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 10, 31)
    current = start_date
    
    dates_checked = 0
    
    while current <= end_date:
        date_str = current.strftime('%Y-%m-%d')
        
        # Skip 11 septembre (référence)
        if date_str == ref_date:
            current += timedelta(days=1)
            continue
        
        # Charger events
        events = get_events_for_date(conn, date_str)
        dates_checked += 1
        
        if len(events) > 0:
            # Comparer cluster
            fingerprint = create_cluster_fingerprint(events)
            
            if clusters_similar(ref_fingerprint, fingerprint, tolerance=1):
                similar_dates.append({
                    'date': date_str,
                    'events': events,
                    'fingerprint': fingerprint
                })
        
        current += timedelta(days=1)
    
    print(f"✅ {dates_checked} dates scannées")
    print(f"📊 Dates avec cluster similaire : {len(similar_dates)}")
    print()
    
    if len(similar_dates) == 0:
        print("⚠️  Aucune répétition trouvée")
        print()
        print("Actions possibles :")
        print("   1. Augmenter tolerance (±2 events)")
        print("   2. Élargir fenêtre temporelle")
        print("   3. Chercher cluster partiel (sous-ensemble events)")
        conn.close()
        return
    
    # Afficher dates similaires
    print("Dates avec cluster similaire :")
    for i, item in enumerate(similar_dates, 1):
        high_count = item['fingerprint'][1]
        print(f"   {i}. {item['date']} ({high_count} events HIGH)")
    
    print()
    
    # ========================================================================
    # ÉTAPE 3 : DÉTECTER DOUBLE WAVE SUR CES DATES
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 3 : DÉTECTION DOUBLE WAVE")
    print("=" * 80)
    print()
    
    print("🔍 Test Rev12 sur dates similaires...")
    print()
    
    dates_with_dw = []
    
    # Tester 11 septembre d'abord
    print(f"[REF] {ref_date} (référence)")
    ref_pattern = detect_for_date_duckdb_rev12(
        db_path=str(DB_PATH),
        table='prices_bern',
        date=datetime.fromisoformat(ref_date),
        tz='Europe/Zurich',
        baseline_mode='prev_close_14_29',
        minutes_after_hint=120,
        trading_window=True,
        debug=False
    )
    
    if ref_pattern:
        wave2_ref = ref_pattern['wave2_amp_pips']
        print(f"      ✅ Double Wave : {wave2_ref:.1f} pips")
        dates_with_dw.append({
            'date': ref_date,
            'pattern': ref_pattern,
            'events': ref_events,
            'is_reference': True
        })
    else:
        print(f"      ❌ Pas de Double Wave détecté")
    
    print()
    
    # Tester dates similaires
    for i, item in enumerate(similar_dates, 1):
        date_str = item['date']
        print(f"[{i}/{len(similar_dates)}] {date_str}")
        
        pattern = detect_for_date_duckdb_rev12(
            db_path=str(DB_PATH),
            table='prices_bern',
            date=datetime.fromisoformat(date_str),
            tz='Europe/Zurich',
            baseline_mode='prev_close_14_29',
            minutes_after_hint=120,
            trading_window=True,
            debug=False
        )
        
        if pattern:
            wave2 = pattern['wave2_amp_pips']
            print(f"      ✅ Double Wave : {wave2:.1f} pips")
            dates_with_dw.append({
                'date': date_str,
                'pattern': pattern,
                'events': item['events'],
                'is_reference': False
            })
        else:
            print(f"      ❌ Pas de Double Wave")
    
    print()
    print(f"✅ Double Wave détectés : {len(dates_with_dw)}/{len(similar_dates)+1}")
    print()
    
    if len(dates_with_dw) < 2:
        print("⚠️  Pas assez de répétitions pour validation")
        print()
        print("Cluster trop spécifique ou Rev12 inadapté")
        conn.close()
        return
    
    # ========================================================================
    # ÉTAPE 4 : VALIDATION FORMULE S115
    # ========================================================================
    
    print("=" * 80)
    print("ÉTAPE 4 : VALIDATION FORMULE S115")
    print("=" * 80)
    print()
    
    print(f"📊 Échantillon : {len(dates_with_dw)} dates avec cluster similaire + Double Wave")
    print()
    
    # Calculer pour chaque
    results = []
    
    for item in dates_with_dw:
        date = item['date']
        pattern = item['pattern']
        events = item['events']
        is_ref = item['is_reference']
        
        # Amplitude réelle
        real_amp = pattern['wave2_amp_pips']
        
        # Calculer score events
        total_score = 0
        for event in events:
            actual = event.get('actual')
            forecast = event.get('forecast')
            previous = event.get('previous')
            
            if actual is None or pd.isna(actual):
                continue
            
            expected = forecast if forecast is not None and not pd.isna(forecast) else previous
            if expected is None or pd.isna(expected) or expected == 0:
                continue
            
            surprise = ((actual - expected) / abs(expected)) * 100
            
            importance = event.get('importance', 'MEDIUM')
            if importance in ['HIGH', 'high', '3']:
                weight = 3.0
            elif importance in ['MEDIUM', 'medium', '2']:
                weight = 2.0
            else:
                weight = 1.0
            
            score = abs(surprise) * weight
            total_score += score
        
        # Formule S115
        AMPLIFICATION = 2.8
        predicted = total_score * AMPLIFICATION / 100.0
        
        # MAE
        mae = abs(real_amp - predicted)
        mae_pct = (mae / real_amp * 100) if real_amp > 0 else 0
        
        results.append({
            'date': date,
            'is_reference': is_ref,
            'real_amplitude': real_amp,
            'predicted_impact': predicted,
            'mae': mae,
            'mae_pct': mae_pct,
            'events_count': len([e for e in events if e.get('importance') in ['HIGH', 'high', '3']])
        })
    
    # Afficher résultats
    print("RÉSULTATS PAR DATE :")
    print()
    
    for i, r in enumerate(results, 1):
        marker = "★ REF" if r['is_reference'] else f"  [{i}]"
        print(f"{marker} {r['date']}")
        print(f"     Réel    : {r['real_amplitude']:6.1f} pips")
        print(f"     Prédit  : {r['predicted_impact']:6.1f} pips")
        print(f"     MAE     : {r['mae']:6.1f} pips ({r['mae_pct']:5.1f}%)")
        print(f"     Events  : {r['events_count']} HIGH")
        print()
    
    # Statistiques
    mae_values = [r['mae'] for r in results]
    mae_mean = sum(mae_values) / len(mae_values)
    mae_median = sorted(mae_values)[len(mae_values)//2]
    
    print("=" * 80)
    print("STATISTIQUES CLUSTER")
    print("=" * 80)
    print()
    
    print(f"Échantillon     : {len(results)} dates")
    print(f"MAE moyen       : {mae_mean:.2f} pips")
    print(f"MAE médian      : {mae_median:.2f} pips")
    print()
    
    under_5 = sum(1 for mae in mae_values if mae < 5)
    under_10 = sum(1 for mae in mae_values if mae < 10)
    under_20 = sum(1 for mae in mae_values if mae < 20)
    
    print(f"MAE < 5 pips    : {under_5}/{len(results)} ({under_5/len(results)*100:.1f}%)")
    print(f"MAE < 10 pips   : {under_10}/{len(results)} ({under_10/len(results)*100:.1f}%)")
    print(f"MAE < 20 pips   : {under_20}/{len(results)} ({under_20/len(results)*100:.1f}%)")
    print()
    
    # Verdict
    if mae_mean < 5:
        print("✅✅✅ CLUSTER VALIDÉ : MAE moyen < 5 pips")
        print("      Formule S115 précise pour ce cluster")
    elif mae_mean < 10:
        print("✅✅ CLUSTER BON : MAE moyen < 10 pips")
        print("      Formule acceptable, ajustements mineurs possibles")
    elif mae_mean < 20:
        print("✅ CLUSTER ACCEPTABLE : MAE moyen < 20 pips")
        print("      Formule utilisable avec prudence")
    else:
        print("⚠️  CLUSTER PROBLÉMATIQUE : MAE moyen > 20 pips")
        print("      Formule inadaptée pour ce cluster")
    
    print()
    
    # Sauvegarder
    output = {
        'reference_date': ref_date,
        'reference_events': high_events_ref,
        'cluster_fingerprint': list(ref_fingerprint[0]),
        'similar_dates_found': len(similar_dates),
        'double_wave_detected': len(dates_with_dw),
        'validation_results': results,
        'mae_mean': mae_mean,
        'mae_median': mae_median
    }
    
    output_file = OUTPUT_DIR / 'cluster_sept11_validation.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"💾 Résultats : {output_file}")
    print()
    
    conn.close()
    
    print("=" * 80)


if __name__ == '__main__':
    main()
