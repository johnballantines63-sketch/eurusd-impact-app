# 🚀 SESSION 9 - EXÉCUTION ET ANALYSE

**Date de création :** 17 octobre 2025  
**Session précédente :** Session 8 (voir RAPPORT_SESSION8_FINAL.md)

---

## ⚠️ AVANT DE COMMENCER - LECTURE OBLIGATOIRE

**Lis dans CET ORDRE :**

1. **`RAPPORT_SESSION8_FINAL.md`** ⭐⭐⭐
   - Résumé complet Session 8
   - Scripts créés
   - Ce qui reste à faire

2. **`ADDENDUM_CRITIQUE_SESSION7.md`** ⭐⭐
   - Contexte du problème corrigé
   - Pourquoi le calcul était incorrect

3. **`session8_measurements/README_SESSION8_SCRIPTS.md`** ⭐
   - Guide d'utilisation des scripts
   - Résultats attendus

---

## 📋 RÉSUMÉ RAPIDE SESSION 8

### ✅ Ce qui a été fait

1. ✅ **Mesures MT5 complètes**
   - 11 septembre analysé en détail
   - Range Phase 1 : 111.5 pips

2. ✅ **Compréhension du problème**
   - Calcul individuel vs groupé
   - Cause de la sous-estimation (47%)

3. ✅ **Scripts créés**
   - `calculate_grouped_impacts.py`
   - `validate_grouped_impacts.py`

4. ✅ **Documentation complète**
   - 5 documents de mesure
   - 1 rapport final
   - 1 README utilisateur

### ⏳ Ce qui reste à faire (Session 9)

1. ⏳ **Exécuter les scripts**
2. ⏳ **Valider les résultats**
3. ⏳ **Ré-analyser avec bons impacts**
4. ⏳ **Générer formule v9**
5. ⏳ **Mettre à jour documentation**

---

## 🎯 OBJECTIFS SESSION 9

### Priorité 1 : EXÉCUTION ⭐⭐⭐

**Scripts à exécuter :**

```bash
# 1. Calculer les impacts groupés
python calculate_grouped_impacts.py

# 2. Valider les résultats
python validate_grouped_impacts.py
```

**Durée estimée :** 20-30 minutes

**Résultats attendus :**
- Table `event_group_impacts` créée
- ~1,500 groupes temporels (vs ~4,000 événements)
- 11 septembre : 1 ligne pour 14:30 (pas 33)
- Range ~111.5 pips (écart <10% avec MT5)

---

### Priorité 2 : ANALYSE ⭐⭐

**Créer :** `analyze_grouped_impacts.py`

**Fonctionnalités :**

1. **Analyse de corrélation**
   ```python
   # Corrélation empirical_score vs range_pips
   correlation = df['empirical_score'].corr(df['range_pips'])
   
   # Régression linéaire
   from sklearn.linear_model import LinearRegression
   model.fit(X, y)
   ```

2. **Génération formule v9**
   ```python
   # Formule : impact = a + b × score
   # Calculer a (intercept) et b (coef)
   ```

3. **Métriques de qualité**
   ```python
   # R² (coefficient de détermination)
   # MAE (Mean Absolute Error)
   # Corrélation de Pearson
   ```

4. **Comparaison avec v6**
   ```python
   # v6 : R² = 0.719 (sur calcul incorrect)
   # v9 : R² = ? (sur calcul correct)
   ```

**Durée estimée :** 1-2 heures

---

### Priorité 3 : DOCUMENTATION ⭐

**Mettre à jour :**

1. **KNOWLEDGE_BASE.md**
   - Ajouter erreur #7 (calcul individuel vs groupé)
   - Marquer formules v7/v8 comme obsolètes
   - Ajouter formule v9 et métriques

2. **START_HERE.md**
   - État après Session 9
   - Prochaines étapes Session 10

3. **Créer RAPPORT_SESSION9_FINAL.md**
   - Résultats exécution
   - Formule v9
   - Validation

