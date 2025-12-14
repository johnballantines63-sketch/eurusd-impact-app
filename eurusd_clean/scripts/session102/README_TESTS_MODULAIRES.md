# TESTS MODULAIRES - MÉTHODOLOGIE VALIDATION

## 📋 Vue d'Ensemble

Scripts modulaires pour valider la méthodologie complète sur le cas référence 11.09.2025.

**Avantages :**
- ✅ Debug isolé de chaque étape
- ✅ Passage de données entre steps via JSON
- ✅ Relance partielle possible
- ✅ Logs clairs et structurés

---

## 🚀 Utilisation Rapide

### Lancer Tous les Tests en Séquence

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session102

chmod +x run_tests_modulaires.sh
./run_tests_modulaires.sh
```

**Durée totale : ~15 secondes**

---

## 🔧 Tests Individuels (Debug)

### STEP 1 : Détection Tendance

```bash
python3 test_step1_detection_tendance.py
```

**Teste :**
- Détection TOP-N sur 14 jours
- Identification dernière inversion
- Calcul métriques (durée, amplitude, R²)

**Output :** `step1_output.json`

---

### STEP 2 : Chargement Événements

```bash
python3 test_step2_chargement_events.py
```

**Prérequis :** `step1_output.json`

**Teste :**
- Query SQL avec GROUP BY (anti-doublons)
- Validation nombre événements
- Détection doublons CPI/Jobless

**Output :** `step2_output.json`

---

### STEP 3 : Calcul Impact Baseline

```bash
python3 test_step3_calcul_baseline.py
```

**Prérequis :** `step2_output.json`

**Teste :**
- Ajustement score selon surprise
- Calcul impact avec amp=2.5 (fixe)
- Formules S51-55

**Output :** `step3_output.json`

---

### STEP 4 : Mesure Impact Réel

```bash
python3 test_step4_mesure_impact_reel.py
```

**Prérequis :** `step3_output.json`

**Teste :**
- Chargement prix 60 min après événement
- Calcul max-min (pas end-start)
- Comparaison avec baseline

**Output :** `step4_output.json`

---

### STEP 5 : Amplification Optimale

```bash
python3 test_step5_amp_optimal.py
```

**Prérequis :** `step4_output.json`

**Teste :**
- Optimisation scipy
- Calcul amp_optimal
- Facteur correction vs baseline

**Output :** `step5_output.json`

---

## 📊 Fichiers Générés

### Format JSON

Chaque step génère un fichier JSON contenant :
- Données du step précédent (héritage)
- Nouveaux résultats calculés
- Métriques de validation

**Exemple `step5_output.json` (final) :**

```json
{
  "event_date": "2025-09-11",
  "trend": {
    "duration_hours": 54.5,
    "amplitude_pips": 114.3,
    "r_squared": 0.638
  },
  "events": {
    "count": 11,
    "score_mean": 44.3
  },
  "baseline": {
    "score_adjusted": 84.2,
    "amplification": 2.5,
    "impact_pips": 56.3
  },
  "impact_real": {
    "impact_pips": 44.6
  },
  "amp_optimal": {
    "value": 1.982,
    "correction_factor": 0.793
  }
}
```

---

## 🐛 Debug d'un Step Spécifique

### Exemple : Step 2 échoue

```bash
# Relancer juste step 2 (step1_output.json doit exister)
python3 test_step2_chargement_events.py

# Lire output pour debug
cat step2_output.json | python3 -m json.tool
```

### Exemple : Modifier Step 3 et tester

```bash
# 1. Modifier test_step3_calcul_baseline.py
nano test_step3_calcul_baseline.py

# 2. Relancer depuis step 3 (step2_output.json doit exister)
python3 test_step3_calcul_baseline.py
python3 test_step4_mesure_impact_reel.py
python3 test_step5_amp_optimal.py
```

---

## ✅ Validation Complète

**Critères de succès :**

```
STEP 1 ✅
  - Tendance détectée
  - Durée 54±5h
  - Amplitude 95±30 pips
  
STEP 2 ✅
  - 8-12 événements chargés
  - Pas de doublons CPI (≤9)
  
STEP 3 ✅
  - Score ajusté correctement
  - Impact baseline calculé
  
STEP 4 ✅
  - Prix chargés (60 points M1)
  - Impact réel mesuré
  
STEP 5 ✅
  - amp_optimal trouvé
  - Erreur < 5 pips
```

**Si tous les critères passent :**

```
✅✅ MÉTHODOLOGIE VALIDÉE
→ Prêt pour calibration 44 dates
```

---

## 🔄 Workflow Complet

```
1. Lancer tests modulaires
   ./run_tests_modulaires.sh
   
2. Si échec :
   - Identifier step échoué
   - Relancer step isolé avec logs
   - Corriger problème
   - Relancer depuis ce step
   
3. Si succès :
   - Analyser step5_output.json
   - Vérifier amp_optimal vs baseline
   - Lancer calibration 44 dates
```

---

## 📚 Scripts Validés

**✅ Base Solide Production :**
- `app/utils/detect_trend_optimized.py`
- `fx_impact_app/src/formulas_validated.py`

**✅ Tests Validés :**
- `test_step1_detection_tendance.py`
- `test_step2_chargement_events.py`
- `test_step3_calcul_baseline.py`
- `test_step4_mesure_impact_reel.py`
- `test_step5_amp_optimal.py`
- `run_tests_modulaires.sh`

**⏳ À Valider (Prochaine étape) :**
- `recalculate_metrics_optimized.py` (44 dates)
- `calibrate_amp_formula_optimized.py` (formule finale)
- `run_calibration_optimized.sh` (lanceur)

---

## 🎯 Prochaine Action

**Après validation tests modulaires :**

```bash
# Lancer calibration 44 dates
./run_calibration_optimized.sh
```

**Objectif :** Trouver formule `amp = f(R², amplitude, durée)`

---

**Auteur :** André Valentin  
**Date :** 31 octobre 2025 - Session 103  
**Status :** ✅ Validé cas référence 11.09.2025
