"""
DEBUG DATE QUERY - Session 70
Teste si la requête SQL utilise bien la date fournie

Problème rapporté :
- Date saisie : 2025-02-12
- Résultats retournés : 2025-09-11 (toujours)

Test :
1. Exécuter requête avec 2025-02-12
2. Exécuter requête avec 2025-09-11
3. Comparer résultats
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter chemin src
file_dir = Path(__file__).resolve().parent
fx_impact_app_dir = file_dir.parent
src_path = fx_impact_app_dir / "src"
sys.path.insert(0, str(src_path))

from config import get_db_path
import duckdb


def test_query_with_date(test_date: str):
    """
    Teste la requête avec une date spécifique
    
    Args:
        test_date: Date format 'YYYY-MM-DD'
    """
    print(f"\n{'='*60}")
    print(f"TEST REQUÊTE AVEC DATE : {test_date}")
    print(f"{'='*60}")
    
    db_path = get_db_path()
    conn = duckdb.connect(str(db_path), read_only=True)
    
    # Query EXACTE du Planificateur
    query = """
    SELECT 
        e.event_key,
        e.label,
        e.ts_utc,
        e.actual,
        e.estimate,
        ef.family,
        ef.empirical_score,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key AND e.country = ef.country
    WHERE DATE(e.ts_utc) = ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40
    ORDER BY e.ts_utc
    """
    
    print(f"\n🔍 Requête SQL :")
    print(query)
    print(f"\n📅 Paramètre : {test_date}")
    
    # Exécuter
    df_events = conn.execute(query, [test_date]).df()
    
    print(f"\n📊 Résultats :")
    print(f"   Nombre d'événements : {len(df_events)}")
    
    if not df_events.empty:
        print(f"\n   Événements trouvés :")
        for idx, row in df_events.iterrows():
            print(f"   {idx+1}. {row['label']} - {row['ts_utc']} - Score: {row['empirical_score']:.1f}")
        
        # Filtrer CPI
        cpi_events = df_events[
            df_events['label'].str.contains('CPI', case=False, na=False) | 
            df_events['family'].str.contains('CPI', case=False, na=False)
        ]
        
        print(f"\n   Événements CPI après filtre :")
        print(f"   Nombre : {len(cpi_events)}")
        if not cpi_events.empty:
            for idx, row in cpi_events.iterrows():
                print(f"   {idx+1}. {row['label']} - {row['ts_utc']}")
    else:
        print(f"   ❌ Aucun événement trouvé pour {test_date}")
    
    conn.close()
    return df_events


def main():
    """Test principal"""
    print("\n" + "="*60)
    print("DEBUG DATE QUERY - Session 70")
    print("="*60)
    
    # Test 1 : Date problématique (2025-02-12)
    print("\n\n🧪 TEST 1 : Date saisie par utilisateur")
    df1 = test_query_with_date('2025-02-12')
    
    # Test 2 : Date référence (2025-09-11)
    print("\n\n🧪 TEST 2 : Date référence (11 septembre)")
    df2 = test_query_with_date('2025-09-11')
    
    # Test 3 : Autre date CPI connue
    print("\n\n🧪 TEST 3 : Autre date CPI (12 décembre 2024)")
    df3 = test_query_with_date('2024-12-11')
    
    # Résumé
    print("\n\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    print(f"Date 2025-02-12 : {len(df1)} événements")
    print(f"Date 2025-09-11 : {len(df2)} événements")
    print(f"Date 2024-12-11 : {len(df3)} événements")
    
    print("\n\n💡 DIAGNOSTIC :")
    if len(df2) > 0 and len(df1) == 0:
        print("   La requête SQL fonctionne CORRECTEMENT.")
        print("   Le 11 septembre a des événements.")
        print("   Le 12 février 2025 n'a PAS d'événements CPI (score > 40).")
        print("\n   ⚠️ CONCLUSION : Ce n'est PAS un bug SQL !")
        print("   Le problème est que la date 2025-02-12 n'a vraiment")
        print("   pas d'événements CPI qualifiants dans la DB.")
    else:
        print("   Vérifier les résultats ci-dessus.")


if __name__ == "__main__":
    main()
