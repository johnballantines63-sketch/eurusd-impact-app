"""
Script pour extraire et insérer TOUS les événements du 11 septembre 2025

Ce script :
1. Lit tous les événements du 11 sept depuis la table 'events'
2. Calcule les prédictions via le planificateur (predicted_pips, direction, etc.)
3. Insère tout dans validation_events

Avantage : On récupère TOUS les événements réels, pas juste 3 manuels
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb

# Ajouter fx_impact_app/src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path
from create_validation_table import insert_validation_event


def get_all_events_11sept():
    """
    Récupère TOUS les événements du 11 septembre 2025 depuis la table events
    """
    
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    query = """
    SELECT 
        ts_utc,
        event_key,
        country,
        actual,
        forecast,
        estimate,
        previous,
        importance,
        importance_n
    FROM events
    WHERE DATE(ts_utc) = '2025-09-11'
    ORDER BY ts_utc, importance_n DESC
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    return df


def map_event_to_family(event_key: str):
    """
    Mappe un event_key vers sa famille
    
    Utilise la même logique que le planificateur
    """
    
    # Import de la logique de mapping du planificateur
    # Pour l'instant, mapping simplifié
    
    family_mapping = {
        'Initial Jobless Claims': 'Jobless_Claims',
        'Jobless Claims': 'Jobless_Claims',
        'Consumer Price Index': 'CPI',
        'CPI': 'CPI',
        'Core CPI': 'CPI',
        'Current Account': 'Current_Account',
        'GDP': 'GDP',
        'Retail Sales': 'Retail_Sales',
        'Industrial Production': 'Industrial_Production',
        'Manufacturing PMI': 'PMI',
        'Services PMI': 'PMI',
        'Producer Price Index': 'PPI',
        'Trade Balance': 'Trade_Balance',
        'Building Permits': 'Building_Permits',
        'Housing Starts': 'Housing_Starts',
    }
    
    # Chercher correspondance
    for key_pattern, family in family_mapping.items():
        if key_pattern.lower() in event_key.lower():
            return family
    
    # Si pas de correspondance, utiliser event_key comme famille
    return event_key.replace(' ', '_')


def calculate_predictions_for_event(event_row, precomputed_stats=None):
    """
    Calcule predicted_pips, direction, latency, ttr pour un événement
    
    Utilise la même logique que le planificateur
    """
    
    family = map_event_to_family(event_row['event_key'])
    
    # Calculer surprise
    surprise = 0.0
    surprise_pct = 0.0
    if pd.notna(event_row['actual']) and pd.notna(event_row['forecast']):
        surprise = event_row['actual'] - event_row['forecast']
        if event_row['forecast'] != 0:
            surprise_pct = (surprise / event_row['forecast']) * 100
    
    # Calculer empirical_score (basé sur importance_n)
    importance_n = event_row.get('importance_n', 0)
    if pd.notna(importance_n):
        empirical_score = float(importance_n) * 100 / 3  # Normaliser 0-3 → 0-100
    else:
        empirical_score = 50.0  # Défaut
    
    # Calculer direction (logique simplifiée pour l'instant)
    # TODO: Utiliser vraie fonction get_event_direction du planificateur
    from sequence_multi_event_timeline_v87 import get_event_direction
    
    direction = get_event_direction(family, surprise)
    
    # Calculer predicted_pips (formule v9_clean pour l'instant)
    from forecaster_mvp import ForecastEngine
    
    engine = ForecastEngine(get_db_path())
    predicted_pips = engine.predict_impact_v9_clean(
        empirical_score=empirical_score,
        num_events=1  # Impact individuel
    )
    
    if predicted_pips is None:
        predicted_pips = 10.0  # Défaut
    
    # Latency et TTR (valeurs par défaut pour l'instant)
    latency_median = 5.0
    ttr_median = 10.0
    
    return {
        'family': family,
        'surprise': surprise,
        'surprise_pct': surprise_pct,
        'predicted_pips': abs(predicted_pips),
        'direction': direction,
        'latency_median': latency_median,
        'ttr_median': ttr_median,
        'empirical_score': empirical_score
    }


