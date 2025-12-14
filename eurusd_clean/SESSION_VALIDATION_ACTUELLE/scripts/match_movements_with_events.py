#!/usr/bin/env python3
"""
Matching des mouvements détectés avec les événements économiques

Objectif : 
1. Charger tous les mouvements détectés indépendamment (all_movements_detected.csv)
2. Pour chaque mouvement, chercher les événements dans une fenêtre temporelle
3. Analyser la corrélation entre mouvements et événements
4. Identifier les mouvements "expliqués" vs "non expliqués" par les événements

Date : 2025-01-XX
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Essayer plusieurs chemins possibles pour la DB
DB_PATHS = [
    Path(__file__).parent.parent.parent / 'data' / 'warehouse.duckdb',
    Path(__file__).parent.parent.parent / 'warehouse.duckdb',
]

DB_PATH = None
for db_path in DB_PATHS:
    if db_path.exists():
        DB_PATH = db_path
        break

if DB_PATH is None:
    raise FileNotFoundError("Aucune base de données trouvée")

TZ_BERN = pytz.timezone('Europe/Zurich')
TZ_UTC = pytz.timezone('UTC')

# Fenêtre de matching : ±60 minutes autour du début du mouvement
MATCHING_WINDOW_MINUTES = 60

# Seuil d'importance minimum pour les événements
MIN_IMPORTANCE = 3  # HIGH importance seulement

def find_events_for_movement(
    conn: duckdb.DuckDBPyConnection,
    movement_start_time: pd.Timestamp,
    window_minutes: int = MATCHING_WINDOW_MINUTES
) -> pd.DataFrame:
    """
    Trouve tous les événements dans une fenêtre autour du début du mouvement
    
    Args:
        conn: Connexion DuckDB
        movement_start_time: Début du mouvement (timezone aware)
        window_minutes: Fenêtre de matching en minutes
    
    Returns:
        DataFrame avec événements trouvés
    """
    
    # Définir fenêtre
    window_start = movement_start_time - timedelta(minutes=window_minutes)
    window_end = movement_start_time + timedelta(minutes=window_minutes)
    
    # Convertir en UTC pour requête DB
    if movement_start_time.tzinfo is None:
        movement_start_time = TZ_BERN.localize(movement_start_time)
    
    window_start_utc = window_start.astimezone(TZ_UTC) if window_start.tzinfo else TZ_BERN.localize(window_start).astimezone(TZ_UTC)
    window_end_utc = window_end.astimezone(TZ_UTC) if window_end.tzinfo else TZ_BERN.localize(window_end).astimezone(TZ_UTC)
    
    # Requête événements
    query = """
    SELECT 
        ts_utc,
        event_key,
        event_title,
        country,
        importance_n,
        actual,
        estimate,
        previous
    FROM events
    WHERE ts_utc >= ?
      AND ts_utc <= ?
      AND importance_n <= ?
    ORDER BY ts_utc
    """
    
    try:
        df_events = conn.execute(
            query, 
            [window_start_utc, window_end_utc, MIN_IMPORTANCE]
        ).df()
        return df_events
    except Exception as e:
        print(f"⚠️ Erreur requête événements : {e}")
        return pd.DataFrame()

def match_all_movements():
    """
    Match tous les mouvements avec les événements
    """
    
    print("=" * 80)
    print("MATCHING MOUVEMENTS AVEC ÉVÉNEMENTS")
    print("=" * 80)
    print()
    
    # 1. Charger mouvements détectés
    print("📊 ÉTAPE 1 : Chargement des mouvements détectés")
    print("-" * 80)
    
    movements_file = Path(__file__).parent.parent / 'outputs' / 'all_movements_detected.csv'
    
    if not movements_file.exists():
        print(f"❌ Fichier non trouvé : {movements_file}")
        print("   Exécutez d'abord scan_all_movements_independent.py")
        return
    
    df_movements = pd.read_csv(movements_file)
    
    # Convertir colonnes datetime
    datetime_cols = ['movement_start_time', 'peak_time', 'movement_end_time']
    for col in datetime_cols:
        if col in df_movements.columns:
            df_movements[col] = pd.to_datetime(df_movements[col], utc=True)
            df_movements[col] = df_movements[col].dt.tz_convert('Europe/Zurich')
    
    print(f"✅ {len(df_movements)} mouvements chargés")
    print(f"   Période : {df_movements['date'].min()} → {df_movements['date'].max()}")
    print()
    
    # 2. Connecter DB
    print("📊 ÉTAPE 2 : Connexion à la base de données")
    print("-" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Compter événements disponibles
    total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"✅ {total_events:,} événements dans la base de données")
    print()
    
    # 3. Matcher événements pour chaque mouvement
    print(f"📊 ÉTAPE 3 : Matching événements (fenêtre ±{MATCHING_WINDOW_MINUTES} min)")
    print("-" * 80)
    
    results = []
    
    for idx, row in df_movements.iterrows():
        if (idx + 1) % 500 == 0:
            print(f"   Progression : {idx + 1}/{len(df_movements)} mouvements analysés...")
        
        movement_start = row['movement_start_time']
        
        # Trouver événements
        df_events = find_events_for_movement(conn, movement_start)
        
        # Compter événements par pays
        countries = df_events['country'].value_counts().to_dict() if not df_events.empty else {}
        
        # Compter événements par importance
        importance_counts = df_events['importance_n'].value_counts().to_dict() if not df_events.empty else {}
        
        # Extraire event_keys
        event_keys = ','.join(df_events['event_key'].tolist()) if not df_events.empty else ""
        
        results.append({
            'date': row['date'],
            'movement_start_time': movement_start,
            'peak_time': row['peak_time'],
            'peak_pips': row['peak_pips'],
            'movement_class': row['movement_class'],
            'direction': row['direction'],
            'confidence': row['confidence'],
            'n_events': len(df_events),
            'n_events_us': countries.get('US', 0),
            'n_events_eu': countries.get('EU', 0),
            'n_events_de': countries.get('DE', 0),
            'n_events_high': importance_counts.get(3, 0),
            'n_events_medium': importance_counts.get(2, 0),
            'n_events_low': importance_counts.get(1, 0),
            'event_keys': event_keys,
            'has_events': len(df_events) > 0
        })
    
    print(f"✅ Matching terminé")
    print()
    
    # 4. Analyser résultats
    print("=" * 80)
    print("RÉSULTATS")
    print("=" * 80)
    print()
    
    df_results = pd.DataFrame(results)
    
    # Statistiques globales
    total_movements = len(df_results)
    movements_with_events = (df_results['has_events'] == True).sum()
    movements_without_events = (df_results['has_events'] == False).sum()
    
    print(f"📊 Statistiques globales :")
    print(f"   Total mouvements                : {total_movements:,}")
    print(f"   Mouvements avec événements     : {movements_with_events:,} ({100.0 * movements_with_events / total_movements:.1f}%)")
    print(f"   Mouvements sans événements     : {movements_without_events:,} ({100.0 * movements_without_events / total_movements:.1f}%)")
    print()
    
    # Statistiques par classe de mouvement
    print(f"📊 Par classe de mouvement :")
    for movement_class in df_results['movement_class'].unique():
        df_class = df_results[df_results['movement_class'] == movement_class]
        with_events = (df_class['has_events'] == True).sum()
        total_class = len(df_class)
        pct = 100.0 * with_events / total_class if total_class > 0 else 0.0
        avg_pips = df_class['peak_pips'].mean()
        print(f"   {movement_class:12s} : {with_events:4d}/{total_class:4d} avec événements ({pct:5.1f}%) | Moyenne : {avg_pips:6.1f} pips")
    print()
    
    # Statistiques par amplitude
    print(f"📊 Par amplitude (pips) :")
    bins = [0, 30, 50, 70, 100, float('inf')]
    labels = ['<30', '30-50', '50-70', '70-100', '>100']
    df_results['amplitude_bin'] = pd.cut(df_results['peak_pips'], bins=bins, labels=labels)
    
    for bin_label in labels:
        df_bin = df_results[df_results['amplitude_bin'] == bin_label]
        if len(df_bin) > 0:
            with_events = (df_bin['has_events'] == True).sum()
            total_bin = len(df_bin)
            pct = 100.0 * with_events / total_bin
            print(f"   {bin_label:8s} pips : {with_events:4d}/{total_bin:4d} avec événements ({pct:5.1f}%)")
    print()
    
    # Top mouvements sans événements
    print(f"🏆 Top 10 mouvements FORTS sans événements :")
    df_strong_no_events = df_results[
        (df_results['has_events'] == False) & 
        (df_results['peak_pips'] >= 50.0)
    ].nlargest(10, 'peak_pips')
    
    for idx, row in df_strong_no_events.iterrows():
        peak_str = row['peak_time'].strftime('%H:%M') if pd.notna(row['peak_time']) else 'N/A'
        print(f"   {row['date']} {peak_str:5s} : {row['peak_pips']:6.1f} pips ({row['movement_class']:12s}, {row['direction']})")
    print()
    
    # Top mouvements avec événements
    print(f"🏆 Top 10 mouvements FORTS avec événements :")
    df_strong_with_events = df_results[
        (df_results['has_events'] == True) & 
        (df_results['peak_pips'] >= 50.0)
    ].nlargest(10, 'peak_pips')
    
    for idx, row in df_strong_with_events.iterrows():
        peak_str = row['peak_time'].strftime('%H:%M') if pd.notna(row['peak_time']) else 'N/A'
        n_events = row['n_events']
        print(f"   {row['date']} {peak_str:5s} : {row['peak_pips']:6.1f} pips ({row['movement_class']:12s}, {row['direction']}) | {n_events} événements")
    print()
    
    # 5. Sauvegarder résultats
    output_file = Path(__file__).parent.parent / 'outputs' / 'movements_matched_with_events.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Préparer pour CSV (convertir datetime en string)
    df_csv = df_results.copy()
    for col in ['movement_start_time', 'peak_time']:
        if col in df_csv.columns:
            df_csv[col] = df_csv[col].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S%z') if pd.notna(x) else None
            )
    
    df_csv = df_csv.drop(columns=['amplitude_bin'])  # Supprimer colonne temporaire
    
    df_csv.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    conn.close()
    
    return df_results

if __name__ == '__main__':
    match_all_movements()


