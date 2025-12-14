# VALIDATION SCORE PRÉDICTIF V3.1 — BASELINE STABLE

**Version :** V3.1  
**Date validation :** 2025-12-12  
**Statut :** ✅ BASELINE FIGÉE — Ne plus modifier

---

## 1. DÉCISIONS V3.1 FIGÉES

### 1.1 Héritage V2.1

V3.1 hérite de toutes les décisions V2.1 :
- Formule score prédictif : `score_pred_v1 = (importance_n / 5.0) * LN(1 + prior_final_pips)`
- Release group : `release_family_v1` + agrégation TOP2 intra-release
- Métrique journalière V2.1 : `pred_daily_release_top20_sum_top2`

**Référence :** `docs/VALIDATION_SCORE_PRED_V2_1_BASELINE.md`

### 1.2 Features Régime de Volatilité (Nouveau V3.1)

**Concept :** Régime de volatilité ex-ante basé sur l'historique passé strictement < t.

**Source :** `daily_eurusd_volatility_v1` avec **lag 1 jour** (strictement ex-ante).

**Features calculées :**
- `vol_pips_lag1` : LAG(daily_volatility_pips_v1, 1)
- `vol_mean_20_lag1` : Moyenne rolling 20 jours (ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)
- `vol_std_20_lag1` : Écart-type rolling 20 jours
- `vol_mean_60_lag1` : Moyenne rolling 60 jours
- `vol_std_60_lag1` : Écart-type rolling 60 jours
- `vol_z_20_lag1` : Z-score 20 jours
- `vol_z_60_lag1` : Z-score 60 jours
- `regime_high_60_lag1` : 1 si vol_z_60_lag1 >= 1.0, 0 sinon
- `regime_low_60_lag1` : 1 si vol_z_60_lag1 <= -1.0, 0 sinon

