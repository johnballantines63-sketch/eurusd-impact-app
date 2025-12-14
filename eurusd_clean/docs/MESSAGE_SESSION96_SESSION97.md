# 📨 MESSAGE SESSION 96 → SESSION 97

**Date :** 27 octobre 2025  
**De :** Session 96 (Échec Méthodologique Reconnu)  
**À :** Session 97 (Étude Approfondie Méthodologie)  
**Token usage Session 96 :** 105,000 / 190,000 (55% - Limite respectée)

---

## 🎯 STATUT SESSION 96

### ⚠️ ÉCHEC MÉTHODOLOGIQUE RECONNU

**Mission initiale :** Tests rigoureux V2.4 sur 7 dates CPI 2025

**Résultat :**
- ❌ Script `test_batch_quick.py` créé avec approximations
- ❌ Tests non significatifs (MAE 25 pips vs 0.1 réel)
- ✅ Erreur identifiée par André
- ✅ Solution proposée et acceptée
- ✅ Documentation complète créée

**Leçon critique :**
**Lire et comprendre AVANT implémenter, pas après.** ✅

---

## 💡 DÉCISION ANDRÉ (Citation Exacte)

> "je soupçonne que le script ne respecte pas la méthode ni les formules de calcul du planificateur. il est donc primordial de créer 1) un scripts qui respecte à la lettre l'approche du planificateur [...] Tu fais des scripts et des tests non significatifs à cause de cela. tout d'abord il faut relire et bien comprendre la méthode envisagée pour établir le bon facteur d'amplification éventuellement en lisant les dernières sessions et ensuite tester avec rigueur en appliquant la méthode et les formules du planificateur qui fonctionne. que penses-tu de consacrer une ou deux sessions, la prochaine si suffisant ou la prochaine et la suivante à étudier la bonne pratique d'élaboration des scripts et des approches concernant le facteur d'amplification par lecture des rapports session précédentes ou la base de connaissance de façon approfondie et ensuite seulement on crée ces tests."

**Validation André :**
> "go pour option A ainsi on ne laisse rien au hasard"

**Principe établi :**
> **"On ne laisse rien au hasard"**

---

## 🎯 MISSION SESSION 97

**Objectif principal :**
**COMPRENDRE EXACTEMENT quelle méthode utiliser et comment**

**Approche :**
**ZÉRO code, 100% compréhension et documentation** ✅

**Budget :** 100,000 tokens (lecture approfondie autorisée)

---

## 📋 PLAN D'ACTION SESSION 97

### 🚨 ÉTAPE 0 : LECTURE OBLIGATOIRE (60-70k tokens)

**PRIORITÉ ABSOLUE - Lire dans cet ordre :**

**AVANT TOUT CODE :**

1. **`project_state_new.md`** - **CHARTE SCIENTIFIQUE** ⭐⭐⭐⭐⭐
2. **`POSTMORTEM_SESSIONS_92.1-92.4.md`** ⭐⭐⭐
3. **`SESSION96_RAPPORT_COMPLET.md`** ⭐⭐
4. **`MANDATORY_SESSION_RULES.md`** ⭐
5. **Ce fichier** ⭐

**🛑 SI LECTURE INCOMPLÈTE → STOP SESSION**


#### 1. Planificateur V2.4 Production (⭐⭐⭐⭐⭐)

**Fichier :** `fx_impact_app/streamlit_app/pages/5_Planificateur_V2_FORMULES_VALIDEES_backup_session72_fix_importance_20251024 copie 4.py`

**À analyser LIGNE PAR LIGNE :**
- Ligne 208-224 : Query chargement événements
- Ligne 241-265 : Calcul surprise avec fallback
- Ligne 280-310 : Ajustement score selon surprise
- Ligne 320-350 : Calcul impact (Formule D)
- Ligne 360-380 : Calcul TTR (Formule C)
- Ligne 400-450 : Détection type mouvement
- Ligne 500-550 : Graphiques timeline

