"""
Validation formules S115 multi-dates avec patterns détectés

Utilise Double Wave détectés par scan_2024_2025_db125k.py
Calcule formules et MAE pour chaque cas

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Fichiers
DOUBLE_WAVES_FILE = Path(__file__).parent / 'scan_results' / 'double_waves_db125k.json'
OUTPUT_FILE = Path(__file__).parent / 'scan_results' / 'validation_results.json'

def calculate_surprise(actual, forecast, previous):
    """Calculer surprise normalisée"""
    
    if actual is None:
        return 0.0
    
    # Utiliser forecast si disponible, sinon previous
    expected = forecast if forecast is not None else previous
    
    if expected is None or expected == 0:
        return 0.0
    
    surprise = ((actual - expected) / abs(expected)) * 100
    
    return surprise

def calculate_event_score(event):
    """Calculer score événement"""
    
    surprise = calculate_surprise(
        event.get('actual'),
        event.get('forecast'),
        event.get('previous')
    )
    
    # Importance
    importance = event.get('importance', 'MEDIUM')
    if importance == 'HIGH' or importance == 'high':
        importance_weight = 3.0
    elif importance == 'MEDIUM' or importance == 'medium':
        importance_weight = 2.0
    else:
        importance_weight = 1.0
    
    score = abs(surprise) * importance_weight
    
    return score

def calculate_cluster_impact(events):
    """Calculer impact cluster (formule S55)"""
    
    if len(events) == 0:
        return 0.0
    
    # Somme scores
    total_score = sum(calculate_event_score(e) for e in events)
    
    # Amplification empirique 2.8
    AMPLIFICATION = 2.8
    
    impact_pips = total_score * AMPLIFICATION / 100.0
    
    return impact_pips

def validate_pattern(pattern_data):
    """Valider un pattern spécifique"""
    
    # Amplitude réelle
    real_amplitude = pattern_data.get('max_move', 0)
    
    # Events causaux
    events = pattern_data.get('events', [])
    
    if len(events) == 0:
        return {
            'status': 'NO_EVENTS',
            'real_amplitude': real_amplitude,
            'predicted_impact': 0,
            'mae': real_amplitude,
            'events_count': 0
        }
    
    # Calculer impact prédit
    predicted_impact = calculate_cluster_impact(events)
    
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
        'events_detail': [
            {
                'name': e.get('event_name'),
                'country': e.get('country'),
                'surprise': calculate_surprise(e.get('actual'), e.get('forecast'), e.get('previous')),
                'score': calculate_event_score(e),
                'delta_minutes': e.get('delta_minutes')
            }
            for e in events
        ]
    }

def main():
    """Validation complète multi-dates"""
    
    print("=" * 80)
    print("VALIDATION FORMULES MULTI-DATES - PATTERNS DB 125K")
    print("=" * 80)
    print()
    
    # Charger Double Wave détectés
    if not DOUBLE_WAVES_FILE.exists():
        print(f"❌ Fichier non trouvé : {DOUBLE_WAVES_FILE}")
        print()
        print("Exécutez d'abord : python scan_2024_2025_db125k.py")
        return
    
    with open(DOUBLE_WAVES_FILE, 'r') as f:
        double_waves = json.load(f)
    
    print(f"📊 Double Wave à valider : {len(double_waves)}")
    print()
    
    # Filtrer avec events
    dw_with_events = [dw for dw in double_waves if dw.get('num_events', 0) > 0]
    
    print(f"   Avec events causaux : {len(dw_with_events)}")
    print(f"   Sans events         : {len(double_waves) - len(dw_with_events)}")
    print()
    
    if len(dw_with_events) == 0:
        print("⚠️  Aucun Double Wave avec events à valider")
        return
    
    # Valider chaque cas
    print("=" * 80)
    print("VALIDATION CAS PAR CAS")
    print("=" * 80)
    print()
    
    results = []
    
    for i, dw in enumerate(dw_with_events, 1):
        date_str = dw.get('datetime', 'Unknown')
        
        print(f"[{i}/{len(dw_with_events)}] {date_str}")
        print(f"   Amplitude réelle : {dw.get('max_move', 0):.1f} pips")
        print(f"   Events causaux   : {dw.get('num_events', 0)}")
        
        # Valider
        result = validate_pattern(dw)
        
        if result['status'] == 'VALIDATED':
            print(f"   Impact prédit    : {result['predicted_impact']:.1f} pips")
            print(f"   MAE              : {result['mae']:.1f} pips ({result['mae_pct']:.1f}%)")
            
            # Indicateur précision
            if result['mae'] < 5:
                indicator = "✅✅✅"
            elif result['mae'] < 10:
                indicator = "✅✅"
            elif result['mae'] < 20:
                indicator = "✅"
            else:
                indicator = "⚠️"
            
            print(f"   Précision        : {indicator}")
        else:
            print(f"   ⚠️  {result['status']}")
        
        print()
        
        # Ajouter aux résultats
        result['datetime'] = date_str
        result['amplitude_real'] = dw.get('max_move', 0)
        results.append(result)
    
    # Statistiques globales
    print("=" * 80)
    print("STATISTIQUES GLOBALES")
    print("=" * 80)
    print()
    
    validated = [r for r in results if r['status'] == 'VALIDATED']
    
    if len(validated) == 0:
        print("⚠️  Aucun cas validé")
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
    
    # Objectif < 5 pips
    under_5 = sum(1 for mae in mae_values if mae < 5)
    under_10 = sum(1 for mae in mae_values if mae < 10)
    under_20 = sum(1 for mae in mae_values if mae < 20)
    
    print(f"Distribution MAE :")
    print(f"   MAE < 5 pips  : {under_5}/{len(validated)} ({under_5/len(validated)*100:.1f}%)")
    print(f"   MAE < 10 pips : {under_10}/{len(validated)} ({under_10/len(validated)*100:.1f}%)")
    print(f"   MAE < 20 pips : {under_20}/{len(validated)} ({under_20/len(validated)*100:.1f}%)")
    print()
    
    # Critère succès Session 120
    if mae_mean < 5:
        print("✅✅✅ OBJECTIF ATTEINT : MAE moyen < 5 pips")
    elif mae_mean < 10:
        print("✅✅ BON : MAE moyen < 10 pips")
    elif mae_mean < 20:
        print("✅ ACCEPTABLE : MAE moyen < 20 pips")
    else:
        print("⚠️  À AMÉLIORER : MAE moyen > 20 pips")
    
    print()
    
    # R² (coefficient détermination)
    real_values = [r['amplitude_real'] for r in validated]
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
    
    # Top 5 meilleurs cas
    print("TOP 5 MEILLEURS CAS (MAE plus faible) :")
    sorted_results = sorted(validated, key=lambda x: x['mae'])
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"   {i}. {r['datetime']}")
        print(f"      Réel: {r['amplitude_real']:.1f} pips | Prédit: {r['predicted_impact']:.1f} pips | MAE: {r['mae']:.1f} pips")
    
    print()
    
    # Top 5 pires cas
    print("TOP 5 PIRES CAS (MAE plus élevée) :")
    for i, r in enumerate(sorted_results[-5:][::-1], 1):
        print(f"   {i}. {r['datetime']}")
        print(f"      Réel: {r['amplitude_real']:.1f} pips | Prédit: {r['predicted_impact']:.1f} pips | MAE: {r['mae']:.1f} pips")
    
    print()
    
    # Sauvegarder résultats
    output = {
        'summary': {
            'total_patterns': len(double_waves),
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
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Résultats sauvegardés : {OUTPUT_FILE}")
    print()
    
    # Conclusion
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    if mae_mean < 5 and r_squared > 0.90:
        print("🎉 FORMULES VALIDÉES")
        print()
        print("   Critères atteints :")
        print(f"   ✅ MAE moyen < 5 pips ({mae_mean:.2f})")
        print(f"   ✅ R² > 0.90 ({r_squared:.3f})")
        print()
        print("   Formules S115 production-ready !")
    elif mae_mean < 10:
        print("✅ FORMULES BONNES")
        print()
        print(f"   MAE moyen : {mae_mean:.2f} pips (objectif < 5)")
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

if __name__ == '__main__':
    main()
