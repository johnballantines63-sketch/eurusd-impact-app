# ANALYSE BESOINS APPLICATION - Structure Requise

**Date :** 2025-12-06  
**Objectif :** Identifier tous les fichiers nécessaires au bon fonctionnement de l'application Streamlit

---

## 🎯 OBJECTIF APPLICATION

**Interface Streamlit pour trader avec prédictions d'impact de clusters d'événements économiques.**

### Fonctionnalités Requises

1. **Recherche dates futures candidates** (mouvements moyens/forts)
2. **Recherche mouvements historiques** (3 dernières années, analyse prix)
3. **Classification par patterns** (single wave fort, double wave, zigzag, bullish/bearish)
4. **Identification clusters d'événements** et association aux patterns
5. **Recherche dates futures** avec clusters similaires
6. **Calcul prédictions** (impact, latence, durée, pattern) selon formules
7. **Calendrier dates futures** avec cluster/pattern/impact attendu
8. **Sélection date** par utilisateur
9. **Fenêtre événements** du cluster sélectionné
10. **Affichage Previous/Estimate** + case Actual (manuelle)
11. **Calcul prédiction** avec actuals fournis
12. **Indications trading** : quand rentrer (buy/sell), quand sortir (temps/pips), score confiance
13. **Stratégie de sortie** (pas au pic absolu, garantir trades gagnants)

---

## 📋 FICHIERS NÉCESSAIRES PAR FONCTIONNALITÉ

### 1. Recherche Dates Futures Candidates

**Fonctions requises :**
- Recherche dans `events` table pour dates futures
- Filtrage par importance (checkbox fort/moyen)
- Association avec clusters d'événements

**Fichiers nécessaires :**
- ✅ `core/event_loader.py` - Chargement événements
- ✅ `core/config.py` - Configuration DB
- ❓ Script de recherche dates futures (à vérifier si existe)

### 2. Recherche Mouvements Historiques (3 dernières années)

**Fonctions requises :**
- Analyse prix historiques (`prices_finnhub_m1`, `prices_finnhub_h1`)
- Détection mouvements moyens/forts
- Classification par amplitude

**Fichiers nécessaires :**
- ✅ `core/price_loader_finnhub.py` - Chargement prix
- ✅ `pipeline/double_wave_detector_rev12.py` - Détection patterns
- ❓ Script d'analyse mouvements historiques (à vérifier)

### 3. Classification par Patterns

**Fonctions requises :**
- Détection Single Wave Fort
- Détection Double Wave
- Détection Zigzag
- Classification Bullish/Bearish

**Fichiers nécessaires :**
- ✅ `core/double_wave.py` - Prédiction Double Wave
- ✅ `core/single_wave_strong.py` - Prédiction Single Wave
- ✅ `pipeline/double_wave_detector_rev12.py` - Détection Double Wave
- ❓ Script détection Zigzag (à vérifier)
- ❓ Script classification Bullish/Bearish (à vérifier)

### 4. Identification Clusters d'Événements

**Fonctions requises :**
- Détection clusters (fenêtre temporelle)
- Association clusters ↔ patterns
- Vérification si un cluster peut produire patterns différents

**Fichiers nécessaires :**
- ✅ `pipeline/run_pipeline_complete.py` - Étape 2 (détection clusters)
- ✅ `pipeline/run_pipeline_complete.py` - Étape 3 (noyau dur)
- ✅ `pipeline/run_pipeline_complete.py` - Étape 4 (clusters identiques)
- ✅ `pipeline/run_pipeline_complete.py` - Étape 8.6 (pattern detection)

### 5. Recherche Dates Futures avec Clusters Similaires

**Fonctions requises :**
- Recherche dans `events` table (dates futures)
- Comparaison clusters (Jaccard similarity)
- Identification dates avec clusters similaires

**Fichiers nécessaires :**
- ✅ `pipeline/run_pipeline_complete.py` - Étape 4 (recherche clusters identiques)
- ❓ Script recherche dates futures (à vérifier)

### 6. Calcul Prédictions