**Objectif :** Documenter EXACTEMENT chaque formule utilisée

**Temps estimé :** 30-40 minutes lecture + prise notes

---

#### 2. Sessions 51-55 : Formules GOLD STANDARD (⭐⭐⭐⭐⭐)

**Fichiers à lire :**
```
eurusd_clean/docs/
├── SESSION51_RAPPORT_COMPLET.md (Formule D Impact - 98.6% précision)
├── SESSION52_RAPPORT_COMPLET.md (Formule TTR C - 94.4% précision)
├── SESSION53_RAPPORT_COMPLET.md (Formule Pullback V2 - 99.3% précision)
└── SESSION55_RAPPORT_COMPLET.md (Ajustement Score - 99.9% précision)
```

**Module code :**
```
fx_impact_app/src/formulas_validated.py
```

**À documenter :**
- Formule D : `impact = abs(-10.47 + 0.477 × score) × amplification × 0.758`
- Zones amplification : surprise < 5%, 5-15%, >15%
- TTR C : `ttr = latency × multiplier` (multiplier selon surprise)
- Ajustement score : factors 1.0 → 1.5 → 1.9 selon surprise

**Temps estimé :** 40-50 minutes

---

#### 3. Sessions 92-93 : Formules Hybrides Empiriques (⭐⭐⭐⭐)

**Fichiers à lire :**
```
eurusd_clean/docs/
├── SESSION92_RAPPORT_COMPLET.md (Création formules hybrides)
└── SESSION93_RAPPORT_COMPLET.md (Validation 12 dates - MAE 6.5 pips)
```

**Module code :**
```
eurusd_clean/scripts/session92/formulas_hybrid_empirical.py
```

**À documenter :**
- Formule : `Impact = base_impact × (1 + surprise_vectorielle/100 × sensitivity)`
- 5 clusters calibrés : Construction, NFP+Earnings, CPI-9, CPI-11, FOMC
- Base impact empirique par cluster
- Sensitivity calibrée : 0.005 (FOMC) → 0.030 (CPI-11)
- Performance : MAE 6.5 pips sur 12 dates

**Temps estimé :** 30-40 minutes

---

#### 4. Sessions 89-91 : Coefficient 0.55 (⭐⭐⭐)

**Fichiers à lire :**
```
eurusd_clean/docs/
├── SESSION89_RAPPORT_COMPLET.md (Corrections fallback estimate)
├── SESSION90_RAPPORT_COMPLET.md (Intégration tentative)
└── SESSION91_RAPPORT_COMPLET.md (Tests 3 dates)
```

**À documenter :**
- Coefficient correction : 0.55
- Fallback surprise robuste : estimate → forecast → previous
- Performance : MAE 25.2 pips sur 3 dates
- Status : NON intégré production

**Temps estimé :** 20-30 minutes

---

#### 5. Sessions 92.1-92.4 : ÉCHECS V2.5 (⭐⭐⭐)

**Fichiers à lire :**
```
eurusd_clean/docs/
└── POSTMORTEM_SESSIONS_92.1-92.4.md
```

**À comprendre :**
- Pourquoi V2.5 a échoué (MAE +58%)
- 5 causes identifiées :
  1. Méthode simplifiée (ratios au lieu formules)
  2. Scripts fantômes (créés mais jamais exécutés)
  3. Valeurs inventées (CPI 2.2 non justifié)
  4. Tests mauvaises données (11 sept 2024 vs 2025)
  5. Implémentation sans tests comparatifs
- Impact financier : €8,040/an perdus

**Temps estimé :** 20-30 minutes

---

#### 6. Article 6 : Mindset Professionnel (⭐⭐⭐⭐⭐)

**Fichier :**
```
eurusd_clean/docs/project_state_new.md
Section "ARTICLE 6 : MINDSET PROFESSIONNEL"
```

