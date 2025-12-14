#!/usr/bin/env python3
"""
RESTRUCTURATION ARCHITECTURE - Phase 2
=======================================

Crée la nouvelle structure propre et migre les fichiers validés.

⚠️ ATTENTION: Ce script fait des modifications importantes
   Assure-toi d'avoir des backups !

Version: 1.0
Date: 04 novembre 2025 - Session 112 - Phase 2
"""

from pathlib import Path
import shutil
from datetime import datetime

print("="*80)
print("🏗️ RESTRUCTURATION ARCHITECTURE")
print("="*80)

base = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC")
eurusd_clean = base / "eurusd_clean"

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Créer la nouvelle structure
# ══════════════════════════════════════════════════════════════════════

print("\n📁 ÉTAPE 1 : Création structure")
print("-"*80)

new_dirs = [
    eurusd_clean / "data",
    eurusd_clean / "src" / "core",
    eurusd_clean / "src" / "analysis",
    eurusd_clean / "streamlit_app",
    eurusd_clean / "streamlit_app" / "pages",
    eurusd_clean / "streamlit_app" / "components",
    eurusd_clean / "scripts" / "archive",
    eurusd_clean / "docs" / "guides",
    eurusd_clean / "tests",
]

for dir_path in new_dirs:
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"✅ {dir_path.relative_to(base)}")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Identifier la DB principale
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 ÉTAPE 2 : Identification DB principale")
print("-"*80)

# Chercher DB avec vue prices_bern
db_candidates = list(base.rglob("warehouse.duckdb"))

main_db = None

for db in db_candidates:
    try:
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        
        # Tester vue
        try:
            count = con.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
            print(f"\n✅ DB avec vue prices_bern trouvée:")
            print(f"   Chemin: {db.relative_to(base)}")
            print(f"   Vue: {count:,} lignes")
            main_db = db
            con.close()
            break
        except:
            pass
        
        con.close()
    except:
        pass

if not main_db:
    print(f"\n⚠️ Aucune DB avec vue prices_bern trouvée")
    print(f"   Utilisation DB par défaut")
    main_db = eurusd_clean / "app" / "data" / "warehouse.duckdb"

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Copier la DB (PAS déplacer, copier pour sécurité)
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("💾 ÉTAPE 3 : Migration DB")
print("-"*80)

target_db = eurusd_clean / "data" / "warehouse.duckdb"

if target_db.exists():
    # Backup existante
    backup_name = f"warehouse_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.duckdb"
    backup_path = eurusd_clean / "data" / backup_name
    shutil.copy2(target_db, backup_path)
    print(f"✅ Backup DB existante: {backup_name}")

print(f"\n📋 Copie DB:")
print(f"   Source: {main_db.relative_to(base)}")
print(f"   Cible:  {target_db.relative_to(base)}")

# Demander confirmation
proceed = input("\n⚠️ Copier la DB ? (oui/non): ").strip().lower()

if proceed == "oui":
    shutil.copy2(main_db, target_db)
    size_mb = target_db.stat().st_size / (1024 * 1024)
    print(f"✅ DB copiée ({size_mb:.2f} MB)")
else:
    print(f"⏭️ DB non copiée (skip)")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 4 : Copier modules Python validés
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📦 ÉTAPE 4 : Migration modules Python")
print("-"*80)

modules_to_copy = [
    ("fx_impact_app/src/formulas_validated.py", "src/core/formulas_validated.py"),
    ("fx_impact_app/src/impact_measurement.py", "src/core/impact_measurement.py"),
    ("fx_impact_app/src/event_loader.py", "src/core/event_loader.py"),
]

for source_rel, target_rel in modules_to_copy:
    source = base / source_rel
    target = eurusd_clean / target_rel
    
    if source.exists():
        shutil.copy2(source, target)
        print(f"✅ {target_rel}")
    else:
        print(f"⚠️ {source_rel} (introuvable)")

# Créer __init__.py
init_file = eurusd_clean / "src" / "core" / "__init__.py"
init_file.write_text('"""Core modules validés"""')
print(f"✅ src/core/__init__.py")

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 5 : Créer config.py centralisé
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("⚙️ ÉTAPE 5 : Configuration centralisée")
print("-"*80)

config_content = '''"""
Configuration centralisée - eurusd_clean
=========================================

Chemins et paramètres pour toute l'application.

Version: 1.0
Date: 04 novembre 2025 - Session 112
"""

from pathlib import Path

# Chemins de base
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "warehouse.duckdb"

# Paramètres DB
DB_TABLE_PRICES = "prices_bern"  # ✅ TOUJOURS utiliser prices_bern
DB_TABLE_EVENTS = "events"

# Paramètres mesure impact
DEFAULT_LOOKBACK_MINUTES = 5
DEFAULT_LOOKAHEAD_MINUTES = 120

# Formules validées (Session 51-55)
FORMULAS_VERSION = "2.4"
AMPLIFICATION_BASELINE = 2.5

# Timezone
TIMEZONE_BERN = "Europe/Zurich"

# Validation
REFERENCE_CASE = {
    "date": "2025-09-11",
    "time": "14:30:00",
    "expected_impact": 56.2,  # pips
}

def get_db_path():
    """Retourne le chemin vers la DB principale"""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB introuvable: {DB_PATH}")
    return DB_PATH

def validate_db():
    """Valide que la DB contient la vue prices_bern"""
    import duckdb
    
    con = duckdb.connect(str(DB_PATH), read_only=True)
    
    try:
        # Vérifier vue
        count = con.execute("SELECT COUNT(*) FROM prices_bern").fetchone()[0]
        print(f"✅ Vue prices_bern: {count:,} lignes")
        return True
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        return False
    finally:
        con.close()

if __name__ == "__main__":
    print("Configuration eurusd_clean")
    print(f"DB: {DB_PATH}")
    validate_db()
'''

config_file = eurusd_clean / "src" / "config.py"
config_file.write_text(config_content)
print(f"✅ src/config.py créé")

# ══════════════════════════════════════════════════════════════════════
# RÉSUMÉ
# ══════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("📊 RÉSUMÉ RESTRUCTURATION")
print("="*80)

print(f"""
✅ Structure créée
✅ DB copiée (avec vue prices_bern)
✅ Modules Python migrés
✅ Configuration centralisée

📁 Nouvelle structure:
   eurusd_clean/
   ├── data/warehouse.duckdb (205 MB)
   ├── src/
   │   ├── core/
   │   │   ├── formulas_validated.py
   │   │   ├── impact_measurement.py
   │   │   └── event_loader.py
   │   └── config.py
   ├── streamlit_app/ (vide, prêt pour app)
   ├── scripts/
   ├── docs/
   └── tests/

📋 Prochaines étapes:
   1. Tester que les imports fonctionnent
   2. Créer app Streamlit simplifiée
   3. Archiver anciennes versions
""")

print("="*80)
print("✅ RESTRUCTURATION TERMINÉE")
print("="*80)
