#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECTION AUTOMATIQUE - EUR/USD Trading App
Corrige automatiquement les bugs avec backup et validation
"""

import os
import sys
import shutil
import ast
from datetime import datetime
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

def creer_backup(filepath):
    """Crée un backup avec timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{os.path.splitext(filepath)[0]}_backup_{timestamp}.py"
    
    try:
        shutil.copy2(filepath, backup_name)
        return True, backup_name
    except Exception as e:
        return False, str(e)

def valider_syntaxe(code):
    """Valide la syntaxe Python"""
    try:
        ast.parse(code)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Ligne {e.lineno}: {e.msg}"

def corriger_planificateur():
    """Corrige le bug dans le Planificateur"""
    filepath = "fx_impact_app/4_Planificateur-Multi-Evenements.py"
    
    if not os.path.exists(filepath):
        return {"success": False, "message": "Fichier introuvable"}
    
    # 1. Backup
    print_info("Création backup...")
    success, backup_path = creer_backup(filepath)
    if not success:
        return {"success": False, "message": f"Erreur backup: {backup_path}"}
    print_success(f"Backup: {os.path.basename(backup_path)}")
    
    # 2. Lire fichier
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenu = f.read()
    except Exception as e:
        return {"success": False, "message": f"Erreur lecture: {str(e)}"}
    
    # 3. Appliquer corrections
    contenu_original = contenu
    corrections_appliquees = []
    
    # Correction 1: Formule predict_impact
    ancienne_formule = "impact = mfe_p80 * (surprise / 10"
    nouvelle_formule = "impact = (mfe_p80 / 100) * abs(surprise"
    
    if ancienne_formule in contenu:
        contenu = contenu.replace(ancienne_formule, nouvelle_formule)
        corrections_appliquees.append("Formule predict_impact corrigée")
    
    # Vérifier si des corrections ont été faites
    if contenu == contenu_original:
        return {
            "success": True,
            "message": "Aucune correction nécessaire",
            "backup": backup_path,
            "corrections": 0
        }
    
    # 4. Valider syntaxe
    valide, msg = valider_syntaxe(contenu)
    if not valide:
        return {
            "success": False,
            "message": f"Erreur syntaxe après correction: {msg}",
            "backup": backup_path
        }
    
    # 5. Demander confirmation
    print_header("⚠️  CONFIRMATION REQUISE")
    print(f"Corrections à appliquer: {len(corrections_appliquees)}")
    for i, corr in enumerate(corrections_appliquees, 1):
        print(f"  {i}. {corr}")
    print(f"\nBackup créé: {os.path.basename(backup_path)}")
    
    reponse = input("\nAppliquer les corrections ? (o/n): ").strip().lower()
    if reponse != 'o':
        print_info("Corrections annulées")
        return {
            "success": False,
            "message": "Annulé par l'utilisateur",
            "backup": backup_path
        }
    
    # 6. Sauvegarder
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        return {
            "success": True,
            "message": "Corrections appliquées avec succès",
            "backup": backup_path,
            "corrections": len(corrections_appliquees),
            "details": corrections_appliquees
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur sauvegarde: {str(e)}",
            "backup": backup_path
        }

def main():
    print_header("🔧 CORRECTION AUTOMATIQUE - EUR/USD TRADING APP")
    
    print("📅 Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("📁 Dossier:", os.getcwd())
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists("fx_impact_app"):
        print_error("Erreur: Dossier fx_impact_app introuvable")
        print_info("Lancez ce script depuis: eurusd_news_impact_calculator MPC/")
        return 1
    
    # Correction Planificateur
    print_header("🔧 CORRECTION PLANIFICATEUR")
    resultat = corriger_planificateur()
    
    if resultat["success"]:
        print_success(resultat["message"])
        if resultat.get("corrections", 0) > 0:
            print(f"\n📝 {resultat['corrections']} correction(s) appliquée(s):")
            for detail in resultat.get("details", []):
                print(f"   • {detail}")
            print(f"\n💾 Backup disponible: {resultat['backup']}")
            print("\n✨ CORRECTIONS TERMINÉES")
            print("\n💡 Prochaine étape:")
            print("   python3 03_validation_corrections.py")
            return 0
        else:
            print_info("Code déjà corrigé")
            return 0
    else:
        print_error(resultat["message"])
        if "backup" in resultat:
            print_info(f"Backup disponible: {resultat['backup']}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Correction interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
