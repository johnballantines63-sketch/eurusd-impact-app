# ANALYSE STRUCTURE FICHIERS - Proposition Réorganisation

**Date :** 2025-12-06  
**Objectif :** Analyser la structure actuelle et proposer une réorganisation AVANT modifications

---

## 📊 ÉTAT ACTUEL SESSION_VALIDATION_ACTUELLE

### Structure Actuelle

```
SESSION_VALIDATION_ACTUELLE/
├── README.md
├── INDEX_FICHIERS.md
├── RESUME_SESSION.md
├── GUIDE_DEVELOPPEMENT.md
├── cursor_lire_les_fichiers_et_aider_au_d.md
├── cursor_lire_les_fichiers_et_aider_V2.md
│
├── docs/ (147 fichiers : 143 *.md, 4 *.log)
│   ├── REF-001 à REF-005 (références numérotées)
│   ├── VALIDATION_SESSION_2025_01_XX/ (documentation session)
│   └── PIPELINE_REFERENCE/ (référence pipeline)
│
├── scripts/ (77 fichiers : 76 *.py, 1 *.sh)
│   ├── run_pipeline_complete.py ⭐ CRITIQUE
│   ├── test_*.py (multiples scripts de test)
│   ├── analyze_*.py (scripts d'analyse)
│   ├── investigate_*.py (scripts d'investigation)
│   └── recalculate_empirical_scores_finnhub.py ⭐ CRITIQUE
│
├── outputs/ (25 fichiers CSV/LOG)
│   ├── impacts_reels_mesures.csv ⭐ CRITIQUE
│   ├── comparison_formula_vs_p80_optimized.csv
│   ├── recalcul_complet_2020_2025.log
│   └── ... (autres CSV de tests)
│
├── src_core/ (8 fichiers *.py)
│   ├── formulas_validated.py ⭐ CRITIQUE
│   ├── event_loader.py
│   ├── price_loader_finnhub.py
│   └── ... (copies de src/core/)
│
├── streamlit_app/ (2 fichiers)
│   ├── 5_Planificateur_V3.1_CLEAN_OLD.py
│   └── Home.py
│
└── references/ (backup 20251203_114640)
    └── scripts/ et src/core/ (backup pipeline)
```

---

## 🔍 FICHIERS CRITIQUES IDENTIFIÉS

### 1. Pipeline & Core Logic

**Fichiers essentiels au fonctionnement :**
- ✅ `scripts/run_pipeline_complete.py` - Pipeline complet (8 étapes)
- ✅ `src_core/formulas_validated.py` - Formules validées
- ✅ `src_core/event_loader.py` - Chargement événements
- ✅ `src_core/price_loader_finnhub.py` - Chargement prix
- ✅ `src_core/trend_detection_pre_event_s107.py` - Détection tendance
- ✅ `src_core/random_forest_amplification.py` - RF amplification
- ✅ `src_core/double_wave.py` - Prédiction Double Wave
- ✅ `src_core/single_wave_strong.py` - Prédiction Single Wave

**Statut :** ✅ Présents dans SESSION_VALIDATION_ACTUELLE

### 2. Scripts de Recalcul

**Fichiers essentiels :**
- ✅ `scripts/recalculate_empirical_scores_finnhub.py` - Recalcul scores (formule actuelle)
- ✅ `scripts/recalculate_empirical_scores_finnhub_p80_only.py` - Recalcul scores (P80 uniquement)
- ✅ `scripts/compare_empirical_scores.py` - Comparaison scores

**Statut :** ✅ Présents dans SESSION_VALIDATION_ACTUELLE

### 3. Documentation Référence

**Fichiers essentiels :**
- ✅ `docs/REF-001_DEFINITIONS_ET_REGLES_TESTS.md` - Définitions et règles
- ✅ `docs/REF-002_VERIFICATION_SCORES_EMPIRIQUES_FINNHUB.md` - Vérification scores
- ✅ `docs/REF-003_SCRIPT_RECALCUL_SCORES_FINNHUB.md` - Script recalcul
- ✅ `docs/REF-004_COMPARAISON_SCORES_EMPIRIQUES.md` - Comparaison scores
- ✅ `docs/REF-005_ANALYSE_FONDEMENTS_MATHEMATIQUES_SCORES.md` - Analyse mathématique
- ✅ `docs/INDEX_REFERENCES.md` - Index des références

**Statut :** ✅ Présents dans SESSION_VALIDATION_ACTUELLE

### 4. Outputs Critiques

**Fichiers essentiels :**
- ✅ `outputs/impacts_reels_mesures.csv` - Impacts réels mesurés
- ✅ `outputs/comparison_formula_vs_p80_optimized.csv` - Comparaison formules
- ✅ `outputs/recalcul_complet_2020_2025.log` - Log recalcul

**Statut :** ✅ Présents dans SESSION_VALIDATION_ACTUELLE

### 5. Application Streamlit

**Fichiers essentiels :**
- ⚠️ `streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py` - Planificateur (version OLD)
- ⚠️ `streamlit_app/Home.py` - Page d'accueil

