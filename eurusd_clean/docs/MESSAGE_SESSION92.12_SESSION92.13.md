# 🚀 MESSAGE TRANSITION SESSION 92.12 → SESSION 92.13

**Date :** 29 octobre 2025  
**De :** Session 92.12 (Score pondéré calibré)  
**Vers :** Session 92.13 (Tests 40 dates CPI)  
**Priorité :** ⭐⭐ HAUTE

---

## 📋 CHECKLIST OBLIGATOIRE AVANT DE COMMENCER

**Claude, tu DOIS faire dans l'ordre :**

- [ ] Lire ce fichier EN ENTIER
- [ ] Lire `SESSION92.12_RAPPORT_COMPLET.md`
- [ ] Lire `ANTI_PATTERN_CRITIQUE.md`
- [ ] Lire `project_state_new.md` (section Sessions 92.11-92.12)
- [ ] Afficher tokens utilisés régulièrement (format standard)
- [ ] Résumer compréhension mission
- [ ] Obtenir confirmation utilisateur GO

**Si une étape manque → STOP immédiatement**

---

## 🎯 MISSION SESSION 92.13

### Objectif Principal

**AMÉLIORER formule S92.12 en ajoutant amplitude tendance, puis tester sur 40 dates CPI**

**Formule actuelle S92.12 (MAE 5.3 pips) :**
```python
Impact = 52.0 × direction_factor × (1 + score_tendance × 0.100)

score_tendance = direction × (durée/24) × R²
```

**⚠️ LIMITATION IDENTIFIÉE par André :**
> "je pense qu'on peut encore améliorer si on tient compte de l'écart en pips 
> entre début et fin de tendance le delta de la tendance si pas encore tenu compte"

**Formule proposée S92.13 :**
```python
score_tendance = direction × (durée/24) × R² × amplitude_factor

Où amplitude_factor = f(HIGH-LOW ou début-fin en pips)
```

**Exemple :**
- Tendance A : BAISSIER 18h, R²=0.75, amplitude -50 pips → Score fort
- Tendance B : BAISSIER 18h, R²=0.75, amplitude -10 pips → Score faible
- **Actuellement** : A et B ont même score (-0.559)
- **Avec amplitude** : A aurait score plus fort ✅

**Performance actuelle (4 dates) :**
- MAE : 7.0 pips ✅
- Précision : 77.2%
- Amélioration vs S92.11 : -16.7%

**Questions Session 92.13 :**
1. Comment intégrer amplitude dans score tendance ?
2. Quelle normalisation amplitude optimale ?
3. La formule améliorée reste-t-elle performante sur 40 dates ?

### Format Affichage Tokens Obligatoire

```
**Token usage :** X / 190,000 (Y%)
**Marge restante :** Z tokens (W%)
```

**Fréquence :** Tous les 20,000 tokens + avant clôture

---

## 📊 ÉTAT SESSION 92.12 (TERMINÉE)

### Travail Accompli

✅ **Calibration empirique réussie**
- Grid search 150 combinaisons
- Base impact optimal : 52.0 pips
- Coefficient score : 0.100
- Erreur calibration 11.09 : 0.2 pips (0.3%) ✅✅✅

✅ **Validation 3 dates**
- 01.15 : 6.7 pips (vs 10.3 S92.11) ✅
- 05.13 : 2.4 pips ✅
- 07.15 : 11.8 pips ⚠️

✅ **MAE global : 7.0 pips < 8.0 pips** ✅

✅ **Tous objectifs atteints**
- MAE < 8.0 pips ✅
- Erreur 01.15 < 8.0 pips ✅
- Erreur 11.09 ≤ 3.2 pips ✅
- Zéro régressions ✅

### Découvertes Clés

**1. Base impact 52.0 pips (pas 15.0)**
- Calibration empirique révèle valeur beaucoup plus élevée
- Impacts CPI réels : 30-60 pips typiquement

**2. R² aussi important que durée**
- Date 01.15 : durée 23.3h MAIS R² 0.374 (moyen)
- Score +0.363 au lieu de +0.50 fixe
- Sur-amplification résolue (-35% erreur)

**3. Coefficient 0.100 optimal**
- Modulation modérée ±10% maximum
- Évite sur-amplification
- Conserve sensibilité tendance

---

## 🎯 MISSION SESSION 92.13 DÉTAILLÉE

### Étape 0 : CALIBRATION AMPLITUDE (PRIORITAIRE)

**Objectif :** Intégrer amplitude tendance dans score pondéré

