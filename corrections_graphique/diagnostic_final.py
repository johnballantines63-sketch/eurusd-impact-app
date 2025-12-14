#!/usr/bin/env python3
"""
Diagnostic Final : Localiser exactement où 231.9 pips apparaît
"""

from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent

FILES_TO_CHECK = [
    "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py",
    "fx_impact_app/src/price_curve_generator.py",
]

def analyze_file(filepath):
    """Analyser un fichier pour trouver le problème"""
    
    if not filepath.exists():
        print(f"⚠️  Fichier non trouvé : {filepath}")
        return
    
    print(f"\n{'='*80}")
    print(f" 📄 {filepath.name}")
    print('='*80 + '\n')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    suspects = []
    
    for i, line in enumerate(lines, 1):
        # Chercher valeurs 231/232
        if '231' in line or '232' in line:
            suspects.append((i, '⚠️  VALEUR 231/232', line.strip()))
        
        # Chercher sum(predicted_pips) qui devrait être remplacé
        if 'sum(' in line and 'predicted_pips' in line and 'vectorial_impact' not in line:
            suspects.append((i, '🔍 SUM predicted_pips', line.strip()))
        
        # Chercher annotations/titres avec "Impact" ou "pips"
        if re.search(r'(annotation|title|text)\s*=', line, re.IGNORECASE):
            if 'impact' in line.lower() or 'pips' in line.lower():
                suspects.append((i, '📝 ANNOTATION/TITRE', line.strip()))
        
        # Chercher appels à create_candlestick_prediction_chart
        if 'create_candlestick_prediction_chart' in line:
            suspects.append((i, '🎨 APPEL GRAPHIQUE', line.strip()))
        
        # Chercher total_impact_pips=
        if 'total_impact_pips' in line and '=' in line:
            suspects.append((i, '🎯 total_impact_pips', line.strip()))
    
    if suspects:
        print(f"Trouvé {len(suspects)} ligne(s) suspecte(s) :\n")
        
        for line_num, type_desc, content in suspects:
            print(f"{type_desc}  L{line_num}:")
            print(f"    {content[:100]}")
            if len(content) > 100:
                print(f"    ...{content[100:200]}")
            print()
    else:
        print("✅ Aucun problème détecté dans ce fichier\n")


def check_graphique_section():
    """Vérifier spécifiquement la section graphique minute par minute"""
    
    planif_file = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"
    
    if not planif_file.exists():
        print("⚠️  Fichier Planificateur non trouvé")
        return
    
    print(f"\n{'='*80}")
    print(" 🎨 SECTION GRAPHIQUE MINUTE PAR MINUTE (Diagnostic détaillé)")
    print('='*80 + '\n')
    
    with open(planif_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver la section graphique
    pattern = r'(st\.subheader\("📈 Évolution Prédite.*?)(st\.subheader\(|st\.divider\(\)|\Z)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        section = match.group(1)
        lines = section.split('\n')
        
        print(f"✅ Section trouvée ({len(lines)} lignes)\n")
        
        # Chercher spécifiquement le calcul de total_impact_pips
        print("🔍 Recherche de 'total_impact_pips=' dans la section :\n")
        
        found_total_impact = False
        for i, line in enumerate(lines, 1):
            if 'total_impact_pips' in line and '=' in line:
                found_total_impact = True
                print(f"L{i}: {line.strip()}\n")
                
                # Analyser la ligne
                if 'sum(' in line and 'predicted_pips' in line:
                    print("❌ PROBLÈME TROUVÉ !")
                    print("   La ligne utilise sum(predicted_pips) au lieu de observed_movement\n")
                    print("🔧 CORRECTION NÉCESSAIRE :")
                    print(f"   AVANT : {line.strip()}")
                    print(f"   APRÈS : total_impact_pips=abs(observed_movement),")
                    print()
                elif 'observed_movement' in line or 'vectorial_impact' in line:
                    print("✅ CORRECT : Utilise observed_movement ou vectorial_impact\n")
                else:
                    print("⚠️  Valeur inattendue - Vérifier manuellement\n")
        
        if not found_total_impact:
            print("⚠️  'total_impact_pips=' non trouvé dans la section graphique")
            print("   Cela peut être normal si le paramètre est passé directement")
            print()
            
            # Chercher l'appel à la fonction
            print("🔍 Recherche de l'appel à create_candlestick_prediction_chart :\n")
            
            for i, line in enumerate(lines, 1):
                if 'create_candlestick_prediction_chart' in line:
                    # Afficher l'appel complet (peut s'étendre sur plusieurs lignes)
                    start_line = max(0, i - 2)
                    end_line = min(len(lines), i + 10)
                    
                    print("Appel trouvé :\n")
                    for j in range(start_line, end_line):
                        if j < len(lines):
                            print(f"L{j+1}: {lines[j].rstrip()}")
                    print()
                    break
    else:
        print("⚠️  Section graphique minute par minute non trouvée")
        print("   Chercher manuellement : '📈 Évolution Prédite du Cours EUR/USD'")


def main():
    print("="*80)
    print(" 🔍 DIAGNOSTIC FINAL : Localisation Problème 231.9 pips")
    print("="*80)
    
    # Vérifier chaque fichier
    for filepath in FILES_TO_CHECK:
        full_path = PROJECT_ROOT / filepath
        analyze_file(full_path)
    
    # Analyse spéciale de la section graphique
    check_graphique_section()
    
    print("\n" + "="*80)
    print(" 💡 CONCLUSIONS & RECOMMANDATIONS")
    print("="*80 + "\n")
    
    print("1. Si aucun problème trouvé ci-dessus :")
    print("   → Le code est correct, c'est un problème de CACHE NAVIGATEUR")
    print("   → Solution : Ctrl+Shift+Del → Vider cache → Ctrl+F5")
    print()
    
    print("2. Si sum(predicted_pips) trouvé dans section graphique :")
    print("   → MODIFIER manuellement la ligne pour utiliser observed_movement")
    print("   → Sauvegarder et relancer Streamlit")
    print()
    
    print("3. Si valeur 231/232 hardcodée trouvée :")
    print("   → Supprimer ou remplacer par valeur dynamique")
    print()
    
    print("4. Pour tester la correction :")
    print("   streamlit run fx_impact_app/streamlit_app/Home.py")
    print("   → Planificateur Multi-Événements")
    print("   → 11/09/2025, Mode séquentiel ✅")
    print("   → Générer graphique → Vérifier ~52 pips")
    print()

if __name__ == "__main__":
    main()
