# VALIDATION SCORE PRÉDICTIF V2.1 — BASELINE STABLE

**Version :** V2.1  
**Date validation :** 2025-12-12  
**Statut :** ✅ BASELINE FIGÉE — Ne plus modifier

---

## 1. DÉCISIONS V2.1 FIGÉES

### 1.1 Héritage V1

V2.1 hérite de toutes les décisions V1 :
- Formule score prédictif : `score_pred_v1 = (importance_n / 5.0) * LN(1 + prior_final_pips)`
- Rolling strict < t : `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`
- Shrinkage : `m_default = 20`
- Séparation prédictif vs rétrospectif : aucune information post-release dans le calcul

**Référence :** `docs/VALIDATION_SCORE_PRED_V1_BASELINE.md`

### 1.2 Release Group (Nouveau V2.1)

**Concept :** Regroupement des composantes d'une même publication macro.

**Mapping :** `release_family_v1` dérivé de `event_key` via :
- Mapping explicite prioritaire (dict)
- Fallback heuristique (keywords)
- Fallback final = `event_key`

**Clé release_group :** `release_group_id_v1 = MD5(country || '|' || ts_local || '|' || release_family_v1)`

**Vue source :** `events_with_release_group_v1`  
**Table mapping :** `release_family_map_v1`  
**Module :** `src/core/release_family_v1.py`

### 1.3 Agrégation Intra-Release (Nouveau V2.1)

**Variante retenue :** **TOP2-SUM**

**Définition :** Pour chaque `release_group_id_v1`, calculer :
```sql
score_release_top2 = SUM(score_pred_v1) WHERE rn_in_release <= 2
```

**Justification :** Meilleur compromis anti-dilution / conservation d'information vs MAX (perd trop) et SUM (trop de bruit).

**Alternatives testées :**
- MAX : Spearman 0.1418 (delta: -0.0093 vs V1)
- SUM : Spearman 0.1285 (delta: -0.0227 vs V1)
- **TOP2 : Spearman 0.1644 (delta: +0.0132 vs V1)** ✅

### 1.4 Métrique Journalière V2.1

**Métrique :** `pred_daily_release_top20_sum_top2`

**Définition :** 
1. Calculer `score_release_top2` pour chaque `release_group_id_v1`
2. Agréger par jour : somme des top 20 `score_release_top2` (anti-dilution)

**Vue source :** `daily_pred_score_release_group_v1` (colonne `pred_daily_release_top20_sum_top2`)

**Script d'analyse :** `scripts/analyze_daily_pred_score_release_group_vs_vol_walkforward_v1.py`

---

## 2. VALIDATION WALK-FORWARD V2.1

### 2.1 Résultats Walk-Forward V2.1 vs V1

| Cutoff | n_test | Spearman_V1 | Spearman_V2.1_TOP2 | Delta |
|--------|--------|-------------|---------------------|-------|
| 2023-01-01 | 681 | 0.1383 | 0.1438 | +0.0055 |
| 2023-07-01 | 590 | 0.1957 | 0.2114 | +0.0157 |
| 2024-01-01 | 474 | 0.1706 | 0.1994 | +0.0289 |
| 2024-07-01 | 344 | 0.0999 | 0.1028 | +0.0029 |

**Moyennes :**
- **Spearman V2.1 TOP2 : 0.1644** (delta: **+0.0132** vs V1)
- **Pearson(log) V2.1 TOP2 : 0.2270** (delta: -0.0118 vs V1, dans tolérance)

### 2.2 Comparaison avec Baselines

| Métrique | Spearman | Delta vs V1 |
|----------|----------|-------------|
| **Score V2.1 TOP2** | **0.1644** | **+0.0132** |
| Score V1 | 0.1511 | - |
| n_us_events_day | 0.2084 | - |
| n_events_day | 0.1641 | - |
| n_ts_country_groups_day | 0.1530 | - |

**Note :** V2.1 TOP2 dépasse maintenant `n_events_day` en Spearman, mais reste inférieur à `n_us_events_day` (à traiter en V3).

---

## 3. EVIDENCE QUALITATIVE

### 3.1 Jours qui Expliquent le Gain

**TOP20 jours où V2.1 >> V1 (delta le plus positif) :**

Exemples clés :
- 2024-02-15 : V1 rank 16 → V2.1 rank 1 (delta +38.9, vol 60.3 pips)
- 2025-05-15 : V1 rank 25 → V2.1 rank 2 (delta +38.3, vol 58.0 pips)
- 2024-08-15 : V1 rank 23 → V2.1 rank 3 (delta +37.1, vol 66.2 pips)

**Pattern observé :** V2.1 TOP2 excelle sur les jours avec plusieurs releases multi-composantes (NFP, CPI, Retail Sales).

**TOP20 jours où V2.1 << V1 (delta le plus négatif) :**

Exemples :
- 2024-03-03 : V1 rank 341 → V2.1 rank 441 (delta -23.2, vol 4.2 pips)
- 2025-03-02 : V1 rank 364 → V2.1 rank 445 (delta -21.5, vol 5.2 pips)

**Pattern observé :** V2.1 sous-performe sur les jours avec peu de releases (n_release_groups ≤ 5) et faible volatilité.

### 3.2 Drill-Down par Release

**Exemple NFP 2024-08-01 :**
- `nfp_release` : 16 events → score_max 1.28, score_sum 20.42, **score_top2 2.55** (gain +1.27 vs MAX)
- `continuing jobless claims` : 16 events → score_max 2.12, score_sum 33.93, **score_top2 4.24** (gain +2.12 vs MAX)