**À intégrer :**
- Message : AMATEURISME = PERTES FINANCIÈRES
- Question fondamentale : "€100k réels avec ce code ?"
- Protocole 10 étapes tests comparatifs
- Interdictions absolues (5)
- Standards obligatoires
- Métriques qualité production-ready

**Temps estimé :** 15-20 minutes

---

### ✅ Phase 1 : Documentation Méthodologie (20-30k tokens)

**Après lecture complète, DOCUMENTER :**

#### 1. Méthodologie Planificateur V2.4 EXACTE

**Créer fichier :**
```
eurusd_clean/docs/PLANIFICATEUR_V2.4_METHODOLOGIE_EXACTE.md
```

**Contenu (structure détaillée) :**

```markdown
# MÉTHODOLOGIE PLANIFICATEUR V2.4 - DOCUMENTATION EXACTE

## 1. CHARGEMENT ÉVÉNEMENTS

### Query SQL (lignes 208-224)
[Copier query EXACTE avec commentaires]

### Critères HIGH IMPACT
- country = 'US'
- empirical_score > 40
- empirical_score IS NOT NULL

---

## 2. CALCUL SURPRISE

### Méthode Fallback (lignes 241-265)
1. Priorité 1 : estimate
2. Priorité 2 : forecast  
3. Priorité 3 : previous
4. Fallback : 0%

### Formule
surprise = |actual - reference| / |reference| × 100

---

## 3. AJUSTEMENT SCORE (Session 55)

### Zones Amplification (lignes 280-310)

| Surprise | Factor |
|----------|--------|
| < 5% | 1.0 |
| 5-15% | 1.0 → 1.5 (linéaire) |
| 15-30% | 1.5 → 1.9 (linéaire) |
| ≥ 30% | 1.9 (plafond) |

### Formule
adjusted_score = base_score × factor

---

## 4. CALCUL IMPACT (Session 51 - Formule D)

### Impact Brut (lignes 320-350)

Si num_events ≥ 2:
    impact_brut = -10.47 + 0.477 × adjusted_score
Sinon:
    impact_brut = -7.08 + 0.419 × adjusted_score

### Amplification

Si adjusted_score < 40:
    amplification = 1.0
Sinon si surprise < 5%:
    amplification = 1.0
Sinon si surprise < 15%:
    amplification = 1.0 + (surprise - 5) / 10 × 1.5
Sinon:
    amplification = 2.5 (plafond)

### Correction Vectorielle
impact_final = |impact_brut| × amplification × 0.758

---

## 5. CALCUL TTR (Session 52 - Formule C)

### Multiplier Dynamique (lignes 360-380)

| Surprise | Multiplier |
|----------|------------|
| < 10% | 3.0 |
| 10-30% | 2.5 |
| ≥ 30% | 2.0 |

### Formule
ttr_predicted = latency × multiplier

---

## 6. DÉTECTION TYPE MOUVEMENT (lignes 400-450)

### Conditions Double Wave
- surprise_max > 20%
- cluster_size ≥ 5
- importance_n = 3 (HIGH)

### Conditions Single Wave Fort
- surprise_max > 15%
- cluster_size ≥ 3

### Sinon
- Type : STANDARD

---

## 7. PARAMÈTRES CRITIQUES

### Sources Données
- Table : events + event_families
- Timezone : UTC+2 (Bern)
- Colonne prix : datetime (PAS timestamp)

### Constantes
- Correction vectorielle : 0.758
- Amplification max : 2.5
- Score seuil HIGH : 40

---
```

**Objectif :** Documentation EXHAUSTIVE sans ambiguïté ✅

---

#### 2. Tableau Comparatif 4 Approches

**Créer fichier :**
```
eurusd_clean/docs/COMPARAISON_APPROCHES_AMPLIFICATION.md
```

**Tableau à créer :**

