# 🔍 DÉCOUVERTE CRITIQUE - Analyse Planificateur Multi-Événements

**Date :** 22 octobre 2025  
**Session :** 32 (Fin de session - Découverte tardive)  
**Fichier analysé :** `fx_impact_app/streamlit_app/pages/4_Planificateur-Multi-Evenements.py`  
**Taille :** 2,200+ lignes  
**Impact :** CRITIQUE pour Session 33

---

## 🎯 Contexte de la Découverte

En fin de Session 32, après avoir créé ScoringService, l'utilisateur a signalé que **plusieurs fonctions externalisées sont actuellement exécutées dans le Planificateur** et qu'il faut :

1. ✅ Les identifier précisément
2. ✅ Les migrer vers `eurusd_clean/app/utils/`
3. ✅ Corriger le Planificateur pour qu'il importe ces fonctions

**CRITIQUE** : Le Planificateur est le **cœur fonctionnel** de l'application. C'est là que tout s'articule.

---

## 📋 INVENTAIRE COMPLET DES FONCTIONS DU PLANIFICATEUR

### ✅ Fonctions Déjà Migrées (Sessions 29-32)

| Fonction/Module | Ancien Emplacement | Nouveau (eurusd_clean) | Session | Status |
|-----------------|-------------------|------------------------|---------|--------|
| **ForecastEngine** | `forecaster_mvp.py` | `app/core/calculations.py` | 29 | ✅ |
| **Event, EventFamily** | `event_families.py` | `app/core/models.py` | 29 | ✅ |
| **DataService** | Inline DB access | `app/services/data_service.py` | 30 | ✅ |
| **PredictionService** | `sequence_v87.py` | `app/services/prediction_service.py` | 31 | ✅ |
| **ScoringEngine** | `scoring_engine.py` | `app/services/scoring_service.py` | 32 | ✅ |

### ⚠️ Fonctions ENCORE dans le Planificateur (À migrer Session 33)

#### 1. **Gestion Fenêtres Temporelles** (Lignes ~190-280)

**Fonction :** `group_events_by_time_window(events, max_gap_minutes=30)`

**Code :**
```python
def group_events_by_time_window(events, max_gap_minutes=30):
    """
    Groupe les événements en clusters selon leur proximité temporelle
    
    Args:
        events: Liste de dict avec 'event_time'
        max_gap_minutes: Écart max entre deux événements d'un même cluster
    
    Returns:
        Liste de clusters, chaque cluster = {
            'window_start': datetime,
            'window_end': datetime,
            'events': [event1, event2, ...],
            'event_times': [time1, time2, ...]
        }
    """
    # ... 50 lignes de logique ...
```

**Utilisation :** Grouper événements proches (<30 min) pour analyser impact cumulé

**Destination :** `eurusd_clean/app/utils/time_windows.py`

---

**Fonction :** `calculate_cluster_impact(cluster, predictions_dict)`

**Code :**
```python
def calculate_cluster_impact(cluster, predictions_dict):
    """
    Calcule l'impact cumulé d'un cluster d'événements
    
    Args:
        cluster: Dict du cluster (de group_events_by_time_window)
        predictions_dict: Dict {event_key: prediction}
    
    Returns:
        Dict avec impact cumulé, latence min, TTR max
    """
    # ... 30 lignes de calcul vectoriel ...
```

**Utilisation :** Calculer somme vectorielle des impacts d'un cluster

**Destination :** `eurusd_clean/app/utils/time_windows.py`

---

#### 2. **Backtest et Prix Réels** (Lignes ~550-640)

**Fonction :** `get_real_prices_batch(event_times, window_minutes=60)`

**Code :**
```python
def get_real_prices_batch(event_times, window_minutes=60):
    """
    Récupère les prix réels pour plusieurs événements en UNE SEULE query (OPTIMISÉ)
    
    Args:
        event_times: Liste de datetime
        window_minutes: Fenêtre avant/après événement
    
    Returns:
        Dict {index: DataFrame(time, price)}
    """
    # ... 40 lignes d'optimisation SQL ...
```

