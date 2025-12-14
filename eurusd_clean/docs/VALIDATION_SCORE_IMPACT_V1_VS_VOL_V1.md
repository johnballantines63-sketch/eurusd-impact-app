# ✅ VALIDATION SCORE_IMPACT_V1 vs VOLATILITÉ EURUSD (VOL_SPEC_V1)

**Date** : 2025-12-12  
**Version** : V1  
**Auteur** : Pipeline IMPACT / SCORE / VOL

---

## 1. Contexte & objectifs

Cette note documente la **validation empirique** de la chaîne :

- **IMPACT_SPEC_V1** → impact canonique `impact_unified_pips`
- **SCORE_SPEC_V1** → score d'événement `score_impact_v1` + buckets
- **VOL_SPEC_V1** → volatilité journalière `daily_volatility_pips_v1`

**Objectifs** :

1. Vérifier que le **score d'événements** n'est pas purement décoratif, mais
   qu'il porte un **signal réel** sur la volatilité EURUSD.
2. Quantifier l'impact des **événements HIGH / EXTREME** sur la volatilité journalière.
3. Poser une **base documentée** pour les futures versions (SCORE_SPEC_V2 / VOL_SPEC_V2).

---

## 2. Rappels de spécifications

### 2.1. Impact – IMPACT_SPEC_V1 (rappel)

**Métrique canonique d'impact** : `impact_unified_pips`

- Baseline : prix `event_open`
- Horizon : `120 minutes` après l'événement
- Direction : `impact_unified_direction` (+1 UP, -1 DOWN)

**Backfill global** :

- ~8 344 événements, **99% de complétion** en `impact_unified_pips`
- Qualité : ~98–99% en `impact_unified_quality = 'high'` ou `'medium'`

### 2.2. Score – SCORE_SPEC_V1 (rappel)

**Score d'événement individuel** :

```text
score_impact_v1 =
    ln(1 + impact_unified_pips)
  * (importance_n / 5.0)
  * (1.0 + 0.1 * min(|surprise_pct|, 5.0))
```

**Score signé** :

```text
score_impact_signed_v1 =
  + score_impact_v1 si impact_unified_direction = +1
  - score_impact_v1 si impact_unified_direction = -1
  NULL sinon
```

**Buckets SCORE_SPEC_V1 (figés)** :

- **LOW** : `score_impact_v1 < 2.326`
- **MEDIUM** : `2.326 ≤ score_impact_v1 < 2.845`
- **HIGH** : `2.845 ≤ score_impact_v1 < 3.286`
- **EXTREME** : `score_impact_v1 ≥ 3.286`

**Distribution observée** :

- ~50% LOW, ~25% MEDIUM, ~15% HIGH, ~10% EXTREME
- Bucket EXTREME : impact médian ≈ 50 pips

### 2.3. Volatilité – VOL_SPEC_V1 (rappel)

**Source** : `prices_finnhub_m1` (EURUSD, Bern time, M1).

**Vue** : `daily_eurusd_volatility_v1`

Pour chaque date (Europe/Zurich) :

- `day_open` : premier **open M1** du jour
- `day_close` : dernier **close M1** du jour
- `day_high` : max(high) du jour
- `day_low` : min(low) du jour

**Métriques** :

```text
range_pips          = (day_high - day_low) * 10000
close_to_close_pips = |day_close - day_open| * 10000

daily_volatility_pips_v1 = range_pips   (VOL_SPEC_V1)
```

**Distribution globale (≈ 3 116 jours)** :

- Médiane `daily_volatility_pips_v1` ≈ **63–67 pips**
- P75 ≈ **88 pips**
- Max ≈ **512 pips** (Brexit, Trump, etc.)

---

## 3. Construction des vues journalières

### 3.1. Vue d'impact journalier – `daily_news_score_v1`

Basée sur `events_with_canonical_impact_scored_bucketed_v1`.

Pour chaque date :

