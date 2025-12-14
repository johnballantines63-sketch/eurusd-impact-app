# ARCHIVE - Scripts Obsolètes Session 128

**Date :** 12 novembre 2025  
**Raison :** Scripts créés AVANT correction structure DB

---

## 🔴 POURQUOI ARCHIVÉS ?

Ces scripts ont été développés pendant Session 128 **AVANT** la découverte et correction du problème de structure DB.

### **Problème Découvert**

Table `events` utilisait mauvaise structure :
- ❌ Importée dans `economic_events` (mauvaise table)
- ❌ event_key avec underscores : `inflation_rate_mom`
- ❌ LEFT JOIN échouait avec `event_families`
- ❌ Pas de scores empiriques

### **Correction Appliquée**

Structure MASTER_PLAN restaurée :
- ✅ Import dans `events` (bonne table)
- ✅ event_key avec espaces : `inflation rate_mom`
- ✅ LEFT JOIN fonctionne
- ✅ Scores empiriques trouvés

### **Impact**

**TOUS les scripts développés avant correction sont obsolètes** car ils :
- Cherchaient données dans `economic_events`
- Utilisaient event_key avec underscores
- Avaient mauvais résultats (MAE 19-26 pips au lieu de 0.35)

---

## 📁 SCRIPTS ARCHIVÉS

### **Scripts Test (obsolètes)**
- `test_session115_ORIGINAL_adapted.py` - Adaptait Session 115 pour economic_events
- `test_session115_avec_estimate.py` - Testait avec estimate manquant
- `test_session115_reproduced.py` - Reproduction échouée
- `test_double_wave_11sept_adapted.py` - Double wave adapté (faux)
- `test_double_wave_final.py` - Version finale (fausse)
- `test_1_mapping_variants_non_regression.py` - Tests obsolètes
- `test_2_pipeline_calibration_non_regression.py` - Tests obsolètes
- `test_3_reference_case_11_sept.py` - Tests obsolètes

### **Scripts Debug (obsolètes)**
- `debug_11_sept.py` - Debug dates 11 sept
- `debug_11_sept_all.py` - Debug exhaustif
- `debug_economic_events.py` - Debug economic_events
- `debug_estimates.py` - Debug estimate manquant
- `debug_import_11sept.py` - Debug import
- `debug_importance_format.py` - Debug importance
- `debug_join.py` - Debug JOIN
- `debug_tables.py` - Debug tables
- `debug_scores_divergence.py` - Debug scores (résolu différemment)

### **Scripts Check (obsolètes)**
- `check_11sept_tables.py` - Check tables obsolètes
- `check_current_account_timestamp.py` - Check timestamps
- `check_events_table.py` - Check events (mauvaise table)
- `check_forecast_previous.py` - Check forecast
- `check_jobless_raw_data.py` - Check raw_data
- `check_jobless_timestamps.py` - Check timestamps
- `check_tables.py` - Check général

### **Scripts Import (obsolètes)**
- `import_eodhd_corrected.py` - Importait dans economic_events (faux)

### **Scripts Analysis (obsolètes)**
- `analyze_eodhd_source.py` - Analyse source EODHD
- `analyze_raw_data.py` - Analyse raw_data
- `inspect_country_codes.py` - Inspect codes pays
- `investigate_exhaustive.py` - Investigation complète
- `list_all_events_11sept.py` - Liste événements
- `show_all_columns.py` - Show colonnes
- `verify_db_11sept.py` - Vérification DB
- `verify_surprises.py` - Vérification surprises

### **Scripts Utilitaires (obsolètes)**
- `migrate_country_codes.py` - Migration codes pays
- `run_all_tests.py` - Run tests (obsolètes)
- `launch_tests.sh` - Launch tests

---

## ✅ SCRIPTS VALIDES (GARDÉS)

**Ces scripts restent dans session128/ car créés APRÈS correction :**

1. `import_to_events_MASTERPLAN.py` - Import correct dans table `events`
2. `update_event_families_scores.py` - Mise à jour scores Session 123
3. `validate_infrastructure.py` - Validation Phase 1 (5/5 tests)
4. `validate_mapping_s127.py` - Validation Phase 2 (2/2 tests)
5. `analyze_scores_sources.py` - Analyse sources scores
6. `check_event_families_format.py` - Check format event_key
7. `check_event_families_structure.py` - Check structure table

---

## 📊 MÉTRIQUES SESSION 128

### **Avant Correction**
- Scripts créés : 40+
- Tests échoués : Tous (MAE 19-26 pips)
- Temps perdu : ~2h

### **Après Correction**
- Scripts valides : 7
- Tests réussis : 7/7 (100%)
- **MAE Session 115 : 0.35 pips** ✅✅✅

---

## 🎓 LEÇONS APPRISES

1. **Toujours valider infrastructure AVANT développer** 🎯
   - Un script de référence validé (Session 115) aurait détecté le problème immédiatement
   - 2h de développement perdues car pas de validation initiale

2. **Vérifier structure DB correspond au MASTER_PLAN** 🔍
   - DB peut avoir été modifiée sans documentation
   - Toujours comparer structure actuelle vs attendue

3. **Ne jamais faire confiance aux noms de tables** ⚠️
   - `economic_events` semblait correct mais n'était pas la bonne table
   - `events` est la table MASTER_PLAN

4. **Tests de référence sont critiques** ✅
   - Session 115 ORIGINAL (MAE 0.35) a permis de détecter le problème
   - Sans référence validée, impossible de savoir si résultats corrects

---

**Auteur :** André Valentin avec Claude  
**Date Archive :** 12 novembre 2025  
**Statut :** 📦 ARCHIVÉ - NE PAS UTILISER
