# Correction : Score Vectoriel pour Identification Cluster

## Problème Identifié

Lors de l'identification du cluster principal (Étape 2), le pipeline utilisait une **somme simple** des scores individuels des événements. Cela pouvait mener à rater des clusters importants si les scores individuels étaient faibles, même si plusieurs événements arrivaient en même temps.

**Exemple problématique** :
- 6 événements US HIGH à 14:30 avec scores individuels 20-40
- Somme simple : 150-240 (peut être insuffisant si seuil > 200)
- Mais si événements se renforcent (même direction) ou s'annulent (directions opposées), la somme vectorielle est plus précise

## Solution Implémentée

### Calcul de Score Vectoriel (Session 105)

Le score global du cluster est maintenant calculé avec une **somme vectorielle** :

1. **Pour chaque événement** :
   - Obtenir `empirical_score` (score de base)
   - Obtenir `family` (famille de l'événement)
   - Calculer `surprise` si disponible (actual - estimate)
   - Calculer `direction` avec `get_event_direction(family, surprise)`
   - Calculer `score_vectoriel = score_base × direction`

2. **Somme vectorielle** :
   - `cluster_score_global = sum(scores_vectoriels)`

### Avantages

- **Précision** : Tient compte de la direction des événements (bullish/bearish)
- **Neutralisation** : Événements opposés s'annulent correctement
- **Renforcement** : Événements dans la même direction se renforcent
- **Cohérence** : Utilise la même logique que les formules validées (Session 105)

## Code Modifié

**Fichier** : `scripts/run_pipeline_complete.py`

**Section** : `etape2_detecter_clusters` (lignes 316-361)

```python
# ⚠️ NOUVEAU : Calculer score global du cluster (SOMME VECTORIELLE)
# Permet d'identifier le cluster principal même si scores individuels sont faibles
# Utilise addition vectorielle : score_vectoriel = score_ajusté × direction
# Documentation : Combinaison scores individuels pour identification cluster (Session 105)
cluster_score_global = 0.0
n_events_with_score = 0
n_us_high = 0
n_us_events = 0

# Calculer score vectoriel pour chaque événement
scores_vectoriels = []

if 'empirical_score' in cluster_events.columns:
    for _, event in cluster_events.iterrows():
        base_score = event.get('empirical_score')
        if pd.isna(base_score):
            continue
        
        # Obtenir famille de l'événement (pour direction)
        event_key = event.get('event_key') or event.get('event_title') or event.get('label') or 'Unknown'
        family = event.get('family') or infer_family_from_event_key(event_key)
        
        # Calculer surprise si disponible (pour direction précise)
        actual = event.get('actual')
        estimate = event.get('estimate') or event.get('forecast') or event.get('previous')
        surprise = 0.0
        
        if actual is not None and estimate is not None and estimate != 0:
            surprise = (actual - estimate) / abs(estimate) * 100  # Surprise en %
        elif actual is not None and estimate is not None:
            surprise = actual - estimate  # Surprise brute
        
        # Calculer direction (utilise get_event_direction de formulas_validated)
        # Si surprise = 0, direction basée uniquement sur famille (défaut +1)
        direction = get_event_direction(family, surprise) if surprise != 0 else 1
        
        # Score vectoriel = score_base × direction
        # Note : On utilise score_base (pas ajusté) car on n'a pas encore la surprise complète
        # Pour l'identification du cluster, c'est suffisant
        score_vectoriel = base_score * direction
        scores_vectoriels.append(score_vectoriel)
        n_events_with_score += 1
    
    # SOMME VECTORIELLE des scores (Session 105)
    cluster_score_global = sum(scores_vectoriels) if scores_vectoriels else 0.0
```

## Sélection du Cluster Principal

Le score vectoriel est utilisé dans le calcul du **score de priorité** pour la sélection du cluster principal :

```python
# Score de priorité : combinaison score global + bonus pour US HIGH à 14:30
priority_score = cluster_score_global

# Bonus pour US HIGH à 14:30 (heure typique CPI/NFP/Jobless)
if anchor_hour == 14 and 25 <= anchor_minute <= 35 and n_us_high > 0:
    priority_score += 100.0  # Bonus significatif pour 14:30

# Bonus pour événements US HIGH (même si pas à 14:30)
if n_us_high > 0:
    priority_score += 50.0 * n_us_high  # Bonus par événement US HIGH

# Bonus pour événements US
if n_us_events > 0:
    priority_score += 10.0 * n_us_events  # Bonus par événement US
```

## Références

- **Session 105** : `scripts/session105/test_vectoriel_scores_FINAL.py`
- **Formules validées** : `src/core/formulas_validated.py` (`get_event_direction`, `infer_family_from_event_key`)
- **Cluster Impact Calculator** : `src/core/cluster_impact_calculator.py` (logique similaire pour calcul d'impact)

## Tests

Un script de test a été créé pour vérifier le calcul vectoriel :
- `SESSION_VALIDATION_ACTUELLE/scripts/test_score_vectoriel_cluster.py`

## Date de Correction

2025-12-XX (Session actuelle)




