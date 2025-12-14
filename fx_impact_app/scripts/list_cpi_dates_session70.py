"""
LISTE DES DATES CPI DISPONIBLES - Session 70
Identifie toutes les dates avec événements CPI (score > 40)
pour comprendre pourquoi 2025-02-12 retourne 2025-09-11
"""

import sys
from pathlib import Path

# Ajouter chemin src
file_dir = Path(__file__).resolve().parent
fx_impact_app_dir = file_dir.parent
src_path = fx_impact_app_dir / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
import duckdb


def list_all_cpi_dates():
    """Liste toutes les dates avec événements CPI qualifiants"""
    
    print("\n" + "="*70)
    print("DATES CPI DISPONIBLES DANS LA BASE DE DONNÉES")
    print("="*70)
    
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Query pour trouver toutes les dates CPI
    query = """
    SELECT 
        DATE(e.ts_utc) as date_event,
        COUNT(*) as nb_events,
        AVG(ef.empirical_score) as score_moyen,
        STRING_AGG(DISTINCT e.label, ', ') as events
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
        AND (e.label ILIKE '%CPI%' OR ef.family ILIKE '%CPI%')
    GROUP BY DATE(e.ts_utc)
    ORDER BY DATE(e.ts_utc) DESC
    LIMIT 50
    """
    
    print("\n🔍 Recherche événements CPI (score > 40, US uniquement)...\n")
    
    df = conn.execute(query).df()
    
    if df.empty:
        print("❌ Aucun événement CPI trouvé !")
        conn.close()
        return
    
    print(f"✅ {len(df)} dates trouvées avec événements CPI\n")
    print("="*70)
    print(f"{'Date':<15} {'Nb Events':<12} {'Score Moy':<12} {'Événements'}")
    print("="*70)
    
    for _, row in df.iterrows():
        date_str = row['date_event'].strftime('%Y-%m-%d')
        nb = int(row['nb_events'])
        score = row['score_moyen']
        events_str = row['events'] if row['events'] else 'N/A'
        events = events_str[:50] + "..." if len(events_str) > 50 else events_str
        
        print(f"{date_str:<15} {nb:<12} {score:<12.1f} {events}")
    
    # Chercher spécifiquement 2025-02-12
    print("\n" + "="*70)
    print("RECHERCHE SPÉCIFIQUE : 2025-02-12")
    print("="*70)
    
    query_specific = """
    SELECT 
        e.label,
        e.ts_utc,
        ef.empirical_score,
        ef.family
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = '2025-02-12'
        AND e.country = 'US'
    ORDER BY e.ts_utc
    """
    
    df_feb = conn.execute(query_specific).df()
    
    if df_feb.empty:
        print("\n❌ AUCUN événement trouvé pour 2025-02-12 (toutes catégories)")
    else:
        print(f"\n✅ {len(df_feb)} événement(s) trouvé(s) pour 2025-02-12 :")
        print("\nTous événements :")
        for idx, row in df_feb.iterrows():
            score = row['empirical_score'] if row['empirical_score'] else 'NULL'
            family = row['family'] if row['family'] else 'NULL'
            print(f"{idx+1}. {row['label']}")
            print(f"   Heure: {row['ts_utc']}")
            print(f"   Score: {score}")
            print(f"   Family: {family}")
            print()
        
        # Filtrer score > 40
        df_feb_filtered = df_feb[
            (df_feb['empirical_score'].notna()) & 
            (df_feb['empirical_score'] > 40)
        ]
        
        print(f"\nAprès filtre (score > 40) : {len(df_feb_filtered)} événements")
        
        if not df_feb_filtered.empty:
            print("Événements qualifiants :")
            for idx, row in df_feb_filtered.iterrows():
                print(f"{idx+1}. {row['label']} - Score: {row['empirical_score']:.1f}")
        
        # Filtrer CPI
        df_feb_cpi = df_feb_filtered[
            (df_feb_filtered['label'].str.contains('CPI', case=False, na=False)) | 
            (df_feb_filtered['family'].str.contains('CPI', case=False, na=False))
        ]
        
        print(f"\nAprès filtre CPI : {len(df_feb_cpi)} événements")
    
    conn.close()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("\n💡 Si 2025-02-12 n'apparaît pas dans la liste ci-dessus,")
    print("   alors le Planificateur retourne correctement 'Aucun événement'.")
    print("\n💡 Si l'interface affiche quand même des résultats du 11 septembre,")
    print("   c'est un problème de CACHE Streamlit (st.cache_resource).")
    print("\n✅ SOLUTION : Redémarrer l'application Streamlit pour vider le cache.")


if __name__ == "__main__":
    list_all_cpi_dates()
