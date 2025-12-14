# 📋 ANALYSE CLUSTERS APPROFONDIE - HYPOTHÈSES SESSION 92.6

**Date :** 28 octobre 2025  
**Contexte :** Investigation facteur manquant - Théorie des clusters  
**Problème :** 4 dates CPI identiques (11 events, surprise 33%) → Impacts différents (24.6 à 51.7 pips)

---

## 🎯 MISSION PROPOSÉE

### Objectif

**Identifier le facteur manquant qui explique la variance d'impact entre clusters identiques**

### Clusters Analysés

**4 dates CPI avec configuration IDENTIQUE :**

| Date | Nb Events | Surprise Max | Score Ajusté | Impact Réel | Variance vs Référence |
|------|-----------|--------------|--------------|-------------|-----------------------|
| 2025-09-11 | 11 | 33.3% | 84.2 | **51.7 pips** | Référence ✅ |
| 2025-01-15 | 11 | 33.3% | 84.2 | **49.9 pips** | -1.8 pips ✅ |
| 2025-05-13 | 11 | 33.3% | 84.2 | **34.0 pips** | -17.7 pips ❌ |
| 2025-07-15 | 11 | 33.3% | 84.2 | **24.6 pips** | -27.1 pips ❌ |

**Variance : 27.1 pips (de 24.6 à 51.7)**

---

## 🔬 HYPOTHÈSES À TESTER

### ✅ Hypothèse A : Direction Surprise Compte

**Théorie :**
La direction des surprises (CPI > ou < estimé) influence l'impact, pas seulement la magnitude.

**Variables testées :**
1. Ratio ABOVE/BELOW (événements au-dessus vs en-dessous estimate)
2. Surprise nette (somme algébrique des surprises signées)

**Données requises :**
- `actual` et `estimate` pour chaque événement (✅ disponible dans DB)
- Direction surprise : `(actual - estimate) / |estimate| × 100` (signé)

**Résultats :**
- ✅ **TESTÉE Session 92.6** via `analyze_missing_factor.py`
- ✅ **VALIDÉE : Corrélation 0.866** (surprise nette vs impact)
- ✅ Pattern identifié :
  - Surprise nette POSITIVE (+33.6%) → Impact FORT (51.7 pips)
  - Surprise nette NÉGATIVE (-108.5%) → Impact FAIBLE (34.0 pips)

**Explication économique :**
- CPI > estimate → Inflation plus haute → Marché panique → Réaction violente
- CPI < estimate → Inflation plus basse → Marché soulagé → Réaction modérée

**Status : ✅ HYPOTHÈSE VALIDÉE - Formules créées (`calculate_direction_factor`)**

---

### ⏸️ Hypothèse B : Contexte Inflation Élevée Amplifie

**Théorie :**
Le niveau absolu de l'inflation avant l'annonce amplifie ou atténue la réaction du marché.

**Variables à tester :**
1. Niveau CPI tendance (moyenne 3 mois précédents)
2. Tendance inflation (hausse/baisse/stable)
3. Distance vs target Fed (2%)
4. Contexte "hot inflation" vs "cooling inflation"

**Données requises :**
- Historique CPI 3-6 mois avant chaque cluster
- Niveau CPI actuel vs consensus marché
- Distance vs target Fed 2%
- Narrative macro du moment (inflation inquiétante ? sous contrôle ?)

**Hypothèse détaillée :**
- Si inflation ÉLEVÉE (>4%) + surprise POSITIVE → Amplification panique
- Si inflation BASSE (<3%) + surprise POSITIVE → Réaction modérée
- Si inflation ÉLEVÉE + surprise NÉGATIVE → Soulagement amplifié
- Si inflation BASSE + surprise NÉGATIVE → Réaction faible

**Exemples à analyser :**

| Date | CPI Actuel | Tendance 3M | Surprise Net | Impact | Pattern Attendu |
|------|------------|-------------|--------------|--------|-----------------|
| 2025-09-11 | ? | ? | +33.6% | 51.7 pips | Hot inflation + surprise + → Panique ? |
| 2025-05-13 | ? | ? | -108.5% | 34.0 pips | Cooling + surprise - → Soulagement ? |

