#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTIC COMPLET - EUR/USD Trading App
Analyse SANS MODIFICATION du système
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def analyser_base_donnees():
    """Analyse la base de données"""
    db_path = Path("fx_impact_app/data/fx_events.db")
    
    if not db_path.exists():
        return {"status": "error", "message": "Base de données introuvable"}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Stats générales
        cursor.execute("SELECT COUNT(*) FROM price_data")
        nb_prix = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM economic_events")
        nb_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM event_classification")
        nb_classif = cursor.fetchone()[0]
        
        # Vérifier données récentes
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM price_data")
        min_date, max_date = cursor.fetchone()
        
        conn.close()
        
        return {
            "status": "ok",
            "nb_prix": nb_prix,
            "nb_events": nb_events,
            "nb_classif": nb_classif,
            "date_debut": min_date,
            "date_fin": max_date
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def rechercher_bug_formule():
    """Recherche le bug dans predict_impact"""
    planificateur = "fx_impact_app/4_Planificateur-Multi-Evenements.py"
    
    if not os.path.exists(planificateur):
        return {"found": False, "message": "Fichier Planificateur introuvable"}
    
    try:
        with open(planificateur, 'r', encoding='utf-8') as f:
            lignes = f.readlines()
        
        bugs_trouves = []
        for i, ligne in enumerate(lignes, 1):
            # Bug connu: mauvaise formule
            if "impact = mfe_p80 * (surprise / 10" in ligne:
                bugs_trouves.append({
                    "ligne": i,
                    "type": "CRITIQUE",
                    "code": ligne.strip(),
                    "probleme": "Formule incorrecte (division par 10)",
                    "solution": "impact = (mfe_p80 / 100) * abs(surprise)"
                })
        
        return {
            "found": len(bugs_trouves) > 0,
            "count": len(bugs_trouves),
            "bugs": bugs_trouves
        }
    except Exception as e:
        return {"found": False, "message": f"Erreur: {str(e)}"}

def main():
    print_header("🔍 DIAGNOSTIC COMPLET - EUR/USD TRADING APP")
    
    print("📅 Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("📁 Dossier:", os.getcwd())
    
    # 1. Base de données
    print_header("1️⃣  ANALYSE BASE DE DONNÉES")
    db_info = analyser_base_donnees()
    if db_info["status"] == "ok":
        print(f"✅ Base de données opérationnelle")
        print(f"   📊 Prix: {db_info['nb_prix']:,} enregistrements")
        print(f"   📰 Événements: {db_info['nb_events']:,}")
        print(f"   🏷️  Classifications: {db_info['nb_classif']:,}")
        print(f"   📅 Période: {db_info['date_debut']} → {db_info['date_fin']}")
    else:
        print(f"❌ Erreur DB: {db_info['message']}")
    
    # 2. Recherche bugs
    print_header("2️⃣  RECHERCHE BUGS CONNUS")
    bug_info = rechercher_bug_formule()
    if bug_info["found"]:
        print(f"❌ {bug_info['count']} BUG(S) DÉTECTÉ(S)\n")
        for bug in bug_info["bugs"]:
            print(f"   Ligne {bug['ligne']} - {bug['type']}")
            print(f"   Code actuel : {bug['code']}")
            print(f"   Problème    : {bug['probleme']}")
            print(f"   Solution    : {bug['solution']}\n")
    else:
        if "message" in bug_info:
            print(f"⚠️  {bug_info['message']}")
        else:
            print("✅ Aucun bug connu détecté")
    
    # 3. Structure fichiers
    print_header("3️⃣  VÉRIFICATION STRUCTURE")
    fichiers_cles = [
        "fx_impact_app/1_Collecteur-API-Economie.py",
        "fx_impact_app/2_Classificateur-Evenements.py",
        "fx_impact_app/3_Calculateur-TTR.py",
        "fx_impact_app/4_Planificateur-Multi-Evenements.py",
        "fx_impact_app/data/fx_events.db",
        "fx_impact_app/streamlit_app/Home.py"
    ]
    
    for fichier in fichiers_cles:
        if os.path.exists(fichier):
            taille = os.path.getsize(fichier)
            print(f"✅ {fichier} ({taille:,} bytes)")
        else:
            print(f"❌ {fichier} MANQUANT")
    
    # Résumé
    print_header("📊 RÉSUMÉ DIAGNOSTIC")
    
    if db_info["status"] == "ok":
        print("✅ Base de données: OK")
    else:
        print("❌ Base de données: PROBLÈME")
    
    if bug_info["found"]:
        print(f"❌ {bug_info['count']} bug(s) critique(s) détecté(s)")
        print("\n💡 PROCHAINE ÉTAPE:")
        print("   python3 02_correction_automatique.py")
    else:
        print("✅ Pas de bugs connus détectés")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostic interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        sys.exit(1)
