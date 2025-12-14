# REF-013 : Explication Détaillée des 4 Options d'Intégration

**Date :** 2025-12-06  
**Objectif :** Expliquer clairement les 4 alternatives pour intégrer les scores core_scores

---

## 📋 CONTEXTE

**Problème :** L'intégration directe des scores `core_scores` cause une dégradation significative (MAE : 5.45 → 46.65 pips).

**Cause :** Les scores `core_scores` sont trop élevés (ex. 80.13 pour NFP) par rapport aux scores `event_families` moyens (~50-60).

**Solution :** Tester 4 alternatives pour intégrer progressivement les scores `core_scores`.

---

## 🔍 OPTION A : Utiliser Scores core_scores comme Bonus (Addition)

### Principe

Au lieu de **remplacer** les scores `event_families`, on **ajoute un bonus** basé sur la différence entre `core_scores` et la moyenne `event_families`.

### Formule

```python
# Score actuel (moyenne des scores individuels)
base_score_mean = mean(event_families_scores)  # Ex: 50.0

# Bonus basé sur score core_scores
core_score = 80.13  # Ex: NFP
bonus = (core_score - base_score_mean) * 0.3  # 30% du bonus
# bonus = (80.13 - 50.0) * 0.3 = 9.04

# Score final
score_final = base_score_mean + bonus
# score_final = 50.0 + 9.04 = 59.04
```

### Exemple Concret

**Situation :** NFP avec 3 événements
- Scores individuels : 45, 50, 55 → moyenne = 50.0
- Score core_scores : 80.13
- Bonus (30%) : (80.13 - 50.0) × 0.3 = 9.04
- **Score final : 59.04** (au lieu de 50.0 ou 80.13)

### Avantages

✅ **Conserve la base actuelle** qui fonctionne  
✅ **Ajoute information supplémentaire** progressivement  
✅ **Risque minimal** (bonus limité à 30%)  
✅ **Facile à ajuster** (changer le pourcentage)

### Inconvénients

⚠️ Nécessite de calculer la moyenne `event_families` d'abord  
⚠️ Le bonus peut être négatif si `core_score < base_score_mean`

---

## 🔍 OPTION B : Utiliser Scores core_scores Uniquement pour Certains Types

### Principe

Utiliser les scores `core_scores` **uniquement** pour les types de noyaux durs avec un **sample_size élevé** (plus robuste statistiquement).

### Critères de Sélection

```python
# Types avec sample_size élevé (plus robustes)
HIGH_CONFIDENCE_TYPES = {
    'NFP': 43,      # 43 occurrences → robuste
    'CPI': 32,      # 32 occurrences → robuste
    'JOBLESS': 54,  # 54 occurrences → robuste
}

# Types avec sample_size faible (moins robustes)
LOW_CONFIDENCE_TYPES = {
    'JOBLESS_PCE': 20,  # 20 occurrences → acceptable
    'PCE': 14,          # 14 occurrences → faible
    'GDP': ?            # ? occurrences → à vérifier
}
```

### Logique

```python
if core_type in ['NFP', 'CPI', 'JOBLESS'] and sample_size >= 20:
    # Utiliser score core_scores (robuste)
    base_score = core_score
else:
    # Fallback : moyenne event_families (comportement actuel)
    base_score = mean(event_families_scores)
```

### Exemple Concret

**Situation 1 :** NFP (sample_size = 43)
- ✅ Utilise `core_score = 80.13` (robuste)

**Situation 2 :** PCE (sample_size = 14)
- ❌ Utilise `mean(event_families_scores) = 50.0` (fallback)

### Avantages

✅ **Utilise scores les plus robustes** (sample_size élevé)  
✅ **Évite types avec peu de données** (moins fiable)  
✅ **Sélectif** (seulement types validés)

### Inconvénients

