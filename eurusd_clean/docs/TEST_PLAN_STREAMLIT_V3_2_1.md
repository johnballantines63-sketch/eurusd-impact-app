# Plan de Test Rigoureux - Streamlit V3.2.1

**Date :** 2025-12-12  
**Objectif :** Validation scientifique complète du système avant production

---

## 🎯 Principes

1. **Aucune supposition** : Tout doit être testé empiriquement
2. **Tests reproductibles** : Scripts automatisés avec résultats vérifiables
3. **Validation données réelles** : Tests sur dates connues avec résultats attendus
4. **Traçabilité** : Chaque test documente ses inputs, outputs, et verdict

---

## 📋 Tests Unitaires

### Test 1 : Import et Initialisation

**Script :** `tests/test_imports_streamlit.py`

**Objectif :** Vérifier que tous les imports fonctionnent

**Tests :**
- [ ] Import `app.streamlit_app` sans erreur
- [ ] Import `app.compute_real_prediction` sans erreur
- [ ] Toutes les dépendances présentes (duckdb, pandas, streamlit, etc.)
- [ ] PROJECT_ROOT correctement défini

**Critère de succès :** Tous les imports réussissent

---

### Test 2 : Fonction `load_day_events`

**Script :** `tests/test_load_day_events.py`

**Objectif :** Vérifier le chargement des events depuis DB

**Tests :**
- [ ] Charge correctement pour une date avec events (ex: 2024-09-11)
- [ ] Retourne DataFrame vide pour date sans events
- [ ] Colonnes présentes : ts_local, country, event_key, actual, previous, forecast
- [ ] `actual` présent dans les colonnes
- [ ] Pas de NULL sur ts_local
- [ ] Ordre correct (ORDER BY ts_local ASC)

**Date de test :** 2024-09-11 (connue pour avoir des events)

**Critère de succès :** ≥1 event chargé, colonnes complètes

---

### Test 3 : Fonction `load_actuals_from_db`

**Script :** `tests/test_load_actuals_from_db.py`

**Objectif :** Vérifier le chargement des actuals depuis DB

**Tests :**
- [ ] Charge actuals pour date passée avec actuals (ex: 2024-09-11)
- [ ] Retourne dict vide pour date sans actuals
- [ ] Format event_uid correct : `{event_key}|{ts_iso}|row={idx}`
- [ ] Valeurs actuals non-NULL uniquement
- [ ] Compatibilité fallback : inclut aussi clé sans `row=`

**Date de test :** 2024-09-11

**Critère de succès :** ≥1 actual chargé, format UID correct

---

### Test 4 : Fonction `detect_clusters`

**Script :** `tests/test_detect_clusters.py`

**Objectif :** Vérifier la détection de clusters

**Tests :**
- [ ] Fenêtre glissante : 14:30, 14:50, 15:10 → 1 cluster (30 min)
- [ ] Séparation : 14:30, 14:50, 15:30 → 2 clusters (60 min gap)
- [ ] Retourne (clusters, df_sorted) correctement
- [ ] `row_ids` correspond aux indices de df_sorted
- [ ] Pas de clusters vides

**Données de test :** DataFrame avec events à différentes heures

**Critère de succès :** Clusters corrects, cohérence indices

---

### Test 5 : Fonction `calculate_cluster_direction_impact`

**Script :** `tests/test_calculate_cluster_impact.py`

**Objectif :** Vérifier le calcul d'impact avec actuals

**Tests :**
- [ ] Trouve actuals avec event_uid nouveau format (`row=`)
- [ ] Fallback vers ancien format si nouveau non trouvé
- [ ] Calcul surprise correct : `((actual - forecast) / forecast) * 100`
- [ ] Direction correcte selon FAMILY_SENTIMENT
- [ ] Impact > 0 si actuals présents
- [ ] Impact = 0 si aucun actual trouvé

**Données de test :** Cluster avec 1-2 events, actuals connus

**Critère de succès :** Impact calculé correctement selon actuals

---

### Test 6 : Fonction `compute_real_prediction`

**Script :** `tests/test_compute_real_prediction.py`

**Objectif :** Vérifier le calcul complet de prédiction

**Tests :**
- [ ] Charge pred_vol_pips depuis daily_risk_signal_v3_2_1
- [ ] Détecte clusters correctement
- [ ] Calcule impact avec actuals fournis
- [ ] Retourne direction BUY/SELL/NO_TRADE correcte
- [ ] Pattern détecté (single_wave/double_wave/zigzag)
- [ ] Structure dict compatible UI
- [ ] Validation Pydantic si disponible (sans casser si absent)

**Date de test :** 2024-09-11 avec actuals connus

**Critère de succès :** Prédiction complète et cohérente

---

## 🔗 Tests d'Intégration

### Test 7 : Workflow Complet (Date Passée)