**Utilisation :** Récupérer prix réels depuis `prices_1m` pour backtest

**Destination :** `eurusd_clean/app/utils/backtest.py`

**IMPORTANT :** Utilise UNE SEULE query SQL avec OR pour tous les événements (optimisation critique)

---

**Fonction :** `measure_real_impact(prices_df, threshold_pips=5.0)`

**Code :**
```python
def measure_real_impact(prices_df, threshold_pips=5.0):
    """
    Mesure l'impact réel du marché à partir des prix
    
    Args:
        prices_df: DataFrame avec colonnes time, price
        threshold_pips: Seuil pour détecter réaction (défaut 5)
    
    Returns:
        Dict avec :
            - real_impact_pips: Mouvement max observé
            - real_direction: +1 (UP) ou -1 (DOWN)
            - real_latency_minutes: Temps avant réaction ≥ threshold
            - real_ttr_minutes: Temps jusqu'au retournement
            - peak_time_minutes: Index du pic
            - had_reaction: Boolean
    """
    # ... 50 lignes d'analyse prix ...
```

**Utilisation :** Mesurer impact RÉEL depuis prix observés (pour validation TTR)

**Destination :** `eurusd_clean/app/utils/backtest.py`

**CRITIQUE :** Cette fonction est utilisée pour calculer le **TTR observé** qui corrige le TTR prédit (très imprécis)

---

#### 3. **Visualisation Backtest** (Lignes ~640-750)

**Fonction :** `create_backtest_chart(prices_df, event_time, predicted_impact, predicted_latency, predicted_ttr, real_metrics)`

**Code :**
```python
def create_backtest_chart(
    prices_df,
    event_time,
    predicted_impact,
    predicted_latency,
    predicted_ttr,
    real_metrics
):
    """
    Crée graphique comparaison prédiction vs réalité
    
    Args:
        prices_df: DataFrame prix réels
        event_time: Timestamp événement
        predicted_impact: Impact prédit (pips)
        predicted_latency: Latence prédite (min)
        predicted_ttr: TTR prédit (min)
        real_metrics: Dict depuis measure_real_impact()
    
    Returns:
        Plotly Figure
    """
    # ... 100 lignes de graphique Plotly ...
```

**Utilisation :** Afficher graphique comparaison prédiction vs réalité

**Destination :** `eurusd_clean/app/utils/visualization.py`

---

#### 4. **Détection Chevauchements** (Lignes ~500-530)

**Fonction :** `detect_overlaps(predictions)`

**Code :**
```python
def detect_overlaps(predictions):
    """
    Détecte les chevauchements entre fenêtres d'événements
    
    Args:
        predictions: Liste de dict avec event, ttr_median
    
    Returns:
        Liste de dict {
            'event1': str,
            'event2': str,
            'overlap_minutes': float,
            'severity': 'HIGH' | 'MEDIUM'
        }
    """
    # ... 25 lignes de détection ...
```

**Utilisation :** Détecter quand TTR d'un événement chevauche le suivant

**Destination :** `eurusd_clean/app/utils/time_windows.py`

---

#### 5. **Score Tradabilité** (Lignes ~530-550)

**Fonction :** `calculate_tradability_score(predictions, overlaps, time_span)`

**Code :**
```python
def calculate_tradability_score(predictions, overlaps, time_span):
    """
    Calcule un score de tradabilité de 0-100 pour la session
    
    Args:
        predictions: Liste prédictions
        overlaps: Liste chevauchements (detect_overlaps)
        time_span: Durée fenêtre (heures)
    
    Returns:
        Score 0-100
    """
    # ... 30 lignes de calcul score ...
```

**Utilisation :** Évaluer qualité de la session de trading (cohérence directionnelle, etc.)