**Corrélation attendue :**
- Contexte inflation × Surprise nette → Impact
- Interaction non-linéaire possible

**Status : ⏸️ HYPOTHÈSE NON TESTÉE - Données historiques CPI requises**

---

### ⏸️ Hypothèse C : Volatilité Pré-Annonce Compte

**Théorie :**
La volatilité du marché AVANT l'annonce influence l'amplitude de la réaction.

**Variables à tester :**
1. ATR (Average True Range) 1h avant cluster
2. Volatilité implicite (si disponible)
3. Range prix 2h avant annonce
4. Momentum pré-annonce (prix en hausse/baisse avant news)

**Données requises :**
- Prix EURUSD minute par minute
- Calcul ATR 1h avant timestamp cluster
- Range (high - low) 2h avant cluster
- Direction prix (pente 1h avant)

**Hypothèse détaillée :**
- Marché CALME avant + surprise → Réaction AMPLIFIÉE (effet "choc")
- Marché VOLATIL avant + surprise → Réaction ATTÉNUÉE (déjà "pricé")
- Momentum HAUSSIER + CPI ABOVE → Amplification (continuation)
- Momentum BAISSIER + CPI ABOVE → Réaction encore plus forte (reversal)

**Exemples à analyser :**

| Date | ATR 1h avant | Range 2h | Momentum | Surprise Net | Impact | Pattern |
|------|--------------|----------|----------|--------------|--------|---------|
| 2025-09-11 | ? | ? | ? | +33.6% | 51.7 | Calme + surprise → Choc ? |
| 2025-07-15 | ? | ? | ? | -70.0% | 24.6 | Volatil → Atténué ? |

**Corrélation attendue :**
- Volatilité pré-annonce INVERSE corrélation impact
- Marché calme → Réaction forte
- Marché agité → Réaction modérée

**Status : ⏸️ HYPOTHÈSE NON TESTÉE - Données prix EURUSD minute requises**

---

### ⏸️ Hypothèse D : Position dans Cycle Fed Compte

**Théorie :**
Le cycle monétaire de la Fed (haussier/baissier/pause) influence la sensibilité du marché aux données CPI.

**Variables à tester :**
1. Phase cycle Fed (hausse taux / pause / baisse taux)
2. Prochaine réunion FOMC (proximité temporelle)
3. Forward guidance Fed (hawkish / dovish)
4. Attentes marché (probabilités hausse/baisse taux)

**Données requises :**
- Historique décisions Fed (taux directeur)
- Dates réunions FOMC
- Fed Funds futures (probabilités marché)
- Minutes Fed / discours Powell (sentiment)

**Hypothèse détaillée :**

**Cycle HAUSSIER (Fed monte taux) :**
- CPI ABOVE estimate → Amplification (craint plus de hausses)
- CPI BELOW estimate → Soulagement amplifié (espoir pause)

**Cycle BAISSIER (Fed baisse taux) :**
- CPI ABOVE estimate → Réaction modérée (Fed continue baisses)
- CPI BELOW estimate → Validation politique Fed

**Cycle PAUSE (Fed attend) :**
- CPI ABOVE estimate → Déclenche panique (reprise hausses ?)
- CPI BELOW estimate → Confirmation pause

**Exemples à analyser :**

| Date | Phase Fed | Prochaine FOMC | Sentiment | Surprise Net | Impact | Pattern |
|------|-----------|----------------|-----------|--------------|--------|---------|
| 2025-09-11 | ? | ? | ? | +33.6% | 51.7 | Fed hawkish + CPI + → Panique ? |
| 2025-05-13 | ? | ? | ? | -108.5% | 34.0 | Fed pause + CPI - → Modéré ? |

**Corrélation attendue :**
- Cycle Fed × Direction surprise → Impact
- Interaction complexe selon narrative macro

**Status : ⏸️ HYPOTHÈSE NON TESTÉE - Données Fed / FOMC requises**

---

