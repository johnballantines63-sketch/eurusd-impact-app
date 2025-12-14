# 🎯 SESSION 92.14 - ÉTAPE 1 : BASELINE - RÉSUMÉ EXÉCUTION

**Date :** 29 octobre 2025  
**Status :** ✅ Scripts prêts - En attente exécution

---

## 📦 FICHIERS CRÉÉS (3 fichiers)

```
eurusd_clean/scripts/session92.14/
├── test_baseline_planificateur.py  (320 lignes - Script principal)
├── run_baseline.sh                 (Script lancement bash)
└── README_ETAPE1.md                (Documentation complète)
```

---

## 🚀 EXÉCUTION (Simple - 2 commandes)

### Terminal :

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session92.14

chmod +x run_baseline.sh

./run_baseline.sh
```

**Durée estimée :** 5-10 secondes

---

## 📊 CE QUE ÇA VA FAIRE

1. **Charger événements HIGH** pour 4 dates (query SQL exacte Planificateur)
2. **Calculer prédictions** avec formules S51-55 (réplication exacte)
3. **Comparer vs réels** MT5 (51.7, 49.9, 34.0, 24.6 pips)
4. **Calculer MAE baseline** (métrique clé)
5. **Créer CSV résultats** (`baseline_results.csv`)

---

## ✅ RÉSULTATS ATTENDUS

### Console affichera :

```
================================================================================
RÉSUMÉ BASELINE (4 dates)
================================================================================

📊 MÉTRIQUES GLOBALES :
   MAE (Mean Absolute Error)  : X.XX pips  ← VALEUR CLÉ
   RMSE (Root Mean Square)    : X.XX pips
   ...

📋 TABLEAU RÉCAPITULATIF :

Date         Prédit     Réel       Erreur     %        Éval        
----------------------------------------------------------------------
2025-09-11     XX.X p    51.7 p      X.X p    X.X%   ✅ Excellent
2025-01-15     XX.X p    49.9 p      X.X p    X.X%   ✅ Bon
2025-05-13     XX.X p    34.0 p      X.X p    X.X%   ⚠️ Acceptable
2025-07-15     XX.X p    24.6 p      X.X p    X.X%   ❌ Insuffisant
----------------------------------------------------------------------
MOYENNE                               X.XX p          BASELINE
```

### Fichier créé :

**`baseline_results.csv`** avec toutes les métriques par date

---

## 🎯 CE QU'ON ATTEND

**Hypothèses (à confirmer) :**
- MAE baseline : **5-15 pips**
- Date 11.09 : **Erreur < 5 pips** (cas validé S92.13)
- Date 07.15 : **Erreur > 10 pips** (outlier géopolitique)

**Interprétation :**

| MAE Baseline | Signification | Implication ÉTAPE 2 |
|--------------|---------------|---------------------|
| < 10 pips | ✅ Système déjà EXCELLENT | Amélioration difficile |
| 10-20 pips | ✅ Système BON | Amélioration possible |
| > 20 pips | ⚠️ Système MOYEN | Vérifier méthodologie |

---

## 📋 ACTION ANDRÉ

### 1. Exécuter script

```bash
./run_baseline.sh
```

### 2. Vérifier résultats

- ✅ 4/4 dates testées ?
- ✅ MAE baseline affiché ?
- ✅ Fichier `baseline_results.csv` créé ?

### 3. Partager avec Claude

**Copier-coller UNIQUEMENT la section finale :**

```
================================================================================
RÉSUMÉ BASELINE (4 dates)
================================================================================

📊 MÉTRIQUES GLOBALES :
   MAE (Mean Absolute Error)  : X.XX pips
   ...

📋 TABLEAU RÉCAPITULATIF :
[tout le tableau]
```

**OU envoyer fichier :** `baseline_results.csv`

---

## 🔧 DÉPANNAGE RAPIDE

### Erreur : "Base de données introuvable"

```bash
# Vérifier
ls -lh ../../../fx_impact_app/data/warehouse.duckdb

# Si absent → problème chemin
```

### Erreur : "Module not found"

```bash
# Vérifier Python
python3 --version  # Doit être 3.8+

# Vérifier modules
pip3 list | grep -E "(pandas|duckdb|sklearn)"
```

### Script ne démarre pas

```bash
# Rendre exécutable
chmod +x run_baseline.sh

# OU exécuter directement
python3 test_baseline_planificateur.py
```

---

## ⏭️ APRÈS ÉTAPE 1

**Si succès :**

→ Claude passe à **ÉTAPE 2** : Créer modules amplitude
   - `amplitude_analysis.py` (300+ lignes)
   - `formulas_validated_v2.py` (200+ lignes)

→ Puis **ÉTAPE 3** : Tester amélioration vs baseline

**Budget tokens restant :** ~74,000 tokens (39%)

---

## 📞 QUESTIONS FRÉQUENTES

**Q : Puis-je tester sur d'autres dates ?**
A : Oui, modifier `TEST_DATES` dans le script (ligne ~40)

**Q : Que faire si MAE > 20 pips ?**
A : Vérifier que script réplique bien Planificateur (comparer résultats manuels)

**Q : Le CSV contient quoi exactement ?**
A : Toutes métriques par date (scores, surprises, impacts, erreurs)

---

**✅ TOUT EST PRÊT POUR EXÉCUTION !**

**Action André :** `./run_baseline.sh` puis partager résultats

---

_Session 92.14 - ÉTAPE 1 Baseline_  
_29 octobre 2025_  
_"Mesurer avant d'améliorer" 📊_