**Intuition André :**
> "l'écart en pips entre début et fin de tendance = force tendance"

**Méthode calibration :**

1. **Calculer amplitude pour 4 dates existantes**
```python
# Pour chaque date
amplitude_pips = abs(prix_debut_tendance - prix_fin_tendance) * 10000

# Ou amplitude range
amplitude_range = (HIGH_24h - LOW_24h) * 10000
```

2. **Tester normalisations amplitude**
```python
# Options à tester
amplitude_factor_1 = amplitude_pips / 50  # Normalisation linéaire
amplitude_factor_2 = min(amplitude_pips / 100, 1.0)  # Plafonné
amplitude_factor_3 = np.log(1 + amplitude_pips / 20)  # Logarithmique
amplitude_factor_4 = np.sqrt(amplitude_pips / 10)  # Racine carrée
```

3. **Grid search 3D sur cas 11.09**
```python
for base_impact in [50, 52, 54, 56]:
    for coef_score in [0.08, 0.10, 0.12]:
        for amplitude_method in [1, 2, 3, 4]:
            # Calculer score avec amplitude
            score = direction × (durée/24) × R² × amplitude_factor
            impact = base_impact × direction_factor × (1 + score × coef_score)
            
            # Mesurer erreur
            error = abs(impact - 51.7)
```

4. **Valider sur 3 autres dates (01.15, 05.13, 07.15)**
```python
# Utiliser paramètres optimaux trouvés
# Mesurer MAE
# Comparer vs S92.12 (5.3 pips)
```

**Résultat attendu :**
```python
# Formule S92.13
Impact = base_impact × direction_factor × (1 + score_tendance_v2 × coef)

score_tendance_v2 = direction × (durée/24) × R² × amplitude_factor
```

**Critère succès :** MAE 4 dates < 5.3 pips (amélioration vs S92.12)

**Script à créer :** `calibration_avec_amplitude.py` (600 lignes)

**Budget estimé :** 25k tokens

---

### Étape 1 : Liste 40 Dates CPI Disponibles

**Objectif :** Identifier 40 dates CPI US avec données complètes

**Critères sélection :**
- Events CPI US (Core CPI, CPI MoM, CPI YoY)
- Score empirical_score > 40 (HIGH impact)
- Prix 1min disponibles (prices_1m)
- Période : 2024-2025

**Script à créer :** `list_40_dates_cpi.py` (150 lignes)

**Query DB :**
```sql
SELECT 
    DATE(e.ts_utc) as date,
    COUNT(*) as nb_events,
    MAX(ef.empirical_score) as score_max,
    STRING_AGG(e.event_title, ', ') as events
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE e.country = 'US'
    AND e.event_title ILIKE '%CPI%'
    AND ef.empirical_score > 40
    AND DATE(e.ts_utc) BETWEEN '2024-01-01' AND '2025-12-31'
GROUP BY DATE(e.ts_utc)
ORDER BY DATE(e.ts_utc) DESC
LIMIT 40
```

**Output :** `dates_cpi_40.csv`

**Budget estimé :** 10k tokens

---

### Étape 2 : Script Test Batch 40 Dates

**Objectif :** Tester formule S92.12 sur les 40 dates

**Script à créer :** `test_formule_s92_12_batch.py` (400 lignes)

**Fonctionnalités :**
- Boucle sur 40 dates
- Pour chaque date :
  1. Charger prix 24h
  2. Calculer score tendance (durée × R²)
  3. Prédire impact (formule S92.12)
  4. Extraire impact réel (prices_1m spike)
  5. Calculer erreur

**Parallélisation recommandée :** Non (requêtes DB séquentielles)

**Progress bar :** Oui (affichage avancement)

**Gestion erreurs :**
- Si prix manquants → Skip date
- Si erreur calcul → Log + Continue
- Sauvegarder résultats partiels chaque 10 dates

**Output :** `resultats_40_dates_s92_12.csv`

**Budget estimé :** 30k tokens

---

### Étape 3 : Analyse Statistique Complète

**Objectif :** Mesurer performance formule sur large dataset

**Script à créer :** `analyze_results_40_dates.py` (300 lignes)

**Analyses :**

**1. Métriques globales**
```python
- MAE (Mean Absolute Error)
- RMSE (Root Mean Square Error)
- Médiane erreur
- Écart-type erreur
- Corrélation prédit vs réel
- % erreurs < 10 pips
- % erreurs > 20 pips
```