**Destination :** `eurusd_clean/app/utils/scoring.py` (nouveau fichier)

---

#### 6. **Niveaux Fibonacci** (Lignes ~480-500)

**Fonction :** `calculate_fibonacci_levels(impact_pips, direction)`

**Code :**
```python
def calculate_fibonacci_levels(impact_pips, direction):
    """
    Calcule les niveaux de retracement Fibonacci
    
    Args:
        impact_pips: Mouvement total (pips)
        direction: +1 (UP) ou -1 (DOWN)
    
    Returns:
        Dict {'0%': 0, '23.6%': X, '38.2%': Y, ...}
    """
    levels = {
        '0%': 0,
        '23.6%': impact_pips * 0.236,
        '38.2%': impact_pips * 0.382,
        '50%': impact_pips * 0.5,
        '61.8%': impact_pips * 0.618,
        '78.6%': impact_pips * 0.786,
        '100%': impact_pips
    }
    
    if direction < 0:
        levels = {k: -v for k, v in levels.items()}
    
    return levels
```

**Utilisation :** Calculer zones support/résistance

**Destination :** `eurusd_clean/app/utils/fibonacci.py`

---

#### 7. **Timeline Visuelle** (Lignes ~400-480)

**Fonction :** `create_timeline_chart(predictions, weighted_latency, min_ttr)`

**Code :**
```python
def create_timeline_chart(predictions, weighted_latency, min_ttr):
    """
    Crée timeline visuelle interactive avec Plotly
    
    Args:
        predictions: Liste prédictions
        weighted_latency: Latence moyenne pondérée
        min_ttr: TTR minimum
    
    Returns:
        Plotly Figure
    """
    # ... 80 lignes de graphique Plotly ...
```

**Utilisation :** Afficher timeline événements avec fenêtres latence/TTR

**Destination :** `eurusd_clean/app/utils/visualization.py`

---

### 📊 Fonctions Auxiliaires (Lignes ~300-400)

**Fonction :** `load_empirical_scores_from_db()`

**Code :**
```python
@st.cache_data(ttl=3600)
def load_empirical_scores_from_db():
    """
    Charge les scores empiriques depuis event_families
    
    Returns:
        Dict {(event_key, country): {'score': float, 'impact': str}}
    """
```

**Utilisation :** Cache scores empiriques pour UI

**Destination :** **DÉJÀ COUVERT** par `DataService.get_event_families()` ✅

---

**Fonction :** `load_precomputed_stats_from_db()`

**Code :**
```python
@st.cache_data(ttl=3600)
def load_precomputed_stats_from_db():
    """Charge stats pré-calculées depuis DB"""
```

**Utilisation :** Cache stats latence/TTR pour UI

**Destination :** **DÉJÀ COUVERT** par `DataService.get_event_families()` ✅

---

**Fonction :** `predict_impact_fast()`

**Code :**
```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3, empirical_score=None, num_events=1):
    """Version ULTRA-RAPIDE avec support empirical_score"""
```

**Utilisation :** Wrapper optimisé pour prédictions rapides

**Destination :** **DÉJÀ COUVERT** par `PredictionService.predict_single_event()` ✅

---

**Fonction :** `predict_impact()`

**Code :**
```python
def predict_impact(family, surprise, years_back=3):
    """Prédit impact avec latence et TTR basés sur historique réel (avec cache)"""
```

**Utilisation :** Version non-optimisée (fallback)

**Destination :** **DÉJÀ COUVERT** par `PredictionService` ✅

---

**Fonction :** `get_event_direction()`

**Code :**
```python
FAMILY_SENTIMENT = {
    'Jobless_Claims': -1,
    'Unemployment': -1,
    'CPI': -1,
    'NFP': 1,
    'GDP': 1,
    # ...
}

def get_event_direction(family, surprise):
    """Calcule la direction EUR/USD selon le sentiment de la famille"""
```

