#!/usr/bin/env python3
"""
Scanner Mouvements Forts - Session 75
AMÉLIORATION : Échantillonnage stratifié par semaine

Objectif : Dataset diversifié 50+ dates différentes (pas 1 seul jour)
Méthode : 1-2 mouvements par semaine (pas top 50 absolus)

Changements vs Session 73 :
- Échantillonnage stratifié (GROUP BY semaine)
- Lookback 60 min → 120 min (momentum prolongé)
- Seuil 100 pips → 80 pips (plus de diversité)
- Limite Top 50 → illimité (échantillon par semaine)

Author: Claude
Date: 24 octobre 2025 - Session 75
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


def scan_strong_movements_stratified(
    db_path: str,
    min_impact_pips: float = 80.0,
    lookback_minutes: int = 120,
    start_date: str = "2024-01-01",
    end_date: str = "2025-10-24",
    top_per_week: int = 2
) -> pd.DataFrame:
    """
    Scanner mouvements forts avec ÉCHANTILLONNAGE STRATIFIÉ
    
    NOUVEAU (Session 75) :
    - Grouper par semaine (année + numéro semaine)
    - Prendre top 1-2 mouvements PAR SEMAINE
    - Garantir diversité dates (50+ dates au lieu de 1 jour)
    
    Args:
        db_path: Chemin warehouse.duckdb
        min_impact_pips: Seuil minimum impact (défaut 80 pips - abaissé vs 100)
        lookback_minutes: Fenêtre calcul impact (défaut 120 min - augmenté vs 60)
        start_date: Date début analyse
        end_date: Date fin analyse
        top_per_week: Nombre mouvements à prendre par semaine (défaut 2)
    
    Returns:
        DataFrame avec colonnes :
        - date, time, datetime, close
        - impact_pips_{lookback}min : Impact calculé
        - price_start, price_peak
        - direction : UP/DOWN
        - year, week : Identifiants période
    """
    
    print(f"\n{'='*70}")
    print(f"SCANNER MOUVEMENTS FORTS - SESSION 75 (STRATIFIÉ)")
    print(f"{'='*70}\n")
    
    print(f"📊 Paramètres (AMÉLIORÉS vs Session 73) :")
    print(f"   - Période : {start_date} → {end_date}")
    print(f"   - Seuil impact : >{min_impact_pips} pips (80 vs 100) ⬇️")
    print(f"   - Fenêtre lookback : {lookback_minutes} min (120 vs 60) ⬆️")
    print(f"   - Échantillonnage : Top {top_per_week} par semaine (NOUVEAU) 🆕")
    print(f"   - Database : {db_path}")
    
    # Connexion DB
    print(f"\n🔌 Connexion database...")
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Étape 1 : Scanner TOUS les mouvements >80 pips
    print(f"\n🔍 Étape 1 : Scanner TOUS mouvements >{min_impact_pips} pips...")
    
    query_all = f"""
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
    ORDER BY datetime ASC
    """
    
    df_all = conn.execute(query_all).fetchdf()
    conn.close()
    
    print(f"   ✅ Mouvements totaux détectés : {len(df_all)}")
    
    if len(df_all) == 0:
        print("\n⚠️  Aucun mouvement détecté avec ces paramètres.")
        return pd.DataFrame()
    
    # Étape 2 : Ajouter colonnes year + week
    print(f"\n📅 Étape 2 : Grouper par semaine...")
    
    df_all['datetime_parsed'] = pd.to_datetime(df_all['datetime'])
    df_all['year'] = df_all['datetime_parsed'].dt.isocalendar().year
    df_all['week'] = df_all['datetime_parsed'].dt.isocalendar().week
    
    # Statistiques groupées
    weeks_unique = df_all.groupby(['year', 'week']).size()
    print(f"   📊 Semaines uniques : {len(weeks_unique)}")
    print(f"   📊 Mouvements par semaine (médiane) : {weeks_unique.median():.1f}")
    
    # Étape 3 : Échantillonner top N par semaine
    print(f"\n🎯 Étape 3 : Échantillonner top {top_per_week} par semaine...")
    
    df_stratified = []
    
    for (year, week), group in df_all.groupby(['year', 'week']):
        # Prendre top N mouvements de cette semaine
        top_week = group.nlargest(top_per_week, 'abs_impact')
        df_stratified.append(top_week)
    
    df_result = pd.concat(df_stratified, ignore_index=True)
    
    # Trier par date
    df_result = df_result.sort_values('datetime').reset_index(drop=True)
    
    print(f"   ✅ Mouvements échantillonnés : {len(df_result)}")
    print(f"   ✅ Dates uniques : {df_result['date'].nunique()}")
    print(f"   ✅ Semaines couvertes : {len(df_result.groupby(['year', 'week']))}")
    
    # Vérification diversité dates
    dates_count = df_result['date'].value_counts()
    max_same_day = dates_count.max()
    
    print(f"\n✅ Vérification diversité :")
    print(f"   Max mouvements même jour : {max_same_day}")
    
    if max_same_day > 5:
        print(f"   ⚠️  ATTENTION : {max_same_day} mouvements sur une même date")
        print(f"   Dates concernées :")
        for date, count in dates_count.head(3).items():
            print(f"      {date} : {count} mouvements")
    else:
        print(f"   ✅ EXCELLENT : Diversité dates respectée (<5 par jour)")
    
    # Statistiques finales
    print(f"\n📈 Top 5 mouvements échantillonnés :")
    for idx, row in df_result.nlargest(5, 'abs_impact').iterrows():
        print(f"   {idx+1}. {row['date']} {row['time']} (Semaine {row['year']}-W{row['week']:02d}) : "
              f"{row['direction']} {abs(row['impact_pips']):.1f} pips")
    
    return df_result


def analyze_movement_characteristics(df: pd.DataFrame) -> dict:
    """
    Analyser caractéristiques statistiques des mouvements détectés
    
    AMÉLIORÉ Session 75 :
    - Analyse diversité dates
    - Distribution par semaine
    - Vérification concentration
    
    Args:
        df: DataFrame résultats scanner
    
    Returns:
        dict avec statistiques descriptives
    """
    
    print(f"\n{'='*70}")
    print(f"ANALYSE STATISTIQUES MOUVEMENTS (SESSION 75)")
    print(f"{'='*70}\n")
    
    stats = {
        'n_movements': len(df),
        'n_dates_unique': df['date'].nunique(),
        'n_weeks': len(df.groupby(['year', 'week'])),
        'impact_mean': df['abs_impact'].mean(),
        'impact_median': df['abs_impact'].median(),
        'impact_std': df['abs_impact'].std(),
        'impact_min': df['abs_impact'].min(),
        'impact_max': df['abs_impact'].max(),
        'direction_up_pct': (df['direction'] == 'UP').sum() / len(df) * 100,
        'direction_down_pct': (df['direction'] == 'DOWN').sum() / len(df) * 100
    }
    
    print(f"📊 Statistiques Dataset :")
    print(f"   Mouvements totaux : {stats['n_movements']}")
    print(f"   Dates uniques : {stats['n_dates_unique']} 🆕")
    print(f"   Semaines couvertes : {stats['n_weeks']} 🆕")
    print(f"   Ratio mouvements/dates : {stats['n_movements']/stats['n_dates_unique']:.2f}")
    
    print(f"\n📊 Statistiques Impact :")
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
    
    print(f"\n📅 Distribution Temporelle (Top 5 mois) :")
    for month, count in movements_per_month.nlargest(5).items():
        print(f"      {month} : {count} mouvements")
    
    # Distribution par heure
    df['hour'] = pd.to_datetime(df['datetime']).dt.hour
    movements_per_hour = df.groupby('hour').size()
    
    print(f"\n⏰ Distribution Horaire (Top 5) :")
    for hour, count in movements_per_hour.nlargest(5).items():
        print(f"      {hour:02d}:00 UTC : {count} mouvements")
    
    # Vérifier concentration dates
    dates_count = df['date'].value_counts()
    concentration_pct = (dates_count > 3).sum() / len(dates_count) * 100
    
    print(f"\n🎯 Analyse Concentration (NOUVEAU) :")
    print(f"   Dates avec >3 mouvements : {(dates_count > 3).sum()} ({concentration_pct:.1f}%)")
    
    if concentration_pct > 20:
        print(f"   ⚠️  ATTENTION : Concentration élevée (>{concentration_pct:.1f}%)")
    else:
        print(f"   ✅ Excellente diversité (concentration <20%)")
    
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
        'impact_pips', 'direction', 'abs_impact',
        'year', 'week'
    ]].copy()
    
    # Export CSV
    df_export.to_csv(output_path, index=False)
    
    print(f"   ✅ Fichier créé : {output_path}")
    print(f"   📊 Lignes : {len(df_export)}")
    print(f"   📁 Colonnes : {', '.join(df_export.columns)}")


def main():
    """
    Main : Scanner mouvements stratifiés + analyse + export
    """
    
    print("\n" + "="*70)
    print("SESSION 75 - SCANNER MOUVEMENTS STRATIFIÉ")
    print("Échantillonnage par Semaine (AMÉLIORATION vs Session 73)")
    print("="*70)
    
    # Paramètres
    db_path = DB_PATH
    output_csv = fx_impact_app_path / "data" / "movements_strong_session75_stratified.csv"
    
    # 1. Scanner mouvements STRATIFIÉS
    df = scan_strong_movements_stratified(
        db_path=str(db_path),
        min_impact_pips=80.0,      # Abaissé 100→80 pour diversité
        lookback_minutes=120,       # Augmenté 60→120 pour momentum prolongé
        start_date="2024-01-01",
        end_date="2025-10-24",
        top_per_week=2              # NOUVEAU : 2 mouvements par semaine
    )
    
    if len(df) == 0:
        print("\n⚠️  Aucun mouvement détecté avec ces paramètres.")
        return
    
    # 2. Analyser caractéristiques
    stats = analyze_movement_characteristics(df)
    
    # 3. Export résultats
    export_results(df, str(output_csv))
    
    print(f"\n{'='*70}")
    print(f"✅ SCAN STRATIFIÉ COMPLÉTÉ AVEC SUCCÈS")
    print(f"{'='*70}\n")
    
    print(f"📊 Résumé SESSION 75 :")
    print(f"   Mouvements échantillonnés : {len(df)}")
    print(f"   Dates uniques : {stats['n_dates_unique']} (vs 1 en Session 73) 🎯")
    print(f"   Semaines couvertes : {stats['n_weeks']}")
    print(f"   Impact moyen : {stats['impact_mean']:.1f} pips")
    print(f"   Fichier output : {output_csv}")
    
    print(f"\n🎯 Amélioration vs Session 73 :")
    print(f"   ✅ Échantillonnage stratifié (pas top 50 absolus)")
    print(f"   ✅ Lookback 120 min (vs 60)")
    print(f"   ✅ Seuil 80 pips (vs 100)")
    print(f"   ✅ Diversité dates garantie")
    
    print(f"\n🚀 Prochaine étape :")
    print(f"   Exécuter create_dataset_session73_FIXED.py avec nouveau CSV")
    
    return df, stats


if __name__ == "__main__":
    df, stats = main()
