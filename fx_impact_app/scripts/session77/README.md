# SESSION 77 - GRID SEARCH CALIBRATION

**Date :** 25 octobre 2025  
**Objectif :** Calibrer coefficients formule D (Sessions 51-55) sur 27 mouvements

---

## 🎯 MISSION

Calibrer 4 coefficients de la formule D via Grid Search exhaustif :
- `intercept_multi`, `coef_multi` (multi-événements, nb_events ≥ 2)
- `intercept_single`, `coef_single` (événement isolé, nb_events = 1)

**GARDER structure validée Sessions 51-55 :**
- Somme vectorielle + direction (FAMILY_SENTIMENT)
- Amplification surprise (zones 1-3)
- Correction 0.758

---

## 📊 CRITÈRES SUCCÈS

1. **Grid Search (27 mouvements)** : MAE CV < 30 pips
2. **Test 11 septembre** : MAE < 10 pips (pas de régression)
3. **Validation Session 75** : MAE < 32 pips (amélioration 50%)

---

## 🚀 EXÉCUTION

### Option 1 : Pipeline complet (RECOMMANDÉ)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

# Rendre script exécutable
chmod +x scripts/session77/run_pipeline.sh

# Exécuter pipeline complet (3 étapes)
./scripts/session77/run_pipeline.sh
```

**Durée totale :** ~3-4 minutes

---

### Option 2 : Étape par étape

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app

# ÉTAPE 1 : Grid Search Calibration (2-3 min)
python3 scripts/session77/1_grid_search_calibration.py

# ÉTAPE 2 : Test 11 septembre (< 1 min)
python3 scripts/session77/2_test_11septembre.py

# ÉTAPE 3 : Validation Session 75 (< 1 min)
python3 scripts/session77/3_validation_session75.py
```

---

## 📁 FICHIERS GÉNÉRÉS

**Après exécution, vous obtiendrez :**

```
scripts/session77/
├── calibration_results_session77.txt          # Meilleurs paramètres
├── calibration_grid_analysis.csv              # Top 100 combinaisons
├── test_11sept_results_session77.txt          # Validation cas référence
├── validation_session75_results_session77.txt # Validation 7 mouvements
└── validation_session75_details_session77.csv # Détails par mouvement
```

---

## 🔍 INTERPRÉTATION RÉSULTATS

### 1. calibration_results_session77.txt

**Consulter :**
- MAE CV (doit être < 30 pips)
- Paramètres calibrés (intercept/coef × 2)
- Comparaison avec V1 (Sessions 51-55)

**Vérifier :**
- ✅ Coefficients positifs (coef_multi, coef_single > 0)
- ❌ Si coefficients négatifs → RED FLAG, investiguer

---

### 2. test_11sept_results_session77.txt

**Consulter :**
- Impact V2 vs Réel (53 pips)
- MAE V2 (doit être < 10 pips)
- Comparaison V1 vs V2

**Interpréter :**
- MAE < 10 pips : ✅ SUCCÈS
- 10-15 pips : ⚠️ ACCEPTABLE
- > 15 pips : ❌ RÉGRESSION, investiguer

---

### 3. validation_session75_results_session77.txt

**Consulter :**
- MAE V2 global (doit être < 32 pips)
- Amélioration vs S75 original (64.9 pips)
- Comparaison V1 vs V2

**Interpréter :**
- MAE < 32 pips : ✅ OBJECTIF ATTEINT (>50% amélioration)
- 32-40 pips : ⚠️ PROCHE OBJECTIF
- > 40 pips : ❌ OBJECTIF NON ATTEINT

---

## 📊 CONFIGURATION GRID SEARCH

**Plages paramètres :**
```python
intercept_multi : -20 à 0 (pas 1)    → 21 valeurs
coef_multi      : 0.30 à 0.80 (0.05) → 11 valeurs
intercept_single: -15 à 0 (pas 1)    → 16 valeurs
coef_single     : 0.30 à 0.70 (0.05) → 9 valeurs

Total : 21 × 11 × 16 × 9 = 33,264 combinaisons
```

**Validation :** Leave-One-Out CV (27 iterations par combinaison)

**Durée estimée :** 2-3 minutes

---

## ⚠️ TROUBLESHOOTING

### Erreur : Dataset non trouvé

```
❌ Dataset non trouvé : dataset_session76_ultra.csv
```

**Solution :**
```bash
# Vérifier présence dataset
ls -lh scripts/session76/dataset_session76_ultra.csv

# Si absent, vérifier session76
ls -lh scripts/session76/
```

---

### Erreur : Base de données non trouvée

```
❌ Base de données non trouvée : warehouse.duckdb
```

**Solution :**
```bash
# Vérifier présence DB
ls -lh data/warehouse.duckdb

# Vérifier taille (doit être ~205 MB)
```

---

### Grid Search trop long (> 5 min)

**Normal si :**
- Ancienne machine (CPU lent)
- Nombreux processus en arrière-plan

**Optimisation possible :**
- Fermer applications lourdes
- Exécuter en priorité (nice -n -10)

---

### Coefficients négatifs détectés

```
⚠️ RED FLAG : coef_multi négatif (-0.123)
```

**Action :**
- STOP immédiatement
- Investiguer données
- Vérifier dataset (27 mouvements corrects ?)
- Contacter développeur si problème persiste

---

## 📞 SUPPORT

**En cas de problème :**

1. Consulter `SESSION77_RAPPORT_COMPLET.md`
2. Vérifier `MESSAGE_SESSION76_SESSION77.md`
3. Vérifier tokens utilisés (limite 190k)

**Fichiers clés :**
- `docs/MANDATORY_SESSION_RULES.md`
- `docs/project_state_new.md`
- `docs/SESSION76_RAPPORT_COMPLET.md`

---

## ✅ PROCHAINES ÉTAPES

**Après succès Session 77 :**

1. **Créer module formulas_validated_v2.py**
   - Fonction `calculate_impact_v2()`
   - Coefficients calibrés
   - Documentation complète

2. **Intégration Planificateur V2.5**
   - Importer formulas_validated_v2
   - Choix V1/V2 par utilisateur
   - Tests interface Streamlit

3. **Documentation Session 77**
   - `SESSION77_RAPPORT_COMPLET.md`
   - `MESSAGE_SESSION77_SESSION78.md`
   - Mise à jour `project_state_new.md`

---

*README Session 77 - Créé le 25 octobre 2025*
