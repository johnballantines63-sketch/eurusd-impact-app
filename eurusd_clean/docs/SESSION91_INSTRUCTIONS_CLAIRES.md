# 🚀 SESSION 91 - INSTRUCTIONS CLAIRES ET PRÉCISES

**Date :** 26 octobre 2025  
**Mission :** Exécuter validation étendue + Décider intégration  
**Budget :** 105,000 tokens (session fraîche)

---

## ⚠️ RÈGLES IMPÉRATIVES DÉMARRAGE

**AVANT TOUT CODE, Claude DOIT :**

1. ✅ Lire `MANDATORY_SESSION_RULES.md`
2. ✅ Lire `project_state_new.md` 
3. ✅ Lire `SESSION90_RAPPORT_FINAL.md`
4. ✅ Lire ce fichier (`SESSION91_INSTRUCTIONS_CLAIRES.md`)
5. ✅ Afficher tokens régulièrement
6. ✅ **LIMITE TOKENS : 105,000 MAX (pas 190k)**

---

## 📊 CONTEXTE SESSION 90

**Ce qui a été fait :**
- ✅ 6 scripts validation créés
- ✅ Documentation complète
- ✅ Méthodologie établie

**Ce qui RESTE à faire (Session 91) :**
- ⏳ Exécuter les tests
- ⏳ Analyser résultats
- ⏳ Décider intégration ou corrections

**Pourquoi Session 91 ?**
- Session 90 : 102,832 / 105,000 tokens (98%)
- Tests validation = 20-30k tokens
- Besoin budget frais

---

## 🎯 MISSION SESSION 91 - SIMPLE ET CLAIRE

### Phase 1 : Trouver les dates à tester (5k tokens)

**Action :** Exécuter script qui liste dates disponibles

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90
python3 list_available_dates.py
```

**Ce script va :**
- Scanner la DB pour dates HIGH IMPACT
- Afficher Top 20 dates dans console
- Créer CSV `dates_disponibles_session90.csv`

**Durée :** 30 secondes

---

### Phase 2 : Sélectionner 10-15 dates (collaboration utilisateur)

**Après exécution Phase 1, Claude doit :**

1. **Afficher les résultats console** au complet
2. **Indiquer le chemin du CSV créé**
3. **Demander à l'utilisateur** : "Quelle(s) date(s) veux-tu tester ?"

**Options pour l'utilisateur :**

**A) Test rapide (3 dates Session 89) :**
- Juste valider que ça marche
- Durée : 5 min
- Réponse : "Lance avec les 3 dates actuelles"

**B) Validation complète (10-15 dates) :**
- Utilisateur ouvre CSV
- Utilisateur choisit dates
- Utilisateur donne liste à Claude
- Claude configure TEST_DATES
- Durée : 30-40 min

**C) Semi-automatique (5-7 dates) :**
- Claude propose 5-7 dates du CSV
- Utilisateur valide
- Claude configure TEST_DATES
- Durée : 15-20 min

---

### Phase 3 : Configuration TEST_DATES (5k tokens)

**Si utilisateur choisit dates, Claude doit :**

1. Éditer `test_multi_dates_extended.py` ligne 31
2. Ajouter les dates au format :

```python
TEST_DATES = [
    # Session 89 (GARDER)
    {'date': '2025-08-01', 'time': '12:30:00', 'name': '01 Août (NFP 500%)', 'type': 'NFP'},
    {'date': '2025-09-17', 'time': '12:30:00', 'name': '17 Sept (Standard)', 'type': 'CPI'},
    {'date': '2025-09-05', 'time': '12:30:00', 'name': '05 Sept (NFP)', 'type': 'NFP'},
    
    # DATES AJOUTÉES SESSION 91
    {'date': 'YYYY-MM-DD', 'time': '12:30:00', 'name': 'Description', 'type': 'NFP/CPI/Jobless/Retail'},
    # ... autres dates
]
```

**⚠️ IMPORTANT :** Garder les 3 dates Session 89 !

---

### Phase 4 : Exécution validation (15-20k tokens)

**Action :** Lancer le test

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session90
python3 test_multi_dates_extended.py
```

