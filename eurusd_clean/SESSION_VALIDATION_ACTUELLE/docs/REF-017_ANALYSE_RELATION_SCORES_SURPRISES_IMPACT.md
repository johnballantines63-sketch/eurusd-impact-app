# REF-017 : Analyse Relation Scores → Surprises → Impact

**Date :** 2025-12-06  
**Objectif :** Identifier des patterns récurrents entre scores individuels, surprises et impacts réels pour améliorer les prédictions

---

## 📊 RÉSUMÉ EXÉCUTIF

### Objectif
Comprendre la relation entre :
- **Scores individuels** des événements core
- **Surprises** (écart entre actual et estimate)
- **Score global du noyau dur** (combinaison des scores)
- **Impact réel** mesuré sur le marché

### Méthodes de Calcul Testées

1. **WEIGHTED_SUM** : `sum(score × importance_n)`
2. **WEIGHTED_AVG** : `sum(score × importance_n) / sum(importance_n)`
3. **VECTORIAL_SUM** : `sum(score × direction × (1 + abs(surprise)/100))`
4. **MAX_SCORE** : `max(scores)`
5. **ADJUSTED_SUM** : `sum(score_ajusté_surprise)`

---

## 📈 RÉSULTATS PAR DATE

### 2025-09-11 (CPI)

**Noyau dur :** 6 événements CPI (5 avec estimate valide)

| Event Key | Score | Imp | Estimate | Actual | Surprise | Adj Score |
|-----------|-------|-----|----------|--------|----------|-----------|
| core inflation rate mom | 84.4 | 1 | 0.30 | 0.30 | 0.0% | 84.4 |
| core inflation rate yoy | 84.4 | 1 | 3.10 | 3.10 | 0.0% | 84.4 |
| cpi | 84.4 | 2 | 323.89 | 323.98 | +0.0% | 84.4 |
| inflation rate mom | 84.4 | 1 | 0.30 | 0.40 | **+33.3%** | 160.3 |
| inflation rate yoy | 84.4 | 1 | 2.90 | 2.90 | 0.0% | 84.4 |

**Scores calculés :**
- Score core_scores (DB) : **75.06**
- Score global (weighted_avg) : **84.38**
- Surprise nette : **+33.36%**
- Impact réel : **62.40 pips**

**Ratio Impact/Score :**
- Impact / Score core_scores : **0.831**
- Impact / Score weighted_avg : **0.740**

---

### 2025-05-29 (JOBLESS_PCE)

**Noyau dur :** 5 événements (4 avec estimate valide)

| Event Key | Score | Imp | Estimate | Actual | Surprise | Adj Score |
|-----------|-------|-----|----------|--------|----------|-----------|
| continuing jobless claims | 54.8 | 3 | 1890.00 | 1919.00 | +1.5% | 54.8 |
| core pce prices qoq 2nd est | 47.0 | 3 | 3.50 | 3.40 | -2.9% | 47.0 |
| initial jobless claims | 54.8 | 2 | 230.00 | 240.00 | +4.3% | 54.8 |
| pce prices qoq 2nd est | 47.0 | 3 | 3.60 | 3.60 | 0.0% | 47.0 |

**Scores calculés :**
- Score core_scores (DB) : **53.51**
- Score global (weighted_avg) : **50.53**
- Surprise nette : **+3.03%**
- Impact réel : **89.40 pips**

**Ratio Impact/Score :**
- Impact / Score core_scores : **1.671**
- Impact / Score weighted_avg : **1.769**

**Observation :** Impact beaucoup plus élevé que le score suggère (ratio > 1.7)

---

### 2025-08-01 (NFP)

**Noyau dur :** 2 événements NFP

| Event Key | Score | Imp | Estimate | Actual | Surprise | Adj Score |
|-----------|-------|-----|----------|--------|----------|-----------|
| non farm payrolls | 80.7 | 1 | 50.00 | 119.00 | **+138.0%** | 153.2 |
| nonfarm payrolls private | 80.7 | 3 | 62.00 | 97.00 | +56.5% | 153.2 |

**Scores calculés :**
- Score core_scores (DB) : **80.13**
- Score global (weighted_avg) : **80.65**
- Surprise nette : **-50.64%** (somme vectorielle)
- Surprise abs : **50.64%**
- Impact réel : **188.40 pips**