⚠️ Incohérence (certains types utilisent core_scores, d'autres non)  
⚠️ Nécessite de définir seuil de sample_size

---

## 🔍 OPTION C : Moyenne Pondérée (Recommandée)

### Principe

**Combiner** les scores `core_scores` et `event_families` avec une **pondération** (ex. 70% event_families + 30% core_scores).

### Formule

```python
# Score actuel (moyenne des scores individuels)
base_score_mean = mean(event_families_scores)  # Ex: 50.0

# Score core_scores
core_score = 80.13  # Ex: NFP

# Moyenne pondérée
score_final = 0.7 * base_score_mean + 0.3 * core_score
# score_final = 0.7 * 50.0 + 0.3 * 80.13
# score_final = 35.0 + 24.04 = 59.04
```

### Exemple Concret

**Situation :** NFP avec 3 événements
- Scores individuels : 45, 50, 55 → moyenne = 50.0
- Score core_scores : 80.13
- **Score final : 0.7 × 50.0 + 0.3 × 80.13 = 59.04**

### Avantages

✅ **Conserve majorité du comportement actuel** (70%)  
✅ **Intègre information supplémentaire** progressivement (30%)  
✅ **Risque minimal** (pondération conservatrice)  
✅ **Facile à ajuster** (changer les pourcentages : 60/40, 80/20, etc.)

### Inconvénients

⚠️ Nécessite de calculer la moyenne `event_families` d'abord  
⚠️ Résultat intermédiaire (ni purement actuel, ni purement nouveau)

---

## 🔍 OPTION D : Ajuster Formule pour Scores Aggrégés

### Principe

Les scores `core_scores` représentent déjà une **moyenne agrégée** sur plusieurs occurrences historiques. Il faut donc **adapter la formule** `calculate_impact_d` pour tenir compte de cela.

### Problème Actuel

```python
# Score core_scores = moyenne sur 43 occurrences NFP
core_score = 80.13  # Déjà agrégé

# Mais on utilise comme score individuel
impact_base = calculate_impact_d(
    empirical_score=core_score,  # 80.13 (trop élevé car déjà agrégé)
    num_events=3,                 # 3 événements dans le cluster
    amplification=1.0,
    correction_factor=0.758       # Correction pour plusieurs événements
)
# → Impact surestimé car double comptage
```

### Solution

```python
# Si score core_scores utilisé, traiter comme score unique
# (car déjà agrégé sur historique)
if use_core_score:
    effective_num_events = 1  # Score déjà agrégé = 1 événement équivalent
    correction_factor = 1.0   # Pas de correction vectorielle
else:
    effective_num_events = num_events  # Nombre réel d'événements
    correction_factor = 0.758          # Correction vectorielle

impact_base = calculate_impact_d(
    empirical_score=core_score,
    num_events=effective_num_events,  # = 1 au lieu de 3
    amplification=1.0,
    correction_factor=correction_factor  # = 1.0 au lieu de 0.758
)
```

### Exemple Concret

**Situation :** NFP avec 3 événements
- Score core_scores : 80.13 (déjà agrégé sur 43 occurrences)
- **Option D :** `num_events = 1` (score déjà agrégé)
- Impact base : Calculé avec `num_events=1` au lieu de `num_events=3`

### Avantages

✅ **Utilise directement score core_scores** (pas de moyenne)  
✅ **Évite double comptage** (num_events = 1)  
✅ **Logique cohérente** (score agrégé = 1 événement équivalent)

### Inconvénients

⚠️ **Nécessite modification de la logique** `calculate_impact_d`  
⚠️ **Plus complexe** (gestion de deux cas)  
⚠️ **Risque d'erreur** si logique mal implémentée

---

## 📊 COMPARAISON DES 4 OPTIONS

| Option | Complexité | Risque | Amélioration Attendue | Recommandation |
|--------|------------|--------|----------------------|----------------|
| **A (Bonus)** | Faible | Minimal | Modeste | ✅ À tester |
| **B (Sélectif)** | Moyenne | Faible | Modérée | ⚠️ Si Option C échoue |
| **C (Pondérée)** | Faible | Minimal | Modeste | ✅ **RECOMMANDÉE** |
| **D (Ajustement)** | Élevée | Moyen | Potentiellement élevée | ⚠️ Si autres échouent |

---

## 🎯 RECOMMANDATION FINALE

### Ordre de Test

1. **Option C (Moyenne Pondérée 70/30)** ⭐ **RECOMMANDÉE**
   - Risque minimal
   - Facile à implémenter
   - Intégration progressive

2. **Option A (Bonus 30%)**
   - Si Option C ne fonctionne pas
   - Alternative simple

3. **Option B (Sélectif)**
   - En complément de Option C
   - Pour types robustes uniquement

4. **Option D (Ajustement Formule)**
   - Si toutes les autres échouent
   - Nécessite plus de travail

---

## 💡 EXEMPLE VISUEL

### Situation : NFP avec 3 événements

**Scores individuels :** 45, 50, 55  
**Moyenne event_families :** 50.0  
**Score core_scores :** 80.13

| Option | Calcul | Score Final | Impact sur Prédiction |
|--------|--------|-------------|----------------------|
| **Actuel** | `mean([45, 50, 55])` | **50.0** | Baseline |
| **Option A** | `50.0 + (80.13-50.0)×0.3` | **59.04** | +18% |
| **Option B** | `80.13` (si sample_size≥20) | **80.13** | +60% |
| **Option C** | `0.7×50.0 + 0.3×80.13` | **59.04** | +18% |
| **Option D** | `80.13` avec `num_events=1` | **80.13** | Variable selon formule |

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