**Utilisation :** Déterminer direction mouvement (UP/DOWN)

**Destination :** **DÉJÀ MIGRÉ** dans `PredictionService` (Session 31) ✅

---

## 🎯 CAS DE RÉFÉRENCE : 11 Septembre 2025

### Valeurs Confirmées par André (MT5)

**Document :** `docs/REFERENCE_CASE_11_SEPT_2025.md`

| Moment | Heure UTC | Prix | Rôle |
|--------|-----------|------|------|
| **Annonce** | 12:30:00 | 1.16816 | Départ |
| **TTR** | 12:35:00 | 1.17190 | Pic Phase 1 |
| **Pullback** | 12:45:00 | 1.16919 | Après nouvel event |
| **Stabilisation** | 13:10:00 | 1.17378 | Phase 2 |

**Phase 1 (12:30→12:35) :** **37.4 pips** (pas 522 pips !)  
**TTR réel :** **5 minutes** (pas 31-50 min prédits)

### Correction Historique

**IMPORTANT :** Les sessions précédentes mentionnaient incorrectement "522 pips" ou "600 pips" pour le 11 septembre. 

**Valeur correcte :** 37.4 pips jusqu'au TTR (Phase 1)

Cette erreur est maintenant corrigée. Les valeurs du document REFERENCE_CASE_11_SEPT_2025.md sont les références officielles.

### Impact sur le Code

Le Planificateur utilise ce cas pour :
1. ✅ Valider le TTR observé depuis prix réels
2. ✅ Calculer MAE/RMSE du TTR prédit vs observé
3. ✅ Afficher warning si TTR prédit > 20 min (très imprécis)

**Correction appliquée dans le Planificateur (v8.5) :**
```python
# Facteur de correction basé sur observations :
# CPI : 39 min → 7 min (× 0.18)
# Jobless : 31 min → 7 min (× 0.23)
# Current : 50 min → 7 min (× 0.14)
# Moyenne : × 0.20
correction_factor = 0.23
```

---

## 📋 PLAN DE MIGRATION SESSION 33

### Fichiers à Créer

#### 1. `app/utils/time_windows.py`

**Fonctions :**
- `group_events_by_time_window(events, max_gap_minutes=30)`
- `calculate_cluster_impact(cluster, predictions_dict)`
- `detect_overlaps(predictions)`

**Lignes estimées :** ~120 lignes

---

#### 2. `app/utils/backtest.py`

**Fonctions :**
- `get_real_prices_batch(event_times, window_minutes=60)`
- `measure_real_impact(prices_df, threshold_pips=5.0)`

**Lignes estimées :** ~100 lignes

**CRITIQUE :** `get_real_prices_batch()` utilise optimisation SQL avec OR pour tous événements (1 seule query)

---

#### 3. `app/utils/visualization.py`

**Fonctions :**
- `create_timeline_chart(predictions, weighted_latency, min_ttr)`
- `create_backtest_chart(prices_df, event_time, ...)`

**Lignes estimées :** ~200 lignes

---

#### 4. `app/utils/fibonacci.py`

**Fonctions :**
- `calculate_fibonacci_levels(impact_pips, direction)`

**Lignes estimées :** ~20 lignes

---

#### 5. `app/utils/scoring.py`

**Fonctions :**
- `calculate_tradability_score(predictions, overlaps, time_span)`

**Lignes estimées :** ~40 lignes

---

### Tests à Créer

#### 1. `tests/test_utils/test_time_windows.py`

**Tests :**
- test_group_events_by_time_window()
- test_calculate_cluster_impact()
- test_detect_overlaps()
- test_edge_cases (événements vides, 1 seul, etc.)

**Lignes estimées :** ~150 lignes

---

#### 2. `tests/test_utils/test_backtest.py`

**Tests :**
- test_get_real_prices_batch()
- test_measure_real_impact()
- test_edge_cases (pas de prix, prix manquants, etc.)
- **test_reference_case_11_sept_2025()** ← CRITIQUE

