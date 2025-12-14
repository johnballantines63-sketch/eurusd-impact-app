# 🗺️ CARTOGRAPHIE COMPLÈTE DU PLANIFICATEUR
**Session 48** - 23 octobre 2025  
**Fichier** : `4_Planificateur_STABLE_0159_PERFECT.py`  
**Lignes totales** : 1742  
**Taille** : 91.3 KB

---

## 📊 RÉSUMÉ EXÉCUTIF

### Statistiques Globales
- **Fonctions définies** : 19 fonctions
- **Imports externes** : 12 modules
- **Appels à fonctions externes** : sequence_multi_event_timeline_v87, ForecastEngine, LatencyAnalyzer
- **Problème critique identifié** : ⚠️ **DOUBLE CALCUL D'IMPACT** (2 méthodes différentes)

### Catégories de Fonctions

| Catégorie | Nombre | Lignes Code | Priorité Audit |
|-----------|--------|-------------|----------------|
| 🎯 CALCUL IMPACT | 2 | ~200 | ⭐⭐⭐ CRITIQUE |
| 🧭 DIRECTION | 1 | ~50 | ⭐⭐⭐ CRITIQUE |
| 🔄 REFRESH DATA | 1 | ~40 | ⭐ Faible |
| 💾 PRÉCHARGEMENT | 1 | ~30 | ⭐ Faible |
| 📊 CHARGEMENT DATA | 3 | ~150 | ⭐⭐ Moyenne |
| 🕐 GROUPEMENT | 2 | ~80 | ⭐ Faible |
| 📐 FIBONACCI | 1 | ~15 | ⭐ Faible |
| 📈 TIMELINE | 1 | ~200 | ⭐ Faible |
| ⚠️ ANALYSE | 3 | ~80 | ⭐ Faible |
| 🎯 BACKTEST | 3 | ~150 | ⭐⭐ Moyenne |

---

## 🎯 SECTION CRITIQUE : FONCTIONS DE CALCUL D'IMPACT

### ⚠️ PROBLÈME IDENTIFIÉ : DOUBLE CALCUL

Le planificateur contient **2 fonctions de calcul d'impact** qui utilisent des **formules différentes** :

---

### 🔴 FONCTION 1 : `predict_impact_fast()`

**Localisation** : Lignes 398-461  
**Usage** : PRINCIPALE - Utilisée par le planificateur  
**Source données** : Stats pré-calculées en DB

#### Signature
```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3)
```

#### Formule Impact
```python
mfe = stats['mfe_p80']
impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
impact = mfe * impact_factor
```

#### Formule Direction
```python
direction = get_event_direction(family, surprise)
```

#### Formule TTR
```python
# Si TTR > 20 min, appliquer correction
correction_factor = 0.23
ttr_corrected = stats['ttr_median'] * correction_factor
```

#### Retour
```python
return {
    'predicted_pips': impact,
    'direction': direction,
    'latency_median': stats['latency_median'],
    'ttr_median': ttr_corrected,  # ← CORRIGÉ v8.5
    'source': 'precomputed_db_corrected'
}
```

#### Points Clés
- ✅ Utilise stats pré-calculées (RAPIDE)
- ✅ Applique correction TTR (facteur 0.23)
- ✅ Direction via `get_event_direction()`
- ⚠️ Formule simple : `mfe × (1 + surprise/100)`
- 📊 Source : `precomputed_stats` dict

---

### 🔴 FONCTION 2 : `predict_impact()`

**Localisation** : Lignes 750-867  
**Usage** : FALLBACK - Si famille pas en cache  
**Source données** : Calcul dynamique (LatencyAnalyzer + ForecastEngine)

#### Signature
```python
def predict_impact(family, surprise, years_back=3)
```

#### Processus Calcul

**Étape 1 : Latence (LatencyAnalyzer)**
```python
analyzer = LatencyAnalyzer(get_db_path())
latency_stats = analyzer.calculate_family_latency_stats(
    family_pattern=pattern,
    threshold_pips=5.0,
    min_events=5,
    lookback_days=years_back * 365
)
```

**Étape 2 : MFE (ForecastEngine)**
```python
engine = ForecastEngine(get_db_path())
mfe_stats = engine.calculate_family_stats(
    pattern,
    horizon_minutes=60,
    hist_years=years_back,
    countries=None
)
```