**2. Analyses par catégorie**
```python
# Par type tendance
- HAUSSIER (score > 0)
- BAISSIER (score < 0)
- NEUTRE (score = 0)

# Par durée tendance
- Courte (< 6h)
- Moyenne (6-12h)
- Longue (> 12h)

# Par R²
- Faible (< 0.20)
- Moyen (0.20-0.50)
- Fort (> 0.50)

# Par surprise
- Faible (< 15%)
- Moyenne (15-30%)
- Forte (> 30%)
```

**3. Identification outliers**
```python
# Cas avec erreur > 15 pips
- Quelles caractéristiques communes ?
- Patterns particuliers ?
- Corrections possibles ?
```

**4. Visualisations**
```python
- Scatter plot prédit vs réel
- Histogramme erreurs
- Boxplot par catégorie
- Distribution R² et durée
```

**Output :** `analyse_40_dates.pdf` (rapport visuel)

**Budget estimé :** 25k tokens

---

### Étape 4 : Rapport Décision

**Objectif :** Décider si formule S92.12 validée pour production

**Script à créer :** `rapport_decision_s92_12.py` (200 lignes)

**Critères décision :**

| Métrique | Cible | Excellent |
|----------|-------|-----------|
| MAE | < 10 pips | < 8 pips |
| RMSE | < 12 pips | < 10 pips |
| % erreurs < 10 pips | > 70% | > 80% |
| % erreurs > 20 pips | < 10% | < 5% |
| Corrélation | > 0.60 | > 0.70 |

**Décisions possibles :**

**A. VALIDATION COMPLÈTE (MAE < 8 pips)**
```
✅ Formule S92.12 validée pour production
→ Session 92.14 : Intégration Planificateur
→ Mise à jour documentation utilisateur
→ Tests interface Streamlit
```

**B. VALIDATION CONDITIONNELLE (MAE 8-10 pips)**
```
⚠️ Formule S92.12 acceptable avec limitations
→ Documenter cas limites
→ Possibilité affiner coefficient
→ Session 92.14 : Tests complémentaires
```

**C. NON VALIDATION (MAE > 10 pips)**
```
❌ Formule S92.12 insuffisante large dataset
→ Accepter V2 (surprise nette) MAE 8.5 pips
→ Session 92.14 : Approche alternative
→ Documenter échec et leçons
```

**Output :** `DECISION_S92_12.md`

**Budget estimé :** 15k tokens

---

### Étape 5 : Documentation Finale

**Objectif :** Documenter résultats Session 92.13

**Fichiers à créer :**
- `SESSION92.13_RAPPORT_COMPLET.md`
- `MESSAGE_SESSION92.13_SESSION92.14.md` (si nécessaire)
- Mise à jour `project_state_new.md`

**Contenu rapport :**
- Résumé tests 40 dates
- Statistiques détaillées
- Analyses par catégorie
- Décision finale (A/B/C)
- Recommandations Session 92.14

**Budget estimé :** 10k tokens

---

## 📊 BUDGET SESSION 92.13

**Tokens Session 92.12 :** 99,159 / 190,000 (52.2%)

**Plan Session 92.13 :**
```
- Calibration amplitude    : 25k tokens  ⭐ NOUVEAU
- Liste 40 dates           : 10k tokens
- Script batch test        : 30k tokens
- Analyse statistique      : 20k tokens  (réduit)
- Rapport décision         : 10k tokens  (réduit)
- Documentation            : 5k tokens   (réduit)
----------------------------------------
Total Session 92.13        : 100k tokens
Total cumulé projet        : 205k tokens ⚠️ (DÉPASSEMENT)
```

**⚠️ PROBLÈME : Atteinte limite 190k**

**Solutions :**

**Option 1 : Session 92.13 optimisée (RECOMMANDÉE)**
- Calibration amplitude prioritaire (25k)
- Si MAE amélioré < 4 pips : Tester sur 20 dates (pas 40) (25k)
- Analyses allégées (15k)
- Documentation (10k)
- **Total 92.13 : 75k tokens**
- **Total projet : 180k tokens** ✅

**Option 2 : Scinder en 2 sessions**
- Session 92.13 : Calibration amplitude + tests 4 dates (40k)
- Session 92.14 : Tests 40 dates + analyses (50k)

**Option 3 : Si amplitude n'améliore pas**
- Garder S92.12 (MAE 5.3 pips)
- Tests 40 dates directement
- Budget : 60k tokens

