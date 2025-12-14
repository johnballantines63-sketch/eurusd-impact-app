#!/usr/bin/env python3
"""
Créer Dataset Complet - Session 73
Croiser mouvements forts avec événements DB

Objectif : Pour chaque mouvement fort, identifier événements associés
         et calculer métriques prédicteurs

Author: Claude
Date: 24 octobre 2025
"""

import sys
from pathlib import Path

# Ajouter fx_impact_app au path
fx_impact_app_path = Path(__file__).parent.parent
sys.path.insert(0, str(fx_impact_app_path))

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Path database
DB_PATH = fx_impact_app_path / "data" / "warehouse.duckdb"
MOVEMENTS_CSV = fx_impact_app_path / "data" / "movements_strong_session73.csv"


def load_movements(csv_path: str) -> pd.DataFrame:
    """
    Charger mouvements depuis CSV scanner
    
    Args:
        csv_path: Chemin CSV movements
    
    Returns:
        DataFrame mouvements
    """
    
    print(f"\n📂 Chargement mouvements depuis CSV...")
    df = pd.read_csv(csv_path)
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print(f"   ✅ {len(df)} mouvements chargés")
    
    return df


def get_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement_datetime: datetime,
    time_window_minutes: int = 10
) -> pd.DataFrame:
    """
    Récupérer événements associés à un mouvement
    
    Args:
        conn: Connexion DuckDB
        movement_datetime: Datetime du mouvement (peak)
        time_window_minutes: Fenêtre recherche événements (±N min)
    
    Returns:
        DataFrame événements trouvés
    """
    
    # Fenêtre temporelle
    start_time = movement_datetime - timedelta(minutes=time_window_minutes)
    end_time = movement_datetime + timedelta(minutes=time_window_minutes)
    
    # Query événements
    query = f"""
    SELECT 
        e.event_key,
        e.event_title,
        e.ts_utc,
        e.country,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        e.importance_n,
        AVG(ef.empirical_score) as empirical_score,
        MIN(ef.family) as family,
        CASE 
            WHEN e.estimate IS NOT NULL AND e.estimate != 0 
            THEN ABS((e.actual - e.estimate) / e.estimate * 100)
            WHEN e.forecast IS NOT NULL AND e.forecast != 0
            THEN ABS((e.actual - e.forecast) / e.forecast * 100)
            WHEN e.previous IS NOT NULL AND e.previous != 0
            THEN ABS((e.actual - e.previous) / e.previous * 100)
            ELSE 0
        END as surprise_pct
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.ts_utc >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
        AND e.ts_utc <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
        AND e.country = 'US'
    GROUP BY 
        e.event_key, e.event_title, e.ts_utc, e.country,
        e.actual, e.estimate, e.forecast, e.previous, e.importance_n
    ORDER BY e.ts_utc
    """
    
    df_events = conn.execute(query).fetchdf()
    
    return df_events


def calculate_cluster_metrics(df_events: pd.DataFrame, movement_direction: str) -> dict:
    """
    Calculer métriques du cluster d'événements
    
    Args:
        df_events: DataFrame événements
        movement_direction: Direction mouvement (UP/DOWN)
    
    Returns:
        dict avec métriques calculées
    """
    
    if len(df_events) == 0:
        return {
            'nb_events': 0,
            'score_cumule': 0,
            'score_moyen': 0,
            'surprise_max': 0,
            'surprise_moyenne': 0,
            'surprise_cumule': 0,
            'ratio_concordance': 0,
            'coherence_famille': 0,
            'families_list': '',
            'events_list': '',
            'has_high_importance': False
        }
    
    # Métriques de base
    nb_events = len(df_events)
    score_cumule = df_events['empirical_score'].sum()
    score_moyen = df_events['empirical_score'].mean()
    surprise_max = df_events['surprise_pct'].max()
    surprise_moyenne = df_events['surprise_pct'].mean()
    surprise_cumule = df_events['surprise_pct'].sum()
    
    # Concordance direction
    # Logique : CPI/GDP/NFP surprise+ = économie forte = USD fort = EUR/USD DOWN
    # On compte combien d'événements vont dans le sens du mouvement observé
    
    # Simplification : utiliser signe de (actual - estimate)
    # Si actual > estimate (surprise positive) → USD fort probable → DOWN attendu
    # Si actual < estimate (surprise négative) → USD faible probable → UP attendu
    
    df_events['expected_direction'] = df_events.apply(
        lambda row: 'DOWN' if (row['actual'] or 0) > (row['estimate'] or row['forecast'] or row['previous'] or 0)
                    else 'UP',
        axis=1
    )
    
    concordant_events = (df_events['expected_direction'] == movement_direction).sum()
    ratio_concordance = concordant_events / nb_events if nb_events > 0 else 0
    
    # Cohérence famille (tous même famille = 1.0, mix = 0.0-0.9)
    families = df_events['family'].dropna().unique()
    if len(families) == 0:
        coherence_famille = 0
    elif len(families) == 1:
        coherence_famille = 1.0
    else:
        # Ratio événements de la famille dominante
        famille_dominante = df_events['family'].value_counts().iloc[0]
        coherence_famille = famille_dominante / nb_events
    
    # Has HIGH importance
    has_high_importance = (df_events['importance_n'] == 3).any()
    
    # Listes pour inspection
    families_list = ', '.join(families) if len(families) > 0 else 'None'
    events_list = ' | '.join(df_events['event_title'].tolist())
    
    return {
        'nb_events': nb_events,
        'score_cumule': score_cumule,
        'score_moyen': score_moyen,
        'surprise_max': surprise_max,
        'surprise_moyenne': surprise_moyenne,
        'surprise_cumule': surprise_cumule,
        'ratio_concordance': ratio_concordance,
        'coherence_famille': coherence_famille,
        'families_list': families_list,
        'events_list': events_list,
        'has_high_importance': has_high_importance
    }