**Statut :** ⚠️ Présents mais version "OLD" (à vérifier si c'est la bonne version)

---

## 📋 FICHIERS MANQUANTS (À VÉRIFIER)

### 1. Fichiers depuis `src/core/` (racine projet)

**À vérifier si présents dans SESSION_VALIDATION_ACTUELLE :**
- ❓ `src/core/finnhub_patterns.py` - Patterns Finnhub
- ❓ `src/core/r2_amplification_correlation.py` - Corrélation R²
- ❓ `src/core/amplification_random_forest.py` - RF amplification (nom différent ?)

**Statut :** ⚠️ À vérifier (peut-être dans `src_core/` avec nom différent)

### 2. Fichiers depuis `scripts/` (racine projet)

**À vérifier si présents :**
- ❓ `scripts/session120/double_wave_detector_rev12.py` - Détecteur Double Wave
- ❓ Autres scripts session120 si utilisés

**Statut :** ⚠️ À vérifier (peut-être dans `references/` ou `scripts/`)

### 3. Configuration

**À vérifier :**
- ❓ `src/config.py` - Configuration (DB_PATH, etc.)

**Statut :** ⚠️ À vérifier (utilisé par scripts mais peut-être pas copié)

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
│   ├── formulas_validated.py            # Formules validées
│   ├── event_loader.py                  # Chargement événements
│   ├── price_loader_finnhub.py          # Chargement prix
│   ├── trend_detection_pre_event_s107.py
│   ├── random_forest_amplification.py
│   ├── double_wave.py
│   ├── single_wave_strong.py
│   ├── finnhub_patterns.py              # ⚠️ À ajouter si manquant
│   ├── r2_amplification_correlation.py  # ⚠️ À ajouter si manquant
│   └── config.py                        # ⚠️ À ajouter (DB_PATH, etc.)
│
├── 📁 pipeline/                          # ⭐ NOUVEAU : Pipeline et scripts principaux
│   ├── run_pipeline_complete.py         # Pipeline complet
│   ├── double_wave_detector_rev12.py    # ⚠️ À ajouter si manquant
│   └── README.md                         # Documentation pipeline
│
├── 📁 scripts/                           # Scripts utilitaires
│   ├── recalcul/                         # ⭐ NOUVEAU : Scripts recalcul
│   │   ├── recalculate_empirical_scores_finnhub.py
│   │   ├── recalculate_empirical_scores_finnhub_p80_only.py
│   │   └── compare_empirical_scores.py
│   │
│   ├── tests/                            # ⭐ NOUVEAU : Scripts de test
│   │   ├── test_*.py
│   │   └── validate_*.py
│   │
│   ├── analysis/                         # ⭐ NOUVEAU : Scripts d'analyse
│   │   ├── analyze_*.py
│   │   └── investigate_*.py
│   │
│   └── utils/                            # ⭐ NOUVEAU : Utilitaires
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
│   ├── validation/                       # ⭐ NOUVEAU : Documentation validation
│   │   └── VALIDATION_SESSION_2025_01_XX/
│   │
│   ├── pipeline/                         # ⭐ NOUVEAU : Documentation pipeline
│   │   └── PIPELINE_REFERENCE/
│   │
│   └── methodology/                      # ⭐ NOUVEAU : Méthodologie
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

## ✅ AVANTAGES PROPOSITION

1. **Séparation claire** : core / pipeline / scripts / docs / outputs
2. **Organisation logique** : scripts groupés par fonction (recalcul, tests, analysis)
3. **Documentation structurée** : docs organisés par type (references, validation, pipeline)
4. **Outputs organisés** : séparation data / logs / tests
5. **Core unifié** : tous les modules core dans un seul répertoire

---

## ⚠️ FICHIERS À VÉRIFIER/SUPPRIMER

### Fichiers potentiellement obsolètes

1. **`cursor_lire_les_fichiers_et_aider_au_d.md`** - ⚠️ À supprimer si obsolète
2. **`cursor_lire_les_fichiers_et_aider_V2.md`** - ⚠️ À supprimer si obsolète
3. **`src_core/`** - ⚠️ À fusionner dans `core/` si doublon
4. **`references/`** - ⚠️ À déplacer dans `backups/` si c'est un backup

### Fichiers à vérifier présence

1. **`src/core/finnhub_patterns.py`** - ⚠️ À vérifier si présent
2. **`src/core/r2_amplification_correlation.py`** - ⚠️ À vérifier si présent
3. **`src/config.py`** - ⚠️ À vérifier si présent (critique pour DB_PATH)
4. **`scripts/session120/double_wave_detector_rev12.py`** - ⚠️ À vérifier si présent

---

## 📋 PLAN D'ACTION PROPOSÉ

### Phase 1 : Vérification (AVANT modifications)

1. ✅ Vérifier présence fichiers critiques depuis `src/core/`
2. ✅ Vérifier présence fichiers critiques depuis `scripts/`
3. ✅ Identifier doublons (`src_core/` vs `core/`)
4. ✅ Identifier fichiers obsolètes

### Phase 2 : Proposition détaillée

1. ✅ Créer liste complète fichiers à déplacer
2. ✅ Créer liste complète fichiers à supprimer
3. ✅ Créer liste complète fichiers à ajouter (depuis racine projet)

### Phase 3 : Validation

1. ⏳ Attendre validation utilisateur
2. ⏳ Appliquer modifications si validé

---

## 🔗 FICHIERS DEPUIS RACINE PROJET À VÉRIFIER

### Depuis `src/core/`

- `src/core/finnhub_patterns.py`
- `src/core/r2_amplification_correlation.py`
- `src/core/amplification_random_forest.py` (ou nom similaire)
- `src/config.py` ⭐ CRITIQUE

### Depuis `scripts/`

- `scripts/session120/double_wave_detector_rev12.py`
- Autres scripts session120 si utilisés

### Depuis `streamlit_app/`

- `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py` (vérifier si c'est la bonne version)
- Autres pages Streamlit si utilisées

---

**Prochaine étape :** Vérifier présence fichiers manquants et créer liste détaillée AVANT modifications