**Ce script va :**
1. Charger événements pour chaque date
2. Calculer prédictions (coefficient 0.55)
3. Mesurer impacts réels (prix DB)
4. Calculer erreurs (MAE)
5. Afficher résultats

**Durée :**
- 3 dates : 2-5 min
- 10 dates : 10-15 min
- 15 dates : 15-20 min

**Claude doit :** Attendre et afficher résultats complets

---

### Phase 5 : Analyse résultats (10-15k tokens)

**Le script affichera un tableau comme :**

```
📊 RÉSUMÉ VALIDATION ÉTENDUE
┌─────────────────────┬──────┬────────┬─────────┬────────┬─────────┬────────┐
│ Date                │ Type │ Évts   │ Surpr   │ Prédit │ Réel    │ Erreur │
├─────────────────────┼──────┼────────┼─────────┼────────┼─────────┼────────┤
│ 01 Août (NFP 500%)  │ NFP  │ 17     │ 500.0%  │ 106.9p │ 173.8p  │ 66.9p ❌│
│ 17 Sept (Standard)  │ CPI  │ 13     │ 33.3%   │ 45.2p  │ 45.5p   │ 0.3p ✅│
│ ...                 │ ...  │ ...    │ ...     │ ...    │ ...     │ ...    │
└─────────────────────┴──────┴────────┴─────────┴────────┴─────────┴────────┘

📊 STATISTIQUES GLOBALES :
   MAE global    : XX.X pips
   Tests < 30    : X/X (XX%)
   Outliers > 80 : X
```

**Claude doit analyser :**

1. **MAE global :**
   - < 25 pips : ✅ Excellent
   - 25-30 pips : ✅ Acceptable
   - 30-40 pips : ⚠️ Moyen
   - > 40 pips : ❌ Problématique

2. **Outliers (erreur > 80 pips) :**
   - 0 outliers : ✅ Parfait
   - 1-2 outliers : ⚠️ Acceptable si expliqué
   - 3+ outliers : ❌ Problème formule

3. **MAE par type :**
   - NFP < 40 pips : ✅
   - CPI < 30 pips : ✅
   - Jobless < 25 pips : ✅
   - Retail < 20 pips : ✅

---

### Phase 6 : Décision (5k tokens)

**Claude doit recommander UNE des 3 options :**

---

#### OPTION A : Intégration Immédiate ✅

**Conditions :**
- MAE global < 30 pips
- 0-1 outliers
- N ≥ 10 dates testées

**Action Session 91 :**
→ Intégrer `calculate_amplification_extended()` dans `planner.py`

**Budget restant :** 30-40k tokens

---

#### OPTION B : Ajustements Mineurs ⚠️

**Conditions :**
- MAE global 30-40 pips
- 1-2 outliers
- Pattern identifiable

**Action Session 91 :**
→ Tester coefficient alternatif (0.50 ou 0.60)
→ Retester 3-5 dates clés
→ Si OK → Intégrer

**Budget restant :** 40-50k tokens

---

#### OPTION C : Report Session 92 ❌

**Conditions :**
- MAE global > 40 pips
- 3+ outliers
- Pas de pattern clair

**Action Session 91 :**
→ Diagnostic approfondi seulement
→ Documentation causes
→ Intégration reportée Session 92

**Budget restant :** Utiliser pour documentation

---

### Phase 7 : Intégration (si Option A) (30-40k tokens)

**Seulement si MAE < 30 et validation OK**

#### 7.1 Backup

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app
cp planner.py planner.py.backup_session91_avant_integration
```

#### 7.2 Localiser le code à modifier

**Fichier :** `fx_impact_app/planner.py`

**Chercher la ligne avec :** `amplification = 2.5` ou `amplification = XXX`

#### 7.3 Modifications

**Import à ajouter (début fichier, après autres imports) :**
```python
from formulas_validated import calculate_amplification_extended
```

**Remplacer l'ancienne amplification par :**
```python
# Calculer surprise max
surprise_max = max([event.get('surprise_pct', 0) for event in events])

