# PROPOSITION RÉORGANISATION - SESSION_VALIDATION_ACTUELLE

**Date :** 2025-12-06  
**Statut :** ⏳ EN ATTENTE VALIDATION  
**⚠️ AUCUNE MODIFICATION EFFECTUÉE - PROPOSITION UNIQUEMENT**

---

## ✅ RECALCUL TERMINÉ

**Résultats du recalcul complet (2020-2025) :**
- ✅ 1237 scores calculés
- ✅ Score moyen : 33.20
- ✅ Score médian : 33.14
- ✅ Score min : 5.02, Score max : 85.45
- ✅ Backup créé : `event_families_backup`
- ✅ Scores mis à jour dans `event_families`

---

## 📊 ANALYSE STRUCTURE ACTUELLE

### Fichiers Présents ✅

**Core Modules (dans `src_core/`) :**
- ✅ `formulas_validated.py`
- ✅ `event_loader.py`
- ✅ `price_loader_finnhub.py`
- ✅ `trend_detection_pre_event_s107.py`
- ✅ `random_forest_amplification.py`
- ✅ `double_wave.py`
- ✅ `single_wave_strong.py`
- ✅ `r2_amplification_correlation.py`

**Pipeline :**
- ✅ `scripts/run_pipeline_complete.py`

**Scripts Recalcul :**
- ✅ `scripts/recalculate_empirical_scores_finnhub.py`
- ✅ `scripts/recalculate_empirical_scores_finnhub_p80_only.py`
- ✅ `scripts/compare_empirical_scores.py`

**Documentation :**
- ✅ `docs/REF-001` à `REF-005`
- ✅ `docs/INDEX_REFERENCES.md`
- ✅ `docs/VALIDATION_SESSION_2025_01_XX/`
- ✅ `docs/PIPELINE_REFERENCE/`

**Outputs :**
- ✅ `outputs/impacts_reels_mesures.csv`
- ✅ `outputs/comparison_formula_vs_p80_optimized.csv`
- ✅ `outputs/recalcul_complet_2020_2025.log`

---

## ⚠️ FICHIERS MANQUANTS IDENTIFIÉS

### 1. Fichiers depuis `src/core/` (racine projet)

**Manquants dans SESSION_VALIDATION_ACTUELLE :**
- ❌ `src/core/finnhub_patterns.py` ⚠️ **IMPORTANT**
- ❌ `src/core/amplification_random_forest.py` (différent de `random_forest_amplification.py` ?)
- ❌ `src/config.py` ⭐ **CRITIQUE** (DB_PATH, configuration)

**À vérifier :**
- ❓ `src/core/cluster_impact_calculator.py`
- ❓ `src/core/impact_measurement.py`
- ❓ `src/core/event_families.py`

### 2. Fichiers depuis `scripts/` (racine projet)

**Manquants :**
- ❌ `scripts/session120/double_wave_detector_rev12.py` ⚠️ **IMPORTANT**
  - Utilisé par `run_pipeline_complete.py` dans Étape 8.6

### 3. Fichiers Potentiellement Obsolètes

**À supprimer si confirmé :**
- ⚠️ `cursor_lire_les_fichiers_et_aider_au_d.md`
- ⚠️ `cursor_lire_les_fichiers_et_aider_V2.md`

**Doublons à fusionner :**
- ⚠️ `src_core/` vs `references/20251203_114640/src/core/` (versions différentes)

---

## 🎯 PROPOSITION RÉORGANISATION

### Structure Proposée

