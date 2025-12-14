#!/usr/bin/env python3
"""
SESSION 73 - PHASE 2 : CROISER MOUVEMENTS AVEC EVENTS

Objectif : Pour chaque mouvement, trouver événements responsables et calculer métriques
- Lire movements_session73.csv (40 mouvements)
- Pour chaque mouvement : query events dans ±10 min
- Calculer 9 métriques cluster
- Identifier événements manquants (mouvements sans events)

Output : dataset_session73.csv
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Chemins
DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
INPUT_FILE = Path(__file__).parent / "movements_session73.csv"
OUTPUT_FILE = Path(__file__).parent / "dataset_session73.csv"

# Paramètres
TIME_WINDOW_MINUTES = 10  # ±10 min autour du mouvement


# ==============================================================================
# FONCTIONS
# ==============================================================================

def calculate_surprise(actual, estimate, forecast, previous):
    """
    Calculer surprise en % avec fallback estimate → forecast → previous.
    
    Retourne 0 si impossible de calculer.
    """
    # Priorité : estimate > forecast > previous
    baseline = estimate if pd.notna(estimate) and estimate != 0 else \
               forecast if pd.notna(forecast) and forecast != 0 else \
               previous if pd.notna(previous) and previous != 0 else None
    
    if baseline is None or pd.isna(actual):
        return 0.0
    
    return abs((actual - baseline) / baseline * 100)


def get_events_for_movement(conn, movement_time, window_minutes=10):
    """
    Récupérer événements dans fenêtre ±window_minutes autour du mouvement.
    
    Args:
        conn: Connexion DuckDB
        movement_time: Datetime du mouvement (str ou datetime)
        window_minutes: Fenêtre temporelle ±N minutes
        
    Returns:
        DataFrame événements avec colonnes nécessaires
    """
    
    # Convertir en string si datetime
    if isinstance(movement_time, pd.Timestamp):
        movement_time = movement_time.strftime('%Y-%m-%d %H:%M:%S')
    
    query = f"""
    SELECT 
        e.ts_utc,
        e.event_key,
        e.event_title,
        e.country,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        e.importance_n,
        ef.family,
        ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE e.ts_utc >= '{movement_time}'::TIMESTAMP - INTERVAL '{window_minutes} minutes'
      AND e.ts_utc <= '{movement_time}'::TIMESTAMP + INTERVAL '{window_minutes} minutes'
    ORDER BY e.ts_utc
    """
    
    df = conn.execute(query).fetchdf()
    return df


def calculate_cluster_metrics(events_df, movement_direction):
    """
    Calculer 9 métriques pour un cluster d'événements.
    
    Args:
        events_df: DataFrame événements
        movement_direction: Direction mouvement réel (1=UP, -1=DOWN)
        
    Returns:
        dict avec 9 métriques
    """
    
    if len(events_df) == 0:
        return {
            'nb_events': 0,
            'score_cumule': 0.0,
            'score_moyen': 0.0,
            'surprise_max': 0.0,
            'surprise_moyenne': 0.0,
            'surprise_cumule': 0.0,
            'ratio_concordance': 0.0,
            'coherence_famille': 0.0,
            'has_high_importance': False
        }
    
    # Calculer surprise pour chaque événement
    surprises = []
    for _, event in events_df.iterrows():
        surprise = calculate_surprise(
            event['actual'],
            event['estimate'],
            event['forecast'],
            event['previous']
        )
        surprises.append(surprise)
    
    events_df['surprise_pct'] = surprises
    
    # Scores
    scores = events_df['empirical_score'].fillna(0)
    
    # Direction concordance (simplifié : assume events HIGH = DOWN pour EUR/USD)
    # On ne peut pas calculer direction précise sans FAMILY_SENTIMENT
    # Pour l'instant : ratio events avec surprise > 0
    events_with_surprise = (events_df['surprise_pct'] > 0).sum()
    ratio_concordance = events_with_surprise / len(events_df) if len(events_df) > 0 else 0.0
    
    # Cohérence famille (ratio famille dominante)
    if events_df['family'].notna().any():
        family_counts = events_df['family'].value_counts()
        coherence_famille = family_counts.iloc[0] / len(events_df) if len(family_counts) > 0 else 0.0
    else:
        coherence_famille = 0.0
    
    # High importance
    has_high_importance = (events_df['importance_n'] == 3).any()
    
    return {
        'nb_events': len(events_df),
        'score_cumule': float(scores.sum()),
        'score_moyen': float(scores.mean()),
        'surprise_max': float(events_df['surprise_pct'].max()),
        'surprise_moyenne': float(events_df['surprise_pct'].mean()),
        'surprise_cumule': float(events_df['surprise_pct'].sum()),
        'ratio_concordance': float(ratio_concordance),
        'coherence_famille': float(coherence_famille),
        'has_high_importance': bool(has_high_importance)
    }


def format_events_list(events_df):
    """Formater liste événements pour export."""
    if len(events_df) == 0:
        return ""
    
    events = []
    for _, event in events_df.iterrows():
        title = event['event_title'] if pd.notna(event['event_title']) else 'Unknown'
        country = event['country'] if pd.notna(event['country']) else '??'
        events.append(f"{country}:{title}")
    
    return " | ".join(events)


def format_families_list(events_df):
    """Formater liste familles pour export."""
    if len(events_df) == 0:
        return ""
    
    families = events_df['family'].dropna().unique()
    return " | ".join(families) if len(families) > 0 else ""


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "="*80)
    print("SESSION 73 - PHASE 2 : CROISER MOUVEMENTS AVEC EVENTS")
    print("="*80)
    
    # Vérifier fichiers existent
    if not INPUT_FILE.exists():
        print(f"\n❌ ERREUR : Fichier movements introuvable : {INPUT_FILE}")
        print(f"   Exécutez d'abord : 1_scanner_movements_DEDUP.py")
        return
    
    if not DB_PATH.exists():
        print(f"\n❌ ERREUR : Base de données introuvable : {DB_PATH}")
        return
    
    print(f"\n✅ Fichier mouvements : {INPUT_FILE}")
    print(f"✅ Base de données : {DB_PATH}")
    print(f"   Fenêtre temporelle : ±{TIME_WINDOW_MINUTES} minutes")
    
    # Charger mouvements
    print(f"\n📂 Chargement mouvements...")
    df_movements = pd.read_csv(INPUT_FILE)
    print(f"   ✅ {len(df_movements)} mouvements chargés")
    
    # Connexion DB
    print(f"\n🔗 Connexion DuckDB...")
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Traiter chaque mouvement
    print(f"\n🔍 Analyse mouvements...")
    print("="*80)
    
    results = []
    movements_with_events = 0
    movements_without_events = 0
    
    for idx, movement in df_movements.iterrows():
        movement_time = movement['datetime']
        impact_pips = movement['impact_pips']
        direction = movement['direction']
        
        print(f"\n[{idx+1}/{len(df_movements)}] {movement['date']} {movement['time']} ({impact_pips:+.1f} pips)")
        
        # Chercher événements
        events_df = get_events_for_movement(conn, movement_time, TIME_WINDOW_MINUTES)
        
        if len(events_df) > 0:
            movements_with_events += 1
            print(f"   ✅ {len(events_df)} événement(s) trouvé(s)")
            
            # Afficher événements
            for _, event in events_df.iterrows():
                title = event['event_title'] if pd.notna(event['event_title']) else 'Unknown'
                country = event['country'] if pd.notna(event['country']) else '??'
                score = event['empirical_score']
                score_str = f"{score:.1f}" if pd.notna(score) else "NA"
                print(f"      - {country} {title} (score: {score_str})")
        else:
            movements_without_events += 1
            print(f"   ⚠️  Aucun événement trouvé")
        
        # Calculer métriques
        metrics = calculate_cluster_metrics(events_df, direction)
        
        # Construire ligne résultat
        result = {
            # Identifiants mouvement
            'year': movement['year'],
            'date': movement['date'],
            'time': movement['time'],
            'datetime': movement['datetime'],
            
            # Variables CIBLES (réalité observée)
            'impact_reel_pips': abs(impact_pips),
            'duration_min': movement['duration_min'],
            'direction': direction,
            
            # Variables PRÉDICTEURS (métriques cluster)
            'nb_events': metrics['nb_events'],
            'score_cumule': metrics['score_cumule'],
            'score_moyen': metrics['score_moyen'],
            'surprise_max': metrics['surprise_max'],
            'surprise_moyenne': metrics['surprise_moyenne'],
            'surprise_cumule': metrics['surprise_cumule'],
            'ratio_concordance': metrics['ratio_concordance'],
            'coherence_famille': metrics['coherence_famille'],
            'has_high_importance': metrics['has_high_importance'],
            
            # Variables CONTEXTE (pour analyse)
            'events_list': format_events_list(events_df),
            'families_list': format_families_list(events_df)
        }
        
        results.append(result)
    
    # Créer DataFrame final
    df_dataset = pd.DataFrame(results)
    
    # Statistiques
    print(f"\n" + "="*80)
    print(f"📊 STATISTIQUES DATASET")
    print("="*80)
    
    print(f"\n🎯 Couverture événements")
    print(f"   Avec événements    : {movements_with_events} mouvements ({movements_with_events/len(df_movements)*100:.1f}%)")
    print(f"   Sans événements    : {movements_without_events} mouvements ({movements_without_events/len(df_movements)*100:.1f}%)")
    
    # Stats sur mouvements AVEC événements
    df_with_events = df_dataset[df_dataset['nb_events'] > 0]
    
    if len(df_with_events) > 0:
        print(f"\n📈 Mouvements AVEC événements (n={len(df_with_events)})")
        print(f"   Nb événements moyen : {df_with_events['nb_events'].mean():.1f}")
        print(f"   Nb événements max   : {df_with_events['nb_events'].max():.0f}")
        print(f"   Score moyen         : {df_with_events['score_moyen'].mean():.1f}")
        print(f"   Surprise max moy.   : {df_with_events['surprise_max'].mean():.1f}%")
        print(f"   Impact moyen        : {df_with_events['impact_reel_pips'].mean():.1f} pips")
    
    # Stats sur mouvements SANS événements
    df_without_events = df_dataset[df_dataset['nb_events'] == 0]
    
    if len(df_without_events) > 0:
        print(f"\n⚠️  Mouvements SANS événements (n={len(df_without_events)})")
        print(f"   Impact moyen        : {df_without_events['impact_reel_pips'].mean():.1f} pips")
        print(f"   Durée moyenne       : {df_without_events['duration_min'].mean():.1f} min")
        
        print(f"\n   Top 5 dates sans événements :")
        for _, row in df_without_events.nlargest(5, 'impact_reel_pips').iterrows():
            print(f"      {row['date']} {row['time']} : {row['impact_reel_pips']:.1f} pips")
    
    # Export CSV
    print(f"\n" + "="*80)
    print(f"💾 EXPORT DATASET")
    print("="*80)
    
    df_dataset.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Fichier créé : {OUTPUT_FILE}")
    print(f"   Total lignes : {len(df_dataset)}")
    print(f"   Colonnes : {len(df_dataset.columns)}")
    
    print(f"\n📋 Colonnes dataset :")
    print(f"   Variables CIBLES (3) : impact_reel_pips, duration_min, direction")
    print(f"   Variables PRÉDICTEURS (9) : nb_events, scores, surprises, concordance, cohérence")
    print(f"   Variables CONTEXTE (2) : events_list, families_list")
    
    # Fermer connexion
    conn.close()
    
    print(f"\n✅ PHASE 2 TERMINÉE")
    print("="*80)


if __name__ == "__main__":
    main()
