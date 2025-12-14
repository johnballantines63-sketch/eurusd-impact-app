"""
DIAGNOSTIC CRITIQUE - TROUVER BONNE TABLE ÉVÉNEMENTS
Session 137 - Laquelle contient les événements HIGH ?

Problème: 0 événements HIGH trouvés dans table 'events'
Hypothèse: Les données sont peut-être dans 'economic_events' ?

Auteur: André Valentin avec Claude
Date: 14 novembre 2025
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "warehouse.duckdb"

def check_all_event_tables():
    """Vérifier TOUTES les tables qui pourraient contenir événements"""
    
    print("="*80)
    print("DIAGNOSTIC - TROUVER BONNE TABLE ÉVÉNEMENTS")
    print("="*80)
    
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    
    # Tables candidates
    tables_to_check = [
        'events',
        'economic_events',
        'event_impacts_v2'
    ]
    
    for table_name in tables_to_check:
        print(f"\n{'='*80}")
        print(f"TABLE: {table_name}")
        print("="*80)
        
        try:
            # 1. Compter total
            query_count = f"SELECT COUNT(*) FROM {table_name}"
            total = conn.execute(query_count).fetchone()[0]
            print(f"\nTotal lignes: {total:,}")
            
            if total == 0:
                print("⚠️ Table VIDE")
                continue
            
            # 2. Structure
            print("\nStructure (colonnes):")
            print("-" * 80)
            structure = conn.execute(f"DESCRIBE {table_name}").df()
            print(structure[['column_name', 'column_type']].to_string(index=False))
            
            # 3. Chercher colonne importance
            importance_cols = structure[structure['column_name'].str.contains('importance', case=False)]
            
            if len(importance_cols) > 0:
                importance_col = importance_cols.iloc[0]['column_name']
                print(f"\n✅ Colonne importance trouvée: {importance_col}")
                
                # 4. Distribution importance
                query_dist = f"""
                SELECT {importance_col}, COUNT(*) as count
                FROM {table_name}
                GROUP BY {importance_col}
                ORDER BY {importance_col}
                """
                df_dist = conn.execute(query_dist).df()
                print("\nDistribution importance:")
                print("-" * 80)
                print(df_dist.to_string(index=False))
                
                # 5. Compter HIGH (si importance_n)
                if importance_col == 'importance_n':
                    query_high = f"SELECT COUNT(*) FROM {table_name} WHERE importance_n = 3"
                    high_count = conn.execute(query_high).fetchone()[0]
                    print(f"\n✅ Événements HIGH (importance_n = 3): {high_count:,}")
                    
                    if high_count > 0:
                        # Aperçu
                        query_sample = f"""
                        SELECT * FROM {table_name}
                        WHERE importance_n = 3
                        LIMIT 3
                        """
                        df_sample = conn.execute(query_sample).df()
                        print("\nAperçu événements HIGH:")
                        print("-" * 80)
                        print(df_sample.to_string())
            else:
                print("\n⚠️ Aucune colonne importance trouvée")
            
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
    
    conn.close()
    
    # Recommandation
    print("\n" + "="*80)
    print("RECOMMANDATION")
    print("="*80)
    print("\nSi table 'economic_events' contient les événements HIGH:")
    print("   → Modifier toutes les requêtes pour utiliser 'economic_events'")
    print("   → OU clarifier quelle table utiliser")
    
    print("\nSi table 'events' est vraiment vide:")
    print("   → Problème de structure DB")
    print("   → Vérifier documentation MASTER_PLAN.md")

if __name__ == "__main__":
    check_all_event_tables()
