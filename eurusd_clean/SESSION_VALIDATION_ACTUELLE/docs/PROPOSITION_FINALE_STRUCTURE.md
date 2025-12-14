# PROPOSITION FINALE STRUCTURE - Basée sur Besoins Application

**Date :** 2025-12-06  
**Basé sur :** Objectif application et fonctionnalités requises

---

## 🎯 CONTEXTE APPLICATION

**Objectif :** Interface Streamlit pour trader avec prédictions d'impact de clusters d'événements économiques.

**13 Fonctionnalités principales identifiées** (voir `ANALYSE_BESOINS_APPLICATION.md`)

---

## ✅ FICHIERS CRITIQUES IDENTIFIÉS

### 1. Core Modules (Tous nécessaires)

**Présents dans SESSION_VALIDATION_ACTUELLE :**
- ✅ `src_core/formulas_validated.py` - Formules validées
- ✅ `src_core/event_loader.py` - Chargement événements
- ✅ `src_core/price_loader_finnhub.py` - Chargement prix
- ✅ `src_core/trend_detection_pre_event_s107.py` - Détection tendance
- ✅ `src_core/random_forest_amplification.py` - RF amplification
- ✅ `src_core/double_wave.py` - Prédiction Double Wave
- ✅ `src_core/single_wave_strong.py` - Prédiction Single Wave
- ✅ `src_core/r2_amplification_correlation.py` - Corrélation R²

**Manquants (à ajouter) :**
- ❌ `core/config.py` ⭐ **CRITIQUE** (DB_PATH, utilisé partout)
- ❌ `core/finnhub_patterns.py` ⚠️ **IMPORTANT** (utilisé dans planificateur ligne 76-79)

### 2. Pipeline

**Présents :**
- ✅ `scripts/run_pipeline_complete.py` - Pipeline complet (8 étapes)

**Manquants :**
- ❌ `pipeline/double_wave_detector_rev12.py` ⚠️ **IMPORTANT**
  - Utilisé dans Étape 8.6 pour détection patterns depuis prix
  - Nécessaire pour fonctionnalités 2, 3, 4

### 3. Streamlit App

**Présents :**
- ✅ `streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py` - Planificateur principal
- ✅ `streamlit_app/Home.py` - Page d'accueil

**Fonctions identifiées dans planificateur :**
- ✅ `search_future_clusters()` - Fonctionnalité 1, 5
- ✅ `detect_pattern_type()` - Fonctionnalité 3
- ✅ `load_cache_patterns()` - Cache patterns
- ✅ `enrich_pattern_with_finnhub()` - Enrichissement patterns

**À vérifier :**
- ❓ Fonction calcul score confiance (fonctionnalité 12)
- ❓ Fonction stratégie sortie (fonctionnalité 13)
- ❓ Fonction détection Zigzag (fonctionnalité 3)

### 4. Scripts Utilitaires

**Présents :**
- ✅ `scripts/recalculate_empirical_scores_finnhub.py`
- ✅ `scripts/recalculate_empirical_scores_finnhub_p80_only.py`
- ✅ `scripts/compare_empirical_scores.py`

**À créer (question utilisateur) :**
- ⚠️ `scripts/recalcul/recalculate_core_scores_historical.py`
  - Calculer scores pour noyaux durs sur toutes dates historiques avec mouvements forts

---

## 📋 RÉPONSE QUESTION UTILISATEUR

**"Est-ce qu'on devrait établir des scores pour les noyaux durs pour toutes les dates dans la DB avec clusters/mouvements forts ?"**

### ✅ OUI, RECOMMANDÉ

**Justification :**

1. **Meilleure précision** : Scores spécifiques à chaque type de noyau dur (CPI, NFP, JOBLESS_PCE, GDP)
2. **Validation patterns** : Permet de vérifier si un noyau dur produit toujours le même pattern
3. **Prédiction améliorée** : Utiliser scores historiques réels au lieu de scores génériques

### Implémentation Proposée

**Script à créer :** `scripts/recalcul/recalculate_core_scores_historical.py`

**Méthodologie :**
1. Identifier toutes les dates avec mouvements forts (3 dernières années)
   - Utiliser `pipeline/double_wave_detector_rev12.py` pour détecter patterns
   - Filtrer mouvements > seuil (ex: 20 pips)
2. Pour chaque date avec mouvement fort :
   - Exécuter Étape 1-3 du pipeline (charger événements, détecter clusters, définir noyau dur)
   - Identifier type noyau dur (CPI, NFP, JOBLESS_PCE, GDP, GENERIC)
   - Mesurer impact réel depuis prix
3. Grouper par type noyau dur :
   - Calculer statistiques (avg, p80, median, std)
   - Calculer score empirique (formule actuelle ou P80 uniquement)
4. Stocker dans table `core_scores` :