# Amplification dynamique (coefficient 0.55 validé Session 89-91)
amplification = calculate_amplification_extended(surprise_max)
```

#### 7.4 Tests

- Lancer Streamlit
- Tester 1-2 dates via interface
- Vérifier que l'amplification s'affiche correctement

---

### Phase 8 : Documentation (15-20k tokens)

**TOUJOURS créer (peu importe Option A/B/C) :**

1. `SESSION91_RAPPORT_COMPLET.md` dans `/docs`
   - Résultats tests
   - Analyse MAE
   - Décision prise
   - Actions effectuées

2. `MESSAGE_SESSION91_SESSION92.md` (si nécessaire)
   - Seulement si intégration non faite
   - Instructions Session 92

3. Mise à jour `project_state_new.md`
   - Section Session 91
   - État coefficient 0.55
   - Prochaines étapes

---

## 🚫 ERREURS À ÉVITER

### Erreur 1 : Ne pas attendre résultats complets

❌ **Mauvais :**
```
Script lancé... *passe à l'étape suivante*
```

✅ **Bon :**
```
Script lancé... *affiche TOUS les résultats* → Analyse
```

---

### Erreur 2 : Intégrer sans validation

❌ **Mauvais :**
MAE = 35 pips → Intégrer quand même

✅ **Bon :**
MAE = 35 pips → Option B (ajustements) ou C (diagnostic)

---

### Erreur 3 : Oublier backup

❌ **Mauvais :**
Modifier `planner.py` directement

✅ **Bon :**
Backup PUIS modification

---

### Erreur 4 : Ignorer outliers

❌ **Mauvais :**
"3 outliers mais MAE global OK donc j'intègre"

✅ **Bon :**
"3 outliers = problème à comprendre d'abord"

---

## 📊 BUDGET TOKENS SESSION 91

```
Lecture docs :           5,000 tokens
Phase 1 (liste dates) :  5,000 tokens
Phase 2 (sélection) :    2,000 tokens
Phase 3 (config) :       5,000 tokens
Phase 4 (tests) :       20,000 tokens
Phase 5 (analyse) :     15,000 tokens
Phase 6 (décision) :     5,000 tokens
Phase 7 (intégration) : 30,000 tokens (si Option A)
Phase 8 (documentation): 20,000 tokens
─────────────────────────────────────────────
TOTAL Option A :        107,000 tokens ⚠️
```

**⚠️ IMPORTANT :**
- Si Option A : Documentation minimale (10k au lieu de 20k)
- Si Option B/C : Pas d'intégration (économise 30k)

---

## ⚡ WORKFLOW RÉSUMÉ

```
1. list_available_dates.py
   ↓ (30 sec)
   
2. Demander dates à utilisateur
   ↓ (2 min)
   
3. Configurer TEST_DATES
   ↓ (5 min)
   
4. test_multi_dates_extended.py
   ↓ (10-20 min)
   
5. Analyser résultats MAE
   ↓ (5 min)
   
6. Recommander Option A/B/C
   ↓ (2 min)
   
7. Si A → Intégrer planner.py
   Si B → Ajuster + retest
   Si C → Documentation seulement
   ↓ (20-40 min)
   
8. Documentation finale
   ✅ (15 min)
```

**Durée totale : 1h - 1h30**

---

## 🎯 MESSAGE POUR CLAUDE SESSION 91

**Cher Claude,**

**Mission simple :**
1. Lance `list_available_dates.py`
2. Demande-moi quelles dates tester
3. Configure et lance `test_multi_dates_extended.py`
4. Analyse le MAE global
5. Recommande Option A/B/C
6. Exécute l'option choisie
7. Documente

**Surtout :**
- ✅ Affiche TOUS les résultats
- ✅ Respecte limite 105k tokens
- ✅ Demande confirmation avant intégration
- ✅ Backup avant modification

**Tu es prêt !** 🚀

---

_Instructions claires Session 91_  
_26 octobre 2025_
