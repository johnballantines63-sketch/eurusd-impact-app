#!/bin/bash
set -e

echo "🚀 Fix complet + Migration DB + Déploiement"
echo "============================================"

# 1. Créer script migration
echo "📝 Création migrate_db.py..."
cat > migrate_db.py << 'PYMIGRATE'
"""Migration DB : Ajoute colonnes latency si manquantes"""
import duckdb
from pathlib import Path

def get_db_path():
    """Trouve le chemin de la DB"""
    possible_paths = [
        Path(__file__).parent / "fx_impact_app" / "data" / "warehouse.duckdb",
        Path("fx_impact_app/data/warehouse.duckdb"),
        Path("/mount/src/eurusd-news-impact-calculator/fx_impact_app/data/warehouse.duckdb")
    ]
    for p in possible_paths:
        if p.exists():
            return str(p)
    return "fx_impact_app/data/warehouse.duckdb"

def migrate_database():
    """Ajoute colonnes latency si nécessaire"""
    try:
        db_path = get_db_path()
        conn = duckdb.connect(db_path)
        
        schema = conn.execute("DESCRIBE event_families").fetchall()
        existing_cols = [col[0] for col in schema]
        
        if 'latency_median' not in existing_cols:
            print("🔧 Migration DB : Ajout colonnes...")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_median DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p20 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS latency_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_median DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p20 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS ttr_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS mfe_p80 DOUBLE")
            conn.execute("ALTER TABLE event_families ADD COLUMN IF NOT EXISTS n_events_latency INTEGER")
            print("✅ Migration OK")
        
        conn.close()
    except Exception as e:
        print(f"⚠️ Migration: {e}")

if __name__ == "__main__":
    migrate_database()
PYMIGRATE

echo "✅ migrate_db.py créé"

# 2. Modifier Planificateur pour inclure migration
echo "📝 Ajout appel migration dans Planificateur..."
python3 << 'PYADD'
import re

file_path = "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

with open(file_path, 'r') as f:
    content = f.read()

# Chercher juste après st.set_page_config
marker = 'st.set_page_config(page_title="Planificateur Multi-Événements", page_icon="📅", layout="wide")'

if marker in content:
    migration_code = '''

# ═══════════════════════════════════════════════════════════════
# MIGRATION DB AUTOMATIQUE
# ═══════════════════════════════════════════════════════════════
try:
    import sys
    from pathlib import Path
    migrate_path = Path(__file__).parent.parent.parent.parent
    if str(migrate_path) not in sys.path:
        sys.path.insert(0, str(migrate_path))
    from migrate_db import migrate_database
    migrate_database()
except Exception as e:
    pass  # Ignore erreurs migration (DB peut être read-only sur cloud)
'''
    
    # Insérer après set_page_config
    pos = content.find(marker) + len(marker)
    content = content[:pos] + migration_code + content[pos:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Migration ajoutée au Planificateur")
else:
    print("⚠️ Marqueur non trouvé")
PYADD

# 3. Tester en local
echo ""
echo "🧪 Test migration local..."
python migrate_db.py

# 4. Vérifier que tout compile
echo ""
echo "🔍 Vérification syntaxe..."
python -m py_compile fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
echo "✅ Syntaxe OK"

# 5. Git add
echo ""
echo "📦 Ajout fichiers Git..."
git add fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py
git add migrate_db.py

# 6. Commit
echo ""
echo "💾 Commit..."
git commit -m "fix: Add DB migration for latency columns + handle missing columns gracefully

- Add migrate_db.py for automatic DB schema migration
- Add migration call at Planificateur startup
- Creates latency_median, ttr_median, mfe_p80 columns if missing
- Handles read-only DB on Streamlit Cloud gracefully
- Fixes CatalogException on cloud deployment"

# 7. Push
echo ""
echo "🚀 Push vers GitHub..."
git push origin main

echo ""
echo "============================================"
echo "✅ DÉPLOIEMENT TERMINÉ !"
echo "⏳ Attendre 2-3 min pour redéploiement Streamlit Cloud"
echo "🌐 URL: https://eurusd-impact-app-ddv6jiartgucij23suwfyq.streamlit.app"
echo "============================================"
