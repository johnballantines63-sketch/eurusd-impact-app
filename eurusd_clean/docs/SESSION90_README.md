# 📋 SESSION 90 - VALIDATION ÉTENDUE COEFFICIENT 0.55

**Date :** 26 octobre 2025  
**Statut :** ✅ EN COURS - Phase validation étendue  
**Objectif :** Valider coefficient 0.55 sur 10-15 dates avant intégration production

---

## 🎯 MISSION

**Contexte Session 89 :**
- ✅ MAE = 25.2 pips atteint (< 30 objectif)
- ✅ Coefficient 0.55 validé sur 3 dates
- ⚠️ Dataset trop petit (N=3 statistiquement insuffisant)
- ❌ 1 outlier 75.1 pips sur NFP non expliqué

**Décision :** Validation étendue 10-15 dates AVANT intégration production

**Objectifs Session 90 :**
1. ✅ MAE global < 30 pips sur ≥10 dates
2. ✅ MAE NFP < 40 pips sur ≥3 dates NFP
3. ✅ 0 cas outlier > 80 pips
4. ✅ Comprendre pourquoi 05.09 NFP = 75.1 pips
5. ✅ Analyser variabilité par type événement

---

## 📊 SCRIPTS CRÉÉS

### 1. diagnose_0509_detailed.py (Session 90)

**Objectif :** Diagnostic approfondi 05.09.2025 (outlier 75.1 pips)

**Fonctionnalités :**
- Charger tous événements HIGH 05.09
- Analyser disponibilité estimate/forecast/previous
- Calculer surprises avec fallback robuste
- Comparer avec dates réussies (01.08, 17.09)
- Identifier cause MAE élevé

**Exécution :**
```bash
cd /path/to/scripts/session90
python3 diagnose_0509_detailed.py
```

**Output attendu :**
- Liste événements avec sources utilisées
- Statistiques coverage données
- Comparaison vs dates réussies
- Hypothèses causes outlier

---

### 2. list_available_dates.py (Session 90)

**Objectif :** Identifier 10-15 dates optimales pour validation

**Fonctionnalités :**
- Scanner DB pour dates HIGH IMPACT (score > 40)
- Filtrer ≥3 événements par date
- Classer par type (NFP, CPI, Jobless, Retail)
- Sauvegarder CSV dates disponibles

**Exécution :**
```bash
python3 list_available_dates.py
```

**Output :**
- Console : Top 20 dates + breakdown par type
- CSV : `dates_disponibles_session90.csv`

**Critères sélection recommandés :**
- 3-4 dates NFP (haute variabilité)
- 3-4 dates CPI (variabilité moyenne)
- 2-3 dates Jobless Claims
- 1-2 dates Retail Sales
- 1-2 dates autres types

---

### 3. test_multi_dates_extended.py (Session 90)

**Objectif :** Validation étendue coefficient 0.55 sur 10-15 dates

**Basé sur :** `test_multi_dates.py` (Session 89) - même logique

**Améliorations :**
- Support 10-15 dates (vs 3 Session 89)
- Statistiques par type événement
- Détection outliers > 80 pips
- Validation critères multiples

**Configuration :**
1. Exécuter `list_available_dates.py`
2. Ouvrir CSV généré
3. Sélectionner 10-15 dates diversifiées
4. Ajouter dans variable `TEST_DATES` (ligne 31)
5. Exécuter script

**Exécution :**
```bash
python3 test_multi_dates_extended.py
```

**Output :**
- Console : Tableau résultats + statistiques
- CSV : `validation_results_session90.csv`

**Métriques calculées :**
- MAE global
- RMSE
- Médiane erreur
- Tests < 30 pips (%)
- Outliers > 80 pips (count)
- MAE par type événement

**Critères validation :**
- ✅ MAE < 30 pips
- ✅ 0 outliers
- ✅ N ≥ 10 dates

---

### 4. validate_extended.py (Session 90)

**Objectif :** Script validation alternative (prédictions seulement)

**Note :** Script simplifié calculant uniquement prédictions (pas impacts réels).  
**Recommandé :** Utiliser `test_multi_dates_extended.py` qui mesure impacts réels.

