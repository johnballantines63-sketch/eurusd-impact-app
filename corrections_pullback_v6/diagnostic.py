#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC AUTOMATIQUE - État du générateur de courbes
Vérifie quelle version est actuellement active et son état
"""

import sys
from pathlib import Path
from datetime import datetime

def diagnostic():
    """Effectue un diagnostic complet de l'état actuel"""
    
    print("=" * 70)
    print("🔍 DIAGNOSTIC GÉNÉRATEUR DE COURBES EUR/USD")
    print("=" * 70)
    print()
    
    # Chemins
    project_root = Path(__file__).parent.parent
    generator_path = project_root / "fx_impact_app" / "src" / "price_curve_generator.py"
    backups_dir = project_root / "fx_impact_app" / "src" / "backups"
    
    # ============================================================
    # 1. VÉRIFIER EXISTENCE DU FICHIER
    # ============================================================
    print("📁 1. VÉRIFICATION FICHIER")
    print("-" * 70)
    
    if not generator_path.exists():
        print(f"❌ ERREUR : Fichier principal introuvable")
        print(f"   Chemin : {generator_path}")
        sys.exit(1)
    else:
        print(f"✅ Fichier principal trouvé")
        print(f"   Chemin : {generator_path}")
    print()
    
    # ============================================================
    # 2. IDENTIFIER LA VERSION ACTIVE
    # ============================================================
    print("🔎 2. IDENTIFICATION VERSION")
    print("-" * 70)
    
    content = generator_path.read_text(encoding='utf-8')
    
    # Chercher les marqueurs de version
    has_correction_v4 = "CORRECTION FINALE V4" in content
    has_correction_v5 = "AMÉLIORATION V5" in content
    has_correction_v6 = "CORRECTION V6" in content
    
    if has_correction_v6:
        version = "V6 (Pullback corrigé)"
        status = "✅"
        amplitude_expected = "~120-159 pips avec pullback réaliste"
    elif has_correction_v5:
        version = "V5 (Pullback bugué)"
        status = "❌"
        amplitude_expected = "~230 pips (dérive)"
    elif has_correction_v4:
        version = "V4 STABLE (avant pullback)"
        status = "✅"
        amplitude_expected = "~120-159 pips"
    else:
        version = "Version inconnue"
        status = "⚠️"
        amplitude_expected = "Inconnue"
    
    print(f"{status} Version active : {version}")
    print(f"   Amplitude attendue : {amplitude_expected}")
    print()
    
    # ============================================================
    # 3. VÉRIFIER STRUCTURE DU CODE PULLBACK
    # ============================================================
    print("🔧 3. STRUCTURE CODE PULLBACK")
    print("-" * 70)
    
    # Chercher le code problématique V5
    bug_pattern_v5 = "base_contribution -= pullback_amount * (1 if vectorial_impact_total > 0 else -1)"
    has_bug_v5 = bug_pattern_v5 in content
    
    # Chercher le code corrigé V6
    fix_pattern_v6 = "pullback_level = 1.0 - (0.35 * pullback_intensity)"
    has_fix_v6 = fix_pattern_v6 in content
    
    if has_bug_v5:
        print("❌ Bug 'double négatif' détecté (V5)")
        print("   Action : Appliquer correction V6 ou revenir à stable")
    elif has_fix_v6:
        print("✅ Correction V6 appliquée (modèle substitution)")
        print("   Pullback : Modèle de réduction propre")
    else:
        print("✅ Code stable (pas de pullback)")
        print("   Pattern : Mouvement simple sans retracement intermédiaire")
    print()
    
    # ============================================================
    # 4. LISTE DES BACKUPS DISPONIBLES
    # ============================================================
    print("💾 4. BACKUPS DISPONIBLES")
    print("-" * 70)
    
    if backups_dir.exists():
        backups = sorted(backups_dir.glob("price_curve_generator_*.py"))
        if backups:
            for backup in backups:
                size_kb = backup.stat().st_size / 1024
                modified = datetime.fromtimestamp(backup.stat().st_mtime)
                print(f"   • {backup.name}")
                print(f"     Taille : {size_kb:.1f} KB")
                print(f"     Modifié : {modified.strftime('%d/%m/%Y %H:%M:%S')}")
                print()
        else:
            print("   ⚠️  Aucun backup trouvé")
    else:
        print("   ⚠️  Répertoire backups inexistant")
    print()
    
    # ============================================================
    # 5. RECOMMANDATIONS
    # ============================================================
    print("💡 5. RECOMMANDATIONS")
    print("-" * 70)
    
    if has_bug_v5:
        print("❌ ACTION REQUISE : Bug détecté")
        print()
        print("   Option A : Revenir à version stable")
        print("   cd ~/Desktop/eurusd_news_impact_calculator_MPC")
        print("   cp fx_impact_app/src/backups/price_curve_generator_before_pullback_v5_*.py \\")
        print("      fx_impact_app/src/price_curve_generator.py")
        print()
        print("   Option B : Appliquer correction V6")
        print("   cd corrections_pullback_v6")
        print("   ./run_pullback_v6_correction.sh")
    elif has_fix_v6:
        print("✅ Correction V6 active")
        print()
        print("   1. Vider cache Python :")
        print("      find . -name '__pycache__' -exec rm -rf {} +")
        print()
        print("   2. Vider cache navigateur : Cmd+Shift+Del")
        print()
        print("   3. Tester :")
        print("      Date : 11/09/2025")
        print("      Prix : 1.16810")
        print("      Amplitude attendue : ~120-159 pips avec pullback")
    else:
        print("✅ Version stable active")
        print()
        print("   1. Vider cache Python :")
        print("      find . -name '__pycache__' -exec rm -rf {} +")
        print()
        print("   2. Vider cache navigateur : Cmd+Shift+Del")
        print()
        print("   3. Tester :")
        print("      Date : 11/09/2025")
        print("      Prix : 1.16810")
        print("      Amplitude attendue : ~120-159 pips")
    print()
    
    # ============================================================
    # 6. RÉSUMÉ
    # ============================================================
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"Version      : {version}")
    print(f"Status       : {status}")
    print(f"Amplitude    : {amplitude_expected}")
    print(f"Backups dispo: {len(backups) if backups_dir.exists() else 0}")
    print("=" * 70)

if __name__ == "__main__":
    diagnostic()
