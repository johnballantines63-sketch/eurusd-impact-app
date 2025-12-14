# VALIDATION SCORE PRÉDICTIF V1 — BASELINE STABLE

**Version :** V1  
**Date validation :** 2025-12-12  
**Statut :** ✅ BASELINE FIGÉE — Ne plus modifier

---

## 1. DÉCISIONS V1 FIGÉES

### 1.1 Formule Score Prédictif

**Formule :** `score_pred_v1 = importance_component × prior_component`

**Composantes :**
- `importance_component = COALESCE(importance_n, 1) / 5.0`
- `prior_component = LN(1 + COALESCE(prior_final_pips, 0.0))`

**Formule complète :**
```sql
score_pred_v1 = (COALESCE(importance_n, 1) / 5.0) * LN(1.0 + COALESCE(prior_final_pips, 0.0))
```

**Vue source :** `events_with_pred_score_v1`

### 1.2 Rolling Strict < t

**Règle :** Tous les calculs de priors utilisent une fenêtre rolling **strictement antérieure** à l'événement courant.

**Implémentation SQL :**
```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
```

**Garantie :** Aucune information future (`t` ou post-`t`) n'est utilisée dans le calcul des priors à la date `t`.

**Vue source :** `event_priors_rolling_v1`

### 1.3 Shrinkage

**Paramètre :** `m_default = 20` (pseudo-count)

**Formule shrinkage :**
```sql
shrunk_mean = (n * mean + m * global_mean) / (n + m)
```

**Note :** Le paramètre `m` peut être analysé via grid search en analyse, mais la valeur par défaut production est `m=20`.

**Vue source :** `event_priors_rolling_v1`

### 1.4 Métrique Journalière Retenue

**Métrique :** `pred_daily_top20_sum`

**Définition :** Somme des `score_pred_v1` des 20 événements les plus importants de la journée (anti-dilution).

**Vue source :** `daily_pred_score_robust_v1`

**Alternatives analysées :**
- `pred_daily_top5_sum` : trop restrictif (non évalué formellement en walk-forward V1)
- `pred_daily_sum_ts_country_max` : performance inférieure (voir section 2)

### 1.5 Séparation Prédictif vs Rétrospectif

**Règle critique :** Le calcul de `score_pred_v1` n'utilise aucune information post-release (`actual`, `surprise_pct`, `impact_unified_*`). Des colonnes post-release peuvent exister en sortie pour inspection, mais ne doivent jamais être utilisées dans le calcul.

**Garantie :** Aucun risque de leakage accidentel dans les calculs ex-ante.

---

## 2. VALIDATION WALK-FORWARD

### 2.1 Résultats Walk-Forward

| Cutoff | n_train | n_test | Pearson | Spearman | Pearson(log) |
|--------|---------|--------|---------|----------|--------------|
| 2023-01-01 | 33 | 681 | 0.1126 | 0.1382 | 0.1595 |
| 2023-07-01 | 124 | 590 | 0.1747 | 0.1959 | 0.2474 |
| 2024-01-01 | 240 | 474 | 0.1671 | 0.1707 | 0.2640 |
| 2024-07-01 | 370 | 344 | 0.1374 | 0.0999 | 0.2842 |

**Moyennes :** Pearson=0.1479, Spearman=0.1511, Pearson(log)=0.2388

**Script :** `scripts/analyze_daily_pred_score_vs_vol_walkforward_v1.py`

### 2.2 Comparaison avec Baselines

| Métrique | Pearson | Spearman | Pearson(log) |
|----------|---------|----------|--------------|
| **Score (pred_daily_top20_sum)** | **0.1479** | **0.1511** | **0.2388** |
| n_us_events_day | 0.0960 | 0.2084 | 0.1377 |
| n_events_day | 0.0709 | 0.1641 | 0.1384 |
| n_ts_country_groups_day | 0.0731 | 0.1530 | 0.1731 |
| max_importance_day | 0.0386 | 0.0609 | 0.0479 |

**Baselines calculées depuis :** `events_with_ts_local_v1` (agrégation par date)

---

## 3. INTERPRÉTATION

### 3.1 Performance vs Baselines

**Pearson :** Le score bat toutes les baselines (0.1479 vs max 0.0960 pour `n_us_events_day`).  
**Pearson(log) :** Le score bat toutes les baselines (0.2388 vs max 0.1731 pour `n_ts_country_groups_day`).  
**Spearman :** Le score est inférieur à `n_us_events_day` (0.1511 vs 0.2084). Cette baseline capture un effet volume US qui sera traité en V2 via `release_group` (déduplication des macro reports).

### 3.2 Stabilité Temporelle

**Pearson :** min=0.1126, max=0.1747 (écart ~0.06) — **acceptable**  
**Spearman :** min=0.0999, max=0.1959 (écart ~0.10) — **acceptable**  
**Pearson(log) :** min=0.1595, max=0.2842 — **bonne stabilité**

**Conclusion :** Pas de dérive majeure sur les différents cutoffs temporels.

### 3.3 Interprétation Scientifique

Le score n'est pas linéairement explicatif sur toute la distribution (Pearson modéré), mais il classe correctement les journées à risque (Spearman positif). C'est exactement ce qu'on attend d'un score de risque ex-ante.

