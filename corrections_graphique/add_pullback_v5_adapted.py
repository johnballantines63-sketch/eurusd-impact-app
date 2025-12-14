#!/usr/bin/env python3
"""
AMÉLIORATION V5 ADAPTÉE : Pullback technique pour code V4
"""

import sys
from pathlib import Path
from datetime import datetime

# Chemins
project_root = Path(__file__).parent.parent
generator_file = project_root / "fx_impact_app/src/price_curve_generator.py"
backup_dir = project_root / "fx_impact_app/src/backups"

def create_backup(file_path):
    """Créer backup"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"price_curve_generator_before_pullback_v5_{timestamp}.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Backup : {backup_path.name}")
    return backup_path

def add_pullback_v5():
    """Ajouter pullback technique au code V4"""
    
    print("\n" + "="*80)
    print(" 🎨 AMÉLIORATION V5 - PULLBACK TECHNIQUE")
    print("="*80 + "\n")
    
    # Backup
    create_backup(generator_file)
    
    # Lire fichier
    with open(generator_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si déjà appliqué
    if "AMÉLIORATION V5" in content or "pullback technique" in content.lower():
        print("ℹ️  L'amélioration V5 semble déjà présente")
        return False
    
    # Pattern à remplacer : la section "Phase mouvement" dans le code V4
    old_pattern = """            elif minutes_since_event < avg_ttr:
                # Phase mouvement
                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                contribution = vectorial_impact_total * sigmoid_progress
                active_phase = "mouvement\""""
    
    # Nouveau code avec pullback
    new_pattern = """            elif minutes_since_event < avg_ttr:
                # ✅ AMÉLIORATION V5 : Phase mouvement avec pullback technique
                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                base_contribution = vectorial_impact_total * sigmoid_progress
                
                # Ajouter pullback technique si plusieurs phases/événements
                if len(predictions) > 1:
                    # Pullback entre 35% et 65% du mouvement
                    pullback_start = 0.35
                    pullback_end = 0.65
                    pullback_strength = 0.40  # Retracement de 40%
                    
                    if pullback_start <= progress <= pullback_end:
                        # Position dans le pullback (0 → 1)
                        pullback_position = (progress - pullback_start) / (pullback_end - pullback_start)
                        # Courbe sinusoïdale pour transition douce
                        pullback_intensity = np.sin(pullback_position * np.pi)
                        # Appliquer le retracement
                        pullback_amount = abs(vectorial_impact_total) * pullback_strength * pullback_intensity
                        # Soustraire du mouvement
                        base_contribution -= pullback_amount * (1 if vectorial_impact_total > 0 else -1)
                
                contribution = base_contribution
                active_phase = "mouvement\""""
    
    # Vérifier que le pattern existe
    if old_pattern not in content:
        print("⚠️  Pattern V4 non trouvé !")
        print("    Le code a peut-être changé")
        
        # Chercher des indicateurs
        if "Phase mouvement" in content:
            print("\n✅ 'Phase mouvement' trouvée")
            print("    Mais la structure exacte diffère")
            print("\n📝 Vérifiez manuellement ligne ~125 de price_curve_generator.py")
        
        return False
    
    # Appliquer
    new_content = content.replace(old_pattern, new_pattern)
    
    if new_content == content:
        print("❌ Aucune modification")
        return False
    
    # Sauvegarder
    with open(generator_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("\n" + "="*80)
    print(" ✅ AMÉLIORATION V5 APPLIQUÉE !")
    print("="*80 + "\n")
    
    print("📄 Fichier : price_curve_generator.py")
    print("💾 Backup : backups/")
    
    print("\n" + "="*80)
    print(" 🎯 COMPORTEMENT AJOUTÉ")
    print("="*80)
    print("""
✅ Pullback entre 35-65% du mouvement
✅ Retracement de 40% de l'amplitude
✅ Courbe sinusoïdale pour transition douce
✅ S'applique uniquement si plusieurs phases

Résultat attendu :
  Phase 1 : Monte à ~1.179
  Pullback : Retracement à ~1.177
  Phase 2 : Reprend à ~1.180
    """)
    
    print("\n" + "="*80)
    print(" 🚀 ACTIONS NÉCESSAIRES")
    print("="*80)
    print("""
1. Vider cache Python :
   find . -type d -name "__pycache__" -exec rm -rf {} +

2. FERMER COMPLÈTEMENT le navigateur

3. Rouvrir en mode privé (Cmd+Shift+N)

4. Relancer Streamlit

5. Tester : Date 11/09/2025, prix 1.16810
    """)
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" 🎨 AMÉLIORATION V5 - PULLBACK TECHNIQUE")
    print("="*80 + "\n")
    
    success = add_pullback_v5()
    
    if success:
        print("\n✅ SUCCÈS !")
        print("\n⚠️  N'oubliez pas de :")
        print("  1. Vider cache Python")
        print("  2. FERMER le navigateur")
        print("  3. Rouvrir en mode privé")
    else:
        print("\n❌ Échec ou déjà appliqué")
    
    print("\n" + "="*80)
    print(" FIN")
    print("="*80 + "\n")