**Durée estimée :** 30-45 minutes

---

## 📊 CRITÈRES DE SUCCÈS

### Validation technique

- [ ] Table `event_group_impacts` créée
- [ ] 11 septembre : 1 ligne pour 14:30 (pas 33)
- [ ] Range calculé ≈ 111.5 pips (écart <20%)
- [ ] Direction = UP
- [ ] Aucune erreur d'exécution

### Métriques qualité

- [ ] R² formule v9 > 0.3
- [ ] Corrélation score vs range > 0.5
- [ ] Précision 11 sept > 70%
- [ ] Pas de valeurs aberrantes (>500 pips)

### Documentation

- [ ] KNOWLEDGE_BASE.md mis à jour
- [ ] Formule v9 documentée
- [ ] RAPPORT_SESSION9_FINAL.md créé
- [ ] Métriques v9 documentées

---

## 🔧 SCRIPTS À CRÉER

### 1. analyze_grouped_impacts.py

**Structure recommandée :**

```python
#!/usr/bin/env python3
"""
ANALYSE DES IMPACTS GROUPÉS ET GÉNÉRATION FORMULE V9

Objectif : Analyser les corrélations et générer une nouvelle formule
           basée sur les impacts groupés (calcul correct)
"""

import duckdb
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib.pyplot as plt

def analyze_correlations():
    """Analyse des corrélations score vs impact"""
    # 1. Charger les impacts groupés
    # 2. Calculer corrélations
    # 3. Visualiser scatter plot
    pass

def generate_formula_v9():
    """Génère la formule v9 par régression"""
    # 1. Préparer les données
    # 2. Régression linéaire
    # 3. Calculer métriques (R², MAE)
    # 4. Retourner formule
    pass

def compare_with_v6():
    """Compare formule v9 avec v6"""
    # 1. Charger formule v6
    # 2. Appliquer sur même dataset
    # 3. Comparer précisions
    pass

def validate_on_sept_11():
    """Valide la formule v9 sur le 11 septembre"""
    # 1. Appliquer formule v9
    # 2. Comparer avec MT5 (111.5 pips)
    # 3. Calculer écart
    pass

if __name__ == '__main__':
    main()
```

---

### 2. test_formula_v9.py (optionnel)

**Tests sur plusieurs dates :**

```python
#!/usr/bin/env python3
"""
TEST FORMULE V9 SUR DATES MULTIPLES

Objectif : Tester la formule v9 sur plusieurs dates historiques
           pour valider sa robustesse
"""

def test_multiple_dates():
    """Teste sur 10-20 dates"""
    test_dates = [
        '2025-09-11',  # Référence
        '2025-08-15',
        '2025-07-10',
        # ... etc
    ]
    
    for date in test_dates:
        # Appliquer formule v9
        # Comparer avec impact réel
        # Calculer écart
    pass
```

---

## 📏 VALIDATION 11 SEPTEMBRE

### Données de référence

**MT5 (référence terrain) :**
- Time group : 14:30:00
- Nombre événements : 33
- Range : 111.5 pips
- Direction : UP
- Prix référence : 1.16810
- Prix max : 1.17190
- Prix min : 1.16075

**Script v7 (incorrect) :**
- Lignes créées : 33
- MFE moyen : 59.2 pips
- Méthode : Individuel
- ❌ Sous-estimation : 47%

**Script v8 (attendu) :**
- Lignes créées : 1
- Range : ~111.5 pips
- Méthode : Groupé
- ✅ Écart attendu : <10%

---

## 🐛 PROBLÈMES POTENTIELS

### Si calculate_grouped_impacts.py échoue

**Erreurs possibles :**

1. **"prices_1m not found"**
   - Vérifier que `warehouse.duckdb` contient prices_1m
   - Vérifier dates disponibles (>= 2024-01-01)

2. **"Too slow / no progress"**
   - Normal : 10-20 min pour tous les groupes
   - Vérifier que tqdm est installé
   - Checkpoints tous les 100 groupes