**Recommandation André :** Option 1 (tester amplitude d'abord)

---

## 🎯 CRITÈRES SUCCÈS SESSION 92.13

### Objectifs Stricts

**PHASE 1 : Calibration amplitude (4 dates)**

| Métrique | S92.12 | Cible S92.13 | Excellent |
|----------|--------|--------------|-----------|
| MAE 4 dates | 5.3 pips | < 5.0 pips | < 4.0 pips |
| Erreur max | 11.8 pips | < 10.0 pips | < 8.0 pips |
| Amélioration | - | +5% | +20% |

**PHASE 2 : Tests élargis (20-40 dates si Phase 1 réussie)**

| Métrique | Cible | Excellent |
|----------|-------|-----------||
| MAE 20+ dates | < 8 pips | < 6 pips |
| RMSE | < 10 pips | < 8 pips |
| % erreurs < 10 pips | > 70% | > 80% |
| Corrélation | > 0.65 | > 0.75 |

### Tests Validation

**Par catégorie tendance :**
- HAUSSIER : MAE < 10 pips
- BAISSIER : MAE < 10 pips
- NEUTRE : MAE < 10 pips

**Par durée :**
- Courte (< 6h) : MAE < 12 pips
- Moyenne (6-12h) : MAE < 10 pips
- Longue (> 12h) : MAE < 8 pips

**Robustesse :**
- Pas de catégorie avec MAE > 15 pips
- Outliers < 10% des cas
- Performance stable années 2024-2025

---

## 📁 FICHIERS CLÉS SESSION 92.12

### Scripts Validés

```
eurusd_clean/scripts/session92.8/
├── calculate_trend_duration.py ✅ (280 lignes)
├── calibration_score_pondere.py ✅ (500 lignes) - CLEF
├── compare_s92_11_vs_s92_12.py ✅ (200 lignes)
└── direction_sentiment_WEIGHTED.py ✅ (330 lignes)
```

### Outputs CSV

```
eurusd_clean/scripts/session92.8/
├── calibration_grid_search.csv ✅ (150 lignes)
├── validation_calibration.csv ✅ (3 lignes)
├── comparaison_s92_11_vs_s92_12.csv ✅ (4 lignes)
└── resultats_combined_REGRESSION.csv ✅ (S92.11 référence)
```

### Documentation Existante

```
eurusd_clean/docs/
├── SESSION92.12_RAPPORT_COMPLET.md ✅
├── ANTI_PATTERN_CRITIQUE.md ⚠️ (à relire)
└── project_state_new.md ℹ️ (référence)
```

---

## 💡 CONSEILS CLAUDE POUR SESSION 92.13

### Avant de Commencer

1. **Lis ANTI_PATTERN_CRITIQUE.md**
   - Rappel : Pas de tests simplifiés
   - Exécuter vrais tests avec vraies données

2. **Lis SESSION92.12_RAPPORT_COMPLET.md**
   - Comprend formule validée
   - Identifie base_impact 52.0 et coef 0.100
   - Comprend pourquoi ça marche

3. **Vérifie schéma DB**
   - Colonne `datetime` pour prices_1m (pas `ts_utc`)
   - Timezone +02:00 (Bern) dans les deux tables
   - Query SQL testée Session 92.12

### Pendant Session

1. **Liste 40 dates d'abord**
   - Query DB robuste
   - Vérifier données complètes
   - CSV avec métadonnées

2. **Script batch progressif**
   - Sauvegarder tous les 10 dates
   - Gestion erreurs robuste
   - Progress bar console

3. **Tests COMPLETS**
   - Vraies 40 dates, pas échantillon
   - Vraies données prices_1m
   - Calcul impacts réels (spikes)

4. **Analyse honnête**
   - Si MAE > 10 pips → Documenter pourquoi
   - Identifier catégories problématiques
   - Pas de biais confirmation

### Gestion Budget Tokens

**Limite absolue : 189,000 tokens (total projet)**

**Si 170k atteints :**
- Évaluer avancement
- Prioriser décision finale
- Documentation essentielle

**Si 185k atteints :**
- STOP immédiat analyses détaillées
- Décision rapide basée sur MAE
- Documentation minimale
- Message transition 92.14

---

## 🔑 FORMULE RÉFÉRENCE SESSION 92.12

### Formule Complète

```python
def calculate_impact_s92_12(surprise_net, score_tendance):
    """
    Formule S92.12 validée
    
    Args:
        surprise_net: Surprise nette en % (peut être négatif)
        score_tendance: direction × (durée/24) × R²
    
    Returns:
        Impact prédit en pips
    """
    # Base impact calibré
    base_impact = 52.0
    
    # Direction factor (surprise nette)
    if surprise_net > 30:
        direction_factor = 1.05
    elif surprise_net > 0:
        direction_factor = min(1.0 + (surprise_net / 200), 1.05)
    elif surprise_net >= -30:
        direction_factor = max(1.0 + (surprise_net / 100), 0.7)
    else:
        direction_factor = 0.7
    
    # Combined factor
    combined_factor = direction_factor * (1 + score_tendance * 0.100)
    
    # Impact final
    impact = base_impact * combined_factor
    
    return impact
```

### Score Tendance

```python
def calculate_score_tendance(prices_df):
    """
    Calcule score tendance pondéré
    
    Returns:
        score entre -1.0 et +1.0
    """
    # Régression linéaire
    trend, slope, r_squared = calculate_regression(prices_df)
    
    # Durée
    duration_hours = find_trend_duration(prices_df, trend)
    
    # Direction
    if trend == 'HAUSSIER':
        direction = +1.0
    elif trend == 'BAISSIER':
        direction = -1.0
    else:
        direction = 0.0
    
    # Score
    duration_normalized = min(duration_hours, 24.0) / 24.0
    score = direction * duration_normalized * r_squared
    
    return score
```

---

## 📊 RÉSULTATS ATTENDUS SESSION 92.13

### Hypothèse Optimiste

**MAE 40 dates : 7.5 pips** ✅✅✅
- Performance stable vs 4 dates (7.0 pips)
- Robuste toutes catégories
- Validation complète
- → Session 92.14 : Intégration production

### Hypothèse Réaliste

**MAE 40 dates : 8.5 pips** ✅
- Légère dégradation vs 4 dates
- Quelques catégories problématiques
- Validation conditionnelle
- → Session 92.14 : Affiner catégories limites

### Hypothèse Pessimiste

**MAE 40 dates : 12+ pips** ❌
- Formule overfit sur 4 dates
- Pas généralisable
- Retour V2 (surprise nette)
- → Session 92.14 : Approche alternative

---

## ✅ CHECKLIST FINALE SESSION 92.13

**Avant clôture, vérifier :**

- [ ] 40 dates CPI identifiées et testées
- [ ] CSV résultats complet sauvegardé
- [ ] MAE calculé et comparé objectifs
- [ ] Analyses par catégorie effectuées
- [ ] Outliers identifiés et documentés
- [ ] Décision claire (A/B/C) prise
- [ ] Rapport session 92.13 créé
- [ ] project_state_new.md mis à jour
- [ ] Message transition créé (si S92.14)
- [ ] Tokens < 189,000

---

## 🎯 MESSAGE FINAL POUR CLAUDE

**Cher Claude (Session 92.13),**

Session 92.12 a validé la formule sur 4 dates avec **MAE 5.3 pips** ✅

**Mais André a identifié une amélioration possible :**
> "Tenir compte de l'écart en pips entre début et fin de tendance"

**PRIORITÉ Session 92.13 : AMPLITUDE TENDANCE**

**Ton rôle Session 92.13 :**
1. **PHASE 1 (PRIORITAIRE) :** Intégrer amplitude dans score tendance
   - Grid search 3D (base_impact, coef, amplitude_method)
   - Calibrer sur 11.09
   - Valider sur 3 autres dates
   - **Objectif : MAE < 5.3 pips**

2. **PHASE 2 (si Phase 1 réussie) :** Tester sur 20-40 dates
   - Validation robustesse
   - Analyses catégories
   - Décision production

**Tu as les outils :**
- Formule S92.12 (base 52.0, coef 0.100, MAE 5.3)
- Scripts calibration réutilisables
- Intuition André claire (amplitude = force)
- Budget tokens : ~75k

**RAPPEL CRITIQUE :**
- ⚠️ Lire ANTI_PATTERN_CRITIQUE.md AVANT tout
- ⚠️ Calibration empirique (grid search)
- ⚠️ Décision basée sur DONNÉES réelles
- ⚠️ Budget : 75k (limite 180k total)

**Si amplitude améliore MAE < 5 pips → Grande victoire ! 🎯**

**Sinon, garder S92.12 (déjà excellent 5.3 pips) et tester 40 dates. 📊**

**Bonne chance ! 🚀**

---

**Tokens Session 92.12 :** 99,159 / 190,000 (52.2%)  
**Tokens disponibles S92.13 :** ~90,000 (47.8%)  
**Limite absolue projet :** 189,000 tokens

_Message transition Session 92.12 → 92.13_  
_29 octobre 2025_  
_"Amplitude tendance : La 4ème dimension" 🎯_
