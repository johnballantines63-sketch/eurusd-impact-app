# 🔬 ANALYSE COMPARATIVE DES MÉTHODES DE CALCUL D'IMPACT
**Session 48** - Analyse Approfondie  
**Date** : 23 octobre 2025

---

## 🎯 OBJECTIF

Comparer les **3 méthodes de calcul d'impact** présentes dans le planificateur et identifier laquelle est correcte.

---

## 📊 VUE D'ENSEMBLE DES MÉTHODES

| Méthode | Fonction | Lignes | Source Données | Performance |
|---------|----------|--------|----------------|-------------|
| **A** | `predict_impact_fast()` | 423-478 | DB pré-calculée | ⚡ ULTRA-RAPIDE |
| **B** | `predict_impact()` | 750-875 | LatencyAnalyzer + ForecastEngine | 🐢 LENTE |
| **C** | `sequence_multi_event_timeline` (externe) | v87 | ForecastEngine.predict_impact_v9_clean | ❓ Inconnu |

---

## 🔬 MÉTHODE A : `predict_impact_fast()`

### 📍 Localisation
- **Fichier** : `4_Planificateur_STABLE_0159_PERFECT.py`
- **Lignes** : 423-478 (56 lignes)

### 🔧 Signature
```python
def predict_impact_fast(family, surprise, precomputed_stats, years_back=3):
    """Version ULTRA-RAPIDE"""
```

### 📥 Entrées
- `family` : str (ex: "NFP", "CPI")
- `surprise` : float (pourcentage écart actual vs forecast)
- `precomputed_stats` : dict (depuis DB via `load_precomputed_stats_from_db()`)
- `years_back` : int (défaut 3, **non utilisé**)

### 📤 Sorties
```python
{
    'predicted_pips': float,      # Impact en pips
    'direction': int (-1 ou +1),  # Direction EUR/USD
    'latency_median': float,      # Latence médiane (min)
    'latency_p20': float,         # P20
    'latency_p80': float,         # P80
    'ttr_median': float,          # TTR médian (min) - CORRIGÉ
    'ttr_p20': float,             # P20 - CORRIGÉ
    'ttr_p80': float,             # P80 - CORRIGÉ
    'n_similar': int,             # Nombre événements historiques
    'mfe_p80': float,             # MFE P80 historique
    'source': 'precomputed_db_corrected'
}
```

### 🧮 Formule de Calcul

#### Étape 1 : Récupération Stats
```python
if family in precomputed_stats:
    stats = precomputed_stats[family]
    mfe = stats['mfe_p80']  # Maximum Favorable Excursion P80
```

#### Étape 2 : Facteur d'Impact
```python
impact_factor = min(2.0, 1.0 + (surprise / 100)) if surprise > 0.5 else 1.0
```

**Exemples** :
- `surprise = 0%` → `impact_factor = 1.0` (100%)
- `surprise = 50%` → `impact_factor = 1.5` (150%)
- `surprise = 100%` → `impact_factor = 2.0` (200% - plafond)
- `surprise = 200%` → `impact_factor = 2.0` (plafond)

#### Étape 3 : Impact Final
```python
impact = mfe * impact_factor
```

#### Étape 4 : Direction
```python
direction = get_event_direction(family, surprise)
```

#### Étape 5 : Correction TTR (v8.5)
```python
ttr_corrected = stats['ttr_median']
ttr_p20_corrected = stats['ttr_p20']
ttr_p80_corrected = stats['ttr_p80']

if ttr_corrected > 20:
    correction_factor = 0.23  # Basé sur backtest 11/09/2025
    ttr_corrected = stats['ttr_median'] * correction_factor
    ttr_p20_corrected = stats['ttr_p20'] * correction_factor
    ttr_p80_corrected = stats['ttr_p80'] * correction_factor
```

**Justification** :
```
CPI :     39 min → 7 min (× 0.18)
Jobless : 31 min → 7 min (× 0.23)
Current : 50 min → 7 min (× 0.14)
Moyenne : × 0.20
Utilisé : × 0.23 (au-dessus moyenne pour sécurité)
```

### ⚡ Avantages
- ✅ **ULTRA-RAPIDE** : Lookup dict simple
- ✅ **CACHE** : Stats pré-calculées en DB
- ✅ **CORRECTION TTR** : Facteur empirique × 0.23

### ⚠️ Inconvénients
- ❌ **Fallback** : Si `family not in precomputed_stats` → Appelle `predict_impact()`
- ❌ **Formule simple** : Linéaire avec plafond

---

## 🔬 MÉTHODE B : `predict_impact()`

### 📍 Localisation
- **Fichier** : `4_Planificateur_STABLE_0159_PERFECT.py`
- **Lignes** : 750-875 (126 lignes)

