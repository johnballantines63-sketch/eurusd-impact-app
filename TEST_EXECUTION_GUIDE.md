# 🧪 GUIDE D'EXÉCUTION DES TESTS - SESSION 11

**Date :** 18 octobre 2025  
**Objectif :** Valider la logique v9-CLEAN avant correction du code

---

## 📋 TESTS CRÉÉS

### 1️⃣ `test_v9_formula_validation.py` ⭐ **EXÉCUTER EN PREMIER**

**Objectif :** Vérifier que la formule v9-CLEAN est correctement implémentée

**Ce qu'il teste :**
- ✅ Formule v9-CLEAN (1 événement) : `impact = -7.08 + 0.419 × score`
- ✅ Formule v9-MULTI (≥2 événements) : `impact = -10.47 + 0.477 × score`
- ✅ Gestion des scores NULL
- ✅ Différence entre v9-CLEAN et v9-MULTI
- ✅ Cas réel du 11 septembre 2025

**Durée estimée :** 5 secondes

**Commande :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 test_v9_formula_validation.py
```

**Résultat attendu :**
```
✅ TOUS LES TESTS PASSENT
✅ La formule v9-CLEAN est correctement implémentée
```

---

### 2️⃣ `test_vectorial_logic_11sept.py` ⭐⭐⭐ **TEST PRINCIPAL**

**Objectif :** Valider la logique de somme vectorielle

**Ce qu'il teste :**
1. Calcul des impacts individuels avec v9-MULTI
2. Application des directions selon les surprises
3. Somme vectorielle des impacts
4. Comparaison avec l'impact réel MT5 (43.4 pips)
5. Analyse des contributions de chaque événement
6. Comparaison approche vectorielle vs approche actuelle

**Durée estimée :** 10 secondes

**Commande :**
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC
python3 test_vectorial_logic_11sept.py
```

**Résultat attendu :**

Le script va afficher un rapport détaillé avec :
- Impact combiné (somme vectorielle)
- Erreur vs MT5
- Direction correcte ou non
- Comparaison des deux approches
- Recommandations

---

## 🎯 ORDRE D'EXÉCUTION

### Étape 1 : Test simple de la formule (5 sec)

```bash
python3 test_v9_formula_validation.py
```

**Si ce test ÉCHOUE :**
- ❌ La formule v9-CLEAN n'est pas correctement implémentée
- 🔧 Action : Vérifier `fx_impact_app/src/forecaster_mvp.py`
- ⏸️ NE PAS continuer tant que ce test ne passe pas

**Si ce test PASSE :**
- ✅ La formule v9-CLEAN est correcte
- ➡️ Passer à l'étape 2

---

### Étape 2 : Test logique vectorielle (10 sec)

```bash
python3 test_vectorial_logic_11sept.py
```

**Ce test va déterminer :**

#### Scénario A : Erreur < 50% ✅

```
Impact combiné : +110 pips
Impact réel MT5 : +43.4 pips
Erreur : +67 pips (+154%)
```

**Interprétation :**
- La somme vectorielle **SUREstime** l'impact réel
- C'est le comportement **ATTENDU** selon la théorie
- La formule v9-CLEAN prédit des impacts **moyens** historiques
- Un événement majeur peut déclencher un effet **amplificateur**
- **Conclusion :** La logique est CORRECTE, mais il faut un **facteur de correction**

**Action recommandée :**
- ✅ Implémenter la somme vectorielle dans le code
- 🔧 Ajouter un facteur de correction global (ex: × 0.4)
- 🔧 Ou pondérer les événements par importance (CPI > Jobless Claims)

---

#### Scénario B : Erreur 50-100% ⚠️

```
Impact combiné : +70 pips
Impact réel MT5 : +43.4 pips
Erreur : +27 pips (+62%)
```

**Interprétation :**
- La somme vectorielle est dans l'ordre de grandeur
- Erreur acceptable pour prédiction de marché (R² = 0.264)
- Direction probablement correcte

**Action recommandée :**
- ✅ Implémenter la somme vectorielle dans le code
- ⚠️ Ajuster les scores empiriques (peut-être légèrement surestimés)
- 💡 Considérer un facteur de correction léger (× 0.6-0.8)

---

#### Scénario C : Erreur > 150% ❌

```
Impact combiné : +200 pips
Impact réel MT5 : +43.4 pips
Erreur : +157 pips (+362%)
```

**Interprétation :**
- La somme vectorielle donne un résultat aberrant
- Problème possible dans :
  - Les scores empiriques (trop élevés)
  - Les directions (inversées ?)
  - La formule v9-CLEAN elle-même

**Action recommandée :**
- ❌ NE PAS implémenter la somme vectorielle en l'état
- 🔍 Revoir les scores empiriques (vérifier la base de données)
- 🔍 Vérifier la fonction `get_event_direction()`
- 🔍 Valider la formule v9-CLEAN sur d'autres cas

