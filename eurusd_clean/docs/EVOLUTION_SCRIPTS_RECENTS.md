# Évolution des Scripts Récents - Analyse Complète

**Date d'analyse** : Scripts modifiés depuis le 3 décembre 2025  
**Objectif** : Comprendre l'évolution du pipeline et identifier les changements récents

---

## 📋 SCRIPTS ANALYSÉS

### Scripts de Test Récents (3 décembre 2025)
1. ✅ `pipeline_etape_par_etape_interactif.py` (16:24) - Exécution interactive étape par étape
2. ✅ `test_pipeline_seuil_adaptatif.py` (15:51) - Test du seuil adaptatif pour noyau dur
3. ✅ `test_impact_options_noyau_dur.py` (14:34) - Comparaison options noyau dur
4. ✅ `investiguer_jobless_claims.py` (16:02) - Investigation Jobless Claims
5. ✅ `test_configurations_patterns.py` (09:43) - Test configurations et patterns
6. ✅ `test_phase1_restauration.py` (12:00) - Test restauration pipeline référence

### Script Principal
7. ✅ `run_pipeline_complete.py` (16:17) - Pipeline principal (2313 lignes)

---

## 🔍 ÉVOLUTION IDENTIFIÉE

### 1. ÉTAPE 2 : DÉTECTION CLUSTERS

**Implémentation actuelle** (lignes 180-245) :
```python
# Fenêtre définie APRÈS l'événement déclencheur
window_start = row['ts_utc']  # Premier événement du cluster
window_end = window_start + timedelta(minutes=window_minutes)  # 30 min après
```

**✅ CONFIRMATION** : La fenêtre est bien définie APRÈS l'événement déclencheur (premier événement du cluster).  
**⚠️ POINT À VÉRIFIER** : L'utilisateur mentionne que la fenêtre doit être définie APRÈS les événements déclencheurs du mouvement, pas avant. Peut-être que cela signifie que la fenêtre doit être définie après avoir identifié les événements déclencheurs principaux (CPI/NFP), pas juste après le premier événement du cluster.

**Exemple pour 2025-09-11** :
- Premier événement : 14:15 (EU)
- CPI US : 14:30
- Fenêtre actuelle : 14:15 → 14:45
- Peut-être devrait être : 14:30 → 15:00 (après CPI US déclencheur)

---

### 2. TIMINGS PARFAITS (Session 64)

**✅ IMPLÉMENTÉ** dans `etape8_appliquer_cluster_cible` (lignes 1776-1916) :