**Étape 3 : Combiner**
```python
stats = {
    'latency_median': latency_stats['initial_reaction']['median_minutes'],
    'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 1.5,  # ← Formule différente !
    'mfe_p80': mfe_stats.get('mfe_p80', 10)
}
```

#### Formule Impact
```python
base_impact = stats['mfe_p80']
direction = 1 if surprise > 0 else -1  # ← DIFFÉRENT de predict_impact_fast !
surprise_factor = min(abs(surprise) / 50.0, 2.0)
adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
```

#### Retour
```python
return {
    'predicted_pips': adjusted_impact,
    'direction': direction,  # ← Formule simple, PAS get_event_direction()
    'latency_median': stats['latency_median'],
    'ttr_median': stats['ttr_median'],  # ← TTR = latence × 1.5
    'n_similar': stats['n_events'],
    'mfe_p80': stats['mfe_p80']
}
```

#### Points Clés
- ⚠️ Calcul dynamique (LENT)
- ⚠️ TTR = latence × 1.5 (PAS de correction 0.23)
- ⚠️ Direction simplifiée : `1 if surprise > 0 else -1`
- ❌ N'utilise PAS `get_event_direction()` (ignore sentiment famille)
- 🐌 Appelle 2 moteurs (LatencyAnalyzer + ForecastEngine)

---

## 🧭 FONCTION CRITIQUE : `get_event_direction()`

**Localisation** : Lignes 497-548  
**Usage** : Calcule direction EUR/USD selon sentiment de famille  
**Appelé par** : `predict_impact_fast()` UNIQUEMENT

### Dictionnaire Sentiment
```python
FAMILY_SENTIMENT = {
    # INVERSÉ : Surprise+ = BAD = EUR/USD DOWN
    'Jobless_Claims': -1,
    'Unemployment': -1,
    'Inflation': -1,
    'CPI': -1,
    
    # NORMAL : Surprise+ = GOOD = EUR/USD DOWN
    'GDP': 1,
    'Retail_Sales': 1,
    'NFP': 1,
    # ... etc
}
```

### Logique Direction
```python
def get_event_direction(family, surprise):
    family_normalized = family.replace(' ', '_')
    sentiment = FAMILY_SENTIMENT.get(family_normalized, 1)
    
    if surprise > 0:
        if sentiment == -1:
            direction = 1  # Famille inversée
        else:
            direction = -1  # Famille normale
    else:
        if sentiment == -1:
            direction = -1
        else:
            direction = 1
    
    return direction
```

### Exemple
```python
# CPI (famille inversée, sentiment = -1)
CPI, surprise = +2.0 → direction = +1 (EUR/USD UP)
CPI, surprise = -2.0 → direction = -1 (EUR/USD DOWN)

# NFP (famille normale, sentiment = 1)
NFP, surprise = +100K → direction = -1 (EUR/USD DOWN)
NFP, surprise = -100K → direction = +1 (EUR/USD UP)
```

---

## 🚨 ANALYSE DES CONFLITS

### Conflit #1 : Formules Impact Différentes

| Aspect | `predict_impact_fast()` | `predict_impact()` |
|--------|-------------------------|---------------------|
| **Base** | `mfe_p80` | `mfe_p80` |
| **Facteur** | `1.0 + (surprise / 100)` | `0.5 + 0.5 × (surprise / 50)` |
| **Max facteur** | 2.0 | 2.0 |
| **Exemple surprise=50** | `impact = mfe × 1.5` | `impact = mfe × 1.0` |
| **Exemple surprise=100** | `impact = mfe × 2.0` | `impact = mfe × 1.5` |

**⚠️ RÉSULTAT** : Impacts différents pour même surprise !

---

### Conflit #2 : Direction

| Méthode | `predict_impact_fast()` | `predict_impact()` |
|---------|-------------------------|---------------------|
| **Fonction** | `get_event_direction(family, surprise)` | `1 if surprise > 0 else -1` |
| **Utilise sentiment** | ✅ OUI | ❌ NON |
| **Exemple CPI +2.0** | direction = +1 (UP) | direction = +1 (UP) |
| **Exemple NFP +100K** | direction = -1 (DOWN) | direction = +1 (UP) ⚠️ |

**🚨 CRITIQUE** : `predict_impact()` ignore le sentiment des familles !

