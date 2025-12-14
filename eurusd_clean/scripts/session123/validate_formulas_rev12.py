"""
Validation formules S115 sur patterns Rev12

Charge les 149 Double Wave détectés par Rev12
Calcule impacts prédits avec formules S115
Compare vs amplitudes réelles
Calcule MAE et statistiques

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 124 - ÉTAPE 2
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
import pytz

# Fichiers
PATTERNS_FILE = Path(__file__).parent / 'validation_results' / 'double_waves_rev12_2024_2025.json'
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb'
OUTPUT_DIR = Path(__file__).parent / 'validation_results'


def calculate_surprise(actual, forecast, previous):
    """Calculer surprise normalisée"""
    
    if actual is None or pd.isna(actual):
        return 0.0
    
    # Utiliser forecast si disponible, sinon previous
    expected = forecast if forecast is not None and not pd.isna(forecast) else previous
    
    if expected is None or pd.isna(expected) or expected == 0:
        return 0.0
    
    surprise = ((actual - expected) / abs(expected)) * 100
    
    return surprise


def calculate_event_score(event):
    """Calculer score événement (formule S55)"""
    
    surprise = calculate_surprise(
        event.get('actual'),
        event.get('forecast'),
        event.get('previous')
    )
    
    # Importance (par défaut MEDIUM = 2.0)
    importance = event.get('importance', 'MEDIUM')
    if importance in ['HIGH', 'high', '3']:
        importance_weight = 3.0
    elif importance in ['MEDIUM', 'medium', '2']:
        importance_weight = 2.0
    else:
        importance_weight = 1.0
    
    score = abs(surprise) * importance_weight
    
    return score, surprise


def calculate_cluster_impact(events):
    """Calculer impact cluster (formule S115)"""
    
    if len(events) == 0:
        return 0.0, []
    
    # Calculer scores
    scores = []
    for event in events:
        score, surprise = calculate_event_score(event)
        scores.append({
            'event_name': event.get('event_name'),
            'country': event.get('country'),
            'surprise': surprise,
            'score': score
        })
    
    # Somme scores
    total_score = sum(s['score'] for s in scores)
    
    # Amplification empirique 2.8 (validée S113)
    AMPLIFICATION = 2.8
    
    impact_pips = total_score * AMPLIFICATION / 100.0
    
    return impact_pips, scores


def find_causal_events(conn, pattern_time, lookback=30, lookforward=10):
    """Trouver events causaux dans fenêtre temporelle"""
    
    # Parser datetime
    dt = pd.to_datetime(pattern_time)
    if dt.tz is None:
        dt = dt.tz_localize('Europe/Zurich')
    
    # Convertir en UTC pour query
    dt_utc = dt.tz_convert('UTC')
    
    start = dt_utc - timedelta(minutes=lookback)
    end = dt_utc + timedelta(minutes=lookforward)
    
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
    
    try:
        results = conn.execute(query, [start, end]).fetchall()
    except Exception as e:
        print(f"⚠️  Erreur query events: {e}")
        return []
    
    events = []
    for row in results:
        dt_event_utc = pd.to_datetime(row[0], utc=True)
        dt_event_bern = dt_event_utc.tz_convert('Europe/Zurich')
        
        # Delta temporel
        delta_minutes = (dt_event_bern - dt).total_seconds() / 60.0
        
        events.append({
            'datetime': str(dt_event_bern),
            'event_name': row[1],
            'country': row[2],
            'importance': row[3],
            'actual': row[4],
            'forecast': row[5],
            'previous': row[6],
            'delta_minutes': delta_minutes
        })
    
    return events


def validate_pattern(pattern, conn):
    """Valider un pattern spécifique"""
    
    # Amplitude réelle
    real_amplitude = pattern.get('wave2_amp_pips', 0)
    
    # Chercher events causaux autour de baseline_time
    baseline_time = pattern.get('baseline_time')
    if not baseline_time:
        return {
            'status': 'NO_BASELINE',
            'real_amplitude': real_amplitude,
            'predicted_impact': 0,
            'mae': real_amplitude
        }
    
    events = find_causal_events(conn, baseline_time, lookback=30, lookforward=10)
    
    if len(events) == 0:
        return {
            'status': 'NO_EVENTS',
            'real_amplitude': real_amplitude,
            'predicted_impact': 0,
            'mae': real_amplitude,
            'events_count': 0
        }
    
    # Calculer impact prédit
    predicted_impact, event_scores = calculate_cluster_impact(events)
    
    # MAE
    mae = abs(real_amplitude - predicted_impact)
    mae_pct = (mae / real_amplitude * 100) if real_amplitude > 0 else 0
    
    return {
        'status': 'VALIDATED',
        'real_amplitude': real_amplitude,
        'predicted_impact': predicted_impact,
        'mae': mae,
        'mae_pct': mae_pct,
        'events_count': len(events),
        'events_scores': event_scores
    }


def main():
    """Validation complète patterns Rev12"""
    
    print("=" * 80)
    print("VALIDATION FORMULES S115 - PATTERNS REV12")
    print("=" * 80)
    print()
    
    # Charger patterns
    if not PATTERNS_FILE.exists():
        print(f"❌ Fichier patterns non trouvé : {PATTERNS_FILE}")
        print()
        print("Exécutez d'abord : python scan_with_rev12.py")
        return
    
    with open(PATTERNS_FILE, 'r') as f:
        patterns = json.load(f)
    
    print(f"📊 Patterns Rev12 : {len(patterns)}")
    print()
    
    # Connexion DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Valider chaque pattern
    print("=" * 80)
    print("VALIDATION CAS PAR CAS")
    print("=" * 80)
    print()
    
    results = []
    
    for i, pattern in enumerate(patterns, 1):
        date = pattern.get('date', 'Unknown')
        wave2 = pattern.get('wave2_amp_pips', 0)
        
        if i % 20 == 0 or i == 1:  # Afficher tous les 20
            print(f"[{i}/{len(patterns)}] {date} : {wave2:.1f} pips réels")
        
        # Valider
        result = validate_pattern(pattern, conn)
        
        # Ajouter infos pattern
        result['date'] = date
        result['direction'] = pattern.get('direction')
        result['confidence'] = pattern.get('confidence')
        
        results.append(result)
    
    conn.close()
    
    print()
    print(f"✅ {len(patterns)} patterns validés")
    print()
    
    # ========================================================================
    # STATISTIQUES GLOBALES
    # ========================================================================
    
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()
    
    validated = [r for r in results if r['status'] == 'VALIDATED']
    no_events = [r for r in results if r['status'] == 'NO_EVENTS']
    
    print(f"Résultats :")
    print(f"   Avec events    : {len(validated)} ({len(validated)/len(results)*100:.1f}%)")
    print(f"   Sans events    : {len(no_events)} ({len(no_events)/len(results)*100:.1f}%)")
    print()
    
    if len(validated) == 0:
        print("⚠️  Aucun pattern validé avec events")
        return
    
    # MAE
    mae_values = [r['mae'] for r in validated]
    mae_mean = np.mean(mae_values)
    mae_median = np.median(mae_values)
    mae_std = np.std(mae_values)
    mae_min = np.min(mae_values)
    mae_max = np.max(mae_values)
    
    print(f"MAE (Mean Absolute Error) :")
    print(f"   Moyenne   : {mae_mean:.2f} pips")
    print(f"   Médiane   : {mae_median:.2f} pips")
    print(f"   Écart-type: {mae_std:.2f} pips")
    print(f"   Min       : {mae_min:.2f} pips")
    print(f"   Max       : {mae_max:.2f} pips")
    print()
    
    # Distribution MAE
    under_5 = sum(1 for mae in mae_values if mae < 5)
    under_10 = sum(1 for mae in mae_values if mae < 10)
    under_20 = sum(1 for mae in mae_values if mae < 20)
    
    print(f"Distribution MAE :")
    print(f"   MAE < 5 pips  : {under_5}/{len(validated)} ({under_5/len(validated)*100:.1f}%)")
    print(f"   MAE < 10 pips : {under_10}/{len(validated)} ({under_10/len(validated)*100:.1f}%)")
    print(f"   MAE < 20 pips : {under_20}/{len(validated)} ({under_20/len(validated)*100:.1f}%)")
    print()
    
    # Critère succès GAP #1
    if mae_mean < 5:
        print("✅✅✅ OBJECTIF GAP #1 ATTEINT : MAE moyen < 5 pips")
    elif mae_mean < 10:
        print("✅✅ BON : MAE moyen < 10 pips")
    elif mae_mean < 20:
        print("✅ ACCEPTABLE : MAE moyen < 20 pips")
    else:
        print("⚠️  À AMÉLIORER : MAE moyen > 20 pips")
    
    print()
    
    # R² (coefficient détermination)
    real_values = [r['real_amplitude'] for r in validated]
    pred_values = [r['predicted_impact'] for r in validated]
    
    real_mean = np.mean(real_values)
    ss_tot = sum((r - real_mean)**2 for r in real_values)
    ss_res = sum((real_values[i] - pred_values[i])**2 for i in range(len(real_values)))
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    print(f"R² (coefficient détermination) : {r_squared:.3f}")
    
    if r_squared > 0.90:
        print("   ✅✅✅ Excellent (> 0.90)")
    elif r_squared > 0.80:
        print("   ✅✅ Très bon (> 0.80)")
    elif r_squared > 0.70:
        print("   ✅ Bon (> 0.70)")
    else:
        print("   ⚠️  À améliorer (< 0.70)")
    
    print()
    
    # Top/Bottom 5
    sorted_results = sorted(validated, key=lambda x: x['mae'])
    
    print("TOP 5 MEILLEURS CAS (MAE plus faible) :")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"   {i}. {r['date']}")
        print(f"      Réel: {r['real_amplitude']:.1f} pips | Prédit: {r['predicted_impact']:.1f} pips | MAE: {r['mae']:.1f} pips")
    
    print()
    
    print("TOP 5 PIRES CAS (MAE plus élevée) :")
    for i, r in enumerate(sorted_results[-5:][::-1], 1):
        print(f"   {i}. {r['date']}")
        print(f"      Réel: {r['real_amplitude']:.1f} pips | Prédit: {r['predicted_impact']:.1f} pips | MAE: {r['mae']:.1f} pips")
    
    print()
    
    # ========================================================================
    # SAUVEGARDER
    # ========================================================================
    
    output = {
        'summary': {
            'total_patterns': len(patterns),
            'validated_patterns': len(validated),
            'mae_mean': float(mae_mean),
            'mae_median': float(mae_median),
            'mae_std': float(mae_std),
            'mae_min': float(mae_min),
            'mae_max': float(mae_max),
            'r_squared': float(r_squared),
            'under_5pips': under_5,
            'under_10pips': under_10,
            'under_20pips': under_20
        },
        'results': results
    }
    
    output_file = OUTPUT_DIR / 'validation_results_rev12.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    # ========================================================================
    # CONCLUSION
    # ========================================================================
    
    print("=" * 80)
    print("CONCLUSION GAP #1")
    print("=" * 80)
    print()
    
    if mae_mean < 5 and r_squared > 0.90:
        print("🎉 GAP #1 RÉSOLU")
        print()
        print("   Critères atteints :")
        print(f"   ✅ MAE moyen < 5 pips ({mae_mean:.2f})")
        print(f"   ✅ R² > 0.90 ({r_squared:.3f})")
        print(f"   ✅ {len(validated)} patterns validés")
        print()
        print("   Formules S115 PRODUCTION-READY !")
    elif mae_mean < 10:
        print("✅ FORMULES BONNES")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips")
        print(f"   R²        : {r_squared:.3f}")
        print()
        print("   Ajustements mineurs possibles")
    else:
        print("⚠️  FORMULES À AMÉLIORER")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips (objectif < 5)")
        print(f"   R²        : {r_squared:.3f}")
        print()
        print("   Investigation nécessaire")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
