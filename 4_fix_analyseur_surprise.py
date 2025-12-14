#!/usr/bin/env python3
"""
Correction Analyseur Surprise - Utiliser previous au lieu de forecast
Modifie la page Streamlit pour fonctionner sans forecast
"""

import shutil
from pathlib import Path

SURPRISE_PAGE = Path("fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py")
BACKUP_PAGE = Path("fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py.backup")


def backup_page():
    """Sauvegarde la page originale"""
    if SURPRISE_PAGE.exists():
        shutil.copy2(SURPRISE_PAGE, BACKUP_PAGE)
        print(f"✓ Sauvegarde créée: {BACKUP_PAGE}")
        return True
    print(f"❌ Page non trouvée: {SURPRISE_PAGE}")
    return False


def fix_surprise_analyzer():
    """Corrige le code pour utiliser previous"""
    
    if not SURPRISE_PAGE.exists():
        print(f"❌ Fichier non trouvé: {SURPRISE_PAGE}")
        return False
    
    with open(SURPRISE_PAGE, 'r') as f:
        content = f.read()
    
    # Remplacements
    replacements = [
        # Requête SQL
        (
            "WHERE forecast IS NOT NULL",
            "WHERE previous IS NOT NULL"
        ),
        # Affichage dans interface
        (
            "st.number_input('Consensus (Forecast)'",
            "st.number_input('Référence (Previous)'"
        ),
        # Calcul surprise
        (
            "surprise = actual - forecast",
            "surprise = actual - previous  # Utilise previous comme référence"
        ),
        # Messages
        (
            "forecast",
            "previous"
        ),
        # Titre colonne
        (
            "'Forecast'",
            "'Previous'"
        ),
    ]
    
    modified = content
    changes = 0
    
    for old, new in replacements:
        if old in modified:
            modified = modified.replace(old, new)
            changes += 1
    
    if changes > 0:
        with open(SURPRISE_PAGE, 'w') as f:
            f.write(modified)
        
        print(f"\n✅ Fichier modifié: {SURPRISE_PAGE}")
        print(f"   {changes} remplacements effectués")
        return True
    
    print("⚠️  Aucune modification nécessaire")
    return False


def add_warning_note():
    """Ajoute une note explicative en haut de la page"""
    
    with open(SURPRISE_PAGE, 'r') as f:
        lines = f.readlines()
    
    # Trouver première ligne après imports
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('st.'):
            insert_pos = i
            break
    
    warning = '''
# Note sur les données
st.info("""
📊 **Note importante** : Cette analyse utilise la valeur `previous` comme référence 
au lieu de `forecast`, car l'API EODHD gratuite ne fournit pas les consensus.

La formule devient : **Surprise = Actual - Previous**

Cela reste pertinent pour analyser l'impact historique des événements.
""")

'''
    
    lines.insert(insert_pos, warning)
    
    with open(SURPRISE_PAGE, 'w') as f:
        f.writelines(lines)
    
    print("✓ Note explicative ajoutée")


def verify_changes():
    """Vérifie que les changements sont corrects"""
    
    with open(SURPRISE_PAGE, 'r') as f:
        content = f.read()
    
    checks = [
        ('previous IS NOT NULL', '✓ Requête SQL corrigée'),
        ('Previous', '✓ Interface utilisateur adaptée'),
        ('actual - previous', '✓ Calcul surprise mis à jour'),
    ]
    
    print("\n📋 Vérification des modifications:")
    all_ok = True
    
    for pattern, message in checks:
        if pattern in content:
            print(f"  {message}")
        else:
            print(f"  ❌ Manque: {pattern}")
            all_ok = False
    
    return all_ok


def main():
    print("🔧 CORRECTION ANALYSEUR SURPRISE")
    print("=" * 60)
    print("\nAdaptation pour fonctionner sans forecast (utilise previous)")
    print()
    
    # Sauvegarde
    if not backup_page():
        return
    
    # Corrections
    if fix_surprise_analyzer():
        add_warning_note()
        
        # Vérification
        if verify_changes():
            print("\n" + "=" * 60)
            print("✅ CORRECTION TERMINÉE")
            print("\nL'Analyseur Surprise utilise maintenant 'previous' comme référence.")
            print("\n📋 TESTER:")
            print("  streamlit run fx_impact_app/streamlit_app/pages/3_Analyseur-Surprise.py")
            print("\n💾 Restaurer original si besoin:")
            print(f"  cp {BACKUP_PAGE} {SURPRISE_PAGE}")
        else:
            print("\n⚠️  Vérification échouée - vérifier manuellement")
    else:
        print("\n❌ Correction échouée")


if __name__ == '__main__':
    main()