**Script :** `tests/test_integration_past_date.py`

**Objectif :** Tester le workflow complet pour une date passée

**Scénario :**
1. Sélectionner date passée : 2024-09-11
2. Charger events depuis DB
3. Actuals chargés automatiquement depuis DB
4. Calculer prédiction avec moteur réel
5. Vérifier résultats

**Vérifications :**
- [ ] Events chargés correctement
- [ ] Actuals pré-remplis depuis DB
- [ ] Moteur réel calculé avec succès
- [ ] Direction != NO_TRADE si actuals présents et impact > 0
- [ ] Prédiction cohérente avec données

**Critère de succès :** Workflow complet fonctionne sans erreur

---

### Test 8 : Workflow Complet (Date Future)

**Script :** `tests/test_integration_future_date.py`

**Objectif :** Tester le workflow pour une date future

**Scénario :**
1. Sélectionner date future : 2026-01-15
2. Charger events (si disponibles)
3. Formulaire actuals en mode édition
4. Saisir actuals manuellement
5. Calculer prédiction

**Vérifications :**
- [ ] Formulaire actuals éditable
- [ ] Actuals saisis stockés dans session_state
- [ ] Moteur réel utilise actuals saisis
- [ ] Calcul fonctionne avec actuals manuels

**Critère de succès :** Workflow future date fonctionne

---

### Test 9 : Event UID Uniqueness

**Script :** `tests/test_event_uid_uniqueness.py`

**Objectif :** Vérifier qu'il n'y a pas de collisions

**Tests :**
- [ ] Events dupliqués (même event_key + ts_local) → UIDs différents
- [ ] Clés Streamlit uniques pour tous les widgets
- [ ] Pas de collisions dans session_state
- [ ] Moteur retrouve correctement les actuals même avec duplications

**Données de test :** DataFrame avec events dupliqués

**Critère de succès :** Pas de collisions, tous les actuals retrouvés

---

## 🧪 Tests End-to-End (E2E)

### Test 10 : Scénario Réel Complet

**Script :** `tests/test_e2e_realistic_scenario.py`

**Objectif :** Simuler un usage réel complet

**Scénario :**
1. Date : 2024-09-11 (date connue avec events et actuals)
2. Charger tous les events
3. Vérifier actuals chargés depuis DB
4. Calculer prédiction avec moteur réel
5. Vérifier structure résultat
6. Vérifier cohérence des valeurs

**Vérifications :**
- [ ] Tous les events chargés
- [ ] Actuals présents pour events core
- [ ] Prédiction calculée : direction, pattern, impact
- [ ] Fenêtres entry/exit calculées
- [ ] Targets (take_profit, stop_loss) cohérents

**Critère de succès :** Scénario complet fonctionne, résultats cohérents

---

## 📊 Validation Données Réelles

### Test 11 : Validation sur Dates Connues

**Script :** `tests/test_validation_known_dates.py`

**Objectif :** Valider sur plusieurs dates réelles connues

**Dates de test :**
- 2024-09-11 (NFP + autres)
- 2024-10-10 (CPI probablement)
- 2025-08-01 (date mentionnée par l'utilisateur)

**Pour chaque date :**
- [ ] Events chargés correctement
- [ ] Actuals présents en DB
- [ ] Prédiction calculée
- [ ] Pas d'erreurs

**Critère de succès :** Toutes les dates fonctionnent

---

## 🔍 Tests de Régression

### Test 12 : Pas de Régression vs Placeholder

**Script :** `tests/test_no_regression.py`

**Objectif :** Vérifier que le moteur réel ≥ placeholder

**Tests :**
- [ ] Moteur réel fonctionne (pas de crash)
- [ ] Résultats cohérents (direction valide, impact ≥ 0)
- [ ] Pas de perte de fonctionnalité vs placeholder

**Critère de succès :** Moteur réel fonctionne au moins aussi bien que placeholder

---

## 📝 Checklist Finale

Avant de considérer le système "production-ready" :

- [ ] Tous les tests unitaires passent
- [ ] Tous les tests d'intégration passent
- [ ] Tests E2E fonctionnent
- [ ] Validation dates réelles OK
- [ ] Pas de régressions
- [ ] Documentation complète
- [ ] Erreurs gérées proprement

---

## 🚨 Critères de Blocage

Le système NE DOIT PAS être considéré comme prêt si :

- ❌ Des tests unitaires échouent
- ❌ Des tests d'intégration échouent
- ❌ Des erreurs non gérées apparaissent
- ❌ Des données sont perdues ou corrompues
- ❌ Des collisions event_uid existent
- ❌ Des actuals ne sont pas retrouvés quand ils devraient l'être

---

**Document créé le :** 2025-12-12  
**Statut :** ⚠️ EN ATTENTE DE TESTS