---

### 5. run_validation_complete.sh (Session 90)

**Objectif :** Orchestrateur complet validation Session 90

**Séquence :**
1. Diagnostic 05.09
2. Liste dates disponibles
3. Pause utilisateur (sélection dates)
4. Validation étendue

**Exécution :**
```bash
chmod +x run_validation_complete.sh
./run_validation_complete.sh
```

---

## 🔧 WORKFLOW RECOMMANDÉ

### Étape 1 : Comprendre Outlier 05.09

```bash
python3 diagnose_0509_detailed.py
```

**Questions à répondre :**
- Quels événements ce jour ?
- Surprise max calculée ?
- Coverage estimate/forecast/previous ?
- Différences vs 01.08 (succès) ?

---

### Étape 2 : Identifier Dates Optimales

```bash
python3 list_available_dates.py
```

**Actions :**
1. Lire output console (top 20 dates)
2. Ouvrir CSV généré
3. Sélectionner 10-15 dates selon critères

**Critères sélection :**
- Diversité types (NFP, CPI, Jobless, Retail)
- Diversité scores (40-100)
- Diversité temporelle (différents mois)
- Éviter dates trop proches

---

### Étape 3 : Configuration Tests

Éditer `test_multi_dates_extended.py` ligne 31 :

```python
TEST_DATES = [
    # Session 89
    {'date': '2025-08-01', 'time': '12:30:00', 'name': '01 Août (NFP 500%)', 'type': 'NFP'},
    {'date': '2025-09-17', 'time': '12:30:00', 'name': '17 Sept (Standard)', 'type': 'CPI'},
    {'date': '2025-09-05', 'time': '12:30:00', 'name': '05 Sept (NFP)', 'type': 'NFP'},
    
    # Session 90 - NOUVELLES DATES
    {'date': 'YYYY-MM-DD', 'time': 'HH:MM:SS', 'name': 'Description', 'type': 'Type'},
    # ... ajouter 7-12 dates supplémentaires
]
```

---

### Étape 4 : Exécution Validation

```bash
python3 test_multi_dates_extended.py
```

**Durée estimée :** 5-10 min (selon nombre dates)

---

### Étape 5 : Analyse Résultats

**Si validation réussie (MAE < 30, 0 outliers, N ≥ 10) :**
→ **Session 91 :** Intégration production `planner.py`

**Si validation partielle :**
→ **Session 91 :** Ajustements formule + retest

**Cas spécifiques :**

**MAE 30-35 pips :**
- Analyser outliers (> 80 pips)
- Possibilité ajuster coefficient 0.55 → 0.50 ou 0.60
- Retester avec nouveau coefficient

**MAE > 35 pips :**
- Analyse approfondie par type
- Possibilité coefficients différenciés (NFP vs CPI)
- Itération Session 91

**Outliers présents :**
- Identifier dates problématiques
- Analyser causes (données manquantes ?)
- Décider exclusion ou correction

---

## 📈 RÉSULTATS ATTENDUS

### Scénario A : Validation Réussie ✅

**Critères :**
- MAE global < 30 pips
- 0 outliers > 80 pips
- N ≥ 10 dates testées
- MAE NFP < 40 pips

**Décision :** Intégration production Session 91

**Actions Session 91 :**
1. Backup `planner.py`
2. Intégrer `calculate_amplification_extended()`
3. Tests Streamlit
4. Documentation utilisateur
5. Livraison production

---

### Scénario B : Validation Partielle ⚠️

**Cas 1 : MAE 30-35 pips (acceptable)**

**Décision :** Ajustement mineur + intégration

**Actions Session 91 :**
1. Tester coefficient 0.50 ou 0.60
2. Retester 5 dates clés
3. Si MAE < 30 → Intégration
4. Sinon → Itération

**Cas 2 : MAE > 35 pips ou outliers présents**

**Décision :** Analyse approfondie nécessaire

**Actions Session 91 :**
1. Diagnostic outliers détaillé
2. Analyse corrélations (type, surprise, score)
3. Hypothèses corrections
4. Implémentation corrections
5. Retest complet
6. Décision intégration