```
SESSION_VALIDATION_ACTUELLE/
│
├── 📄 README.md                          # Guide principal
├── 📄 INDEX_FICHIERS.md                  # Index complet
├── 📄 RESUME_SESSION.md                  # Résumé session
├── 📄 GUIDE_DEVELOPPEMENT.md             # Guide développement
│
├── 📁 core/                              # ⭐ NOUVEAU : Modules core unifiés
│   ├── __init__.py
│   ├── config.py                        # ⚠️ À AJOUTER depuis src/config.py
│   ├── formulas_validated.py
│   ├── event_loader.py
│   ├── price_loader_finnhub.py
│   ├── trend_detection_pre_event_s107.py
│   ├── random_forest_amplification.py
│   ├── double_wave.py
│   ├── single_wave_strong.py
│   ├── r2_amplification_correlation.py
│   ├── finnhub_patterns.py              # ⚠️ À AJOUTER depuis src/core/
│   ├── cluster_impact_calculator.py     # ⚠️ À VÉRIFIER si utilisé
│   ├── impact_measurement.py            # ⚠️ À VÉRIFIER si utilisé
│   └── event_families.py                # ⚠️ À VÉRIFIER si utilisé
│
├── 📁 pipeline/                          # ⭐ NOUVEAU : Pipeline et scripts principaux
│   ├── run_pipeline_complete.py
│   ├── double_wave_detector_rev12.py    # ⚠️ À AJOUTER depuis scripts/session120/
│   └── README.md
│
├── 📁 scripts/                           # Scripts utilitaires
│   ├── recalcul/                         # ⭐ NOUVEAU
│   │   ├── recalculate_empirical_scores_finnhub.py
│   │   ├── recalculate_empirical_scores_finnhub_p80_only.py
│   │   └── compare_empirical_scores.py
│   │
│   ├── tests/                            # ⭐ NOUVEAU
│   │   ├── test_*.py
│   │   └── validate_*.py
│   │
│   ├── analysis/                         # ⭐ NOUVEAU
│   │   ├── analyze_*.py
│   │   └── investigate_*.py
│   │
│   └── utils/                            # ⭐ NOUVEAU
│       └── explain_formula_vs_p80.py
│
├── 📁 docs/                              # Documentation
│   ├── references/                      # ⭐ NOUVEAU : Références numérotées
│   │   ├── REF-001_*.md
│   │   ├── REF-002_*.md
│   │   ├── REF-003_*.md
│   │   ├── REF-004_*.md
│   │   ├── REF-005_*.md
│   │   └── INDEX_REFERENCES.md
│   │
│   ├── validation/                       # ⭐ NOUVEAU
│   │   └── VALIDATION_SESSION_2025_01_XX/
│   │
│   ├── pipeline/                         # ⭐ NOUVEAU
│   │   └── PIPELINE_REFERENCE/
│   │
│   └── methodology/                      # ⭐ NOUVEAU
│       └── METHODOLOGIE_TRAVAIL.md
│
├── 📁 outputs/                           # Résultats et logs
│   ├── data/                             # ⭐ NOUVEAU : Données critiques
│   │   ├── impacts_reels_mesures.csv
│   │   └── comparison_formula_vs_p80_optimized.csv
│   │
│   ├── logs/                             # ⭐ NOUVEAU : Logs
│   │   └── recalcul_complet_2020_2025.log
│   │
│   └── tests/                            # ⭐ NOUVEAU : Résultats tests
│       └── *.csv (autres CSV de tests)
│
├── 📁 streamlit_app/                     # Application Streamlit
│   ├── Home.py
│   └── pages/
│       └── 5_Planificateur_V3.1_CLEAN_OLD.py
│
└── 📁 backups/                           # ⭐ NOUVEAU : Backups organisés
    └── 20251203_114640/                  # Backup pipeline
        └── ...
```

---

## 📋 ACTIONS PROPOSÉES

### Phase 1 : Ajout Fichiers Manquants

1. **Copier `src/config.py` → `core/config.py`** ⭐ CRITIQUE
2. **Copier `src/core/finnhub_patterns.py` → `core/finnhub_patterns.py`**
3. **Copier `scripts/session120/double_wave_detector_rev12.py` → `pipeline/double_wave_detector_rev12.py`**
4. **Vérifier et copier si nécessaire :**
   - `src/core/cluster_impact_calculator.py`
   - `src/core/impact_measurement.py`
   - `src/core/event_families.py`

### Phase 2 : Réorganisation

1. **Renommer `src_core/` → `core/`** (fusionner avec nouveaux fichiers)
2. **Créer sous-répertoires dans `scripts/` :**
   - `scripts/recalcul/`
   - `scripts/tests/`
   - `scripts/analysis/`
   - `scripts/utils/`
3. **Déplacer scripts dans sous-répertoires appropriés**
4. **Créer sous-répertoires dans `docs/` :**
   - `docs/references/`
   - `docs/validation/`
   - `docs/pipeline/`
   - `docs/methodology/`
5. **Déplacer documentation dans sous-répertoires appropriés**
6. **Créer sous-répertoires dans `outputs/` :**
   - `outputs/data/`
   - `outputs/logs/`
   - `outputs/tests/`
7. **Déplacer outputs dans sous-répertoires appropriés**
8. **Renommer `references/` → `backups/`**

### Phase 3 : Nettoyage

1. **Supprimer fichiers obsolètes :**
   - `cursor_lire_les_fichiers_et_aider_au_d.md`
   - `cursor_lire_les_fichiers_et_aider_V2.md`
2. **Mettre à jour imports dans scripts** (après réorganisation)

---

## ⚠️ AVANT DE PROCÉDER

### Vérifications Requises

1. ✅ **Vérifier que tous les fichiers critiques sont identifiés**
2. ⏳ **Valider la structure proposée**
3. ⏳ **Confirmer fichiers à supprimer**
4. ⏳ **Confirmer fichiers à ajouter**

### Questions à Résoudre

1. **`src_core/` vs `references/20251203_114640/src/core/` :**
   - Versions différentes détectées
   - Quelle version utiliser ? (actuelle dans `src_core/` ou backup dans `references/`)

2. **`streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py` :**
   - Version "OLD" - est-ce la bonne version à conserver ?
   - Ou faut-il utiliser une version depuis `streamlit_app/pages/` (racine projet) ?

3. **Fichiers `cursor_*.md` :**
   - À supprimer ou à conserver comme documentation ?

---

## ✅ VALIDATION REQUISE

**⚠️ AUCUNE MODIFICATION NE SERA EFFECTUÉE SANS VOTRE VALIDATION**

**Merci de confirmer :**
1. ✅ Structure proposée acceptable ?
2. ✅ Fichiers à ajouter corrects ?
3. ✅ Fichiers à supprimer corrects ?
4. ✅ Questions à résoudre avant de procéder ?

---

**Prochaine étape :** Attendre votre validation avant d'appliquer les modifications