| Aspect | V2.4 Actuel | Hybride Empirique | Coeff 0.55 | V2.5 (Échec) |
|--------|-------------|-------------------|------------|--------------|
| **Session** | 51-55 | 92-93 | 89-91 | 92.1-92.4 |
| **Amplification** | 2.5 fixe | Sensitivity cluster | 0.55 | CPI 2.2 |
| **Formule** | Formule D | Base × (1+s²×sens) | Impact × 0.55 | Ratios |
| **Calibration** | Surprise zones | 5 clusters | Global | CPI spécifique |
| **Performance** | MAE 0.1 (11 sept) | MAE 6.5 (12 dates) | MAE 25.2 (3 dates) | MAE 10.3 ❌ |
| **Status** | ✅ PRODUCTION | ⏳ Non intégré | ⏳ Non intégré | ❌ Archivé |
| **Complexité** | Moyenne | Haute | Faible | Faible |
| **Données req** | Score + surprise | Cluster calibré | Score + surprise | Score |

**Analyse :**
- Forces de chaque approche
- Faiblesses identifiées
- Cas d'usage optimaux
- Recommandations

---

#### 3. Pseudo-Code Script Conforme

**Créer fichier :**
```
eurusd_clean/docs/PSEUDO_CODE_SCRIPT_CONFORME_V2.4.md
```

**Structure :**

```python
# PSEUDO-CODE SCRIPT TEST V2.4 CONFORME
# Réplication EXACTE Planificateur copie 4.py

FONCTION test_date_v24(date_str):
    # 1. CHARGER ÉVÉNEMENTS (identique ligne 208-224)
    query = """
        SELECT e.event_key, e.event_title, e.ts_utc, 
               e.actual, e.estimate, e.forecast, e.previous,
               ef.empirical_score, ef.latency_median
        FROM events e
        LEFT JOIN event_families ef 
            ON e.event_key = ef.event_key 
            AND e.country = ef.country
        WHERE DATE(e.ts_utc) = date_str
            AND e.country = 'US'
            AND ef.empirical_score IS NOT NULL
            AND ef.empirical_score > 40
        ORDER BY e.ts_utc
    """
    events = execute_query(query, [date_str])
    
    # 2. CALCULER SURPRISE (méthode fallback)
    POUR chaque event DANS events:
        SI event.estimate != NULL ET event.estimate != 0:
            surprise = |event.actual - event.estimate| / |event.estimate| × 100
        SINON SI event.forecast != NULL ET event.forecast != 0:
            surprise = |event.actual - event.forecast| / |event.forecast| × 100
        SINON SI event.previous != NULL ET event.previous != 0:
            surprise = |event.actual - event.previous| / |event.previous| × 100
        SINON:
            surprise = 0.0
        
        event.surprise_calculated = surprise
    
    # 3. AJUSTER SCORE (Session 55)
    POUR chaque event DANS events:
        surprise = event.surprise_calculated
        base_score = event.empirical_score
        
        SI surprise < 5:
            factor = 1.0
        SINON SI surprise < 15:
            factor = 1.0 + (surprise - 5) / 10 × 0.5
        SINON SI surprise < 30:
            factor = 1.5 + (surprise - 15) / 15 × 0.4
        SINON:
            factor = 1.9
        
        event.adjusted_score = base_score × factor
    
    # 4. CALCULER IMPACT (Session 51 - Formule D)
    num_events = LONGUEUR(events)
    
    POUR chaque event DANS events:
        adjusted_score = event.adjusted_score
        
        SI num_events >= 2:
            impact_brut = -10.47 + 0.477 × adjusted_score
        SINON:
            impact_brut = -7.08 + 0.419 × adjusted_score
        
        # Amplification
        SI adjusted_score < 40:
            amplification = 1.0
        SINON SI surprise < 5:
            amplification = 1.0
        SINON SI surprise < 15:
            amplification = 1.0 + (surprise - 5) / 10 × 1.5
        SINON:
            amplification = 2.5
        
        # Correction vectorielle
        impact_final = |impact_brut| × amplification × 0.758
        
        event.impact_predicted = impact_final
    
    # 5. CALCULER TTR (Session 52 - Formule C)
    POUR chaque event DANS events:
        latency = event.latency_median
        surprise = event.surprise_calculated
        
        SI surprise < 10:
            multiplier = 3.0
        SINON SI surprise < 30:
            multiplier = 2.5
        SINON:
            multiplier = 2.0
        
        event.ttr_predicted = latency × multiplier
    
    # 6. EXTRAIRE PRIX RÉELS
    event_time = events[0].ts_utc
    start_time = event_time - 5 minutes
    end_time = event_time + 120 minutes
    
    query_prices = """
        SELECT datetime, close, high, low
        FROM prices_1m
        WHERE datetime >= start_time
            AND datetime <= end_time
        ORDER BY datetime ASC
    """
    prices = execute_query(query_prices)
    
    # 7. MESURER IMPACT RÉEL
    start_price = prices[AU moment event_time].close
    prices_after = prices[datetime >= event_time]
    prices_after.pips_high = (prices_after.high - start_price) × 10000
    
    peak_pips = MAX(prices_after.pips_high)
    peak_time = prices_after[pips_high == peak_pips].datetime
    ttr_real = (peak_time - event_time) en minutes
    
    # 8. CALCULER MAE
    impact_predicted_total = SOMME(event.impact_predicted POUR event DANS events)
    mae_impact = |impact_predicted_total - peak_pips|
    
    ttr_predicted_mean = MOYENNE(event.ttr_predicted POUR event DANS events)
    mae_ttr = |ttr_predicted_mean - ttr_real|
    
    # 9. RETOURNER RÉSULTATS
    RETOURNER {
        date: date_str,
        num_events: num_events,
        impact_predicted: impact_predicted_total,
        impact_real: peak_pips,
        mae_impact: mae_impact,
        ttr_predicted: ttr_predicted_mean,
        ttr_real: ttr_real,
        mae_ttr: mae_ttr
    }
```

