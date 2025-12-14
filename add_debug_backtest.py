#!/usr/bin/env python3
"""
Ajouter des prints de debug dans le backtest
Pour voir où ça plante
"""

from pathlib import Path
from datetime import datetime

FILE_PATH = Path('fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py')

print("🔧 AJOUT DEBUG BACKTEST")
print("=" * 60)

with open(FILE_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Backup
backup_path = FILE_PATH.parent / 'backups' / f"backup_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
backup_path.parent.mkdir(exist_ok=True)
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"💾 Backup: {backup_path}")

# Trouver ligne du subheader backtest
modified = False
for i, line in enumerate(lines):
    if 'st.subheader("🎯 Backtest : Prédiction vs Réalité")' in line:
        # Insérer print debug AVANT
        indent = ' ' * (len(line) - len(line.lstrip()))
        debug_lines = [
            f'{indent}# === DEBUG BACKTEST ===\n',
            f'{indent}print("\\n" + "="*60)\n',
            f'{indent}print("DEBUG: Entrée dans section backtest")\n',
            f'{indent}print(f"DEBUG: Nombre de predictions: {{len(predictions)}}")\n',
            f'{indent}print("="*60 + "\\n")\n',
            f'{indent}st.warning("🔍 DEBUG: Section backtest atteinte !")\n',
            f'{indent}# === FIN DEBUG ===\n',
            '\n'
        ]
        
        lines = lines[:i] + debug_lines + lines[i:]
        modified = True
        print(f"✅ Debug ajouté à la ligne {i+1}")
        break

if not modified:
    print("❌ Impossible de trouver le subheader backtest")
else:
    # Ajouter aussi debug après détection is_past
    for i, line in enumerate(lines):
        if "is_past = all(t < now for t in events_times)" in line:
            indent = ' ' * (len(line) - len(line.lstrip()))
            debug_line = f'{indent}print(f"DEBUG: is_past = {{is_past}}, events_times = {{events_times[:2]}}")\n'
            lines.insert(i + 1, debug_line)
            print(f"✅ Debug is_past ajouté à la ligne {i+2}")
            break
    
    # Ajouter debug dans le if is_past
    for i, line in enumerate(lines):
        if 'if is_past:' in line and 'Événements passés détectés' in lines[i+1]:
            indent = ' ' * (len(line) - len(line.lstrip()))
            debug_line = f'{indent}    print("DEBUG: Entrée dans bloc is_past")\n'
            lines.insert(i + 1, debug_line)
            print(f"✅ Debug bloc is_past ajouté à la ligne {i+2}")
            break
    
    # Écrire
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✅ Debugs ajoutés !")
    print("\n📋 Logs à chercher après redémarrage Streamlit:")
    print("   - 'DEBUG: Entrée dans section backtest'")
    print("   - 'DEBUG: is_past = ...'")
    print("   - 'DEBUG: Entrée dans bloc is_past'")
    print("\n🔄 Redémarrez Streamlit et sélectionnez événements passés")
    print("   Regardez le terminal pour les prints DEBUG")
