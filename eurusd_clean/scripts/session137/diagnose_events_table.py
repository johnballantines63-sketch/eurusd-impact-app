"""
DIAGNOSTIC TABLE EVENTS - Session 137
Comprendre pourquoi importance_n = 3 retourne 0 lignes

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

def diagnose_events():
    """Diagnostiquer la table events"""
    
    print("=" * 80)
    print("DIAGNOSTIC TABLE EVENTS")
    print("=" * 80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Nombre total événements
    print("\n📊 STATISTIQUES GÉNÉRALES :")
    print("-" * 80)
    
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"   Total événements dans table events : {total:,}")
    
    # 2. Valeurs dans importance_n
    print("\n📋 VALEURS COLONNE importance_n :")
    print("-" * 80)
    
    query = """
    SELECT 
        importance_n,
        COUNT(*) as nb_events,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
    FROM events
    WHERE importance_n IS NOT NULL
    GROUP BY importance_n
    ORDER BY importance_n
    """
    
    results = conn.execute(query).fetchall()
    for imp_n, nb, pct in results:
        print(f"   importance_n = {imp_n} : {nb:,} événements ({pct}%)")
    
    # 3. Valeurs NULL
    null_count = conn.execute("SELECT COUNT(*) FROM events WHERE importance_n IS NULL").fetchone()[0]
    print(f"   importance_n = NULL : {null_count:,} événements")
    
    # 4. Échantillon événements
    print("\n📋 ÉCHANTILLON ÉVÉNEMENTS (10 premiers) :")
    print("-" * 80)
    
    query_sample = """
    SELECT 
        event_key,
        event_title,
        country,
        importance_n,
        ts_utc
    FROM events
    ORDER BY ts_utc DESC
    LIMIT 10
    """
    
    samples = conn.execute(query_sample).fetchall()
    for key, title, country, imp_n, ts in samples:
        print(f"   {key[:30]:30s} | {country:2s} | imp={imp_n} | {title[:30]:30s}")
    
    # 5. Vérifier si autre colonne importance
    print("\n🔍 RECHERCHE AUTRES COLONNES IMPORTANCE :")
    print("-" * 80)
    
    cols = conn.execute("PRAGMA table_info(events)").fetchall()
    importance_cols = [col[1] for col in cols if 'import' in col[1].lower()]
    
    if importance_cols:
        print(f"   Colonnes trouvées : {', '.join(importance_cols)}")
        
        for col in importance_cols:
            print(f"\n   Distribution {col} :")
            query_col = f"""
            SELECT 
                {col},
                COUNT(*) as nb
            FROM events
            WHERE {col} IS NOT NULL
            GROUP BY {col}
            ORDER BY nb DESC
            LIMIT 5
            """
            results_col = conn.execute(query_col).fetchall()
            for val, nb in results_col:
                print(f"      {val} : {nb:,}")
    else:
        print("   Aucune autre colonne 'importance' trouvée")
    
    # 6. Comparer avec event_families
    print("\n🔗 COMPARAISON events ↔ event_families :")
    print("-" * 80)
    
    query_join = """
    SELECT 
        COUNT(DISTINCT e.event_key) as events_distincts,
        COUNT(DISTINCT ef.event_key) as families_distincts,
        COUNT(DISTINCT CASE WHEN ef.event_key IS NOT NULL THEN e.event_key END) as match
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key
    """
    
    ev_dist, fam_dist, match = conn.execute(query_join).fetchone()
    print(f"   event_key distincts dans events        : {ev_dist:,}")
    print(f"   event_key distincts dans event_families : {fam_dist:,}")
    print(f"   Matchés (events ∩ families)             : {match:,}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("FIN DIAGNOSTIC")
    print("=" * 80)

if __name__ == '__main__':
    diagnose_events()
