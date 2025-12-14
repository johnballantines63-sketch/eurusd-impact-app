# ANALYSE STRUCTURE COMPLÈTE - Fichiers Nécessaires

**Date :** 2025-12-06  
**Objectif :** Identifier tous les fichiers nécessaires pour le bon fonctionnement de l'application

---

## 📊 FICHIERS PRÉSENTS DANS SESSION_VALIDATION_ACTUELLE

### Core Modules (`src_core/`)

**Fichiers présents :**
- ✅ `formulas_validated.py`
- ✅ `event_loader.py`
- ✅ `price_loader_finnhub.py`
- ✅ `trend_detection_pre_event_s107.py`
- ✅ `random_forest_amplification.py`
- ✅ `double_wave.py`
- ✅ `single_wave_strong.py`
- ✅ `r2_amplification_correlation.py`

**Fichiers manquants (à ajouter) :**
- ❌ `config.py` ⭐ **CRITIQUE** (DB_PATH, configuration)
- ❌ `finnhub_patterns.py` ⚠️ **IMPORTANT** (utilisé dans planificateur)

**Fichiers à vérifier (peuvent être nécessaires) :**
- ❓ `cluster_impact_calculator.py`
- ❓ `impact_measurement.py`
- ❓ `event_families.py`
- ❓ `amplification_random_forest.py` (nom différent de `random_forest_amplification.py` ?)

### Pipeline

**Fichiers présents :**
- ✅ `scripts/run_pipeline_complete.py`

**Fichiers manquants :**
- ❌ `pipeline/double_wave_detector_rev12.py` ⚠️ **IMPORTANT**
  - Utilisé dans Étape 8.6 pour détection patterns depuis prix
  - Localisation : `scripts/session120/double_wave_detector_rev12.py`

### Streamlit App

**Fichiers présents :**
- ✅ `streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py` (4900 lignes)
- ✅ `streamlit_app/Home.py`

**Fichiers à vérifier :**
- ❓ `streamlit_app/pages/1_Calendrier_Trading.py` (fonctionnalité 1, 7)
- ❓ Autres pages Streamlit si utilisées

### Scripts Utilitaires

**Fichiers présents :**
- ✅ `scripts/recalculate_empirical_scores_finnhub.py`
- ✅ `scripts/recalculate_empirical_scores_finnhub_p80_only.py`
- ✅ `scripts/compare_empirical_scores.py`

**Fichiers à créer :**
- ⚠️ `scripts/recalcul/recalculate_core_scores_historical.py` (question utilisateur)

---

## 📋 FICHIERS DEPUIS RACINE PROJET À AJOUTER

### Depuis `src/core/`

1. **`src/config.py`** ⭐ **CRITIQUE**
   - DB_PATH, configuration
   - Utilisé par tous les scripts

2. **`src/core/finnhub_patterns.py`** ⚠️ **IMPORTANT**
   - Patterns Finnhub
   - Utilisé dans planificateur (ligne 76-79)

3. **`src/core/cluster_impact_calculator.py`** ❓ **À VÉRIFIER**
   - Calcul impact cluster
   - Peut être utilisé dans pipeline

4. **`src/core/impact_measurement.py`** ❓ **À VÉRIFIER**
   - Mesure impact
   - Peut être utilisé dans pipeline

5. **`src/core/event_families.py`** ❓ **À VÉRIFIER**
   - Gestion familles événements
   - Peut être utilisé dans pipeline

### Depuis `scripts/`

1. **`scripts/session120/double_wave_detector_rev12.py`** ⚠️ **IMPORTANT**
   - Détection patterns depuis prix
   - Utilisé dans Étape 8.6 du pipeline

### Depuis `streamlit_app/pages/`

1. **`streamlit_app/pages/1_Calendrier_Trading.py`** ❓ **À VÉRIFIER**
   - Calendrier trading
   - Peut contenir fonctionnalités utiles

---

## 🎯 STRUCTURE FINALE PROPOSÉE

```
SESSION_VALIDATION_ACTUELLE/
│
├── 📁 core/                              # Modules core unifiés
│   ├── __init__.py
│   ├── config.py                        # ⚠️ À AJOUTER (src/config.py)
│   ├── formulas_validated.py
│   ├── event_loader.py
│   ├── price_loader_finnhub.py
│   ├── trend_detection_pre_event_s107.py
│   ├── random_forest_amplification.py
│   ├── double_wave.py
│   ├── single_wave_strong.py
│   ├── r2_amplification_correlation.py
│   ├── finnhub_patterns.py             # ⚠️ À AJOUTER (src/core/finnhub_patterns.py)
│   ├── cluster_impact_calculator.py    # ⚠️ À VÉRIFIER
│   ├── impact_measurement.py            # ⚠️ À VÉRIFIER
│   └── event_families.py                # ⚠️ À VÉRIFIER
│
├── 📁 pipeline/                          # Pipeline et scripts principaux
│   ├── run_pipeline_complete.py
│   ├── double_wave_detector_rev12.py    # ⚠️ À AJOUTER (scripts/session120/)
│   └── README.md
│
├── 📁 scripts/                           # Scripts utilitaires
│   ├── recalcul/                         # Scripts recalcul
│   │   ├── recalculate_empirical_scores_finnhub.py
│   │   ├── recalculate_empirical_scores_finnhub_p80_only.py
│   │   ├── compare_empirical_scores.py
│   │   └── recalculate_core_scores_historical.py  # ⚠️ À CRÉER
│   │
│   ├── tests/                            # Scripts de test
│   │   └── test_*.py
│   │
│   ├── analysis/                         # Scripts d'analyse
│   │   └── analyze_*.py, investigate_*.py
│   │
│   └── utils/                            # Utilitaires
│       └── explain_formula_vs_p80.py
│
├── 📁 docs/                              # Documentation
│   ├── references/                      # Références numérotées
│   ├── validation/                       # Documentation validation
│   ├── pipeline/                         # Documentation pipeline
│   └── methodology/                      # Méthodologie
│
├── 📁 outputs/                           # Résultats et logs
│   ├── data/                             # Données critiques
│   ├── logs/                             # Logs
│   └── tests/                            # Résultats tests
│
├── 📁 streamlit_app/                     # Application Streamlit
│   ├── Home.py
│   └── pages/
│       └── 5_Planificateur_V3.1_CLEAN_OLD.py
│
└── 📁 backups/                           # Backups organisés
    └── 20251203_114640/
```

---

## 📋 CHECKLIST FICHIERS À AJOUTER

### Critiques (Nécessaires au fonctionnement)

- [ ] `core/config.py` ⭐ **CRITIQUE**
- [ ] `core/finnhub_patterns.py` ⚠️ **IMPORTANT**
- [ ] `pipeline/double_wave_detector_rev12.py` ⚠️ **IMPORTANT**

### À Vérifier (Peuvent être nécessaires)

- [ ] `core/cluster_impact_calculator.py`
- [ ] `core/impact_measurement.py`
- [ ] `core/event_families.py`
- [ ] `streamlit_app/pages/1_Calendrier_Trading.py`

### À Créer

- [ ] `scripts/recalcul/recalculate_core_scores_historical.py` ⚠️ **QUESTION UTILISATEUR**

---

## ✅ PROCHAINES ÉTAPES

1. ✅ Analyser structure complète
2. ⏳ Créer script `recalculate_core_scores_historical.py`
3. ⏳ Tester script
4. ⏳ Ajouter fichiers manquants critiques
5. ⏳ Réorganiser structure

---

**En cours : Création script recalculate_core_scores_historical.py...**




