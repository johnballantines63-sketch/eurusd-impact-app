"""
LISTE DATES DISPONIBLES - PLANIFICATEUR
========================================

Session 82 - Query des dates avec HIGH IMPACT US events dans warehouse.duckdb

Objectif :
- Lister toutes les dates avec événements HIGH IMPACT US
- Statistiques par date (total events, US events, high impact US)
- Top 50 dates pour le planificateur

"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Chemin vers la DB
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")

def list_available_dates():
    """
    Liste les dates disponibles avec HIGH IMPACT US events
    
    Returns:
        DataFrame avec dates et statistiques
    """
    print("="*80)
    print("📅 DATES DISPONIBLES PLANIFICATEUR - SESSION 82")
    print("="*80)
    print(f"\n📂 Base de données : {DB_PATH}")
    print(f"✅ Existe : {DB_PATH.exists()}\n")
    
    if not DB_PATH.exists():
        print(f"❌ ERREUR : Base de données introuvable")
        return None
    
    # Connexion DB
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Query dates avec événements HIGH IMPACT US
    # MÉTHODE PLANIFICATEUR : empirical_score > 40 (pas importance_n)
    query = """
    SELECT 
        DATE(e.ts_utc) as date,
        COUNT(DISTINCT e.event_key) as total_events,
        COUNT(DISTINCT CASE WHEN e.country = 'US' THEN e.event_key ELSE NULL END) as us_events,
        COUNT(DISTINCT CASE WHEN e.country = 'US' AND ef.empirical_score > 40 
            THEN e.event_key ELSE NULL END) as high_impact_us,
        MAX(CASE WHEN e.country = 'US' AND ef.empirical_score > 40 
            THEN ef.empirical_score ELSE 0 END) as max_score
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) >= '2024-01-01'
        AND DATE(e.ts_utc) <= '2025-12-31'
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
    GROUP BY DATE(e.ts_utc)
    HAVING COUNT(DISTINCT CASE WHEN ef.empirical_score > 40 THEN e.event_key ELSE NULL END) > 0
    ORDER BY date DESC
    LIMIT 50
    """
    
    print("⏳ Exécution query...")
    df = conn.execute(query).df()
    conn.close()
    
    print(f"✅ Query complétée : {len(df)} dates trouvées\n")
    
    return df

def analyze_dates(df):
    """Analyse et affiche statistiques des dates"""
    
    print("="*80)
    print("📊 TOP 50 DATES DISPONIBLES")
    print("="*80)
    print()
    
    # Afficher DataFrame
    print(df.to_string(index=False))
    
    print("\n" + "="*80)
    print("📈 STATISTIQUES GLOBALES")
    print("="*80)
    
    print(f"\n📅 Dates disponibles : {len(df)}")
    print(f"📊 Moyenne HIGH IMPACT US : {df['high_impact_us'].mean():.1f} événements/jour")
    print(f"📈 Max HIGH IMPACT US : {df['high_impact_us'].max()} événements")
    print(f"📉 Min HIGH IMPACT US : {df['high_impact_us'].min()} événement(s)")
    print(f"⭐ Score max observé : {df['max_score'].max():.1f}")
    
    # Top 10 dates par nombre d'événements
    print("\n" + "="*80)
    print("🏆 TOP 10 DATES PAR NOMBRE D'ÉVÉNEMENTS HIGH IMPACT US")
    print("="*80)
    print()
    
    top10 = df.nlargest(10, 'high_impact_us')[['date', 'high_impact_us', 'max_score']]
    print(top10.to_string(index=False))
    
    # Distribution par nombre d'événements
    print("\n" + "="*80)
    print("📊 DISTRIBUTION PAR NOMBRE D'ÉVÉNEMENTS")
    print("="*80)
    print()
    
    distribution = df['high_impact_us'].value_counts().sort_index()
    for n_events, count in distribution.items():
        bar = '█' * int(count / 2)
        print(f"{n_events:2d} événements : {count:3d} dates {bar}")
    
    # Recommandations test
    print("\n" + "="*80)
    print("🎯 RECOMMANDATIONS TESTS PLANIFICATEUR")
    print("="*80)
    print()
    
    # Dates validées Session 81
    validated = df[df['date'].isin(['2025-09-11', '2025-02-12'])]
    if not validated.empty:
        print("✅ DATES DÉJÀ VALIDÉES (Session 81) :")
        print(validated[['date', 'high_impact_us', 'max_score']].to_string(index=False))
        print()
    
    # Date 01.08.2025 (NFP extrême)
    date_0108 = df[df['date'] == '2025-08-01']
    if not date_0108.empty:
        print("🔥 DATE PRIORITAIRE (NFP Extrême) :")
        print(date_0108[['date', 'high_impact_us', 'max_score']].to_string(index=False))
        print()
    
    # Suggestions autres dates
    print("💡 SUGGESTIONS DATES DIVERSIFIÉES :")
    
    # Faible impact (2-4 événements)
    low = df[(df['high_impact_us'] >= 2) & (df['high_impact_us'] <= 4)].head(2)
    if not low.empty:
        print("\n  📉 Faible impact (2-4 événements) :")
        print("  " + low[['date', 'high_impact_us']].to_string(index=False).replace('\n', '\n  '))
    
    # Moyen impact (5-8 événements)
    medium = df[(df['high_impact_us'] >= 5) & (df['high_impact_us'] <= 8)].head(2)
    if not medium.empty:
        print("\n  📊 Moyen impact (5-8 événements) :")
        print("  " + medium[['date', 'high_impact_us']].to_string(index=False).replace('\n', '\n  '))
    
    # Fort impact (9+ événements)
    high = df[df['high_impact_us'] >= 9].head(2)
    if not high.empty:
        print("\n  📈 Fort impact (9+ événements) :")
        print("  " + high[['date', 'high_impact_us']].to_string(index=False).replace('\n', '\n  '))
    
    print("\n" + "="*80)

def main():
    """Fonction principale"""
    
    # Lister dates
    df = list_available_dates()
    
    if df is None or df.empty:
        print("❌ Aucune date trouvée")
        return
    
    # Analyser dates
    analyze_dates(df)
    
    # Sauvegarder CSV
    output_path = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session82/dates_disponibles.csv")
    df.to_csv(output_path, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
