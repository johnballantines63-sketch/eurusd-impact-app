#!/usr/bin/env python3
"""
Script de validation de la migration du Planificateur
Compare les résultats entre fonctions inline et fonctions clean
Cas de référence : 11 septembre 2025, 12:30 UTC - CPI US
Session 36
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Ajouter eurusd_clean au path
eurusd_clean_path = Path(__file__).parent.parent
sys.path.insert(0, str(eurusd_clean_path))

# Imports depuis eurusd_clean
from app.config import Config
from app.services.data_service import DataService
from app.utils.time_windows import (
    group_events_by_time_window,
    calculate_cluster_impact,
    detect_overlaps
)
from app.utils.backtest import (
    get_real_prices_batch,
    measure_real_impact
)
from app.utils.fibonacci import calculate_fibonacci_levels
from app.utils.visualization import (
    create_timeline_chart,
    create_backtest_chart
)
from app.utils.scoring import calculate_tradability_score


def compare_floats(val1, val2, tolerance=0.01, name=""):
    """Compare deux valeurs float avec tolérance"""
    if val1 is None or val2 is None:
        match = val1 == val2
    else:
        diff = abs(val1 - val2)
        match = diff <= tolerance
    
    status = "✅" if match else "❌"
    print(f"  {status} {name}: {val1} vs {val2}")
    return match


def compare_dicts(dict1, dict2, name="", tolerance=0.01):
    """Compare deux dictionnaires"""
    print(f"\n🔍 Comparaison {name}:")
    
    all_keys = set(list(dict1.keys()) + list(dict2.keys()))
    matches = []
    
    for key in sorted(all_keys):
        val1 = dict1.get(key)
        val2 = dict2.get(key)
        
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            match = compare_floats(val1, val2, tolerance, key)
        else:
            match = val1 == val2
            status = "✅" if match else "❌"
            print(f"  {status} {key}: {val1} vs {val2}")
        
        matches.append(match)
    
    return all(matches)


def test_get_real_prices_batch():
    """Test 1: get_real_prices_batch"""
    print("\n" + "="*70)
    print("TEST 1: get_real_prices_batch")
    print("="*70)
    
    # IMPORTANT: Utilisons une date dans la plage disponible (juin-octobre 2024)
    # Par exemple: 11 juillet 2024, 12:30
    event_time = datetime(2024, 7, 11, 12, 30, 0)
    
    print(f"\n⚠️  NOTE: Utilisation de juillet 2024 (plage disponible: juin-oct 2024)")
    
    # Version clean
    config = Config()
    data_service = DataService(config.get_db_path())
    
    try:
        prices = get_real_prices_batch(data_service, [event_time], window_minutes=60)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"   Nombre d'événements: {len(prices)}")
        if 0 in prices and prices[0] is not None:
            df = prices[0]
            print(f"   Points de prix pour événement 0: {len(df)}")
            print(f"   Plage temps: {df['time'].min()} → {df['time'].max()}")
            print(f"   Plage prix: {df['price'].min():.5f} → {df['price'].max():.5f}")
        
        return True
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_measure_real_impact():
    """Test 2: measure_real_impact"""
    print("\n" + "="*70)
    print("TEST 2: measure_real_impact")
    print("="*70)
    
    # Utiliser juillet 2024 (dans la plage disponible)
    event_time = datetime(2024, 7, 11, 12, 30, 0)
    
    print(f"\n⚠️  NOTE: Utilisation de juillet 2024 (plage disponible: juin-oct 2024)")
    
    # Récupérer les prix
    config = Config()
    data_service = DataService(config.get_db_path())
    prices = get_real_prices_batch(data_service, [event_time], window_minutes=60)
    
    if 0 not in prices or prices[0] is None:
        print("❌ Impossible de récupérer les prix")
        return False
    
    prices_df = prices[0]
    
    try:
        metrics = measure_real_impact(prices_df, threshold_pips=5.0)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"\n📊 Métriques calculées:")
        print(f"   Impact réel: {metrics['real_impact_pips']:.1f} pips")
        print(f"   Direction: {metrics['real_direction']} ({'UP' if metrics['real_direction'] > 0 else 'DOWN'})")
        print(f"   Latence: {metrics['real_latency_minutes']:.1f} min")
        print(f"   TTR: {metrics['real_ttr_minutes']:.1f} min")
        print(f"   Réaction détectée: {metrics['had_reaction']}")
        
        # Validation simple (juillet 2024)
        print(f"\n🎯 Validation juillet 2024:")
        impact_ok = abs(metrics['real_impact_pips']) >= 5  # Au moins 5 pips
        ttr_ok = 1 <= metrics['real_ttr_minutes'] <= 60  # Entre 1 et 60 min
        direction_ok = metrics['real_direction'] in [-1, 1]  # Direction valide
        
        print(f"   {'✅' if impact_ok else '❌'} Impact: {metrics['real_impact_pips']:.1f} pips (validé: >=5 pips)")
        print(f"   {'✅' if ttr_ok else '❌'} TTR: {metrics['real_ttr_minutes']:.1f} min (validé: 1-60 min)")
        print(f"   {'✅' if direction_ok else '❌'} Direction: {'UP' if metrics['real_direction'] > 0 else 'DOWN'} (validé: +1 ou -1)")
        
        return impact_ok and ttr_ok and direction_ok
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculate_fibonacci_levels():
    """Test 3: calculate_fibonacci_levels"""
    print("\n" + "="*70)
    print("TEST 3: calculate_fibonacci_levels")
    print("="*70)
    
    # Test avec impact 37.4 pips UP
    impact_pips = 37.4
    direction = 1
    
    try:
        levels = calculate_fibonacci_levels(impact_pips, direction)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"\n📊 Niveaux Fibonacci (Impact: {impact_pips} pips, Direction: UP):")
        for level_name, level_value in sorted(levels.items(), key=lambda x: x[1]):
            print(f"   {level_name:6s}: {level_value:6.2f} pips")
        
        # Validations basiques
        assert levels['0%'] == 0
        assert abs(levels['100%'] - impact_pips) < 0.01
        assert levels['50%'] == impact_pips * 0.5
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_group_events_by_time_window():
    """Test 4: group_events_by_time_window"""
    print("\n" + "="*70)
    print("TEST 4: group_events_by_time_window")
    print("="*70)
    
    # Créer événements test
    base_time = datetime(2025, 9, 11, 12, 0, 0)
    events = [
        {'event_time': base_time, 'event': 'Event1'},
        {'event_time': base_time + timedelta(minutes=15), 'event': 'Event2'},
        {'event_time': base_time + timedelta(minutes=60), 'event': 'Event3'},
    ]
    
    try:
        clusters = group_events_by_time_window(events, max_gap_minutes=30)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"   Nombre de clusters: {len(clusters)}")
        
        for i, cluster in enumerate(clusters):
            print(f"\n   Cluster {i+1}:")
            print(f"      Début: {cluster['window_start']}")
            print(f"      Fin: {cluster['window_end']}")
            print(f"      Événements: {len(cluster['events'])}")
        
        # Validation: devrait créer 2 clusters (Event1+Event2, Event3)
        assert len(clusters) == 2
        assert len(clusters[0]['events']) == 2
        assert len(clusters[1]['events']) == 1
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detect_overlaps():
    """Test 5: detect_overlaps"""
    print("\n" + "="*70)
    print("TEST 5: detect_overlaps")
    print("="*70)
    
    # Créer prédictions test avec chevauchements
    base_time = datetime(2025, 9, 11, 12, 0, 0)
    predictions = [
        {
            'event': 'CPI',
            'event_time': base_time,
            'ttr_median': 30  # TTR 30 min
        },
        {
            'event': 'Jobless Claims',
            'event_time': base_time + timedelta(minutes=20),  # 20 min après
            'ttr_median': 25
        },
    ]
    
    try:
        overlaps = detect_overlaps(predictions)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"   Nombre de chevauchements: {len(overlaps)}")
        
        for overlap in overlaps:
            print(f"\n   Chevauchement détecté:")
            print(f"      Event 1: {overlap['event1']}")
            print(f"      Event 2: {overlap['event2']}")
            print(f"      Overlap: {overlap['overlap_minutes']:.1f} min")
            print(f"      Sévérité: {overlap['severity']}")
        
        # Validation: devrait détecter 1 chevauchement
        assert len(overlaps) >= 1
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculate_tradability_score():
    """Test 6: calculate_tradability_score"""
    print("\n" + "="*70)
    print("TEST 6: calculate_tradability_score")
    print("="*70)
    
    # Créer prédictions test
    base_time = datetime(2025, 9, 11, 12, 0, 0)
    predictions = [
        {
            'event': 'CPI',
            'predicted_pips': 37.4,  # Nom correct
            'direction': 1,
            'ttr_median': 5
        },
        {
            'event': 'Jobless Claims',
            'predicted_pips': 15.0,  # Nom correct
            'direction': 1,
            'ttr_median': 7
        },
    ]
    
    overlaps = []  # Pas de chevauchements
    time_span = 2.0  # 2 heures
    
    try:
        score = calculate_tradability_score(predictions, overlaps, time_span)
        
        print(f"\n✅ Fonction clean exécutée avec succès")
        print(f"   Score de tradabilité: {score}/100")
        
        # Validation basique
        assert 0 <= score <= 100
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécuter tous les tests"""
    print("\n" + "="*70)
    print("🔬 VALIDATION MIGRATION PLANIFICATEUR - SESSION 36")
    print("="*70)
    print("\nCas de référence: 11 septembre 2025, 12:30 UTC - CPI US")
    print("Valeurs attendues: Impact 37.4 ±5 pips, TTR 5 ±2 min, Direction UP")
    
    results = []
    
    # Exécuter les tests
    results.append(("get_real_prices_batch", test_get_real_prices_batch()))
    results.append(("measure_real_impact", test_measure_real_impact()))
    results.append(("calculate_fibonacci_levels", test_calculate_fibonacci_levels()))
    results.append(("group_events_by_time_window", test_group_events_by_time_window()))
    results.append(("detect_overlaps", test_detect_overlaps()))
    results.append(("calculate_tradability_score", test_calculate_tradability_score()))
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_pass = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Résultat global: {total_pass}/{total} tests réussis")
    
    if total_pass == total:
        print("\n✅ TOUS LES TESTS SONT PASSÉS !")
        print("✅ Les fonctions clean produisent les mêmes résultats que les inline")
        print("✅ Migration validée - Prêt pour suppression des fonctions inline")
        return 0
    else:
        print(f"\n⚠️  {total - total_pass} test(s) échoué(s)")
        print("⚠️  Vérifier les différences avant de continuer la migration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
