"""
Script pour renseigner les événements du 11 septembre 2025

Ce script insère les événements de référence utilisés pour valider les formules.
Les données sont basées sur :
- Graphiques MT5 d'André (valeurs réelles)
- Planificateur (prédictions)
- Documentation SESSION 48/49

Une fois insérés, ces événements servent de référence pour tous les tests futurs.
"""

import sys
from pathlib import Path

# Ajouter fx_impact_app/src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from create_validation_table import insert_validation_event


def insert_11sept_events():
    """
    Insère les événements du 11 septembre 2025
    
    Basé sur REFERENCE_CASE_11_SEPT_2025.md et observations MT5 d'André
    """
    
    print("=" * 70)
    print("📅 INSERTION ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    # ════════════════════════════════════════════════════════════════
    # ÉVÉNEMENT 1 : Initial Jobless Claims (14:30 CEST = 12:30 UTC)
    # ════════════════════════════════════════════════════════════════
    
    print("\n📋 Événement 1/3 : Initial Jobless Claims")
    print("   Heure : 14:30 CEST (12:30 UTC)")
    print("   Surprise : +28K (+11.9%)")
    
    event1_id = insert_validation_event(
        event_datetime='2025-09-11 12:30:00',  # UTC
        event_key='Initial Jobless Claims',
        family='Jobless_Claims',
        country='US',
        actual=263.0,  # 263K
        forecast=235.0,  # 235K
        estimate=235.0,
        previous=235.0,
        predicted_pips=60.0,  # À ajuster selon vos tests
        direction=1,  # UP (surprise positive = BAD for USD)
        latency_median=5.0,
        ttr_median=7.0,
        empirical_score=75.0,
        source='manual_reference_11sept',
        notes='Événement majeur du 11 sept. Surprise +28K. Famille inversée (surprise+ = EUR/USD UP)'
    )
    
    # ════════════════════════════════════════════════════════════════
    # ÉVÉNEMENT 2 : Consumer Price Index (14:30 CEST = 12:30 UTC)
    # ════════════════════════════════════════════════════════════════
    
    print("\n📋 Événement 2/3 : Consumer Price Index (CPI)")
    print("   Heure : 14:30 CEST (12:30 UTC)")
    print("   Surprise : +0.3%")
    
    event2_id = insert_validation_event(
        event_datetime='2025-09-11 12:30:00',  # UTC
        event_key='Consumer Price Index',
        family='CPI',
        country='US',
        actual=3.0,  # 3.0%
        forecast=2.7,  # 2.7%
        estimate=2.7,
        previous=2.7,
        predicted_pips=80.0,  # À ajuster selon vos tests
        direction=-1,  # DOWN (surprise inflation+ = BAD for EUR = EUR/USD DOWN)
        latency_median=5.0,
        ttr_median=7.0,
        empirical_score=85.0,
        source='manual_reference_11sept',
        notes='Événement majeur simultané. Surprise +0.3%. Famille normale inflation (surprise+ = EUR/USD DOWN)'
    )
    
    # ════════════════════════════════════════════════════════════════
    # ÉVÉNEMENT 3 : Current Account DE (14:45 CEST = 12:45 UTC)
    # ════════════════════════════════════════════════════════════════
    
    print("\n📋 Événement 3/3 : Current Account (DE)")
    print("   Heure : 14:45 CEST (12:45 UTC)")
    print("   Surprise : -5.0B")
    
    event3_id = insert_validation_event(
        event_datetime='2025-09-11 12:45:00',  # UTC
        event_key='Current Account',
        family='Current_Account',
        country='DE',
        actual=15.0,  # 15.0B
        forecast=20.0,  # 20.0B
        estimate=20.0,
        previous=20.0,
        predicted_pips=40.0,  # À ajuster selon vos tests
        direction=-1,  # DOWN (surprise négative = BAD for EUR)
        latency_median=5.0,
        ttr_median=7.0,
        empirical_score=60.0,
        source='manual_reference_11sept',
        notes='Événement secondaire après pullback. Surprise -5.0B. Importance moyenne.'
    )
    
    print("\n" + "=" * 70)
    print("✅ 3 ÉVÉNEMENTS INSÉRÉS")
    print("=" * 70)
    print(f"   Event 1 ID: {event1_id} - Initial Jobless Claims (12:30 UTC)")
    print(f"   Event 2 ID: {event2_id} - Consumer Price Index (12:30 UTC)")
    print(f"   Event 3 ID: {event3_id} - Current Account DE (12:45 UTC)")
    
    print("\n💡 MOUVEMENT RÉEL OBSERVÉ (MT5) :")
    print("   Phase 1 (12:30→12:35) : +37.4 pips")
    print("   Pullback (12:35→12:45) : -27.1 pips")
    print("   Phase 2 (12:45→13:10) : +45.9 pips")
    print("   NET (12:30→13:10) : +56.2 pips")
    
    print("\n📊 CES ÉVÉNEMENTS SONT MAINTENANT DISPONIBLES POUR :")
    print("   - Test Formule A (predict_impact_fast)")
    print("   - Test Formule B (predict_impact)")
    print("   - Test Formule C (timeline v87)")
    print("   - Futurs tests de nouvelles formules")
    
    return [event1_id, event2_id, event3_id]


def verify_insertion():
    """Vérifie que les événements ont bien été insérés"""
    
    from create_validation_table import get_validation_events_for_date
    
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION INSERTION")
    print("=" * 70)
    
    df = get_validation_events_for_date('2025-09-11')
    
    if df.empty:
        print("❌ Aucun événement trouvé pour le 11/09/2025")
        return False
    
    print(f"✅ {len(df)} événement(s) trouvé(s)")
    print("\nDétails :")
    print(df[['id', 'event_time', 'event_key', 'family', 'surprise', 'predicted_pips', 'direction']].to_string(index=False))
    
    return True


def main():
    """Fonction principale"""
    
    # Insérer les événements
    event_ids = insert_11sept_events()
    
    # Vérifier
    verify_insertion()
    
    print("\n✅ SCRIPT TERMINÉ")


if __name__ == "__main__":
    main()
