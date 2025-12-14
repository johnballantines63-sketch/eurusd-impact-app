# Optimisation Recherche Clusters Identiques (Étape 4)

**Date** : 2025-01-XX  
**Problème** : Recherche de clusters identiques très lente (5 ans d'historique, parcours jour par jour)  
**Objectif** : Réduire le temps d'exécution de plusieurs minutes à quelques secondes

---

## 🔍 ANALYSE DES GOUlets D'ÉTRANGLEMENT

### Architecture Actuelle

La fonction `etape4_rechercher_clusters_identiques` parcourt **jour par jour** sur 5 ans (1825 jours) :

```python
while current_date <= date_end:
    # 1. Charger événements HIGH impact pour cette date
    df_events_hist = load_high_impact_events(...)
    
    # 2. Détecter clusters pour cette date
    clusters_hist = self.etape2_detecter_clusters(...)
    
    # 3. Pour chaque cluster historique
    for cluster_hist in clusters_hist:
        # 4. Définir noyau dur pour ce cluster
        cluster_info_hist = self.etape3_definir_noyau_dur(...)
        
        # 5. Calculer similarité Jaccard
        jaccard_score = intersection / union
```

### Goulots d'Étranglement Identifiés

1. **Parcours séquentiel** : 1825 appels à `load_high_impact_events` (1 par jour)
2. **Détection clusters répétée** : 1825 appels à `etape2_detecter_clusters`
3. **Définition noyau dur répétée** : N appels à `etape3_definir_noyau_dur` (N = nombre total de clusters)
4. **Pas de filtrage précoce** : Toutes les dates sont traitées même si elles n'ont pas d'événements à l'heure cible
5. **Pas d'arrêt anticipé** : La recherche continue même après avoir trouvé assez de clusters

### Estimation Temps d'Exécution

- **Chargement événements** : ~10-50ms par date → 18-91 secondes pour 1825 dates
- **Détection clusters** : ~5-20ms par date → 9-36 secondes
- **Définition noyau dur** : ~1-5ms par cluster → variable selon nombre de clusters
- **Total estimé** : 30-150 secondes pour 5 ans d'historique

---

## ✅ OPTIMISATIONS PROPOSÉES

### 1. Requête SQL Directe (PRIORITÉ HAUTE)

**Au lieu de** : Charger événements jour par jour  
**Faire** : Une seule requête SQL pour charger tous les événements de la période

```python
# AVANT (lent)
while current_date <= date_end:
    df_events_hist = load_high_impact_events(current_date, ...)

# APRÈS (rapide)
query = """
SELECT 
    e.event_key,
    e.country,
    e.ts_utc,
    e.importance_n,
    ef.empirical_score,
    ...
FROM events e
LEFT JOIN event_families ef ON ...
WHERE DATE(e.ts_utc) >= ? AND DATE(e.ts_utc) < ?
    AND e.country = 'US'
    AND ef.empirical_score > 40.0
    AND EXTRACT(HOUR FROM e.ts_utc) = ?
    AND EXTRACT(MINUTE FROM e.ts_utc) BETWEEN ? AND ?
ORDER BY e.ts_utc
"""
df_all_events = conn.execute(query, [date_start, date_end, target_hour, target_minute-10, target_minute+10]).df()
```

**Gain estimé** : 90-95% de réduction du temps de chargement

---

### 2. Filtrage Précoce par Heure (PRIORITÉ HAUTE)

**Au lieu de** : Charger tous les événements puis filtrer par heure  
**Faire** : Filtrer directement dans la requête SQL

```python
# Filtrer par heure d'événement dans la requête SQL
AND EXTRACT(HOUR FROM e.ts_utc) = target_hour
AND EXTRACT(MINUTE FROM e.ts_utc) BETWEEN target_minute-10 AND target_minute+10
```

**Gain estimé** : Réduction de 80-90% du volume de données à traiter

---

### 3. Groupement par Date dans SQL (PRIORITÉ MOYENNE)

**Au lieu de** : Détecter clusters pour chaque date séparément  
**Faire** : Grouper les événements par date dans SQL, puis détecter clusters

```python
# Grouper par date dans SQL
df_all_events['date'] = pd.to_datetime(df_all_events['ts_utc']).dt.date
events_by_date = df_all_events.groupby('date')

# Détecter clusters seulement pour les dates qui ont des événements
for date, df_date_events in events_by_date:
    clusters_hist = self.etape2_detecter_clusters(df_date_events, ...)
```

**Gain estimé** : Évite de traiter les dates sans événements

---

### 4. Cache des Noyaux Durs (PRIORITÉ MOYENNE)

**Au lieu de** : Redéfinir le noyau dur pour chaque cluster  
**Faire** : Mettre en cache les noyaux durs par type de cluster

```python
# Cache des noyaux durs par type
core_cache = {}  # {(core_type, tuple(sorted(event_keys))): core_events}

# Vérifier cache avant de recalculer
cache_key = (core_type, tuple(sorted(event_keys)))
if cache_key in core_cache:
    core_events = core_cache[cache_key]
else:
    cluster_info = self.etape3_definir_noyau_dur(cluster)
    core_cache[cache_key] = cluster_info['core_events']
```

**Gain estimé** : 50-70% de réduction si beaucoup de clusters similaires

---

### 5. Arrêt Anticipé (PRIORITÉ BASSE)

**Au lieu de** : Parcourir toutes les dates même après avoir trouvé assez de clusters  
**Faire** : Arrêter la recherche une fois qu'on a trouvé `min_clusters_found` avec le meilleur seuil

```python
# Si on a trouvé assez de clusters avec un seuil, arrêter
if len(identical_clusters) >= min_clusters_found:
    threshold_used = threshold
    break  # Arrêter la recherche
```

**Gain estimé** : Variable selon la position des clusters dans l'historique

---

### 6. Index SQL (PRIORITÉ BASSE)

**S'assurer que** : Les index SQL sont optimaux pour les requêtes

```sql
-- Index recommandés
CREATE INDEX IF NOT EXISTS idx_events_ts_utc ON events(ts_utc);
CREATE INDEX IF NOT EXISTS idx_events_country ON events(country);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(DATE(ts_utc));
```

**Gain estimé** : 10-30% selon la taille de la base

---

## 📊 IMPACT ESTIMÉ DES OPTIMISATIONS

### Scénario Actuel (5 ans, jour par jour)

- **Temps estimé** : 30-150 secondes
- **Requêtes SQL** : ~1825 requêtes
- **Appels fonctions** : ~1825 appels `etape2_detecter_clusters`

### Scénario Optimisé (Requête SQL directe + Filtrage)

- **Temps estimé** : 2-5 secondes (réduction de 85-95%)
- **Requêtes SQL** : 1 requête
- **Appels fonctions** : ~50-200 appels `etape2_detecter_clusters` (seulement pour dates avec événements)

---

## 🎯 PLAN D'IMPLÉMENTATION

### Phase 1 : Optimisation Critique (Impact Maximum)

1. ✅ **Requête SQL directe** : Charger tous les événements en une seule requête
2. ✅ **Filtrage précoce par heure** : Filtrer dans SQL avant traitement
3. ✅ **Groupement par date** : Grouper dans SQL, traiter seulement dates avec événements

**Temps estimé** : 1-2 heures  
**Gain estimé** : 85-95% de réduction

### Phase 2 : Optimisations Complémentaires (Impact Moyen)

4. ✅ **Cache des noyaux durs** : Éviter recalculs inutiles
5. ✅ **Arrêt anticipé** : Arrêter après avoir trouvé assez de clusters

**Temps estimé** : 30-60 minutes  
**Gain estimé** : 10-20% de réduction supplémentaire

### Phase 3 : Optimisations Avancées (Impact Faible)

6. ✅ **Index SQL** : Optimiser les requêtes
7. ✅ **Parallélisation** : Traiter plusieurs dates en parallèle (si nécessaire)

**Temps estimé** : 1-2 heures  
**Gain estimé** : 5-15% de réduction supplémentaire

---

## 📝 CODE PROPOSÉ

### Version Optimisée (Phase 1)

```python
def etape4_rechercher_clusters_identiques_optimized(
    self,
    cluster_info: Dict,
    jaccard_threshold: float = 0.60,
    years_lookback: int = 5,
    min_clusters_found: int = 3
) -> List[Dict]:
    """Version optimisée avec requête SQL directe"""
    
    core_events_set = set(cluster_info['core_events'])
    anchor_time = cluster_info['cluster']['anchor_time']
    
    if not core_events_set:
        return []
    
    # Calculer dates de recherche
    date_start = anchor_time - timedelta(days=years_lookback * 365)
    date_end = anchor_time - timedelta(days=1)
    
    # Heure de référence (±10 minutes)
    target_hour = anchor_time.hour
    target_minute = anchor_time.minute
    
    conn = self._get_connection()
    
    # OPTIMISATION 1 : Requête SQL directe pour charger tous les événements
    query = """
    SELECT 
        e.event_key,
        e.country,
        e.ts_utc,
        e.importance_n,
        e.actual,
        e.estimate,
        e.forecast,
        e.previous,
        ef.empirical_score,
        ef.family,
        ef.latency_median
    FROM events e
    LEFT JOIN event_families ef 
        ON e.event_key = ef.event_key 
        AND e.country = ef.country
    WHERE DATE(e.ts_utc) >= ?
        AND DATE(e.ts_utc) < ?
        AND e.country = 'US'
        AND ef.empirical_score IS NOT NULL
        AND ef.empirical_score > 40.0
        AND EXTRACT(HOUR FROM e.ts_utc) = ?
        AND EXTRACT(MINUTE FROM e.ts_utc) BETWEEN ? AND ?
    ORDER BY e.ts_utc
    """
    
    df_all_events = conn.execute(query, [
        date_start.strftime('%Y-%m-%d'),
        date_end.strftime('%Y-%m-%d'),
        target_hour,
        target_minute - 10,
        target_minute + 10
    ]).df()
    
    if df_all_events.empty:
        return []
    
    # OPTIMISATION 2 : Grouper par date
    df_all_events['date'] = pd.to_datetime(df_all_events['ts_utc']).dt.date
    events_by_date = df_all_events.groupby('date')
    
    all_candidates = []
    
    # OPTIMISATION 3 : Traiter seulement dates avec événements
    for date, df_date_events in events_by_date:
        # Détecter clusters pour cette date
        clusters_hist = self.etape2_detecter_clusters(df_date_events, window_minutes=30)
        
        for cluster_hist in clusters_hist:
            # Définir noyau dur
            cluster_info_hist = self.etape3_definir_noyau_dur(cluster_hist)
            core_events_hist_set = set(cluster_info_hist['core_events'])
            
            if not core_events_hist_set:
                continue
            
            # Calculer Jaccard
            intersection = len(core_events_set & core_events_hist_set)
            union = len(core_events_set | core_events_hist_set)
            
            if union == 0:
                continue
            
            jaccard_score = intersection / union
            
            all_candidates.append({
                'date': date,
                'jaccard_score': jaccard_score,
                'core_events': list(core_events_hist_set),
                'cluster': cluster_hist,
                'cluster_info': cluster_info_hist,
                'anchor_time': cluster_hist['anchor_time']
            })
    
    # Appliquer seuil adaptatif (code existant)
    # ...
    
    return identical_clusters
```

---

## ✅ VALIDATION

### Tests à Effectuer

1. **Test performance** : Comparer temps d'exécution avant/après
2. **Test résultats** : Vérifier que les clusters trouvés sont identiques
3. **Test edge cases** : Dates sans événements, clusters multiples, etc.

### Métriques de Succès

- **Temps d'exécution** : < 5 secondes pour 5 ans d'historique
- **Précision** : 100% des clusters trouvés identiques à la version non optimisée
- **Couverture** : Tous les clusters similaires trouvés

---

**Status** : 📋 **PLANIFIÉ - EN ATTENTE D'IMPLÉMENTATION**




