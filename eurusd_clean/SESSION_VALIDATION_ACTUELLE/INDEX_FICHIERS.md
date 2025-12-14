# Index Complet des Fichiers - Session Validation Actuelle

**Date de création** : 2025-01-XX  
**Objectif** : Index exhaustif de tous les fichiers utilisés dans cette session

---

## 📋 STRUCTURE DU RÉPERTOIRE

```
SESSION_VALIDATION_ACTUELLE/
├── README.md
├── INDEX_FICHIERS.md (ce fichier)
├── scripts/
│   ├── run_pipeline_complete.py
│   ├── validate_pipeline_multi_dates.py
│   ├── measure_real_impacts_all_dates.py
│   └── ...
├── docs/
│   ├── VALIDATION_SESSION_2025_01_XX/
│   └── PIPELINE_REFERENCE/
├── streamlit_app/
│   └── 5_Planificateur_V3.1_CLEAN_OLD.py
├── outputs/
│   └── impacts_reels_mesures.csv
├── src_core/
│   └── ...
└── references/
    └── ...
```

---

## 🔍 FICHIERS PAR CATÉGORIE

### 1. Scripts Principaux

#### Pipeline Complet
- **`scripts/run_pipeline_complete.py`**
  - **Description** : Pipeline complet en 8 étapes
  - **Date modification** : 2025-12-04 01:26
  - **Statut** : ✅ Actif
  - **Utilisation** : Exécution complète du pipeline de prédiction

#### Validation
- **`scripts/validate_pipeline_multi_dates.py`**
  - **Description** : Validation du pipeline sur plusieurs dates
  - **Date modification** : 2025-12-04 01:47
  - **Statut** : ✅ Actif
  - **Utilisation** : Tests de validation multi-dates

- **`scripts/measure_real_impacts_all_dates.py`**
  - **Description** : Mesure des impacts réels depuis Finnhub
  - **Date création** : 2025-01-XX
  - **Statut** : ✅ Nouveau
  - **Utilisation** : Remplacer valeurs incorrectes dans CSV

#### Tests
- **`scripts/test_restauration_cas_base.py`**
  - **Description** : Tests de restauration sur cas de base
  - **Statut** : ✅ Actif

- **`scripts/test_pipeline_cas_base_validation.py`**
  - **Description** : Validation pipeline sur cas de base
  - **Statut** : ✅ Actif

- **`scripts/test_2025_08_01_detailed.py`**
  - **Description** : Test détaillé pour 2025-08-01
  - **Statut** : ✅ Actif

- **`scripts/test_2025_05_29_detailed.py`**
  - **Description** : Test détaillé pour 2025-05-29
  - **Statut** : ✅ Actif

---

### 2. Documentation

#### Session Actuelle
- **`docs/VALIDATION_SESSION_2025_01_XX/`**
  - **Contenu** : Toute la documentation de la session actuelle
  - **Fichiers clés** :
    - `RAPPORT_VALIDATION_MULTI_DATES.md`
    - `ANALYSE_AMPLIFICATION_RANDOM_FOREST.md`
    - `CORRECTION_VALEUR_REELLE_2025_09_11.md`
    - `NOUVEAUX_PATTERNS_NOYAUX_DURS.md`
    - `OPTIMISATION_RECHERCHE_CLUSTERS_IDENTIQUES.md`
    - `INVESTIGATION_PROBLEME_CPI_COMPLETE.md`
    - Etc.

#### Référence Pipeline
- **`docs/PIPELINE_REFERENCE/`**
  - **Contenu** : Documentation de référence du pipeline
  - **Fichiers clés** :
    - `PIPELINE_KNOWLEDGE_BASE.md`
    - `PIPELINE_REFERENCE_COMPLETE.md`
    - `PIPELINE_ARCHITECTURE_DETAILED.md`
    - `PIPELINE_FORMULAS_REFERENCE.md`

#### Méthodologie
- **`docs/METHODOLOGIE_TRAVAIL.md`**
  - **Description** : Méthodologie de travail (Search -> Document -> Propose -> Apply)
  - **Statut** : ✅ Actif

- **`docs/INDEX_DOCUMENTATION_CENTRAL.md`**
  - **Description** : Index central de toute la documentation
  - **Statut** : ✅ Actif

---

### 3. Application Streamlit

- **`streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py`**
  - **Description** : Planificateur Streamlit actuel
  - **Statut** : ✅ Actif
  - **Note** : Version "OLD" mais toujours utilisée

- **`streamlit_app/Home.py`**
  - **Description** : Page d'accueil Streamlit
  - **Statut** : ✅ Actif

---

### 4. Modules Core

- **`src_core/formulas_validated.py`**
  - **Description** : Formules validées (Formule D, Session 88, etc.)
  - **Fonctions clés** :
    - `calculate_impact_d()`
    - `calculate_adjusted_empirical_score()`
    - `calculate_amplification_extended()`
    - `calculate_pullback_v2()`

