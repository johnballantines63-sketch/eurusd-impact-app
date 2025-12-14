# Analyse de la Situation Actuelle - Planificateur V3.0

**Date** : 2025-01-XX  
**Objectif** : Retrouver la situation fonctionnelle d'hier soir avec le planificateur qui fonctionnait bien (sauf problème d'échelle du graphique)

---

## 📋 État Actuel

### Fichiers Existants ✅

1. **`streamlit_app/pages/5_Planificateur_Pipeline_Valide.py`**
   - Structure de base créée
   - Contrôles d'échelle du graphique présents (sliders temps et amplitude Y)
   - Interface utilisateur complète
   - ⚠️ Mais le pipeline est simplifié et incomplet

2. **`scripts/run_pipeline_complete.py`**
   - Classe `PipelineExecutor` créée
   - Structure des 8 étapes présente
   - ⚠️ Mais les implémentations sont simplifiées (stubs)

3. **Modules Core Existants** :
   - ✅ `src/core/event_loader.py` - Chargement événements HIGH impact
   - ✅ `src/core/formulas_validated.py` - Calcul impact de base (Formule D)
   - ✅ `src/core/trend_detection_pre_event_s107.py` - Détection tendance par inversion
   - ✅ `src/core/impact_measurement.py` - Mesure impact réel depuis prix

---

## ❌ Fichiers Manquants (Mentionnés dans la Documentation)

### 1. `scripts/phase_a_robust_validation.py` ⚠️ CRITIQUE

**Fonctions attendues** :
- `detect_double_wave_pattern()` - Détection pattern Double Wave/Single Wave
- `load_price_window()` - Chargement fenêtre de prix

**Références dans la documentation** :
- `PIPELINE_REFERENCE_COMPLETE.md` ligne 262 : "Fichier : `scripts/phase_a_robust_validation.py` - `detect_double_wave_pattern`"
- `PIPELINE_KNOWLEDGE_BASE.md` ligne 344 : "scripts/phase_a_robust_validation.py"

**Fichiers similaires trouvés** (mais pas le bon) :
- `scripts/session137/extract_all_patterns_real_metrics_correct_workflow.py` - Contient `detect_double_wave()` mais pas la structure attendue
- `scripts/session118/double_wave_detector.py` - Détecteur mais pas la fonction `detect_double_wave_pattern()` attendue
- `src/core/double_wave.py` - Contient `detect_double_wave_conditions()` mais pas la détection complète

**Action requise** : Créer ce fichier avec les fonctions attendues selon la documentation

---

### 2. `src/core/amplification_random_forest.py` ⚠️ IMPORTANT

**Fonction attendue** :
- `predict_amplification_random_forest()` - Prédiction amplification RF global

**Références dans la documentation** :
- `PIPELINE_REFERENCE_COMPLETE.md` ligne 659 : "src/core/amplification_random_forest.py : Random Forest global"
- `PIPELINE_ARCHITECTURE_DETAILED.md` ligne 168 : "core.amplification_random_forest : RF global"

**Action requise** : Créer ce module avec Random Forest global pour prédiction amplification

---

### 3. `src/core/amplification_random_forest_per_date.py` ⚠️ IMPORTANT

**Fonctions attendues** :
- `train_random_forest_per_date()` - Entraînement RF par date
- `predict_amplification_with_per_date_rf()` - Prédiction amplification RF par date

**Références dans la documentation** :
- `PIPELINE_REFERENCE_COMPLETE.md` ligne 660 : "src/core/amplification_random_forest_per_date.py : Random Forest par date"
- `PIPELINE_ARCHITECTURE_DETAILED.md` ligne 169 : "core.amplification_random_forest_per_date : RF par date"

**Action requise** : Créer ce module avec Random Forest par date pour prédiction amplification

---

### 4. `src/core/exit_strategy.py` ⚠️ IMPORTANT

**Fonction attendue** :
- `calculate_exit_target()` - Calcul target de sortie optimisé