def create_complete_dataset(
    movements_csv: str,
    db_path: str,
    time_window_minutes: int = 10
) -> pd.DataFrame:
    """
    Créer dataset complet en croisant mouvements et événements
    
    Args:
        movements_csv: Chemin CSV mouvements
        db_path: Chemin warehouse.duckdb
        time_window_minutes: Fenêtre recherche événements
    
    Returns:
        DataFrame dataset complet
    """
    
    print(f"\n{'='*70}")
    print(f"CRÉATION DATASET COMPLET - SESSION 73")
    print(f"{'='*70}\n")
    
    # 1. Charger mouvements
    df_movements = load_movements(movements_csv)
    
    # 2. Connexion DB
    print(f"\n🔌 Connexion database...")
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # 3. Pour chaque mouvement, récupérer événements et calculer métriques
    print(f"\n🔍 Analyse mouvements et croisement événements...")
    print(f"   Fenêtre temporelle : ±{time_window_minutes} min")
    
    dataset = []
    
    for idx, movement in df_movements.iterrows():
        
        if (idx + 1) % 10 == 0:
            print(f"   Progression : {idx+1}/{len(df_movements)} mouvements traités...")
        
        # Récupérer événements
        df_events = get_events_for_movement(
            conn, 
            movement['datetime'],
            time_window_minutes
        )
        
        # Calculer métriques
        metrics = calculate_cluster_metrics(df_events, movement['direction'])
        
        # Créer row dataset
        row = {
            # Variables CIBLES (à prédire)
            'impact_reel_pips': movement['abs_impact'],
            'direction': movement['direction'],
            
            # Informations temporelles
            'date': movement['date'],
            'time': movement['time'],
            'datetime': movement['datetime'],
            'price_start': movement['price_start'],
            'price_peak': movement['price_peak'],
            
            # PRÉDICTEURS (features)
            'nb_events': metrics['nb_events'],
            'score_cumule': metrics['score_cumule'],
            'score_moyen': metrics['score_moyen'],
            'surprise_max': metrics['surprise_max'],
            'surprise_moyenne': metrics['surprise_moyenne'],
            'surprise_cumule': metrics['surprise_cumule'],
            'ratio_concordance': metrics['ratio_concordance'],
            'coherence_famille': metrics['coherence_famille'],
            'has_high_importance': metrics['has_high_importance'],
            
            # Informations contextuelles
            'families_list': metrics['families_list'],
            'events_list': metrics['events_list']
        }
        
        dataset.append(row)
    
    conn.close()
    
    # Créer DataFrame
    df_dataset = pd.DataFrame(dataset)
    
    print(f"\n✅ Dataset créé !")
    print(f"   Lignes : {len(df_dataset)}")
    print(f"   Colonnes : {len(df_dataset.columns)}")
    
    return df_dataset


