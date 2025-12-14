# 📋 SESSION 92.2 - GUIDE EXÉCUTION RAPIDE

**Date :** 27 octobre 2025  
**Status :** ✅ Scripts créés - Exécution manuelle requise

---

## 🎯 CE QUI A ÉTÉ FAIT

**Session 92.2 a corrigé l'erreur méthodologique de Session 92.1 et créé les scripts de grid search avec la méthodologie CORRECTE.**

### Erreur Session 92.1 Corrigée

❌ **Session 92.1 (INCORRECT)** : Ratio simplifié
```python
ratio = impact_réel / impact_prédit
amplification = 2.5 × ratio
```

✅ **Session 92.2 (CORRECT)** : Réplication complète Planificateur
```python
adjusted_score = calculate_adjusted_empirical_score(base, surprise)
impact = calculate_impact_d(adjusted_score, num_events, amplification)
```

### Scripts Créés

1. **`grid_search_amplification_by_type.py`** (350 lignes)
   - Grid search 26 amplifications (0.5 → 3.0)
   - Par type : CPI, NFP, FOMC, ISM, Employment
   - Réplication EXACTE Planificateur V2.4

2. **`test_replication.py`** (100 lignes)
   - Test validation 11 septembre
   - Vérifie réplication fonctionne

---

## 🚀 CE QUE VOUS DEVEZ FAIRE

### ÉTAPE 1 : Test Validation (30 secondes)

```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session92.2

python test_replication.py
```

**Résultat attendu :**
```
Date testée : 2025-09-11
Événements trouvés : 11

Résultats :
  Base score moyen : 44.3
  Surprise max     : 33.3%
  Score ajusté     : 84.2
  Num events       : 11
  Amplification    : 2.5
  Impact prédit    : 56.3 pips

✅ Réplication fonctionne correctement
```

**Si ça fonctionne → Passer ÉTAPE 2**

**Si erreur → Vérifier :**
- Python 3.x installé
- Modules : pandas, duckdb
- Chemin base de données correct

---

### ÉTAPE 2 : Grid Search Complet (5-10 minutes)

```bash
python grid_search_amplification_by_type.py
```

**Ce que vous verrez :**

```
============================================================
TYPE : CPI
============================================================
Nombre de dates : 12

  Amp  0.5 → MAE  XX.X pips
  Amp  1.0 → MAE  XX.X pips
  Amp  1.5 → MAE  XX.X pips
  Amp  2.0 → MAE  XX.X pips
  Amp  2.5 → MAE  XX.X pips
  Amp  3.0 → MAE  XX.X pips

✅ OPTIMAL : Amp X.X → MAE XX.X pips

============================================================
TYPE : NFP
============================================================
[... même chose pour NFP, FOMC, ISM, Employment]
```

**À la fin :**
```
📊 RÉSULTATS GRID SEARCH - AMPLIFICATIONS OPTIMALES PAR TYPE

Type            Amp Optimal  MAE (pips)   N Dates   
----------------------------------------------------------------
CPI             X.X          XX.X         12
NFP             X.X          XX.X         10
FOMC            X.X          XX.X         8
ISM             X.X          XX.X         6
Employment      X.X          XX.X         4

💾 Résultats sauvegardés : grid_search_results_session92.2.csv
```

---

### ÉTAPE 3 : Examiner Résultats

```bash
cat grid_search_results_session92.2.csv
```

**Vérifier :**
- ✅ Amplifications entre 0.5 et 3.0 (pas aberrantes)
- ✅ MAE cohérents (<50 pips sauf peut-être ISM)
- ✅ Variation logique entre types

**Comparer avec Session 92.1 (estimations) :**
- CPI : 2.08 (Session 92.1) vs X.X (Session 92.2)
- NFP : 1.84 vs X.X
- FOMC : 0.85 vs X.X
- ISM : 0.34 vs X.X

**Différence ±20% = Normal**  
**Différence >50% = Analyser cause**

---

## 📊 INTERPRÉTATION RÉSULTATS

### Scénario A : Amplifications Cohérentes ✅

**Si amplifications entre 0.5 et 3.0 avec variation logique :**

