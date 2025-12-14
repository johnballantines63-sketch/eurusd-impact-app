#!/usr/bin/env python3
"""
🔧 Ajout Toggle Classification - Calendrier Trading
Ajoute la double classification (Calendrier/Empirique) de manière chirurgicale

Usage:
    python add_classification_toggle.py

Modifications:
    - Ajoute toggle dans sidebar
    - Switch entre impact_calendar et impact_empirical
    - Adapte filtres et statistiques
"""

from pathlib import Path
import shutil
from datetime import datetime
import re

def backup_file(filepath: Path) -> Path:
    """Crée un backup avec timestamp"""
    backup_dir = filepath.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{filepath.stem}_{timestamp}.backup"
    
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup créé: {backup_path}")
    return backup_path

def add_classification_toggle():
    """Ajoute le toggle de classification au Calendrier Trading"""
    filepath = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not filepath.exists():
        print(f"❌ Fichier introuvable: {filepath}")
        return False
    
    # Backup
    backup_file(filepath)
    
    # Lire contenu
    content = filepath.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # === MODIFICATION 1 : Toggle dans sidebar ===
    
    # Trouver la ligne avec st.sidebar.header
    sidebar_header_idx = None
    for i, line in enumerate(lines):
        if 'st.sidebar.header("⚙️ Configuration")' in line:
            sidebar_header_idx = i
            break
    
    if sidebar_header_idx is None:
        print("❌ Impossible de trouver st.sidebar.header")
        return False
    
    # Insérer le toggle juste après
    toggle_code = '''
# Classification
st.sidebar.subheader("📊 Classification")
classification_mode = st.sidebar.radio(
    "Source d'importance",
    ["📅 Calendrier (a priori)", "📊 Empirique (historique)"],
    index=0,
    help=(
        "📅 **Calendrier** : Importance théorique selon économistes\\n\\n"
        "📊 **Empirique** : Impact réel observé sur EUR/USD (3 ans)"
    )
)

st.sidebar.divider()
'''
    
    lines.insert(sidebar_header_idx + 1, toggle_code)
    print("✅ Modification 1/4: Toggle ajouté dans sidebar")
    
    # === MODIFICATION 2 : Switch impact après chargement ===
    
    # Trouver load_all_events_cached
    load_events_idx = None
    for i, line in enumerate(lines):
        if 'def load_all_events_cached' in line:
            load_events_idx = i
            break
    
    if load_events_idx:
        # Trouver la fin de la fonction (prochain 'def' ou ligne vide après return)
        func_end_idx = None
        for i in range(load_events_idx + 1, len(lines)):
            if lines[i].strip().startswith('def ') or \
               (lines[i].strip() == '' and i > load_events_idx + 20):
                func_end_idx = i
                break
        
        if func_end_idx:
            switch_code = '''
# === Switch Classification ===
# Ajouté automatiquement par add_classification_toggle.py
use_empirical = classification_mode == "📊 Empirique (historique)"

if use_empirical:
    df_all['impact'] = df_all['impact_empirical']
    # Gérer les Unknown
    df_all['impact'] = df_all['impact'].fillna('Unknown')
else:
    df_all['impact'] = df_all['impact_calendar']
# === Fin Switch ===
'''
            lines.insert(func_end_idx, switch_code)
            print("✅ Modification 2/4: Switch impact ajouté")
        else:
            print("⚠️  Modification 2/4: Impossible de trouver fin de fonction")
    else:
        print("⚠️  Modification 2/4: load_all_events_cached non trouvée")
    
    # === MODIFICATION 3 : Adapter statistiques High Impact ===
    
    # Trouver le calcul de high_impact (ligne avec "len(df_all[df_all['impact']")
    stats_idx = None
    for i, line in enumerate(lines):
        if "high_impact = len(df_all[df_all['impact']" in line:
            stats_idx = i
            break
    
    if stats_idx:
        # Remplacer par version conditionnelle
        old_line = lines[stats_idx]
        indent = len(old_line) - len(old_line.lstrip())
        indent_str = ' ' * indent
        
        stats_code = f'''{indent_str}# Adapter selon classification
{indent_str}if use_empirical:
{indent_str}    high_impact = len(df_all[df_all['impact'] == 'HIGH'])
{indent_str}    unknown = len(df_all[df_all['impact'] == 'Unknown'])
{indent_str}else:
{indent_str}    high_impact = len(df_all[df_all['impact'] == 'High'])
{indent_str}    unknown = 0'''
        
        lines[stats_idx] = stats_code
        print("✅ Modification 3/4: Statistiques adaptées")
    else:
        print("⚠️  Modification 3/4: Calcul high_impact non trouvé")
    
    # === MODIFICATION 4 : Adapter options filtres ===
    
    # Trouver le multiselect Impact
    filter_idx = None
    for i, line in enumerate(lines):
        if 'st.sidebar.multiselect' in line and 'Impact' in lines[i+1]:
            filter_idx = i
            break
    
    if filter_idx:
        # Chercher la ligne avec les options (souvent 2-3 lignes plus bas)
        for j in range(filter_idx, min(filter_idx + 10, len(lines))):
            if "['High', 'Medium', 'Low']" in lines[j] or \
               "['HIGH', 'MEDIUM', 'LOW']" in lines[j]:
                
                indent = len(lines[j]) - len(lines[j].lstrip())
                indent_str = ' ' * indent
                
                # Insérer avant le multiselect
                options_code = f'''{indent_str}# Options selon mode
{indent_str}if use_empirical:
{indent_str}    impact_options = ['HIGH', 'MEDIUM', 'LOW', 'Unknown']
{indent_str}else:
{indent_str}    impact_options = ['High', 'Medium', 'Low']
{indent_str}'''
                
                lines.insert(filter_idx, options_code)
                
                # Remplacer la ligne d'options hardcodées par impact_options
                lines[j + 4] = lines[j + 4].replace(
                    "['High', 'Medium', 'Low']",
                    "impact_options"
                ).replace(
                    "['HIGH', 'MEDIUM', 'LOW']",
                    "impact_options"
                )
                
                print("✅ Modification 4/4: Filtres adaptés")
                break
    else:
        print("⚠️  Modification 4/4: Multiselect Impact non trouvé")
    
    # === MODIFICATION 5 : Affichage dans display_event_card ===
    
    # Trouver display_event_card (si elle existe)
    card_idx = None
    for i, line in enumerate(lines):
        if 'def display_event_card' in line:
            card_idx = i
            break
    
    if card_idx:
        # Chercher l'affichage de l'impact dans la fonction
        for i in range(card_idx, min(card_idx + 100, len(lines))):
            if "'impact']" in lines[i] and 'st.write' in lines[i]:
                indent = len(lines[i]) - len(lines[i].lstrip())
                indent_str = ' ' * indent
                
                # Ajouter affichage score si empirique
                score_code = f'''
{indent_str}# Afficher score si mode empirique et disponible
{indent_str}if use_empirical and pd.notna(event.get('empirical_score')):
{indent_str}    score = event['empirical_score']
{indent_str}    st.caption(f"Score: {{score:.0f}}/100")
'''
                lines.insert(i + 1, score_code)
                print("✅ Modification 5/5: Affichage score dans cards")
                break
    
    # Écrire le fichier modifié
    content_new = '\n'.join(lines)
    filepath.write_text(content_new, encoding='utf-8')
    print(f"💾 Sauvegardé: {filepath}\n")
    
    return True

