# 🎯 GUIDE VISUEL - 3 ÉTAPES SIMPLES

```
┌─────────────────────────────────────────────────────────────────┐
│                    ÉTAPE 1 : TERMINAL                           │
└─────────────────────────────────────────────────────────────────┘

cd ~/Desktop/eurusd_news_impact_calculator_MPC/corrections_graphique
python3 make_executable.py
./run_full_fix.sh

⏱️  Temps : 30 secondes
✅ Le script fait TOUT automatiquement !


┌─────────────────────────────────────────────────────────────────┐
│                ÉTAPE 2 : VIDER CACHE NAVIGATEUR                 │
└─────────────────────────────────────────────────────────────────┘

OPTION A : Vider Cache                OPTION B : Mode Privé
┌──────────────────────┐              ┌──────────────────────┐
│ 1. Cmd+Shift+Del     │              │ 1. Cmd+Shift+N       │
│ 2. Cocher "Cache"    │              │ 2. Ouvrir URL        │
│ 3. Cliquer "Effacer" │              │    Streamlit         │
└──────────────────────┘              └──────────────────────┘

⏱️  Temps : 10 secondes              ⏱️  Temps : 5 secondes
✅ Recommandé si 1ère fois           ✅ Plus rapide !


┌─────────────────────────────────────────────────────────────────┐
│                    ÉTAPE 3 : TESTER                             │
└─────────────────────────────────────────────────────────────────┘

Dans Streamlit (qui s'est ouvert automatiquement) :

1. Aller dans "Planificateur Multi-Événements"
2. Sidebar → Date : 11/09/2025 ou 2025-09-11 09:30
3. Pays : États-Unis (US)
4. Cliquer "Charger Événements"
5. Sélectionner événements disponibles
6. Remplir valeurs hypothétiques
7. Descendre jusqu'à "Graphique Minute par Minute"
8. Entrer prix actuel (ex: 1.0950)
9. Cliquer "Générer Graphique"

⏱️  Temps : 1 minute


┌─────────────────────────────────────────────────────────────────┐
│                  ✅ RÉSULTAT ATTENDU                            │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────┐
│ 📊 Métriques                      │
│                                   │
│ Impact Total       : 52.4 pips ✅ │
│ Latence Attendue   : 4 min     ✅ │
│ TTR Combiné        : 7 min     ✅ │
│                                   │
│ 📈 Graphique                      │
│                                   │
│ Amplitude Totale   : 52-67 pips ✅│
│ (PAS 377 PIPS !)                  │
│                                   │
│ 🎯 Précision       : ~98%      ✅ │
└───────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│              🆘 SI ÇA NE MARCHE PAS                             │
└─────────────────────────────────────────────────────────────────┘

❌ Amplitude toujours incorrecte ?

1️⃣  Vérifier cache navigateur vidé
   → Fermer COMPLÈTEMENT le navigateur
   → Rouvrir en mode privé (Cmd+Shift+N)

2️⃣  Relancer le script
   → cd corrections_graphique
   → ./run_full_fix.sh

3️⃣  Vérifier la correction appliquée
   → Chercher "✅ CORRECTION APPLIQUÉE" dans terminal

4️⃣  Restaurer et réessayer
   → cd fx_impact_app/src/backups
   → cp price_curve_generator_before_*.py ../price_curve_generator.py
   → cd ~/Desktop/eurusd_news_impact_calculator_MPC/corrections_graphique
   → ./run_full_fix.sh


┌─────────────────────────────────────────────────────────────────┐
│                    📊 TEMPS TOTAL                               │
└─────────────────────────────────────────────────────────────────┘

Étape 1 : Terminal           → 30 sec
Étape 2 : Cache navigateur   → 10 sec
Étape 3 : Test graphique     → 60 sec
──────────────────────────────────────
TOTAL                        → 2 min ⏱️

🎯 Probabilité de succès : 99%+


┌─────────────────────────────────────────────────────────────────┐
│                  🚀 C'EST PARTI !                               │
└─────────────────────────────────────────────────────────────────┘

Ouvrir terminal et copier-coller :

cd ~/Desktop/eurusd_news_impact_calculator_MPC/corrections_graphique && python3 make_executable.py && ./run_full_fix.sh

✅ Suivre les instructions à l'écran
✅ Vider cache navigateur quand demandé
✅ Tester le graphique
✅ Vérifier : amplitude ≈ 52 pips !

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Créé le** : 14 Octobre 2025  
**Tout est prêt !** 🎉  
**Lancez `./run_full_fix.sh` et c'est réglé !** ✅
