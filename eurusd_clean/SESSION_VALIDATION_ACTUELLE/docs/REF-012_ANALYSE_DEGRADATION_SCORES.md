# REF-012 : Analyse de la Dégradation avec Scores core_scores

**Date :** 2025-12-06  
**Statut :** ❌ **Dégradation significative détectée**

---

## 📊 RÉSULTATS DU TEST COMPARATIF

### Métriques

| Métrique | ACTUEL (event_families) | NOUVEAU (core_scores) | Différence |
|----------|-------------------------|----------------------|------------|
| **MAE** | 5.45 pips | 46.65 pips | **-41.20 pips (-756%)** ❌ |
| **RMSE** | 7.97 pips | 59.85 pips | **-51.88 pips** ❌ |

### Détails par Date

| Date | Core Type | Impact Réel | Prédiction Actuelle | Erreur Actuelle | Prédiction Nouvelle | Erreur Nouvelle | Dégradation |
|------|-----------|-------------|---------------------|-----------------|---------------------|-----------------|-------------|
| 2025-05-29 | JOBLESS_PCE | 89.40 | 74.40 | 15.00 (16.8%) | 77.20 | 12.20 (13.6%) | ✅ -2.80 |
| 2025-09-11 | CPI | 62.40 | 60.70 | 1.70 (2.7%) | 68.50 | 6.10 (9.8%) | ❌ +4.40 |
| 2025-08-01 | NFP | 183.30 | 188.40 | 5.10 (2.8%) | 291.09 | 107.79 (58.8%) | ❌ +102.69 |
| 2025-11-20 | NFP | 36.60 | 36.60 | 0.00 (0.0%) | 65.01 | 28.41 (77.6%) | ❌ +28.41 |

---

## 🔍 ANALYSE DES CAUSES

### Problème 1 : Scores core_scores Trop Élevés

**Hypothèse :** Les scores core_scores sont significativement plus élevés que les scores event_families moyens.

**Exemples :**
- NFP (US) : 80.13 (core_scores) vs ~50-60 (event_families moyen)
- CPI (US) : 75.06 (core_scores) vs ~50-60 (event_families moyen)

**Impact :** Score plus élevé → Impact base plus élevé → Prédiction surestimée

### Problème 2 : Calcul de l'Impact Base

**Formule actuelle :**
```python
impact_base = calculate_impact_d(
    empirical_score=core_score,  # Score élevé (80.13 pour NFP)
    num_events=num_events,
    amplification=1.0,
    correction_factor=0.758
)
```

**Problème :** Le score core_scores représente déjà une **moyenne agrégée** sur plusieurs occurrences, alors que `calculate_impact_d` est conçu pour un score **individuel**.

### Problème 3 : Double Comptage

**Hypothèse :** Les scores core_scores incluent déjà l'effet de plusieurs événements (ex. JOBLESS_PCE = Jobless + PCE), mais on les utilise comme un score unique dans `calculate_impact_d`.

---

## 💡 ALTERNATIVES PROPOSÉES

### Option A : Utiliser Scores core_scores comme Bonus (Addition)

**Principe :** Ajouter un bonus basé sur le score core_scores plutôt que remplacer.

```python
base_score_mean = mean(event_families_scores)  # Score actuel
core_score_bonus = (core_score - base_score_mean) * 0.3  # 30% du bonus
score_final = base_score_mean + core_score_bonus
```

**Avantages :**
- ✅ Conserve la base actuelle qui fonctionne
- ✅ Ajoute information supplémentaire progressivement
- ✅ Moins risqué

### Option B : Utiliser Scores core_scores Uniquement pour Certains Types

**Principe :** Utiliser core_scores uniquement pour types avec sample_size élevé (plus robuste).

```python
if core_type in ['CPI', 'NFP'] and sample_size >= 20:
    # Utiliser score core_scores
    base_score = core_score
else:
    # Fallback : moyenne event_families
    base_score = mean(event_families_scores)
```

**Avantages :**
- ✅ Utilise scores les plus robustes
- ✅ Évite types avec peu de données

### Option C : Moyenne Pondérée

**Principe :** Combiner scores core_scores et event_families avec pondération.

```python
base_score_mean = mean(event_families_scores)
score_final = 0.7 * base_score_mean + 0.3 * core_score
```

**Avantages :**
- ✅ Conserve majorité du comportement actuel
- ✅ Intègre information supplémentaire progressivement

### Option D : Ajuster Formule pour Scores Aggrégés

**Principe :** Modifier `calculate_impact_d` pour tenir compte que core_score est déjà agrégé.

```python
# Si score core_scores utilisé, réduire num_events effectif
effective_num_events = 1  # Score déjà agrégé
impact_base = calculate_impact_d(
    empirical_score=core_score,
    num_events=effective_num_events,  # = 1 au lieu de num_events réel
    amplification=1.0,
    correction_factor=1.0  # Pas de correction vectorielle
)
```

**Avantages :**
- ✅ Utilise directement score core_scores
- ✅ Évite double comptage

---

## 🎯 RECOMMANDATION

**Ne pas intégrer les scores core_scores directement** (dégradation trop importante).

**Tester les alternatives dans l'ordre :**

1. **Option C (Moyenne Pondérée)** : 70% event_families + 30% core_scores
   - Risque minimal
   - Intégration progressive

2. **Option A (Bonus)** : Ajouter 20-30% du bonus
   - Conserve base actuelle
   - Ajoute information supplémentaire

3. **Option D (Ajustement Formule)** : Si Option C/A ne fonctionnent pas
   - Nécessite modification de la logique

4. **Option B (Types Sélectifs)** : En complément
   - Pour types avec sample_size élevé uniquement

---

## 📋 PLAN D'ACTION

1. ✅ Test comparatif effectué → Dégradation détectée
2. ⏳ Tester Option C (Moyenne Pondérée 70/30)
3. ⏳ Si non satisfaisant, tester Option A (Bonus)
4. ⏳ Analyser résultats et décider

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




