#!/usr/bin/env python3
"""
Script Session 19 : Application du fix 'comparison' (MoM/YoY/QoQ)
================================================================

PROBLÈME RÉSOLU :
-----------------
L'API EODHD retourne plusieurs versions d'un même indicateur :
- Inflation Rate (MoM) : actual=0.4, estimate=0.3 → Surprise 33%
- Inflation Rate (YoY) : actual=2.9, estimate=2.9 → Surprise 0%

Le code actuel ne les distingue pas → écrasement aléatoire.

SOLUTION :
----------
Utiliser le champ 'comparison' de l'API EODHD pour enrichir event_key :
- 'comparison': 'mom' → event_key devient 'inflation_rate_mom'
- 'comparison': 'yoy' → event_key devient 'inflation_rate_yoy'
- 'comparison': 'qoq' → event_key devient 'inflation_rate_qoq'

Ce script :
1. Crée backups (DB + code)
2. Modifie eodhd_client.py
3. Teste sur 11 septembre 2025
4. Vérifie que les 2 versions sont bien distinctes

Date : 19 octobre 2025
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "fx_impact_app" / "data" / "warehouse.duckdb"
CODE_PATH = PROJECT_ROOT / "fx_impact_app" / "src" / "eodhd_client.py"
BACKUP_DIR = PROJECT_ROOT / "backups_session19"

# Couleurs pour output
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
# STEP 1 : BACKUPS
# =============================================================================

def create_backups():
    """Crée backups de la DB et du code"""
    print_step("Création des backups de sécurité")
    
    # Créer dossier backups
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup DB
    if DB_PATH.exists():
        db_backup = BACKUP_DIR / f"warehouse_backup_{timestamp}.duckdb"
        shutil.copy2(DB_PATH, db_backup)
        print_success(f"DB sauvegardée : {db_backup.name}")
        print(f"   Taille : {db_backup.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print_error(f"DB introuvable : {DB_PATH}")
        return False
    
    # Backup code
    if CODE_PATH.exists():
        code_backup = BACKUP_DIR / f"eodhd_client_backup_{timestamp}.py"
        shutil.copy2(CODE_PATH, code_backup)
        print_success(f"Code sauvegardé : {code_backup.name}")
    else:
        print_error(f"Code introuvable : {CODE_PATH}")
        return False
    
    return True


# =============================================================================
# STEP 2 : MODIFICATION DU CODE
# =============================================================================

def apply_code_fix():
    """Applique le fix dans eodhd_client.py"""
    print_step("Application du fix 'comparison' dans eodhd_client.py")
    
    # Lire le code actuel
    with open(CODE_PATH, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Vérifier que le fix n'est pas déjà appliqué
    if 'comparison' in code and 'SESSION 19' in code:
        print_warning("Le fix semble déjà appliqué (marqueur 'SESSION 19' trouvé)")
        return True
    
    # === MODIFICATION 1 : Extraire le champ comparison ===
    
    # Trouver la ligne où unit est défini
    unit_line = 'unit = _col(raw, "unit", "unit_short", "units").astype("string")'
    
    if unit_line not in code:
        print_error("Ligne 'unit = ...' introuvable. Code modifié ?")
        return False
    
    # Ajouter extraction de comparison juste après unit
    comparison_extraction = '''unit = _col(raw, "unit", "unit_short", "units").astype("string")
    
    # ✅ SESSION 19 : Extraire comparison (mom, yoy, qoq)
    comparison = _col(raw, "comparison").astype("string")'''
    
    code = code.replace(unit_line, comparison_extraction)
    print_success("Extraction de 'comparison' ajoutée")
    
    # === MODIFICATION 2 : Ajouter comparison dans le DataFrame ===
    
    # Trouver la construction du DataFrame
    df_construction = '''df = pd.DataFrame({
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
        "importance_n": importance_n,
    })'''
    
    if df_construction not in code:
        print_error("Construction DataFrame introuvable. Code modifié ?")
        return False
    
    # Ajouter comparison dans le DataFrame
    df_with_comparison = '''df = pd.DataFrame({
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
    
    code = code.replace(df_construction, df_with_comparison)
    print_success("Colonne 'comparison' ajoutée au DataFrame")
    
    # === MODIFICATION 3 : Enrichir event_key avec comparison ===
    
    # Trouver le return final
    return_line = '    return df.reset_index(drop=True)'
    
    if return_line not in code:
        print_error("Ligne 'return df.reset_index(drop=True)' introuvable")
        return False
    
    # Ajouter enrichissement event_key AVANT le return
    enrichment_code = '''
    # ✅ SESSION 19 : Enrichir event_key avec comparison (mom/yoy/qoq)
    for idx in df.index:
        comp = df.at[idx, 'comparison']
        if pd.notna(comp):
            comp_lower = str(comp).lower().strip()
            event_key_current = str(df.at[idx, 'event_key']).lower().strip()
            
            # Ajouter suffixe si comparison valide et pas déjà présent
            if comp_lower in ['mom', 'yoy', 'qoq']:
                if comp_lower not in event_key_current:
                    df.at[idx, 'event_key'] = f"{event_key_current}_{comp_lower}"
    
    # Supprimer colonne temporaire comparison
    df = df.drop(columns=['comparison'], errors='ignore')
    
    return df.reset_index(drop=True)'''
    
    code = code.replace(return_line, enrichment_code)
    print_success("Enrichissement event_key ajouté")
    
    # Sauvegarder le code modifié
    with open(CODE_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print_success(f"Code modifié et sauvegardé : {CODE_PATH}")
    return True


# =============================================================================
# STEP 3 : TEST SUR 11 SEPTEMBRE 2025
# =============================================================================

def test_fix_sept11():
    """Teste le fix sur le cas problématique du 11 septembre"""
    print_step("Test du fix sur 11 septembre 2025")
    
    try:
        # Import APRÈS modification du code
        sys.path.insert(0, str(PROJECT_ROOT))
        from fx_impact_app.src.eodhd_client import fetch_calendar_json, calendar_to_events_df
        
        print("   Récupération données EODHD pour 11 septembre 2025...")
        data = fetch_calendar_json('2025-09-11', '2025-09-11', countries=['US'])
        
        if not data:
            print_error("Aucune donnée retournée par EODHD")
            return False
        
        print(f"   {len(data)} événements bruts récupérés")
        
        # Normaliser
        df = calendar_to_events_df(data)
        
        if df.empty:
            print_error("DataFrame vide après normalisation")
            return False
        
        print(f"   {len(df)} événements après normalisation")
        
        # Filtrer Inflation Rate
        inflation_events = df[
            df['event_key'].str.contains('inflation', case=False, na=False)
        ].copy()
        
        if inflation_events.empty:
            print_warning("Aucun événement 'inflation' trouvé")
            return False
        
        print(f"\n   📊 Événements Inflation Rate trouvés :")
        print(f"   {'event_key':<30} {'actual':>10} {'estimate':>10} {'surprise':>10}")
        print(f"   {'-'*65}")
        
        has_mom = False
        has_yoy = False
        
        for _, row in inflation_events.iterrows():
            event_key = row['event_key']
            actual = row.get('actual', None)
            estimate = row.get('estimate', None)
            
            # Calculer surprise
            if pd.notna(actual) and pd.notna(estimate) and estimate != 0:
                surprise = abs((actual - estimate) / estimate) * 100
            else:
                surprise = 0.0
            
            print(f"   {event_key:<30} {actual:>10} {estimate:>10} {surprise:>9.1f}%")
            
            # Vérifier présence des versions
            if '_mom' in event_key.lower():
                has_mom = True
            if '_yoy' in event_key.lower():
                has_yoy = True
        
        print()
        
        # Validation
        if has_mom and has_yoy:
            print_success("✅ Les versions MoM et YoY sont bien distinctes !")
            
            # Vérifier que MoM a une surprise significative
            mom_events = inflation_events[
                inflation_events['event_key'].str.contains('_mom', case=False, na=False)
            ]
            
            if not mom_events.empty:
                mom_row = mom_events.iloc[0]
                if pd.notna(mom_row.get('actual')) and pd.notna(mom_row.get('estimate')):
                    actual = float(mom_row['actual'])
                    estimate = float(mom_row['estimate'])
                    if estimate != 0:
                        surprise = abs((actual - estimate) / estimate) * 100
                        if surprise > 20:
                            print_success(f"✅ Surprise MoM significative : {surprise:.1f}%")
                            return True
        
        print_warning("Les versions MoM/YoY ne sont pas correctement séparées")
        return False
        
    except Exception as e:
        print_error(f"Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}SESSION 19 : Application du fix 'comparison' (MoM/YoY/QoQ){Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    
    # Step 1 : Backups
    if not create_backups():
        print_error("\nÉchec création backups. Abandon.")
        return 1
    
    # Step 2 : Modification code
    if not apply_code_fix():
        print_error("\nÉchec modification code. Abandon.")
        print_warning("Les backups sont disponibles dans backups_session19/")
        return 1
    
    # Step 3 : Test
    if not test_fix_sept11():
        print_error("\nÉchec test 11 septembre.")
        print_warning("Le code a été modifié. Vérifiez manuellement.")
        print_warning("Backups disponibles dans backups_session19/")
        return 1
    
    # Succès
    print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ FIX APPLIQUÉ AVEC SUCCÈS !{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Prochaines étapes :{Colors.END}")
    print("1. Re-import complet 2023-2025 :")
    print("   python fx_impact_app/scripts/ingest_eodhd_calendar.py \\")
    print("     --from 2023-01-01 --to 2025-10-19 \\")
    print("     --countries US EU GB DE FR JP AU ES IT")
    print("\n2. Mise à jour event_families (créer variantes MoM/YoY)")
    print("\n3. Re-validation Session 17 et cas 11 septembre")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
