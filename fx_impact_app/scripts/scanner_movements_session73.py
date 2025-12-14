#!/usr/bin/env python3
"""
Scanner Mouvements Forts - Session 73
Méthodologie inversée data-driven

Objectif : Identifier mouvements EUR/USD >100 pips depuis prices_1m (Dukascopy)
Approche : Partir de la RÉALITÉ observée plutôt que des prédictions

Author: Claude
Date: 24 octobre 2025
"""

import sys
from pathlib import Path

# Ajouter fx_impact_app au path
fx_impact_app_path = Path(__file__).parent.parent
sys.path.insert(0, str(fx_impact_app_path))

import duckdb
from datetime import datetime, timedelta
import pandas as pd

# Path database
DB_PATH = fx_impact_app_path / "data" / "warehouse.duckdb"


def scan_strong_movements(
    db_path: str,
    min_impact_pips: float = 100.0,
    lookback_minutes: int = 60,
    start_date: str = "2024-01-01",
    end_date: str = "2025-10-24",
    limit: int = 50
) -> pd.DataFrame:
    """
    Scanner mouvements forts EUR/USD depuis prices_1m
    
    Logique :
    - Pour chaque minute, calculer impact sur les N minutes précédentes
    - Identifier pics >100 pips
    - Extraire caractéristiques du mouvement
    
    Args:
        db_path: Chemin warehouse.duckdb
        min_impact_pips: Seuil minimum impact (défaut 100 pips)
        lookback_minutes: Fenêtre calcul impact (défaut 60 min)
        start_date: Date début analyse
        end_date: Date fin analyse
        limit: Nombre max mouvements retournés
    
    Returns:
        DataFrame avec colonnes :
        - date, time, datetime, close
        - impact_pips_{lookback}min : Impact calculé
        - price_start, price_peak
        - direction : UP/DOWN
    """
    
    print(f"\n{'='*70}")
    print(f"SCANNER MOUVEMENTS FORTS - SESSION 73")
    print(f"{'='*70}\n")
    
    print(f"📊 Paramètres :")
    print(f"   - Période : {start_date} → {end_date}")
    print(f"   - Seuil impact : >{min_impact_pips} pips")
    print(f"   - Fenêtre lookback : {lookback_minutes} min")
    print(f"   - Limite résultats : Top {limit}")
    print(f"   - Database : {db_path}")
    
    # Connexion DB
    print(f"\n🔌 Connexion database...")
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Query : Calculer impact sur fenêtre glissante
    query = f"""
    WITH price_changes AS (
        SELECT 
            DATE(datetime) as date,
            strftime(datetime, '%H:%M') as time,
            datetime,
            close,
            LAG(close, {lookback_minutes}) OVER (ORDER BY datetime) as price_start,
            (close - LAG(close, {lookback_minutes}) OVER (ORDER BY datetime)) * 10000 as impact_pips,
            CASE 
                WHEN (close - LAG(close, {lookback_minutes}) OVER (ORDER BY datetime)) > 0 
                THEN 'UP'
                ELSE 'DOWN'
            END as direction
        FROM prices_1m
        WHERE datetime >= '{start_date}' AND datetime <= '{end_date}'
    )
    SELECT 
        date,
        time,
        datetime,
        close as price_peak,
        price_start,
        impact_pips,
        direction,
        ABS(impact_pips) as abs_impact
    FROM price_changes
    WHERE ABS(impact_pips) >= {min_impact_pips}
    ORDER BY abs_impact DESC
    LIMIT {limit}
    """
    
    print(f"\n🔍 Exécution query SQL...")
    print(f"   Query : Scan prices_1m avec fenêtre {lookback_minutes} min")
    
    df = conn.execute(query).fetchdf()
    conn.close()
    
    print(f"\n✅ Scan complété !")
    print(f"   Mouvements détectés : {len(df)}")
    
    if len(df) > 0:
        print(f"\n📈 Top 5 mouvements les plus forts :")
        for idx, row in df.head(5).iterrows():
            print(f"   {idx+1}. {row['date']} {row['time']} : "
                  f"{row['direction']} {abs(row['impact_pips']):.1f} pips "
                  f"({row['price_start']:.5f} → {row['price_peak']:.5f})")
    
    return df


