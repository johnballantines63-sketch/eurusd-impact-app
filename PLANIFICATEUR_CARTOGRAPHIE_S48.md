# 🗺️ CARTOGRAPHIE COMPLÈTE DU PLANIFICATEUR
**Date** : 23 octobre 2025  
**Session** : 48  
**Fichier analysé** : `4_Planificateur_STABLE_0159_PERFECT.py`

---

## 📊 VUE D'ENSEMBLE

### Statistiques Globales
- **📏 Lignes totales** : ~1742 lignes (91 KB)
- **🔧 Nombre de fonctions** : En cours d'extraction...
- **📦 Imports externes** :
  - `streamlit` (UI)
  - `pandas`, `numpy` (Data)
  - `duckdb` (DB)
  - `plotly` (Graphiques)
  - `forecaster_mvp.ForecastEngine`
  - `scoring_engine.ScoringEngine`
  - `latency_analyzer.LatencyAnalyzer`
  - `sequence_multi_event_timeline_v87`

---

## 🎯 DÉCOUVERTES SESSION 47

### ❌ PROBLÈME IDENTIFIÉ : Double Calcul d'Impact

**Flux actuel** :
```python
1. Planificateur appelle predict_impact_fast()
   ├─> Calcule : impact = mfe_p80 × impact_factor
   ├─> Calcule : direction = get_event_direction(family, surprise)
   └─> Retourne prédiction

2. sequence_multi_event_timeline() RE-CALCULE TOUT
   ├─> Appelle : predict_impact_func(score, num_events)
   ├─> Appelle : get_direction_func(family, surprise)
   └─> IGNORE les valeurs calculées à l'étape 1 !
```

**Résultat** : Les calculs du planificateur sont **inutiles** et **redondants**

---

## 📂 STRUCTURE DES FONCTIONS

### 🔧 Catégorie : Calcul d'Impact (3 fonctions)

#### 1. `predict_impact_fast()` ⭐ PRINCIPALE
- **Ligne** : 423-478
- **Rôle** : Calcul ULTRA-RAPIDE depuis stats pré-calculées
- **Paramètres** : `(family, surprise, precomputed_stats, years_back=3)`
- **Source données** : `precomputed_stats` dict (depuis DB)

**Formule d'impact** :
```python
impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
impact = mfe_p80 * impact_factor
direction = get_event_direction(family, surprise)
```

**Correction TTR v8.5** :
```python
if ttr_corrected > 20:
    correction_factor = 0.23  # CPI: 39→7, Jobless: 31→7
    ttr_corrected = stats['ttr_median'] * correction_factor
```

---

#### 2. `predict_impact()` ⭐ FALLBACK
- **Ligne** : 750-875
- **Rôle** : Calcul LENT si stats pré-calculées indisponibles
- **Paramètres** : `(family, surprise, years_back=3)`
- **Source données** : 
  - `LatencyAnalyzer` → Latence
  - `ForecastEngine` → MFE (impact)

**Formule d'impact** :
```python
base_impact = stats['mfe_p80']
direction = 1 if surprise > 0 else -1
surprise_factor = min(abs(surprise) / 50.0, 2.0)
adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
```

**Correction TTR v8.5** :
```python
'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 1.5
'ttr_p20': latency_stats['initial_reaction']['median_minutes'] * 1.0
'ttr_p80': latency_stats['initial_reaction']['median_minutes'] * 2.0
```

---

#### 3. `calculate_cluster_impact()`
- **Ligne** : 387-420
- **Rôle** : Calcul impact CUMULÉ d'un cluster temporel
- **Paramètres** : `(cluster, predictions_dict)`
- **Méthode** : Somme vectorielle des impacts

```python
for event in cluster['events']:
    impact = pred['predicted_pips'] * pred['direction']
    cluster_impact['total_pips'] += impact  # ← SOMME VECTORIELLE
```

---

### 📐 Catégorie : Direction/Sentiment (1 fonction)

#### `get_event_direction()` ⭐ CRITIQUE
- **Ligne** : 481-540
- **Rôle** : Détermine direction EUR/USD selon sentiment famille
- **Paramètres** : `(family, surprise)`

