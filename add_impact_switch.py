#!/usr/bin/env python3
"""
🔧 Ajout du Switch Impact - Patch Final
Ajoute uniquement le switch manquant entre impact_calendar et impact_empirical

Usage:
    python add_impact_switch.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def backup_file(filepath: Path) -> Path:
    """Crée un backup"""
    backup_dir = filepath.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.stem}_{timestamp}.backup"
    shutil.copy2(filepath, backup_path)
    return backup_path

def add_switch():
    """Ajoute le switch impact dans le bon endroit"""
    filepath = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not filepath.exists():
        print(f"❌ Fichier introuvable")
        return False
    
    backup_file(filepath)
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Stratégie : Chercher le bouton "Analyser la Période" ou équivalent
    # et insérer le switch juste après le chargement des données
    
    print("🔍 Recherche du point d'insertion...")
    
    # Pattern 1 : Chercher "if st.sidebar.button" (déclencheur d'analyse)
    button_idx = None
    for i, line in enumerate(lines):
        if 'st.sidebar.button' in line and ('Analyser' in line or 'Charger' in line):
            button_idx = i
            print(f"✅ Bouton d'analyse trouvé ligne {i + 1}")
            break
    
    if not button_idx:
        # Pattern 2 : Chercher "with st.spinner" (chargement de données)
        for i, line in enumerate(lines):
            if 'with st.spinner' in line and 'événement' in line.lower():
                button_idx = i - 5
                print(f"✅ Spinner trouvé ligne {i + 1}")
                break
    
    if button_idx:
        # Chercher où les données sont chargées/utilisées
        # On cherche "future_events" ou "df" ou "events"
        
        data_loaded_idx = None
        for i in range(button_idx, min(button_idx + 100, len(lines))):
            # Chercher une ligne qui assigne à une variable df/events
            if ('= get_future_events' in lines[i] or 
                '= load_' in lines[i] or
                'events = ' in lines[i] or
                'df = ' in lines[i]):
                data_loaded_idx = i
                print(f"✅ Chargement données ligne {i + 1}")
                break
        
        if data_loaded_idx:
            # Trouver l'indentation
            indent_level = len(lines[data_loaded_idx]) - len(lines[data_loaded_idx].lstrip())
            indent = ' ' * indent_level
            
            # Vérifier qu'on n'a pas déjà le switch
            has_switch = False
            for i in range(data_loaded_idx, min(data_loaded_idx + 20, len(lines))):
                if 'impact_empirical' in lines[i] or 'impact_calendar' in lines[i]:
                    has_switch = True
                    print("ℹ️  Switch déjà présent")
                    break
            
            if not has_switch:
                # Insérer le switch juste après le chargement
                insert_idx = data_loaded_idx + 1
                
                # Trouver le nom de la variable (df, events, etc.)
                var_name = 'df'
                if '=' in lines[data_loaded_idx]:
                    var_name = lines[data_loaded_idx].split('=')[0].strip()
                
                switch_code = f"""
{indent}# === Switch Classification (Calendrier vs Empirique) ===
{indent}if use_empirical:
{indent}    {var_name}['impact'] = {var_name}['impact_empirical'].fillna('Unknown')
{indent}else:
{indent}    {var_name}['impact'] = {var_name}['impact_calendar']
{indent}# === Fin Switch ===
"""
                
                lines.insert(insert_idx, switch_code)
                print(f"✅ Switch ajouté après ligne {insert_idx}")
                
                # Sauvegarder
                content_new = '\n'.join(lines)
                filepath.write_text(content_new, encoding='utf-8')
                print(f"💾 Fichier sauvegardé")
                
                return True
    
    # Si on arrive ici, on n'a pas trouvé le bon endroit
    print("\n⚠️  Impossible de trouver le bon emplacement automatiquement")
    print("\n📝 AJOUT MANUEL REQUIS:")
    print("\n1. Ouvre: fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    print("\n2. Cherche la ligne où les événements sont chargés, par exemple:")
    print("   - future_events = get_future_events(...)")
    print("   - df = load_all_events(...)")
    print("   - events = conn.execute(...).fetchdf()")
    print("\n3. Juste APRÈS cette ligne, ajoute:")
    print("""
    # === Switch Classification ===
    if use_empirical:
        df['impact'] = df['impact_empirical'].fillna('Unknown')
    else:
        df['impact'] = df['impact_calendar']
    # === Fin Switch ===
""")
    print("\n4. Remplace 'df' par le nom de ta variable si différent")
    
    return False

def verify():
    """Vérifie la présence du switch"""
    filepath = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    content = filepath.read_text(encoding='utf-8')
    
    has_empirical = 'impact_empirical' in content
    has_calendar = 'impact_calendar' in content
    
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION")
    print("="*70)
    
    if has_empirical and has_calendar:
        print("\n✅ Switch impact présent !")
        print("✅ impact_empirical trouvé")
        print("✅ impact_calendar trouvé")
        return True
    else:
        print("\n❌ Switch impact manquant")
        if not has_empirical:
            print("❌ impact_empirical absent")
        if not has_calendar:
            print("❌ impact_calendar absent")
        return False

def main():
    print("="*70)
    print("🔧 AJOUT SWITCH IMPACT - Patch Final")
    print("="*70)
    print()
    
    if not Path("fx_impact_app").exists():
        print("❌ Lancez depuis la racine du projet")
        return
    
    print("🎯 Ajout du switch manquant entre impact_calendar et impact_empirical\n")
    
    if add_switch():
        if verify():
            print("\n" + "="*70)
            print("🎉 SUCCÈS ! Switch ajouté")
            print("="*70)
            print("\n📝 Test:")
            print("   streamlit run fx_impact_app/streamlit_app/Home.py")
        else:
            print("\n⚠️  Ajout effectué mais vérification échouée")
    else:
        print("\n💡 Suivez les instructions ci-dessus pour ajout manuel")

if __name__ == "__main__":
    main()