def analyze_dataset_statistics(df: pd.DataFrame):
    """
    Analyser statistiques descriptives du dataset
    
    Args:
        df: DataFrame dataset
    """
    
    print(f"\n{'='*70}")
    print(f"ANALYSE STATISTIQUES DATASET")
    print(f"{'='*70}\n")
    
    # Statistiques variables cibles
    print(f"📊 VARIABLES CIBLES :")
    print(f"\n   Impact Réel (pips) :")
    print(f"      Moyenne : {df['impact_reel_pips'].mean():.1f}")
    print(f"      Médiane : {df['impact_reel_pips'].median():.1f}")
    print(f"      Écart-type : {df['impact_reel_pips'].std():.1f}")
    print(f"      Min : {df['impact_reel_pips'].min():.1f}")
    print(f"      Max : {df['impact_reel_pips'].max():.1f}")
    
    print(f"\n   Direction :")
    direction_counts = df['direction'].value_counts()
    for direction, count in direction_counts.items():
        print(f"      {direction} : {count} ({count/len(df)*100:.1f}%)")
    
    # Statistiques prédicteurs
    print(f"\n📈 PRÉDICTEURS :")
    
    print(f"\n   Nb Événements :")
    print(f"      Moyenne : {df['nb_events'].mean():.1f}")
    print(f"      Médiane : {df['nb_events'].median():.1f}")
    print(f"      Min : {df['nb_events'].min():.0f}")
    print(f"      Max : {df['nb_events'].max():.0f}")
    
    print(f"\n   Score Cumulé :")
    print(f"      Moyenne : {df['score_cumule'].mean():.1f}")
    print(f"      Médiane : {df['score_cumule'].median():.1f}")
    
    print(f"\n   Surprise Max (%) :")
    print(f"      Moyenne : {df['surprise_max'].mean():.1f}%")
    print(f"      Médiane : {df['surprise_max'].median():.1f}%")
    print(f"      Max : {df['surprise_max'].max():.1f}%")
    
    print(f"\n   Ratio Concordance :")
    print(f"      Moyenne : {df['ratio_concordance'].mean():.2f}")
    print(f"      Médiane : {df['ratio_concordance'].median():.2f}")
    
    print(f"\n   Cohérence Famille :")
    print(f"      Moyenne : {df['coherence_famille'].mean():.2f}")
    print(f"      Médiane : {df['coherence_famille'].median():.2f}")
    
    # Mouvements sans événements
    no_events = (df['nb_events'] == 0).sum()
    print(f"\n⚠️  Mouvements SANS événements détectés : {no_events} ({no_events/len(df)*100:.1f}%)")
    
    if no_events > 0:
        print(f"   → Ces mouvements sont probablement dus à :")
        print(f"      - Événements non-US (pas dans scope)")
        print(f"      - Réactions cumulatives tardives")
        print(f"      - Mouvements techniques (pas fondamentaux)")


def export_dataset(df: pd.DataFrame, output_path: str):
    """
    Exporter dataset vers CSV
    
    Args:
        df: DataFrame dataset
        output_path: Chemin fichier output
    """
    
    print(f"\n💾 Export dataset...")
    
    df.to_csv(output_path, index=False)
    
    print(f"   ✅ Fichier créé : {output_path}")
    print(f"   📊 Lignes : {len(df)}")
    print(f"   📁 Colonnes : {len(df.columns)}")
    print(f"\n   Colonnes cibles : impact_reel_pips, direction")
    print(f"   Colonnes prédicteurs : nb_events, score_cumule, score_moyen,")
    print(f"                          surprise_max, surprise_moyenne, surprise_cumule,")
    print(f"                          ratio_concordance, coherence_famille, has_high_importance")


def main():
    """
    Main : Créer dataset complet
    """
    
    print("\n" + "="*70)
    print("SESSION 73 - CRÉATION DATASET COMPLET")
    print("Croiser Mouvements + Événements")
    print("="*70)
    
    # Paramètres
    movements_csv = MOVEMENTS_CSV
    db_path = DB_PATH
    output_csv = fx_impact_app_path / "data" / "dataset_complete_session73.csv"
    
    # Vérifier existence CSV mouvements
    if not Path(movements_csv).exists():
        print(f"\n❌ ERREUR : Fichier mouvements non trouvé : {movements_csv}")
        print(f"   → Exécuter d'abord scanner_movements_session73.py")
        return
    
    # 1. Créer dataset
    df_dataset = create_complete_dataset(
        movements_csv=str(movements_csv),
        db_path=str(db_path),
        time_window_minutes=10
    )
    
    # 2. Analyser statistiques
    analyze_dataset_statistics(df_dataset)
    
    # 3. Export
    export_dataset(df_dataset, str(output_csv))
    
    print(f"\n{'='*70}")
    print(f"✅ DATASET CRÉÉ AVEC SUCCÈS")
    print(f"{'='*70}\n")
    
    print(f"🎯 Prochaine étape :")
    print(f"   Exécuter analyze_correlations_session73.py pour ML/stats")
    
    return df_dataset


if __name__ == "__main__":
    df = main()