- **`src_core/random_forest_amplification.py`**
  - **Description** : Random Forest pour prédiction amplification
  - **Fonctions clés** :
    - `train_rf_from_identical_clusters()`
    - `predict_amplification_with_rf()`
    - `extract_features_for_rf()`

- **`src_core/price_loader_finnhub.py`**
  - **Description** : Chargement prix depuis Finnhub
  - **Fonctions clés** :
    - `measure_impact_from_finnhub()`

- **`src_core/trend_detection_pre_event_s107.py`**
  - **Description** : Détection tendance pré-événement
  - **Fonctions clés** :
    - `detect_trend_by_inversion_s107()`

- **`src_core/event_loader.py`**
  - **Description** : Chargement événements
  - **Fonctions clés** :
    - `load_high_impact_events()`

- **`src_core/r2_amplification_correlation.py`**
  - **Description** : Corrélation R² ↔ Amplification
  - **Fonctions clés** :
    - `predict_amplification_from_r2()`

- **`src_core/double_wave.py`**
  - **Description** : Prédiction Double Wave
  - **Fonctions clés** :
    - `predict_double_wave_timeline_s64()`
    - `detect_double_wave_conditions()`

- **`src_core/single_wave_strong.py`**
  - **Description** : Prédiction Single Wave Strong
  - **Fonctions clés** :
    - `predict_single_wave_timeline()`

---

### 5. Outputs

- **`outputs/validation_finale_pipeline.csv`**
  - **Description** : Résultats validation finale (⚠️ certaines valeurs incorrectes)
  - **Statut** : ⚠️ À vérifier

- **`outputs/validation_pipeline_multi_dates.csv`**
  - **Description** : Résultats validation multi-dates
  - **Statut** : ✅ Actif

- **`outputs/impacts_reels_mesures.csv`**
  - **Description** : Impacts réels mesurés fraîchement (nouveau)
  - **Statut** : ✅ Nouveau

- **`outputs/timing_precision_comparison.csv`**
  - **Description** : Comparaison précision timings
  - **Statut** : ✅ Actif

---

### 6. Références

- **`references/20251203_114640/`**
  - **Description** : Backup pipeline du 2025-12-03 11:46:40
  - **Statut** : 📖 Référence
  - **Note** : Version restaurée avec MAE 8.4 pips

---

## ⏰ DISTINCTION PRÉ/POST 11h37

### Pré-11h37 (Avant Corrections Majeures)

**Fichiers** :
- Backups dans `pipeline_backup/20251203_114640/`
- Anciennes versions des scripts
- CSV avec valeurs potentiellement incorrectes

**Caractéristiques** :
- Pipeline restauré depuis backup
- Certaines valeurs CSV incorrectes (ex: 21.7 pips pour 2025-09-11)
- Méthodes moins optimisées

### Post-11h37 (Après Corrections)

**Fichiers** :
- `scripts/run_pipeline_complete.py` (modifié 2025-12-04 01:26)
- `scripts/validate_pipeline_multi_dates.py` (modifié 2025-12-04 01:47)
- Nouveaux patterns noyaux durs (JOBLESS_PCE, GDP, etc.)
- Optimisations recherche clusters identiques
- Corrections détection CPI

**Caractéristiques** :
- Pipeline optimisé
- Nouvelles fonctionnalités
- Documentation exhaustive
- Mesures fraîches des impacts réels

---

## 📊 DATES DE TEST

### Dates Principales

1. **2025-09-11** - CPI (Cas de référence)
2. **2025-08-01** - NFP Single Wave Fort
3. **2025-11-20** - NFP Double Wave
4. **2025-10-10** - Double Wave
5. **2025-06-23** - Double Wave
6. **2025-01-15** - CPI
7. **2025-05-29** - JOBLESS_PCE
8. **2024-09-11** - CPI historique

### Valeurs Réelles Mesurées

Voir `outputs/impacts_reels_mesures.csv` pour les valeurs fraîchement mesurées.

---

## ✅ CHECKLIST VALIDATION

- [x] Répertoire créé
- [x] Fichiers copiés
- [x] Script mesure impacts créé
- [ ] Impacts réels mesurés pour toutes les dates
- [ ] CSV corrigés avec valeurs réelles
- [ ] Documentation exhaustive complétée
- [ ] Index fichiers créé

---

## 🔗 LIENS UTILES

- **Documentation principale** : `docs/VALIDATION_SESSION_2025_01_XX/`
- **Référence pipeline** : `docs/PIPELINE_REFERENCE/`
- **Méthodologie** : `docs/METHODOLOGIE_TRAVAIL.md`

---

**Dernière mise à jour** : 2025-01-XX