---

#### Scénario D : Direction incorrecte ❌

```
Impact combiné : -80 pips (DOWN)
Impact réel MT5 : +43.4 pips (UP)
```

**Interprétation :**
- La somme vectorielle prédit la **mauvaise direction**
- Problème critique dans :
  - La fonction `get_event_direction()`
  - Le calcul des surprises
  - Le mapping famille → sentiment

**Action recommandée :**
- ❌ NE PAS implémenter la somme vectorielle
- 🔧 CORRIGER PRIORITAIREMENT la fonction `get_event_direction()`
- 🔍 Vérifier le calcul des surprises (actual - forecast)
- 🧪 Re-tester après correction

---

## 📊 INTERPRÉTATION DES RÉSULTATS

### Comparaison des approches

Le test va comparer :

**Approche actuelle (individuelle) :**
- Compare chaque événement séparément au mouvement global
- Erreur moyenne : ~37% (sous-estimation systématique)
- Problème : mathématiquement incorrect

**Approche vectorielle (proposée) :**
- Somme tous les événements avec leurs directions
- Erreur : variable selon les données
- Avantage : cohérent avec la physique du marché

### Critères de décision

| Erreur vectorielle | Décision |
|-------------------|----------|
| **< 50%** | ✅ Implémenter avec facteur correction |
| **50-100%** | ⚠️ Implémenter avec ajustements |
| **> 100%** | ❌ Revoir les données avant implémentation |
| **Direction incorrecte** | ❌ Corriger get_event_direction() d'abord |

---

## 🔧 APRÈS LES TESTS

### Si les tests passent ✅

**Prochaines étapes :**

1. **Analyser le rapport** généré par `test_vectorial_logic_11sept.py`
2. **Déterminer le facteur de correction** nécessaire
3. **Modifier `sequence_multi_event_timeline_v86.py`** pour implémenter la somme vectorielle
4. **Créer `sequence_multi_event_timeline_v87.py`** avec la correction
5. **Tester avec Streamlit** sur le 11 septembre 2025
6. **Valider sur d'autres dates**

### Si les tests échouent ❌

**Actions de debug :**

1. **Vérifier `forecaster_mvp.py`**
   - La fonction `predict_impact_v9_clean()` existe ?
   - Les formules sont correctes ?

2. **Vérifier les scores empiriques dans la DB**
   ```sql
   SELECT event_key, country, empirical_score 
   FROM events 
   WHERE date(ts_utc) = '2025-09-11' 
   AND time(ts_utc) = '14:30:00'
   ```

3. **Vérifier `get_event_direction()`**
   - Le mapping FAMILY_SENTIMENT est correct ?
   - Les surprises sont bien calculées ?

4. **Examiner les logs détaillés** du test

---

## 📝 FICHIERS CRÉÉS

```
test_v9_formula_validation.py        ← Test simple formule
test_vectorial_logic_11sept.py       ← Test logique vectorielle
TEST_EXECUTION_GUIDE.md              ← Ce fichier
```

---

## 🚀 COMMANDES RAPIDES

### Tout tester en une fois

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC

# Test 1 : Formule
python3 test_v9_formula_validation.py

# Test 2 : Logique vectorielle
python3 test_vectorial_logic_11sept.py
```

### Rediriger la sortie vers un fichier

```bash
python3 test_vectorial_logic_11sept.py > test_results_11sept.txt 2>&1
cat test_results_11sept.txt
```

---

## 💡 POINTS CLÉS À SURVEILLER

### Dans le test de formule

- ✅ Tous les calculs doivent être exacts (< 0.01 pips de différence)
- ✅ La différence v9-CLEAN vs v9-MULTI doit être ~4.7%
- ✅ Les scores NULL doivent retourner None

### Dans le test de logique vectorielle

- 🎯 La **direction** prédite (UP/DOWN) doit être correcte
- 📊 L'**ordre de grandeur** doit être cohérent (pas 10× trop grand)
- 📉 L'**erreur** doit être analysée en contexte (R² = 0.264)
- 🔍 Les **contributions** de chaque événement doivent être logiques

---

## ⏱️ TEMPS ESTIMÉ

- **Tests :** 15 secondes
- **Lecture des résultats :** 5 minutes
- **Analyse et décision :** 10 minutes
- **TOTAL :** 15-20 minutes

---

## 📞 SI BESOIN D'AIDE

Si les résultats sont ambigus ou inattendus :

1. Copie la **sortie complète** du test
2. Note les **valeurs clés** :
   - Impact combiné prédit
   - Impact réel MT5
   - Erreur %
   - Direction correcte ou non
3. Partage ces informations pour analyse

---

**Prêt à lancer les tests ?** 🚀

```bash
python3 test_v9_formula_validation.py
```

---

**Version :** 1.0  
**Date :** 18 octobre 2025  
**Statut :** ✅ Prêt pour exécution
