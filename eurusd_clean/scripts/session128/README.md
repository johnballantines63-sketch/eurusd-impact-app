# SESSION 128 - TESTS NON-RÉGRESSION

**Date :** 12 novembre 2025  
**Objectif :** Valider que mapping variantes Session 127 n'a pas cassé le système  
**Statut :** ✅ Tests créés - En attente exécution

---

## 🎯 OBJECTIF

Valider solidité système après Session 127 (mapping variantes) avant intégration Planificateur V2.5.

**Critères succès :**
- ✅ 100% scores retrouvés avec nouvelle fonction
- ✅ Pipeline calibration intact
- ✅ Cas référence 11 septembre : MAE < 5 pips

---

## 📂 FICHIERS CRÉÉS

### Tests Principaux
```
test_1_mapping_variants_non_regression.py
  → Test 20 cas + comparaison baseline
  → Mesure amélioration vs avant Session 127
  
test_2_pipeline_calibration_non_regression.py
  → Validation fonction amp(R²) intacte
  → Vérification imports et dépendances
  
test_3_reference_case_11_sept.py
  → Workflow complet 11 septembre 2025
  → Validation MAE < 5 pips
```

### Script Lancement
```
run_all_tests.py
  → Exécute 3 tests en séquence
  → Génère rapport consolidé
```

---

## 🚀 UTILISATION

### Exécution Complète (Recommandé)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session128

# Lancer tous tests
python run_all_tests.py
```

**Durée estimée :** 5-10 minutes  
**Output :** `RAPPORT_TESTS_NON_REGRESSION.md`

---

### Exécution Individuelle

```bash
# Test 1 : Mapping variantes (20 cas)
python test_1_mapping_variants_non_regression.py

# Test 2 : Pipeline calibration
python test_2_pipeline_calibration_non_regression.py

# Test 3 : Cas référence 11 septembre
python test_3_reference_case_11_sept.py
```

---

## 📊 TESTS DÉTAILLÉS

### Test 1 : Mapping Variantes (20 cas)

**Objectif :** Valider `get_empirical_score_with_variants()` vs baseline

**Cas testés :**
- 10 HIGH importance (variantes MoM/YoY/QoQ + direct + international)
- 5 MEDIUM importance (variantes MoM + direct)
- 3 LOW importance (direct + variantes)
- 2 cas limites (event/pays inexistants)

**Métriques :**
- Taux succès nouvelle fonction vs baseline
- Nombre améliorations (scores trouvés par S127)
- Nombre régressions (scores perdus)
- Scores corrects (vs attendus)

**Critères succès :**
- [ ] 100% scores attendus retrouvés
- [ ] 0 régressions
- [ ] Amélioration mesurable (+X scores)

---

### Test 2 : Pipeline Calibration

**Objectif :** Valider pipeline Sessions 125-126 intact

**Tests :**
1. Fonction `calculate_amplification_from_r2()` intacte
2. Métriques référence disponibles (CPI, NFP, Fed)
3. Imports et dépendances OK

**Métriques référence :**
```
CPI          : MAE 0.82 pips  (+95% amélioration)
NFP          : MAE 19.5 pips  (+88% amélioration)
Fed Decision : MAE 34.8 pips  (+59% amélioration)
```

**Critères succès :**
- [ ] Fonction amp(R²) calcule correctement (6 cas)
- [ ] Imports OK (utils_mapping, utils_mapping_variants)
- [ ] Métriques référence chargées

⚠️ **Note :** Test 2 valide structure, exécution pipeline complète recommandée manuellement

---

### Test 3 : Cas Référence 11 Septembre

**Objectif :** Workflow complet sur cas critique

**Workflow :**
1. Charger événements 11 septembre (DB)
2. Calculer scores (mapping variantes)
3. Calculer impact prédit (formule simplifiée)
4. Comparer avec impact réel MT5 : 56.2 pips

**Critères succès :**
- [ ] 2+ événements chargés (CPI, Jobless)
- [ ] 100% scores retrouvés
- [ ] Impact prédit : 44-58 pips (±5 pips)
- [ ] MAE < 5 pips

⚠️ **Note :** Test 3 utilise formule simplifiée. Version complète nécessite modules Session 111-115.

---

## 📈 INTERPRÉTATION RÉSULTATS

### Succès Complet ✅✅✅
```
3/3 tests réussis
→ Session 127 validée
→ Prêt ÉTAPE 2 (Intégration Planificateur V2.5)
```

### Succès Partiel ⚠️
```
2/3 tests réussis
→ Analyser test échoué
→ Corriger si nécessaire
→ Relancer validation
```

### Échec ❌
```
<2/3 tests réussis
→ Problèmes critiques détectés
→ Vérifier Session 127 (mapping variantes)
→ Vérifier imports et dépendances
```

---

## 🔧 DÉPANNAGE

### Erreur Import utils_mapping_variants

**Problème :**
```
ImportError: No module named 'utils_mapping_variants'
```

**Solution :**
```bash
# Vérifier fichier existe
ls ../session127/utils_mapping_variants.py

