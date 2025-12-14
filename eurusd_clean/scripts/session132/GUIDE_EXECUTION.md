# 🧪 GUIDE EXÉCUTION TESTS - SESSION 132

**Date :** 13 novembre 2025  
**Objectif :** Valider module `doublewave_prediction.py`

---

## 📋 SCRIPTS DE TEST CRÉÉS

### **1. verify_module.py** (Vérification syntaxique)
**Objectif :** Vérifier import et structure de base  
**Durée :** < 1 seconde  
**Prérequis :** Aucun (pas de DB)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session132/verify_module.py
```

**Attendu :**
```
✅ Module importé avec succès
✅ PatternClassifier présente
✅ InclusionCriteria présente
✅ predict_doublewave_overlap présente
✅ Cas liste vide : exclusion correcte
✅ Cas 0 events scorés : exclusion correcte
✅ Cas score < 50 : exclusion correcte
✅ Cas cascade périphérique : exclusion correcte
✅ Cas overlap standard valide : prédiction correcte

✅ TOUS LES TESTS SYNTAXIQUES PASSÉS
```

---

### **2. test_quick.py** (Tests données simulées)
**Objectif :** Valider logique avec 6 cas simulés  
**Durée :** < 5 secondes  
**Prérequis :** Aucun (pas de DB)

```bash
python scripts/session132/test_quick.py
```

**Attendu :**
```
TEST 1 : Overlap Standard
✅ TEST 1 RÉUSSI - Overlap standard correctement prédit

TEST 2 : Cascade Périphériques
✅ TEST 2 RÉUSSI - Cascade correctement exclu

TEST 3 : 0 Events Scorés
✅ TEST 3 RÉUSSI - 0 events scorés correctement exclu

TEST 4 : Score Trop Faible
✅ TEST 4 RÉUSSI - Score faible correctement exclu

TEST 5 : Superposition Simulée
✅ TEST 5 RÉUSSI - Superposition détectée

TEST 6 : Trop Peu d'Events
✅ TEST 6 RÉUSSI - Trop peu d'events correctement exclu

Tests exécutés : 6
  ✅ Réussis : 6 (100%)
  ❌ Échoués : 0 (0%)

🎉 TOUS LES TESTS RAPIDES PASSÉS ✅
```

---

### **3. test_doublewave_prediction.py** (Tests DB réelle)
**Objectif :** Valider sur 8 cas Session 131  
**Durée :** 10-30 secondes  
**Prérequis :** ✅ DB warehouse.duckdb opérationnelle

```bash
python scripts/session132/test_doublewave_prediction.py
```

**Attendu :**
```
GROUPE 1 : OVERLAP STANDARDS
  - 2023-02-03 : ✅ Prédit (amp 0.1201)
  - 2023-03-22 : ✅ Prédit (amp 0.1201)
  - 2025-02-03 : ✅ Prédit (amp 0.1201)

GROUPE 2 : OVERLAP SUPERPOSITION
  - 2025-09-11 : ✅ Prédit (amp 0.0128)

GROUPE 3 : CASCADE
  - 2023-03-07 : ✅ Exclu (cascade)
  - 2023-03-10 : ✅ Exclu (cascade)
  - 2023-07-12 : ✅ Exclu (cascade)
  - 2025-04-04 : ✅ Exclu (cascade)

Tests exécutés : 8
  ✅ Réussis : 8 (100%)

🎉 TOUS LES TESTS PASSÉS - MODULE VALIDÉ ✅
```

---

## 🚀 ORDRE D'EXÉCUTION RECOMMANDÉ

### **ÉTAPE 1 : Vérification syntaxique** (obligatoire)

```bash
python scripts/session132/verify_module.py
```

**Si ça échoue :**
- Module a erreur syntaxe Python
- Problème imports
- → Corriger avant continuer

**Si ça passe :**
- ✅ Module importable
- ✅ Structure correcte
- → Passer ÉTAPE 2

---

### **ÉTAPE 2 : Tests rapides** (recommandé)

```bash
python scripts/session132/test_quick.py
```

**Si ça échoue :**
- Logique critères incorrecte
- Amplifications incorrectes
- → Corriger module

**Si ça passe :**
- ✅ Logique validée
- ✅ 6/6 cas simulés OK
- → Passer ÉTAPE 3

---

### **ÉTAPE 3 : Tests DB réelle** (final)

```bash
python scripts/session132/test_doublewave_prediction.py
```

**Si ça échoue :**
- Problème chargement events DB
- Timestamps incorrects
- Scores manquants
- → Analyser échecs

**Si ça passe :**
- ✅ 8/8 cas Session 131 validés
- ✅ MODULE PRODUCTION-READY
- → Session 132 COMPLÉTÉE

---

## ⚠️ PROBLÈMES POTENTIELS

### **Problème 1 : Import Error**

```
ModuleNotFoundError: No module named 'core'
```

**Solution :**
```bash
# Vérifier que src/ est dans PYTHONPATH
export PYTHONPATH=/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/src:$PYTHONPATH

