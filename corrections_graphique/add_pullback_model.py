#!/usr/bin/env python3
"""
AMÉLIORATION : Ajouter pullback technique inter-phases réaliste
Modélise le comportement 2 vagues observé sur MetaTrader
"""

import sys
from pathlib import Path
from datetime import datetime

# Chemins
project_root = Path(__file__).parent.parent
generator_file = project_root / "fx_impact_app/src/price_curve_generator.py"
backup_dir = project_root / "fx_impact_app/src/backups"

def create_backup(file_path):
    """Créer backup avec timestamp"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"price_curve_generator_before_pullback_{timestamp}.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Backup : {backup_path.name}")
    return backup_path

def add_pullback_model():
    """Ajouter modèle de pullback inter-phases"""
    
    print("\n" + "="*80)
    print(" 🎨 AMÉLIORATION - PULLBACK TECHNIQUE INTER-PHASES")
    print("="*80 + "\n")
    
    # Backup
    create_backup(generator_file)
    
    # Lire fichier
    with open(generator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher la section à modifier dans generate_candlestick_curve_multi_events
    # On doit modifier la logique de calcul du target_price
    
    # Pattern à chercher : la section qui calcule contribution après "if max_progress > 0:"
    old_pattern = """        # Appliquer le mouvement vectoriel avec le progress maximum
        if max_progress > 0:
            if active_phase == "mouvement":
                sigmoid_progress = sigmoid(10 * (max_progress - 0.5))
                contribution = vectorial_impact_total * sigmoid_progress
            else:  # retracement
                contribution = vectorial_impact_total * max_progress
            
            target_price += contribution"""
    
    # Nouveau code avec modèle de pullback
    new_pattern = """        # ✅ AMÉLIORATION V5 : Modèle avec pullback inter-phases
        if max_progress > 0:
            if active_phase == "mouvement":
                # Phase mouvement normale
                sigmoid_progress = sigmoid(10 * (max_progress - 0.5))
                base_contribution = vectorial_impact_total * sigmoid_progress
                
                # ✅ AJOUT : Détection pullback inter-phases
                # Si on a plusieurs événements/phases, ajouter un pullback technique
                if len(predictions) > 1:
                    # Simuler pullback entre phases
                    # Le pullback arrive vers 40-60% du mouvement initial
                    pullback_start = 0.40
                    pullback_end = 0.70
                    pullback_strength = 0.35  # Retracement de 35% du mouvement
                    
                    if pullback_start <= max_progress <= pullback_end:
                        # Calculer l'intensité du pullback (0 → 1 → 0)
                        pullback_position = (max_progress - pullback_start) / (pullback_end - pullback_start)
                        # Courbe en cloche pour le pullback
                        pullback_intensity = np.sin(pullback_position * np.pi)
                        # Appliquer le pullback (soustrait du mouvement)
                        pullback_amount = vectorial_impact_total * pullback_strength * pullback_intensity
                        base_contribution -= pullback_amount
                
                contribution = base_contribution
                
            else:  # retracement
                contribution = vectorial_impact_total * max_progress
            
            target_price += contribution"""
    
    # Vérifier si déjà appliqué
    if "AMÉLIORATION V5" in content:
        print("ℹ️  L'amélioration V5 est déjà présente")
        print("    Le modèle de pullback existe déjà dans le code")
        return False
    
    # Vérifier si le pattern existe
    if old_pattern not in content:
        print("⚠️  Pattern original non trouvé")
        print("    Le code a peut-être été modifié")
        print("    Recherche de patterns alternatifs...")
        
        # Chercher au moins la ligne caractéristique
        if "if max_progress > 0:" in content and "sigmoid_progress = sigmoid" in content:
            print("\n✅ Structure trouvée, mais format différent")
            print("    Vérifiez manuellement le fichier :")
            print(f"    {generator_file}")
            print("\n    Cherchez 'if max_progress > 0:' et ajoutez la logique de pullback")
        
        return False
    
    # Appliquer la modification
    new_content = content.replace(old_pattern, new_pattern)
    
    if new_content == content:
        print("❌ Aucune modification appliquée")
        return False
    
    # Sauvegarder
    with open(generator_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\n" + "="*80)
    print(" ✅ AMÉLIORATION APPLIQUÉE !")
    print("="*80 + "\n")
    
    print("📄 Fichier modifié : price_curve_generator.py")
    print("💾 Backup sauvegardé : backups/")
    
    print("\n" + "="*80)
    print(" 🎯 COMPORTEMENT AJOUTÉ")
    print("="*80)
    print("""
✅ Phase 1 (0-40% du mouvement) :
   Monte normalement
   
✅ Pullback technique (40-70% du mouvement) :
   Retracement de ~35% de la phase 1
   Simule la prise de profit des traders
   Courbe en cloche pour transition douce
   
✅ Phase 2 (70-100% du mouvement) :
   Reprend le mouvement initial
   Atteint l'objectif final
   
✅ Résultat :
   Graphique avec "2 vagues + pullback"
   Comme observé sur MetaTrader ! 🎯
    """)
    
    print("\n" + "="*80)
    print(" 🚀 PROCHAINES ÉTAPES")
    print("="*80)
    print("""
1. Vider cache Python :
   find . -type d -name "__pycache__" -exec rm -rf {} +

2. Vider cache navigateur :
   Cmd+Shift+Del OU mode privé (Cmd+Shift+N)

3. Relancer Streamlit :
   streamlit run fx_impact_app/streamlit_app/Home.py

4. Tester avec date 11/09/2025, prix 1.16810

5. Résultat attendu :
   📊 Monte à ~1.182 (phase 1)
   📉 Retracement à ~1.179 (pullback)
   📈 Reprend à ~1.184 (phase 2)
   ✅ Pattern 2 vagues visible !
    """)
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" 🎨 AMÉLIORATION PULLBACK TECHNIQUE")
    print("="*80 + "\n")
    
    print("Cette amélioration va :")
    print("  1. Détecter quand il y a plusieurs phases")
    print("  2. Ajouter un pullback technique entre 40-70% du mouvement")
    print("  3. Simuler le comportement réel observé sur MetaTrader")
    print("  4. Créer un graphique avec 2 vagues + retracement")
    print()
    
    success = add_pullback_model()
    
    if success:
        print("\n✅ AMÉLIORATION RÉUSSIE !")
        print("\n🎯 Testez maintenant !")
    else:
        print("\n⚠️  Amélioration non appliquée")
        print("   Vérifiez si déjà présente ou si structure différente")
    
    print("\n" + "="*80)
    print(" FIN DU SCRIPT")
    print("="*80 + "\n")