**Fonction `predict_double_wave_timeline_s64()`** :
- **T+5 min** : Peak Phase 1 (58% de l'impact total)
- **T+11 min** : Creux Pullback (84% retrace de Phase 1)
- **T+15 min** : Peak Phase 2 (absolu, 90% de l'impact total)
- **T+40 min** : Stabilisation finale

**Timings validés** : 0.00 min d'erreur (57/57 dates = 100% cas parfaits)

**Adaptation pour clusters multiples** (lignes 1807-1815) :
- Si plusieurs clusters détectés (ex: 2025-09-11 avec Cluster 2 à 14:45)
- Pullback ajusté : T+19 (4 min après Cluster 2)
- Peak 2 ajusté : T+40 (21 min après pullback)

**✅ CONFIRMATION** : Les timings parfaits sont bien implémentés et utilisés pour Double Wave.

---

### 3. NOYAU DUR - SEUIL ADAPTATIF

**✅ IMPLÉMENTÉ** dans `etape3_definir_noyau_dur` (lignes 251-450) :

**Logique adaptative** :
```python
# Support >= 60% OU (support >= 40% ET importance <= 2) OU (support >= 20% ET importance <= 3 ET GENERIC)
if support >= 0.60 or \
   (support >= 0.40 and importance <= 2) or \
   (support >= 0.20 and importance <= 3 and core_type == 'GENERIC'):
    core_events.append(event_id)
```

**Correction pour événements génériques** (lignes 277-450) :
- Pour `core_type == 'GENERIC'` : Calcul support sur **TOUS** les clusters historiques, pas seulement ceux du même type
- Permet d'inclure Jobless Claims même si leur support dans clusters CPI est faible (19-21%)

**✅ CONFIRMATION** : Le seuil adaptatif est implémenté et corrigé pour inclure Jobless Claims.

---

### 4. IMPACT DE BASE - MÉTHODE SESSION 88

**✅ IMPLÉMENTÉ** dans `etape8_appliquer_cluster_cible` (lignes 1185-1224) :

**Méthode Session 88** :
1. Score moyen des événements du cluster (sans ajustement individuel)
2. Surprise maximale du cluster
3. Ajuster score moyen avec surprise MAX
4. Calculer impact de base avec Formule D (correction vectorielle 0.758)

**Documentation** : `docs/ANALYSE_DIFFERENCES_SESSION88.md`  
**Validation** : Erreur réduite de 126.83 à 16.62 pips (87% d'amélioration)

**✅ CONFIRMATION** : La méthode Session 88 est utilisée pour l'impact de base.

---

### 5. DÉTECTION PATTERN RÉEL vs PRÉDIT

**✅ IMPLÉMENTÉ** dans `etape8_appliquer_cluster_cible` (lignes 1665-1705) :

**Logique** :
1. Détecter d'abord le pattern réel dans les prix (Session 120, `detect_for_date_duckdb_rev12`)
2. Vérifier si critères Double Wave sont remplis (événements)
3. Si pattern réel = Single Wave ET critères Double Wave remplis → Utiliser Single Wave Fort
4. Si pattern réel = Double Wave ET critères remplis → Utiliser Double Wave avec timings prédits

**Exemple 2025-08-01** :
- Critères Double Wave remplis (événements)
- Pattern réel détecté : Single Wave
- → Utiliser Single Wave Fort avec timings T+8, T+15, T+25

**✅ CONFIRMATION** : La détection pattern réel est implémentée et utilisée pour valider les patterns prédits.

---

### 6. STRATÉGIE HYBRIDE PATTERN/FORMULES

**✅ IMPLÉMENTÉ** dans `etape8_appliquer_cluster_cible` (lignes 2051-2101) :

**Logique selon pattern** :

**Single Wave** :
- Si écart < 10 pips → Utiliser formules
- Sinon → Utiliser pattern (plus fiable pour Single Wave)

**Double Wave** :
- Si formules suspectes (amplification < 0.5x OU impact < 30% du pattern) → Utiliser pattern
- Sinon → Utiliser formules (plus fiables pour Double Wave)

**Correction récente** (lignes 2078-2091) :
- Pour Double Wave, si formules très faibles (ex: 4.24 pips) et pattern disponible (ex: 56.8 pips) → Utiliser pattern
- Cas 11 septembre : Formules (4.24 pips) vs Pattern (56.8 pips) → Pattern plus réaliste

**✅ CONFIRMATION** : La stratégie hybride est implémentée avec logique différenciée selon le pattern.

---

### 7. AMPLIFICATION - HIÉRARCHIE

**✅ IMPLÉMENTÉ** dans `etape8_appliquer_cluster_cible` (lignes 1230-1400) :

**Hiérarchie** :
1. **Random Forest** (si clusters identiques >= 3)
2. **Linéaire** (si tendance détectée avec R² > 0.3)
3. **Moyenne** (fallback)

**Documentation** : `docs/VALIDATION_SESSION_2025_01_XX/EXPLICATION_HIERARCHIE_8_3.md`

**✅ CONFIRMATION** : La hiérarchie d'amplification est implémentée (RF → Linéaire → Moyenne).

---

## ⚠️ POINTS À VÉRIFIER

### 1. ÉTAPE 2 : Fenêtre Temporelle

**Question** : La fenêtre doit-elle être définie APRÈS les événements déclencheurs principaux (CPI/NFP) plutôt qu'après le premier événement du cluster ?

**Exemple 2025-09-11** :
- Premier événement : 14:15 (EU)
- CPI US déclencheur : 14:30
- Fenêtre actuelle : 14:15 → 14:45
- Fenêtre proposée : 14:30 → 15:00 (après CPI US)

**Action** : Vérifier dans la documentation si la fenêtre doit être ancrée sur l'événement déclencheur principal.

---

### 2. TIMINGS PARFAITS - Utilisation

**✅ CONFIRMÉ** : Les timings parfaits sont implémentés et utilisés pour Double Wave.

**Question** : Sont-ils également utilisés pour Single Wave Fort ?

**Réponse** : Oui, Single Wave Fort utilise `predict_single_wave_timeline()` avec timings T+8, T+15, T+25 (Session 67).

---

### 3. PRÉDICTION TIMINGS - Indicateur

**✅ IMPLÉMENTÉ** : Le champ `timings_predicted` est retourné dans `final_prediction` (ligne 2134) :
- `True` : Timings prédits (Session 64/67)
- `False` : Timings détectés depuis prix réels

**✅ CONFIRMATION** : L'indicateur est présent pour distinguer timings prédits vs détectés.

---

## 📊 RÉSUMÉ DES CORRECTIONS RÉCENTES

### Corrections Appliquées (3 décembre 2025)

1. ✅ **Seuil adaptatif noyau dur** : Support calculé sur tous clusters pour événements génériques
2. ✅ **Jobless Claims inclus** : Seuil adaptatif permet inclusion même avec support faible (19-21%)
3. ✅ **Stratégie hybride Double Wave** : Utiliser pattern si formules suspectes (amplification < 0.5x)
4. ✅ **Timings parfaits** : Implémentés pour Double Wave (T+5, T+11, T+15, T+40)
5. ✅ **Méthode Session 88** : Utilisée pour impact de base (score moyen ajusté avec surprise MAX)
6. ✅ **Détection pattern réel** : Validation pattern réel avant utilisation timings prédits

---

## 🎯 PROCHAINES ÉTAPES

1. **Vérifier Étape 2** : Confirmer si la fenêtre doit être ancrée sur l'événement déclencheur principal (CPI/NFP)
2. **Tester pipeline** : Exécuter étape par étape pour valider toutes les corrections
3. **Comparer résultats** : Comparer avec résultats précédents (avant corrections)
4. **Documenter** : Mettre à jour documentation avec toutes les corrections appliquées

---

## 📝 NOTES

- **Performance attendue** : MAE < 10 pips (objectif)
- **Performance validée** : MAE 8.4 pips (avec pic absolu)
- **Taux acceptable** : 63.2%
- **Taux excellent** : 55.3%

**Documentation de référence** : `docs/PIPELINE_REFERENCE/`

---

**Date de création** : Analyse des scripts récents  
**Dernière mise à jour** : 3 décembre 2025