- `n_events` : nombre total d'événements
- `sum_score_impact_v1`
- `max_score_impact_v1`
- `avg_score_impact_v1`
- `p50_score_impact_v1`
- `n_low`, `n_medium`, `n_high`, `n_extreme`
- `daily_news_score_v1` = `SUM(score_impact_v1)` (score global V1)

**Distribution (714 jours avec news)** :

- Médiane `daily_news_score_v1` ≈ **63.7**
- P75 ≈ **109.0**
- Max ≈ **695.2**
- Médiane `n_events` ≈ **29** événements/jour

### 3.2. Jointure score ↔ vol

**Vue logique utilisée dans les analyses** :

```text
daily_eurusd_volatility_v1 d
JOIN daily_news_score_v1 n
  ON d.date = n.date
```

**Périmètre analysé** :

- 714 jours avec à la fois **news** et **volatilité**
- Période : ~2022-09-21 → 2025-10-17

---

## 4. Résultats – corrélations globales

### 4.1. Corrélation brute score ↔ vol

Sur les 714 jours :

- Corr(score, vol) ≈ **0.11**
- Corr(log(score+1), log(vol+1)) ≈ **0.15**

**Interprétation** :

- Corrélation **faible mais positive**.
- Le score explique une **petite partie** de la volatilité journalière.
- Ce n'est **pas surprenant** : la vol dépend d'autres facteurs (FX global, risque, flux, etc.).

### 4.2. Volatilité par quartiles de score journalier

Score journalier réparti en 4 quartiles (Q1→Q4).

**Tendances observées** :

- Q1 (score faible) : vol médiane ≈ **63–64 pips**
- Q4 (score élevé) : vol médiane ≈ **76–77 pips**

Soit une hausse d'environ **+20%** de la volatilité médiane entre jours "faibles en news" et jours "forts en news".