---

### Scénario C : Validation Échouée ❌

**Critères :**
- MAE > 40 pips
- Plusieurs outliers
- Pattern incohérent

**Décision :** Retour formule Session 51-55 (sans coefficient 0.55)

**Alternative :** Approche conditionnelle
- Coefficient 0.55 si surprise < 100%
- Coefficient alternatif si surprise > 100%
- Tests A/B

---

## 🎓 LEÇONS SESSION 90

### 1. Méthodologie Validation

**N=3 est insuffisant :**
- Aucune significativité statistique
- Risque overfitting sur cas spécifiques
- Outlier non détectable

**N=10-15 recommandé :**
- Significativité statistique acceptable
- Variabilité observable
- Outliers identifiables
- Confiance robuste

---

### 2. Qualité > Rapidité

**Décision correcte :**
- Refuser intégration prématurée
- Préférer validation robuste
- 1 session supplémentaire = sécurité

**Conséquences si intégration S89 :**
- Découverte problème en production
- Perte confiance utilisateurs
- Rollback coûteux

---

### 3. Diversité Dataset

**Types événements :**
- NFP : haute variabilité
- CPI : variabilité moyenne
- Jobless : prévisibilité haute
- Retail : variabilité basse

**Importance diversité :**
- Comprendre limites formule
- Identifier coefficients optimaux par type
- Anticiper edge cases

---

## 🔑 COMMANDES RAPIDES

```bash
# Répertoire Session 90
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90

# Workflow complet
chmod +x run_validation_complete.sh
./run_validation_complete.sh

# OU étapes individuelles

# 1. Diagnostic 05.09
python3 diagnose_0509_detailed.py

# 2. Liste dates
python3 list_available_dates.py

# 3. Validation étendue (après configuration TEST_DATES)
python3 test_multi_dates_extended.py

# 4. Vérifier résultats
cat validation_results_session90.csv
```

---

## 📊 BUDGET TOKENS SESSION 90

**Estimé :** 70,000 tokens

**Répartition :**
- Lecture docs : 10,000
- Diagnostic 05.09 : 10,000
- Liste dates : 5,000
- Scripts validation : 20,000
- Tests exécution : 10,000
- Documentation : 15,000

**Tokens utilisés actuellement : 85,694 / 190,000 (45%)**

**Restant pour Session 90 : ~104,306 tokens (55%)**

---

## ✅ CHECKLIST SESSION 90

### Phase 1 : Préparation ✅
- [x] Lire MANDATORY_SESSION_RULES.md
- [x] Lire project_state_new.md
- [x] Lire SESSION89_RAPPORT_COMPLET.md
- [x] Lire MESSAGE_SESSION89_SESSION90.md
- [x] Valider mission avec utilisateur
- [x] Créer répertoire session90

### Phase 2 : Scripts ✅
- [x] Script diagnostic 05.09
- [x] Script liste dates disponibles
- [x] Script validation étendue
- [x] Script orchestrateur
- [x] Documentation README

### Phase 3 : Exécution ⏳
- [ ] Exécuter diagnostic 05.09
- [ ] Exécuter liste dates
- [ ] Sélectionner 10-15 dates
- [ ] Configurer TEST_DATES
- [ ] Exécuter validation étendue
- [ ] Analyser résultats

### Phase 4 : Décision ⏳
- [ ] MAE < 30 pips validé ?
- [ ] 0 outliers confirmé ?
- [ ] N ≥ 10 dates testé ?
- [ ] Décision intégration ou itération

### Phase 5 : Documentation ⏳
- [ ] Rapport SESSION90_RAPPORT_COMPLET.md
- [ ] Message SESSION90_SESSION91.md
- [ ] Mise à jour project_state_new.md
- [ ] Fichiers créés documentés

---

**Session 90 : ✅ EN COURS - Phase validation étendue**  
**Tokens utilisés : 85,694 / 190,000 (45%)**  
**Prochaine étape : Exécution tests**

---

_README Session 90 - Validation étendue coefficient 0.55_  
_26 octobre 2025_
