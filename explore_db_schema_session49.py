"""
Script Session 49 : Explorer le schéma RÉEL de la base de données

Objectif : Comprendre la structure exacte avant de continuer
"""

import sys
from pathlib import Path
import duckdb

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "fx_impact_app" / "src"))

from config import get_db_path


def explore_schema():
    """Explore la structure complète de la DB"""
    
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    print("=" * 80)
    print("📊 EXPLORATION SCHÉMA BASE DE DONNÉES")
    print("=" * 80)
    
    # 1. Lister toutes les tables
    print("\n🗂️  TABLES DISPONIBLES :")
    print("-" * 80)
    
    tables = conn.execute("SHOW TABLES").fetchall()
    for table in tables:
        print(f"  • {table[0]}")
    
    # 2. Pour chaque table importante, afficher structure
    important_tables = ['events', 'event_families', 'event_group_impacts', 
                        'precomputed_family_stats', 'prices_1m']
    
    for table_name in important_tables:
        try:
            print(f"\n📋 TABLE : {table_name}")
            print("-" * 80)
            
            # Schéma de la table
            schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
            
            print("Colonnes :")
            for col in schema:
                col_name = col[0]
                col_type = col[1]
                nullable = col[2] if len(col) > 2 else 'unknown'
                print(f"  • {col_name:30s} | {col_type:20s} | Nullable: {nullable}")
            
            # Compter les lignes
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"\n  📊 Nombre de lignes : {count:,}")
            
            # Échantillon de données (3 premières lignes)
            print("\n  🔍 Échantillon (3 premières lignes) :")
            sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
            
            if sample:
                # Récupérer les noms de colonnes
                cols = [desc[0] for desc in schema]
                
                for i, row in enumerate(sample, 1):
                    print(f"\n    Ligne {i}:")
                    for col_name, value in zip(cols, row):
                        # Tronquer les valeurs trop longues
                        val_str = str(value)
                        if len(val_str) > 60:
                            val_str = val_str[:57] + "..."
                        print(f"      {col_name:25s} = {val_str}")
            
        except Exception as e:
            print(f"  ⚠️  Table non trouvée ou erreur : {e}")
    
    # 3. Requête spéciale : événements du 11 septembre
    print("\n" + "=" * 80)
    print("🎯 ÉVÉNEMENTS DU 11 SEPTEMBRE 2025")
    print("=" * 80)
    
    # Essayer différentes approches pour trouver les événements
    
    # Approche 1 : Par date dans events
    try:
        query = """
        SELECT *
        FROM events
        WHERE strftime(ts_utc, '%Y-%m-%d') = '2025-09-11'
        ORDER BY ts_utc
        LIMIT 10
        """
        
        result = conn.execute(query).fetchall()
        
        if result:
            print(f"\n✅ {len(result)} événements trouvés le 11/09/2025 dans 'events'")
            
            # Afficher colonnes disponibles
            desc = conn.execute(query).description
            col_names = [d[0] for d in desc]
            print(f"\nColonnes : {', '.join(col_names)}")
            
            # Afficher les 3 premiers
            for i, row in enumerate(result[:3], 1):
                print(f"\n  Événement {i}:")
                for col_name, value in zip(col_names, row):
                    val_str = str(value)
                    if len(val_str) > 60:
                        val_str = val_str[:57] + "..."
                    print(f"    {col_name:20s} = {val_str}")
        else:
            print("❌ Aucun événement trouvé le 11/09/2025")
            
    except Exception as e:
        print(f"❌ Erreur recherche événements : {e}")
    
    # Approche 2 : Vérifier s'il y a une table de mapping
    print("\n" + "=" * 80)
    print("🔗 RECHERCHE TABLE DE MAPPING FAMILY")
    print("=" * 80)
    
    try:
        # Chercher si event_families existe
        ef_query = "SELECT * FROM event_families LIMIT 5"
        ef_result = conn.execute(ef_query).fetchall()
        
        if ef_result:
            print("✅ Table 'event_families' trouvée")
            
            desc = conn.execute(ef_query).description
            col_names = [d[0] for d in desc]
            print(f"Colonnes : {', '.join(col_names)}")
            
            print("\nExemples de mapping :")
            for i, row in enumerate(ef_result, 1):
                print(f"  {i}. {dict(zip(col_names, row))}")
    except Exception as e:
        print(f"⚠️  Pas de table event_families ou erreur : {e}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("💡 CONCLUSION")
    print("=" * 80)
    print("""
Cette exploration nous montre :
1. La structure RÉELLE des tables
2. Quelles colonnes existent vraiment (pas 'family' mais 'label' ?)
3. Comment le planificateur fait le mapping
4. Où sont stockées les données forecast/actual/surprise

PROCHAINE ÉTAPE :
- Comprendre comment le planificateur charge les événements
- Identifier la logique de mapping vers 'family'
- Voir si on peut enrichir la DB ou si les calculs sont fait ailleurs
""")


if __name__ == "__main__":
    explore_schema()
