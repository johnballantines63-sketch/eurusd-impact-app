"""
Re-merge et re-import avec septembre corrigé

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
"""

import subprocess
import sys
from pathlib import Path
import time

def run_script(script_name: str, description: str):
    """Exécuter script Python"""
    
    print("=" * 80)
    print(f"▶️  {description}")
    print("=" * 80)
    print()
    
    script_path = Path(__file__).parent / script_name
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start
        print()
        print(f"✅ Terminé en {elapsed:.1f}s")
        print()
        return True
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Re-merge et re-import avec septembre corrigé"""
    
    print("=" * 80)
    print("RE-MERGE ET RE-IMPORT - SEPTEMBRE CORRIGÉ")
    print("=" * 80)
    print()
    print("🎯 Septembre EODHD corrigé:")
    print("   • 2,618 événements (vs 1,000 avant)")
    print("   • 122 événements 11 septembre")
    print("   • 20 événements US 11 septembre")
    print()
    print("Étapes:")
    print("   1. Re-copier septembre corrigé")
    print("   2. Re-merger sources (JBlanked + EODHD complet)")
    print("   3. Re-importer dans DB")
    print()
    
    input("Appuyez sur ENTRÉE pour continuer...")
    print()
    
    start_total = time.time()
    
    # ÉTAPE 1 : Copier septembre corrigé
    print("=" * 80)
    print("▶️  ÉTAPE 1/3 : Copie septembre corrigé")
    print("=" * 80)
    print()
    
    import shutil
    data_dir = Path(__file__).parent.parent.parent / 'data'
    
    monthly_file = data_dir / 'eodhd_2020_2025_monthly' / 'events_2025.json'
    all_file = data_dir / 'eodhd_2020_2025_monthly' / 'eodhd_all_2020_2025_monthly.json'
    
    # Recharger tout EODHD avec nouveau septembre
    print("🔄 Reconstruction fichier complet EODHD...")
    
    import json
    all_events = []
    
    for year in range(2020, 2026):
        year_file = data_dir / 'eodhd_2020_2025_monthly' / f'events_{year}.json'
        if year_file.exists():
            with open(year_file, 'r') as f:
                events = json.load(f)
                all_events.extend(events)
                print(f"   {year}: {len(events)} événements")
    
    with open(all_file, 'w') as f:
        json.dump(all_events, f, indent=2)
    
    print()
    print(f"✅ Fichier EODHD complet: {len(all_events)} événements")
    print()
    
    # Copier vers dossier principal
    main_dir = data_dir / 'eodhd_2020_2025'
    main_file = main_dir / 'eodhd_all_2020_2025.json'
    
    shutil.copy2(all_file, main_file)
    print(f"✅ Copié vers: {main_file}")
    print()
    
    # ÉTAPE 2 : Re-merger
    success = run_script(
        'merge_sources.py',
        'ÉTAPE 2/3 : Re-merge sources (JBlanked + EODHD complet)'
    )
    
    if not success:
        print("❌ Arrêt - Erreur merge")
        return
    
    # ÉTAPE 3 : Re-import DB
    success = run_script(
        'import_master_to_db.py',
        'ÉTAPE 3/3 : Re-import DB'
    )
    
    if not success:
        print("❌ Arrêt - Erreur import")
        return
    
    # Fin
    elapsed_total = time.time() - start_total
    
    print("=" * 80)
    print("✅ RE-MERGE ET RE-IMPORT TERMINÉS")
    print("=" * 80)
    print()
    print(f"⏱️  Durée totale: {elapsed_total:.1f}s")
    print()
    print("🎯 VÉRIFICATION FINALE:")
    print()
    
    # Vérifier DB
    import duckdb
    db_path = Path(__file__).parent.parent.parent / 'warehouse.duckdb'
    
    if db_path.exists():
        conn = duckdb.connect(str(db_path), read_only=True)
        
        total = conn.execute("SELECT COUNT(*) FROM economic_events").fetchone()[0]
        
        sept_11 = conn.execute("""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
        """).fetchone()[0]
        
        sept_11_usd = conn.execute("""
            SELECT COUNT(*) 
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            AND country = 'usd'
        """).fetchone()[0]
        
        print(f"📊 DB warehouse.duckdb:")
        print(f"   Total événements    : {total:,}")
        print(f"   11 septembre total  : {sept_11}")
        print(f"   11 septembre USD    : {sept_11_usd}")
        print()
        
        if sept_11_usd > 7:
            print(f"🎉 11 SEPTEMBRE AMÉLIORÉ !")
            print(f"   Avant : 7 événements USD (JBlanked seul)")
            print(f"   Après : {sept_11_usd} événements USD (JBlanked + EODHD)")
            print(f"   Gain  : +{sept_11_usd - 7} événements (+{(sept_11_usd-7)/7*100:.0f}%)")
        
        print()
        
        # Détail événements USD 11 sept
        print("   Événements USD 11 septembre:")
        events = conn.execute("""
            SELECT datetime_utc, event_name, source
            FROM economic_events
            WHERE DATE(datetime_utc) = '2025-09-11'
            AND country = 'usd'
            ORDER BY datetime_utc
        """).fetchall()
        
        for dt, name, source in events[:15]:
            print(f"      {dt} | {name:35s} | {source}")
        
        if len(events) > 15:
            print(f"      ... et {len(events)-15} autres")
        
        conn.close()
    
    print()
    print("=" * 80)
    print("🎉 SYSTÈME FINALISÉ AVEC SEPTEMBRE CORRIGÉ")
    print("=" * 80)


if __name__ == '__main__':
    main()