**Ratio Impact/Score :**
- Impact / Score core_scores : **2.348**
- Impact / Score weighted_avg : **2.335**

**Observation :** Impact très élevé (ratio > 2.3) malgré surprise modérée

---

### 2025-11-20 (NFP)

**Noyau dur :** 2 événements NFP

| Event Key | Score | Imp | Estimate | Actual | Surprise | Adj Score |
|-----------|-------|-----|----------|--------|----------|-----------|
| non farm payrolls | 80.7 | 1 | 50.00 | 119.00 | **+138.0%** | 153.2 |
| nonfarm payrolls private | 80.7 | 3 | 62.00 | 97.00 | +56.5% | 153.2 |

**Scores calculés :**
- Score core_scores (DB) : **80.13**
- Score global (weighted_avg) : **80.65**
- Surprise nette : **+194.45%**
- Impact réel : **35.50 pips**

**Ratio Impact/Score :**
- Impact / Score core_scores : **0.443**
- Impact / Score weighted_avg : **0.440**

**Observation :** Surprise très élevée (194%) mais impact faible (35.5 pips) - **contre-intuitif**

---

## 🔍 ANALYSE DES CORRÉLATIONS

### Corrélations Calculées

| Relation | Corrélation | Interprétation |
|----------|-------------|----------------|
| **Score core_scores ↔ Impact réel** | **0.110** | Très faible corrélation |
| **Surprise abs ↔ Impact réel** | **-0.449** | Corrélation négative modérée |
| **Score global (weighted_sum) ↔ Impact réel** | **-0.280** | Corrélation négative faible |

### Observations Critiques

1. **Score seul insuffisant** : Corrélation très faible (0.110) entre score core_scores et impact réel
2. **Surprise ≠ Impact** : Corrélation négative (-0.449) suggère que surprise élevée ne garantit pas impact élevé
3. **Cas contradictoires** :
   - 2025-11-20 : Surprise 194% → Impact 35.5 pips (faible)
   - 2025-08-01 : Surprise 50% → Impact 188.4 pips (élevé)

---

## 💡 PATTERNS IDENTIFIÉS

### Pattern 1 : Ratio Impact/Score Variable

| Date | Core Type | Score DB | Impact Réel | Ratio | Catégorie |
|------|-----------|----------|-------------|-------|-----------|
| 2025-09-11 | CPI | 75.06 | 62.40 | 0.831 | Normal |
| 2025-05-29 | JOBLESS_PCE | 53.51 | 89.40 | 1.671 | **Sous-estimé** |
| 2025-08-01 | NFP | 80.13 | 188.40 | 2.348 | **Très sous-estimé** |
| 2025-11-20 | NFP | 80.13 | 35.50 | 0.443 | **Sur-estimé** |

**Observation :** Le ratio varie de 0.44 à 2.35, suggérant que d'autres facteurs influencent l'impact.

### Pattern 2 : Surprise vs Impact

| Date | Surprise Abs | Impact Réel | Relation |
|------|--------------|-------------|----------|
| 2025-09-11 | 33.36% | 62.40 pips | Modérée |
| 2025-05-29 | 3.03% | 89.40 pips | **Faible surprise, fort impact** |
| 2025-08-01 | 50.64% | 188.40 pips | Modérée surprise, très fort impact |
| 2025-11-20 | 194.45% | 35.50 pips | **Très forte surprise, faible impact** |

**Observation :** Aucune relation linéaire évidente entre surprise et impact.

### Pattern 3 : Type de Core Event

| Core Type | Score DB Moyen | Impact Réel Moyen | Ratio Moyen |
|-----------|----------------|-------------------|-------------|
| CPI | 75.06 | 62.40 | 0.831 |
| JOBLESS_PCE | 53.51 | 89.40 | 1.671 |
| NFP | 80.13 | 111.95 | 1.396 |

**Observation :** JOBLESS_PCE et NFP ont des ratios plus élevés que CPI.

---

## 🎯 FACTEURS NON CAPTURÉS PAR LE SCORE

### Facteurs Potentiels

1. **Contexte de marché** :
   - Tendance pré-événement
   - Volatilité
   - Sentiment général

2. **Timing** :
   - Heure de publication
   - Chevauchement avec autres événements
   - Jour de la semaine

3. **Amplification** :
   - Formule Session 88 pour surprises extrêmes
   - Random Forest (si entraîné)
   - Ajustements support/résistance