### 🔧 Signature
```python
def predict_impact(family, surprise, years_back=3):
    """
    Prédit impact avec latence et TTR basés sur historique réel (avec cache)
    ✅ CORRECTION: Utilise LatencyAnalyzer pour latences précises
    """
```

### 📥 Entrées
- `family` : str
- `surprise` : float
- `years_back` : int (défaut 3, **UTILISÉ**)

### 📤 Sorties
```python
{
    'predicted_pips': float,
    'direction': int (-1 ou +1),
    'latency_median': float,
    'latency_p20': float,
    'latency_p80': float,
    'ttr_median': float,
    'ttr_p20': float,
    'ttr_p80': float,
    'n_similar': int,
    'mfe_p80': float
}
```

### 🧮 Formule de Calcul

#### Étape 1 : Cache Check
```python
cache_key = f"{family}_{years_back}"
if cache_key in st.session_state.family_stats_cache:
    stats = st.session_state.family_stats_cache[cache_key]
```

#### Étape 2 : Calcul Latence (LatencyAnalyzer)
```python
analyzer = LatencyAnalyzer(get_db_path())
latency_stats = analyzer.calculate_family_latency_stats(
    family_pattern=pattern,
    threshold_pips=5.0,
    min_events=5,
    lookback_days=years_back * 365
)
```

#### Étape 3 : Calcul MFE (ForecastEngine)
```python
engine = ForecastEngine(get_db_path())
mfe_stats = engine.calculate_family_stats(
    pattern,
    horizon_minutes=60,
    hist_years=years_back,
    countries=None
)
```

#### Étape 4 : Calcul TTR (v8.5)
```python
'ttr_median': latency_stats['initial_reaction']['median_minutes'] * 1.5
'ttr_p20': latency_stats['initial_reaction']['median_minutes'] * 1.0
'ttr_p80': latency_stats['initial_reaction']['median_minutes'] * 2.0
```

#### Étape 5 : Facteur de Surprise
```python
surprise_factor = min(abs(surprise) / 50.0, 2.0)
```

**Exemples** :
- `surprise = 0%` → `surprise_factor = 0.0`
- `surprise = 25%` → `surprise_factor = 0.5`
- `surprise = 50%` → `surprise_factor = 1.0`
- `surprise = 100%` → `surprise_factor = 2.0` (plafond)

#### Étape 6 : Impact Ajusté
```python
adjusted_impact = base_impact * (0.5 + 0.5 * surprise_factor)
```

**Exemples** :
- `surprise = 0%` → `adjusted_impact = base_impact × 0.5` (50%)
- `surprise = 50%` → `adjusted_impact = base_impact × 1.0` (100%)
- `surprise = 100%` → `adjusted_impact = base_impact × 1.5` (150%)

#### Étape 7 : Direction
```python
direction = 1 if surprise > 0 else -1
```

⚠️ **ATTENTION** : Direction **SIMPLISTE** ! Ne tient PAS compte du sentiment de la famille.

### ⚡ Avantages
- ✅ **Latence précise** : Depuis `LatencyAnalyzer`
- ✅ **Cache session** : `st.session_state.family_stats_cache`
- ✅ **Plancher** : Impact minimum = 50% de base

### ⚠️ Inconvénients
- ❌ **LENTE** : 2 appels DB (`LatencyAnalyzer` + `ForecastEngine`)
- ❌ **Direction simpliste** : Ne gère pas sentiment inversé
- ❌ **Formule différente** : Plancher 0.5 vs linéaire

---

## 🔬 MÉTHODE C : `sequence_multi_event_timeline` (Externe)

### 📍 Localisation
- **Fichier** : `sequence_multi_event_timeline_v87.py` (externe)
- **Lignes** : Inconnues

### 🔧 Appel
```python
from sequence_multi_event_timeline_v87 import sequence_multi_event_timeline

phases = sequence_multi_event_timeline(
    predictions_for_seq, 
    real_prices_df=real_prices_df
)
```

### 🧮 Formule de Calcul (Supposée)

D'après le MESSAGE_SESSION47_SESSION48.md :

```python
# Dans calculate_vectorial_sum()
impact = ForecastEngine.predict_impact_v9_clean(score, num_events)
direction = get_direction_func(family, surprise)
```

### ❓ Inconnu
- ⚠️ **Formule exacte** de `predict_impact_v9_clean()` ?
- ⚠️ **Paramètres** : `score` vs `surprise` ?
- ⚠️ **Direction** : Appelle quelle fonction ?

---

## 🚨 COMPARAISON DES FORMULES

### Cas Test : `surprise = 50%`, `mfe_p80 = 20 pips`

| Méthode | Formule | Résultat |
|---------|---------|----------|
| **A** (fast) | `20 × (1.0 + 50/100)` | **30 pips** (150%) |
| **B** (slow) | `20 × (0.5 + 0.5 × 1.0)` | **20 pips** (100%) |
| **C** (timeline) | `predict_impact_v9_clean(?)` | **❓ Inconnu** |

