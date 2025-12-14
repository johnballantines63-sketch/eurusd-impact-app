#!/usr/bin/env python3
"""
Script de Validation Post-Correction
Vérifie que les corrections ont été appliquées correctement

USAGE: python3 3_validation_corrections.py
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC")
PLANIFICATEUR = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

# ═══════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def test_impact_formula(content):
    """Vérifie formule d'impact"""
    
    bad = r'impact\s*=\s*\w+\s*\*\s*\(surprise\s*/\s*10(?:\.0)?\)'
    has_bad = bool(re.search(bad, content))
    
    good1 = r'surprise_pct\s*=\s*abs\(surprise\)\s*\*\s*100'
    good2 = r'impact_factor\s*=\s*min\(2\.0,\s*1\.0\s*\+\s*\(surprise_pct\s*/\s*50\.0\)\)'
    
    has_good1 = bool(re.search(good1, content))
    has_good2 = bool(re.search(good2, content))
    
    if has_bad:
        return False, "❌ Ancienne formule détectée"
    elif has_good1 and has_good2:
        return True, "✅ Nouvelle formule correcte"
    else:
        return None, "⚠️  Formule non standard"

def test_surprise_conversion(content):
    """Vérifie conversion surprise"""
    
    pattern = r'surprise_pct\s*=\s*abs\(surprise\)(?:\s*\*\s*100)?'
    matches = re.findall(pattern, content)
    
    if not matches:
        return None, "⚠️  Aucune conversion trouvée"
    
    bad = [m for m in matches if '* 100' not in m and '*100' not in m]
    
    if bad:
        return False, f"❌ {len(bad)} sans * 100"
    else:
        return True, f"✅ {len(matches)} correcte(s)"

def test_functions(content):
    """Vérifie fonctions prédiction"""
    
    funcs = []
    
    if re.search(r'def\s+predict_impact\(', content):
        funcs.append('predict_impact()')
    
    if re.search(r'def\s+predict_impact_fast\(', content):
        funcs.append('predict_impact_fast()')
    
    if not funcs:
        return False, "❌ Aucune fonction trouvée"
    
    return True, f"✅ {len(funcs)} fonction(s)"

def test_syntax(content):
    """Test basique syntaxe"""
    
    open_p = content.count('(')
    close_p = content.count(')')
    
    if open_p != close_p:
        return False, f"❌ Parenthèses ({open_p} vs {close_p})"
    
    return True, "✅ Équilibrage OK"

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print_header("✅ VALIDATION POST-CORRECTION")
    print(f"\n  Exécuté le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifier fichier
    if not PLANIFICATEUR.exists():
        print(f"\n  ❌ Fichier introuvable")
        sys.exit(1)
    
    print(f"\n  ✅ Fichier trouvé")
    
    # Lire
    try:
        content = read_file(PLANIFICATEUR)
        print(f"  ✅ {len(content):,} caractères")
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        sys.exit(1)
    
    # Tests
    print("\n" + "─"*70)
    print("  🔍 TESTS DE VALIDATION")
    print("─"*70 + "\n")
    
    tests = [
        ("Bug Impact Corrigé", test_impact_formula),
        ("Conversion Surprise", test_surprise_conversion),
        ("Fonctions Prédiction", test_functions),
        ("Syntaxe Basique", test_syntax),
    ]
    
    passed = 0
    failed = 0
    warnings = 0
    
    for test_name, test_func in tests:
        status, message = test_func(content)
        print(f"  {test_name:25s} : {message}")
        
        if status is True:
            passed += 1
        elif status is False:
            failed += 1
        else:
            warnings += 1
    
    # Résumé
    print_header("📊 RÉSUMÉ")
    
    total = len(tests)
    print(f"\n  Total tests        : {total}")
    print(f"  ✅ Réussis         : {passed}")
    print(f"  ❌ Échoués         : {failed}")
    print(f"  ⚠️  Avertissements  : {warnings}")
    
    print()
    
    if failed > 0:
        print("  ❌ VALIDATION ÉCHOUÉE")
        print("\n  💡 Relancer : python3 2_correction_automatique.py")
        sys.exit(1)
    elif warnings > 0:
        print("  ⚠️  VALIDATION PARTIELLE")
        sys.exit(2)
    else:
        print("  ✅ VALIDATION RÉUSSIE")
        print("\n  🎉 Tous les tests passés !")
        print("\n  📝 Tester l'application :")
        print("     cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC'")
        print("     streamlit run fx_impact_app/streamlit_app/Home.py")
        sys.exit(0)

if __name__ == "__main__":
    main()