4. **Pattern détecté** :
   - Single Wave vs Double Wave
   - Confiance du pattern
   - Timings réels vs prédits

---

## 🔧 PISTES D'AMÉLIORATION

### 1. Intégrer Score Global dans Pipeline

**Proposition :** Utiliser le score global (weighted_avg) comme facteur supplémentaire dans la prédiction d'impact.

**Formule proposée :**
```python
impact_predicted = (
    score_global_weighted_avg × 
    amplification_factor × 
    context_factor × 
    pattern_factor
)
```

### 2. Ajuster selon Ratio Historique

**Proposition :** Calculer le ratio moyen Impact/Score pour chaque core_type et l'utiliser comme multiplicateur.

**Exemple :**
- CPI : Ratio moyen = 0.831 → Multiplicateur = 0.83
- JOBLESS_PCE : Ratio moyen = 1.671 → Multiplicateur = 1.67
- NFP : Ratio moyen = 1.396 → Multiplicateur = 1.40

### 3. Intégrer Surprise Nette (Vectorielle)

**Proposition :** Utiliser la surprise nette (somme vectorielle) pour ajuster l'amplification, pas seulement la surprise absolue.

**Logique :**
- Surprise nette positive → Amplification UP
- Surprise nette négative → Amplification DOWN
- Surprise nette faible → Amplification modérée

### 4. Random Forest avec Features Enrichies

**Proposition :** Ajouter au Random Forest :
- Score global (weighted_avg)
- Surprise nette (vectorielle)
- Ratio historique Impact/Score pour core_type
- Nombre d'événements core
- Direction nette

### 5. Validation avec Plus de Données

**Proposition :** Étendre l'analyse à toutes les dates avec core_scores calculés (32+ dates pour CPI, etc.)

---

## 📋 PROCHAINES ÉTAPES

### Étape 1 : Validation Données ✅
- [x] Vérifier données Finnhub
- [x] Recalculer core_scores
- [x] Mesurer impacts réels correctement

### Étape 2 : Analyse Relation (EN COURS)
- [x] Calculer scores globaux
- [x] Identifier corrélations
- [x] Documenter patterns

### Étape 3 : Tests Alternatives
- [ ] Tester intégration score global dans pipeline
- [ ] Tester ajustement selon ratio historique
- [ ] Tester Random Forest enrichi
- [ ] Comparer performances

### Étape 4 : Validation Multi-Dates
- [ ] Étendre à toutes les dates avec core_scores
- [ ] Calculer ratios moyens par core_type
- [ ] Identifier outliers et causes

---

## 📊 TABLEAU RÉCAPITULATIF COMPLET

| Date | Core Type | Score DB | Score Global (avg) | Surprise | Impact Réel | Ratio | Catégorie |
|------|-----------|----------|---------------------|----------|-------------|-------|-----------|
| 2025-09-11 | CPI | 75.06 | 84.38 | 33.36% | 62.40 | 0.831 | Normal |
| 2025-05-29 | JOBLESS_PCE | 53.51 | 50.53 | 3.03% | 89.40 | 1.769 | Sous-estimé |
| 2025-08-01 | NFP | 80.13 | 80.65 | 50.64% | 188.40 | 2.335 | Très sous-estimé |
| 2025-11-20 | NFP | 80.13 | 80.65 | 194.45% | 35.50 | 0.440 | Sur-estimé |

---

## 🎯 CONCLUSION

### Constats Principaux

1. **Score seul insuffisant** : Corrélation très faible (0.110) avec impact réel
2. **Surprise ≠ Impact** : Corrélation négative (-0.449) - surprise élevée ne garantit pas impact élevé
3. **Ratio variable** : Impact/Score varie de 0.44 à 2.35 selon les cas
4. **Facteurs multiples** : D'autres facteurs (contexte, timing, pattern) influencent l'impact

### Recommandations

1. **Intégrer score global** comme facteur supplémentaire (pas remplacement)
2. **Utiliser ratio historique** par core_type comme multiplicateur
3. **Enrichir Random Forest** avec nouvelles features
4. **Valider sur plus de dates** avant d'implémenter

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06  
**Fichier CSV :** `SESSION_VALIDATION_ACTUELLE/outputs/analyse_relation_scores_surprises_impact.csv`