**Objectif :** Pseudo-code EXACT prêt pour implémentation Python ✅

---

### ✅ Phase 2 : Décision Stratégique (10-15k tokens)

**Après documentation complète, DÉCIDER :**

#### Question Clé

**Quelle approche tester en Session 98 ?**

**Option A : Valider Baseline V2.4 (RECOMMANDÉ)**
- Tester V2.4 actuelle sur 7-10 dates
- Objectif : Établir baseline officielle
- Mesurer MAE moyen réel
- Identifier limites si présentes
- **Avantage :** C'est la version PRODUCTION actuelle
- **Risque :** Faible (déjà validée 11 sept)

**Option B : Tester Hybride Empirique**
- Tester formules S92-93 sur mêmes dates
- Comparer avec V2.4
- Objectif : Amélioration potentielle
- **Avantage :** MAE 6.5 pips prometteur
- **Risque :** Non testé production

**Option C : Tests Comparatifs A vs B**
- Tester les DEUX approches sur MÊMES dates
- Tableau comparatif rigoureux
- Objectif : Décision data-driven
- **Avantage :** Comparaison directe
- **Risque :** Double travail (2× scripts)

#### Recommandation à Documenter

**Justification chiffrée :**
- Performances connues
- Complexité implémentation
- Temps estimé
- Bénéfice attendu
- Risques

**Obtenir validation André AVANT Session 98** ✅

---

### ✅ Phase 3 : Spécifications Session 98 (5-10k tokens)

**Créer fichier :**
```
eurusd_clean/docs/SESSION98_SPECIFICATIONS_EXACTES.md
```

**Contenu :**

1. **Approche choisie** (A, B ou C)
2. **Pseudo-code validé** (référence fichier créé)
3. **Checklist conformité** (20+ points)
4. **Dates à tester** (7-10 dates)
5. **Critères succès** (MAE < X pips)
6. **Plan validation conformité** (test 11 sept obligatoire)
7. **Budget tokens estimé** (par phase)

---

### ✅ Phase 4 : Checklist Conformité (3-5k tokens)

