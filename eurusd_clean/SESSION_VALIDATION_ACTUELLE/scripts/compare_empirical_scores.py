"""
Comparaison des scores empiriques calculés vs scores actuels dans la DB

Référence : REF-004
Date : 2025-12-06
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from config import DB_PATH
from SESSION_VALIDATION_ACTUELLE.scripts.recalculate_empirical_scores_finnhub import (
    recalculate_empirical_scores_finnhub
)

def load_current_scores(db_path: Path, countries: list = ['US']) -> pd.DataFrame:
    """Charge les scores actuels de la DB"""
    conn = duckdb.connect(str(db_path), read_only=True)
    
    countries_str = "', '".join(countries)
    query = f"""
    SELECT 
        event_key,
        country,
        empirical_score,
        avg_movement_pips,
        sample_size,
        family
    FROM event_families
    WHERE country IN ('{countries_str}')
      AND empirical_score IS NOT NULL
    ORDER BY event_key, country
    """
    
    df = conn.execute(query).df()
    conn.close()
    
    return df

def calculate_scores_dry_run(db_path: Path, start_date: str, end_date: str, countries: list) -> pd.DataFrame:
    """Calcule les scores en mode dry-run et retourne les résultats"""
    import io
    import contextlib
    
    # Capturer la sortie pour extraire les résultats
    # On va modifier temporairement la fonction pour retourner les résultats
    from SESSION_VALIDATION_ACTUELLE.scripts import recalculate_empirical_scores_finnhub as recalc_module
    
    # Exécuter le recalcul et capturer les résultats
    results = []
    
    # On va utiliser une version modifiée qui retourne les résultats
    conn = duckdb.connect(str(db_path), read_only=False)
    
    try:
        # Recalculer (on va copier la logique mais retourner les résultats)
        from SESSION_VALIDATION_ACTUELLE.scripts.recalculate_empirical_scores_finnhub import (
            recalculate_empirical_scores_finnhub
        )
        
        # On va créer une version qui retourne les résultats au lieu de les afficher
        # Pour l'instant, on va simplement exécuter et extraire depuis la DB temporaire
        
        # Créer une table temporaire avec les résultats
        # On va modifier le script pour qu'il sauvegarde dans une table temporaire même en dry-run
        
        # Solution plus simple : exécuter le recalcul et extraire les résultats depuis le code
        # On va appeler directement les fonctions internes
        
        from SESSION_VALIDATION_ACTUELLE.scripts.recalculate_empirical_scores_finnhub import (
            calculate_scores_for_event_family,
            measure_impact_for_event
        )
        
        # Charger événements
        countries_str = "', '".join(countries)
        query_events = f"""
        SELECT 
            event_key,
            country,
            ts_utc,
            importance_n
        FROM events
        WHERE DATE(ts_utc) >= '{start_date}'
          AND DATE(ts_utc) <= '{end_date}'
          AND country IN ('{countries_str}')
        ORDER BY event_key, country, ts_utc
        """
        
        df_all_events = conn.execute(query_events).df()
        
        if df_all_events.empty:
            return pd.DataFrame()
        
        # Grouper par (event_key, country)
        grouped = df_all_events.groupby(['event_key', 'country'])
        
        for (event_key, country), events_df in grouped:
            if len(events_df) < 3:  # MIN_SAMPLE_SIZE
                continue
            
            result = calculate_scores_for_event_family(
                conn, event_key, country, events_df, verbose=False
            )
            
            if result:
                results.append(result)
        
        return pd.DataFrame(results)
        
    finally:
        conn.close()

def compare_scores(
    db_path: Path = DB_PATH,
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    countries: list = ['US']
):
    """Compare les scores calculés avec ceux de la DB"""
    print("="*100)
    print("COMPARAISON SCORES EMPIRIQUES : CALCULÉS vs DB ACTUELLE")
    print("="*100)
    print()
    
    # 1. Charger scores actuels
    print("1. Chargement scores actuels depuis event_families...")
    df_current = load_current_scores(db_path, countries)
    print(f"   ✅ {len(df_current)} scores chargés")
    print()
    
    # 2. Calculer nouveaux scores
    print("2. Calcul nouveaux scores depuis Finnhub...")
    print("   (Cela peut prendre quelques minutes...)")
    print()
    df_calculated = calculate_scores_dry_run(db_path, start_date, end_date, countries)
    print(f"   ✅ {len(df_calculated)} scores calculés")
    print()
    
    if df_calculated.empty:
        print("❌ Aucun score calculé - arrêt")
        return
    
    # 3. Fusionner pour comparaison
    print("3. Fusion des données pour comparaison...")
    df_merged = df_current.merge(
        df_calculated,
        on=['event_key', 'country'],
        how='outer',
        suffixes=('_current', '_calculated')
    )
    print(f"   ✅ {len(df_merged)} entrées fusionnées")
    print()
    
    # 4. Calculer écarts
    print("4. Calcul des écarts...")
    df_merged['ecart_absolu'] = df_merged['empirical_score_calculated'] - df_merged['empirical_score_current']
    df_merged['ecart_pct'] = (
        (df_merged['empirical_score_calculated'] - df_merged['empirical_score_current']) 
        / df_merged['empirical_score_current'] * 100
    ).fillna(0)
    
    # Filtrer seulement ceux qui existent dans les deux
    df_both = df_merged[
        df_merged['empirical_score_current'].notna() & 
        df_merged['empirical_score_calculated'].notna()
    ].copy()
    
    print(f"   ✅ {len(df_both)} événements présents dans les deux")
    print()
    
    # 5. Statistiques générales
    print("="*100)
    print("STATISTIQUES GÉNÉRALES")
    print("="*100)
    print()
    
    print(f"Scores actuels (DB):")
    print(f"   Moyenne: {df_current['empirical_score'].mean():.2f}")
    print(f"   Médiane: {df_current['empirical_score'].median():.2f}")
    print(f"   Min: {df_current['empirical_score'].min():.2f}")
    print(f"   Max: {df_current['empirical_score'].max():.2f}")
    print()
    
    print(f"Scores calculés (Finnhub):")
    print(f"   Moyenne: {df_calculated['empirical_score'].mean():.2f}")
    print(f"   Médiane: {df_calculated['empirical_score'].median():.2f}")
    print(f"   Min: {df_calculated['empirical_score'].min():.2f}")
    print(f"   Max: {df_calculated['empirical_score'].max():.2f}")
    print()
    
    if len(df_both) > 0:
        print(f"Écarts (Calculé - Actuel):")
        print(f"   Moyenne: {df_both['ecart_absolu'].mean():.2f} pips")
        print(f"   Médiane: {df_both['ecart_absolu'].median():.2f} pips")
        print(f"   Écart moyen (%): {df_both['ecart_pct'].mean():.1f}%")
        print(f"   Écart médian (%): {df_both['ecart_pct'].median():.1f}%")
        print()
        
        # Événements avec écarts significatifs
        df_significant = df_both[
            (df_both['ecart_absolu'].abs() > 10) | 
            (df_both['ecart_pct'].abs() > 20)
        ].sort_values('ecart_absolu', key=abs, ascending=False)
        
        print(f"Événements avec écarts significatifs (>10 pips ou >20%): {len(df_significant)}")
        print()
    
    # 6. Top écarts positifs (scores calculés > actuels)
    print("="*100)
    print("TOP 20 ÉCARTS POSITIFS (Calculé > Actuel)")
    print("="*100)
    if len(df_both) > 0:
        df_positive = df_both[df_both['ecart_absolu'] > 0].nlargest(20, 'ecart_absolu')
        if len(df_positive) > 0:
            print(f"{'Event Key':<50} {'Country':<8} {'Actuel':<10} {'Calculé':<10} {'Écart':<10} {'Écart %':<10}")
            print("-"*100)
            for _, row in df_positive.iterrows():
                print(f"{row['event_key'][:49]:<50} {row['country']:<8} "
                      f"{row['empirical_score_current']:<10.2f} {row['empirical_score_calculated']:<10.2f} "
                      f"{row['ecart_absolu']:<10.2f} {row['ecart_pct']:<10.1f}%")
        else:
            print("Aucun écart positif significatif")
    print()
    
    # 7. Top écarts négatifs (scores calculés < actuels)
    print("="*100)
    print("TOP 20 ÉCARTS NÉGATIFS (Calculé < Actuel)")
    print("="*100)
    if len(df_both) > 0:
        df_negative = df_both[df_both['ecart_absolu'] < 0].nsmallest(20, 'ecart_absolu')
        if len(df_negative) > 0:
            print(f"{'Event Key':<50} {'Country':<8} {'Actuel':<10} {'Calculé':<10} {'Écart':<10} {'Écart %':<10}")
            print("-"*100)
            for _, row in df_negative.iterrows():
                print(f"{row['event_key'][:49]:<50} {row['country']:<8} "
                      f"{row['empirical_score_current']:<10.2f} {row['empirical_score_calculated']:<10.2f} "
                      f"{row['ecart_absolu']:<10.2f} {row['ecart_pct']:<10.1f}%")
        else:
            print("Aucun écart négatif significatif")
    print()
    
    # 8. Événements seulement dans DB actuelle
    print("="*100)
    print("ÉVÉNEMENTS SEULEMENT DANS DB ACTUELLE (non recalculés)")
    print("="*100)
    df_only_current = df_merged[
        df_merged['empirical_score_current'].notna() & 
        df_merged['empirical_score_calculated'].isna()
    ]
    if len(df_only_current) > 0:
        print(f"   {len(df_only_current)} événements")
        print("   Top 10:")
        for _, row in df_only_current.head(10).iterrows():
            print(f"      - {row['event_key']} ({row['country']}): {row['empirical_score_current']:.2f}")
    else:
        print("   Aucun")
    print()
    
    # 9. Événements seulement dans calculés (nouveaux)
    print("="*100)
    print("ÉVÉNEMENTS SEULEMENT DANS CALCULÉS (nouveaux)")
    print("="*100)
    df_only_calculated = df_merged[
        df_merged['empirical_score_current'].isna() & 
        df_merged['empirical_score_calculated'].notna()
    ]
    if len(df_only_calculated) > 0:
        print(f"   {len(df_only_calculated)} événements")
        print("   Top 10:")
        for _, row in df_only_calculated.head(10).iterrows():
            print(f"      - {row['event_key']} ({row['country']}): {row['empirical_score_calculated']:.2f}")
    else:
        print("   Aucun")
    print()
    
    # 10. Sauvegarder résultats
    output_file = PROJECT_ROOT / 'SESSION_VALIDATION_ACTUELLE' / 'outputs' / 'comparison_empirical_scores.csv'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(output_file, index=False)
    print("="*100)
    print(f"✅ Résultats sauvegardés: {output_file}")
    print("="*100)

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comparer scores empiriques calculés vs DB')
    parser.add_argument('--start-date', type=str, default='2024-01-01', help='Date début')
    parser.add_argument('--end-date', type=str, default='2024-12-31', help='Date fin')
    parser.add_argument('--countries', type=str, nargs='+', default=['US'], help='Pays')
    
    args = parser.parse_args()
    
    compare_scores(
        db_path=DB_PATH,
        start_date=args.start_date,
        end_date=args.end_date,
        countries=args.countries
    )

if __name__ == '__main__':
    main()




