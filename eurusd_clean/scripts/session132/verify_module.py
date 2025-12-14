"""
Analyse Syntaxique Module - Vérification Imports et Structure
==============================================================

Vérifie que le module peut être importé et que la structure est correcte.

Auteur: Session 132
Date: 13 novembre 2025
"""

import sys
from pathlib import Path

# Ajouter src au path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

print("\n" + "="*70)
print(" VÉRIFICATION MODULE DOUBLEWAVE PREDICTION")
print("="*70)

print("\n1. Vérification import module...")
try:
    from core import doublewave_prediction
    print("   ✅ Module importé avec succès")
except Exception as e:
    print(f"   ❌ Erreur import : {e}")
    sys.exit(1)

print("\n2. Vérification classes...")
try:
    assert hasattr(doublewave_prediction, 'PatternClassifier')
    print("   ✅ PatternClassifier présente")
    
    assert hasattr(doublewave_prediction, 'InclusionCriteria')
    print("   ✅ InclusionCriteria présente")
except AssertionError as e:
    print(f"   ❌ Classe manquante")
    sys.exit(1)

print("\n3. Vérification fonctions...")
try:
    assert hasattr(doublewave_prediction, 'predict_doublewave_overlap')
    print("   ✅ predict_doublewave_overlap présente")
    
    assert hasattr(doublewave_prediction, 'calculate_combined_surprise')
    print("   ✅ calculate_combined_surprise présente")
except AssertionError:
    print(f"   ❌ Fonction manquante")
    sys.exit(1)

print("\n4. Vérification constantes PatternClassifier...")
try:
    pc = doublewave_prediction.PatternClassifier
    assert pc.OVERLAP_SCORE_MIN == 150
    print("   ✅ OVERLAP_SCORE_MIN = 150")
    
    assert pc.OVERLAP_SCORE_MAX == 350
    print("   ✅ OVERLAP_SCORE_MAX = 350")
    
    assert pc.OVERLAP_EVENTS_MIN == 5
    print("   ✅ OVERLAP_EVENTS_MIN = 5")
    
    assert pc.OVERLAP_EVENTS_MAX == 10
    print("   ✅ OVERLAP_EVENTS_MAX = 10")
    
    assert pc.SUPERPOSITION_SCORE_MIN == 500
    print("   ✅ SUPERPOSITION_SCORE_MIN = 500")
    
    assert pc.MAJOR_COUNTRIES == {'US', 'EU', 'UK', 'CA', 'JP', 'CH'}
    print("   ✅ MAJOR_COUNTRIES correct")
    
    assert pc.PERIPHERAL_COUNTRIES == {'RS', 'MK', 'UZ', 'CO'}
    print("   ✅ PERIPHERAL_COUNTRIES correct")
except AssertionError as e:
    print(f"   ❌ Constante incorrecte : {e}")
    sys.exit(1)

print("\n5. Test fonction predict_doublewave_overlap (cas simple)...")
try:
    from core.doublewave_prediction import predict_doublewave_overlap
    
    # Test avec liste vide
    result = predict_doublewave_overlap([])
    assert result['status'] == 'excluded'
    assert result['reason'] == 'Aucun événement fourni'
    print("   ✅ Cas liste vide : exclusion correcte")
    
    # Test avec 0 events scorés
    events_no_score = [
        {'event_key': 'test', 'country': 'US', 'score': 0}
    ]
    result = predict_doublewave_overlap(events_no_score)
    assert result['status'] == 'excluded'
    assert 'Aucun événement scoré' in result['reason']
    print("   ✅ Cas 0 events scorés : exclusion correcte")
    
    # Test avec score trop faible
    events_low = [
        {'event_key': 'test', 'country': 'US', 'score': 20.0}
    ]
    result = predict_doublewave_overlap(events_low)
    assert result['status'] == 'excluded'
    assert 'trop faible' in result['reason'].lower()
    print("   ✅ Cas score < 50 : exclusion correcte")
    
    # Test avec cascade (périphérique)
    events_cascade = [
        {'event_key': 'test', 'country': 'RS', 'score': 60.0}
    ]
    result = predict_doublewave_overlap(events_cascade)
    assert result['status'] == 'excluded'
    assert result['pattern_type'] == 'cascade'
    print("   ✅ Cas cascade périphérique : exclusion correcte")
    
    # Test avec overlap standard valide
    events_valid = [
        {'event_key': 'nfp', 'country': 'US', 'score': 48.0, 'actual': 200, 'estimate': 150},
        {'event_key': 'unemployment', 'country': 'US', 'score': 44.0, 'actual': 3.5, 'estimate': 3.6},
        {'event_key': 'cpi', 'country': 'US', 'score': 48.0, 'actual': 0.3, 'estimate': 0.2},
        {'event_key': 'gdp', 'country': 'EU', 'score': 44.0, 'actual': 0.5, 'estimate': 0.4},
        {'event_key': 'inflation', 'country': 'EU', 'score': 48.0, 'actual': 2.5, 'estimate': 2.3},
    ]
    result = predict_doublewave_overlap(events_valid)
    assert result['status'] == 'predicted'
    assert result['amplification'] == 0.1201
    assert result['pattern_type'] == 'overlap_standard'
    assert result['prediction'] is not None
    print("   ✅ Cas overlap standard valide : prédiction correcte")
    print(f"      → Prediction: {result['prediction']} pips")
    print(f"      → Score: {result['total_score']:.1f}")
    print(f"      → Events: {result['events_scored']}")
    
except Exception as e:
    print(f"   ❌ Erreur test : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print(" ✅ TOUS LES TESTS SYNTAXIQUES PASSÉS")
print("="*70)

print("\n📋 STRUCTURE MODULE VALIDÉE :")
print("   • PatternClassifier : ✅")
print("   • InclusionCriteria : ✅")
print("   • predict_doublewave_overlap : ✅")
print("   • Constantes Session 131 : ✅")
print("   • Logique exclusion : ✅")
print("   • Logique prédiction : ✅")

print("\n✨ MODULE PRÊT POUR TESTS COMPLETS\n")
print("➡️  PROCHAINE ÉTAPE :")
print("   python scripts/session132/test_quick.py")
print("   (tests avec données simulées)\n")