---

### Conflit #3 : TTR

| Méthode | `predict_impact_fast()` | `predict_impact()` |
|---------|-------------------------|---------------------|
| **Formule base** | `stats['ttr_median']` | `latence × 1.5` |
| **Correction** | × 0.23 si > 20 min | Aucune |
| **Exemple latence=5** | `ttr_corrected ≈ 1.15 min` | `ttr = 7.5 min` |
| **Exemple latence=30** | `ttr_corrected ≈ 6.9 min` | `ttr = 45 min` |

**⚠️ RÉSULTAT** : Écart TTR de 6x possible !

---

## 🔍 AUTRES FONCTIONS (Non-Critiques)

### 📊 Chargement Données

#### `load_precomputed_stats_from_db()`
- **Lignes** : 122-154
- **Rôle** : Charge stats pré-calculées depuis DB
- **Cache** : `@st.cache_data(ttl=3600)`
- **Retour** : `dict {family: stats}`

#### `load_all_events_for_date()`
- **Lignes** : 551-616
- **Rôle** : Charge événements mapped + unmapped
- **Cache** : `@st.cache_data(ttl=3600)`
- **Retour** : `{'mapped': df, 'unmapped': df}`

#### `get_future_events()`
- **Lignes** : 628-672
- **Rôle** : Récupère événements d'une période
- **Retour** : DataFrame

### 🕐 Groupement Événements

#### `group_events_by_time_window()`
- **Lignes** : 268-314
- **Rôle** : Groupe événements par proximité temporelle
- **Paramètre** : `max_gap_minutes=30`
- **Retour** : Liste de clusters

#### `calculate_cluster_impact()`
- **Lignes** : 316-352
- **Rôle** : Calcule impact cumulé d'un cluster
- **Retour** : Dict avec `total_pips`, `min_latency`, `max_ttr`

### 📐 Fibonacci

#### `calculate_fibonacci_levels()`
- **Lignes** : 870-883
- **Rôle** : Calcule niveaux retracement
- **Retour** : Dict {level: pips}

### 📈 Timeline

#### `create_timeline_chart()`
- **Lignes** : 886-1054
- **Rôle** : Crée graphique Plotly interactif
- **Retour** : Figure Plotly

### ⚠️ Analyse

#### `detect_overlaps()`
- **Lignes** : 1057-1082
- **Rôle** : Détecte chevauchements TTR
- **Retour** : Liste overlaps

#### `calculate_tradability_score()`
- **Lignes** : 1085-1113
- **Rôle** : Score 0-100 de tradabilité
- **Retour** : int

### 🎯 Backtest

#### `get_real_prices_batch()`
- **Lignes** : 1116-1171
- **Rôle** : Récupère prix MT5 (batch optimisé)
- **Retour** : `dict {idx: DataFrame}`

#### `measure_real_impact()`
- **Lignes** : 1174-1227
- **Rôle** : Mesure impact réel depuis prix
- **Retour** : Dict métriques

#### `create_backtest_chart()`
- **Lignes** : 1230-1324
- **Rôle** : Graphique comparaison prédit vs réel
- **Retour** : Figure Plotly

### 🔄 Utilitaires

#### `refresh_today_events()`
- **Lignes** : 73-113
- **Rôle** : Mise à jour depuis EODHD API
- **Retour** : bool

#### `identify_family()`
- **Lignes** : 619-625
- **Rôle** : Identifie famille via regex
- **Retour** : str ou None

---

## 🔗 GRAPHE DE DÉPENDANCES

### Fonction Principale : `predict_impact_fast()`

```
predict_impact_fast()
├─> precomputed_stats (dict en session_state)
├─> get_event_direction(family, surprise) ← IMPORTANT
│   └─> FAMILY_SENTIMENT (dict global)
└─> [RETOUR] dict prediction
```

### Fonction Fallback : `predict_impact()`

```
predict_impact()
├─> FAMILY_PATTERNS (module externe)
├─> LatencyAnalyzer.calculate_family_latency_stats() ← EXTERNE
├─> ForecastEngine.calculate_family_stats() ← EXTERNE
├─> [PAS d'appel à get_event_direction()] ⚠️
└─> [RETOUR] dict prediction
```

### Appel Depuis UI

