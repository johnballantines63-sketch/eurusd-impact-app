#!/usr/bin/env python3
"""
Scan de TOUS les mouvements indépendamment des événements

Objectif : Détecter TOUS les mouvements forts/moyens/faibles dans l'historique
sans aucune référence aux événements pour éviter tout biais.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime
from typing import List, Dict

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.movement_detection_robust import (
    calculate_historical_thresholds,
    detect_all_movements
)

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

# Vérifier quelle table de prix existe
def find_price_table(db_path: Path) -> str:
    """Trouve la table de prix disponible"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Essayer différentes tables (priorité aux tables Finnhub)
    tables_to_try = [
        'prices_finnhub_m1',  # Priorité 1 : Finnhub M1
        'prices_finnhub_h1',  # Priorité 2 : Finnhub H1
        'prices_bern',        # Priorité 3 : Bern (Dukascopy)
        'prices_1m',         # Priorité 4 : Dukascopy M1
        'prices_h1'          # Priorité 5 : Dukascopy H1
    ]
    
    for table in tables_to_try:
        try:
            result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            if result and result[0] > 0:
                conn.close()
                return table
        except:
            continue
    
    conn.close()
    return None

def scan_all_movements(
    db_path: Path,
    start_date: str = '2024-01-01',
    end_date: str = '2025-12-31',
    min_movement_pips: float = 10.0
) -> List[Dict]:
    """
    Scanne TOUTES les dates et détecte TOUS les mouvements
    
    ⚠️ IMPORTANT : Aucune référence aux événements
    """
    
    table_name = find_price_table(db_path)
    
    if table_name is None:
        print("❌ Aucune table de prix trouvée")
        return []
    
    print(f"✅ Utilisation de la table : {table_name}")
    print()
    
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Scanner TOUTES les dates disponibles
    query_dates = f"""
    SELECT DISTINCT DATE(datetime) as date_hist
    FROM {table_name}
    WHERE DATE(datetime) >= '{start_date}'
      AND DATE(datetime) <= '{end_date}'
    ORDER BY date_hist ASC
    """
    
    df_dates = conn.execute(query_dates).df()
    
    print(f"📊 Analyse de {len(df_dates)} dates...")
    print()
    
    all_movements_detected = []
    
    # Calculer seuils historiques d'abord
    print("1️⃣ Calcul des seuils statistiques historiques...")
    thresholds = calculate_historical_thresholds(DB_PATH, years=3, table_name=table_name)
    print()
    
    # Scanner chaque date
    print("2️⃣ Détection des mouvements sur chaque date...")
    
    for idx, row in df_dates.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"   Progression : {idx + 1}/{len(df_dates)} dates analysées...")
        
        date_str = row['date_hist'].strftime('%Y-%m-%d')
        
        # Charger prix pour la journée
        query_prices = f"""
        SELECT datetime, open, high, low, close
        FROM {table_name}
        WHERE DATE(datetime) = '{date_str}'
        ORDER BY datetime ASC
        """
        
        df_prices = conn.execute(query_prices).df()
        
        if df_prices.empty or len(df_prices) < 60:
            continue
        
        df_prices['datetime'] = pd.to_datetime(df_prices['datetime'])
        df_prices = df_prices.set_index('datetime')
        
        # ⚠️ Détecter mouvements SANS référence à événements
        # Utiliser le début de journée comme référence
        day_start = df_prices.index[0]
        
        # Détecter TOUS les mouvements dans la journée
        movements = detect_all_movements(
            df_prices,
            day_start,  # Utiliser début de journée comme référence
            baseline_time=day_start,
            thresholds=thresholds,
            window_hours=24.0  # Scanner toute la journée
        )
        
        # Enregistrer les mouvements détectés
        for mov in movements:
            if mov['peak_pips'] >= min_movement_pips:
                all_movements_detected.append({
                    'date': date_str,
                    'movement_start_time': mov['movement_start_time'],
                    'movement_start_pips': mov['movement_start_pips'],
                    'peak_time': mov['peak_time'],
                    'peak_pips': mov['peak_pips'],
                    'movement_end_time': mov['movement_end_time'],
                    'movement_class': mov['movement_class'],
                    'direction': mov['direction'],
                    'confidence': mov['confidence']
                })
    
    conn.close()
    
    return all_movements_detected

def main():
    """Fonction principale"""
    
    print("=" * 80)
    print("SCAN DE TOUS LES MOUVEMENTS (INDÉPENDANT DES ÉVÉNEMENTS)")
    print("=" * 80)
    print()
    
    # Scanner mouvements
    movements = scan_all_movements(
        DB_PATH,
        start_date='2024-01-01',
        end_date='2025-12-31',
        min_movement_pips=10.0
    )
    
    print()
    print("=" * 80)
    print("RÉSULTATS")
    print("=" * 80)
    print()
    
    if not movements:
        print("❌ Aucun mouvement détecté")
        return
    
    df_movements = pd.DataFrame(movements)
    
    print(f"✅ {len(df_movements)} mouvements détectés (≥10 pips)")
    print()
    
    # Statistiques par classe
    print("📊 Classification des mouvements :")
    class_counts = df_movements['movement_class'].value_counts()
    for class_name, count in class_counts.items():
        pct = (count / len(df_movements)) * 100
        print(f"   - {class_name:12s} : {count:4d} ({pct:5.1f}%)")
    print()
    
    # Statistiques par amplitude
    print("📈 Statistiques d'amplitude :")
    print(f"   - Minimum  : {df_movements['peak_pips'].min():.1f} pips")
    print(f"   - Maximum  : {df_movements['peak_pips'].max():.1f} pips")
    print(f"   - Médiane  : {df_movements['peak_pips'].median():.1f} pips")
    print(f"   - Moyenne  : {df_movements['peak_pips'].mean():.1f} pips")
    print(f"   - P25      : {df_movements['peak_pips'].quantile(0.25):.1f} pips")
    print(f"   - P75      : {df_movements['peak_pips'].quantile(0.75):.1f} pips")
    print()
    
    # Sauvegarder résultats
    output_file = Path(__file__).parent.parent / 'outputs' / 'all_movements_detected.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df_movements.to_csv(output_file, index=False)
    print(f"💾 Résultats sauvegardés : {output_file}")
    print()
    
    # Afficher top 20 mouvements
    print("🏆 Top 20 mouvements les plus forts :")
    top_movements = df_movements.nlargest(20, 'peak_pips')
    for idx, row in top_movements.iterrows():
        peak_str = row['peak_time'].strftime('%H:%M') if pd.notna(row['peak_time']) else 'N/A'
        print(f"   {row['date']} {peak_str:5s} : {row['peak_pips']:6.1f} pips ({row['movement_class']:12s}, {row['direction']})")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()

