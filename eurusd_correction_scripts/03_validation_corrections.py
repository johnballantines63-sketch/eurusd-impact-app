#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATION CORRECTIONS - EUR/USD Trading App
Vérifie que les corrections sont appliquées correctement
"""

import os
import sys
import ast
import sqlite3
from pathlib import Path

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def valider_syntaxe_fichier(filepath):
    """Valide la syntaxe Python"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Ligne {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def verifier_formule_corrigee():
    """Vérifie que la formule est corrigée"""
    filepath = "fx_impact_app/4_Planificateur-Multi-Evenements.py"
    
    if not os.path.exists(filepath):
        return False, "Fichier introuvable"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifier la bonne formule
        if "impact = (mfe_p80 / 100) * abs(surprise" in contenu:
            return True, "Formule correcte détectée"
        elif "impact = mfe_p80 * (surprise / 10" in contenu:
            return False, "Ancienne formule toujours présente"
        else:
            return None, "Formule non trouvée"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def tester_imports():
    """Teste les imports requis"""
    modules = ['streamlit', 'pandas', 'numpy', 'plotly']
    resultats = []
    
    for module in modules:
        try:
            __import__(module)
            resultats.append((module, True))
        except ImportError:
            resultats.append((module, False))
    
    return resultats

def main():
    print_header("🔍 VALIDATION CORRECTIONS")
    
    # Test 1: Syntaxe
    print_info("Test 1/4 : Syntaxe Python...")
    fichiers = [
        "fx_impact_app/4_Planificateur-Multi-Evenements.py",
        "fx_impact_app/streamlit_app/Home.py"
    ]
    
    erreurs = 0
    for f in fichiers:
        if os.path.exists(f):
            ok, msg = valider_syntaxe_fichier(f)
            if ok:
                print_success(f"{os.path.basename(f)}: {msg}")
            else:
                print_error(f"{os.path.basename(f)}: {msg}")
                erreurs += 1
    
    # Test 2: Formule
    print_info("\nTest 2/4 : Formule predict_impact...")
    ok, msg = verifier_formule_corrigee()
    if ok:
        print_success(msg)
    elif ok is None:
        print_info(msg)
    else:
        print_error(msg)
        erreurs += 1
    
    # Test 3: Base de données
    print_info("\nTest 3/4 : Base de données...")
    db_path = "fx_impact_app/data/fx_events.db"
    if os.path.exists(db_path):
        print_success(f"Base trouvée ({os.path.getsize(db_path):,} bytes)")
    else:
        print_error("Base de données introuvable")
        erreurs += 1
    
    # Test 4: Modules
    print_info("\nTest 4/4 : Modules Python...")
    resultats = tester_imports()
    modules_ok = 0
    for module, ok in resultats:
        if ok:
            print_success(f"{module}")
            modules_ok += 1
        else:
            print_error(f"{module} manquant")
    
    # Résumé
    print_header("📊 RÉSUMÉ")
    
    if erreurs == 0 and modules_ok == len(resultats):
        print_success("VALIDATION RÉUSSIE !")
        print("\n💡 Prochaine étape:")
        print("   cd '/Users/andrevalentin/Desktop/eurusd_news_impact_calculator MPC'")
        print("   streamlit run fx_impact_app/streamlit_app/Home.py")
        return 0
    else:
        print_error(f"Validation incomplète ({erreurs} erreur(s))")
        if modules_ok < len(resultats):
            print_info("Installez les modules: pip install streamlit pandas numpy plotly")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        sys.exit(1)