**Logique** :
```python
FAMILY_SENTIMENT = {
    'Jobless_Claims': -1,  # INVERSÉ : surprise+ = BAD for USD = UP
    'CPI': -1,             # INVERSÉ
    'NFP': 1,              # NORMAL : surprise+ = GOOD for USD = DOWN
    'GDP': 1,              # NORMAL
}

if surprise > 0:
    if sentiment == -1:
        direction = 1   # EUR/USD UP
    else:
        direction = -1  # EUR/USD DOWN
else:
    if sentiment == -1:
        direction = -1  # EUR/USD DOWN
    else:
        direction = 1   # EUR/USD UP
```

---

### 🔄 Catégorie : Groupement/Clustering (2 fonctions)

#### 1. `group_events_by_time_window()`
- **Ligne** : 310-364
- **Rôle** : Groupe événements proches (< 30 min)
- **Paramètres** : `(events, max_gap_minutes=30)`

#### 2. `calculate_cluster_impact()`
- Voir section Calcul d'Impact ci-dessus

---

### 💾 Catégorie : DB/Chargement Données (5 fonctions)

#### 1. `load_precomputed_stats_from_db()` ⭐
- **Ligne** : 125-161
- **Rôle** : Charge stats pré-calculées (latence, TTR, MFE)
- **Paramètres** : `()`
- **Cache** : `@st.cache_data(ttl=3600)`

#### 2. `load_all_events_for_date()`
- **Ligne** : 543-611
- **Rôle** : Charge TOUS événements (mappés + non-mappés)

#### 3. `get_future_events()`
- **Ligne** : 619-669
- **Rôle** : Charge événements d'une période

#### 4. `refresh_today_events()`
- **Ligne** : 69-117
- **Rôle** : MAJ événements du jour depuis EODHD API

#### 5. `identify_family()`
- **Ligne** : 614-617
- **Rôle** : Identifie famille d'un événement par regex

---

### 📊 Catégorie : Visualisation/Charts (2 fonctions)

#### 1. `create_timeline_chart()`
- **Ligne** : 907-1080
- **Rôle** : Timeline interactive avec Plotly

#### 2. `create_backtest_chart()`
- **Ligne** : 1213-1292
- **Rôle** : Graphique comparaison prédiction vs réalité

---

### 🎯 Catégorie : Backtest/Validation (3 fonctions)

#### 1. `get_real_prices_batch()` ⭐ OPTIMISÉ
- **Ligne** : 1115-1168
- **Rôle** : Récupère prix MT5 en UNE SEULE query
- **Paramètres** : `(event_times, window_minutes=60)`

#### 2. `measure_real_impact()`
- **Ligne** : 1171-1211
- **Rôle** : Mesure impact réel depuis prix MT5

#### 3. Section inline dans le code principal
- **Ligne** : ~1700+
- **Rôle** : Comparaison métriques (MAE, RMSE, Corrélation)

---

### 🧮 Catégorie : Fibonacci/Niveaux (1 fonction)

#### `calculate_fibonacci_levels()`
- **Ligne** : 878-895
- **Rôle** : Calcule niveaux retracement Fibonacci

---

### 🔍 Catégorie : Utilitaires (3 fonctions)

#### 1. `detect_overlaps()`
- **Ligne** : 1083-1105
- **Rôle** : Détecte chevauchements TTR

#### 2. `calculate_tradability_score()`
- **Ligne** : 1108-1143
- **Rôle** : Score 0-100 de tradabilité

#### 3. Divers helper functions inline

---

## 🚨 ANALYSE DES REDONDANCES

### Problème #1 : Double Calcul Impact ❌

**Où** :
1. **Ligne 423-478** : `predict_impact_fast()` calcule impact
2. **Fonction externe** : `sequence_multi_event_timeline_v87` RE-CALCULE

**Conflit** :
- **Planificateur** utilise : `impact = mfe_p80 × (1.0 + surprise/100)`
- **Timeline** utilise : `ForecastEngine.predict_impact_v9_clean(score, num_events)`

**Question** : **Les deux formules donnent-elles le même résultat ?**

---