def insert_all_11sept_events():
    """
    Insère TOUS les événements du 11 septembre dans validation_events
    """
    
    print("=" * 70)
    print("📅 EXTRACTION & INSERTION - TOUS ÉVÉNEMENTS 11 SEPTEMBRE 2025")
    print("=" * 70)
    
    # Récupérer événements depuis table events
    print("\n📥 Récupération événements depuis table 'events'...")
    df = get_all_events_11sept()
    
    if df.empty:
        print("❌ Aucun événement trouvé pour le 11/09/2025")
        return
    
    print(f"✅ {len(df)} événement(s) trouvé(s)")
    
    # Afficher résumé
    print("\n📊 Résumé des événements :")
    for idx, row in df.iterrows():
        time_str = pd.to_datetime(row['ts_utc']).strftime('%H:%M')
        print(f"   {idx+1}. {time_str} - {row['event_key']} ({row['country']})")
    
    # Calculer prédictions pour chaque événement
    print("\n🔢 Calcul des prédictions...")
    
    inserted_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Calculer prédictions
            predictions = calculate_predictions_for_event(row)
            
            # Insérer
            event_id = insert_validation_event(
                event_datetime=str(row['ts_utc']),
                event_key=row['event_key'],
                family=predictions['family'],
                country=row['country'],
                actual=row['actual'] if pd.notna(row['actual']) else None,
                forecast=row['forecast'] if pd.notna(row['forecast']) else None,
                estimate=row['estimate'] if pd.notna(row['estimate']) else None,
                previous=row['previous'] if pd.notna(row['previous']) else None,
                predicted_pips=predictions['predicted_pips'],
                direction=predictions['direction'],
                latency_median=predictions['latency_median'],
                ttr_median=predictions['ttr_median'],
                empirical_score=predictions['empirical_score'],
                source='auto_extract_from_events',
                notes=f"Auto-extrait de la table events. Surprise: {predictions['surprise']:.2f}, Score: {predictions['empirical_score']:.1f}"
            )
            
            inserted_count += 1
            
        except Exception as e:
            print(f"⚠️  Erreur insertion événement {idx+1} ({row['event_key']}) : {e}")
    
    print(f"\n✅ {inserted_count} événement(s) inséré(s) avec succès")
    
    # Vérifier
    verify_insertion_complete()


def verify_insertion_complete():
    """Vérifie l'insertion avec TOUTES les colonnes"""
    
    from create_validation_table import get_validation_events_for_date
    
    print("\n" + "=" * 70)
    print("🔍 VÉRIFICATION COMPLÈTE")
    print("=" * 70)
    
    df = get_validation_events_for_date('2025-09-11')
    
    if df.empty:
        print("❌ Aucun événement trouvé")
        return
    
    print(f"✅ {len(df)} événement(s) dans validation_events")
    
    # Afficher résumé complet
    print("\n📊 Détails complets :")
    
    for idx, row in df.iterrows():
        print(f"\n{'─' * 70}")
        print(f"📍 Événement {idx + 1}/{len(df)}")
        print(f"{'─' * 70}")
        print(f"   ID              : {row['id']}")
        print(f"   DateTime        : {row['event_datetime']}")
        print(f"   Event Key       : {row['event_key']}")
        print(f"   Family          : {row['family']}")
        print(f"   Country         : {row['country']}")
        print(f"   Actual          : {row['actual']}")
        print(f"   Forecast        : {row['forecast']}")
        print(f"   Surprise        : {row['surprise']:.2f}" if pd.notna(row['surprise']) else "   Surprise        : N/A")
        print(f"   Surprise %      : {row['surprise_pct']:.1f}%" if pd.notna(row['surprise_pct']) else "   Surprise %      : N/A")
        print(f"   Predicted Pips  : {row['predicted_pips']:.1f}")
        print(f"   Direction       : {'+' if row['direction'] > 0 else '-'}")
        print(f"   Empirical Score : {row['empirical_score']:.1f}")
        print(f"   Latency         : {row['latency_median']:.1f} min")
        print(f"   TTR             : {row['ttr_median']:.1f} min")
    
    print("\n" + "=" * 70)


def main():
    """Fonction principale"""
    
    print("\n⚠️  AVERTISSEMENT :")
    print("   Ce script va REMPLACER les 3 événements manuels")
    print("   par TOUS les événements réels du 11 septembre.")
    print()
    
    response = input("   Continuer ? (o/n) : ")
    
    if response.lower() != 'o':
        print("❌ Annulé")
        return
    
    # Supprimer événements existants du 11 sept
    print("\n🗑️  Suppression événements existants du 11 sept...")
    conn = duckdb.connect(get_db_path())
    conn.execute("DELETE FROM validation_events WHERE event_date = '2025-09-11'")
    conn.commit()
    conn.close()
    print("✅ Événements supprimés")
    
    # Insérer tous les événements
    insert_all_11sept_events()
    
    print("\n✅ SCRIPT TERMINÉ")
    print("\n💡 Vous pouvez maintenant lancer test_multi_formulas.py")


if __name__ == "__main__":
    main()