## 📊 RÉCAPITULATIF HYPOTHÈSES

| Hypothèse | Variable | Corrélation Attendue | Status | Corrélation Mesurée |
|-----------|----------|----------------------|--------|---------------------|
| **A** | Direction surprise (nette) | > 0.7 | ✅ **VALIDÉE** | **0.866** |
| **B** | Contexte inflation | > 0.5 | ⏸️ Non testée | N/A |
| **C** | Volatilité pré-annonce | < -0.4 | ⏸️ Non testée | N/A |
| **D** | Cycle Fed | > 0.4 | ⏸️ Non testée | N/A |

---

## 🎯 DÉCISION SESSION 92.6

**André a choisi Option A : Tester Hypothèse A (Direction surprise)**

**Résultat :**
- ✅ Hypothèse A VALIDÉE (corrélation 0.866)
- ✅ Facteur manquant principal IDENTIFIÉ (surprise nette)
- ✅ Formules créées (`calculate_direction_factor`)

**Hypothèses B, C, D mises EN RÉSERVE pour investigations futures**

---

## 🚀 PROCHAINES ÉTAPES (SESSION 92.7 - OPTION B)

**Phase 1 : Validation Surprise Nette**
1. Tester formules sur 4 dates CPI
2. Tester sur 40 dates complètes
3. Valider amélioration MAE

**Phase 2 : Investigation Hypothèse C (Direction_Sentiment)**

**André a choisi d'implémenter Hypothèse C en parallèle :**

**Direction_Sentiment = Combinaison :**
- ⏸️ Volatilité pré-annonce (Hypothèse C)
- ⏸️ Momentum prix (tendance 1h avant)
- ⏸️ Position dans range
- ⏸️ Indicateurs techniques (RSI, MACD)

**Méthodologie :**
1. Charger prix EURUSD 1-2h avant chaque cluster
2. Calculer ATR, range, momentum
3. Créer `calculate_direction_sentiment()` → Score -1 à +1
4. Tester corrélation direction_sentiment vs impact
5. Tester combinaison : surprise_net × direction_sentiment

**Objectif Session 92.7-92.8 :**
- Valider surprise nette (Hypothèse A)
- Implémenter direction_sentiment (Hypothèse C partielle)
- Tester combinaison des deux facteurs

**Hypothèses B et D restent EN RÉSERVE pour futures sessions si nécessaire**

---

## 💡 ORDRE D'IMPLÉMENTATION RECOMMANDÉ

**Session 92.7 (Option B - Phase 1) :**
1. ✅ Valider surprise nette (Hypothèse A déjà testée)
2. 🔄 Implémenter direction_sentiment (Hypothèse C)
3. 🔄 Tester corrélation direction_sentiment

**Session 92.8 (Option B - Phase 2) :**
4. 🔄 Combiner surprise_net + direction_sentiment
5. 🔄 Valider sur 40 dates complètes
6. 🔄 Implémenter dans Planificateur V2.5

**Sessions Futures (Si Amélioration Insuffisante) :**
7. ⏸️ Tester Hypothèse B (Contexte inflation)
8. ⏸️ Tester Hypothèse D (Cycle Fed)

---

## 📁 FICHIERS ASSOCIÉS

```
eurusd_clean/docs/
├── ANALYSE_CLUSTERS_HYPOTHESES.md                (ce document)
├── SESSION92.6_CONTINUATION_RAPPORT_FINAL.md     (rapport complet)
├── APPROCHE_AMPLIFICATION_TYPE_RESERVE.md        (approche en réserve)
└── MESSAGE_SESSION92.6_SESSION92.7_FINAL.md      (handoff)

eurusd_clean/scripts/session92.6/
├── analyze_missing_factor.py                     (test Hypothèse A)
├── formulas_surprise_net.py                      (formules Hypothèse A)
└── test_surprise_net_validation.py               (validation Hypothèse A)
```

---

_Analyse Clusters Approfondie - Hypothèses Session 92.6 - 28 octobre 2025_  
_"Hypothèse A validée (0.866) - Hypothèses B, C, D en réserve" ✅_
