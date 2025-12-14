# 🔗 INTÉGRATION CLUSTERS IDENTIQUES DANS LE WORKFLOW VALIDÉ

**Date :** 22 novembre 2025  
**Objectif :** Intégrer la détection de clusters identiques (noyau dur) dans le pipeline de prédiction validé

---

## 🎯 PROBLÈME IDENTIFIÉ

Les tests précédents étaient **faussés** car :
1. ❌ On n'identifiait pas les **clusters identiques** au noyau dur
2. ❌ Les calculs d'amplification (R² ↔ amp) se basaient sur des clusters **hétérogènes**
3. ❌ Les tendances (R²) n'étaient pas calculées sur des **cas vraiment similaires**

**Résultat** : Prédictions erronées car basées sur des données non comparables.

---

## ✅ SOLUTION : DÉTECTION CLUSTERS IDENTIQUES

### A) Nouvelle Approche Méthodologique

**Script créé** : `scripts/analyze_recurrent_cluster_patterns.py`

**Méthode** :
1. **Méthode 1** : Similarité Jaccard entre clusters complets
2. **Méthode 2** : Fréquence individuelle + co-occurrence
3. **Extraction noyau dur** : Support >= 80% = core events

**Résultats pour 20.11.2025 à 14:30** :
- ✅ **27 clusters identiques** au noyau dur trouvés
- ✅ **10 événements core** (support 100%)
- ✅ **Impact médian** : 23.8 pips (sur 20 clusters)
- ✅ **Pattern dominant** : SINGLE_WAVE (90%)
- ✅ **Direction dominante** : DOWN (55%)

---

## 🔄 WORKFLOW INTÉGRÉ (NOUVEAU)

### ÉTAPE 1 : Détection Mouvement
```python
# Scanner prix pour détecter mouvement fort
movements = scan_price_movements(df_prices, min_pips=35.0)
main_movement = select_main_movement(movements, cluster_anchor_time)
```

### ÉTAPE 2 : Identification Cluster Identique
```python
# NOUVEAU : Identifier cluster par ADN (noyau dur)
cluster_info = identify_cluster_from_date(
    target_date,
    movement_time=main_movement['start_time'],
    min_importance=3,
    jaccard_threshold=0.5  # Seuil adaptatif
)

if cluster_info and cluster_info.get('n_samples', 0) >= 4:
    # Cluster identique trouvé !
    core_events = extract_core_cluster(cluster_info)
    
    # Chercher clusters identiques au noyau dur
    identical_clusters = find_identical_clusters_to_core(
        core_events,
        clusters_historical
    )
    
    if len(identical_clusters) >= 3:
        # ✅ UTILISER MÉTRIQUES CLUSTERS IDENTIQUES
        metrics = calculate_metrics_from_identical_clusters(
            identical_clusters
        )
        # metrics = {
        #     'impact_median': 23.8 pips,
        #     'pattern_dominant': 'SINGLE_WAVE',
        #     'direction_dominant': 'DOWN',
        #     'confidence_interval': [10.5, 37.0] pips
        # }
```

### ÉTAPE 3 : Calcul R² pour Clusters Identiques
```python
# NOUVEAU : Calculer R² pour CHAQUE cluster identique
r2_by_cluster = {}

for date, cluster in identical_clusters:
    r2_trend = calculate_r2_trend(
        date,
        lookback_days=30,
        window=240  # 4h pour détection swing
    )
    r2_by_cluster[date] = r2_trend

# Statistiques R²
r2_median = np.median(list(r2_by_cluster.values()))
r2_mean = np.mean(list(r2_by_cluster.values()))
r2_std = np.std(list(r2_by_cluster.values()))
```

### ÉTAPE 4 : Calibration Amplification (R² ↔ amp)
```python
# NOUVEAU : Calibrer amplification UNIQUEMENT sur clusters identiques
calibration_data = []

for date, cluster in identical_clusters:
    r2 = r2_by_cluster[date]
    impact_measured = cluster['impact_pips']
    total_score = cluster['total_score']
    n_events = cluster['n_events']
    
    # Calculer amplification idéale (formule inversée)
    amp_ideal = impact_measured / (total_score * np.sqrt(n_events))
    
    calibration_data.append({
        'r2_trend': r2,
        'amp_ideal': amp_ideal,
        'impact_measured': impact_measured
    })

# Calibrer fonction amp(R²) sur clusters identiques
amplification_function = calibrate_amplification_function(
    calibration_data,
    models=['linear', 'quadratic', 'sigmoid']
)
# Meilleur modèle : quadratique
# amp = a + b×R² + c×R²²
```

### ÉTAPE 5 : Prédiction avec Clusters Identiques
```python
# Calculer R² pour le cluster actuel
r2_current = calculate_r2_trend(
    target_date,
    lookback_days=30,
    window=240
)

# Prédire amplification avec fonction calibrée
amp_predicted = amplification_function(r2_current)

# OU : Utiliser impact médian directement si cluster identique
if len(identical_clusters) >= 10:
    # Impact médian plus fiable que formule
    impact_predicted = metrics['impact_median']  # 23.8 pips
    confidence_interval = metrics['confidence_interval']  # [10.5, 37.0]
else:
    # Utiliser formule avec amplification
    impact_base = calculate_impact_d(
        empirical_score=mean_adjusted_score,
        num_events=num_events,
        amplification=amp_predicted
    )
    impact_predicted = impact_base
```

---

## 📊 AVANTAGES INTÉGRATION

### 1. Prédictions Plus Précises
- ✅ Basées sur **cas vraiment similaires** (même noyau dur)
- ✅ Impact médian : **23.8 pips** (plus fiable que formule générique)
- ✅ Pattern prévisible : **SINGLE_WAVE 90%**

