"""
Script pour insérer les 11 événements EXACTS du 11 septembre 2025

Données sources : Calendrier économique réel fourni par André
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path
from create_validation_table import insert_validation_event
from sequence_multi_event_timeline_v87 import get_event_direction
import duckdb


def clear_existing_events():
    """Supprime les événements existants du 11 septembre"""
    conn = duckdb.connect(get_db_path())
    conn.execute("DELETE FROM validation_events WHERE event_date = '2025-09-11'")
    conn.commit()
    conn.close()
    print("✅ Événements existants supprimés")


def insert_exact_11sept_events():
    """
    Insère les 11 événements EXACTS du 11 septembre 2025
    avec les données réelles du calendrier économique
    """
    
    print("=" * 70)
    print("📅 INSERTION ÉVÉNEMENTS EXACTS - 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    events = [
        # ════════════════════════════════════════════════════════════════
        # 14:30 CEST (12:30 UTC) - 9 ÉVÉNEMENTS US SIMULTANÉS
        # ════════════════════════════════════════════════════════════════
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'Continuing Jobless Claims',
            'family': 'Jobless_Claims',
            'country': 'US',
            'actual': 1939.0,  # 1939K
            'forecast': 1950.0,  # 1950K
            'estimate': 1950.0,
            'previous': 1939.0,
            'importance': 'HIGH',
            'notes': 'Reclamations Continues des Sans-Emploi (Aug/30)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'Initial Jobless Claims',
            'family': 'Jobless_Claims',
            'country': 'US',
            'actual': 263.0,  # 263K
            'forecast': 235.0,  # 235K
            'estimate': 235.0,
            'previous': 236.0,  # 236K
            'importance': 'HIGH',
            'notes': 'Revendications chômage initiales (Sep/06) - ÉVÉNEMENT MAJEUR'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': '4-Week Average Jobless Claims',
            'family': 'Jobless_Claims',
            'country': 'US',
            'actual': 240.5,  # 240.5K
            'forecast': 232.0,  # 232K
            'estimate': 232.0,
            'previous': 230.75,  # 230.75K
            'importance': 'HIGH',
            'notes': 'Demandes de chômage, moyenne sur 4 semaines (Sep/06)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'Core CPI MoM',
            'family': 'CPI',
            'country': 'US',
            'actual': 0.3,  # 0.3%
            'forecast': 0.3,  # 0.3%
            'estimate': 0.3,
            'previous': 0.3,
            'importance': 'HIGH',
            'notes': 'Taux D\'Inflation De Base (Mensuel) (Aug)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'CPI Index',
            'family': 'CPI',
            'country': 'US',
            'actual': 323.364,
            'forecast': 323.0,
            'estimate': 323.0,
            'previous': 322.132,
            'importance': 'HIGH',
            'notes': 'IPC de (Aug)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'CPI Final',
            'family': 'CPI',
            'country': 'US',
            'actual': 323.98,
            'forecast': 323.89,
            'estimate': 323.89,
            'previous': 323.05,
            'importance': 'HIGH',
            'notes': 'IPC finale (Aug)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'CPI MoM',
            'family': 'CPI',
            'country': 'US',
            'actual': 0.4,  # 0.4%
            'forecast': 0.3,  # 0.3%
            'estimate': 0.3,
            'previous': 0.2,  # 0.2%
            'importance': 'HIGH',
            'notes': 'Taux d\'inflation (mensuel) (Aug) - SURPRISE +'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'CPI YoY',
            'family': 'CPI',
            'country': 'US',
            'actual': 2.9,  # 2.9%
            'forecast': 2.9,  # 2.9%
            'estimate': 2.9,
            'previous': 2.7,  # 2.7%
            'importance': 'HIGH',
            'notes': 'Taux D\'Inflation (Annuel) (Aug)'
        },
        {
            'datetime': '2025-09-11 12:30:00',
            'event_key': 'Core CPI YoY',
            'family': 'CPI',
            'country': 'US',
            'actual': 3.1,  # 3.1%
            'forecast': 3.1,  # 3.1%
            'estimate': 3.1,
            'previous': 3.1,
            'importance': 'HIGH',
            'notes': 'Taux D\'Inflation De Base (Annuel) (Aug)'
        },
        
        # ════════════════════════════════════════════════════════════════
        # 14:45 CEST (12:45 UTC) - 2 ÉVÉNEMENTS EUR
        # ════════════════════════════════════════════════════════════════
        {
            'datetime': '2025-09-11 12:45:00',
            'event_key': 'ECB Press Conference',
            'family': 'Interest_Rate_Decision',
            'country': 'EUR',
            'actual': None,
            'forecast': None,
            'estimate': None,
            'previous': None,
            'importance': 'HIGH',
            'notes': 'Conférence De Presse De La BCE'
        },
        {
            'datetime': '2025-09-11 12:45:00',
            'event_key': 'Current Account',
            'family': 'Current_Account',
            'country': 'EUR',
            'actual': 14.8,  # €14.8B
            'forecast': 21.5,  # €21.5B
            'estimate': 21.5,
            'previous': 17.1,  # €17.1B
            'importance': 'LOW',
            'notes': 'Compte Courant (Jul) - FAIBLE importance'
        }
    ]
    
    # Calculer prédictions pour chaque événement
    from forecaster_mvp import ForecastEngine
    engine = ForecastEngine(get_db_path())
    
    inserted_ids = []
    
    for idx, evt in enumerate(events):
        print(f"\n📋 Événement {idx + 1}/11 : {evt['event_key']}")
        
        # Calculer surprise
        surprise = 0.0
        surprise_pct = 0.0
        if evt['actual'] is not None and evt['forecast'] is not None:
            surprise = evt['actual'] - evt['forecast']
            if evt['forecast'] != 0:
                surprise_pct = (surprise / evt['forecast']) * 100
            print(f"   Surprise : {surprise:+.2f} ({surprise_pct:+.1f}%)")
        else:
            print(f"   Surprise : N/A (pas de actual/forecast)")
        
        # Empirical score basé sur importance
        if evt['importance'] == 'HIGH':
            empirical_score = 85.0
        elif evt['importance'] == 'MEDIUM':
            empirical_score = 60.0
        else:  # LOW
            empirical_score = 40.0
        
        # Predicted pips via formule v9_clean
        predicted_pips = engine.predict_impact_v9_clean(
            empirical_score=empirical_score,
            num_events=1
        )
        
        if predicted_pips is None or predicted_pips < 0:
            predicted_pips = 10.0  # Défaut
        
        # Direction
        direction = get_event_direction(evt['family'], surprise)
        
        print(f"   Predicted : {predicted_pips:.1f} pips, Direction : {'+' if direction > 0 else '-'}")
        
        # Insérer
        try:
            event_id = insert_validation_event(
                event_datetime=evt['datetime'],
                event_key=evt['event_key'],
                family=evt['family'],
                country=evt['country'],
                actual=evt['actual'],
                forecast=evt['forecast'],
                estimate=evt['estimate'],
                previous=evt['previous'],
                predicted_pips=predicted_pips,
                direction=direction,
                latency_median=5.0,
                ttr_median=10.0,
                empirical_score=empirical_score,
                source='manual_exact_calendar',
                notes=evt['notes']
            )
            inserted_ids.append(event_id)
            print(f"   ✅ Inséré : ID={event_id}")
        except Exception as e:
            print(f"   ❌ Erreur : {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ {len(inserted_ids)} ÉVÉNEMENTS INSÉRÉS")
    print("=" * 70)
    
    return inserted_ids


def verify_insertion():
    """Vérifie l'insertion avec détails complets"""
    
    from create_validation_table import get_validation_events_for_date
    import pandas as pd
    
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION COMPLÈTE")
    print("=" * 70)
    
    df = get_validation_events_for_date('2025-09-11')
    
    if df.empty:
        print("❌ Aucun événement trouvé")
        return
    
    print(f"✅ {len(df)} événement(s) trouvé(s)")
    
    # Grouper par heure
    # event_time est déjà un objet time, pas besoin de to_datetime
    df['hour'] = df['event_time'].astype(str).str[:5]  # Extraire HH:MM
    
    for hour in df['hour'].unique():
        hour_events = df[df['hour'] == hour]
        print(f"\n⏰ {hour} UTC ({len(hour_events)} événements)")
        print("─" * 70)
        
        for _, row in hour_events.iterrows():
            surprise_str = f"{row['surprise']:+.2f}" if pd.notna(row['surprise']) else "N/A"
            dir_str = "⬆️ UP" if row['direction'] > 0 else "⬇️ DOWN"
            
            print(f"   • {row['event_key']} ({row['country']})")
            print(f"     Actual: {row['actual']}, Forecast: {row['forecast']}, Surprise: {surprise_str}")
            print(f"     → {row['predicted_pips']:.1f} pips {dir_str}, Score: {row['empirical_score']:.0f}")
    
    # Résumé global
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ GLOBAL")
    print("=" * 70)
    print(f"   Total événements    : {len(df)}")
    print(f"   Événements 12:30 UTC : {len(df[df['hour'] == '12:30'])}")
    print(f"   Événements 12:45 UTC : {len(df[df['hour'] == '12:45'])}")
    print(f"   Impact total prédit  : {df['predicted_pips'].sum():.1f} pips (brut)")
    print(f"   UP (direction +1)    : {len(df[df['direction'] > 0])}")
    print(f"   DOWN (direction -1)  : {len(df[df['direction'] < 0])}")


def main():
    """Fonction principale"""
    
    print("\n⚠️  Ce script va remplacer les événements existants")
    print("   par les 11 événements EXACTS du calendrier économique")
    print()
    
    response = input("   Continuer ? (o/n) : ")
    
    if response.lower() != 'o':
        print("❌ Annulé")
        return
    
    # Supprimer événements existants
    print("\n🗑️  Suppression événements existants...")
    clear_existing_events()
    
    # Insérer événements exacts
    insert_exact_11sept_events()
    
    # Vérifier
    verify_insertion()
    
    print("\n✅ SCRIPT TERMINÉ")
    print("\n💡 Les 11 événements sont prêts pour les tests multi-formules")


if __name__ == "__main__":
    main()