### Problème #2 : Deux Méthodes de Calcul Impact ⚠️

#### Méthode A : `predict_impact_fast()` (ligne 423)
```python
impact_factor = min(2.0, 1.0 + (surprise / 100))
impact = mfe_p80 * impact_factor
```

#### Méthode B : `predict_impact()` (ligne 750)
```python
surprise_factor = min(abs(surprise) / 50.0, 2.0)
adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
```

**Différence** :
- **Méthode A** : Facteur multiplicatif simple
- **Méthode B** : Facteur avec plancher (0.5)

**Impact** : Pour `surprise = 50%` :
- **A** : `impact = mfe_p80 × 1.5` (150% de base)
- **B** : `impact = mfe_p80 × 1.0` (100% de base)

**❓ Laquelle est correcte ?**

---

### Problème #3 : TTR Correction Incohérente ⚠️

#### Dans `predict_impact_fast()` (ligne 438-450)
```python
if ttr_corrected > 20:
    correction_factor = 0.23
    ttr_corrected = stats['ttr_median'] * correction_factor
```

#### Dans `predict_impact()` (ligne 824-826)
```python
'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 1.5
```

**Différence** :
- **Fast** : Correction AGRESSIVE (×0.23) si TTR > 20
- **Slow** : Toujours TTR = latence × 1.5

**❓ Quelle méthode est plus précise ?**

---

### Problème #4 : Direction Calculée 2 Fois ❌

**Où** :
1. **Ligne 468** : Dans `predict_impact_fast()` → `direction = get_event_direction(...)`
2. **Externe** : Dans `sequence_multi_event_timeline_v87` → RE-APPEL `get_direction_func(...)`

**Conséquence** : Même calcul effectué 2 fois !

---

## 🔬 POINTS À VALIDER

### Test de Validation Requis

**Script** : `test_validation_11sept.py`

**Objectif** : Comparer formules théoriques vs données MT5 réelles

**Métriques** :
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)
- Corrélation

**Cas de test** : 11 septembre 2025 (14:30)

---

## 💡 RECOMMANDATIONS SESSION 48

### Phase 1 : Validation (PRIORITÉ)

1. ✅ Cartographie terminée (ce document)
2. ⏳ **Lancer test validation**
3. ⏳ Analyser métriques MAE
4. ⏳ Identifier formule correcte

### Phase 2 : Corrections (Session 49 ?)

Si MAE < 20 pips → Corriger uniquement pullback  
Si MAE > 50 pips → Refonte méthodologie requise

### Phase 3 : Refactoring (Session 50 ?)

1. **Externaliser calculs d'impact** hors du planificateur
2. **Créer module unique** `impact_calculator.py`
3. **Centraliser appels** → Une seule méthode, une seule formule
4. **Simplifier** architecture du planificateur

---

## 📋 DÉPENDANCES EXTERNES

### Fonctions Appelées Depuis Modules Externes

| Fonction | Module | Ligne |
|----------|--------|-------|
| `sequence_multi_event_timeline()` | `sequence_multi_event_timeline_v87` | 1567 |
| `calculate_ttr_accuracy_stats()` | `sequence_multi_event_timeline_v87` | 1579 |
| `display_sequential_timeline()` | `streamlit_sequential_ui` | 1582 |
| `ForecastEngine.calculate_family_stats()` | `forecaster_mvp` | 808 |
| `LatencyAnalyzer.calculate_family_latency_stats()` | `latency_analyzer` | 781 |

---

## 🎯 PROCHAINES ACTIONS

### Session 48 (Maintenant)

- [x] Cartographie complète ✅
- [ ] Lancer `test_validation_11sept.py`
- [ ] Analyser résultats
- [ ] Documenter découvertes

### Session 49 (Future)

- [ ] Corriger méthode de calcul selon résultats
- [ ] Refactorer architecture
- [ ] Externaliser calculs d'impact

---

**📊 Tokens Session 48** : ~100k / 190k (53%)  
**⏱️ Temps estimé restant** : ~60k tokens disponibles

---

*Document généré automatiquement - Session 48*  
*Fichier source : 4_Planificateur_STABLE_0159_PERFECT.py*