### 2. Amplification Corrigée
- ✅ R² calculé sur **clusters identiques** uniquement
- ✅ Fonction amp(R²) calibrée sur **données homogènes**
- ✅ Évite biais d'hétérogénéité

### 3. Intervalle de Confiance
- ✅ Basé sur **écart-type réel** des clusters identiques
- ✅ Intervalle : **[10.5, 37.0] pips** (au lieu de formule générique)

---

## 🔧 INTÉGRATION PLANIFICATEUR V3 CLEAN

### Modifications Nécessaires

**1. Fonction `identify_cluster_from_date`** (déjà modifiée)
- ✅ Accepte `movement_time` comme paramètre
- ✅ Utilise seuil adaptatif (0.5 pour clusters validés)

**2. Nouvelle fonction : `find_identical_clusters_to_core`**
```python
def find_identical_clusters_to_core(
    core_events: Set[str],
    clusters_historical: Dict[datetime, Set[str]]
) -> List[Tuple[datetime, Set[str], float]]:
    """
    Trouve clusters historiques contenant exactement le noyau dur.
    
    Returns:
        List[(date, cluster_events, jaccard)]
    """
    identical = []
    for date, cluster in clusters_historical.items():
        if core_events.issubset(cluster):
            jaccard = calculate_jaccard_similarity(core_events, cluster)
            identical.append((date, cluster, jaccard))
    return sorted(identical, key=lambda x: x[2], reverse=True)
```

**3. Nouvelle fonction : `calculate_metrics_from_identical_clusters`**
```python
def calculate_metrics_from_identical_clusters(
    identical_clusters: List[Tuple[datetime, Set[str], float]],
    db_path: Path
) -> Dict:
    """
    Calcule métriques d'impact pour clusters identiques.
    
    Returns:
        {
            'impact_median': float,
            'impact_mean': float,
            'impact_std': float,
            'pattern_dominant': str,
            'direction_dominant': str,
            'confidence_interval': [min, max],
            'n_samples': int
        }
    """
    # Charger impacts depuis DB pour chaque date
    impacts = []
    patterns = []
    directions = []
    
    for date, cluster, jaccard in identical_clusters:
        impact = load_impact_for_date(date, db_path)
        if impact:
            impacts.append(impact['impact_pips'])
            patterns.append(impact.get('pattern', 'UNKNOWN'))
            directions.append(impact.get('direction', 'UNKNOWN'))
    
    if not impacts:
        return None
    
    return {
        'impact_median': np.median(impacts),
        'impact_mean': np.mean(impacts),
        'impact_std': np.std(impacts),
        'pattern_dominant': pd.Series(patterns).value_counts().idxmax(),
        'direction_dominant': pd.Series(directions).value_counts().idxmax(),
        'confidence_interval': [
            np.median(impacts) - np.std(impacts),
            np.median(impacts) + np.std(impacts)
        ],
        'n_samples': len(impacts)
    }
```

**4. Modification fonction prédiction**
```python
def predict_impact_with_cluster_identification(
    target_date: datetime,
    movement_time: datetime,
    df_events: pd.DataFrame,
    df_prices: pd.DataFrame
) -> Dict:
    """
    Prédit impact en utilisant clusters identiques si disponibles.
    """
    # 1. Identifier cluster
    cluster_info = identify_cluster_from_date(...)
    
    # 2. Chercher clusters identiques
    if cluster_info and cluster_info.get('n_samples', 0) >= 4:
        core_events = extract_core_cluster(cluster_info)
        identical_clusters = find_identical_clusters_to_core(...)
        
        if len(identical_clusters) >= 3:
            # ✅ UTILISER MÉTRIQUES CLUSTERS IDENTIQUES
            metrics = calculate_metrics_from_identical_clusters(...)
            
            # Calculer R² pour calibration
            r2_by_cluster = calculate_r2_for_clusters(identical_clusters)
            
            # Calibrer amplification
            amp_function = calibrate_amplification(r2_by_cluster, metrics)
            
            # Prédire avec R² actuel
            r2_current = calculate_r2_trend(target_date)
            amp_predicted = amp_function(r2_current)
            
            return {
                'impact_predicted': metrics['impact_median'],  # OU formule avec amp
                'amplification': amp_predicted,
                'pattern_expected': metrics['pattern_dominant'],
                'confidence_interval': metrics['confidence_interval'],
                'method': 'identical_clusters',
                'n_identical_clusters': len(identical_clusters)
            }
    
    # Fallback : méthode standard (formules génériques)
    return predict_impact_standard(...)
```

---

## 📈 RÉSULTATS ATTENDUS

### Amélioration Prédictions

**AVANT** (sans clusters identiques) :
- MAE : ~20-25 pips
- Basé sur formules génériques
- Amplification calibrée sur clusters hétérogènes

**APRÈS** (avec clusters identiques) :
- MAE : **~15-18 pips** (amélioration 20-30%)
- Basé sur impact médian clusters identiques
- Amplification calibrée sur clusters homogènes
- Intervalle de confiance réel

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ **Intégrer dans Planificateur V3 CLEAN**
   - Ajouter fonction `find_identical_clusters_to_core`
   - Ajouter fonction `calculate_metrics_from_identical_clusters`
   - Modifier workflow prédiction

2. ✅ **Tester sur dates variées**
   - 20.11.2025 (27 clusters identiques)
   - 11.09.2025 (cluster référence)
   - Autres dates avec clusters identiques

3. ✅ **Valider amélioration**
   - Comparer MAE avant/après
   - Vérifier précision amplification
   - Confirmer intervalle confiance

---

**Auteur :** André Valentin avec Claude  
**Date :** 22 novembre 2025  
**Statut :** 📋 PLAN D'INTÉGRATION - À IMPLÉMENTER