# Ou exécuter depuis racine projet
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
python scripts/session132/verify_module.py
```

---

### **Problème 2 : DB Non Trouvée**

```
duckdb.Error: IO Error: Cannot open file
```

**Solution :**
```bash
# Vérifier chemin DB
ls -lh /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb

# Si DB absente, tests rapides suffisent pour validation logique
python scripts/session132/test_quick.py
```

---

### **Problème 3 : Dates Manquantes**

```
❌ TEST ÉCHOUÉ - 0 événements chargés
```

**Causes possibles :**
- Timestamp incorrect (timezone)
- Période pas dans DB
- Events filtrés (importance, country)

**Actions :**
1. Vérifier date existe dans DB
2. Ajuster timestamp (± 30 min)
3. Documenter dans PREDICTION_DECISIONS.md

---

## 📊 MÉTRIQUES ATTENDUES

**Après ÉTAPE 1 :**
- Import : ✅ OK
- Constantes : ✅ Correctes (150, 350, 0.1201, 0.0128)
- 5 tests basiques : ✅ 5/5

**Après ÉTAPE 2 :**
- 6 cas simulés : ✅ 6/6 (100%)
- Overlap standards : ✅ Prédit (amp 0.1201)
- Cascade : ✅ Exclu
- Superposition : ✅ Détectée

**Après ÉTAPE 3 :**
- 8 cas Session 131 : ✅ 8/8 (100%)
- Overlap standards : 3/3 ✅
- Overlap superposition : 1/1 ✅
- Cascade : 4/4 exclu ✅

---

## ✅ CHECKLIST VALIDATION

- [ ] ÉTAPE 1 passée (verify_module.py)
- [ ] ÉTAPE 2 passée (test_quick.py)
- [ ] ÉTAPE 3 passée (test_doublewave_prediction.py) OU documenté si dates manquantes
- [ ] Amplifications correctes (0.1201, 0.0128)
- [ ] Cascade exclus systématiquement
- [ ] Raisons exclusion documentées

**Si TOUS cochés :**
- ✅ Module validé
- ✅ Session 132 objectif ÉTAPE 1-2 ATTEINT
- → Créer PREDICTION_DECISIONS.md (ÉTAPE 3)
- → Rapport final Session 132

---

## 🎯 ACTIONS ANDRÉ

### **MAINTENANT (5 minutes) :**

1. **Ouvrir Terminal**
   ```bash
   cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean
   ```

2. **Exécuter ÉTAPE 1** (vérification syntaxique)
   ```bash
   python scripts/session132/verify_module.py
   ```

3. **Copier-coller résultat complet ici**
   - Si ✅ → Passer ÉTAPE 2
   - Si ❌ → Analyser erreurs ensemble

---

### **ENSUITE (2 minutes) :**

4. **Exécuter ÉTAPE 2** (tests rapides)
   ```bash
   python scripts/session132/test_quick.py
   ```

5. **Copier-coller résultat complet**
   - Si 6/6 ✅ → Passer ÉTAPE 3
   - Si échecs → Corriger module

---

### **FINALEMENT (10 minutes) :**

6. **Exécuter ÉTAPE 3** (tests DB)
   ```bash
   python scripts/session132/test_doublewave_prediction.py
   ```

7. **Analyser résultats**
   - Si 8/8 ✅ → MODULE VALIDÉ
   - Si échecs → Documenter cas problématiques

---

## 📝 APRÈS TESTS

**Si validation complète :**
1. Créer `PREDICTION_DECISIONS.md` (documentation décisions)
2. Créer `SESSION_132_RAPPORT_FINAL.md`
3. Mettre à jour `MASTER_PLAN.md`
4. Créer `SESSION_133_HANDOFF.md`

**Si validation partielle :**
1. Documenter échecs dans README
2. Analyser causes (DB, timestamps, scores)
3. Décider : corriger OU accepter limites documentées

---

**Prêt à tester ?** 🚀

Exécute la commande ÉTAPE 1 et colle-moi le résultat complet.
