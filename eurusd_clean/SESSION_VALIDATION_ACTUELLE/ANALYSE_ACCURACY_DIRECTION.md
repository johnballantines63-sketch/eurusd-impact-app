# Analyse : Pourquoi l'Accuracy Directionnelle Reste à 48%

**Date** : 2025-12-07  
**Problème** : Accuracy directionnelle n'a pas augmenté malgré exclusion surprises nulles

---

## 🔍 Analyse du Problème

### 1. Exclusion Surprises Nulles

**Modification** : Exclusion événements avec `abs(surprise) < 0.1%` du calcul cluster

**Impact Attendu** :
- ✅ Surprise cluster plus représentative
- ✅ Direction plus précise
- ⚠️ **Mais accuracy toujours à 48%**

**Hypothèse** : L'exclusion des surprises nulles améliore la qualité de la surprise cluster, mais ne résout pas le problème fondamental de prédiction directionnelle.

---

## 🎯 Problèmes Identifiés

### Problème 1 : Calcul Direction Individuel vs Cluster

**Approche Actuelle** :
```python
# Pour chaque événement individuellement
direction = get_event_direction(family, surprise)
contribution = direction × surprise × empirical_score
direction_cluster = sign(sum(contributions))
```

**Problème** :
- ⚠️ Chaque événement contribue individuellement
- ⚠️ Pas de prise en compte de l'interaction entre événements
- ⚠️ Familles différentes peuvent s'annuler incorrectement

**Exemple** :
- Événement 1 (CPI, surprise +5%, score 50) → direction = -1 → contribution = -250
- Événement 2 (Jobless, surprise +3%, score 30) → direction = +1 → contribution = +90
- Somme = -160 → Prédit DOWN
- Mais si CPI domine, devrait être DOWN (correct)
- Mais si Jobless est plus important dans ce contexte, pourrait être UP

### Problème 2 : Seuil Surprise Trop Bas (0.1%)

**Actuel** : Exclusion si `abs(surprise) < 0.1%`

**Problème** :
- ⚠️ 0.1% est très faible (peut être du bruit)
- ⚠️ Beaucoup d'événements avec surprise 0.1-0.5% peuvent encore fausser
- ⚠️ Seuil devrait être adaptatif selon type d'événement

**Suggestion** : Tester seuils plus élevés (0.5%, 1.0%)

### Problème 3 : Pondération Linéaire

**Actuel** : `contribution = direction × abs(surprise) × empirical_score`

**Problème** :
- ⚠️ Pondération linéaire : surprise 2x = contribution 2x
- ⚠️ Les grandes surprises devraient avoir plus de poids (non-linéaire)

**Suggestion** : Tester `surprise²` ou `sqrt(surprise)` pour donner plus de poids aux grandes surprises

### Problème 4 : Pas de Fallback pour UNKNOWN

**Actuel** : Si `direction_sum == 0` → UNKNOWN

**Problème** :
- ⚠️ 8 cas UNKNOWN sur 50 (16%)
- ⚠️ Pas de stratégie de fallback (pattern historique, famille dominante, etc.)

**Suggestion** : Implémenter fallback intelligent

---

## 💡 Approches à Tester

### Approche 1 : Seuil Surprise Plus Élevé

```python
# Tester différents seuils
for threshold in [0.1, 0.5, 1.0, 2.0]:
    if abs(surprise) < threshold:
        continue
```

**Hypothèse** : Seuil plus élevé exclut plus de bruit, améliore précision

### Approche 2 : Pondération Non-Linéaire

```python
# Surprise² (donne plus de poids aux grandes surprises)
contribution = direction × (abs(surprise) ** 2) × empirical_score

# OU sqrt(surprise) (atténue les très grandes surprises)
contribution = direction × np.sqrt(abs(surprise)) × empirical_score
```

**Hypothèse** : Les grandes surprises sont plus significatives pour la direction

### Approche 3 : Surprise Cluster + Famille Dominante

```python
# Utiliser surprise cluster directement
surprise_cluster = sum(surprises) / len(surprises)

# Famille dominante (plus grand score total)
dominant_family = max(family_scores, key=family_scores.get)

# Utiliser surprise cluster avec famille dominante
direction = get_event_direction(dominant_family, surprise_cluster)
```

**Hypothèse** : Surprise cluster est plus représentative que somme individuelle

### Approche 4 : Fallback Intelligent

```python
if direction_sum == 0:
    # Fallback 1 : Famille dominante
    dominant_family = get_dominant_family(events)
    direction = get_direction_from_family(dominant_family)
    
    # Fallback 2 : Pattern historique
    if direction == UNKNOWN:
        direction = get_historical_pattern(date)
    
    # Fallback 3 : Tendance pré-événement
    if direction == UNKNOWN:
        direction = get_pre_event_trend(event_time)
```

**Hypothèse** : Réduit cas UNKNOWN, améliore accuracy globale

---

## 📊 Paramètres à Optimiser

1. **Seuil surprise** : 0.1%, 0.5%, 1.0%, 2.0%
2. **Pondération surprise** : linéaire, carré, sqrt
3. **Pondération score** : linéaire, log, sqrt
4. **Stratégie cluster** : individuel, cluster net, famille dominante
5. **Fallback** : aucun, famille dominante, historique, tendance

---

## 🎯 Plan d'Action

1. ✅ **Analyser erreurs actuelles** : Identifier patterns
2. ✅ **Tester seuils différents** : 0.1%, 0.5%, 1.0%
3. ✅ **Tester pondération non-linéaire** : surprise²
4. ✅ **Tester approche cluster** : surprise cluster + famille dominante
5. ⏳ **Implémenter fallback** : Réduire UNKNOWN
6. ⏳ **Valider sur toutes dates** : Comparer approches

---

**Status** : 🔍 **Analyse en cours - Tests à effectuer**


