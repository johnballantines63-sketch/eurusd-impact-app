# 📊 GUIDE VISUEL - RESTAURATION & CORRECTION

```
┌─────────────────────────────────────────────────────────────┐
│                    SITUATION ACTUELLE                        │
└─────────────────────────────────────────────────────────────┘

Version fichier : ✅ STABLE (avant pullback V5)
Backup créé    : ✅ before_pullback_v5_20251014_101318.py
Amplitude      : 🎯 ~120-159 pips (attendue)


┌─────────────────────────────────────────────────────────────┐
│                    ÉVOLUTION AMPLITUDE                       │
└─────────────────────────────────────────────────────────────┘

Initial         : 463 pips  ❌ Bug boucle Planificateur
    ↓
V4 CRITIQUE     : 159 pips  ✅ Correction appliquée
    ↓
V5 Pullback     : 230 pips  ❌ Bug "double négatif"
    ↓
RESTAURATION    : 159 pips  ✅ VERSION ACTUELLE (stable)
    ↓
V6 Pullback     : 159 pips  🔧 Correction disponible (+ pullback)


┌─────────────────────────────────────────────────────────────┐
│                    2 CHEMINS POSSIBLES                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────┐
│   CHEMIN A : STABLE     │         │  CHEMIN B : PULLBACK V6 │
│   (recommandé si OK)    │         │  (si besoin réalisme)   │
└─────────────────────────┘         └─────────────────────────┘
         │                                     │
         │ 1. Vider cache                     │ 1. cd corrections_pullback_v6
         │ 2. Tester                           │ 2. ./run_pullback_v6_correction.sh
         │ 3. Valider ~159 pips               │ 3. Vider cache
         │                                     │ 4. Tester
         ↓                                     ↓
    ┌─────────┐                          ┌─────────┐
    │  FINI   │                          │ VALIDER │
    └─────────┘                          └─────────┘
                                              │
                                         ┌────┴────┐
                                         │         │
                                    ✅ OK      ❌ Rollback
                                         │         │
                                    Garder      Revenir
                                     V6        stable


┌─────────────────────────────────────────────────────────────┐
│                    BUG CORRIGÉ EN V6                         │
└─────────────────────────────────────────────────────────────┘

❌ AVANT (V5) :
base_contribution -= pullback_amount * (1 if vectorial > 0 else -1)
│
└─→ Problème : Soustraction crée un rebond → dérive 230 pips

✅ APRÈS (V6) :
pullback_level = 1.0 - (0.35 * pullback_intensity)
base_contribution = vectorial * sigmoid * pullback_level
│
└─→ Solution : Substitution propre → stable 159 pips


┌─────────────────────────────────────────────────────────────┐
│                    COMMANDES RAPIDES                         │
└─────────────────────────────────────────────────────────────┘

# Garder version stable
find . -name "__pycache__" -exec rm -rf {} +

# Appliquer correction V6
cd corrections_pullback_v6 && ./run_pullback_v6_correction.sh

# Rollback si problème
cp fx_impact_app/src/backups/price_curve_generator_before_pullback_v5_*.py \
   fx_impact_app/src/price_curve_generator.py


┌─────────────────────────────────────────────────────────────┐
│                    TESTS À FAIRE                             │
└─────────────────────────────────────────────────────────────┘

Date      : 11/09/2025
Prix      : 1.16810
Attendu   : ~159 pips (stable) ou ~159 pips + pullback (V6)

✅ Vérifier :
   □ Amplitude dans la plage attendue
   □ Pas de dérive (tester plusieurs fois)
   □ Pattern réaliste (si V6)
   □ Cache vidé avant test


┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENTATION                             │
└─────────────────────────────────────────────────────────────┘

Resume sessions Claude/
├── session_14oct2025_RESUME_COMPLET_FINAL.md  ← Historique
├── session_14oct2025_RESTAURATION.md          ← Détails
└── [CE FICHIER]                                ← Vue d'ensemble

corrections_pullback_v6/
├── ACTIONS_RAPIDES.md      ← Guide concis
├── README.md               ← Documentation complète
└── run_*.sh                ← Scripts d'exécution


┌─────────────────────────────────────────────────────────────┐
│                  DÉCISION RECOMMANDÉE                        │
└─────────────────────────────────────────────────────────────┘

1. ✅ Tester version STABLE d'abord
2. 📊 Vérifier amplitude (~159 pips)
3. 🤔 Décider :
   • Si OK      → Garder stable (FINI)
   • Si pas OK  → Analyser le problème
   • Si besoin pullback → Tester V6

4. 🎯 Toujours vider cache avant test !


┌─────────────────────────────────────────────────────────────┐
│                    PHRASE MAGIQUE                            │
└─────────────────────────────────────────────────────────────┘

"Suite restauration 14/10/2025.
Version : [stable / pullback V6]
Amplitude : [VALEUR] pips
Choix : [garder / corriger / problème]"

```

---

**Créé le** : 14 Octobre 2025  
**Par** : Claude (Anthropic)  
**Pour** : André Valentin  
**Projet** : EUR/USD News Impact Calculator
