# 🎯 SCORE_PRED_IMPL_V1 – Note d'implémentation

**Date** : 2025-12-12  
**Version** : SCORE_PRED_IMPL_V1  
**Basé sur** : SCORE_PRED_SPEC_V1

---

## 1. Rappel : Anti-leakage strict

Le score prédictif `score_pred_v1` **ne doit jamais utiliser** :
- ❌ `impact_unified_pips` (de l'événement courant)
- ❌ `score_impact_v1` (de l'événement courant)
- ❌ `surprise_pct` (de l'événement courant)
- ❌ `actual` (de l'événement courant)

**Seule exception autorisée** : Les priors peuvent être basés sur `impact_unified_pips` **uniquement sur l'historique strict** (`ts_local < t`) pour construire des priors ex-ante.

---

## 2. Shrinkage (expanding mean + pseudo-count)

### 2.1. Formule de shrinkage

Pour chaque niveau de prior (event_key, country, event_key+country, global) :

```text
shrunk_mean = (n * mean + m * global_mean) / (n + m)
```

Où :
- `n` = nombre d'observations historiques (strictement < t)
- `mean` = moyenne historique pour ce niveau
- `global_mean` = moyenne globale historique (toutes observations < t)
- `m` = pseudo-count (défaut = 20)

### 2.2. Paramètres

- **m_default** : 20 (utilisé dans les vues)
- **Grid m** : seulement dans l'analyse (`analyze_daily_pred_score_vs_vol_v1.py`), ne modifie pas les vues

---

## 3. Hiérarchie de prior

Ordre de priorité (fallback) :

1. **prior_ekc_pips** : (event_key, country) - le plus spécifique
2. **prior_event_key_pips** : event_key seul
3. **prior_country_pips** : country seul
4. **global_mean_past** : moyenne globale historique

**Prior final** :
```sql
prior_final_pips = COALESCE(
    prior_ekc_pips,
    prior_event_key_pips,
    prior_country_pips,
    global_mean_past
)
```

---

## 4. Calcul rolling strict (< t)

### 4.1. Window functions avec frame

Tous les calculs de priors utilisent des window functions avec frame strict :

```sql
ORDER BY ts_local
ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
```

Cela garantit qu'aucune observation future n'est utilisée.

### 4.2. Cas particulier : début de série

Si `global_mean_past IS NULL` (première date) :
- `prior_final_pips = NULL`
- `prior_component = LN(1 + 0.0) = 0.0`
- `score_pred_v1` minimal (seulement importance_component)

---

## 5. Formule du score prédictif V1

```text
importance_component = COALESCE(importance_n, 1) / 5.0
prior_component = LN(1 + COALESCE(prior_final_pips, 0.0))
score_pred_v1 = importance_component * prior_component
```

**Propriétés** :
- `score_pred_v1 >= 0` (toujours positif)
- Purement ex-ante (calculable avant la release)
- Interprétable (importance × log-prior)

---

## 6. Outputs attendus des vues

### 6.1. `event_priors_rolling_v1`

Pour chaque événement (ts_local, country, event_key) :
- `prior_ekc_pips`, `prior_event_key_pips`, `prior_country_pips`, `prior_final_pips`
- `ekc_n_past`, `event_key_n_past`, `country_n_past`, `global_n_past`
- `global_mean_past`

### 6.2. `events_with_pred_score_v1`

Pour chaque événement :
- `score_pred_v1` (score prédictif ex-ante)
- `importance_component`, `prior_component`
- `prior_final_pips` (pour debug)
- Toutes les colonnes de `events_with_ts_local_v1`

### 6.3. `daily_pred_score_robust_v1`

Pour chaque date :
- `pred_daily_sum` : SUM(score_pred_v1)
- `pred_daily_sum_ts_country_max` : anti-duplication
- `pred_daily_top5_sum`, `pred_daily_top20_sum` : anti-dilution
- `pred_top1_share_pct`, `pred_top5_share_pct` : concentration
- `n_events`, `n_ts_country_groups`

---

## 7. Split temporel strict (analyse)

Pour l'analyse `analyze_daily_pred_score_vs_vol_v1.py` :

- **Train** : `min_date → cutoff` (pour calibrer/observer)
- **Test** : `cutoff+1 → max_date` (pour évaluer la prédictivité)

**Règle critique** : Quand on évalue un jour test, les priors n'utilisent **jamais** des événements futurs (garanti par le rolling strict < t).

---

## 8. Timezone

- Utiliser `ts_local` (alias de `ts_utc`) via `events_with_ts_local_v1`
- Pas de conversion timezone (voir TIMEZONE_NOTE.md)

---

**Fin de SCORE_PRED_IMPL_V1**