**Lignes estimées :** ~200 lignes

**IMPORTANT :** Créer test spécifique pour le cas 11 septembre avec valeurs confirmées

---

#### 3. `tests/test_utils/test_fibonacci.py`

**Tests :**
- test_calculate_fibonacci_levels_up()
- test_calculate_fibonacci_levels_down()
- test_edge_cases (impact 0, direction neutre)

**Lignes estimées :** ~50 lignes

---

#### 4. `tests/test_utils/test_scoring.py`

**Tests :**
- test_calculate_tradability_score()
- test_edge_cases (1 événement, tous même direction, etc.)

**Lignes estimées :** ~80 lignes

---

## ⚠️ DÉPENDANCES CRITIQUES

### Services Requis

Les nouvelles fonctions utilitaires dépendent de :

1. **DataService** ✅ (Session 30)
   - Pour `get_real_prices_batch()` → accès `prices_1m`

2. **PredictionService** ✅ (Session 31)
   - Pour `calculate_cluster_impact()` → utilise prédictions

3. **Pas de nouvelles dépendances** ✅

### Imports Externes

Les fonctions utilisent :
- `pandas` ✅
- `numpy` ✅
- `plotly` ✅ (pour visualisations)
- `datetime` / `timedelta` ✅
- `duckdb` ✅ (via DataService)

**Aucune nouvelle bibliothèque requise** ✅

---

## 🎯 RECOMMANDATIONS SESSION 33

### Priorité 1 : Utilitaires Critiques

**Ordre recommandé :**

1. **`app/utils/time_windows.py`** (1.5h)
   - Fonctions utilisées partout dans le Planificateur
   - Tests (1h)

2. **`app/utils/backtest.py`** (1.5h)
   - CRITIQUE pour validation TTR observé
   - Tests (1.5h) incluant test cas 11 septembre

3. **`app/utils/fibonacci.py`** (15 min)
   - Simple, rapide
   - Tests (30 min)

### Priorité 2 : Visualisation (Optionnel)

4. **`app/utils/visualization.py`** (2h)
   - Utile mais pas critique pour la logique
   - Peut être fait Session 34
   - Tests (1h) visuels difficiles à automatiser

### Priorité 3 : Scoring (Optionnel)

5. **`app/utils/scoring.py`** (30 min)
   - Simple calcul de score
   - Tests (30 min)

---

## 📊 ESTIMATION TOTALE SESSION 33

### Code Production

| Module | Lignes Estimées | Temps |
|--------|-----------------|-------|
| time_windows.py | 120 | 1.5h |
| backtest.py | 100 | 1.5h |
| fibonacci.py | 20 | 15min |
| visualization.py | 200 | 2h (opt) |
| scoring.py | 40 | 30min (opt) |
| **TOTAL** | **480** | **6h** |

### Tests

| Module | Lignes Estimées | Temps |
|--------|-----------------|-------|
| test_time_windows.py | 150 | 1h |
| test_backtest.py | 200 | 1.5h |
| test_fibonacci.py | 50 | 30min |
| test_visualization.py | 100 | 1h (opt) |
| test_scoring.py | 80 | 30min (opt) |
| **TOTAL** | **580** | **4.5h** |

**TOTAL GÉNÉRAL :** ~1,060 lignes / ~10.5h

**Tokens estimés :** 70,000-90,000

---

## ⚠️ POINTS D'ATTENTION CRITIQUES

### 1. TTR Observé vs Prédit

**Découverte du Planificateur :**

Le TTR prédit est **très imprécis** (MAE 30.1 min sur cas 11 sept).

**Solution appliquée :**
- Si événements passés → calculer TTR RÉEL depuis `prices_1m`
- Afficher MAE/RMSE pour validation
- Warning si TTR prédit > 20 min

