"""
Script pour inspecter le schéma de la base de données
"""

import duckdb
import sys
from pathlib import Path

# Ajouter le chemin pour importer config depuis fx_impact_app/src
project_root = Path(__file__).parent
fx_app_src = project_root / "fx_impact_app" / "src"
sys.path.insert(0, str(fx_app_src))

try:
    from config import get_db_path
except ImportError:
    def get_db_path():
        return str(project_root / "fx_impact_app" / "data" / "warehouse.duckdb")

print("=" * 80)
print("INSPECTION DU SCHÉMA DE LA BASE DE DONNÉES")
print("=" * 80)
print()

try:
    conn = duckdb.connect(get_db_path(), read_only=True)
    
    # Lister les tables
    print("📊 TABLES DISPONIBLES :")
    tables = conn.execute("SHOW TABLES").df()
    print(tables)
    print()
    
    # Schéma de la table events
    print("=" * 80)
    print("📋 SCHÉMA DE LA TABLE 'events' :")
    print("=" * 80)
    schema = conn.execute("DESCRIBE events").df()
    print(schema)
    print()
    
    # Échantillon de données
    print("=" * 80)
    print("📝 ÉCHANTILLON DE DONNÉES (5 premières lignes) :")
    print("=" * 80)
    sample = conn.execute("""
        SELECT * FROM events 
        WHERE (country = 'US' OR country IN ('EU', 'DE', 'FR', 'IT', 'ES'))
        ORDER BY ts_utc DESC 
        LIMIT 5
    """).df()
    print(sample)
    print()
    
    # Vérifier si des colonnes liées à surprise existent
    print("=" * 80)
    print("🔍 RECHERCHE DE COLONNES LIÉES À 'SURPRISE' :")
    print("=" * 80)
    columns = schema['column_name'].tolist()
    surprise_cols = [col for col in columns if 'surprise' in col.lower() or 'actual' in col.lower()]
    if surprise_cols:
        print(f"✅ Colonnes trouvées : {surprise_cols}")
    else:
        print("❌ Aucune colonne 'surprise' trouvée")
        print("   Colonnes disponibles :", columns)
    print()
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
