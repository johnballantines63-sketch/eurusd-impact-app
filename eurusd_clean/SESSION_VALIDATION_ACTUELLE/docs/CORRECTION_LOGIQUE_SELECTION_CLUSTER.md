# Correction : Logique de Sélection du Cluster Principal

## Problème Identifié

Pour la date 2025-05-29, le pipeline sélectionnait le cluster à **18:00** au lieu de celui à **14:30**, alors que le mouvement réel du prix se produit à **14:30** (visible sur le graphique MT5).

### Cause Racine

La logique de sélection utilisait un système de **bonus additifs** :
- Bonus 14:30 : 100 points
- Bonus US HIGH : 50 points par événement
- Bonus US : 10 points par événement

**Problème** :
- Cluster à 18:00 : 10 événements US HIGH × 50 = **500 points de bonus**
- Cluster à 14:30 : 6 événements US HIGH × 50 = **300 points de bonus** + 100 (14:30) = **400 points**

Le cluster à 18:00 gagnait donc avec 500 > 400, **même si le mouvement réel est à 14:30**.

### Erreur Conceptuelle

Le nombre d'événements ne devrait **PAS** être le critère principal pour identifier le cluster qui cause le mouvement. Les événements à **14:30** (CPI, NFP, Jobless Claims) sont typiquement les plus impactants, même s'ils sont moins nombreux.

## Solution Implémentée

### Nouvelle Logique de Priorité (Hiérarchique)

**PRIORITÉ 1 : Cluster à 14:30 avec événements US HIGH**
- Sélection immédiate si un cluster correspond à ces critères
- Pas de comparaison avec d'autres clusters
- Justification : Heure typique des événements majeurs qui causent les mouvements

**PRIORITÉ 2 : Cluster avec événements US HIGH (même si pas à 14:30)**
- Utiliser le **score global vectoriel** comme critère
- Sélectionner le cluster avec le score vectoriel le plus élevé
- Justification : Le score vectoriel reflète l'impact réel (somme vectorielle des contributions)

**PRIORITÉ 3 : Cluster avec score global vectoriel le plus élevé**
- Tous événements confondus
- Utiliser le score global vectoriel comme critère unique

**PRIORITÉ 4 : Fallback - Cluster le plus grand**
- Si aucun critère précédent ne s'applique

### Avantages

1. **Priorité absolue à 14:30** : Garantit la sélection du cluster qui cause réellement le mouvement
2. **Score vectoriel comme critère** : Reflète l'impact réel, pas juste le nombre d'événements
3. **Logique hiérarchique claire** : Pas de calculs additifs confus
4. **Cohérence avec observations** : Les événements à 14:30 sont effectivement les plus impactants

## Code Modifié

**Fichier** : `scripts/run_pipeline_complete.py`

**Section** : `execute_complete_pipeline` (lignes 2999-3053)

```python
# PRIORITÉ 1 : Cluster à 14:30 avec événements US HIGH
for cluster in clusters:
    anchor_time = cluster.get('anchor_time')
    anchor_hour = anchor_time.hour
    anchor_minute = anchor_time.minute
    n_us_high = cluster.get('n_us_high', 0)
    
    if anchor_hour == 14 and 25 <= anchor_minute <= 35 and n_us_high > 0:
        main_cluster = cluster
        # Sélection immédiate, pas de comparaison
        break

# PRIORITÉ 2 : Cluster US HIGH avec score global le plus élevé
if main_cluster is None:
    clusters_us_high = [c for c in clusters if c.get('n_us_high', 0) > 0]
    if clusters_us_high:
        main_cluster = max(clusters_us_high, key=lambda x: x.get('cluster_score_global', 0))

# PRIORITÉ 3 : Cluster avec score global le plus élevé
if main_cluster is None:
    main_cluster = max(clusters, key=lambda x: x.get('cluster_score_global', 0))

# PRIORITÉ 4 : Fallback
if main_cluster is None:
    main_cluster = max(clusters, key=lambda x: x['n_events'])
```

## Validation

Pour 2025-05-29 :
- ✅ Cluster à 14:30 avec 6 événements US HIGH (Jobless Claims, PCE, GDP) → **Sélectionné**
- ❌ Cluster à 18:00 avec 10 événements US HIGH (Mortgage Rates, EIA) → **Ignoré**

## Références

- **Session 105** : Logique de somme vectorielle pour scores
- **Documentation** : Les événements à 14:30 sont les plus impactants (CPI, NFP, Jobless Claims)
- **Observation graphique** : Mouvement réel à 14:30, pas à 18:00

## Date de Correction

2025-12-XX (Session actuelle)




