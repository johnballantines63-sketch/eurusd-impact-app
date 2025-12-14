"""
ÉTAPE 2.0 - MATCHER ÉVÉNEMENTS DANS FENÊTRE ±60 MIN
Session 137 - Workflow LOO-CV DoubleWave_Overlap

Mission :
1. Pour chaque mouvement (396) : fenêtre ±60 min
2. Trouver TOUS événements dans fenêtre (pas filtrage score ici)
3. Identifier event_key uniques matchés
4. Préparer analyse scores (étape suivante)

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
import pandas as pd
from pathlib import Path
from datetime import timedelta

# =============================================================================
# CHEMINS
# =============================================================================

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"
INPUT_CSV = Path(__file__).parent.parent / "session136" / "step1_price_movements.csv"
OUTPUT_CSV = Path(__file__).parent / "step2_0_matched_events.csv"

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def match_events_in_windows():
    """
    Matcher TOUS événements dans fenêtre ±60 min pour chaque mouvement
    
    PAS de filtrage par score ici - juste identifier quels événements
    correspondent aux mouvements forts détectés
    """
    
    print("=" * 80)
    print("ÉTAPE 2.0 - MATCHING ÉVÉNEMENTS DANS FENÊTRE ±60 MIN")
    print("=" * 80)
    
    # 1. Charger mouvements
    print("\n📊 ÉTAPE 1 : Chargement mouvements")
    print("-" * 80)
    
    df_movements = pd.read_csv(INPUT_CSV)
    
    # Forcer UTC puis convertir Europe/Zurich (évite mixed timezone)
    df_movements['datetime'] = pd.to_datetime(df_movements['datetime'], utc=True)
    df_movements['datetime'] = df_movements['datetime'].dt.tz_convert('Europe/Zurich')
    
    print(f"   ✅ {len(df_movements)} mouvements chargés")
    print(f"   Période : {df_movements['datetime'].min()} → {df_movements['datetime'].max()}")
    
    # 2. Connecter DB
    print("\n📊 ÉTAPE 2 : Connexion database")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Compter événements disponibles
    total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"   ✅ {total_events:,} événements dans DB")
    
    # 3. Matcher événements pour chaque mouvement
    print("\n📊 ÉTAPE 3 : Matching événements (396 mouvements)")
    print("-" * 80)
    
    results = []
    event_keys_matched = set()
    
    for idx, row in df_movements.iterrows():
        movement_time = row['datetime']
        
        # Fenêtre ±60 min
        fenetre_start = movement_time - timedelta(minutes=60)
        fenetre_end = movement_time + timedelta(minutes=60)
        
        # Convertir en UTC pour requête
        fenetre_start_utc = fenetre_start.tz_convert('UTC')
        fenetre_end_utc = fenetre_end.tz_convert('UTC')
        
        # Requête : TOUS événements dans fenêtre
        query = """
        SELECT 
            event_key,
            event_title,
            country,
            ts_utc,
            actual,
            forecast,
            previous
        FROM events
        WHERE ts_utc >= ?
          AND ts_utc <= ?
        ORDER BY ts_utc
        """
        
        events_matched = conn.execute(query, [fenetre_start_utc, fenetre_end_utc]).fetchall()
        
        # Stocker résultats
        num_events = len(events_matched)
        event_keys = ','.join([e[0] for e in events_matched]) if num_events > 0 else ""
        
        # Collecter event_keys uniques
        for event in events_matched:
            event_keys_matched.add(event[0])
        
        results.append({
            'movement_id': idx,
            'movement_datetime': movement_time,
            'impact_pips': row['impact_pips'],
            'direction': row['direction'],
            'num_events': num_events,
            'event_keys': event_keys
        })
        
        # Progress
        if (idx + 1) % 50 == 0:
            print(f"   Progression : {idx + 1}/396 mouvements ({100.0 * (idx + 1) / 396:.1f}%)")
    
    # 4. Statistiques matching
    print("\n📊 ÉTAPE 4 : Statistiques matching")
    print("-" * 80)
    
    df_results = pd.DataFrame(results)
    
    movements_with_events = (df_results['num_events'] > 0).sum()
    movements_without_events = (df_results['num_events'] == 0).sum()
    
    print(f"   Total mouvements                  : {len(df_results)}")
    print(f"   Mouvements avec ≥1 événement      : {movements_with_events} ({100.0 * movements_with_events / len(df_results):.1f}%)")
    print(f"   Mouvements sans événement         : {movements_without_events} ({100.0 * movements_without_events / len(df_results):.1f}%)")
    print(f"   \n   event_key distincts matchés       : {len(event_keys_matched)}")
    
    # Distribution
    print("\n   Distribution événements par mouvement :")
    distrib = df_results['num_events'].value_counts().sort_index()
    for n_events, count in distrib.items():
        if n_events <= 10:
            print(f"      {n_events:2d} événements : {count:3d} mouvements")
    if (df_results['num_events'] > 10).sum() > 0:
        print(f"      10+ événements : {(df_results['num_events'] > 10).sum():3d} mouvements")
    
    # 5. Sauvegarder
    print("\n📊 ÉTAPE 5 : Sauvegarde résultats")
    print("-" * 80)
    
    df_results.to_csv(OUTPUT_CSV, index=False)
    print(f"   ✅ Fichier créé : {OUTPUT_CSV}")
    
    # 6. Sauvegarder liste event_keys uniques
    event_keys_file = Path(__file__).parent / "step2_0_unique_event_keys.txt"
    with open(event_keys_file, 'w') as f:
        for key in sorted(event_keys_matched):
            f.write(f"{key}\n")
    
    print(f"   ✅ Liste event_keys : {event_keys_file}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ÉTAPE 2.0 COMPLÉTÉE")
    print("=" * 80)
    print(f"\n📋 PROCHAINE ÉTAPE : Vérifier scores pour {len(event_keys_matched)} event_keys matchés")
    
    return len(event_keys_matched), movements_with_events

if __name__ == '__main__':
    unique_keys, movements_ok = match_events_in_windows()