**Fonctions requises :**
- Calcul impact base
- Calcul amplification
- Calcul latence
- Calcul durée pattern
- Prédiction pattern (Single/Double Wave)

**Fichiers nécessaires :**
- ✅ `core/formulas_validated.py` - Formules validées
  - `calculate_impact_d()` - Impact base
  - `calculate_adjusted_empirical_score()` - Score ajusté
  - `calculate_amplification_extended()` - Amplification
- ✅ `pipeline/run_pipeline_complete.py` - Pipeline complet (8 étapes)
- ✅ `core/trend_detection_pre_event_s107.py` - Détection tendance
- ✅ `core/random_forest_amplification.py` - RF amplification
- ✅ `core/double_wave.py` - Prédiction Double Wave
- ✅ `core/single_wave_strong.py` - Prédiction Single Wave

### 7. Calendrier Dates Futures

**Fonctions requises :**
- Affichage dates futures
- Affichage cluster/pattern/impact attendu
- Interface Streamlit

**Fichiers nécessaires :**
- ✅ `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py` - Interface Streamlit
- ❓ Autres pages Streamlit si nécessaires

### 8-9. Sélection Date et Fenêtre Événements

**Fonctions requises :**
- Interface sélection date
- Affichage liste événements du cluster
- Affichage Previous/Estimate

**Fichiers nécessaires :**
- ✅ `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py` - Interface Streamlit
- ✅ `core/event_loader.py` - Chargement événements

### 10-11. Calcul Prédiction avec Actuals

**Fonctions requises :**
- Saisie Actual (manuelle)
- Calcul prédiction avec actuals
- Utilisation formules validées

**Fichiers nécessaires :**
- ✅ `pipeline/run_pipeline_complete.py` - Pipeline complet
- ✅ `core/formulas_validated.py` - Formules validées

### 12. Indications Trading

**Fonctions requises :**
- Calcul direction (buy/sell) selon prédiction up/down
- Calcul timing entrée
- Calcul timing sortie (temps ou pips)
- Calcul score confiance

**Fichiers nécessaires :**
- ✅ `core/formulas_validated.py` - Formules validées
- ✅ `core/double_wave.py` - Timings Double Wave
- ✅ `core/single_wave_strong.py` - Timings Single Wave
- ❓ Script calcul score confiance (à vérifier)

### 13. Stratégie de Sortie

**Fonctions requises :**
- Calcul timing sortie (pas au pic absolu)
- Stratégie garantir trades gagnants
- Adaptation si prédiction < réalité (situation actuelle)

**Fichiers nécessaires :**
- ✅ `core/formulas_validated.py` - Formules validées
- ✅ `core/double_wave.py` - Timings patterns
- ❓ Script stratégie sortie (à vérifier)

---

## 🔍 FICHIERS MANQUANTS IDENTIFIÉS

### Critiques (Nécessaires au fonctionnement)

1. **`core/config.py`** ⭐ CRITIQUE
   - DB_PATH, configuration
   - Utilisé par tous les scripts

2. **`core/finnhub_patterns.py`** ⚠️ IMPORTANT
   - Patterns Finnhub
   - Utilisé pour ajustements

3. **`pipeline/double_wave_detector_rev12.py`** ⚠️ IMPORTANT
   - Détection patterns depuis prix
   - Utilisé dans Étape 8.6

### À Vérifier (Peuvent être nécessaires)

1. **Script recherche dates futures**
   - Fonctionnalité 1, 5, 7
   - À vérifier si existe dans `streamlit_app/` ou `scripts/`

2. **Script analyse mouvements historiques**
   - Fonctionnalité 2
   - À vérifier si existe

3. **Script détection Zigzag**
   - Fonctionnalité 3
   - À vérifier si existe

4. **Script classification Bullish/Bearish**
   - Fonctionnalité 3
   - Peut être dans `double_wave_detector_rev12.py`

5. **Script calcul score confiance**
   - Fonctionnalité 12
   - À vérifier si existe

6. **Script stratégie sortie**
   - Fonctionnalité 13
   - À vérifier si existe

---

## 📊 QUESTION UTILISATEUR

