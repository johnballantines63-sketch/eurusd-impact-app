# Implémentation Random Forest pour Prédiction d'Amplification

**Date** : Implémentation  
**Méthode** : 4 étapes selon spécifications utilisateur

---

## 📋 MÉTHODE EN 4 ÉTAPES

### Étape 1 : Définir le Noyau Dur

**Status** : ✅ Déjà implémenté dans `etape3_definir_noyau_dur`

Le noyau dur est défini automatiquement lors de l'étape 3 du pipeline :
- Détection des noyaux durs pré-définis (CPI, NFP) via patterns de familles
- Si cluster correspond à CPI ou NFP : utiliser tous les événements correspondants comme core
- Sinon : tous les événements sont core (fallback)

**Résultat** : `cluster_info` contient `core_events`, `n_core_events`, `core_type`

---

### Étape 2 : Trouver Clusters Identiques

**Status** : ✅ Déjà implémenté dans `etape4_rechercher_clusters_identiques`

Les clusters identiques sont trouvés en comparant les noyaux durs avec Jaccard similarity :
- Seuil Jaccard : 0.60 par défaut
- Lookback : 5 ans par défaut
- Retourne liste de clusters avec même noyau dur

**Résultat** : `identical_clusters` contient les clusters historiques similaires

---

### Étape 3 : Calculer Amplification Idéale pour Chaque Cluster Historique

**Status** : ✅ Implémenté dans `train_rf_from_identical_clusters`

Pour chaque cluster identique trouvé :

1. **Récupérer impact_base** : Déjà calculé dans `etape6_calculer_tendances_impacts`
   - Utilise méthode Session 88 (score moyen ajusté avec surprise MAX)
   - Stocké dans `results_df['impact_base']`

2. **Récupérer impact_real** : Déjà mesuré dans `etape6_calculer_tendances_impacts`
   - Utilise `measure_impact_from_finnhub` (M1, pic réel)
   - Stocké dans `results_df['impact_reel']`

3. **Calculer amplification_ideale** :
   ```python
   amplification_ideale = impact_real / (impact_base * adjustment_factor)
   ```
   - Limité entre 0.1x et 10.0x

4. **Extraire features** :
   - `max_surprise_pct` : Surprise maximale du cluster (%)
   - `mean_surprise_pct` : Surprise moyenne du cluster (%)
   - `num_events` : Nombre d'événements
   - `mean_empirical_score` : Score empirique moyen
   - `trend_r2` : R² de la tendance pré-événement
   - `trend_direction_encoded` : Direction tendance (1=UP, -1=DOWN, 0=UNKNOWN)
   - `trend_amplitude_pips` : Amplitude tendance (pips)

**Résultat** : Liste de features et amplifications idéales pour chaque cluster historique

---

### Étape 4 : Entraîner Random Forest et Prédire

**Status** : ✅ Implémenté dans `train_random_forest_amplification` et `predict_amplification_with_rf`

1. **Entraîner Random Forest** :
   - Features standardisées avec `StandardScaler`
   - Modèle : `RandomForestRegressor`
   - Paramètres :
     - `n_estimators=100` : Nombre d'arbres
     - `max_depth=5` : Profondeur maximale
     - `min_samples_split=5` : Minimum échantillons pour split
     - `random_state=42` : Reproductibilité

2. **Prédire amplification pour cluster cible** :
   - Extraire features du cluster cible
   - Standardiser avec le même scaler
   - Prédire avec modèle entraîné
   - Limiter entre 0.1x et 10.0x

**Résultat** : Amplification prédite pour le cluster cible

---

## 🔧 INTÉGRATION DANS PIPELINE

### Étape 8.3 : Prédiction d'Amplification

**Fichier** : `scripts/run_pipeline_complete.py`  
**Lignes** : ~1111-1148

**Hiérarchie** :
1. **Formule Session 88** (priorité maximale pour surprises >100%)
2. **Random Forest** (si >= 5 clusters identiques)
3. **Modèle linéaire R²** (si tendance détectée)
4. **Moyenne historique** (dernier fallback)

**Code** :
```python
# 1. Random Forest par date
if amplification_method == 'default' and num_clusters >= 5 and results_df is not None:
    rf_result = train_rf_from_identical_clusters(
        identical_clusters=identical_clusters,
        results_df=results_df,
        executor=self,
        min_clusters=5
    )
    
    if rf_result is not None:
        rf_model, scaler, feature_names = rf_result
        features_target = extract_features_for_rf(...)
        amplification_predite = predict_amplification_with_rf(...)
        amplification_method = 'random_forest'
```

---

## 📊 FEATURES UTILISÉES

| Feature | Description | Source |
|---------|-------------|--------|
| `max_surprise_pct` | Surprise maximale du cluster (%) | Calculée depuis actual/estimate |
| `mean_surprise_pct` | Surprise moyenne du cluster (%) | Calculée depuis actual/estimate |
| `num_events` | Nombre d'événements dans le cluster | `len(cluster_events)` |
| `mean_empirical_score` | Score empirique moyen | `cluster_events['empirical_score'].mean()` |
| `trend_r2` | R² de la tendance pré-événement | `etape5_calculer_tendances_impacts` |
| `trend_direction_encoded` | Direction tendance (1=UP, -1=DOWN, 0=UNKNOWN) | `etape5_calculer_tendances_impacts` |
| `trend_amplitude_pips` | Amplitude tendance (pips) | `etape5_calculer_tendances_impacts` |

---

## ✅ AVANTAGES

1. **Utilise données historiques réelles** : Amplifications idéales basées sur impacts réels mesurés
2. **Prend en compte contexte** : Features incluent tendances, surprises, scores empiriques
3. **Non-linéaire** : Random Forest capture relations complexes entre features et amplification
4. **Robuste** : Standardisation des features, validation croisée implicite

---

## ⚠️ LIMITATIONS

1. **Minimum 5 clusters** : Nécessite au moins 5 clusters identiques pour entraîner
2. **Données historiques** : Dépend de la qualité des mesures d'impact réel
3. **Features tendance** : Nécessite que les tendances soient calculées pour clusters historiques

---

## 🧪 TEST

**Script de test** : À créer  
**Date de test** : 2025-08-01  
**Résultats attendus** : Amélioration de la prédiction d'amplification vs moyenne historique

---

_Date création : Implémentation Random Forest amplification_  
_Status : ✅ Implémenté et intégré dans pipeline_