**Références dans la documentation** :
- `PIPELINE_REFERENCE_COMPLETE.md` ligne 302 : "Fichier : `src/core/exit_strategy.py`"
- `PIPELINE_ARCHITECTURE_DETAILED.md` ligne 171 : "core.exit_strategy : Stratégie sortie"

**Action requise** : Créer ce module avec calcul target de sortie (80% du prédit, max 1.5x)

---

## 🔍 Analyse de la Documentation

### Points Clés Identifiés

1. **Pic Absolu** ⭐ CRITIQUE
   - TOUJOURS utiliser `wave2_peak_pips_absolute` au lieu de `impact_pips`
   - Capture Wave 3 et continuations
   - MAE réduit de 23.4 à 8.4 pips (64.3%)

2. **Critères Tendance Assouplis** ⭐
   - `min_hours_before_event` : 12 heures (au lieu de 24)
   - Durée adaptative selon timeframe (6h pour M30/H1, 8h pour M1/M5/M15)

3. **Seuil Jaccard 0.60** ⭐
   - Assoupli de 0.8 pour trouver plus de clusters identiques

4. **Option C pour Pattern/Formules** ⭐
   - Écart < 10 pips : Garder formules (protection bons cas)
   - Écart >= 10 pips : Utiliser pattern directement (100%)

5. **Pas de Corrections DOUBLE_WAVE** ⭐
   - Désactivées car dégradent globalement

---

## 📊 Structure du Pipeline Attendue

### Étape 8 : Application au Cluster Cible

**Sous-étapes détaillées** :

1. **8.1 : Calcul Impact de Base**
   - ✅ Utilise `calculate_impact_d()` - Existe dans `formulas_validated.py`

2. **8.2 : Détection Tendance**
   - ✅ Utilise `detect_trend_pre_event_robust()` - Existe dans `trend_detection_pre_event_s107.py`
   - ⚠️ Mais la fonction s'appelle `detect_trend_by_inversion_s107()` dans le fichier

3. **8.3 : Prédiction Amplification**
   - ❌ Random Forest par date (si >= 5 clusters identiques) - **MANQUANT**
   - ❌ Random Forest global (fallback) - **MANQUANT**
   - ⚠️ Modèle linéaire (fallback) - À implémenter
   - ⚠️ Moyenne historique (dernier fallback) - À implémenter

4. **8.4 : Ajustements Support/Résistance**
   - ⚠️ Logique décrite dans la doc mais module non trouvé
   - À implémenter selon la documentation

5. **8.5 : Ajustements Patterns Finnhub**
   - ⚠️ `src/core/finnhub_amplification_adjustment.py` mentionné mais non trouvé
   - Peut être désactivé pour l'instant (comme dans le planificateur actuel)

6. **8.6 : Détection Pattern de Prix** ⚠️ CRITIQUE
   - ❌ `detect_double_wave_pattern()` - **MANQUANT** dans `phase_a_robust_validation.py`
   - Paramètres attendus :
     - `MIN_PHASE1_PIPS` : 20.0
     - `MIN_PHASE2_PIPS` : 14.0
     - `MIN_PULLBACK_RATIO` : 0.20
     - `MAX_PULLBACK_RATIO` : 0.80
     - `PHASE1_WINDOW_MINUTES` : 90
     - `PULLBACK_WINDOW_MINUTES` : 45
     - `PHASE2_WINDOW_MINUTES` : 180
   - ⚠️ IMPORTANT : Utiliser `wave2_peak_pips_absolute` (pic absolu)

7. **8.7 : Stratégie Hybride Pattern/Formules**
   - ⚠️ Option C sans pondération - À implémenter selon la doc

8. **8.8 : Calcul Target de Sortie**
   - ❌ `calculate_exit_target()` - **MANQUANT** dans `exit_strategy.py`
   - Stratégie : Sortie à 80% du prédit, limite max 1.5x

---

## 🎯 Plan d'Action pour Retrouver la Situation Fonctionnelle

### Phase 1 : Créer les Modules Manquants Critiques