**Usage recommandé :**
- ✅ Ranking des journées par risque
- ✅ Alertes sur journées à fort risque
- ✅ Sizing positionnel relatif

**Usage non recommandé :**
- ❌ Prédiction ponctuelle de volatilité absolue
- ❌ Objectif R² élevé (mauvais objectif pour un score de risque)

---

## 4. GUARDRAILS

### 4.1 Guardrail Timezone

**Script :** `scripts/check_timezone_guardrail.py`  
**Documentation :** `docs/TIMEZONE_NOTE.md`

**Vérification :** Pour des dates repères (ex: 2025-08-01, 2024-09-11), les événements à 14:30 coïncident avec un spike de range sur les prix (vs shifts ±1h/±2h).

**Règle :** `events.ts_utc` et `prices_finnhub_m1.datetime` sont stockés en heure Europe/Zurich (avec offset). Aucune conversion timezone n'est appliquée dans les vues/jointures.

### 4.2 Guardrail Unicité Événements

**Script :** `scripts/check_event_uniqueness_guardrail.py`

**Vérifications :**
- Comptages des vues clés (`events_with_ts_local_v1`, `events_with_pred_score_v1`, etc.)
- Cohérence : `COUNT(*) events_with_pred_score_v1 == COUNT(*) events_with_ts_local_v1`
- Détection de duplications sur `(ts_local, country, event_key)`

**Exit code :** 1 si violation détectée

### 4.3 Règle de Blocage

**Toute modification structurelle** (formule, rolling, shrinkage, métrique) doit :
1. Passer tous les guardrails
2. Maintenir ou améliorer les métriques walk-forward
3. Être documentée dans ce fichier

**Un échec du guardrail bloque tout changement structurel.**

---

## 5. LIMITES CONNUES

### 5.1 Duplications Structurelles

**Problème :** Certaines dates présentent des duplications sur `(ts_local, country, event_key)` (ex: 2025-06-26, ×17 pour certains événements US).

**Cause :** Un macro release ≠ une ligne dans la table. Exemples :
- NFP (headline + unemployment rate + average hourly earnings)
- CPI (headline + core + sous-composantes)
- PMI multi-composantes
- Rapports découpés par sous-indicateurs

**Impact :** Bruit dans le score journalier, dilution de l'information.

**Solution V2 :** Introduction de `release_group` (regroupement par `(ts_local, country, release_family)`).

### 5.2 Spearman vs n_us_events_day

Le score est inférieur à `n_us_events_day` en Spearman (0.1511 vs 0.2084). Cette baseline capture un effet volume US qui sera mieux modélisé en V2 via `release_group` (déduplication).

### 5.3 Calibration m

Le paramètre `m=20` est fixé par défaut. Une analyse de stabilité cross-cutoffs peut être réalisée pour optimiser ce paramètre, mais la valeur actuelle est validée pour V1.

---

## 6. PLAN V2

### 6.1 Release Group / Déduplication Macro Reports

**Objectif :** Regrouper les lignes correspondant à la même publication macro.

**Clé proposée :** `(ts_local, country, release_family)`

**Mapping :** `release_family` dérivée de `event_key` (mapping explicite à définir).

**Résultat attendu :**
- Réduction du bruit (17 lignes → 1 release)
- Amélioration des corrélations sans toucher au cœur du score
- Dépassement de `n_us_events_day` en Spearman

**Statut :** À spécifier proprement avant implémentation.

### 6.2 Features Calendaires Optionnelles

**Idées explorables :**
- Jour de la semaine (lundi vs vendredi)
- Position dans le mois (début vs fin)
- Proximité d'autres événements majeurs

**Statut :** Optionnel, à évaluer après release_group.

### 6.3 Calibration m via Stabilité Cross-Cutoffs

**Approche :** Analyser la variance inter-cutoffs pour différents `m` (5, 10, 20, 30).

**Critère :** Choisir le `m` le plus stable, pas nécessairement le plus élevé.

**Statut :** Analyse optionnelle, `m=20` validé pour V1.

---

## 7. CONCLUSION

### 7.1 Statut Actuel

✅ **Pipeline ex-ante no-leakage : VALIDÉ**  
✅ **Rolling strict < t : VALIDÉ**  
✅ **Shrinkage maîtrisé : VALIDÉ**  
✅ **Séparation prédictif vs rétrospectif : VALIDÉ**  
✅ **Guardrails en place : VALIDÉ**  
✅ **Guardrail unicité en place : VALIDÉ**  
⚠️ **Duplications présentes dans les sources : CONNU / TRACKÉ (voir 5.1) — traité en V2 via release_group**  
✅ **Analyse walk-forward : VALIDÉ**  
✅ **Score bat baselines sur Pearson et Pearson(log) : VALIDÉ**

### 7.2 Exploitabilité

**Le système est exploitable comme indicateur de risque ex-ante.**

**Usage recommandé :**
- Ranking des journées par risque
- Alertes sur journées à fort risque
- Sizing positionnel relatif

**La suite n'est plus de la réparation, c'est de l'ingénierie de signal.**

---

**Document créé le :** 2025-12-12  
**Dernière mise à jour :** 2025-12-12  
**Version :** V1 (BASELINE FIGÉE)

