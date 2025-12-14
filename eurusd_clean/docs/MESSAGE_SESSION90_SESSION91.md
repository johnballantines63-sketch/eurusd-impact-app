# MESSAGE SESSION 90 → SESSION 91

**Date :** 26 octobre 2025  
**Session 90 Statut :** ✅ RÉUSSIE - Scripts validation créés  
**Session 91 Mission :** Exécution validation étendue + Décision intégration

---

## ⚠️ RAPPELS IMPÉRATIFS SESSION 91

### 🚨 CHECKLIST OBLIGATOIRE DÉMARRAGE

**AVANT TOUT CODE, Claude DOIT :**

1. [ ] **Lire `MANDATORY_SESSION_RULES.md`** ⭐⭐⭐
2. [ ] **Lire `project_state_new.md`** (section Session 90)
3. [ ] **Lire `SESSION90_RAPPORT_INTERMEDIAIRE.md`**
4. [ ] **Lire ce message** (`MESSAGE_SESSION90_SESSION91.md`)
5. [ ] **Afficher tokens régulièrement** (tous les 20k)
6. [ ] **Valider mission avec utilisateur AVANT code**

### 📁 Documentation dans `/docs` TOUJOURS

**❌ NE PAS créer docs dans `/scripts`**  
**✅ TOUJOURS créer dans `/docs`**

---

## 📊 ÉTAT SESSION 90

### ✅ RÉUSSIE - Phase Préparation Complète

**Scripts créés (6 fichiers) :**
```
scripts/session90/
├── diagnose_0509_detailed.py         ✅ Diagnostic outlier
├── list_available_dates.py           ✅ Liste dates HIGH
├── test_multi_dates_extended.py      ✅ Validation 10-15 dates
├── validate_extended.py              ✅ Alternative
├── run_validation_complete.sh        ✅ Orchestrateur
```

**Documentation créée (4 fichiers) :**
```
docs/
├── SESSION90_README.md               ✅ Doc complète
├── SESSION90_QUICK_START.md          ✅ Guide rapide
├── SESSION90_RAPPORT_INTERMEDIAIRE.md ✅ Rapport Phase 1
└── SESSION90_RESUME_ANDRE.md         ✅ Résumé utilisateur
```

**Tokens Session 90 :** 95,174 / 105,000 (90.6%)  
**Scripts testés :** ✅ Syntaxe validée  
**Prêt exécution :** ✅ OUI

---

## 🎯 MISSION SESSION 91

### VALIDATION ÉTENDUE + DÉCISION INTÉGRATION

**Objectif :** Valider coefficient 0.55 sur 10-15 dates → Décider intégration production

**3 phases :**

#### Phase 1 : Exécution Tests (15-20k tokens)

**Étape 1.1 : Liste dates disponibles**
```bash
cd scripts/session90
python3 list_available_dates.py
```

**Étape 1.2 : Sélection 10-15 dates**
- Ouvrir `dates_disponibles_session90.csv`
- Sélectionner dates diversifiées :
  - 3-4 NFP
  - 3-4 CPI
  - 2-3 Jobless Claims
  - 1-2 Retail Sales

**Étape 1.3 : Configuration TEST_DATES**
- Éditer `test_multi_dates_extended.py` ligne 31
- Ajouter 7-12 dates sélectionnées

**Étape 1.4 : Validation complète**
```bash
python3 test_multi_dates_extended.py
```

**Durée estimée :** 10-20 minutes exécution

---

#### Phase 2 : Analyse Résultats (10-15k tokens)

**Métriques à analyser :**
- MAE global < 30 pips ? ✅/❌
- RMSE
- Médiane erreur
- Tests < 30 pips (%)
- Outliers > 80 pips (count)
- MAE par type (NFP, CPI, Jobless, Retail)

**Questions critiques :**
1. Outlier 05.09 NFP expliqué ?
2. MAE NFP acceptable (< 40 pips) ?
3. Variabilité par type cohérente ?
4. Coefficient 0.55 robuste sur tous types ?

---

#### Phase 3 : Décision & Documentation (15-20k tokens)

**Scénario A : Validation Réussie (MAE < 30, 0 outliers)**

→ **Intégration production planner.py**

**Actions :**
1. Backup `fx_impact_app/planner.py`
2. Intégrer `calculate_amplification_extended()`
3. Tests Streamlit interface
4. Documentation utilisateur
5. Rapport Session 91 complet

**Budget : 40-50k tokens**

---

**Scénario B : Validation Partielle (MAE 30-35, 1-2 outliers)**

→ **Ajustements mineurs puis intégration**

**Actions :**
1. Analyser causes MAE légèrement élevé
2. Tester coefficients alternatifs (0.50, 0.60)
3. Retester 5 dates clés
4. Si MAE < 30 → Intégration
5. Documentation complète

**Budget : 50-60k tokens**

---

**Scénario C : Validation Échouée (MAE > 35, 3+ outliers)**

→ **Analyse approfondie + Corrections**

