#!/usr/bin/env python3
"""
Vérifie comment le calcul vectoriel est actuellement implémenté
"""

import os

project_root = "/Users/andrevalentin/Projects/eurusd_news_impact_calculator"

print("=" * 80)
print("🔍 VÉRIFICATION CALCUL VECTORIEL")
print("=" * 80)

# Lire le fichier principal
main_file = os.path.join(project_root, "fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py")

with open(main_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("\n📋 RECHERCHE DES CALCULS VECTORIELS...\n")

# Chercher le calcul vectoriel classique
if "vectorial_impact = sum(p['predicted_pips'] * p['direction'] for p in predictions)" in content:
    print("✅ TROUVÉ : Calcul vectoriel CLASSIQUE")
    print("   Code : vectorial_impact = sum(p['predicted_pips'] * p['direction'])")
    print("   → Addition des impacts SIGNÉS de chaque événement")
    print("   → Exemple : Jobless (-31 pips) + CPI (-55 pips) = -86 pips")
else:
    print("❌ Calcul vectoriel classique NON trouvé")

# Chercher sequence_multi_event_timeline
seq_file = os.path.join(project_root, "fx_impact_app/src/sequence_multi_event_timeline.py")

if os.path.exists(seq_file):
    with open(seq_file, 'r', encoding='utf-8') as f:
        seq_content = f.read()
    
    print("\n📋 ANALYSE DE sequence_multi_event_timeline.py...\n")
    
    # Chercher comment il calcule l'impact par phase
    if "impact_pips" in seq_content:
        print("✅ TROUVÉ : Variable 'impact_pips' dans le séquençage")
        
        # Extraire le contexte
        lines = seq_content.split('\n')
        for i, line in enumerate(lines):
            if 'impact_pips' in line and '=' in line:
                print(f"\n   Ligne {i+1}: {line.strip()}")
                # Contexte
                start = max(0, i-3)
                end = min(len(lines), i+4)
                print("   Contexte :")
                for j in range(start, end):
                    marker = ">>>" if j == i else "   "
                    print(f"   {marker} {lines[j]}")
                print()

print("\n" + "=" * 80)
print("📊 ANALYSE THÉORIQUE")
print("=" * 80)

print("""
🎯 DEUX APPROCHES POSSIBLES :

1️⃣ CALCUL VECTORIEL (ce qui DEVRAIT être fait) :
   
   Au temps T0 = 14:30 :
   - Jobless Claims : Surprise -11 → Impact prédit -31 pips (DOWN)
   - CPI : Surprise +0.09 → Impact prédit -55 pips (DOWN)
   
   Impact COMBINÉ = -31 + (-55) = -86 pips DOWN
   
   → Le marché réagit à la RÉSULTANTE globale
   → UN SEUL mouvement de -86 pips
   → TTR commence après ce mouvement unique
   
   📊 Graphique attendu :
   ```
   Prix
   │
   │     ┌─────── (stable après TTR)
   │     │
   │     │ TTR
   │    ╱
   │   ╱  Mouvement -86 pips
   │  ╱   (latence ~3 min)
   │ ╱
   └────────────────> Temps
     14:30  14:33    14:45
   ```

2️⃣ CALCUL SÉQUENTIEL (ce qui semble être fait actuellement) :
   
   Phase 1 (14:30) : Jobless Claims
   - Impact : -31 pips
   - Mouvement DOWN
   - TTR théorique : 31 min... mais interrompu !
   
   Phase 2 (14:30) : CPI 
   - Impact : -55 pips
   - "Interrompt" Jobless
   - TTR théorique : 39 min... mais interrompu !
   
   Phase 3 (14:30) : CPI Core
   - Impact : -55 pips
   - "Interrompt" les autres
   
   ❌ PROBLÈME : Traite les événements comme séquentiels
      alors qu'ils sont SIMULTANÉS (même minute)

📋 CE QUI EST CORRECT :

Pour événements SIMULTANÉS (< 1 minute d'écart) :
✅ Calculer impact vectoriel COMBINÉ
✅ UN SEUL mouvement de marché
✅ UN SEUL TTR (après le mouvement combiné)

Pour événements ESPACÉS (> 5-10 minutes) :
✅ Calculer impact séquentiel
✅ Chaque événement crée son propre mouvement
✅ TTR distincts

🎯 EXEMPLE 11/09/2025 :

14:30 → Jobless + CPI (simultanés) → Impact combiné -86 pips → TTR unique
14:45 → Current Account (15 min après) → Nouvel impact +25 pips → Nouveau TTR

Donc on devrait avoir :
- Phase 1 : 14:30, impact -86 pips, TTR 20-40 min
- Phase 2 : 14:45, impact +25 pips, TTR 50 min
""")

print("\n" + "=" * 80)
print("🔧 RECOMMANDATION")
print("=" * 80)

print("""
Il faut modifier sequence_multi_event_timeline() pour :

1. Grouper les événements par fenêtre temporelle (< 1-2 min d'écart)
2. Pour chaque groupe : calculer impact VECTORIEL combiné
3. Traiter chaque groupe comme UNE phase unique
4. Phases distinctes seulement si événements espacés (> 5 min)

✅ Résultat attendu pour 11/09/2025 :
   - Phase 1 : 14:30 (Jobless+CPI+Core) → -86 pips, TTR 30-40 min
   - Phase 2 : 14:45 (Current Account) → +25 pips, TTR 50 min

Voulez-vous que je corrige sequence_multi_event_timeline() ?
""")
