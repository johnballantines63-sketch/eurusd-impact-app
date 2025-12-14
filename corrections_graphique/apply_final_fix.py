#!/usr/bin/env python3
"""
Correction Automatique Finale : Graphique Amplitude Réelle
Date : 14 Octobre 2025
"""

import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
PLANIFICATEUR_FILE = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
BACKUP_DIR = PROJECT_ROOT / "corrections_graphique/backups"

def create_backup():
    """Créer backup"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"4_Planificateur_before_final_fix_{timestamp}.py"
    
    with open(PLANIFICATEUR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Backup : {backup_file.name}")
    return backup_file

def apply_corrections():
    """Appliquer toutes les corrections possibles"""
    
    with open(PLANIFICATEUR_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    corrections_applied = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # CORRECTION 1 : Dans section graphique, remplacer sum() par observed_movement
    # ═══════════════════════════════════════════════════════════════════════
    
    # Pattern : Après calcul de observed_movement, chercher les sum(predicted_pips)
    pattern1 = r'(observed_movement\s*=\s*max_movement.*?$)(\s+.*?)(sum\([^)]*predicted_pips[^)]*\))'
    
    def replace_sum_after_observed(match):
        """Remplacer sum() par abs(observed_movement) APRÈS calcul observed_movement"""
        before = match.group(1)  # Ligne observed_movement
        middle = match.group(2)  # Lignes entre
        sum_expr = match.group(3)  # Expression sum(...)
        
        # Vérifier qu'on est bien dans le contexte du graphique
        if 'Générer Graphique' in middle or 'minute par minute' in middle.lower():
            corrections_applied.append(f"Remplacement: {sum_expr} → abs(observed_movement)")
            return before + middle + "abs(observed_movement)"
        else:
            return match.group(0)  # Pas de changement
    
    # Appliquer le remplacement (chercher dans fenêtre de 500 caractères)
    content = re.sub(pattern1, replace_sum_after_observed, content, flags=re.MULTILINE | re.DOTALL)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CORRECTION 2 : Remplacer sum() dans paramètre total_impact_pips
    # ═══════════════════════════════════════════════════════════════════════
    
    pattern2 = r'total_impact_pips\s*=\s*sum\([^)]*predicted_pips[^)]*\)'
    
    if re.search(pattern2, content):
        content = re.sub(
            pattern2,
            'total_impact_pips=abs(observed_movement)',
            content
        )
        corrections_applied.append("Remplacement: total_impact_pips=sum(...) → total_impact_pips=abs(observed_movement)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # CORRECTION 3 : Dans statistiques, s'assurer qu'on utilise amplitude réelle
    # ═══════════════════════════════════════════════════════════════════════
    
    # Chercher section "Amplitude Totale" et vérifier le calcul
    pattern3 = r'amplitude\s*=\s*sum\([^)]*predicted_pips[^)]*\)'
    
    if re.search(pattern3, content):
        # Remplacer par calcul depuis max/min price
        content = re.sub(
            pattern3,
            'amplitude = (max_price - min_price) * 10000  # Amplitude réelle',
            content
        )
        corrections_applied.append("Remplacement: amplitude=sum(...) → amplitude=(max_price-min_price)*10000")
    
    # ═══════════════════════════════════════════════════════════════════════
    # VÉRIFICATION : Le code a-t-il changé ?
    # ═══════════════════════════════════════════════════════════════════════
    
    if content == original_content:
        print("\nℹ️  Aucune correction appliquée - Le code semble déjà correct")
        print()
        print("📊 ANALYSE :")
        print()
        print("Le code utilise probablement déjà 'observed_movement' correctement.")
        print("Si le problème persiste (231.9 pips affiché), vérifier :")
        print()
        print("1. Cache navigateur (Ctrl+Shift+Del puis Ctrl+F5)")
        print("2. Annotations hardcodées dans price_curve_generator.py")
        print("3. Console Streamlit pour erreurs Python silencieuses")
        print()
        print("Consultez GUIDE_CORRECTION_GRAPHIQUE.md pour diagnostic manuel.")
        print()
        return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # ÉCRITURE DU FICHIER CORRIGÉ
    # ═══════════════════════════════════════════════════════════════════════
    
    with open(PLANIFICATEUR_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ {len(corrections_applied)} correction(s) appliquée(s) :")
    for correction in corrections_applied:
        print(f"   - {correction}")
    
    return True

def main():
    print("="*80)
    print(" 🎨 CORRECTION AUTOMATIQUE GRAPHIQUE AMPLITUDE RÉELLE")
    print("="*80)
    print()
    
    # Backup
    backup_path = create_backup()
    print()
    
    # Corrections
    success = apply_corrections()
    
    print()
    print("="*80)
    
    if success:
        print(" ✅ CORRECTIONS APPLIQUÉES")
        print("="*80)
        print()
        print("🚀 PROCHAINES ÉTAPES :")
        print()
        print("1. Relancer Streamlit :")
        print("   streamlit run fx_impact_app/streamlit_app/Home.py")
        print()
        print("2. Tester sur 11/09/2025 :")
        print("   - Planificateur Multi-Événements")
        print("   - Mode séquentiel activé ✅")
        print("   - Charger Jobless Claims + CPI")
        print("   - Générer graphique minute par minute")
        print("   - ✅ Vérifier : Amplitude affichée = ~52 pips (PAS 231)")
        print()
        print(f"3. Si problème : Restaurer backup dans corrections_graphique/backups/")
        print()
    else:
        print(" ℹ️  CODE DÉJÀ CORRECT - VOIR RECOMMANDATIONS")
        print("="*80)
        print()
        print("Consultez : corrections_graphique/GUIDE_CORRECTION_GRAPHIQUE.md")
        print("pour diagnostic manuel approfondi.")
        print()

if __name__ == "__main__":
    main()
