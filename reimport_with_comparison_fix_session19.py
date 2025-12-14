#!/usr/bin/env python3
"""
Script Session 19 : Re-import complet avec fix 'comparison'
===========================================================

Maintenant que eodhd_client.py est corrigé pour distinguer MoM/YoY/QoQ,
on re-importe TOUTES les données depuis 2023.

Ce script :
1. Fait un backup de la DB actuelle
2. Re-importe 2023-01-01 → 2025-10-19
3. Vérifie que les nouvelles données contiennent bien _mom et _yoy
4. Compare avant/après

Temps estimé : 45-60 minutes
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess

# Chemins
PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
BACKUP_DIR = PROJECT_ROOT / "backups_session19"
INGEST_SCRIPT = PROJECT_ROOT / "fx_impact_app" / "scripts" / "ingest_eodhd_calendar.py"

# Couleurs
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
# STEP 1 : BACKUP DB (au cas où)
# =============================================================================

def backup_db():
    """Backup DB avant re-import"""
    print_step("Backup de la DB avant re-import")
    
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if DB_PATH.exists():
        db_backup = BACKUP_DIR / f"warehouse_before_reimport_{timestamp}.duckdb"
        shutil.copy2(DB_PATH, db_backup)
        size_mb = db_backup.stat().st_size / 1024 / 1024
        print_success(f"DB sauvegardée : {db_backup.name} ({size_mb:.1f} MB)")
        return True
    else:
        print_error(f"DB introuvable : {DB_PATH}")
        return False


# =============================================================================
# STEP 2 : STATISTIQUES AVANT RE-IMPORT
# =============================================================================

def get_db_stats():
    """Récupère stats DB avant re-import"""
    print_step("Statistiques DB AVANT re-import")
    
    try:
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH))
        
        # Total events
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        print(f"   Total événements : {total:,}")
        
        # Events avec _mom ou _yoy
        mom_yoy = conn.execute("""
            SELECT COUNT(*) FROM events 
            WHERE event_key LIKE '%_mom' 
               OR event_key LIKE '%_yoy'
               OR event_key LIKE '%_qoq'
        """).fetchone()[0]
        print(f"   Avec suffixe MoM/YoY/QoQ : {mom_yoy:,}")
        
        # Top event_keys avec inflation
        print("\n   Top 10 event_keys contenant 'inflation' :")
        result = conn.execute("""
            SELECT event_key, COUNT(*) as cnt
            FROM events
            WHERE event_key LIKE '%inflation%'
            GROUP BY event_key
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()
        
        for event_key, cnt in result:
            print(f"      {event_key:<40} {cnt:>5}")
        
        conn.close()
        
        return {
            'total': total,
            'mom_yoy': mom_yoy
        }
        
    except Exception as e:
        print_error(f"Erreur stats : {e}")
        return None


# =============================================================================
# STEP 3 : RE-IMPORT
# =============================================================================

def run_reimport():
    """Lance le re-import complet"""
    print_step("Re-import complet 2023-2025 (peut prendre 45-60 min)")
    
    if not INGEST_SCRIPT.exists():
        print_error(f"Script ingest introuvable : {INGEST_SCRIPT}")
        return False
    
    # Commande
    cmd = [
        sys.executable,
        str(INGEST_SCRIPT),
        "--from", "2023-01-01",
        "--to", "2025-10-19",
        "--countries", "US", "EU", "GB", "DE", "FR", "JP", "AU", "ES", "IT"
    ]
    
    print(f"\n   Commande : {' '.join(cmd)}\n")
    print("   ⏳ Import en cours... (peut prendre du temps)")
    print("   💡 Les logs défilent ci-dessous :\n")
    print("-" * 70)
    
    try:
        # Exécuter avec output en temps réel
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Afficher output en temps réel
        for line in process.stdout:
            print(f"   {line}", end='')
        
        process.wait()
        
        print("-" * 70)
        
        if process.returncode == 0:
            print_success("Re-import terminé avec succès")
            return True
        else:
            print_error(f"Erreur lors du re-import (code {process.returncode})")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors du re-import : {e}")
        return False


# =============================================================================
# STEP 4 : STATISTIQUES APRÈS RE-IMPORT
# =============================================================================

