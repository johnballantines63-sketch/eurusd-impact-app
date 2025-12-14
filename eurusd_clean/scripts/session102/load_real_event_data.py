#!/usr/bin/env python3
"""
Script Session 102 - Charger Données Réelles Événements

Mission : Pour chaque date dans real_impacts_TIMEZONE_FIX_FINAL.csv,
charger les VRAIES données événements depuis warehouse.duckdb :
- base_score RÉEL (moyenne empirical_score des événements HIGH IMPACT)
- surprise RÉELLE (max |actual - estimate| / |estimate| × 100)
- num_events RÉEL (nombre événements HIGH IMPACT dans le cluster)

Résout le problème identifié Session 101.5 : données hardcodées qui empêchaient
de trouver les corrélations.

Auteur : Claude, Session 102
Date : 30 octobre 2025
"""

import pandas as pd
import duckdb
from pathlib import Path
from typing import Dict, Any
import sys

# Configuration chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT.parent / "warehouse.duckdb"
INPUT_CSV = PROJECT_ROOT / "scripts/session99/real_impacts_TIMEZONE_FIX_FINAL.csv"
OUTPUT_CSV = PROJECT_ROOT / "scripts/session102/real_event_data.csv"

# Seuil HIGH IMPACT
MIN_SCORE = 40


def load_real_impacts() -> pd.DataFrame:
    """Charge le fichier des impacts réels."""
    print(f"\n📂 Chargement impacts réels depuis : {INPUT_CSV}")
    
    if not INPUT_CSV.exists():
        print(f"❌ Fichier introuvable : {INPUT_CSV}")
        sys.exit(1)
    
    df = pd.read_csv(INPUT_CSV)
    print(f"✅ {len(df)} dates chargées")
    
    # Extraire uniquement la date (sans heure)
    df['date_only'] = pd.to_datetime(df['date']).dt.date
    
    return df


