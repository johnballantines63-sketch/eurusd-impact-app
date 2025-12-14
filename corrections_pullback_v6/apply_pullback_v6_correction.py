#!/usr/bin/env python3
"""
🔧 CORRECTION PULLBACK V6 - Option 3 (Modèle de substitution)
Corrige le bug "double négatif" en remplaçant la logique de soustraction
par un modèle de substitution temporaire.

BUG CORRIGÉ : 
- Avant : `base_contribution -= pullback_amount * (1 if vectorial > 0 else -1)`
- Après : `base_contribution = vectorial * sigmoid_progress * pullback_level`

RÉSULTAT ATTENDU : Amplitude stable ~120-159 pips avec pullback réaliste
"""

import sys
from pathlib import Path

def apply_pullback_v6_correction():
    """Applique la correction pullback V6 au générateur de courbes"""
    
    # Chemins
    project_root = Path(__file__).parent.parent
    generator_path = project_root / "fx_impact_app" / "src" / "price_curve_generator.py"
    backup_path = project_root / "fx_impact_app" / "src" / "backups" / f"price_curve_generator_before_pullback_v6_{Path(__file__).stem}.py"
    
    print("🔍 Vérification des fichiers...")
    if not generator_path.exists():
        print(f"❌ Erreur : {generator_path} introuvable")
        sys.exit(1)
    
    # Créer backup
    print(f"💾 Création backup : {backup_path.name}")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(generator_path.read_text(encoding='utf-8'))
    
    # Lire le fichier
    content = generator_path.read_text(encoding='utf-8')
    
    # ✅ CORRECTION V6 : Remplacer le bloc pullback
    old_code = """            elif minutes_since_event < avg_ttr:
                # Phase mouvement
                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                contribution = vectorial_impact_total * sigmoid_progress
                active_phase = "mouvement\""""
    
    new_code = """            elif minutes_since_event < avg_ttr:
                # ✅ CORRECTION V6 : Phase mouvement avec pullback corrigé
                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                
                # Calculer contribution de base
                base_contribution = vectorial_impact_total * sigmoid_progress
                
                # Appliquer pullback technique si plusieurs événements
                if len(predictions) > 1:
                    # Pullback entre 40% et 70% du mouvement
                    pullback_start = 0.40
                    pullback_end = 0.70
                    
                    if pullback_start <= progress <= pullback_end:
                        # Position dans le pullback (0 → 1)
                        pullback_position = (progress - pullback_start) / (pullback_end - pullback_start)
                        # Courbe sinusoïdale pour transition douce
                        pullback_intensity = np.sin(pullback_position * np.pi)
                        
                        # ✅ CORRECTION : Remplacer au lieu de soustraire
                        # Réduire la contribution en multipliant par un facteur < 1
                        pullback_level = 1.0 - (0.35 * pullback_intensity)  # Max 35% de réduction
                        base_contribution = vectorial_impact_total * sigmoid_progress * pullback_level
                
                contribution = base_contribution
                active_phase = "mouvement\""""
    
    # Vérifier que le code existe
    if old_code not in content:
        print("⚠️  Code cible non trouvé. Le fichier a peut-être déjà été modifié.")
        print("Recherche d'une variante...")
        
        # Variante simplifiée
        old_code_simple = """                progress = (minutes_since_event - avg_latency) / (avg_ttr - avg_latency)
                sigmoid_progress = sigmoid(10 * (progress - 0.5))
                contribution = vectorial_impact_total * sigmoid_progress"""
        
        if old_code_simple in content:
            print("✅ Variante trouvée, application de la correction...")
            content = content.replace(old_code_simple, new_code.split('\n', 3)[3])  # Prendre juste le nouveau code
        else:
            print("❌ Impossible de trouver le code à remplacer")
            print("Le fichier est peut-être dans un état inattendu")
            sys.exit(1)
    else:
        # Appliquer la correction
        print("🔧 Application de la correction V6...")
        content = content.replace(old_code, new_code)
    
    # Écrire le fichier modifié
    generator_path.write_text(content, encoding='utf-8')
    
    print("\n✅ CORRECTION V6 APPLIQUÉE AVEC SUCCÈS !")
    print("\n📊 CHANGEMENTS :")
    print("   • Pullback corrigé : modèle de substitution au lieu de soustraction")
    print("   • Fenêtre pullback : 40-70% (au lieu de 35-65%)")
    print("   • Intensité pullback : 35% max (au lieu de 40%)")
    print("   • Bug 'double négatif' : CORRIGÉ")
    print("\n🎯 RÉSULTAT ATTENDU :")
    print("   • Amplitude : ~120-159 pips (stable)")
    print("   • Pattern : 2 vagues avec pullback réaliste")
    print("   • Pas de dérive d'amplitude")
    print("\n⚠️  ACTIONS REQUISES :")
    print("   1. Vider cache Python : find . -name '__pycache__' -exec rm -rf {} +")
    print("   2. Vider cache navigateur : Cmd+Shift+Del ou mode privé")
    print("   3. Tester : Date 11/09/2025, Prix 1.16810")
    print(f"\n💾 Backup créé : {backup_path.name}")

if __name__ == "__main__":
    apply_pullback_v6_correction()