def compare_stats(stats_before):
    """Compare stats avant/après"""
    print_step("Statistiques DB APRÈS re-import")
    
    try:
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH))
        
        # Total events
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        print(f"   Total événements : {total:,}")
        
        # Events avec _mom ou _yoy
        mom_yoy = conn.execute("""
            SELECT COUNT(*) FROM events 
            WHERE event_key LIKE '%_mom' 
               OR event_key LIKE '%_yoy'
               OR event_key LIKE '%_qoq'
        """).fetchone()[0]
        print(f"   Avec suffixe MoM/YoY/QoQ : {mom_yoy:,}")
        
        # Top event_keys avec inflation
        print("\n   Top 10 event_keys contenant 'inflation' :")
        result = conn.execute("""
            SELECT event_key, COUNT(*) as cnt
            FROM events
            WHERE event_key LIKE '%inflation%'
            GROUP BY event_key
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()
        
        for event_key, cnt in result:
            print(f"      {event_key:<40} {cnt:>5}")
        
        # Comparaison
        if stats_before:
            print("\n   📊 COMPARAISON :")
            delta_total = total - stats_before['total']
            delta_mom_yoy = mom_yoy - stats_before['mom_yoy']
            
            print(f"      Total événements : {stats_before['total']:,} → {total:,} ({delta_total:+,})")
            print(f"      Avec MoM/YoY/QoQ : {stats_before['mom_yoy']:,} → {mom_yoy:,} ({delta_mom_yoy:+,})")
        
        conn.close()
        
        return mom_yoy > 0
        
    except Exception as e:
        print_error(f"Erreur stats : {e}")
        return False


# =============================================================================
# STEP 5 : VÉRIFICATION 11 SEPTEMBRE
# =============================================================================

def verify_sept11():
    """Vérifie que 11 septembre a bien les 2 versions"""
    print_step("Vérification cas 11 septembre 2025")
    
    try:
        import duckdb
        
        conn = duckdb.connect(str(DB_PATH))
        
        result = conn.execute("""
            SELECT 
                event_key,
                actual,
                estimate,
                CASE 
                    WHEN estimate IS NOT NULL AND estimate != 0 
                    THEN ABS((actual - estimate) / estimate) * 100
                    ELSE 0
                END as surprise_pct
            FROM events
            WHERE DATE(ts_utc) = '2025-09-11'
              AND event_key LIKE '%inflation%rate%'
            ORDER BY event_key
        """).fetchall()
        
        if not result:
            print_error("Aucun événement inflation trouvé pour 11 septembre")
            conn.close()
            return False
        
        print("\n   Événements Inflation Rate 11 septembre :")
        print(f"   {'Event Key':<40} {'Actual':>10} {'Estimate':>10} {'Surprise':>10}")
        print("   " + "-" * 75)
        
        has_mom = False
        has_yoy = False
        
        for event_key, actual, estimate, surprise in result:
            actual_str = f"{actual:.2f}" if actual is not None else "N/A"
            estimate_str = f"{estimate:.2f}" if estimate is not None else "N/A"
            surprise_str = f"{surprise:.1f}%" if surprise is not None else "N/A"
            
            print(f"   {event_key:<40} {actual_str:>10} {estimate_str:>10} {surprise_str:>10}")
            
            if '_mom' in event_key.lower():
                has_mom = True
            if '_yoy' in event_key.lower():
                has_yoy = True
        
        conn.close()
        
        if has_mom and has_yoy:
            print_success("\n   ✅ Les versions MoM et YoY sont présentes en DB")
            return True
        else:
            print_warning("\n   ⚠️  Versions MoM ou YoY manquantes")
            return False
        
    except Exception as e:
        print_error(f"Erreur vérification : {e}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : Re-import complet avec fix 'comparison'{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    # Step 1 : Backup
    if not backup_db():
        print_error("\nÉchec backup. Abandon.")
        return 1
    
    # Step 2 : Stats avant
    stats_before = get_db_stats()
    
    # Step 3 : Re-import
    print_warning("\n⏰ Le re-import va prendre 45-60 minutes.")
    print("   Vous pouvez suivre la progression ci-dessous.")
    
    if not run_reimport():
        print_error("\nÉchec re-import.")
        return 1
    
    # Step 4 : Stats après
    if not compare_stats(stats_before):
        print_error("\nÉchec comparaison stats.")
        return 1
    
    # Step 5 : Vérification 11 septembre
    if not verify_sept11():
        print_error("\nÉchec vérification 11 septembre.")
        return 1
    
    # Succès
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ RE-IMPORT COMPLET RÉUSSI !{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Prochaines étapes :{Colors.END}")
    print("1. Mettre à jour event_families (créer variantes MoM/YoY)")
    print("2. Re-valider Session 17 (MAE devrait s'améliorer)")
    print("3. Re-tester cas 11 septembre (erreur 29% → 13%)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