**Actions :**
1. Diagnostic détaillé outliers
2. Analyse corrélations (type, surprise, score)
3. Hypothèses corrections
4. Implémentation corrections
5. Retest complet
6. Documentation diagnostic

**Budget : 60-70k tokens**

**Note :** Si Scénario C, intégration reportée Session 92

---

## 📋 PLAN DÉTAILLÉ SESSION 91

### Étape 1 : Démarrage (5k tokens)

**AVANT TOUT CODE :**
```
1. Lire MANDATORY_SESSION_RULES.md
2. Lire project_state_new.md (section S90)
3. Lire SESSION90_RAPPORT_INTERMEDIAIRE.md
4. Lire ce message
5. Résumer mission utilisateur
6. Obtenir GO
```

---

### Étape 2 : Exécution Tests (15-20k tokens)

**Commande unique (recommandée) :**
```bash
cd scripts/session90
chmod +x run_validation_complete.sh
./run_validation_complete.sh
```

**OU manuel :**
```bash
# 1. Liste dates
python3 list_available_dates.py

# 2. Configurer TEST_DATES manuellement

# 3. Validation
python3 test_multi_dates_extended.py
```

**Attendre résultats complets avant continuer**

---

### Étape 3 : Analyse (10-15k tokens)

**Lire output console :**
```
📊 RÉSUMÉ VALIDATION ÉTENDUE
   MAE global    : XX.X pips
   Tests < 30    : X/X (XX%)
   Outliers > 80 : X
```

**Analyser CSV :**
```bash
cat scripts/session90/validation_results_session90.csv
```

**Identifier :**
- Dates succès (< 30 pips)
- Dates problématiques (> 80 pips)
- Patterns par type
- Causes écarts

---

### Étape 4A : Si Validation OK → Intégration (30-40k tokens)

**4A.1 Backup planner.py**
```bash
cp fx_impact_app/planner.py fx_impact_app/planner.py.backup_session91
```

**4A.2 Modification planner.py**

**Fichier :** `fx_impact_app/planner.py`

**Import à ajouter (ligne ~10) :**
```python
from formulas_validated import calculate_amplification_extended
```

**Modification logique amplification (ligne ~XXX) :**
```python
# AVANT (chercher cette ligne)
amplification = 2.5  # Fixe

# APRÈS (remplacer par)
surprise_max = max([event['surprise_pct'] for event in events])
amplification = calculate_amplification_extended(surprise_max)
```

**4A.3 Tests validation**
- Tests unitaires Planificateur
- Tests Streamlit interface
- Validation 2-3 dates via UI
- Vérifier affichage amplification dynamique

---

### Étape 4B : Si Corrections Nécessaires (30-50k tokens)

**4B.1 Diagnostic approfondi**
- Analyser outliers individuellement
- Vérifier données (estimate/forecast/previous)
- Identifier patterns échecs

**4B.2 Hypothèses corrections**
- Coefficient trop élevé ? (0.55 → 0.50)
- Coefficient trop bas ? (0.55 → 0.60)
- Coefficients différenciés par type ?

**4B.3 Tests corrections**
- Implémenter correction
- Retester 5 dates clés
- Comparer résultats

---

### Étape 5 : Documentation (15-20k tokens)

**Toujours créer :**
- `SESSION91_RAPPORT_COMPLET.md` dans `/docs`
- Message `MESSAGE_SESSION91_SESSION92.md`
- Mise à jour `project_state_new.md`

**Tokens réservés :** 20k minimum

---

## 📊 BUDGET TOKENS SESSION 91

### Scénario A : Validation OK + Intégration

```
Lecture docs :          5k tokens
Tests validation :      20k tokens
Intégration planner :   30k tokens
Tests validation :      10k tokens
Documentation :         20k tokens
──────────────────────────────────
TOTAL :                 85k tokens
Budget session :        105k tokens
Marge sécurité :        20k tokens ✅
```

---

### Scénario B : Corrections + Intégration

```
Lecture docs :          5k tokens
Tests validation :      20k tokens
Diagnostic + corrections: 30k tokens
Retests :               15k tokens
Documentation :         20k tokens
──────────────────────────────────
TOTAL :                 90k tokens
Budget session :        105k tokens
Marge sécurité :        15k tokens ✅
```

---

### Scénario C : Diagnostic Approfondi

```
Lecture docs :          5k tokens
Tests validation :      20k tokens
Diagnostic détaillé :   40k tokens
Documentation :         20k tokens
──────────────────────────────────
TOTAL :                 85k tokens
Budget session :        105k tokens
Marge sécurité :        20k tokens ✅
Intégration :           Session 92
```

---

## 🔑 INFORMATIONS CLÉS

### Scripts Session 90 Prêts

**PRINCIPAL à utiliser :**
```bash
scripts/session90/test_multi_dates_extended.py
```

**Fonctionnalités :**
- Validation 10-15 dates
- Calcul MAE, RMSE, médiane
- Détection outliers automatique
- Stats par type événement
- Export CSV résultats

