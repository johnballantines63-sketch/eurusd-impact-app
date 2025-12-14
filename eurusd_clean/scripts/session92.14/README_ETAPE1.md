# SESSION 92.14 - ÉTAPE 1 : BASELINE

**Date :** 29 octobre 2025  
**Objectif :** Mesurer MAE du Planificateur ACTUEL (formules S51-55 seules)

---

## 📋 FICHIERS

```
session92.14/
├── test_baseline_planificateur.py  (Script principal)
├── run_baseline.sh                 (Lancement rapide)
├── README.md                       (Ce fichier)
└── baseline_results.csv            (Résultats - créé après exécution)
```

---

## 🚀 EXÉCUTION

### Méthode 1 : Script bash (recommandé)

```bash
cd eurusd_clean/scripts/session92.14
chmod +x run_baseline.sh
./run_baseline.sh
```

### Méthode 2 : Python direct

```bash
cd eurusd_clean/scripts/session92.14
python3 test_baseline_planificateur.py
```

---

## 🎯 CE QUE FAIT LE SCRIPT

### 1. Charge événements HIGH IMPACT (4 dates)

**Query SQL EXACTE du Planificateur (ligne 208-224) :**
```sql
SELECT e.event_key, e.event_title, e.ts_utc,
       e.actual, e.estimate,
       ef.empirical_score, ef.latency_median
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key AND e.country = ef.country
WHERE DATE(e.ts_utc) = ?
    AND e.country = 'US'
    AND ef.empirical_score > 40  ← CRITÈRE HIGH IMPACT
```

### 2. Calcule prédictions avec formules S51-55

**Réplication EXACTE fonction `calculate_predictions()` du Planificateur :**

```python
# Score moyen
base_score_avg = events['empirical_score'].mean()

# Surprise max
max_surprise = max(surprises)

# Ajuster score (S55)
adjusted_score = calculate_adjusted_empirical_score(base_score_avg, max_surprise)

# Impact (S51)
impact = calculate_impact_d(
    empirical_score=adjusted_score,
    num_events=len(events),
    amplification=2.5  ← Valeur Planificateur
)
```

### 3. Compare vs impacts réels MT5

**4 dates test :**
- **2025-09-11** : Impact réel **51.7 pips** (validé S92.13)
- **2025-01-15** : Impact réel **49.9 pips**
- **2025-05-13** : Impact réel **34.0 pips**
- **2025-07-15** : Impact réel **24.6 pips** (outlier géopolitique)

### 4. Calcule MAE baseline

**Métrique clé :**
```
MAE = moyenne(|impact_prédit - impact_réel|)
```

---

## 📊 RÉSULTATS ATTENDUS

### Format output console

```
================================================================================
TEST BASELINE PLANIFICATEUR - SESSION 92.14
================================================================================

OBJECTIF : Mesurer MAE Planificateur ACTUEL (formules S51-55 seules)
MÉTHODE  : Réplication EXACTE comportement Planificateur

✅ Base de données : warehouse.duckdb
   Taille : 205.0 MB

================================================================================
TESTS BASELINE (4 dates)
================================================================================

📅 11.09.2025 CPI US
   Date : 2025-09-11
   Impact réel MT5 : 51.7 pips

   ✅ 9 événement(s) HIGH chargé(s)
      • CPI (YoY)
        Score : 44.8
        Actual : 2.50, Estimate : 2.30
        Surprise : 8.7%
      • Core CPI (YoY)
        ...

   📊 RÉSULTATS BASELINE :
      Score base moyen : 44.8
      Score ajusté     : XX.X
      Surprise max     : XX.X%
      Nombre events    : 9

   🎯 PRÉDICTION :
      Impact prédit    : XX.X pips
      Impact réel MT5  : 51.7 pips
      Erreur (MAE)     : X.X pips (X.X%)

   ✅ EXCELLENT (MAE < 5 pips)  OU  ⚠️ ACCEPTABLE  OU  ❌ INSUFFISANT

--------------------------------------------------------------------------------

[... 3 autres dates ...]

================================================================================
RÉSUMÉ BASELINE (4 dates)
================================================================================

📊 MÉTRIQUES GLOBALES :
   MAE (Mean Absolute Error)  : X.XX pips
   RMSE (Root Mean Square)    : X.XX pips
   Erreur maximale            : X.X pips
   Erreur minimale            : X.X pips

📈 ÉVALUATION BASELINE :
   ✅ BASELINE EXCELLENT (MAE < 10 pips)
   → Amélioration amplitude sera difficile à démontrer

📋 TABLEAU RÉCAPITULATIF :

Date         Prédit     Réel       Erreur     %        Éval        
----------------------------------------------------------------------
2025-09-11     XX.X p    51.7 p      X.X p    X.X%   ✅ Excellent
2025-01-15     XX.X p    49.9 p      X.X p    X.X%   ✅ Bon
2025-05-13     XX.X p    34.0 p      X.X p    X.X%   ⚠️ Acceptable
2025-07-15     XX.X p    24.6 p      X.X p    X.X%   ❌ Insuffisant
----------------------------------------------------------------------
MOYENNE                               X.XX p          BASELINE

💾 Résultats sauvegardés : baseline_results.csv

================================================================================
✅ TEST BASELINE TERMINÉ
================================================================================

PROCHAINE ÉTAPE : Intégration amélioration amplitude (ÉTAPE 2)
OBJECTIF        : MAE amélioré < X.XX pips (baseline)
```

