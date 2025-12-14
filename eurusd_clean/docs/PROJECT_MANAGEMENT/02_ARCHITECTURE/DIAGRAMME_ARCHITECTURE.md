# 🏗️ DIAGRAMME D'ARCHITECTURE LOGICIELLE

**Version :** 1.0  
**Date :** 16 novembre 2025  
**Architecture :** Clean Architecture (3 couches)

---

## 📑 TABLE DES MATIÈRES

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Couche Présentation (UI)](#2-couche-présentation-ui)
3. [Couche Services](#3-couche-services)
4. [Couche Core (Métier)](#4-couche-core-métier)
5. [Couche Données](#5-couche-données)
6. [Flux de Données](#6-flux-de-données)
7. [Technologies Utilisées](#7-technologies-utilisées)

---

## 1. VUE D'ENSEMBLE

### Architecture en Couches

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE PRÉSENTATION (UI)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Streamlit Application                                    │  │
│  │  - Home.py                                                │  │
│  │  - pages/3_Planificateur_V3.py (650 lignes)              │  │
│  │  - pages/2_Planificateur_V2.py                           │  │
│  │  - pages/1_Calendrier_Trading.py                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ utilise
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE SERVICES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ DataService  │  │ Prediction   │  │ Scoring      │         │
│  │              │  │ Service      │  │ Service      │         │
│  │ - get_events│  │ - predict()  │  │ - calculate()│         │
│  │ - get_prices│  │ - validate() │  │ - weights    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ utilise
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE CORE (MÉTIER)                         │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │ FormulasValidated    │  │ ClusterImpactCalc   │           │
│  │                      │  │                      │           │
│  │ - impact_d()         │  │ - cluster_impact()   │           │
│  │ - ttr_c()            │  │ - double_wave()     │           │
│  │ - pullback_v2()      │  │ - overlapping()     │           │
│  └──────────────────────┘  └──────────────────────┘           │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │ DoubleWavePrediction │  │ PatternDetector      │           │
│  │                      │  │                      │           │
│  │ - predict_overlap()  │  │ - detect_double()   │           │
│  │ - check_criteria()   │  │ - detect_single()   │           │
│  └──────────────────────┘  └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ utilise
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE DONNÉES                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  warehouse.duckdb (205 MB)                                │  │
│  │  ├── events (58,449 événements)                           │  │
│  │  ├── event_families (2,467 scores)                        │  │
│  │  ├── prices_bern (1.1M prix 1-minute)                      │  │
│  │  └── validation_events (cas référence)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. COUCHE PRÉSENTATION (UI)

### Composants

**Streamlit Application**
```
streamlit_app/
├── Home.py                    # Page d'accueil
└── pages/
    ├── 1_Calendrier_Trading.py    # Calendrier événements
    ├── 2_Planificateur_V2.py      # Planificateur V2 (legacy)
    ├── 3_Planificateur_V3.py      # Planificateur V3.0 (650 lignes) ⭐
    ├── 3_API_Status.py            # Statut API
    └── 4_Mise_a_jour_DB.py        # Mise à jour DB
```

**Responsabilités :**
- Interface utilisateur (Streamlit)
- Validation entrées utilisateur
- Affichage résultats formatés
- Export CSV
- Graphiques Plotly

**Technologies :**
- Streamlit (framework UI)
- Plotly (visualisations)
- Pandas (manipulation données)

---

## 3. COUCHE SERVICES

### DataService

**Localisation :** `src/services/data_service.py` (650 lignes)

**Responsabilités :**
- Interface unique accès DB
- Gestion connexions DuckDB
- Prévention erreurs récurrentes
- Context managers (connexions propres)

**Méthodes principales :**
```python
get_events(date, filters)          # Récupération événements
get_event_families()                # Statistiques familles
get_prices(start, end)              # Prix 1-minute
get_db_stats()                      # Diagnostics DB
```

**Erreurs prévenues :**
- ❌ `event_name` → ✅ `event_title`
- ❌ `forecast` NULL → ✅ Fallback estimate/previous
- ❌ JOIN sans country → ✅ JOIN avec country

---

### PredictionService

**Localisation :** `src/services/prediction_service.py` (630 lignes)

**Responsabilités :**
- Prédiction impacts (somme vectorielle)
- Validation prédictions
- Gestion multi-événements

**Note :** ⚠️ À refactoriser pour utiliser `cluster_impact_calculator.py`

---

### ScoringService

**Localisation :** `src/services/scoring_service.py` (650 lignes)

**Responsabilités :**
- Calcul scores composite 0-100
- Pondérations validées (40/30/20/10)
- Scores tradabilité

---

## 4. COUCHE CORE (MÉTIER)

### FormulasValidated

**Localisation :** `src/core/formulas_validated.py`

**Formules validées :**
- `calculate_impact_d()` : Formule D (98.6% précision)
- `calculate_adjusted_empirical_score()` : Ajustement surprise (99.9%)
- `calculate_ttr_c()` : Time To Reversal (94.4%)
- `calculate_pullback_v2()` : Pullback (99.3%)

**Statut :** ✅ Production-ready (NE PAS modifier)

---

### ClusterImpactCalculator

**Localisation :** `src/core/cluster_impact_calculator.py`

**Fonctions :**
- `calculate_cluster_impact()` : Impact cluster isolé (MAE 0.07 pips)
- `calculate_cluster_ttr()` : TTR adaptatif
- `calculate_pullback_characteristics()` : Caractéristiques pullback
- `calculate_double_wave_overlapping()` : Impact total Double Wave (MAE 0.29 pips) ⭐

**Statut :** ✅ Production-ready (5/5 fonctions validées)

---

### DoubleWavePrediction

**Localisation :** `src/core/doublewave_prediction.py`

**Fonctions :**
- `predict_doublewave_overlap()` : Prédiction Double Wave
- Critères inclusion/exclusion automatiques
- Amplifications fixes : 0.1201 (standard) / 0.0128 (superposition)

**Statut :** ✅ Production-ready (Session 132)

---

### PatternDetector

**Localisation :** `scripts/session120/double_wave_detector_rev12.py`

**Fonctions :**
- `detect_double_wave()` : Détection Double Wave (MAE 4.5 pips)
- `detect_single_wave()` : Détection Single Wave
- Classification automatique (6 patterns)

**Statut :** ✅ Production-ready (Session 120)

---

## 5. COUCHE DONNÉES

### warehouse.duckdb

**Localisation :** `data/warehouse.duckdb` (205 MB)

**Tables principales :**

#### **events**
```sql
CREATE TABLE events (
    ts_utc               TIMESTAMP WITH TIME ZONE,
    country              VARCHAR,
    event_title          VARCHAR,  -- ⚠️ PAS "event_name" !
    event_key            VARCHAR,
    importance_n         BIGINT,   -- ⚠️ NUMÉRIQUE : 1=LOW, 2=MED, 3=HIGH
    actual               DOUBLE,
    previous             DOUBLE,
    estimate             DOUBLE,
    forecast             DOUBLE,
    ...
)
```

**Distribution :**
- importance_n = 1 (LOW) : 2,985 événements (7.6%)
- importance_n = 2 (MED) : 28,545 événements (72.8%)
- importance_n = 3 (HIGH) : 7,889 événements (20.1%) ← FOCUS TRADING

#### **event_families**
```sql
CREATE TABLE event_families (
    family               VARCHAR,
    country              VARCHAR,
    event_key            VARCHAR,
    empirical_score      DOUBLE,   -- Score 0-100
    avg_movement_pips    DOUBLE,
    mfe_p80             DOUBLE,
    latency_median      DOUBLE,
    ttr_median          DOUBLE,
    n_events            BIGINT
)
```

**Statistiques :**
- 2,467 scores empiriques
- 100% événements US HIGH couverts

#### **prices_bern**
```sql
CREATE TABLE prices_bern AS
SELECT 
    datetime AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Zurich' as datetime,
    open, high, low, close
FROM prices_1m
```

**⚠️ TIMEZONE CRITIQUE :**
- `prices_bern.datetime` = Europe/Zurich (UTC+01:00 hiver / UTC+02:00 été)
- `events.ts_utc` = UTC (TIMESTAMP WITH TIME ZONE)
- **Conversion nécessaire** lors des jointures !

**Statistiques :**
- 1,114,260 bougies 1-minute
- Période : 2023-01-01 → 2025-11-05

---

## 6. FLUX DE DONNÉES

### Flux : Prédiction Impact (Planificateur V3.0)

```
1. UTILISATEUR
   └─> Saisit date + timezone + min_pips
       │
       ▼
2. PLANIFICATEUR V3.0
   └─> Valide entrée (parse_flexible_date)
       │
       ▼
3. DATASERVICE
   └─> Charge events HIGH (get_events)
   └─> Charge prix 1-minute (get_prices)
       │
       ▼
4. PLANIFICATEUR V3.0
   └─> Enrichit events avec scores (get_scores)
       │
       ▼
5. PATTERNDETECTOR
   └─> Détecte pattern (detect_double_wave / detect_single_wave)
       │
       ▼
6. ROUTING SELON PATTERN
   ├─> DOUBLE_WAVE → DoubleWavePrediction.predict_overlap()
   ├─> SINGLE_WAVE → FormulasValidated.calculate_impact_d()
   └─> INCONNU → Message explicatif
       │
       ▼
7. CLUSTERIMPACTCALCULATOR
   └─> Calcule impact (calculate_cluster_impact / calculate_double_wave_overlapping)
       │
       ▼
8. PLANIFICATEUR V3.0
   └─> Affiche résultats (display_results)
   └─> Export CSV (optionnel)
       │
       ▼
9. UTILISATEUR
   └─> Reçoit prédiction + métriques + graphiques
```

### Flux : Pipeline LOO-CV (Session 139)

```
1. SCANNER MOUVEMENTS
   └─> Détecte mouvements ≥40 pips (2023-2025)
       │
       ▼
2. ENRICHISSEMENT ÉVÉNEMENTS
   └─> Match événements ±60 min
   └─> Calcule scores manquants (295 scores)
       │
       ▼
3. CLASSIFICATION PATTERNS
   └─> Classifie 6 patterns direction-aware
       │
       ▼
4. GROUPING PATTERNS
   └─> Groupe par (pattern_type, score_range)
       │
       ▼
5. VALIDATION LOO-CV
   └─> Leave-One-Out Cross-Validation (396 prédictions)
   └─> Calcule MAE par groupe
       │
       ▼
6. CLASSIFICATION QUALITÉ
   └─> EXCELLENT (<20 pips) / ACCEPTABLE (20-30) / À_OPTIMISER (>30)
```

---

## 7. TECHNOLOGIES UTILISÉES

### Backend

- **Python 3.9+** : Langage principal
- **DuckDB** : Base de données analytique (205 MB)
- **Pandas** : Manipulation données
- **NumPy** : Calculs numériques
- **scikit-learn** : Régression linéaire (R² tendance)

### Frontend

- **Streamlit** : Framework UI
- **Plotly** : Graphiques interactifs
- **Pandas** : Affichage tableaux

### Tests

- **pytest** : Framework tests
- **Coverage** : 65-118% selon modules

### Documentation

- **Markdown** : Documentation projet
- **Mermaid** : Diagrammes (optionnel)
- **Docstrings** : Documentation inline

---

## 🔗 RÉFÉRENCES

- **Architecture complète :** `MASTER_PLAN.md`
- **Modules détaillés :** `MODULES_STATUS.md`
- **Structure DB :** `DB_STRUCTURE.md`

---

**Document créé :** 16 novembre 2025  
**Auteur :** André Valentin avec Claude  
**Version :** 1.0  
**Statut :** Diagramme architecture complet