def analyze_movement_characteristics(df: pd.DataFrame) -> dict:
    """
    Analyser caractéristiques statistiques des mouvements détectés
    
    Args:
        df: DataFrame résultats scanner
    
    Returns:
        dict avec statistiques descriptives
    """
    
    print(f"\n{'='*70}")
    print(f"ANALYSE STATISTIQUES MOUVEMENTS")
    print(f"{'='*70}\n")
    
    stats = {
        'n_movements': len(df),
        'impact_mean': df['abs_impact'].mean(),
        'impact_median': df['abs_impact'].median(),
        'impact_std': df['abs_impact'].std(),
        'impact_min': df['abs_impact'].min(),
        'impact_max': df['abs_impact'].max(),
        'direction_up_pct': (df['direction'] == 'UP').sum() / len(df) * 100,
        'direction_down_pct': (df['direction'] == 'DOWN').sum() / len(df) * 100
    }
    
    print(f"📊 Statistiques Impact :")
    print(f"   Moyenne : {stats['impact_mean']:.1f} pips")
    print(f"   Médiane : {stats['impact_median']:.1f} pips")
    print(f"   Écart-type : {stats['impact_std']:.1f} pips")
    print(f"   Min : {stats['impact_min']:.1f} pips")
    print(f"   Max : {stats['impact_max']:.1f} pips")
    
    print(f"\n🎯 Distribution Direction :")
    print(f"   UP : {stats['direction_up_pct']:.1f}%")
    print(f"   DOWN : {stats['direction_down_pct']:.1f}%")
    
    # Distribution par mois
    df['month'] = pd.to_datetime(df['datetime']).dt.to_period('M')
    movements_per_month = df.groupby('month').size()
    
    print(f"\n📅 Distribution Temporelle :")
    print(f"   Mois avec plus de mouvements :")
    for month, count in movements_per_month.nlargest(5).items():
        print(f"      {month} : {count} mouvements")
    
    # Distribution par heure
    df['hour'] = pd.to_datetime(df['datetime']).dt.hour
    movements_per_hour = df.groupby('hour').size()
    
    print(f"\n⏰ Distribution Horaire (Top 5) :")
    for hour, count in movements_per_hour.nlargest(5).items():
        print(f"      {hour:02d}:00 UTC : {count} mouvements")
    
    return stats


def export_results(df: pd.DataFrame, output_path: str):
    """
    Exporter résultats vers CSV
    
    Args:
        df: DataFrame résultats
        output_path: Chemin fichier output
    """
    
    print(f"\n💾 Export résultats...")
    
    # Préparer colonnes pour export
    df_export = df[[
        'date', 'time', 'datetime', 
        'price_start', 'price_peak', 
        'impact_pips', 'direction', 'abs_impact'
    ]].copy()
    
    # Export CSV
    df_export.to_csv(output_path, index=False)
    
    print(f"   ✅ Fichier créé : {output_path}")
    print(f"   📊 Lignes : {len(df_export)}")
    print(f"   📁 Colonnes : {', '.join(df_export.columns)}")


def main():
    """
    Main : Scanner mouvements forts + analyse + export
    """
    
    print("\n" + "="*70)
    print("SESSION 73 - SCANNER MOUVEMENTS FORTS")
    print("Méthodologie Inversée Data-Driven")
    print("="*70)
    
    # Paramètres
    db_path = DB_PATH
    output_csv = fx_impact_app_path / "data" / "movements_strong_session73.csv"
    
    # 1. Scanner mouvements
    df = scan_strong_movements(
        db_path=str(db_path),
        min_impact_pips=100.0,
        lookback_minutes=60,
        start_date="2024-01-01",
        end_date="2025-10-24",
        limit=50
    )
    
    if len(df) == 0:
        print("\n⚠️  Aucun mouvement détecté avec ces paramètres.")
        return
    
    # 2. Analyser caractéristiques
    stats = analyze_movement_characteristics(df)
    
    # 3. Export résultats
    export_results(df, str(output_csv))
    
    print(f"\n{'='*70}")
    print(f"✅ SCAN COMPLÉTÉ AVEC SUCCÈS")
    print(f"{'='*70}\n")
    
    print(f"📊 Résumé :")
    print(f"   Mouvements détectés : {len(df)}")
    print(f"   Impact moyen : {stats['impact_mean']:.1f} pips")
    print(f"   Impact max : {stats['impact_max']:.1f} pips")
    print(f"   Fichier output : {output_csv}")
    
    print(f"\n🎯 Prochaine étape :")
    print(f"   Exécuter create_dataset_session73.py pour croiser avec events DB")
    
    return df


if __name__ == "__main__":
    df = main()