### Fichier CSV créé

**baseline_results.csv :**
```csv
date,label,num_events,base_score,adjusted_score,max_surprise,impact_predicted,impact_real,error,error_pct
2025-09-11,11.09.2025 CPI US,9,44.8,XX.X,XX.X,XX.X,51.7,X.X,X.X
2025-01-15,01.15.2025 CPI US,8,XX.X,XX.X,XX.X,XX.X,49.9,X.X,X.X
2025-05-13,05.13.2025 CPI US,7,XX.X,XX.X,XX.X,XX.X,34.0,X.X,X.X
2025-07-15,07.15.2025 CPI US,6,XX.X,XX.X,XX.X,XX.X,24.6,X.X,X.X
```

---

## ✅ CRITÈRES SUCCÈS ÉTAPE 1

**Objectif principal :**
- ✅ Script s'exécute sans erreur
- ✅ 4/4 dates testées avec succès
- ✅ MAE baseline calculé
- ✅ Fichier CSV créé

**Valeurs attendues (hypothèse) :**
- MAE baseline : **5-15 pips** (Planificateur est déjà bon)
- Date 11.09 : **Erreur < 5 pips** (cas validé S92.13)
- Date 07.15 : **Erreur > 10 pips** (outlier géopolitique connu)

**Si MAE baseline < 10 pips :**
→ Amélioration amplitude sera DIFFICILE à démontrer (système déjà excellent)

**Si MAE baseline 10-20 pips :**
→ Amélioration amplitude a du POTENTIEL

**Si MAE baseline > 20 pips :**
→ Problème méthodologie (vérifier réplication Planificateur)

---

## 🔍 VALIDATION MÉTHODOLOGIE

### Checklist avant exécution

- [ ] Base de données `warehouse.duckdb` présente (205 MB)
- [ ] Python 3 installé avec pandas, duckdb, sklearn
- [ ] Chemins corrects (`fx_impact_app/src/formulas_validated.py` existe)
- [ ] Imports formules S51-55 fonctionnent

### Checklist après exécution

- [ ] 4/4 dates testées
- [ ] MAE baseline calculé
- [ ] Fichier `baseline_results.csv` créé
- [ ] Résultats cohérents (pas d'erreurs aberrantes)

---

## 📞 AIDE DÉBOGAGE

### Erreur : "Base de données introuvable"

```bash
# Vérifier chemin
ls -lh ../../../fx_impact_app/data/warehouse.duckdb

# Si absent, copier depuis backup
cp /path/to/backup/warehouse.duckdb ../../../fx_impact_app/data/
```

### Erreur : "Module 'formulas_validated' not found"

```python
# Vérifier import
python3 -c "import sys; sys.path.insert(0, '../../../fx_impact_app/src'); from formulas_validated import calculate_impact_d; print('OK')"
```

### Erreur : "Aucun événement HIGH trouvé"

→ Vérifier dates dans DB :
```sql
SELECT DATE(ts_utc), COUNT(*) 
FROM events e
JOIN event_families ef ON e.event_key = ef.event_key
WHERE e.country = 'US' 
  AND ef.empirical_score > 40
  AND DATE(ts_utc) IN ('2025-09-11', '2025-01-15', '2025-05-13', '2025-07-15')
GROUP BY DATE(ts_utc);
```

---

## 🎯 PROCHAINES ÉTAPES

**Si ÉTAPE 1 réussie :**

→ **ÉTAPE 2** : Créer modules amplitude
   - `amplitude_analysis.py` (analyse prix pure)
   - `formulas_validated_v2.py` (wrapper complet)

→ **ÉTAPE 3** : Tester avec amélioration amplitude

→ **ÉTAPE 4** : Comparer baseline vs amélioré

---

**ÉTAPE 1 prête à être exécutée !** ✅

**Action André :** Lancer `./run_baseline.sh` et partager résultats