1. **`scripts/phase_a_robust_validation.py`** ⭐ PRIORITÉ 1
   - Implémenter `detect_double_wave_pattern()` selon la documentation
   - Implémenter `load_price_window()` pour charger les prix
   - ⚠️ CRITIQUE : Utiliser pic absolu (`wave2_peak_pips_absolute`)

2. **`src/core/exit_strategy.py`** ⭐ PRIORITÉ 2
   - Implémenter `calculate_exit_target()` selon la documentation
   - Stratégie : 80% du prédit, max 1.5x

3. **`src/core/amplification_random_forest.py`** ⭐ PRIORITÉ 3
   - Implémenter Random Forest global pour prédiction amplification
   - Features : R², durée, amplitude, impact_base, num_events, pattern

4. **`src/core/amplification_random_forest_per_date.py`** ⭐ PRIORITÉ 4
   - Implémenter Random Forest par date pour prédiction amplification
   - Utilisé si >= 5 clusters identiques

### Phase 2 : Compléter le PipelineExecutor

1. **Étape 3 : Définir Noyau Dur**
   - Implémenter analyse historique complète (5 ans)
   - Calcul support scores

2. **Étape 4 : Rechercher Clusters Identiques**
   - Implémenter recherche historique complète
   - Calcul similarité Jaccard

3. **Étape 5 : Calculer Tendances**
   - Intégrer complètement `detect_trend_by_inversion_s107()`
   - Multi-timeframe (M1, M5, M15, M30, H1)

4. **Étape 6 : Calculer Impacts Base & Amplifications**
   - Intégrer complètement `measure_impact_from_dukascopy()`
   - Calcul amplification parfaite (réel/base)

5. **Étape 7 : Analyser Relation Tendance → Amplification**
   - Implémenter corrélations
   - Implémenter modèle linéaire
   - Intégrer Random Forest (global et par date)

6. **Étape 8 : Appliquer Cluster Cible**
   - Intégrer toutes les sous-étapes complètes
   - Utiliser pic absolu pour pattern
   - Option C pour pattern/formules

### Phase 3 : Intégrer dans le Planificateur Streamlit

1. **Chargement des Prix**
   - Intégrer `load_price_window()` dans le pipeline
   - Retourner `price_window` dans les résultats

2. **Graphique**
   - Les contrôles d'échelle sont déjà présents ✅
   - Intégrer les données de prix réelles
   - Afficher marqueurs (Wave 1, Wave 2, baseline, événement)

3. **Affichage des Résultats**
   - Structure déjà présente ✅
   - Compléter avec toutes les métriques du pipeline

---

## 📝 Notes Importantes

### Fichiers à Vérifier Manuellement

Si vous avez ces fichiers quelque part, merci de me les indiquer :

1. `scripts/phase_a_robust_validation.py` - Version fonctionnelle d'hier soir ?
2. `src/core/amplification_random_forest.py` - Existe-t-il ailleurs ?
3. `src/core/amplification_random_forest_per_date.py` - Existe-t-il ailleurs ?
4. `src/core/exit_strategy.py` - Existe-t-il ailleurs ?

### Fichiers de Session à Examiner

Il y a plusieurs fichiers de détection de patterns dans `scripts/session*` :
- `scripts/session137/extract_all_patterns_real_metrics_correct_workflow.py` - Contient `detect_double_wave()`
- `scripts/session118/double_wave_detector.py` - Détecteur validé
- `scripts/session119/pattern_detectors.py` - Détecteurs de patterns

**Question** : Est-ce qu'un de ces fichiers était utilisé hier soir dans le planificateur fonctionnel ?

---

## ✅ Prochaines Étapes

1. **Confirmer les fichiers manquants** avec vous
2. **Créer les modules manquants** selon la documentation
3. **Compléter le PipelineExecutor** avec les implémentations complètes
4. **Intégrer dans le planificateur Streamlit** avec les données réelles
5. **Tester sur date de référence** (2025-09-11)

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ⏳ En attente de confirmation des fichiers manquants