**Configuration requise :**
- Éditer ligne 31 : ajouter 7-12 dates
- Format : `{'date': 'YYYY-MM-DD', 'time': 'HH:MM:SS', 'name': '...', 'type': 'NFP/CPI/...'}`

---

### Coefficient Validé Session 89

**Zone 4 (>100% surprise) :**
```python
amplification = 5.0 + 0.55 × log10(surprise - 99)

Exemples :
- 100% → 5.0x
- 200% → 6.1x
- 500% → 6.43x (validé : 0.3 pips MAE Session 89)
- 1000% → 7.7x
```

**Résultats Session 89 (3 dates) :**
- MAE global : 25.2 pips ✅ (< 30 cible)
- 01.08 (500%) : 0.3 pips ✅
- 17.09 (Std) : 0.3 pips ✅
- 05.09 (NFP) : 75.1 pips ❌ (outlier)

**Objectif Session 91 : Valider sur 10-15 dates**

---

### Critères Validation Réussie

```
✅ MAE global < 30 pips
✅ MAE NFP < 40 pips (3+ dates NFP)
✅ 0 outliers > 80 pips
✅ N ≥ 10 dates testées
✅ Amélioration vs Session 88 (31.7 pips)
```

**Si TOUS critères OK → Intégration immédiate**

---

## ⚡ COMMANDES RAPIDES

### Démarrage Session 91

```bash
# Lire docs
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/docs
cat SESSION90_RAPPORT_INTERMEDIAIRE.md | head -100
cat MESSAGE_SESSION90_SESSION91.md

# Tests validation (RECOMMANDÉ)
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90
chmod +x run_validation_complete.sh && ./run_validation_complete.sh

# OU manuel
python3 list_available_dates.py
# Configurer TEST_DATES
python3 test_multi_dates_extended.py

# Analyser résultats
cat validation_results_session90.csv
```

---

## 🎯 OBJECTIF FINAL SESSION 91

**Session 91 doit aboutir à :**

✅ Coefficient 0.55 validé robustement (10-15 dates)  
✅ MAE global < 30 pips confirmé  
✅ Outlier 05.09 expliqué ou exclu  
✅ Planificateur intégré production (si tests OK)  
✅ Documentation complète  
✅ Système prêt utilisation réelle

**OU (si corrections nécessaires) :**

✅ Diagnostic complet causes MAE élevé  
✅ Corrections identifiées et testées  
✅ Plan Session 92 pour intégration  
✅ Documentation diagnostic

---

## 📞 AIDE DÉCISION SESSION 91

**Question : Comment savoir si intégration possible ?**

Résultats `test_multi_dates_extended.py` montreront :
```
✅✅✅ VALIDATION RÉUSSIE !
   MAE < 30 pips : ✅ (XX.X)
   0 outliers    : ✅ (0)
   N ≥ 10        : ✅ (XX)

🎯 COEFFICIENT 0.55 VALIDÉ POUR PRODUCTION
```

**Si "VALIDATION RÉUSSIE" → Intégration**  
**Si "VALIDATION PARTIELLE" → Corrections puis intégration**  
**Si échec validation → Diagnostic approfondi**

---

## ✅ CHECKLIST SESSION 91

### Démarrage ⏳
- [ ] Lire MANDATORY_SESSION_RULES.md
- [ ] Lire project_state_new.md
- [ ] Lire SESSION90_RAPPORT_INTERMEDIAIRE.md
- [ ] Lire MESSAGE_SESSION90_SESSION91.md
- [ ] Valider mission avec utilisateur

### Tests ⏳
- [ ] Exécuter list_available_dates.py
- [ ] Ouvrir dates_disponibles_session90.csv
- [ ] Sélectionner 10-15 dates diversifiées
- [ ] Configurer TEST_DATES
- [ ] Exécuter test_multi_dates_extended.py
- [ ] Analyser résultats MAE

### Décision ⏳
- [ ] MAE < 30 ? Outliers ?
- [ ] Décider Scénario A/B/C

### Intégration (si A/B) ⏳
- [ ] Backup planner.py
- [ ] Intégrer calculate_amplification_extended
- [ ] Tests unitaires
- [ ] Tests Streamlit
- [ ] Documentation utilisateur

### Corrections (si C) ⏳
- [ ] Diagnostic approfondi
- [ ] Hypothèses corrections
- [ ] Implémentation
- [ ] Retests
- [ ] Plan Session 92

### Documentation ⏳
- [ ] Rapport SESSION91_RAPPORT_COMPLET.md
- [ ] Message SESSION91_SESSION92.md (si nécessaire)
- [ ] Mise à jour project_state_new.md
- [ ] Tokens affichés régulièrement

---

**Session 90 : ✅ RÉUSSIE - Scripts validation créés**  
**Session 91 : ⏳ VALIDATION ÉTENDUE + INTÉGRATION**  
**Budget disponible : 105k tokens (session fraîche)**

---

_Message transition Session 90 → Session 91_  
_Validation étendue coefficient 0.55_  
_26 octobre 2025_
