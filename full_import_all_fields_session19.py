#!/usr/bin/env python3
"""
Script Session 19 : TOUT-EN-UN - Import COMPLET de tous les champs EODHD
=========================================================================

Ce script fait TOUT automatiquement :
1. Backup du code et de la DB
2. Modifie eodhd_client.py (calendar_to_events_df + upsert)
3. Modifie le schéma DB (ajout colonnes)
4. Nettoie la table events
5. Re-importe TOUT depuis 2023 avec TOUS les champs
6. Vérifie les résultats

Durée estimée : 60-75 minutes
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import duckdb

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

CODE_PATH = PROJECT_ROOT / "fx_impact_app" / "src" / "eodhd_client.py"
BACKUP_DIR = PROJECT_ROOT / "backups_session19"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(msg: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[STEP]{Colors.END} {msg}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


# =============================================================================
# ÉTAPE 1 : BACKUPS
# =============================================================================

def create_backups(db_path: Path) -> bool:
    """Crée tous les backups"""
    print_step("Backups de sécurité")
    
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup DB
    if db_path.exists():
        db_backup = BACKUP_DIR / f"warehouse_FULL_IMPORT_{timestamp}.duckdb"
        shutil.copy2(db_path, db_backup)
        size_mb = db_backup.stat().st_size / 1024 / 1024
        print_success(f"DB backup : {db_backup.name} ({size_mb:.1f} MB)")
    else:
        print_error("DB introuvable")
        return False
    
    # Backup code
    if CODE_PATH.exists():
        code_backup = BACKUP_DIR / f"eodhd_client_FULL_IMPORT_{timestamp}.py"
        shutil.copy2(CODE_PATH, code_backup)
        print_success(f"Code backup : {code_backup.name}")
    else:
        print_error("Code introuvable")
        return False
    
    return True


# =============================================================================
# ÉTAPE 2 : MODIFIER calendar_to_events_df()
# =============================================================================

def modify_calendar_to_events_df() -> bool:
    """Modifie pour extraire TOUS les champs"""
    print_step("Modification calendar_to_events_df()")
    
    with open(CODE_PATH, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Vérifier marqueur SESSION 19
    if 'SESSION 19' not in code:
        print_error("Fix 'comparison' non appliqué")
        return False
    
    # === MODIFICATION 1 : Extraire tous les champs ===
    
    find1 = '''    # ✅ SESSION 19 : Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")'''
    
    replace1 = '''    # ✅ SESSION 19 : Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")
    
    # ✅ SESSION 19 FULL : Extraire TOUS les autres champs EODHD
    period = _col(raw, "period").astype("string")
    change = pd.to_numeric(_col(raw, "change"), errors="coerce").astype("Float64")
    change_percentage = pd.to_numeric(_col(raw, "change_percentage"), errors="coerce").astype("Float64")
    event_type = _col(raw, "type").astype("string")  # 'type' EODHD (différent de 'category')'''
    
    if find1 in code:
        code = code.replace(find1, replace1)
        print_success("Extraction complète ajoutée")
    else:
        print_warning("Marqueur 'comparison' déjà modifié ou absent")
    
    # === MODIFICATION 2 : Ajouter au DataFrame ===
    
    find2 = '''        "comparison": comparison,  # ✅ SESSION 19 : Ajout comparison
        "importance_n": importance_n,
    })'''
    
    replace2 = '''        "comparison": comparison,  # ✅ SESSION 19 : MoM/YoY/QoQ
        "period": period,  # ✅ SESSION 19 FULL : Période
        "change": change,  # ✅ SESSION 19 FULL : Changement absolu
        "change_percentage": change_percentage,  # ✅ SESSION 19 FULL : Changement %
        "event_type": event_type,  # ✅ SESSION 19 FULL : Type événement EODHD
        "importance_n": importance_n,
    })'''
    
    if find2 in code:
        code = code.replace(find2, replace2)
        print_success("Champs ajoutés au DataFrame")
    else:
        print_warning("DataFrame déjà modifié ou structure différente")
    
    # === MODIFICATION 3 : Ne plus drop comparison ===
    
    find3 = '''    # Supprimer colonne temporaire comparison
    df = df.drop(columns=['comparison'], errors='ignore')'''
    
    replace3 = '''    # ✅ SESSION 19 FULL : On garde TOUS les champs
    # (plus de drop - tous les champs sont précieux)'''
    
    if find3 in code:
        code = code.replace(find3, replace3)
        print_success("Conservation de tous les champs activée")
    
    # Sauvegarder
    with open(CODE_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print_success("calendar_to_events_df() modifié")
    
    return True


# =============================================================================
# ÉTAPE 3 : MODIFIER upsert_events()
# =============================================================================

def modify_upsert_events() -> bool:
    """Modifie upsert pour gérer les nouveaux champs"""
    print_step("Modification upsert_events()")
    
    with open(CODE_PATH, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # === MODIFICATION 1 : Schéma DDL ===
    
    find_ddl = '''_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
  ts_utc TIMESTAMP WITH TIME ZONE,
  country VARCHAR,
  event_title VARCHAR,
  event_key VARCHAR,
  label VARCHAR,
  type VARCHAR,
  estimate DOUBLE,
  forecast DOUBLE,
  previous DOUBLE,
  actual DOUBLE,
  unit VARCHAR,
  importance_n BIGINT
);
"""'''
    
    replace_ddl = '''_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
  ts_utc TIMESTAMP WITH TIME ZONE,
  country VARCHAR,
  event_title VARCHAR,
  event_key VARCHAR,
  label VARCHAR,
  type VARCHAR,
  estimate DOUBLE,
  forecast DOUBLE,
  previous DOUBLE,
  actual DOUBLE,
  unit VARCHAR,
  comparison VARCHAR,
  period VARCHAR,
  change DOUBLE,
  change_percentage DOUBLE,
  event_type VARCHAR,
  importance_n BIGINT
);
"""'''
    
    if find_ddl in code:
        code = code.replace(find_ddl, replace_ddl)
        print_success("Schéma DDL mis à jour")
    else:
        print_warning("DDL déjà modifié ou structure différente")
    
    # === MODIFICATION 2 : Liste colonnes ===
    
    find_cols = '''_DB_COLS = [
    "ts_utc","country","event_title","event_key","label","type",
    "estimate","forecast","previous","actual","unit","importance_n"
]'''
    
    replace_cols = '''_DB_COLS = [
    "ts_utc","country","event_title","event_key","label","type",
    "estimate","forecast","previous","actual","unit",
    "comparison","period","change","change_percentage","event_type",
    "importance_n"
]'''
    
    if find_cols in code:
        code = code.replace(find_cols, replace_cols)
        print_success("Liste _DB_COLS mise à jour")
    else:
        print_warning("_DB_COLS déjà modifié ou structure différente")
    
    # Sauvegarder
    with open(CODE_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print_success("upsert_events() modifié")
    
    return True


# =============================================================================
# ÉTAPE 4 : MODIFIER SCHÉMA DB
# =============================================================================

def update_db_schema(db_path: str) -> bool:
    """Ajoute les nouvelles colonnes à la DB"""
    print_step("Mise à jour schéma DB")
    
    conn = duckdb.connect(db_path)
    
    new_columns = [
        ("comparison", "VARCHAR"),
        ("period", "VARCHAR"),
        ("change", "DOUBLE"),
        ("change_percentage", "DOUBLE"),
        ("event_type", "VARCHAR"),
    ]
    
    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}")
            print_success(f"Colonne ajoutée : {col_name} {col_type}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print_warning(f"Colonne {col_name} existe déjà")
            else:
                print_error(f"Erreur {col_name} : {e}")
                conn.close()
                return False
    
    conn.close()
    print_success("Schéma DB mis à jour")
    
    return True


# =============================================================================
# ÉTAPE 5 : NETTOYER ET RE-IMPORTER
# =============================================================================

def clear_and_reimport(db_path: str) -> bool:
    """Vide et re-importe tout"""
    print_step("Nettoyage + Re-import complet")
    
    from fx_impact_app.src.eodhd_client import (
        fetch_calendar_json,
        calendar_to_events_df,
        upsert_events_df
    )
    
    conn = duckdb.connect(db_path)
    
    # Compter avant
    count_before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"   Événements AVANT : {count_before:,}")
    
    # Nettoyer
    print_warning("   Suppression de toutes les données...")
    conn.execute("DELETE FROM events")
    
    count_after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print_success(f"   Table vidée : {count_after:,} événements")
    
    conn.close()
    
    # Re-import
    print("\n   Re-import 2023-2025 (peut prendre 45-60 min)...\n")
    
    START_DATE = '2023-01-01'
    END_DATE = '2025-10-19'
    COUNTRIES = ['US', 'EU', 'GB', 'DE', 'FR', 'JP', 'AU', 'ES', 'IT']
    
    # Générer plages
    date_ranges = []
    start = datetime.strptime(START_DATE, '%Y-%m-%d')
    end = datetime.strptime(END_DATE, '%Y-%m-%d')
    current = start
    
    while current <= end:
        chunk_end = min(current + timedelta(days=29), end)
        date_ranges.append((
            current.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d')
        ))
        current = chunk_end + timedelta(days=1)
    
    total_chunks = len(date_ranges)
    total_events = 0
    
    for i, (d1, d2) in enumerate(date_ranges, 1):
        try:
            pct = (i / total_chunks) * 100
            print(f"   [{i:>3}/{total_chunks}] {pct:>5.1f}% | {d1} → {d2} ... ", end='', flush=True)
            
            items = fetch_calendar_json(d1, d2, countries=COUNTRIES)
            
            if not items:
                print("⏭️  ", flush=True)
                continue
            
            df = calendar_to_events_df(items)
            
            if df.empty:
                print("⏭️  ", flush=True)
                continue
            
            n = upsert_events_df(df, db_path)
            total_events += n
            
            print(f"✅ {n:>4}", flush=True)
            
        except Exception as e:
            print(f"❌ {e}", flush=True)
    
    print(f"\n   Total importé : {total_events:,} événements")
    
    return True


# =============================================================================
# ÉTAPE 6 : VÉRIFICATION
# =============================================================================

def verify_results(db_path: str) -> bool:
    """Vérifie les résultats"""
    print_step("Vérification des résultats")
    
    conn = duckdb.connect(db_path)
    
    # Total
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    print(f"   Total événements : {total:,}")
    
    # Colonnes remplies
    for col in ['comparison', 'period', 'change', 'change_percentage', 'event_type']:
        count = conn.execute(f"SELECT COUNT(*) FROM events WHERE {col} IS NOT NULL").fetchone()[0]
        pct = (count / total * 100) if total > 0 else 0
        print(f"   {col:<20} : {count:>6,} ({pct:>5.1f}%)")
    
    # 11 septembre
    print("\n   Événements inflation 11 septembre :")
    result = conn.execute("""
        SELECT 
            event_key,
            actual,
            estimate,
            comparison,
            period
        FROM events
        WHERE DATE(ts_utc) = '2025-09-11'
          AND country = 'US'
          AND event_key LIKE '%inflation%'
        ORDER BY event_key
    """).fetchall()
    
    if result:
        for event_key, actual, estimate, comparison, period in result:
            act_str = f"{actual:.2f}" if actual else "N/A"
            est_str = f"{estimate:.2f}" if estimate else "N/A"
            comp_str = comparison or "N/A"
            per_str = period or "N/A"
            print(f"      {event_key:<40} | {act_str} vs {est_str} | {comp_str} | {per_str}")
    
    conn.close()
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : IMPORT COMPLET DE TOUS LES CHAMPS EODHD{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    from fx_impact_app.src.config import get_db_path
    db_path = get_db_path()
    
    # Confirmation
    print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  ATTENTION ⚠️{Colors.END}")
    print("Ce script va :")
    print("1. Modifier eodhd_client.py")
    print("2. Ajouter 5 colonnes à la table events")
    print("3. VIDER la table events")
    print("4. Re-importer TOUT depuis 2023 (60-75 min)")
    print("\nDes backups seront créés automatiquement.")
    
    response = input(f"\n{Colors.BOLD}Continuer ? (oui/non) : {Colors.END}")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Opération annulée.")
        return 1
    
    # Étape 1 : Backups
    if not create_backups(Path(db_path)):
        print_error("Échec backups")
        return 1
    
    # Étape 2 : Modifier calendar_to_events_df
    if not modify_calendar_to_events_df():
        print_error("Échec modification calendar_to_events_df")
        return 1
    
    # Étape 3 : Modifier upsert_events
    if not modify_upsert_events():
        print_error("Échec modification upsert_events")
        return 1
    
    # Étape 4 : Modifier schéma DB
    if not update_db_schema(db_path):
        print_error("Échec mise à jour schéma")
        return 1
    
    # Étape 5 : Nettoyer et re-importer
    if not clear_and_reimport(db_path):
        print_error("Échec re-import")
        return 1
    
    # Étape 6 : Vérification
    if not verify_results(db_path):
        print_error("Échec vérification")
        return 1
    
    # Succès
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ IMPORT COMPLET RÉUSSI !{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Prochaines étapes :{Colors.END}")
    print("1. Mettre à jour event_families (variantes MoM/YoY)")
    print("2. Re-valider Session 17")
    print("3. Documenter les nouveaux champs dans KNOWLEDGE_BASE.md")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\nInterrompu")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nErreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
