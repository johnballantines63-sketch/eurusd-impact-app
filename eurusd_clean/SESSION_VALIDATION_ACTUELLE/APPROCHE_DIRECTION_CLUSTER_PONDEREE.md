# Approche Direction Cluster Pondérée

**Date** : 2025-12-07  
**Question** : Calculer direction depuis surprise cluster (somme vectorielle pondérée par scores)

---

## ✅ Votre Observation est Correcte

Pour prédire la direction d'un **cluster**, il faut :

1. ✅ **Calculer surprise cluster** : Somme vectorielle des surprises individuelles
2. ✅ **Pondérer par scores** : Événements importants (score élevé) ont plus de poids
3. ✅ **Utiliser surprise cluster** pour déterminer la direction

---

## 🔍 Approche Actuelle

### Dans `validate_on_new_dates.py`

J'ai implémenté :

```python
# Contribution pondérée = direction × surprise × poids (empirical_score)
for event in cluster_events:
    direction = get_event_direction(family, surprise)
    contribution = direction * abs(surprise) * empirical_score
    contributions.append(contribution)

direction_cluster = sign(sum(contributions))
```

**Résultat** : Accuracy 48% (insuffisant)

---

## 💡 Approche Alternative Proposée

### Option : Surprise Cluster Pondérée + Famille Dominante

```python
# 1. Calculer surprise cluster pondérée par scores
weighted_surprises = []
weights = []
families = []

for event in cluster_events:
    surprise = calculate_event_surprise(...)
    weight = event['empirical_score']
    family = event['family']
    
    if abs(surprise) > 0.1:  # Seuil minimum
        weighted_surprises.append(surprise * weight)
        weights.append(weight)
        families.append(family)

if weights:
    # Surprise cluster pondérée
    surprise_cluster = sum(weighted_surprises) / sum(weights)
    
    # Famille dominante (celle avec le plus grand score total)
    family_scores = {}
    for event in cluster_events:
        family = event['family']
        score = event['empirical_score']
        family_scores[family] = family_scores.get(family, 0) + score
    
    dominant_family = max(family_scores, key=family_scores.get)
    
    # Utiliser surprise cluster avec famille dominante
    direction = get_event_direction(
        family=dominant_family,
        surprise=surprise_cluster
    )
    
    direction_predicted = 'UP' if direction > 0 else 'DOWN'
else:
    direction_predicted = 'UNKNOWN'
```

---

## 📊 Comparaison

| Approche | Accuracy | Avantages | Inconvénients |
|----------|----------|-----------|---------------|
| **Contributions pondérées** (actuelle) | 48% | Tient compte de toutes les familles | Complexe, peut s'annuler |
| **Surprise cluster + famille dominante** | À tester | Plus simple, utilise surprise cluster | Ignore autres familles |

---

## 🎯 Recommandation

**Tester les deux approches** et choisir la meilleure :

1. **Approche actuelle** : Contributions directionnelles pondérées
2. **Approche alternative** : Surprise cluster pondérée + famille dominante

---

**Status** : 🔍 **Analyse en cours - Approche alternative à tester**