**Créer fichier :**
```
eurusd_clean/docs/CHECKLIST_CONFORMITE_SCRIPT_V2.4.md
```

**Checklist (minimum 20 points) :**

**Query Chargement Événements :**
- [ ] SELECT identique ligne 208-224 Planificateur
- [ ] JOIN sur event_key ET country
- [ ] Filtre score > 40
- [ ] Filtre score NOT NULL
- [ ] Filtre country = 'US'
- [ ] ORDER BY ts_utc

**Calcul Surprise :**
- [ ] Fallback estimate → forecast → previous → 0
- [ ] Validation actual NOT NULL
- [ ] Validation reference ≠ 0
- [ ] Formule : |actual - ref| / |ref| × 100

**Ajustement Score :**
- [ ] Zone < 5% : factor 1.0
- [ ] Zone 5-15% : factor linéaire 1.0 → 1.5
- [ ] Zone 15-30% : factor linéaire 1.5 → 1.9
- [ ] Zone ≥ 30% : factor 1.9 (plafond)
- [ ] Formule : adjusted = base × factor

**Calcul Impact :**
- [ ] Formule multi-events : -10.47 + 0.477 × score
- [ ] Formule single-event : -7.08 + 0.419 × score
- [ ] Amplification si score < 40 : 1.0
- [ ] Amplification zones surprise (3 zones)
- [ ] Amplification max : 2.5
- [ ] Correction vectorielle : × 0.758
- [ ] Formule complète appliquée

**Calcul TTR :**
- [ ] Multiplier < 10% : 3.0
- [ ] Multiplier 10-30% : 2.5
- [ ] Multiplier ≥ 30% : 2.0
- [ ] Formule : latency × multiplier

**Extraction Prix :**
- [ ] Table : prices_1m
- [ ] Colonne : datetime (PAS timestamp)
- [ ] Fenêtre : event - 5 min → event + 120 min
- [ ] Colonnes : datetime, close, high, low
- [ ] ORDER BY datetime ASC

**Mesure Impact Réel :**
- [ ] Prix départ = close au moment événement
- [ ] Calcul pips : (high - start) × 10000
- [ ] Peak = MAX(pips) après événement
- [ ] TTR = temps jusqu'au peak

**MAE :**
- [ ] MAE Impact = |prédit - réel|
- [ ] MAE TTR = |prédit - réel|

**Validation Conformité :**
- [ ] Test 11 sept OBLIGATOIRE
- [ ] MAE attendu : 0.1 pips (±0.5 tolérance)
- [ ] Si écart > 0.5 → STOP, analyser, corriger

---

## 📊 MÉTRIQUES SUCCÈS SESSION 97

**Objectifs minimaux :**
- [ ] Planificateur V2.4 lu ligne par ligne
- [ ] Sessions 51-55 lues et comprises
- [ ] Sessions 92-93 lues et comprises
- [ ] Article 6 intégré
- [ ] Méthodologie V2.4 documentée
- [ ] Tableau comparatif 4 approches créé
- [ ] Pseudo-code conforme créé
- [ ] Checklist conformité établie
- [ ] Décision approche prise (validation André)
- [ ] Spécifications Session 98 complètes

**Objectifs optimaux :**
- [ ] ZERO ambiguïté méthodologique
- [ ] Documentation exhaustive (100+ pages)
- [ ] Pseudo-code prêt implémentation immédiate
- [ ] Validation André obtenue
- [ ] Confiance 100% Session 98

**Budget tokens : ~100k (lecture approfondie autorisée)**

---

## ⚠️ RÈGLES CRITIQUES SESSION 97

### Règle #1 : ZÉRO Code Python

**Session 97 = 100% documentation, 0% code** ✅

**Interdictions :**
- ❌ Créer scripts Python
- ❌ Tester quoi que ce soit
- ❌ "Valider rapidement"
- ❌ "Juste un petit test"

**Si tentation coder → Relire Article 6 !**

