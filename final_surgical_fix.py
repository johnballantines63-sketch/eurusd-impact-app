#!/usr/bin/env python3
"""
Correction chirurgicale FINALE des métriques TTR
Supprime et remplace tout le bloc problématique
"""

from pathlib import Path

def surgical_fix():
    """Correction chirurgicale du bloc TTR"""
    
    file_path = Path(__file__).parent / "fx_impact_app" / "streamlit_app" / "pages" / "4_Planificateur-Multi-Evenements.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trouver et remplacer les lignes TTR (autour de 1735)
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Détecter début du bloc TTR
        if 'st.metric("📊 MAE TTR"' in line or 'st.metric("📊 RMSE TTR"' in line or 'st.metric("📊 MAPE TTR"' in line or 'st.metric("📊 Erreur Max"' in line:
            # Sauter cette ligne et utiliser notre version safe
            indent = len(line) - len(line.lstrip())
            
            if 'MAE' in line:
                new_lines.append(' ' * indent + 'st.metric("📊 MAE TTR", f"{ttr_stats[\'mae\']:.1f} min" if ttr_stats.get(\'mae\') else "N/A")\n')
            elif 'RMSE' in line:
                new_lines.append(' ' * indent + 'st.metric("📊 RMSE TTR", f"{ttr_stats[\'rmse\']:.1f} min" if ttr_stats.get(\'rmse\') else "N/A")\n')
            elif 'MAPE' in line:
                new_lines.append(' ' * indent + 'st.metric("📊 MAPE TTR", f"{ttr_stats[\'mape\']:.1f}%" if ttr_stats.get(\'mape\') else "N/A")\n')
            elif 'Erreur Max' in line:
                # Cette métrique n'existe plus, on la skip complètement
                pass
            
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # Écrire
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Correction appliquée")
    return True

if __name__ == "__main__":
    print("="*80)
    print("🔧 CORRECTION CHIRURGICALE FINALE")
    print("="*80)
    print()
    surgical_fix()
    print("\n✅ Fichier corrigé")
    print("\n🚀 Lance maintenant :")
    print("  pkill -f streamlit")
    print("  streamlit run fx_impact_app/streamlit_app/Home.py")