3. **"Range aberrant (>500 pips)"**
   - Vérifier fenêtre lookforward (60 min)
   - Vérifier données prix (pas de gaps)

### Si validate_grouped_impacts.py trouve des erreurs

**Actions correctives :**

1. **Écart >20% avec MT5**
   - Vérifier timestamps (UTC ?)
   - Vérifier prix référence (5 min avant)
   - Consulter les prix min/max dans sortie

2. **Direction incorrecte**
   - Vérifier calcul net_movement
   - Vérifier prix final vs référence

3. **TTR tous NULL**
   - Normal si prix ne revient jamais à référence
   - Augmenter fenêtre ou tolérance

---

## 🎯 MÉTRIQUES CIBLES

### Formule v9

| Métrique | Cible | Note |
|----------|-------|------|
| R² | > 0.3 | Acceptable si données réelles |
| Corrélation | > 0.5 | Score vs Range |
| MAE | < 30 pips | Erreur moyenne absolue |
| Précision 11 sept | > 70% | Écart <30% avec MT5 |

**Note :** R² plus faible que v6 (0.719) est NORMAL car :
- v6 était basé sur calcul incorrect (surestimé)
- v9 est basé sur vraies données (plus de variance)
- Mieux vaut 0.3 précis que 0.8 biaisé

---

## 💡 CONSEILS POUR SESSION 9

### 1. Exécuter d'abord, analyser ensuite

- Lancer les scripts avant de les analyser
- Pendant l'exécution (10-20 min), préparer l'analyse
- Ne pas attendre les résultats pour commencer le script suivant

### 2. Valider systématiquement

- Toujours vérifier le 11 septembre en premier
- C'est la référence terrain la plus fiable
- Si 11 sept est bon, le reste devrait l'être aussi

### 3. R² faible ≠ échec

- L'impact a une composante aléatoire (contexte, sentiment)
- R² = 0.3-0.4 est excellent pour ce type de prédiction
- L'important est la cohérence, pas la perfection

### 4. Documenter les surprises

- Si résultats très différents d'attendu, documenter
- Ajouter dans KNOWLEDGE_BASE.md
- Sera utile pour Session 10+

---

## 🔄 WORKFLOW SESSION 9

```
1. EXÉCUTION (30 min)
   ├─ calculate_grouped_impacts.py (10-20 min)
   ├─ validate_grouped_impacts.py (5 min)
   └─ Vérifier résultats (5 min)

2. ANALYSE (1-2h)
   ├─ Créer analyze_grouped_impacts.py (45 min)
   ├─ Exécuter et générer formule v9 (15 min)
   ├─ Valider sur 11 septembre (10 min)
   └─ Tests optionnels dates multiples (30 min)

3. DOCUMENTATION (30-45 min)
   ├─ Mettre à jour KNOWLEDGE_BASE.md (15 min)
   ├─ Mettre à jour START_HERE.md (10 min)
   └─ Créer RAPPORT_SESSION9_FINAL.md (15 min)

TOTAL: 2-3 heures
```

---

## 📝 CHECKLIST DÉMARRAGE SESSION 9

- [ ] Lu RAPPORT_SESSION8_FINAL.md
- [ ] Lu ADDENDUM_CRITIQUE_SESSION7.md
- [ ] Lu session8_measurements/README_SESSION8_SCRIPTS.md
- [ ] Compris le problème : individuel vs groupé
- [ ] Compris la solution : calcul par time_group
- [ ] Compris les résultats attendus : 1 ligne, 111.5 pips
- [ ] Prêt à exécuter les scripts

**Si tous cochés → GO ! 🚀**

---

**FIN SESSION9_INTRO.md**

**Version :** 1.0  
**Date :** 17 octobre 2025  
**Statut :** ✅ Prêt pour Session 9

**Prochaine étape :** Exécuter calculate_grouped_impacts.py