def query_events_for_date(conn: duckdb.DuckDBPyConnection, date_str: str) -> pd.DataFrame:
    """
    Query événements HIGH IMPACT pour une date donnée.
    
    Args:
        conn: Connexion DuckDB
        date_str: Date au format 'YYYY-MM-DD'
    
    Returns:
        DataFrame avec colonnes : event_key, event_title, actual, estimate, 
        forecast, previous, empirical_score, latency_median
    """
    query = """
    SELECT 
        e.event_key,
        e.event_title,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > ?
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query, [date_str, MIN_SCORE]).df()
    return df


def calculate_surprise(row: pd.Series) -> float:
    """
    Calcule la surprise pour un événement.
    
    Utilise estimate en priorité, sinon forecast, sinon previous.
    Surprise = |actual - reference| / |reference| × 100
    
    Args:
        row: Ligne avec colonnes actual, estimate, forecast, previous
    
    Returns:
        Surprise en % (ou 0.0 si non calculable)
    """
    actual = row['actual']
    estimate = row['estimate']
    forecast = row['forecast']
    previous = row['previous']
    
    # Priorité : estimate > forecast > previous
    reference = None
    if pd.notna(estimate) and estimate != 0:
        reference = estimate
    elif pd.notna(forecast) and forecast != 0:
        reference = forecast
    elif pd.notna(previous) and previous != 0:
        reference = previous
    
    if reference is None or pd.isna(actual):
        return 0.0
    
    surprise = abs((actual - reference) / reference) * 100
    return surprise


def process_date(conn: duckdb.DuckDBPyConnection, date_obj: Any, impact_real: float) -> Dict[str, Any]:
    """
    Process une date : charge événements et calcule métriques RÉELLES.
    
    Args:
        conn: Connexion DuckDB
        date_obj: Date (pandas datetime ou date)
        impact_real: Impact réel en pips
    
    Returns:
        Dict avec : date, base_score_real, surprise_real, num_events_real, impact_real
    """
    # Convertir en string YYYY-MM-DD
    if hasattr(date_obj, 'strftime'):
        date_str = date_obj.strftime('%Y-%m-%d')
    else:
        date_str = str(date_obj)
    
    print(f"\n📅 Processing {date_str}...")
    
    # Query événements
    events_df = query_events_for_date(conn, date_str)
    
    if events_df.empty:
        print(f"  ⚠️  Aucun événement HIGH IMPACT trouvé pour {date_str}")
        return {
            'date': date_str,
            'base_score_real': 0.0,
            'surprise_real': 0.0,
            'num_events_real': 0,
            'impact_real': impact_real,
            'warning': 'NO_EVENTS'
        }
    
    # Calculer métriques RÉELLES
    num_events = len(events_df)
    base_score = events_df['empirical_score'].mean()
    
    # Calculer surprises
    events_df['surprise'] = events_df.apply(calculate_surprise, axis=1)
    surprise_max = events_df['surprise'].max()
    
    print(f"  ✅ {num_events} événements trouvés")
    print(f"  📊 Score moyen : {base_score:.2f}")
    print(f"  🎯 Surprise max : {surprise_max:.2f}%")
    
    # Debug : afficher événements
    for idx, row in events_df.iterrows():
        print(f"     - {row['event_title']}: score={row['empirical_score']:.1f}, surprise={row['surprise']:.1f}%")
    
    return {
        'date': date_str,
        'base_score_real': base_score,
        'surprise_real': surprise_max,
        'num_events_real': num_events,
        'impact_real': impact_real
    }


def main():
    """Main : charge impacts réels et query événements DB pour chaque date."""
    print("="*80)
    print("🚀 SESSION 102 - CHARGEMENT DONNÉES RÉELLES ÉVÉNEMENTS")
    print("="*80)
    
    # Vérifier DB existe
    if not DB_PATH.exists():
        print(f"❌ DB introuvable : {DB_PATH}")
        sys.exit(1)
    
    print(f"✅ DB trouvée : {DB_PATH}")
    
    # Charger impacts réels
    impacts_df = load_real_impacts()
    
    # Connexion DB (read-only)
    print(f"\n🔌 Connexion à la DB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Process chaque date
        results = []
        
        for idx, row in impacts_df.iterrows():
            date_only = row['date_only']
            impact_real = row['impact_pips']
            
            result = process_date(conn, date_only, impact_real)
            results.append(result)
        
        # Créer DataFrame résultats
        results_df = pd.DataFrame(results)
        
        # Sauvegarder
        print(f"\n💾 Sauvegarde résultats : {OUTPUT_CSV}")
        results_df.to_csv(OUTPUT_CSV, index=False)
        print(f"✅ {len(results_df)} dates sauvegardées")
        
        # Stats finales
        print("\n" + "="*80)
        print("📊 STATISTIQUES FINALES")
        print("="*80)
        
        # Filtrer dates avec événements
        valid_df = results_df[results_df['num_events_real'] > 0]
        
        print(f"\n✅ Dates avec événements : {len(valid_df)} / {len(results_df)}")
        
        if len(valid_df) > 0:
            print(f"\n📈 Base Score Réel :")
            print(f"   Min  : {valid_df['base_score_real'].min():.2f}")
            print(f"   Max  : {valid_df['base_score_real'].max():.2f}")
            print(f"   Moy  : {valid_df['base_score_real'].mean():.2f}")
            print(f"   Std  : {valid_df['base_score_real'].std():.2f}")
            
            print(f"\n🎯 Surprise Réelle :")
            print(f"   Min  : {valid_df['surprise_real'].min():.2f}%")
            print(f"   Max  : {valid_df['surprise_real'].max():.2f}%")
            print(f"   Moy  : {valid_df['surprise_real'].mean():.2f}%")
            print(f"   Std  : {valid_df['surprise_real'].std():.2f}%")
            
            print(f"\n🔢 Nombre Événements :")
            print(f"   Min  : {valid_df['num_events_real'].min()}")
            print(f"   Max  : {valid_df['num_events_real'].max()}")
            print(f"   Moy  : {valid_df['num_events_real'].mean():.1f}")
            
            print(f"\n💥 Impact Réel :")
            print(f"   Min  : {valid_df['impact_real'].min():.1f} pips")
            print(f"   Max  : {valid_df['impact_real'].max():.1f} pips")
            print(f"   Moy  : {valid_df['impact_real'].mean():.1f} pips")
        
        # Vérifier variance (critique pour corrélations)
        print("\n" + "="*80)
        print("🔍 VÉRIFICATION VARIANCE (critique pour corrélations)")
        print("="*80)
        
        if len(valid_df) > 0:
            score_var = valid_df['base_score_real'].var()
            surprise_var = valid_df['surprise_real'].var()
            events_var = valid_df['num_events_real'].var()
            
            print(f"\n✅ Variance Base Score : {score_var:.2f} {'✓ OK' if score_var > 0 else '❌ NULLE'}")
            print(f"✅ Variance Surprise : {surprise_var:.2f} {'✓ OK' if surprise_var > 0 else '❌ NULLE'}")
            print(f"✅ Variance Num Events : {events_var:.2f} {'✓ OK' if events_var > 0 else '❌ NULLE'}")
            
            if score_var > 0 and surprise_var > 0 and events_var > 0:
                print(f"\n🎉 VARIANCE NON-NULLE POUR TOUTES VARIABLES !")
                print(f"   → Corrélations deviennent possibles !")
            else:
                print(f"\n⚠️  Certaines variables ont variance nulle")
                print(f"   → Corrélations impossibles pour ces variables")
        
        print("\n" + "="*80)
        print("✅ SESSION 102 - CHARGEMENT TERMINÉ AVEC SUCCÈS")
        print("="*80)
        print(f"\n📁 Fichier créé : {OUTPUT_CSV}")
        print(f"\n➡️  Prochaine étape : Exécuter analyze_with_real_data.py")
        
    finally:
        conn.close()
        print(f"\n🔌 Connexion DB fermée")


if __name__ == "__main__":
    main()
