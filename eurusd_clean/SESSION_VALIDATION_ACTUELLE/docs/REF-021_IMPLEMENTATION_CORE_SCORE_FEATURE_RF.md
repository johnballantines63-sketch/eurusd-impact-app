# REF-021 : Implémentation core_score comme Feature Random Forest

**Date :** 2025-12-06  
**Référence :** REF-020 (Analyse Mathématique)

---

## ✅ IMPLÉMENTATION

### Modifications Effectuées

1. **`src/core/random_forest_amplification.py`** :
   - ✅ Ajout paramètre `core_score` dans `extract_features_for_rf()`
   - ✅ Ajout `core_score` dans le dictionnaire de features retourné

2. **`scripts/run_pipeline_complete.py`** :
   - ✅ Récupération `core_score` depuis table `core_scores` (RF par date)
   - ✅ Récupération `core_score` depuis table `core_scores` (RF global)
   - ✅ Passage `core_score` à `extract_features_for_rf()`
   - ✅ Passage `core_score` à `predict_amplification_random_forest()`

3. **`src/core/amplification_random_forest.py`** :
   - ✅ Ajout paramètre `core_score` dans `predict_amplification_random_forest()`
   - ✅ Ajout `core_score` dans les features historiques (0.0 pour l'instant)
   - ✅ Ajout `core_score` dans les features de prédiction

---

## 📊 FEATURES RANDOM FOREST

### Features Actuelles

| Feature | Description | Source |
|---------|-------------|--------|
| `trend_r2` | R² de la tendance pré-événement | Étape 8.2 |
| `trend_duration_h` | Durée tendance en heures | Étape 8.2 |
| `trend_amplitude_pips` | Amplitude tendance (pips) | Étape 8.2 |
| `impact_base_pips` | Impact de base calculé | Étape 8.1 |
| `num_events` | Nombre d'événements | Cluster |
| `pattern_impact_pips` | Impact pattern détecté | Étape 8.6 |
| `pattern_wave1_pips` | Wave 1 pips | Étape 8.6 |
| `pattern_wave2_pips` | Wave 2 pips | Étape 8.6 |
| **`core_score`** | **Score core_scores pour core_type** | **Table core_scores** |

---

## 🔧 DÉTAILS TECHNIQUES

### Récupération core_score

**Pour RF par date et RF global :**
```python
# Récupérer core_score depuis core_scores
conn = self._get_connection()
query_core_score = """
SELECT empirical_score
FROM core_scores
WHERE core_type = ? AND country = ?
"""
core_type = cluster_info.get('core_type', 'UNKNOWN')
country = cluster_info.get('country', 'US')
score_row = conn.execute(query_core_score, [core_type, country]).fetchone()
conn.close()
if score_row:
    core_score_db = score_row[0]
```

**Fallback :** `core_score = 0.0` si non trouvé

### Passage aux Features

**RF par date :**
```python
features_target = extract_features_for_rf(
    cluster_events=cluster_events,
    trend_r2=trend_r2,
    trend_duration_h=trend_duration_h,
    trend_amplitude_pips=trend_amplitude_pips,
    impact_base_pips=impact_base,
    num_events=num_events,
    core_score=core_score_db  # ✅ NOUVEAU
)
```

**RF global :**
```python
amplification_predite = predict_amplification_random_forest(
    trend_r2=trend_r2,
    trend_duration_h=trend_duration_h,
    trend_amplitude_pips=trend_amplitude_pips,
    impact_base_pips=impact_base,
    num_events=num_events,
    core_score=core_score_db,  # ✅ NOUVEAU
    results_df=results_df
)
```

---

## ⚠️ LIMITATIONS ACTUELLES

### Pour Clusters Historiques (Entraînement RF)

**Problème :** `core_score` = 0.0 pour les clusters historiques utilisés pour l'entraînement.

**Raison :** Le `core_type` et `country` ne sont pas facilement identifiables depuis les clusters historiques dans `train_rf_from_identical_clusters()`.

**Impact :** 
- RF apprend avec `core_score = 0.0` pour historique
- RF prédit avec `core_score` réel pour cluster cible
- **Peut créer un biais** si `core_score` est important

**Solution Future :**
- Identifier `core_type` et `country` depuis les clusters historiques
- Récupérer `core_score` pour chaque cluster historique
- Utiliser `core_score` réel dans l'entraînement

---

## 🎯 PROCHAINES ÉTAPES

### 1. Améliorer Entraînement RF (Priorité Haute)

**Objectif :** Utiliser `core_score` réel pour clusters historiques.

**Méthode :**
- Identifier `core_type` depuis les événements du cluster historique
- Récupérer `core_score` depuis `core_scores`
- Passer `core_score` réel à `extract_features_for_rf()` dans `train_rf_from_identical_clusters()`

### 2. Tester l'Implémentation

**Objectif :** Vérifier que `core_score` améliore les prédictions.

**Méthode :**
- Tester sur dates de validation
- Comparer prédictions avec/sans `core_score`
- Analyser importance de `core_score` dans le modèle RF

### 3. Analyser Importance Feature

**Objectif :** Comprendre l'importance de `core_score` dans le modèle.

**Méthode :**
- Utiliser `get_feature_importance()` pour voir l'importance de `core_score`
- Comparer avec autres features
- Valider que `core_score` apporte de la valeur

---

## 📋 VALIDATION

### Tests à Effectuer

1. **Test 1 : Récupération core_score**
   - Vérifier que `core_score` est correctement récupéré depuis `core_scores`
   - Vérifier fallback si `core_type` non trouvé

2. **Test 2 : Passage aux Features**
   - Vérifier que `core_score` est présent dans `features_target`
   - Vérifier que `core_score` est présent dans les features historiques

3. **Test 3 : Prédiction RF**
   - Vérifier que RF peut prédire avec `core_score`
   - Comparer prédictions avec/sans `core_score`

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