def verify_modifications():
    """Vérifie que les modifications sont présentes"""
    print("\n🔍 VÉRIFICATION DES MODIFICATIONS\n")
    
    filepath = Path("fx_impact_app/streamlit_app/pages/1_Calendrier-Trading.py")
    
    if not filepath.exists():
        print("❌ Fichier introuvable")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    
    checks = [
        ("classification_mode", "Toggle classification présent"),
        ("use_empirical", "Variable use_empirical présente"),
        ("impact_empirical", "Utilisation impact_empirical"),
        ("impact_calendar", "Utilisation impact_calendar"),
        ("impact_options", "Options dynamiques présentes")
    ]
    
    all_ok = True
    for pattern, description in checks:
        if pattern in content:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - MANQUANT")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 70)
    print("🔧 AJOUT TOGGLE CLASSIFICATION - Calendrier Trading")
    print("=" * 70)
    print()
    
    # Vérifier emplacement
    if not Path("fx_impact_app").exists():
        print("❌ ERREUR: Lancez depuis la racine du projet")
        return
    
    print("📋 Modifications prévues:")
    print("   1. Toggle Classification dans sidebar")
    print("   2. Switch impact_calendar / impact_empirical")
    print("   3. Adapter statistiques High Impact")
    print("   4. Adapter filtres (High/HIGH selon mode)")
    print("   5. Affichage score empirique dans cards")
    print()
    
    input("Appuyez sur ENTRÉE pour continuer...")
    print()
    
    # Appliquer modifications
    if add_classification_toggle():
        if verify_modifications():
            print("\n" + "=" * 70)
            print("🎉 SUCCÈS ! Toggle Classification ajouté")
            print("=" * 70)
            print()
            print("📝 Prochaines étapes:")
            print("   1. Tester: streamlit run fx_impact_app/streamlit_app/Home.py")
            print("   2. Aller sur 'Calendrier Trading'")
            print("   3. Vérifier le toggle 📊 Classification dans la sidebar")
            print("   4. Tester les deux modes (Calendrier / Empirique)")
            print()
            print("💡 Attendu:")
            print("   - Mode Calendrier: High/Medium/Low (données théoriques)")
            print("   - Mode Empirique: HIGH/MEDIUM/LOW/Unknown (données réelles)")
            print()
            print("💾 Backup: fx_impact_app/streamlit_app/pages/backups/")
        else:
            print("\n⚠️  Vérification: Certaines modifications manquent")
            print("   → Vérification manuelle recommandée")
    else:
        print("\n❌ Erreur lors de l'application des modifications")

if __name__ == "__main__":
    main()