**Conclusion** : signal présent, mais encore **modeste** en agrégé global (tous types d'événements confondus).

---

## 5. Résultats – focus événements HIGH / EXTREME

L'analyse segmentée par présence d'événements **HIGH / EXTREME** renforce le signal.

### 5.1. Présence d'au moins un événement EXTREME

**Définition** :

- `has_extreme = 1` si `n_extreme ≥ 1` dans la journée.

**Résultats** :

- **Jours sans EXTREME** (`has_extreme = 0`) :  
  - `n_days` : 512  
  - Vol moyenne ≈ **63.5 pips**  
  - Vol médiane ≈ **58.0 pips**  
  - Score journalier médian ≈ **54.1**

- **Jours avec au moins un EXTREME** (`has_extreme = 1`) :  
  - `n_days` : 202  
  - Vol moyenne ≈ **104.5 pips**  
  - Vol médiane ≈ **94.9 pips**  
  - Score journalier médian ≈ **96.8**

🔍 **Différence clé** :

- Volatilité médiane : **58.0 pips → 94.9 pips**  
  ⇒ **+64%** de volatilité en médiane en présence d'au moins un événement EXTREME.

### 5.2. Présence d'au moins un HIGH ou EXTREME

**Définition** :

- `has_high_or_extreme = 1` si `n_high + n_extreme ≥ 1`.

**Résultats** :

- **Jours sans HIGH/EXTREME** (`has_high_or_extreme = 0`) :  
  - `n_days` : 254  
  - Vol moyenne ≈ **57.3 pips**  
  - Vol médiane ≈ **51.1 pips**  
  - Score journalier médian ≈ **30.4**

- **Jours avec HIGH/EXTREME** (`has_high_or_extreme = 1`) :  
  - `n_days` : 460  
  - Vol moyenne ≈ **84.9 pips**  
  - Vol médiane ≈ **77.4 pips**  
  - Score journalier médian ≈ **82.2**

🔍 **Différence clé** :

- Volatilité médiane : **51.1 pips → 77.4 pips**  
  ⇒ **+51%** de volatilité en médiane lorsque la journée contient au moins un événement HIGH ou EXTREME.

### 5.3. Nombre d'événements EXTREME (0 / 1 / 2+)

**Bucket `n_extreme_bucket`** :

- `'0'` : aucun EXTREME
- `'1'` : exactement 1 EXTREME
- `'2+'` : 2 événements EXTREME ou plus

**Résultats** :

- `n_extreme = 0` :  
  - `n_days` : 512  
  - Vol médiane ≈ **58.0 pips**  
  - Score médian ≈ **54.1**

- `n_extreme = 1` :  
  - `n_days` : 27  
  - Vol médiane ≈ **98.2 pips**  
  - Score médian ≈ **60.1**

- `n_extreme ≥ 2` :  
  - `n_days` : 175  
  - Vol médiane ≈ **94.9 pips**  
  - Score médian ≈ **104.6**

**Lecture** :

- Passage de 0 → 1 EXTREME : saut net de volatilité.
- 2+ EXTREME : vol médiane similaire à 1 EXTREME, mais **score journalier beaucoup plus élevé** (journées "chargées en news extrêmes").
- Les petites différences entre 1 et 2+ sont plausiblement dues à l'échantillonnage / structure des jours.

---

## 6. Interprétation globale

### 6.1. Ce que le système démontre

1. **En agrégé global (tous événements)**  
   → Corrélation score ↔ vol **faible mais positive** (≈ 0.11–0.15).

2. **En se concentrant sur les événements forts (HIGH / EXTREME)**  
   → Le signal devient **nettement plus clair** :
   - +51% de vol médiane avec au moins un HIGH/EXTREME.
   - +64% de vol médiane avec au moins un EXTREME.

3. Les jours avec EXTREME sont **structurellement plus volatils** :
   - vol médiane ≈ 95 pips contre 58 pips sans EXTREME.

### 6.2. Limites de V1

- Le score `score_impact_v1` utilise l'**impact réalisé** (`impact_unified_pips`) → une partie du lien est structurel.
- La volatilité journalière est influencée par :
  - des événements non capturés,
  - la macro de fond, la liquidité, le sentiment global, etc.
- VOL_SPEC_V1 se limite à un **range journalier brut** (pas d'ATR, pas de realized variance).

En résumé : le système **porte un vrai signal**, mais ne prétend pas expliquer toute la volatilité du marché (ce qui serait illusoire).

---

## 7. Roadmap suggérée (SCORE_SPEC_V2 / VOL_SPEC_V2)

### 7.1. Pistes côté SCORE_SPEC_V2

- Tester des scores **sans impact_unified_pips** (importance + surprise only) pour une validation prédictive plus stricte.
- Ajuster les poids (importance vs surprise) pour maximiser :
  - la corrélation score ↔ vol,
  - et/ou la capacité à identifier les jours extrêmes.
- Introduire des **scores multi-horizons** (ex : 30min / 2h / 24h).

### 7.2. Pistes côté VOL_SPEC_V2

- Ajouter :
  - ATR-like (moyenne glissante du range),
  - realized variance M1 intra-journalière,
  - volatilité directionnelle (range_up vs range_down),
  - mesures de gap entre jours.

### 7.3. Pistes d'analyses supplémentaires

- Segmenter par type d'événement (NFP, CPI, FOMC, …).
- Analyser la vol **autour** de l'événement (fenêtre +/- X heures) plutôt que sur la journée entière.
- Étudier la contribution marginale :
  - d'un événement EXTREME isolé,
  - vs une journée "chargée" avec de nombreux événements.

---

## 8. Diagnostic des cas "EXTREME mais vol faible"

### 8.1. Mécanisme identifié

L'analyse de composition journalière (via `explain_day_score_composition.py`) révèle pourquoi certains jours ont beaucoup d'événements EXTREME mais une volatilité modérée :

**Cas type : 2024-08-15** (88 EXTREME, vol 66.2 pips)
- Énorme volume d'événements (264 au total)
- **Duplications structurelles** : 144 événements US au même timestamp (14:30:00)
- Score très dispersé : Top 1 ≈ 0.5% du total, Top 20 ≈ 10.6% du total
- Le `daily_news_score_v1` (SUM) gonfle surtout parce que chaque composante d'un rapport macro est comptée comme un événement distinct

**Cas type : 2025-04-03** (10 EXTREME, vol 341.2 pips)
- Peu d'événements (13 au total)
- Peu de duplications (max 6 événements au même timestamp)
- Score très concentré : Top 1 ≈ 10.6%, Top 5 ≈ 47.2%
- Un petit nombre d'événements majeurs dominent vraiment la journée → volatilité énorme

### 8.2. Implication pour le système

Le score journalier `daily_news_score_v1 = SUM(score_impact_v1)` est utile, mais il est **sensible au "mass-counting"** quand plusieurs composantes sortent au même timestamp.

**Exemple concret** :
- Un rapport NFP avec 10 composantes publiées à 14:30:00 → 10 événements EXTREME comptés séparément
- Un événement isolé majeur (PPI EU) → 1 événement EXTREME mais impact réel beaucoup plus fort

### 8.3. Solution proposée (SCORE_SPEC_V2)

Pour améliorer la robustesse, une variante "anti-duplication" du score journalier est proposée :

1. **Max par timestamp-country, puis somme** : Pour chaque (DATE, ts_utc, country), prendre MAX(score_impact_v1), puis sommer ces maxima sur la journée
2. **Somme des Top-K scores** (K=5, 10, 20) : Mesure la concentration et limite la dilution
3. **Indice de concentration** (top5/total) : Permet de distinguer "journée dispersée" vs "journée dominée"

Ces métriques sont exposées dans la vue `daily_news_score_robust_v1` (voir scripts associés).

### 8.4. Validation des métriques robustes

Une analyse comparative (`analyze_daily_score_robust_vs_vol_v1.py`) a été réalisée pour mesurer l'amélioration apportée par les métriques robustes :

**Corrélations avec la volatilité réalisée** :

| Métrique | Corrélation brute | Corrélation log-log | Amélioration |
|----------|-------------------|---------------------|--------------|
| `daily_sum_score` (baseline) | 0.111 | 0.15 | - |
| `daily_sum_ts_country_max` (anti-dup) | **0.132** | **0.20** | +19% / +33% |
| `daily_top20_sum` (anti-dilution) | **0.212** | 0.154 | **+91%** / +3% |

**Résultats clés** :

1. **`daily_sum_ts_country_max`** élimine efficacement les artefacts de duplication :
   - 2024-08-15 : score normalisé de 695.22 → 24.00
   - Corrélation améliorée de +19% (brute) et +33% (log-log)

2. **`daily_top20_sum`** présente la meilleure corrélation brute (0.212, presque le double de la baseline) :
   - Progression nette par quartiles : vol médiane Q1 = 63.7 pips → Q4 = 81.8 pips (+28%)
   - Met en avant les journées réellement dominées par quelques événements forts

**Conclusion opérationnelle** :

- **`daily_sum_ts_country_max`** = métrique "anti-artefact" (élimine les duplications)
- **`daily_top20_sum`** = meilleur signal volatilité (corrélation maximale)
- **`top5_share_pct`** = indicateur de concentration (distinction dispersé vs dominé)

Ces trois métriques robustes sont retenues comme **features officielles** pour SCORE_SPEC_V2 et exposées dans la vue `daily_news_score_features_v1`.

---

## 9. TL;DR (résumé opérationnel)

- La chaîne IMPACT_SPEC_V1 + SCORE_SPEC_V1 + VOL_SPEC_V1 est **cohérente et fonctionnelle**.
- Les jours avec au moins **un événement EXTREME** ont :
  - une volatilité médiane **~95 pips**,
  - contre **~58 pips** sans EXTREME.
- Le score journalier `daily_news_score_v1` porte un **signal réel**, surtout lorsqu'on se concentre sur les buckets HIGH / EXTREME.
- Ce rapport sert de **base figée V1** avant d'attaquer la calibration empirique (SCORE_SPEC_V2 / VOL_SPEC_V2).

---

**Fin de VALIDATION_SCORE_IMPACT_V1_VS_VOL_V1**

