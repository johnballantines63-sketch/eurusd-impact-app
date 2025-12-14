#!/usr/bin/env python3
"""
Script de diagnostic : Localiser où 231.9 pips est affiché/calculé
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PLANIFICATEUR_FILE = PROJECT_ROOT / "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py"

def analyze_file():
    """Analyser le fichier pour trouver calculs d'impact"""
    
    with open(PLANIFICATEUR_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("="*80)
    print(" 🔍 DIAGNOSTIC : Recherche calculs/affichages d'impact")
    print("="*80)
    print()
    
    # Patterns à chercher
    patterns = [
        (r'sum\([^)]*predicted_pips[^)]*\)', 'Somme vectorielle brute'),
        (r'vectorial_impact\s*=', 'Assignation vectorial_impact'),
        (r'total_impact[^=]*=', 'Assignation total_impact'),
        (r'Impact Total', 'Affichage "Impact Total"'),
        (r'total_impact_pips', 'Variable total_impact_pips'),
        (r'amplitude', 'Mentions amplitude'),
        (r'observed_movement', 'Variable observed_movement'),
        (r'231', 'Valeur 231 (problématique)'),
    ]
    
    findings = []
    
    for i, line in enumerate(lines, 1):
        for pattern, description in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append((i, description, line.strip()))
    
    # Afficher par catégorie
    categories = {}
    for line_num, desc, line_content in findings:
        if desc not in categories:
            categories[desc] = []
        categories[desc].append((line_num, line_content))
    
    for desc in sorted(categories.keys()):
        print(f"\n📊 {desc} ({len(categories[desc])} occurrences):")
        print("-" * 80)
        for line_num, content in categories[desc][:5]:  # Max 5 par catégorie
            print(f"  L{line_num:4d}: {content[:75]}...")
        
        if len(categories[desc]) > 5:
            print(f"  ... et {len(categories[desc]) - 5} autres")
    
    # Analyse spécifique section graphique minute par minute
    print("\n" + "="*80)
    print(" 🎨 SECTION GRAPHIQUE MINUTE PAR MINUTE (lignes 1650-1900)")
    print("="*80)
    print()
    
    in_graph_section = False
    graph_lines = []
    
    for i, line in enumerate(lines, 1):
        if i >= 1650 and i <= 1900:
            if not in_graph_section and '📈 GRAPHIQUE MINUTE PAR MINUTE' in line:
                in_graph_section = True
                print(f"✅ Section trouvée à ligne {i}")
                print()
            
            if in_graph_section:
                # Chercher lignes importantes
                if any(keyword in line for keyword in [
                    'vectorial_impact', 'total_impact', 'observed_movement',
                    'create_candlestick_prediction_chart', 'total_impact_pips',
                    'sum(', 'amplitude'
                ]):
                    graph_lines.append((i, line.rstrip()))
    
    if graph_lines:
        print("📋 Lignes clés trouvées :")
        print()
        for line_num, content in graph_lines:
            # Colorier les patterns importants
            if 'sum(' in content and 'predicted_pips' in content:
                marker = "⚠️  SOMME VECTORIELLE"
            elif 'vectorial_impact' in content:
                marker = "✅ vectorial_impact"
            elif 'observed_movement' in content:
                marker = "✅ observed_movement"
            elif 'total_impact_pips' in content:
                marker = "🎯 total_impact_pips"
            else:
                marker = "   "
            
            print(f"  {marker}  L{line_num:4d}: {content[:70]}")
    else:
        print("⚠️  Section graphique minute par minute non trouvée clairement")
    
    print()
    print("="*80)
    print(" 💡 ANALYSE")
    print("="*80)
    print()
    print("📌 Pour corriger le problème du graphique :")
    print()
    print("1. Si 'sum(p[\"predicted_pips\"] for p in predictions)' apparaît")
    print("   APRÈS le calcul de 'observed_movement' dans la section graphique,")
    print("   il faut le remplacer par 'abs(vectorial_impact)' ou 'abs(observed_movement)'")
    print()
    print("2. Vérifier que create_candlestick_prediction_chart() reçoit bien :")
    print("   total_impact_pips=abs(observed_movement)")
    print("   et NON sum(p['predicted_pips'] for p in predictions)")
    print()
    print("3. Si le problème persiste, c'est peut-être dans une ANNOTATION")
    print("   ou un TEXTE affiché, pas dans un calcul")
    print()

if __name__ == "__main__":
    analyze_file()