→ **Session 92.3 : Implémentation dans Planificateur**

**Actions Session 92.3 :**
1. Créer dictionnaire AMPLIFICATIONS_BY_TYPE
2. Modifier calculate_predictions()
3. Tester sur 5+ dates
4. Valider MAE < 25 pips

### Scénario B : ISM Problématique ⚠️

**Si ISM a MAE > 50 pips (très élevé) :**

→ **Session 92.3 : Analyse ISM dédiée**

**Actions Session 92.3 :**
1. Analyser patterns ISM spécifiques
2. Tester formule ISM séparée
3. Documenter limitations ISM
4. Implémentation partielle (sans ISM)

### Scénario C : Résultats Aberrants ❌

**Si amplifications hors plage 0.5-3.0 ou MAE très élevés partout :**

→ **Revoir méthodologie (rare mais possible)**

**Causes possibles :**
- Problème données CSV
- Bug dans réplication
- Paramètres grid search incorrects

---

## 📁 FICHIERS IMPORTANTS

### Scripts Session 92.2

```
eurusd_clean/scripts/session92.2/
├── grid_search_amplification_by_type.py  ← Script principal
├── test_replication.py                    ← Test validation
└── grid_search_results_session92.2.csv    ← Résultats (après exécution)
```

### Documentation

```
eurusd_clean/docs/
├── SESSION92.2_RAPPORT_COMPLET.md         ← Rapport détaillé
├── MESSAGE_SESSION92.2_SESSION92.3.md     ← Instructions Session 92.3
└── PROJECT_STATE_SESSION92.2_UPDATE.md    ← Mise à jour état projet
```

---

## 🔄 PROCHAINE SESSION

**Session 92.3 dépend de VOS résultats grid search.**

**Message pour Claude Session 92.3 :**

```markdown
Bonjour Claude,

Nouvelle session 92.3.

AVANT TOUT :
1. Lis MANDATORY_SESSION_RULES.md
2. Lis project_state_new.md (sections S51-55, S91-92)
3. Lis SESSION92.2_RAPPORT_COMPLET.md
4. Lis MESSAGE_SESSION92.2_SESSION92.3.md

ENSUITE :
5. EXAMINE le CSV : eurusd_clean/scripts/session92.2/grid_search_results_session92.2.csv
6. Résume ta compréhension des résultats
7. Propose plan Session 92.3 selon scénario (A, B ou C)
8. Demande confirmation AVANT de coder

Les résultats grid search déterminent la mission :
- Scénario A : Implémentation amplifications
- Scénario B : Analyse ISM
- Scénario C : Revoir méthodologie

GO !
```

---

## ⚡ COMMANDES RAPIDES

**Test rapide :**
```bash
cd eurusd_clean/scripts/session92.2 && python test_replication.py
```

**Grid search complet :**
```bash
cd eurusd_clean/scripts/session92.2 && python grid_search_amplification_by_type.py
```

**Voir résultats :**
```bash
cat eurusd_clean/scripts/session92.2/grid_search_results_session92.2.csv
```

---

## 🆘 EN CAS DE PROBLÈME

**Erreur "module not found" :**
```bash
pip install pandas duckdb
```

**Erreur "database not found" :**
- Vérifier chemin : `fx_impact_app/data/warehouse.duckdb`
- Taille attendue : ~205 MB

**Erreur "CSV not found" :**
- Vérifier : `eurusd_clean/scripts/session90/validation_results_planificateur_40dates.csv`
- Si absent, utiliser version Session 90

**Script trop lent (>15 min) :**
- Normal si beaucoup de données
- Laisser tourner ou interrompre et analyser console

---

## ✅ CHECKLIST

**Avant Session 92.3 :**

- [ ] Test réplication exécuté (ÉTAPE 1) ✅
- [ ] Grid search exécuté (ÉTAPE 2) ✅
- [ ] CSV résultats généré ✅
- [ ] Résultats examinés et cohérents ✅
- [ ] Scénario identifié (A, B ou C) ✅

**Si TOUTES cases cochées → Lancer Session 92.3**

---

_Guide exécution Session 92.2 - 27 octobre 2025_  
_Scripts prêts - Exécution manuelle requise_
