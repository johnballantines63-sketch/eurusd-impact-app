#!/usr/bin/env python3
"""
Correction rapide des métriques TTR - Protection contre None
"""

from pathlib import Path

def fix_ttr_metrics():
    """Corrige les 3 lignes de métriques TTR"""
    
    file_path = Path(__file__).parent / "fx_impact_app" / "streamlit_app" / "pages" / "4_Planificateur-Multi-Evenements.py"
    
    if not file_path.exists():
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    # Lire le fichier
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modifications = 0
    
    # Corriger ligne par ligne
    for i, line in enumerate(lines):
        original_line = line
        
        # MAE
        if 'st.metric("📊 MAE TTR"' in line and 'is not None' not in line:
            lines[i] = line.replace(
                'f"{ttr_stats[\'mae\']:.1f} min"',
                'f"{ttr_stats[\'mae\']:.1f} min" if ttr_stats.get(\'mae\') is not None else "N/A"'
            )
            if lines[i] != original_line:
                modifications += 1
                print(f"  ✓ Ligne {i+1} corrigée (MAE)")
        
        # RMSE
        if 'st.metric("📊 RMSE TTR"' in line and 'is not None' not in line:
            lines[i] = line.replace(
                'f"{ttr_stats[\'rmse\']:.1f} min"',
                'f"{ttr_stats[\'rmse\']:.1f} min" if ttr_stats.get(\'rmse\') is not None else "N/A"'
            )
            if lines[i] != original_line:
                modifications += 1
                print(f"  ✓ Ligne {i+1} corrigée (RMSE)")
        
        # MAPE
        if 'st.metric("📊 MAPE TTR"' in line and 'is not None' not in line:
            lines[i] = line.replace(
                'f"{ttr_stats[\'mape\']:.1f}%"',
                'f"{ttr_stats[\'mape\']:.1f}%" if ttr_stats.get(\'mape\') is not None else "N/A"'
            )
            if lines[i] != original_line:
                modifications += 1
                print(f"  ✓ Ligne {i+1} corrigée (MAPE)")
    
    # Écrire le fichier
    if modifications > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"\n✅ {modifications} correction(s) appliquée(s)")
        return True
    else:
        print("❌ Aucune correction appliquée")
        return False

if __name__ == "__main__":
    print("="*80)
    print("🔧 CORRECTION RAPIDE MÉTRIQUES TTR")
    print("="*80)
    print()
    
    success = fix_ttr_metrics()
    
    if success:
        print("\n✅ SUCCÈS")
        print("\n📋 Prochaines étapes :")
        print("  1. pkill -f streamlit")
        print("  2. streamlit run fx_impact_app/streamlit_app/Home.py")
        print("  3. Tester sur 11 sept 2025")
    else:
        print("\n❌ Échec")