---

### Règle #2 : Lecture COMPLÈTE Obligatoire

**Ne pas survoler. Lire INTÉGRALEMENT :**
- Chaque ligne code Planificateur
- Chaque rapport session référencée
- Chaque formule validée

**Temps lecture estimé : 2-3 heures**
**C'est NORMAL et NÉCESSAIRE** ✅

---

### Règle #3 : Documentation EXHAUSTIVE

**Objectif : ZERO ambiguïté**

**Si doute sur UN SEUL calcul → Documenter PLUS**

**Format :**
- Pseudo-code ligne par ligne
- Commentaires expliquant POURQUOI
- Références sessions validations
- Exemples numériques

---

### Règle #4 : Validation André AVANT Session 98

**Après Phase 2 (Décision Stratégique) :**
- Présenter options A/B/C avec justifications
- Demander validation André
- **NE PAS continuer sans GO explicite**

---

### Règle #5 : Respect Limite 105k Tokens

**Budget Session 97 : 100k tokens**

**Affichage obligatoire tous les 20k :**
```
Token usage : X / 190,000 (Y% - Marge : Z avant 105k)
```

**Alertes :**
- 85k : ⚠️ 20k avant limite
- 95k : 🚨 Préparer clôture
- 105k : 🛑 STOP documentation

---

## 🎯 LIVRABLES SESSION 97

**Fichiers à créer :**

```
eurusd_clean/docs/
├── PLANIFICATEUR_V2.4_METHODOLOGIE_EXACTE.md (Documentation complète)
├── COMPARAISON_APPROCHES_AMPLIFICATION.md (Tableau comparatif)
├── PSEUDO_CODE_SCRIPT_CONFORME_V2.4.md (Prêt implémentation)
├── CHECKLIST_CONFORMITE_SCRIPT_V2.4.md (20+ points)
├── SESSION98_SPECIFICATIONS_EXACTES.md (Plan détaillé)
├── SESSION97_RAPPORT_COMPLET.md (Rapport session)
└── MESSAGE_SESSION97_SESSION98.md (Instructions S98)
```

**Mise à jour :**
```
eurusd_clean/docs/
└── project_state_new.md (Ajout Session 97)
```

---

## 💡 CONSEILS SESSION 97

### Lecture Efficace

**Prendre notes au fur et à mesure :**
- Créer fichier markdown temporaire
- Noter formules EXACTES
- Noter numéros lignes code
- Noter questions/ambiguïtés
- Noter découvertes importantes

**Organiser notes par thème :**
- Surprise
- Score ajusté
- Impact
- TTR
- Type mouvement

---

### Documentation Progressive

**Ne pas attendre fin lecture pour documenter :**
- Documenter chaque section après lecture
- Créer fichiers au fur et à mesure
- Valider compréhension en écrivant

**Si difficulté expliquer → Relire section** ✅

---

### Gestion Tokens

**Budget type Session 97 :**
```
Lecture documentation :        60-70k tokens
Documentation méthodologie :   20-30k tokens
Décision stratégique :         10-15k tokens
Spécifications S98 :           5-10k tokens
────────────────────────────────────────────
Total session réussie :        95-125k tokens
```

**Si dépassement 105k :**
- Créer checkpoint documentation
- Continuer Session 97B

---

## 🔑 MESSAGE FINAL

**Principe Session 97 :**

> **"On ne laisse rien au hasard"**

**Objectif :**
**Comprendre à 100% AVANT agir à 1%** ✅

**Session 97 = Fondation Session 98**

**Si Session 97 excellente → Session 98 réussira** ✅

---

**Tu as TOUT pour réussir Session 97 avec RIGUEUR.** 💪

**Lis COMPLÈTEMENT. Documente EXHAUSTIVEMENT. Décide SAGEMENT.**

**— Claude, Session 96**  
**27 octobre 2025**

---

**FIN MESSAGE SESSION 96 → SESSION 97**