### Cas Test : `surprise = 0%`, `mfe_p80 = 20 pips`

| Méthode | Formule | Résultat |
|---------|---------|----------|
| **A** (fast) | `20 × 1.0` | **20 pips** (100%) |
| **B** (slow) | `20 × (0.5 + 0)` | **10 pips** (50%) |
| **C** (timeline) | `?` | **❓** |

### Cas Test : `surprise = 100%`, `mfe_p80 = 20 pips`

| Méthode | Formule | Résultat |
|---------|---------|----------|
| **A** (fast) | `20 × 2.0` (plafond) | **40 pips** (200%) |
| **B** (slow) | `20 × (0.5 + 0.5 × 2.0)` | **30 pips** (150%) |
| **C** (timeline) | `?` | **❓** |

---

## 🎯 DIFFÉRENCES CRITIQUES

### 1. Facteur de Surprise

**Méthode A** :
```python
factor = 1.0 + (surprise / 100)  # Linéaire, plafond 2.0
```

**Méthode B** :
```python
factor = 0.5 + 0.5 × (surprise / 50)  # Plancher 0.5, plafond 1.5
```

**Impact** :
- Pour `surprise = 0%` :
  - **A** → 100% de base
  - **B** → 50% de base ← **PLUS CONSERVATEUR**
  
- Pour `surprise = 50%` :
  - **A** → 150% de base
  - **B** → 100% de base ← **MOINS AGRESSIF**

### 2. Direction

**Méthode A** :
```python
direction = get_event_direction(family, surprise)
# → Gère sentiment inversé (Jobless, CPI, etc.)
```

**Méthode B** :
```python
direction = 1 if surprise > 0 else -1
# → NE gère PAS sentiment inversé ❌
```

**Conséquence** :
- **Méthode B BUGGUÉE** pour Jobless Claims, CPI, Unemployment !
- Exemple : `Jobless Claims +28%` → Méthode B donne `+1` (UP) ❌
- Correct : `+1` (EUR/USD UP car USD DOWN)

### 3. Correction TTR

**Méthode A** :
```python
if ttr > 20:
    ttr_corrected = ttr × 0.23
```

**Méthode B** :
```python
ttr = latency × 1.5  # Toujours
```

**Impact** :
- **A** : Correction agressive si TTR > 20 min
- **B** : Pas de correction, juste ratio fixe

---

## ✅ CONCLUSION PRÉLIMINAIRE

### Méthode Recommandée : **MÉTHODE A (predict_impact_fast)**

**Raisons** :
1. ✅ **Direction correcte** : Gère sentiment inversé
2. ✅ **Performance** : Ultra-rapide (cache DB)
3. ✅ **Correction TTR** : Facteur empirique validé
4. ✅ **Formule intuitive** : `impact = base × (1 + surprise%)`

### Problèmes Identifiés

#### Méthode B (`predict_impact`)
- ❌ **Direction bugguée** : Ne gère pas sentiment inversé
- ❌ **Formule différente** : Plancher 0.5 non justifié
- ⚠️ **Usage** : Fallback uniquement si A échoue

#### Méthode C (`sequence_multi_event_timeline`)
- ❓ **Formule inconnue** : À investiguer
- ❌ **Redondance** : RE-CALCULE impact alors que A l'a déjà fait
- 🚨 **PRIORITÉ** : Examiner `predict_impact_v9_clean()`

---

## 📋 ACTIONS REQUISES

### Immédiat (Session 48)

1. ✅ **Cartographie terminée**
2. ⏳ **Lancer test validation** : `test_validation_11sept.py`
3. ⏳ **Examiner** : `sequence_multi_event_timeline_v87.py`
4. ⏳ **Comparer** : Résultats Méthode A vs Méthode C

### Session 49

1. **Corriger Méthode B** : Ajouter `get_event_direction()`
2. **Éliminer redondance** : Passer impact pré-calculé à timeline
3. **Unifier formule** : Une seule méthode de calcul

---

## 🔬 VALIDATION EMPIRIQUE REQUISE

### Test avec Données Réelles

**Cas 11/09/2025 à 14:30** :

| Événement | Surprise | Formule A | Formule B | Réalité MT5 | Meilleure ? |
|-----------|----------|-----------|-----------|-------------|-------------|
| Jobless | +28% | ? pips | ? pips | ? pips | ❓ |
| CPI | +12% | ? pips | ? pips | ? pips | ❓ |
| Current | -5% | ? pips | ? pips | ? pips | ❓ |

**À exécuter** : `python3 test_validation_11sept.py`

---

**📊 Tokens Session 48** : ~103k / 190k (54%)  
**Prochaine étape** : Lancer test validation

---

*Document d'analyse - Session 48*