**"Est-ce qu'on devrait établir des scores pour les noyaux durs pour toutes les dates dans la DB avec clusters/mouvements forts ?"**

### Analyse

**Noyau dur =** Événements core identifiés dans Étape 3 (CPI, NFP, JOBLESS_PCE, GDP, etc.)

**Scores pour noyaux durs =** Scores empiriques spécifiques aux noyaux durs, calculés sur toutes les dates historiques avec mouvements forts.

### Avantages

1. **Meilleure prédiction** : Scores basés sur historique réel des noyaux durs
2. **Précision accrue** : Scores spécifiques à chaque type de noyau dur
3. **Validation** : Permet de valider si un noyau dur produit toujours le même pattern

### Implémentation Proposée

**Script à créer :** `scripts/recalcul/recalculate_core_scores_historical.py`

**Fonctionnalités :**
1. Identifier toutes les dates avec mouvements forts (3 dernières années)
2. Pour chaque date, identifier le noyau dur (Étape 3)
3. Mesurer l'impact réel pour chaque noyau dur
4. Calculer score empirique par noyau dur (moyenne/P80 des impacts)
5. Stocker dans table `core_scores` ou `event_families` avec type noyau dur

**Table proposée :**
```sql
CREATE TABLE core_scores (
    core_type VARCHAR,  -- 'CPI', 'NFP', 'JOBLESS_PCE', 'GDP', etc.
    country VARCHAR,
    empirical_score DOUBLE,
    avg_impact_pips DOUBLE,
    p80_impact_pips DOUBLE,
    sample_size INTEGER,
    pattern_types VARCHAR,  -- 'DOUBLE_WAVE', 'SINGLE_WAVE', etc.
    created_at TIMESTAMP
)
```

**Utilisation :**
- Dans Étape 3, utiliser score spécifique au noyau dur au lieu de score générique
- Améliorer précision prédiction

---

## ✅ CHECKLIST FICHIERS NÉCESSAIRES

### Core Modules (Critiques)

- [x] `core/formulas_validated.py`
- [x] `core/event_loader.py`
- [x] `core/price_loader_finnhub.py`
- [x] `core/trend_detection_pre_event_s107.py`
- [x] `core/random_forest_amplification.py`
- [x] `core/double_wave.py`
- [x] `core/single_wave_strong.py`
- [x] `core/r2_amplification_correlation.py`
- [ ] `core/config.py` ⭐ **À AJOUTER**
- [ ] `core/finnhub_patterns.py` ⭐ **À AJOUTER**

### Pipeline

- [x] `pipeline/run_pipeline_complete.py`
- [ ] `pipeline/double_wave_detector_rev12.py` ⭐ **À AJOUTER**

### Streamlit App

- [x] `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py`
- [x] `streamlit_app/Home.py`

### Scripts Utilitaires

- [x] `scripts/recalcul/recalculate_empirical_scores_finnhub.py`
- [x] `scripts/recalcul/recalculate_empirical_scores_finnhub_p80_only.py`
- [x] `scripts/recalcul/compare_empirical_scores.py`
- [ ] `scripts/recalcul/recalculate_core_scores_historical.py` ⚠️ **À CRÉER** (question utilisateur)

### Documentation

- [x] `docs/references/REF-001` à `REF-005`
- [x] `docs/validation/VALIDATION_SESSION_2025_01_XX/`
- [x] `docs/pipeline/PIPELINE_REFERENCE/`

---

## 🎯 PROPOSITION STRUCTURE FINALE

Basée sur les besoins de l'application, la structure proposée dans `PROPOSITION_REORGANISATION.md` est **adaptée**, avec ajouts suivants :

1. **Ajouter `core/config.py`** (critique)
2. **Ajouter `core/finnhub_patterns.py`** (important)
3. **Ajouter `pipeline/double_wave_detector_rev12.py`** (important)
4. **Créer `scripts/recalcul/recalculate_core_scores_historical.py`** (question utilisateur)

---

**Prochaine étape :** Vérifier présence fichiers manquants et créer script `recalculate_core_scores_historical.py` si validé




