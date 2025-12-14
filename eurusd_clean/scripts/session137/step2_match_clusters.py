"""
ÉTAPE 2 - MATCHER CLUSTERS ÉVÉNEMENTS HIGH DANS FENÊTRE ±60 MIN
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Workflow exact (doublewave_loo_validation.mermaid ÉTAPE 2):
┌─────────────────────────────────────────────────┐
│ ÉTAPE 2: Identifier cluster events              │
│          à cette date/heure?                    │
│                                                 │
│ Pour CHAQUE mouvement:                          │
│   1. Définir fenêtre ±60 min                    │
│   2. Chercher events HIGH (importance_n = 3)    │
│   3. Si events trouvés:                         │
│      - Compter: num_events                      │
│      - Calculer: total_score (somme scores)     │
│      - Stocker: event_keys (liste clés)         │
│   4. Si aucun event:                            │
│      - num_events=0, total_score=0, event_keys=""│
│                                                 │
│ Output: CSV enrichi avec 3 colonnes:            │
│         - num_events                            │
│         - total_score                           │
│         - event_keys                            │
└─────────────────────────────────────────────────┘

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# =============================================================================
# PARAMÈTRES
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
STEP1_CSV = Path(__file__).parent.parent / "session136" / "step1_price_movements.csv"
OUTPUT_CSV = Path(__file__).parent / "step2_movements_with_clusters.csv"

WINDOW_MINUTES = 60  # Fenêtre matching ±60 min
TIMEZONE_BERN = 'Europe/Zurich'
TIMEZONE_UTC = 'UTC'

# Table scores empiriques (optionnel - si disponible)
SCORES_TABLE = "event_families"  # Ou None si pas de scores

# =============================================================================
# 1. CHARGER MOUVEMENTS ÉTAPE 1
# =============================================================================

def load_movements():
    """Charger mouvements depuis step1_price_movements.csv"""
    
    print("="*80)
    print("ÉTAPE 2.1 : CHARGER MOUVEMENTS")
    print("="*80)
    
    df = pd.read_csv(STEP1_CSV)
    
    print(f"\nMouvements chargés : {len(df)}")
    print(f"Colonnes : {list(df.columns)}")
    print(f"\nPremières lignes:")
    print(df.head(3).to_string())
    
    return df

# =============================================================================
# 2. MATCHER ÉVÉNEMENTS POUR 1 MOUVEMENT
# =============================================================================

def match_events_for_movement(conn, movement_datetime, window_minutes=60):
    """
    Matcher événements HIGH dans fenêtre ±window_minutes autour mouvement
    
    Args:
        conn: Connexion DuckDB
        movement_datetime: Datetime mouvement (timezone aware)
        window_minutes: Fenêtre matching (default 60 min)
    
    Returns:
        dict: {
            'num_events': int,
            'total_score': float,
            'event_keys': str (comma-separated)
        }
    """
    
    # Définir fenêtre ±60 min
    window_start = movement_datetime - timedelta(minutes=window_minutes)
    window_end = movement_datetime + timedelta(minutes=window_minutes)
    
    # Convertir en UTC pour requête DB
    tz_utc = pytz.timezone(TIMEZONE_UTC)
    window_start_utc = window_start.astimezone(tz_utc)
    window_end_utc = window_end.astimezone(tz_utc)
    
    # Requête matching événements HIGH
    query = """
    SELECT 
        ts_utc,
        country,
        event_title,
        event_key,
        importance_n
    FROM events
    WHERE importance_n = 3
      AND ts_utc >= ?
      AND ts_utc <= ?
    ORDER BY ts_utc
    """
    
    df_events = conn.execute(query, [window_start_utc, window_end_utc]).df()
    
    # Si aucun événement
    if len(df_events) == 0:
        return {
            'num_events': 0,
            'total_score': 0.0,
            'event_keys': ""
        }
    
    # Compter événements
    num_events = len(df_events)
    
    # Extraire event_keys
    event_keys = ','.join(df_events['event_key'].tolist())
    
    # Calculer total_score (si table scores disponible)
    # TODO: Implémenter lookup scores empiriques depuis event_families
    # Pour l'instant: utiliser 0.0 (neutre)
    total_score = 0.0
    
    return {
        'num_events': num_events,
        'total_score': total_score,
        'event_keys': event_keys
    }

# =============================================================================
# 3. ENRICHIR TOUS MOUVEMENTS
# =============================================================================

def enrich_movements_with_clusters(df_movements):
    """
    Enrichir DataFrame mouvements avec clusters événements
    
    Pour chaque mouvement:
    1. Définir fenêtre ±60 min
    2. Matcher événements HIGH
    3. Ajouter colonnes: num_events, total_score, event_keys
    
    Args:
        df_movements: DataFrame mouvements depuis ÉTAPE 1
    
    Returns:
        DataFrame: Mouvements enrichis + 3 colonnes
    """
    
    print("\n" + "="*80)
    print("ÉTAPE 2.2 : ENRICHIR MOUVEMENTS AVEC CLUSTERS")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Initialiser colonnes résultats
    num_events_list = []
    total_score_list = []
    event_keys_list = []
    
    # Définir timezone Bern
    tz_bern = pytz.timezone(TIMEZONE_BERN)
    
    # Boucle sur chaque mouvement
    print(f"\nTraitement {len(df_movements)} mouvements...")
    
    for idx, row in df_movements.iterrows():
        
        # Afficher progression tous les 50 mouvements
        if (idx + 1) % 50 == 0:
            print(f"   Traité {idx+1}/{len(df_movements)} mouvements...")
        
        # Convertir datetime mouvement en timezone aware
        movement_dt = pd.to_datetime(row['datetime'])
        
        # Si pas de timezone, supposer déjà Bern
        if movement_dt.tz is None:
            movement_dt = tz_bern.localize(movement_dt)
        
        # Matcher événements
        result = match_events_for_movement(conn, movement_dt, WINDOW_MINUTES)
        
        # Stocker résultats
        num_events_list.append(result['num_events'])
        total_score_list.append(result['total_score'])
        event_keys_list.append(result['event_keys'])
    
    # Ajouter colonnes au DataFrame
    df_enriched = df_movements.copy()
    df_enriched['num_events'] = num_events_list
    df_enriched['total_score'] = total_score_list
    df_enriched['event_keys'] = event_keys_list
    
    conn.close()
    
    print(f"\n✅ Enrichissement complété : {len(df_enriched)} mouvements")
    
    return df_enriched

# =============================================================================
# 4. ANALYSER STATISTIQUES MATCHING
# =============================================================================

def analyze_matching_statistics(df_enriched):
    """Analyser statistiques matching événements"""
    
    print("\n" + "="*80)
    print("ÉTAPE 2.3 : STATISTIQUES MATCHING")
    print("="*80)
    
    # Total mouvements
    total_movements = len(df_enriched)
    
    # Mouvements avec événements
    movements_with_events = (df_enriched['num_events'] > 0).sum()
    movements_without_events = (df_enriched['num_events'] == 0).sum()
    
    print(f"\n1. Distribution matching:")
    print("-" * 80)
    print(f"   Total mouvements       : {total_movements}")
    print(f"   Avec événements (≥1)   : {movements_with_events} ({movements_with_events/total_movements*100:.1f}%)")
    print(f"   Sans événements (0)    : {movements_without_events} ({movements_without_events/total_movements*100:.1f}%)")
    
    # Distribution num_events
    print(f"\n2. Distribution nombre événements par mouvement:")
    print("-" * 80)
    print(df_enriched['num_events'].value_counts().sort_index().to_string())
    
    # Statistiques num_events
    print(f"\n3. Statistiques num_events:")
    print("-" * 80)
    print(f"   Moyenne : {df_enriched['num_events'].mean():.2f}")
    print(f"   Médiane : {df_enriched['num_events'].median():.0f}")
    print(f"   Min     : {df_enriched['num_events'].min()}")
    print(f"   Max     : {df_enriched['num_events'].max()}")
    
    # Statistiques total_score (si scores disponibles)
    if df_enriched['total_score'].sum() > 0:
        print(f"\n4. Statistiques total_score:")
        print("-" * 80)
        print(f"   Moyenne : {df_enriched['total_score'].mean():.2f}")
        print(f"   Médiane : {df_enriched['total_score'].median():.2f}")
        print(f"   Min     : {df_enriched['total_score'].min():.2f}")
        print(f"   Max     : {df_enriched['total_score'].max():.2f}")
    
    # Critère succès
    print(f"\n5. Critère succès Session 137:")
    print("-" * 80)
    print(f"   Objectif minimum : 150 mouvements avec événements (40%)")
    print(f"   Objectif optimal : 200 mouvements avec événements (50%)")
    print(f"   Atteint          : {movements_with_events} mouvements ({movements_with_events/total_movements*100:.1f}%)")
    
    if movements_with_events >= 200:
        print(f"   ✅ OBJECTIF OPTIMAL ATTEINT")
    elif movements_with_events >= 150:
        print(f"   ✅ OBJECTIF MINIMUM ATTEINT")
    else:
        print(f"   ⚠️ OBJECTIF NON ATTEINT (besoin {150 - movements_with_events} de plus)")

# =============================================================================
# 5. SAUVEGARDER RÉSULTATS
# =============================================================================

def save_enriched_movements(df_enriched):
    """Sauvegarder mouvements enrichis en CSV"""
    
    print("\n" + "="*80)
    print("ÉTAPE 2.4 : SAUVEGARDER RÉSULTATS")
    print("="*80)
    
    # Sauvegarder CSV
    df_enriched.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ Fichier sauvegardé : {OUTPUT_CSV}")
    print(f"   Lignes   : {len(df_enriched)}")
    print(f"   Colonnes : {len(df_enriched.columns)}")
    print(f"\nColonnes ajoutées:")
    print(f"   - num_events   : int (0+)")
    print(f"   - total_score  : float (0.0+)")
    print(f"   - event_keys   : str (comma-separated)")

# =============================================================================
# MAIN - WORKFLOW ÉTAPE 2
# =============================================================================

def main():
    """Workflow ÉTAPE 2 complet"""
    
    print("\n" + "="*80)
    print("SESSION 137 - ÉTAPE 2 : MATCH CLUSTERS ÉVÉNEMENTS HIGH")
    print("="*80)
    print(f"\nWorkflow:")
    print(f"  INPUT  : {STEP1_CSV}")
    print(f"  OUTPUT : {OUTPUT_CSV}")
    print(f"  Fenêtre: ±{WINDOW_MINUTES} min (120 min total)")
    print(f"  Filtre : importance_n = 3 (HIGH)")
    
    # ÉTAPE 2.1 : Charger mouvements
    df_movements = load_movements()
    
    # ÉTAPE 2.2 : Enrichir avec clusters
    df_enriched = enrich_movements_with_clusters(df_movements)
    
    # ÉTAPE 2.3 : Analyser statistiques
    analyze_matching_statistics(df_enriched)
    
    # ÉTAPE 2.4 : Sauvegarder
    save_enriched_movements(df_enriched)
    
    print("\n" + "="*80)
    print("✅ ÉTAPE 2 COMPLÉTÉE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