```sql
CREATE TABLE IF NOT EXISTS core_scores (
    core_type VARCHAR,           -- 'CPI', 'NFP', 'JOBLESS_PCE', 'GDP', 'GENERIC'
    country VARCHAR,              -- 'US', 'EU', 'DE', 'GB'
    empirical_score DOUBLE,      -- Score empirique calculé
    avg_impact_pips DOUBLE,      -- Impact moyen en pips
    p80_impact_pips DOUBLE,      -- P80 impact en pips
    median_impact_pips DOUBLE,    -- Médiane impact
    std_impact_pips DOUBLE,       -- Écart-type
    sample_size INTEGER,          -- Nombre de dates avec ce noyau dur
    pattern_types VARCHAR,        -- 'DOUBLE_WAVE', 'SINGLE_WAVE', 'ZIGZAG' (JSON array)
    pattern_distribution VARCHAR, -- Distribution patterns (JSON)
    created_at TIMESTAMP,
    PRIMARY KEY (core_type, country)
)
```

**Utilisation dans pipeline :**
- Dans Étape 3, si score spécifique au noyau dur existe → l'utiliser
- Sinon → fallback sur score générique `event_families`

---

## 🎯 STRUCTURE FINALE PROPOSÉE

```
SESSION_VALIDATION_ACTUELLE/
│
├── 📄 README.md
├── 📄 INDEX_FICHIERS.md
├── 📄 RESUME_SESSION.md
├── 📄 GUIDE_DEVELOPPEMENT.md
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
│   ├── cluster_impact_calculator.py    # ⚠️ À VÉRIFIER si utilisé
│   ├── impact_measurement.py            # ⚠️ À VÉRIFIER si utilisé
│   └── event_families.py                # ⚠️ À VÉRIFIER si utilisé
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
│   │   └── recalculate_core_scores_historical.py  # ⚠️ À CRÉER (question utilisateur)
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
│   │   ├── REF-001_*.md à REF-005_*.md
│   │   └── INDEX_REFERENCES.md
│   │
│   ├── validation/                       # Documentation validation
│   │   └── VALIDATION_SESSION_2025_01_XX/
│   │
│   ├── pipeline/                         # Documentation pipeline
│   │   └── PIPELINE_REFERENCE/
│   │
│   └── methodology/                      # Méthodologie
│       └── METHODOLOGIE_TRAVAIL.md
│
├── 📁 outputs/                           # Résultats et logs
│   ├── data/                             # Données critiques
│   │   ├── impacts_reels_mesures.csv
│   │   └── comparison_formula_vs_p80_optimized.csv
│   │
│   ├── logs/                             # Logs
│   │   └── recalcul_complet_2020_2025.log
│   │
│   └── tests/                            # Résultats tests
│       └── *.csv
│
├── 📁 streamlit_app/                     # Application Streamlit
│   ├── Home.py
│   └── pages/
│       └── 5_Planificateur_V3.1_CLEAN_OLD.py
│
└── 📁 backups/                           # Backups organisés
    └── 20251203_114640/
        └── ...
```

---

## 📋 ACTIONS À EFFECTUER

### Phase 1 : Ajout Fichiers Manquants Critiques

1. **Copier `src/config.py` → `core/config.py`** ⭐ CRITIQUE
2. **Copier `src/core/finnhub_patterns.py` → `core/finnhub_patterns.py`** ⚠️ IMPORTANT
3. **Copier `scripts/session120/double_wave_detector_rev12.py` → `pipeline/double_wave_detector_rev12.py`** ⚠️ IMPORTANT

### Phase 2 : Création Script Noyaux Durs (Question Utilisateur)

4. **Créer `scripts/recalcul/recalculate_core_scores_historical.py`**
   - Identifier dates avec mouvements forts (3 dernières années)
   - Exécuter Étape 1-3 pipeline pour chaque date
   - Mesurer impacts réels
   - Calculer scores par type noyau dur
   - Stocker dans table `core_scores`

### Phase 3 : Réorganisation

5. **Renommer `src_core/` → `core/`** (fusionner avec nouveaux fichiers)
6. **Créer sous-répertoires** dans `scripts/`, `docs/`, `outputs/`
7. **Déplacer fichiers** dans sous-répertoires appropriés
8. **Renommer `references/` → `backups/`**

### Phase 4 : Nettoyage

9. **Supprimer fichiers obsolètes** (`cursor_*.md` si confirmé)
10. **Mettre à jour imports** dans scripts après réorganisation

---

## ⚠️ QUESTIONS À RÉSOUDRE

1. **`src_core/` vs `references/20251203_114640/src/core/` :**
   - Versions différentes détectées
   - Quelle version utiliser ? (actuelle dans `src_core/` recommandée)

2. **`streamlit_app/5_Planificateur_V3.1_CLEAN_OLD.py` :**
   - Version "OLD" - est-ce la bonne version à conserver ?
   - Ou utiliser version depuis `streamlit_app/pages/` (racine projet) ?

3. **Fichiers `cursor_*.md` :**
   - À supprimer ou conserver ?

4. **Script `recalculate_core_scores_historical.py` :**
   - Valider création et méthodologie proposée ?

---

## ✅ VALIDATION REQUISE

**⚠️ AUCUNE MODIFICATION NE SERA EFFECTUÉE SANS VOTRE VALIDATION**

**Merci de confirmer :**
1. ✅ Structure proposée acceptable ?
2. ✅ Fichiers à ajouter corrects ?
3. ✅ Script `recalculate_core_scores_historical.py` à créer ?
4. ✅ Questions à résoudre avant de procéder ?

---

**Prochaine étape :** Attendre votre validation avant d'appliquer les modifications




