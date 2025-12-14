# Release V4.0 — Checklist & note de méthodologie (EURUSD News Impact)

**Objectif :** figer une version *reproductible* du pipeline V4 (scoring + direction) avec paramètres, données, et procédure d’audit documentés.

---

## Paramètres retenus (V4.0)

- **Fenêtre d’apprentissage :** `--years 3`
- **Mesure d’impact post-release :** `--after-min 120`
- **Calibration probas (direction) :** `temp = 0.6` (sélectionnée sur **TRAIN** via **logloss**)
- **Seuil décisionnel direction (classification) :** `threshold = 0.475` (sélectionné sur **TRAIN** via **Youden J**)

> Notes :
> - `temp` sert à calibrer la *confiance* (`prob_up`). Il ne change pas l’ordre des prédictions, donc l’AUC est stable.
> - `threshold` ne sert qu’à transformer `prob_up` en signal binaire (up/down) pour métriques de classification.

---

## Pré-requis (sources)

- **Truth (labels) :** `daily_pattern_truth_v4`
- **Événements enrichis :** `events_enriched_v1` (VIEW)
- **Prix M1 :** `prices_finnhub_m1`

Vérif rapide :
```sql
SELECT MIN(date_local), MAX(date_local), COUNT(*) FROM daily_pattern_truth_v4;
SELECT MIN(date_local), MAX(date_local), COUNT(DISTINCT date_local) FROM events_enriched_v1;
SELECT MIN(datetime), MAX(datetime), COUNT(*) FROM prices_finnhub_m1;
```

---

## 1) Freeze de la configuration (fichier YAML)

Fichier attendu : `config/v4_0.yaml`.

C’est le “contrat” de reproductibilité : on fige tous les paramètres et choix importants.
Exemple minimal recommandé (à adapter si ta version finale diffère) :

```yaml
v4_version: "4.0"
db: "data/warehouse.duckdb"

build:
  years: 3
  after_minutes: 120
  min_n_releases: 20
  shrinkage_k: 20

direction:
  split_date: "2024-01-01"
  temp: 0.6
  clip_logit: 8
  threshold: 0.475
  threshold_criterion: "youden"
  temp_criterion: "logloss"

notes:
  release_id: "country | DATE_TRUNC('minute', ts_utc)"
  bundle_dedup: "aggregate per release_id (max)"
```

---

## 2) Procédure V4.0 — Exécution standard

### 2.1 Construire les priors empiriques (event scores)
```bash
python3 research/build_v4_scoring.py \
  --db data/warehouse.duckdb \
  --build-event-scores \
  --years 3 \
  --after-min 120
```

### 2.2 Apprendre les poids du kernel (direction + impact)
```bash
python3 research/build_v4_scoring.py \
  --db data/warehouse.duckdb \
  --fit-kernel-weights \
  --years 3 \
  --after-min 120
```

### 2.3 Scorer les dates (panel)
**Rappel :** `--score-dates` exige `--dates` ou `--panel-file`.

```bash
# via panel-file (recommandé)
python3 research/build_v4_scoring.py \
  --db data/warehouse.duckdb \
  --score-dates \
  --panel-file outputs/panel_dates.csv \
  --years 3 \
  --after-min 120

# ou subset
python3 research/build_v4_scoring.py \
  --db data/warehouse.duckdb \
  --score-dates \
  --dates "2025-08-01,2025-09-11" \
  --years 3 \
  --after-min 120
```

---

## 3) Audit directionnel (split temporel, sans fuite)

### 3.1 Choisir `temp` sur TRAIN (logloss), reporter sur TEST
```bash
python3 v4_directional_backtest_v3.py \
  --db data/warehouse.duckdb \
  --csv outputs/v4_scores_panel_YYYYMMDD_HHMMSS.csv \
  --years 3 \
  --split-date 2024-01-01 \
  --sweep-temps \
  --temp-criterion logloss \
  --clip-logit 8
```

### 3.2 Choisir `threshold` sur TRAIN (Youden), reporter sur TEST
```bash
python3 v4_directional_backtest_v3.py \
  --db data/warehouse.duckdb \
  --csv outputs/v4_scores_panel_YYYYMMDD_HHMMSS.csv \
  --years 3 \
  --split-date 2024-01-01 \
  --temp 0.6 \
  --clip-logit 8 \
  --sweep-thresholds \
  --criterion youden
```

---

## 4) Critères d’acceptation (V4.0)

- [ ] Reproductibilité : relancer 2× produit les mêmes métriques (à bruit d’arrondi près).
- [ ] Aucune fuite temporelle : `temp` et `threshold` sélectionnés uniquement sur TRAIN.
- [ ] Bundle dédupliqué : `kernel_releases` reflète bien les releases uniques (NFP/EIA/PPI non multipliés).
- [ ] Self-test OK : `score_0_100 ∈ [0,100]`, `prob_up ∈ (0,1)`, `prob_up + prob_down = 1`.
- [ ] Stabilité : résultats cohérents sur plusieurs split-dates (≥2).
- [ ] Tables cohérentes : `event_scores_empirical_v4` et `kernel_weights_v4` remplies (rows > 0).
- [ ] Readonly OK : `--readonly`/`--dry-run` n’effectuent aucune écriture.

---

## 5) Tag & gel du code (V4.0)

- [ ] Commit “freeze” (incluant `config/v4_0.yaml`, scripts backtest, audit runner).
- [ ] Tag Git : `v4.0`
- [ ] Après tag : aucun patch (sinon `v4.0.1` avec nouveau YAML + nouvelle note).

---

## 6) Notes méthodologiques (résumé)

- **Option A (release-level)** : impact mesuré 1× par `release_id` puis agrégé par `event_key`.
- **Shrinkage**
  - `p80_shrunk = (n*p80 + k*p80_global)/(n+k)` avec `k=20`
  - `hit_ratio_shrunk` via posterior mean Beta-Binomial
- **Fiabilité**
  - `reliability='high'` si `n_releases >= 20`
  - poids `w_rel = min(1, n_releases/min_n)` appliqué aux clés “low”
- **Direction** : modèle additif + sigmoid ; calibration via température (`temp`) sélectionnée sur TRAIN.

---

### Annexes — commandes utiles

Dernier CSV produit automatiquement :
```bash
CSV="$(ls -1t outputs/v4_scores_panel_*.csv | head -1)"
echo "$CSV"
```