**À migrer dans :** `app/utils/backtest.py`

---

### 2. Optimisation SQL Batch

**`get_real_prices_batch()` utilise UNE SEULE query :**

```python
# Créer conditions OR pour tous les événements
conditions = " OR ".join([
    f"(timestamp >= {e[1]} AND timestamp <= {e[2]})" 
    for e in epochs
])

query = f"""
SELECT timestamp, close
FROM prices_1m
WHERE {conditions}
ORDER BY timestamp ASC
"""
```

**IMPORTANT :** Ne pas créer N queries (1 par événement) → 1 seule query avec OR

---

### 3. Correction Facteur 0.758

Le Planificateur applique le **facteur 0.758** pour corriger la somme vectorielle.

**DÉJÀ MIGRÉ** dans `PredictionService.predict_multi_events()` ✅

Vérifier cohérence entre Planificateur et PredictionService.

---

### 4. Cas 11 Septembre - Validation

**CRITIQUE :** Créer test automatique avec valeurs confirmées :

```python
def test_reference_case_11_sept_2025():
    """Test validation cas référence 11 septembre"""
    
    # Récupérer prix réels
    prices = get_real_prices_batch(
        [datetime(2025, 9, 11, 12, 30, 0)],
        window_minutes=60
    )
    
    # Mesurer impact réel
    metrics = measure_real_impact(prices[0])
    
    # Validation
    assert 32 <= metrics['real_impact_pips'] <= 42  # 37.4 ±5
    assert 3 <= metrics['real_ttr_minutes'] <= 7    # 5 ±2
    assert metrics['real_direction'] == 1            # UP
```

---

## 📝 DOCUMENTS À METTRE À JOUR

### À Modifier

1. **`PROJECT_STATE.md`**
   - Ajouter section découverte Planificateur
   - Mettre à jour progression 75% → 80% (après Session 33)

2. **`MESSAGE_SESSION_33.md`**
   - Référencer ce document
   - Prioriser utilitaires critiques

3. **`ARCHITECTURE_ETAT_SESSION_32.md`**
   - Ajouter section `app/utils/` prévu

### À Créer Session 33

1. **`SESSION_33_SUMMARY.md`**
   - Résumé création utilitaires
   - Validation cas 11 septembre

2. **`PLANIFICATEUR_MIGRATION_PLAN.md`**
   - Plan détaillé correction Planificateur
   - Imports à modifier
   - Tests à exécuter

---

## 🎯 CONCLUSION

### Découverte Majeure

Le **Planificateur** contient **~500 lignes** de logique métier qui devrait être dans `app/utils/`.

Ces fonctions sont **critiques** pour :
- ✅ Groupement événements temporels
- ✅ Backtest avec prix réels
- ✅ Validation TTR observé
- ✅ Visualisations

### Impact

**Sans cette migration :**
- ❌ Planificateur ingérable (2,200 lignes)
- ❌ Logique dupliquée
- ❌ Impossible de tester unitairement
- ❌ Imports circulaires

**Avec cette migration :**
- ✅ Planificateur réduit à ~1,700 lignes
- ✅ Logique réutilisable
- ✅ Tests unitaires possibles
- ✅ Architecture propre

### Prochaines Étapes

**Session 33 :**
1. Créer `app/utils/time_windows.py` + tests
2. Créer `app/utils/backtest.py` + tests
3. Créer `app/utils/fibonacci.py` + tests
4. Valider cas 11 septembre
5. (Optionnel) Visualisation + Scoring

**Session 34 :**
1. Corriger Planificateur (imports)
2. Tester Planificateur bout-en-bout
3. Créer tests intégration

---

**Document créé :** 22 octobre 2025  
**Session :** 32 (Fin)  
**Tokens utilisés session :** 82,000 / 190,000 (43%)  
**Prêt pour :** Session 33

**🔍 DÉCOUVERTE CRITIQUE DOCUMENTÉE**
