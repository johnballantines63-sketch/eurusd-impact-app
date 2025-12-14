"""
LISTE 40 DATES CPI DISPONIBLES - SESSION 92.13

Objectif : Identifier 40 dates avec événements CPI US pour tests formule S92.13

Critères sélection :
- Events CPI US (Core CPI, CPI MoM, CPI YoY)
- Score empirical_score > 40 (HIGH impact)
- Prix 1min disponibles (prices_1m)
- Période : 2024-2025

Date : 29 octobre 2025
"""

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime


def list_cpi_dates(db_path: str, limit: int = 40) -> pd.DataFrame:
    """
    Liste dates CPI US disponibles avec données complètes
    
    Args:
        db_path: Chemin base de données
        limit: Nombre max de dates
    
    Returns:
        DataFrame avec dates et métadonnées
    """
    print(f"\n{'='*80}")
    print(f"RECHERCHE {limit} DATES CPI US DISPONIBLES")
    print(f"{'='*80}")
    
    conn = duckdb.connect(db_path, read_only=True)
    
    try:
        # Query : Dates avec événements CPI US score > 40
        query = f"""
        SELECT 
            DATE(e.ts_utc) as date,
            COUNT(*) as nb_events,
            MAX(ef.empirical_score) as score_max,
            AVG(ef.empirical_score) as score_avg,
            STRING_AGG(DISTINCT e.event_title, ' | ') as events_list,
            MIN(e.ts_utc) as first_event_time
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE e.country = 'US'
            AND (
                e.event_title ILIKE '%CPI%'
                OR e.event_title ILIKE '%Consumer Price%'
            )
            AND ef.empirical_score > 40
            AND DATE(e.ts_utc) BETWEEN '2024-01-01' AND '2025-12-31'
        GROUP BY DATE(e.ts_utc)
        ORDER BY DATE(e.ts_utc) DESC
        LIMIT {limit}
        """
        
        print(f"\n🔍 Exécution query dates CPI...")
        df_dates = conn.execute(query).df()
        
        print(f"\n✅ Trouvé {len(df_dates)} dates CPI US")
        
        # Vérifier disponibilité prix pour chaque date
        print(f"\n🔍 Vérification disponibilité prix 1min...")
        
        dates_with_prices = []
        
        for idx, row in df_dates.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            
            # Vérifier si prix disponibles pour cette date
            # (24h avant + 2h après event)
            check_query = f"""
            SELECT COUNT(*) as count
            FROM prices_1m
            WHERE DATE(datetime) >= '{date_str}'::DATE - INTERVAL '1 day'
                AND DATE(datetime) <= '{date_str}'::DATE + INTERVAL '1 day'
            """
            
            count_result = conn.execute(check_query).fetchone()
            prix_count = count_result[0] if count_result else 0
            
            if prix_count > 1000:  # Au moins 1000 lignes (environ 16h de données)
                dates_with_prices.append({
                    'date': date_str,
                    'event_time': row['first_event_time'].strftime('%H:%M:%S') if pd.notna(row['first_event_time']) else 'N/A',
                    'nb_events': int(row['nb_events']),
                    'score_max': float(row['score_max']),
                    'score_avg': float(row['score_avg']),
                    'events': row['events_list'][:100] if pd.notna(row['events_list']) else 'N/A',
                    'prix_count': prix_count,
                    'status': '✅'
                })
                print(f"   ✅ {date_str} : {int(row['nb_events'])} events, {prix_count} prix")
            else:
                print(f"   ❌ {date_str} : Prix insuffisants ({prix_count})")
        
        df_final = pd.DataFrame(dates_with_prices)
        
        print(f"\n{'='*80}")
        print(f"RÉSULTAT : {len(df_final)} dates avec données complètes")
        print(f"{'='*80}")
        
        if len(df_final) > 0:
            print(f"\n📊 APERÇU DES {min(10, len(df_final))} PREMIÈRES DATES :")
            print(df_final.head(10).to_string(index=False))
            
            # Statistiques
            print(f"\n📈 STATISTIQUES :")
            print(f"   Période : {df_final['date'].min()} → {df_final['date'].max()}")
            print(f"   Score max moyen : {df_final['score_max'].mean():.1f}")
            print(f"   Events par date (médiane) : {df_final['nb_events'].median():.0f}")
            print(f"   Prix disponibles (médiane) : {df_final['prix_count'].median():.0f}")
        
        return df_final
    
    finally:
        conn.close()


def main():
    """Exécution principale"""
    
    db_path = '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/app/data/warehouse.duckdb'
    
    # Liste 40 dates
    df_dates = list_cpi_dates(db_path, limit=50)  # Query 50 pour avoir marge
    
    if len(df_dates) == 0:
        print("\n❌ ERREUR : Aucune date trouvée avec critères requis")
        return
    
    # Garder top 40 par score
    df_dates = df_dates.sort_values('score_max', ascending=False).head(40)
    
    # Sauvegarder
    output_path = Path(__file__).parent / 'dates_cpi_40.csv'
    df_dates.to_csv(output_path, index=False)
    
    print(f"\n{'='*80}")
    print(f"✅ LISTE SAUVEGARDÉE : {output_path}")
    print(f"{'='*80}")
    print(f"\n📋 {len(df_dates)} dates CPI prêtes pour tests batch")
    print(f"\n🎯 PROCHAINE ÉTAPE : Exécuter test_formule_s92_13_batch.py")


if __name__ == "__main__":
    main()