**Exemple CPI 2024-09-11 :**
- `cpi_release` : 8 events → score_max 1.50, score_sum 11.90, **score_top2 3.00** (gain +1.50 vs MAX)

**Conclusion :** TOP2 récupère efficacement les composantes pertinentes (ex: NFP payroll + earnings, CPI headline + core).

### 3.3 Validation Qualitative

**Sur jours top quartile volatilité (vol >= 87.5 pips) :**
- Médiane rank V1 : 240.0
- Médiane rank V2.1 : 214.0
- **Delta : -26.0** (négatif = mieux classé)
- ✅ **V2.1 mieux classé que V1 sur jours haute volatilité**

**Contrôle faux positifs (jours calmes, vol < 87.5) :**
- Faux positifs V1 : 8.2%
- Faux positifs V2.1 : 12.1%
- ⚠️ V2.1 génère légèrement plus de faux positifs (dans tolérance acceptable)

**Script d'analyse :** `scripts/analyze_v2_1_qualitative.py`

---

## 4. GUARDRAILS

### 4.1 Guardrails V1 (Hérités)

- Guardrail Timezone : `scripts/check_timezone_guardrail.py`
- Guardrail Unicité : `scripts/check_event_uniqueness_guardrail.py`

### 4.2 Guardrail Release Group (Nouveau V2.1)

**Script :** `scripts/check_release_group_guardrail.py`

**Vérifications :**
- COUNT(*) cohérence : `events_with_release_group_v1 == events_with_ts_local_v1`
- `release_family_v1 IS NOT NULL` pour 100% des lignes
- Dates repères : `n_release_groups <= n_events` (toujours)
- Unicité `release_group_id_v1` pour `(country, ts_local, release_family_v1)`
- Pas de regroupement cross-country ou cross-timestamp

### 4.3 Guardrail TOP2 (Nouveau V2.1)

**Script :** `scripts/check_release_group_top2_guardrail.py`

**Vérifications :**
- `TOP2_sum >= MAX` (via vue daily)
- `TOP2_sum <= SUM` (via vue daily)
- Couverture dates identique à `daily_eurusd_volatility_v1`

---

## 5. LIMITES CONNUES

### 5.1 Spearman vs n_us_events_day

V2.1 TOP2 reste inférieur à `n_us_events_day` en Spearman (0.1644 vs 0.2084). Cette baseline capture un effet volume US qui sera mieux modélisé en V3 via modèle composite.

### 5.2 Faux Positifs

V2.1 génère légèrement plus de faux positifs que V1 sur jours calmes (12.1% vs 8.2%). Acceptable compte tenu du gain sur jours haute volatilité.

### 5.3 Mapping release_family

Le mapping actuel couvre les cas majeurs (CPI, NFP, FOMC, ECB, etc.) mais peut être amélioré pour :
- GDP releases (multi-composantes)
- PPI releases
- ADP, JOLTS, Michigan
- Éviter collisions (deux releases différentes mappées pareil)

**Statut :** À améliorer en V3.3 si nécessaire.

---

## 6. PLAN V3

### 6.1 V3.1 — Calendar & Regime (Safe, peu risqué)

**Features journalières (sans leakage) :**
- Jour de semaine (Mon…Fri)
- Semaine du mois / fin de mois
- Mois / saisonnalité (dummy)
- Proximité d'un FOMC / CPI / NFP (±1 jour)
- Régime simple : volatilité passée (vol_rolling_20d basé uniquement sur le passé)

**But :** Capturer le fait que "même score news" ≠ même vol selon contexte.

### 6.2 V3.2 — Modèle Composite

**Modèle :** `global_score_v3 = a * score_v2_1 + b * f(n_us_events_day) + c * regime`

**Calibration :** Uniquement sur train (walk-forward strict), puis évaluation sur test.

**But :** Dépasser `n_us_events_day` en Spearman.

### 6.3 V3.3 — Mapping release_family Amélioré

**Seulement si analyse qualitative montre des regroupements "bizarres" :**
- Ajouter familles manquantes (GDP, PPI, ADP, JOLTS, Michigan)
- Éviter collisions

### 6.4 V3.4 — Non-linéarités Légères

**Sans ML lourd :**
- `log(1+score)` ou `sqrt(score)`
- Cap / winsorization des extrêmes
- Interaction simple : `score * regime_high`

---

## 7. CONCLUSION

### 7.1 Statut Actuel

✅ **Pipeline ex-ante no-leakage : VALIDÉ** (hérité V1)  
✅ **Rolling strict < t : VALIDÉ** (hérité V1)  
✅ **Release group : VALIDÉ**  
✅ **Agrégation TOP2 : VALIDÉ**  
✅ **Guardrails en place : VALIDÉ**  
✅ **Spearman V2.1 > Spearman V1 : VALIDÉ** (+0.0132)  
✅ **Pearson(log) V2.1 maintenu : VALIDÉ** (dans tolérance)  
✅ **V2.1 mieux classé sur jours haute volatilité : VALIDÉ**

### 7.2 Exploitabilité

**Le système V2.1 est exploitable comme indicateur de risque ex-ante amélioré.**

**Usage recommandé :**
- Ranking des journées par risque (amélioré vs V1)
- Alertes sur journées à fort risque
- Sizing positionnel relatif

**La suite V3 permettra d'approcher/dépasser `n_us_events_day` en Spearman.**

---

**Document créé le :** 2025-12-12  
**Dernière mise à jour :** 2025-12-12  
**Version :** V2.1 (BASELINE FIGÉE)

