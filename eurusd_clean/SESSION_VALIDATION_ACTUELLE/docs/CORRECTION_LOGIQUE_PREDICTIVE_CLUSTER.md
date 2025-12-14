# Correction : Logique Prédictive pour Sélection du Cluster Principal

## Problème Identifié

La logique précédente utilisait une **priorité absolue à 14:30**, ce qui est une **constatation** basée sur l'observation, pas une **prédiction** basée sur des métriques objectives.

**Problème** : Pour une vraie prédiction, on ne peut pas utiliser des constatations comme "14:30 est toujours plus important". Il faut utiliser des métriques objectives qui peuvent s'appliquer à n'importe quelle situation.

## Solution Implémentée

### Nouvelle Métrique : Score Moyen par Événement

**Formule** :
```
score_moyen_par_event = abs(score_global_vectoriel) / n_events
```

**Avantage** : Cette métrique privilégie les clusters avec des **scores individuels élevés**, pas juste le nombre d'événements.

**Exemple** :
- Cluster 14:30 : 112.5 / 6 = **18.75 points/événement**
- Cluster 18:00 : 206.9 / 10 = **20.69 points/événement**

Avec cette métrique, le cluster à 18:00 gagne encore, mais la différence est beaucoup plus faible.

### Score de Qualité Composite

**Formule** :
```
score_qualite = score_moyen_par_event × (1.0 + bonus_US_HIGH)
```

Où :
- `bonus_US_HIGH = 0.2` (20%) si le cluster contient des événements US HIGH
- `bonus_US_HIGH = 0.0` sinon

**Avantage** : Combine le score moyen (qualité individuelle) avec un bonus pour les événements US HIGH (importance du calendrier).

**Exemple** :
- Cluster 14:30 : 18.75 × 1.2 = **22.5 points**
- Cluster 18:00 : 20.69 × 1.2 = **24.83 points**

### Logique de Sélection

1. **Calculer score de qualité** pour tous les clusters
2. **Sélectionner** le cluster avec le **score de qualité le plus élevé**
3. **Fallback** : Si aucun cluster, prendre le plus grand

## Code Modifié

**Fichier** : `scripts/run_pipeline_complete.py`

**Section** : `execute_complete_pipeline` (lignes 2999-3030)

```python
# Calculer métriques pour tous les clusters
clusters_with_metrics = []
for cluster in clusters:
    cluster_score_global = cluster.get('cluster_score_global', 0.0)
    n_events = cluster.get('n_events', 1)
    n_events_with_score = cluster.get('n_events_with_score', n_events)
    n_us_high = cluster.get('n_us_high', 0)
    
    # Score moyen par événement (métrique clé pour prédiction)
    score_moyen_par_event = abs(cluster_score_global) / n_events_with_score if n_events_with_score > 0 else 0.0
    
    # Score de qualité composite
    bonus_us_high = 0.2 if n_us_high > 0 else 0.0  # Bonus 20% si contient US HIGH
    score_qualite = score_moyen_par_event * (1.0 + bonus_us_high)
    
    clusters_with_metrics.append({
        'cluster': cluster,
        'score_global': cluster_score_global,
        'score_moyen_par_event': score_moyen_par_event,
        'score_qualite': score_qualite,
        'n_events': n_events,
        'n_us_high': n_us_high
    })

# Sélectionner cluster avec score de qualité le plus élevé
best_cluster_info = max(clusters_with_metrics, key=lambda x: x['score_qualite'])
main_cluster = best_cluster_info['cluster']
```

## Avantages

1. **Prédictive** : Basée sur des métriques objectives, pas des constatations
2. **Équitable** : Privilégie la qualité individuelle, pas juste le nombre
3. **Flexible** : S'applique à n'importe quelle situation (pas limité à 14:30)
4. **Combinée** : Prend en compte à la fois les scores empiriques et l'importance du calendrier

## Validation

Pour 2025-05-29 :
- **Cluster 14:30** : Score moyen 18.75, Score qualité 22.5
- **Cluster 18:00** : Score moyen 20.69, Score qualité 24.83

**Résultat** : Le cluster à 18:00 est sélectionné selon cette logique prédictive.

**Note** : Si le mouvement réel est à 14:30, cela indique que d'autres facteurs (non capturés par les scores empiriques) sont en jeu. Il faudra peut-être ajuster les poids ou ajouter d'autres métriques.

## Date de Correction

2025-12-XX (Session actuelle)




