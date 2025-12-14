#!/usr/bin/env python3
"""
Script Session 19 : Modification COMPLÈTE pour importer TOUS les champs EODHD
=============================================================================

Basé sur l'inspection, l'API retourne 10 champs présents à 100% :
- date, country, actual, previous, estimate
- type, comparison, period, change, change_percentage

On modifie :
1. calendar_to_events_df() pour extraire TOUS les champs
2. Le schéma DB pour stocker TOUS les champs
3. La fonction upsert_events() pour gérer les nouveaux champs

Avantages :
- Plus de confusion forecast/estimate
- Données complètes pour analyses futures
- Pas de re-import nécessaire plus tard
- Debug plus facile
"""

import sys
from pathlib import Path
import shutil
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
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


def backup_code():
    """Backup du code avant modification"""
    print_step("Backup du code")
    
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"eodhd_client_before_full_import_{timestamp}.py"
    
    shutil.copy2(CODE_PATH, backup_path)
    print_success(f"Backup créé : {backup_path.name}")
    
    return True


def modify_calendar_to_events_df():
    """Modifie calendar_to_events_df pour extraire TOUS les champs"""
    print_step("Modification de calendar_to_events_df()")
    
    with open(CODE_PATH, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Vérifier que le marqueur SESSION 19 existe
    if 'SESSION 19' not in code:
        print_error("Le fix 'comparison' n'est pas appliqué. Appliquez-le d'abord.")
        return False
    
    # === MODIFICATION 1 : Extraire TOUS les champs (après comparison) ===
    
    find_text = '''    # ✅ SESSION 19 : Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")'''
    
    if find_text not in code:
        print_error("Marqueur 'comparison' introuvable")
        return False
    
    replace_text = '''    # ✅ SESSION 19 : Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")
    
    # ✅ SESSION 19 COMPLET : Extraire TOUS les autres champs EODHD
    period = _col(raw, "period").astype("string")
    change = pd.to_numeric(_col(raw, "change"), errors="coerce").astype("Float64")
    change_percentage = pd.to_numeric(_col(raw, "change_percentage"), errors="coerce").astype("Float64")
    event_type = _col(raw, "type").astype("string")  # Renommé car 'type' est déjà utilisé'''
    
    code = code.replace(find_text, replace_text)
    print_success("Extraction de tous les champs ajoutée")
    
    # === MODIFICATION 2 : Ajouter les champs au DataFrame ===
    
    find_df = '''    df = pd.DataFrame({
        "ts_utc": ts_utc,
        "country": country,
        "event_title": event_title.astype("string"),
        "event_key": event_key.astype("string"),
        "label": label.astype("string"),
        "type": typ.astype("string"),
        "estimate": estimate.astype("Float64"),
        "forecast": forecast.astype("Float64"),
        "previous": previous.astype("Float64"),
        "actual": actual.astype("Float64"),
        "unit": unit.astype("string"),
        "comparison": comparison,  # ✅ SESSION 19 : Ajout comparison
        "importance_n": importance_n,
    })'''
    
    if find_df not in code:
        print_error("Construction DataFrame introuvable")
        return False
    
    replace_df = '''    df = pd.DataFrame({
        "ts_utc": ts_utc,
        "country": country,
        "event_title": event_title.astype("string"),
        "event_key": event_key.astype("string"),
        "label": label.astype("string"),
        "type": typ.astype("string"),
        "estimate": estimate.astype("Float64"),
        "forecast": forecast.astype("Float64"),
        "previous": previous.astype("Float64"),
        "actual": actual.astype("Float64"),
        "unit": unit.astype("string"),
        "comparison": comparison,  # ✅ SESSION 19 : MoM/YoY/QoQ
        "period": period,  # ✅ SESSION 19 COMPLET : Période (Jan, Feb, Q1, etc.)
        "change": change,  # ✅ SESSION 19 COMPLET : Changement absolu
        "change_percentage": change_percentage,  # ✅ SESSION 19 COMPLET : Changement %
        "event_type": event_type,  # ✅ SESSION 19 COMPLET : Type d'événement EODHD
        "importance_n": importance_n,
    })'''
    
    code = code.replace(find_df, replace_df)
    print_success("Tous les champs ajoutés au DataFrame")
    
    # === MODIFICATION 3 : Garder tous les champs (ne pas drop comparison) ===
    
    find_drop = '''    # Supprimer colonne temporaire comparison
    df = df.drop(columns=['comparison'], errors='ignore')'''
    
    if find_drop in code:
        replace_drop = '''    # ✅ SESSION 19 COMPLET : On garde TOUS les champs maintenant
    # Pas de drop - tous les champs sont utiles'''
        
        code = code.replace(find_drop, replace_drop)
        print_success("Conservation de tous les champs activée")
    
    # Sauvegarder
    with open(CODE_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print_success(f"Code modifié : {CODE_PATH}")
    
    return True


def show_next_steps():
    """Affiche les prochaines étapes"""
    print_step("Prochaines étapes")
    
    print(f"""
{Colors.YELLOW}1. Modifier le schéma DB{Colors.END}
   Ajouter les colonnes à la table events :
   - comparison VARCHAR
   - period VARCHAR
   - change DOUBLE
   - change_percentage DOUBLE
   - event_type VARCHAR

{Colors.YELLOW}2. Modifier upsert_events(){Colors.END}
   Ajouter les nouveaux champs à :
   - _DB_COLS
   - _EVENTS_DDL

{Colors.YELLOW}3. Nettoyer et re-importer{Colors.END}
   python clean_and_reimport_session19.py

{Colors.BOLD}Note :{Colors.END} Je vais créer un script complet qui fait tout ça automatiquement.
    """)


def main():
    """Point d'entrée"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : Modification pour import COMPLET des champs EODHD{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Backup
    if not backup_code():
        return 1
    
    # Modification calendar_to_events_df
    if not modify_calendar_to_events_df():
        return 1
    
    # Afficher prochaines étapes
    show_next_steps()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ Modification calendar_to_events_df() terminée{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Étape 1/3 terminée. Passage à l'étape 2...{Colors.END}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