# Vérifier path dans script
sys.path.insert(0, str(Path(__file__).parent.parent / 'session127'))
```

---

### Erreur Import utils_mapping

**Problème :**
```
ImportError: No module named 'utils_mapping'
```

**Solution :**
```bash
# Vérifier fichier existe
ls ../session126/utils_mapping.py

# Vérifier path dans script
sys.path.insert(0, str(Path(__file__).parent.parent / 'session126'))
```

---

### Scores Manquants

**Problème :**
```
❌ Fichier scores introuvable
```

**Solution :**
```bash
# Vérifier chemin
ls ../session123/validation_results/event_families_eodhd_empirical.csv

# Si manquant, copier depuis autre session
cp ../session124/[...]/event_families_eodhd_empirical.csv ../session123/validation_results/
```

---

### Database Introuvable

**Problème :**
```
❌ Database introuvable
```

**Solution :**
```bash
# Vérifier chemin
ls ../../data/warehouse.duckdb

# Vérifier path dans script
db_path = Path(__file__).parents[2] / "data" / "warehouse.duckdb"
```

---

## 📝 PROCHAINES ÉTAPES

### Si Tests Réussis ✅

**ÉTAPE 2 : Intégration Planificateur V2.5**
1. Intégrer `get_empirical_score_with_variants()` dans DataService
2. Intégrer `calculate_amplification_from_r2()` dans AmplificationCalculator
3. Ajouter UI mode fixe/dynamique
4. Tests interface (3+ dates)

**Durée estimée :** 2-3h

---

### Si Tests Échoués ❌

**Actions correctives :**
1. Analyser rapport `RAPPORT_TESTS_NON_REGRESSION.md`
2. Identifier cause échec
3. Corriger (mapping, imports, données)
4. Relancer tests
5. Itérer jusqu'à succès

---

## 📚 RÉFÉRENCES

**Documentation :**
- `../session127/TEST_RESULTS_FINAL.md` : Résultats tests Session 127
- `../../docs/PROJECT_MANAGEMENT/99_SESSIONS/SESSION_128_HANDOFF.md` : Handoff S127→S128
- `../../docs/PROJECT_MANAGEMENT/01_VISION/MASTER_PLAN.md` : Vision globale

**Modules clés :**
- `../session127/utils_mapping_variants.py` : Fonction mapping variantes
- `../session126/utils_mapping.py` : Fonctions normalisation
- `../session125/[...]/calibrate_universal_amplification.py` : Pipeline calibration

---

## ✅ CHECKLIST VALIDATION

### Avant Exécution
- [ ] Python 3.8+ installé
- [ ] Database warehouse.duckdb accessible
- [ ] Fichier scores CSV accessible
- [ ] utils_mapping_variants.py accessible
- [ ] utils_mapping.py accessible

### Après Exécution
- [ ] Rapport généré : `RAPPORT_TESTS_NON_REGRESSION.md`
- [ ] 3/3 tests réussis
- [ ] Métriques validées (améliorations, MAE)
- [ ] Prêt ÉTAPE 2

---

**Auteur :** André Valentin avec Claude  
**Date :** 12 novembre 2025  
**Session :** 128 - ÉTAPE 1 (Tests Non-Régression)  
**Statut :** ✅ Tests créés - En attente exécution