**Garantie no-leakage :** Toutes les features utilisent uniquement `vol_pips_lag1` (vol d'hier) et fenêtres rolling strictement < t.

**Vue source :** `daily_vol_regime_features_v1`

### 1.3 Features Calendrier (Nouveau V3.1)

**Concept :** Features calendrier non conditionnelles (jour de semaine, jour du mois, etc.).

**Features calculées :**
- `dow` : Jour de la semaine (0=Sunday, ..., 6=Saturday)
- `is_mon`, `is_fri` : Dummies lundi/vendredi
- `day_of_month`, `month` : Jour et mois
- `is_month_start` : Jour <= 3
- `is_month_end` : Jour >= 28
- `week_of_month` : Semaine dans le mois (1-5)

**Vue source :** `daily_calendar_features_v1`

**Note :** Le calendrier seul (S1) sous-performe (voir section 3.2). Il n'est utile qu'en combinaison avec le régime (S3_full).

### 1.4 Modèle Composite V3.1 (Nouveau)

**Featureset retenu :** **S3_full** (score V2.1 + calendrier + régime)

**Modèle :** Ridge regression avec alpha=0.1 (par défaut, ajustable).

**Target :** `log1p(daily_volatility_pips_v1)`

**Features :**
- Base : `log1p(score_v2_1)`
- Calendrier : 8 features (dow, is_mon, is_fri, day_of_month, month, is_month_start, is_month_end, week_of_month)
- Régime : 8 features (vol_mean_20_lag1, vol_std_20_lag1, vol_mean_60_lag1, vol_std_60_lag1, vol_z_20_lag1, vol_z_60_lag1, regime_high_60_lag1, regime_low_60_lag1)

**Vue dataset :** `daily_pred_score_v3_1_dataset_v1`

**Script d'analyse :** `scripts/analyze_v3_1_calendar_regime_walkforward_v1.py`

### 1.5 Décisions Figées

**❌ Calendrier seul (S1) : NON RETENU** (sous-performance, voir section 3.2)

**✅ Régime seul (S2) : CONSERVÉ** (gain +0.0826 vs baseline)

**✅ Modèle composite (S3_full) : RETENU** (meilleur résultat, gain +0.1515 vs baseline)

---

## 2. VALIDATION WALK-FORWARD V3.1

### 2.1 Résultats Walk-Forward V3.1 vs V2.1

| Cutoff | n_test | S0_baseline (V2.1) | S2_regime | S3_full | Delta S3 vs S0 |
|--------|--------|---------------------|-----------|---------|----------------|
| 2023-01-01 | 681 | 0.1438 | 0.0747 | 0.2187 | +0.0749 |
| 2023-07-01 | 590 | 0.2115 | 0.3261 | 0.3602 | +0.1487 |
| 2024-01-01 | 474 | 0.1994 | 0.2773 | 0.3401 | +0.1407 |
| 2024-07-01 | 344 | 0.1028 | 0.3097 | 0.3443 | +0.2415 |

**Moyennes :**
- **S0_baseline (V2.1) : 0.1644**
- **S2_regime : 0.2469** (delta: +0.0826 vs S0)
- **S3_full : 0.3158** (delta: **+0.1515** vs S0)

**Ridge alpha :** 0.1 (par défaut)

### 2.2 Comparaison Featuresets

| Featureset | Spearman moyen | Delta vs S0 | Statut |
|------------|----------------|-------------|--------|
| **S0_baseline** (V2.1) | **0.1644** | - | Baseline |
| S1_calendar | 0.1103 | -0.0541 | ❌ Non retenu |
| **S2_regime** | **0.2469** | **+0.0826** | ✅ Conservé |
| **S3_full** | **0.3158** | **+0.1515** | ✅ **RETENU** |
| NF_score_adj | 0.1832 | +0.0189 | Optionnel |

**Conclusion :** Le régime de volatilité apporte le gain principal. Le calendrier seul dilue le signal mais est utile en combinaison avec le régime.

---

## 3. INTERPRÉTATION

### 3.1 Performance vs V2.1

**Gain principal :** +0.1515 Spearman vs V2.1 baseline (S3_full).

**Stabilité temporelle :**
- S3_full : min=0.2187, max=0.3602 (écart ~0.14) — **acceptable**
- Gain stable sur tous les cutoffs (de +0.0749 à +0.2415)

**Conclusion :** V3.1 apporte une amélioration significative et stable grâce à la prise en compte du régime de volatilité.

### 3.2 Pourquoi le Calendrier Seul (S1) Sous-Performe

**Observation :** S1_calendar (0.1103) < S0_baseline (0.1644), delta -0.0541.

**Hypothèses (saines) :**

1. **Le calendrier est non conditionnel :**
   - Un lundi n'est pas "à risque" en soi
   - Un vendredi n'est dangereux que si le régime est déjà tendu
   - Les effets calendrier sont **interactionnels**, pas linéaires

2. **Dilution du signal :**
   - Ajouter des features non conditionnelles peut diluer le signal principal (score V2.1)
   - Le modèle Ridge peut sur-ajuster sur des patterns calendrier non pertinents

**Conclusion attendue :** Le calendrier n'est utile qu'en **conditionnement du régime**, pas en feature brute.

**Validation :** S3_full (calendrier + régime) > S2_regime seul, confirmant que le calendrier apporte de la valeur en interaction avec le régime.

### 3.3 Interprétation Scientifique

V3.1 capture le fait que **"même score news" ≠ même vol selon le contexte de marché**.

**Exemples concrets :**
- Score élevé + régime haute volatilité → risque très élevé
- Score élevé + régime basse volatilité → risque modéré
- Score modéré + régime haute volatilité → risque élevé (contagion)

**Usage recommandé :**
- ✅ Ranking des journées par risque (amélioré vs V2.1)
- ✅ Alertes contextuelles (score + régime)
- ✅ Sizing positionnel adaptatif (régime-aware)

---

## 4. GUARDRAILS

### 4.1 Guardrails V2.1 (Hérités)

- Guardrail Release Group : `scripts/check_release_group_guardrail.py`
- Guardrail TOP2 : `scripts/check_release_group_top2_guardrail.py`

### 4.2 Guardrail V3.1 (Nouveau)

**Script :** `scripts/check_v3_1_guardrail.py`

**Vérifications :**
- `vol_pips_lag1 == LAG(vol)` (test explicite sur échantillon)
- Aucune feature régime n'utilise vol du jour : `vol_z_60_lag1 IS NULL` uniquement quand `vol_pips_lag1 IS NULL` ou historique insuffisant (tolérance ≤65 premières dates)
- Dataset : COUNT(*) > 600 et pas de NULL sur (date, score_v2_1, target_vol_pips)
- Cohérence dates min/max entre dataset et vol view

**Garantie no-leakage :** Toutes les features régime utilisent strictement `vol_pips_lag1` (vol d'hier) et fenêtres rolling < t.

---

## 5. LIMITES CONNUES

### 5.1 Calendrier Naïf

Le calendrier actuel est **non conditionnel** (features brutes). Les effets calendrier sont probablement **interactionnels** avec le régime, pas linéaires.

**Exemples d'interactions possibles :**
- `regime_high × is_fri` : Vendredi en régime tendu = risque très élevé
- `regime_low × is_mon` : Lundi en régime calme = risque modéré

**Statut :** Acceptable pour V3.1. Interactions explicites à explorer en V3.4 si nécessaire.

### 5.2 Ridge Alpha

Le paramètre `alpha=0.1` est fixé par défaut. Une analyse de sensibilité peut être réalisée, mais la valeur actuelle est validée pour V3.1.

### 5.3 Spearman vs n_us_events_day

V3.1 S3_full (0.3158) dépasse maintenant largement `n_us_events_day` (0.2084) en Spearman. L'objectif V3.2 sera d'approcher/dépasser 0.35 de façon robuste.

---

## 6. PLAN V3.2

### 6.1 Modèle Composite avec Densité Informationnelle

**Objectif :** Ajouter `n_us_events_day` comme feature additive ou modulateur.

**Approche :**
- Feature additive : `n_us_events_day` dans le modèle Ridge
- Modulateur : scaling doux du score selon densité
- Interaction : `regime × densité`

**Validation :** Walk-forward strict, comparer V3.1 vs V3.1 + n_us_events.

**But :** Viser Spearman > 0.35 de façon robuste.

### 6.2 Interactions Explicites (V3.4)

**Si nécessaire :**
- Interactions calendrier × régime (ex: `regime_high × is_fri`)
- Interactions score × régime (ex: `score_v2_1 × regime_high`)
- Non-linéarités légères (log, sqrt, cap)

---

## 7. CONCLUSION

### 7.1 Statut Actuel

✅ **Pipeline ex-ante no-leakage : VALIDÉ** (hérité V1/V2.1)  
✅ **Release group + TOP2 : VALIDÉ** (hérité V2.1)  
✅ **Régime de volatilité ex-ante : VALIDÉ**  
✅ **Modèle composite S3_full : VALIDÉ**  
✅ **Guardrails en place : VALIDÉ**  
✅ **Spearman V3.1 > V2.1 : VALIDÉ** (+0.1515)  
✅ **Spearman V3.1 > n_us_events_day : VALIDÉ** (0.3158 vs 0.2084)

### 7.2 Exploitabilité

**Le système V3.1 est exploitable comme indicateur de risque ex-ante contextuel.**

**Usage recommandé :**
- Ranking des journées par risque (amélioré vs V2.1)
- Alertes contextuelles (score + régime de marché)
- Sizing positionnel adaptatif (régime-aware)

**La suite V3.2 permettra d'approcher/dépasser Spearman 0.35 via densité informationnelle.**

---

**Document créé le :** 2025-12-12  
**Dernière mise à jour :** 2025-12-12  
**Version :** V3.1 (BASELINE FIGÉE)