```
Interface Streamlit
└─> predictions.append({
      'event': event,
      'surprise': surprise,
      **predict_impact_fast(family, surprise, precomputed_stats)  ← APPEL #1
    })

    OU (si pas en cache)

    **predict_impact(family, surprise, years_back)  ← APPEL #2
```

---

## 📊 APPELS À FONCTIONS EXTERNES

### Module `sequence_multi_event_timeline_v87`

**Import** : Ligne 57
```python
from sequence_multi_event_timeline_v87 import (
    sequence_multi_event_timeline,
    calculate_ttr_accuracy_stats
)
```

**Utilisé** : Ligne 1630
```python
phases = sequence_multi_event_timeline(
    predictions_for_seq, 
    real_prices_df=real_prices_df
)
```

**🚨 DÉCOUVERTE SESSION 47** : Cette fonction RE-CALCULE l'impact !

---

## 🎯 RECOMMANDATIONS PRIORITAIRES

### 🔴 Priorité P0 : Unifier Calcul Impact

**Problème** : 2 fonctions, 2 formules différentes

**Actions** :
1. Tester les 2 formules avec script validation
2. Choisir LA formule qui matche le mieux MT5
3. Supprimer ou aligner l'autre

### 🔴 Priorité P1 : Corriger Direction

**Problème** : `predict_impact()` ignore sentiment famille

**Action** : Forcer appel à `get_event_direction()` dans `predict_impact()`

### 🔴 Priorité P2 : Unifier TTR

**Problème** : 2 formules TTR différentes

**Actions** :
1. Valider quelle formule est correcte
2. Appliquer partout (correction 0.23 ou latence × 1.5 ?)

### 🟡 Priorité P3 : Externaliser Calculs

**Problème** : Logique impact mélangée avec UI

**Action** : Créer module `impact_calculator.py`
```python
# impact_calculator.py
class ImpactCalculator:
    def calculate_impact(self, family, surprise, stats):
        # UNE SEULE méthode
        pass
    
    def get_direction(self, family, surprise):
        # Centralisé
        pass
```

---

## 📋 CHECKLIST AUDIT COMPLET

### Fonctions Auditées

- [x] `predict_impact_fast()` ⭐⭐⭐
- [x] `predict_impact()` ⭐⭐⭐
- [x] `get_event_direction()` ⭐⭐⭐
- [x] `load_precomputed_stats_from_db()` ⭐
- [x] `load_all_events_for_date()` ⭐
- [x] `get_future_events()` ⭐
- [x] `group_events_by_time_window()` ⭐
- [x] `calculate_cluster_impact()` ⭐
- [x] `calculate_fibonacci_levels()` ⭐
- [x] `create_timeline_chart()` ⭐
- [x] `detect_overlaps()` ⭐
- [x] `calculate_tradability_score()` ⭐
- [x] `get_real_prices_batch()` ⭐⭐
- [x] `measure_real_impact()` ⭐⭐
- [x] `create_backtest_chart()` ⭐
- [x] `refresh_today_events()` ⭐
- [x] `identify_family()` ⭐

### Problèmes Identifiés

- [x] Double calcul impact
- [x] Formules différentes
- [x] Direction incohérente
- [x] TTR incohérent
- [x] Pas d'appel `get_event_direction()` dans `predict_impact()`

---

## 🎯 PROCHAINES ÉTAPES SESSION 49

### Phase 1 : Tests Empiriques
1. Lancer `test_validation_11sept.py`
2. Comparer `predict_impact_fast()` vs `predict_impact()`
3. Mesurer MAE pour chaque formule

### Phase 2 : Décision
- Si formule A meilleure → Adopter partout
- Si formule B meilleure → Adopter partout
- Si hybride nécessaire → Créer formule C

### Phase 3 : Refactoring
1. Créer `impact_calculator.py`
2. Une seule méthode `calculate_impact()`
3. Une seule méthode `get_direction()`
4. Tests unitaires

### Phase 4 : Mise à jour
1. Modifier planificateur
2. Modifier `sequence_multi_event_timeline_v87`
3. Tests end-to-end

---

**📊 Token Check** : ~99k / 190k (52%)  
**⏱️ Temps écoulé Session 48** : ~1h30  
**📋 Prochaine action** : Créer rapport final + message S49

---

*Cartographie complète - Session 48*  
*Date : 23 octobre 2025*
