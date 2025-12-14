# 📋 APPROCHE AMPLIFICATION PAR TYPE - EN RÉSERVE

**Date :** 28 octobre 2025  
**Status :** ⏸️ **EN RÉSERVE - Non implémentée**  
**Raison :** Facteur manquant identifié - Réplicabilité non validée

---

## 📊 RÉSULTATS GRID SEARCH SESSION 92.6

### Amplifications Trouvées

| Type | Amp | MAE (pips) | Nb Dates | Amélioration vs Baseline |
|------|-----|------------|----------|--------------------------|
| CPI | 2.2 | 10.8 | 10 | 21.3% (13.7 → 10.8 pips) |
| ISM | 0.5 | 7.4 | 9 | 92.1% (93.2 → 7.4 pips) |
| FOMC | 1.0 | 2.8 | 3 | 88.4% (24.1 → 2.8 pips) |
| NFP | 1.4 | 27.8 | 10 | 24.7% (36.9 → 27.8 pips) |

**MAE Globale :**
- Baseline V2.4 : 43.7 pips
- Grid Search : 13.6 pips
- **Amélioration : 68.9%**

---

## ⚠️ PROBLÈME IDENTIFIÉ - RÉPLICABILITÉ

### Cluster CPI Test Case

**Configuration identique testée :**
- 11 événements CPI
- Surprise 33.3%
- Score ajusté 84.2

**Résultats sur 4 dates :**

| Date | Impact Réel | Erreur avec Amp 2.27 | Status |
|------|-------------|----------------------|--------|
| 2025-09-11 | 51.7 pips | 0.1 pips | ✅ Référence |
| 2025-01-15 | 49.9 pips | 1.2 pips | ✅ OK |
| 2025-05-13 | 34.0 pips | 17.1 pips | ❌ Échec |
| 2025-07-15 | 24.6 pips | 26.5 pips | ❌ Échec |

**Taux réussite : 50% seulement**

**Variation impact : 24.6 à 51.7 pips (27.1 pips d'écart)**

**Conclusion :** Un facteur additionnel NON capturé influence l'impact réel

---

## 🔬 FACTEUR MANQUANT - HYPOTHÈSES

### Variables Actuellement Prises en Compte
- ✅ Nombre d'événements
- ✅ Score empirique
- ✅ Surprise % (amplitude)
- ✅ Type d'événement (CPI, NFP, etc.)

### Variables NON Prises en Compte (Hypothèses)
- ❓ **Direction de la surprise** (CPI > ou < estimé)
- ❓ **Contexte économique** (inflation élevée/faible, récession/croissance)
- ❓ **Cycle monétaire** (Fed haussière/baissière)
- ❓ **Volatilité pré-annonce** (marché calme/agité)
- ❓ **Sentiment marché** (risk-on/risk-off)
- ❓ **Timing dans cycle** (début/milieu/fin de tendance)
- ❓ **Attentes marché** (CPI attendu vs consensus)

---

## 📋 INVESTIGATION EN COURS

**Session 92.6 Continuation :** Analyse facteur manquant

**Données requises :**
1. Direction surprise (actual > ou < estimate) pour 4 dates CPI
2. Contexte macro (niveau inflation, cycle Fed)
3. Volatilité pré-annonce
4. Autres variables contextuelles

**Objectif :**
- Identifier variable explicative de la variance
- Intégrer dans formules si pertinent
- Re-tester réplicabilité

---

## 🎯 DÉCISION FINALE

**SI facteur identifié et validé :**
→ Intégrer dans formules, re-tester Grid Search, puis implémenter

**SI aucun facteur trouvé :**
→ Conserver baseline 2.5, attendre plus de données

**EN ATTENDANT :**
→ Approche amplification par type EN RÉSERVE (non implémentée)

---

## 📊 MÉTHODOLOGIE VALIDÉE (À Conserver)

**Grid Search conforme 100% :**
- ✅ Query SQL identique Planificateur
- ✅ Calcul surprise identique
- ✅ Ajustement score (Session 55)
- ✅ Formules multi-événements avec facteur 0.758 (Session 51)

**Méthodologie correcte, mais données hétérogènes sans vrai clustering**

---

## 📁 DOCUMENTS ASSOCIÉS

```
eurusd_clean/docs/
├── SESSION92.6_RAPPORT_COMPLET.md           (analyse complète Grid Search)
├── MESSAGE_SESSION92.6_SESSION92.7.md        (handoff - obsolète)
└── APPROCHE_AMPLIFICATION_TYPE_RESERVE.md    (ce document)

eurusd_clean/scripts/session92.6/
├── grid_search_amplification_by_type.py      (script Grid Search)
└── grid_search_results_session92.6.csv       (résultats)
```

---

_Approche Amplification par Type - En Réserve - 28 octobre 2025_  
_"Amélioration 68.9% prouvée, mais réplicabilité non validée - Investigation facteur manquant en cours"_
