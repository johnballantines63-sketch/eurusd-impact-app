"""
Workflow complet validation multi-dates

1. Scanner 2024-2025 avec DB 125k
2. Valider formules sur patterns détectés

Auteur : André Valentin avec Claude
Date : 09 novembre 2025
Session : 123
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
    
    if not script_path.exists():
        print(f"❌ Script non trouvé: {script_name}")
        return False
    
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
        print(f"✅ Terminé en {elapsed/60:.1f} min")
        print()
        return True
    
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        print()
        print(f"❌ Erreur après {elapsed/60:.1f} min")
        print(f"   Code: {e.returncode}")
        return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Workflow complet"""
    
    print("=" * 80)
    print("WORKFLOW VALIDATION MULTI-DATES - DB 125K")
    print("=" * 80)
    print()
    print("🎯 OBJECTIF:")
    print("   Valider formules S115 sur patterns 2024-2025")
    print("   avec DB EODHD 125k événements (vs 58k)")
    print()
    print("ÉTAPES:")
    print("   1. Scanner 2024-2025 (détection patterns)")
    print("   2. Validation formules (calcul MAE)")
    print()
    print("⏱️  Durée estimée: 45-60 minutes")
    print()
    
    input("Appuyez sur ENTRÉE pour démarrer...")
    print()
    
    start_total = time.time()
    
    # ÉTAPE 1 : Scanner
    success = run_script(
        'scan_2024_2025_db125k.py',
        'ÉTAPE 1/2 : Scanner 2024-2025 avec DB 125k'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur scan")
        return
    
    # ÉTAPE 2 : Validation
    success = run_script(
        'validate_formulas_multidates.py',
        'ÉTAPE 2/2 : Validation formules multi-dates'
    )
    
    if not success:
        print("❌ Workflow arrêté - Erreur validation")
        return
    
    # Fin
    elapsed_total = time.time() - start_total
    
    print("=" * 80)
    print("✅ WORKFLOW TERMINÉ")
    print("=" * 80)
    print()
    print(f"⏱️  Durée totale: {elapsed_total/60:.1f} minutes")
    print()
    print("📊 Fichiers créés:")
    print("   • scan_results/spikes_2024_2025_db125k.json")
    print("   • scan_results/double_waves_db125k.json")
    print("   • scan_results/validation_results.json")
    print()
    print("🎯 PROCHAINES ÉTAPES:")
    print("   1. Analyser validation_results.json")
    print("   2. Vérifier MAE moyen < 5 pips (objectif)")
    print("   3. Identifier outliers si nécessaire")
    print("   4. Ajuster formules si MAE > 5 pips")
    print()
    print("📋 OBJECTIF SESSION 123:")
    print("   ✅ DB 125k événements importée")
    print("   ✅ Re-scan 2024-2025 effectué")
    print("   ⏳ Validation formules (résultats à analyser)")
    print()

if __name__ == '__main__':
    main()
