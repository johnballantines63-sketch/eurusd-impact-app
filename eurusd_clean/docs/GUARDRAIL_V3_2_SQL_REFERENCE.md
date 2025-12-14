# GUARDRAIL V3.2 — SQL REFERENCE (DuckDB)

**Date :** 2025-12-12  
**Usage :** Audit, CI, notebook, debug rapide

---

## 1. COHÉRENCE COUNT(*) V3.1 vs V3.2

```sql
SELECT
    (SELECT COUNT(*) FROM daily_pred_score_v3_1_dataset_v1) AS n_v3_1,
    (SELECT COUNT(*) FROM daily_pred_score_v3_2_dataset_v1) AS n_v3_2,
    CASE
        WHEN
            (SELECT COUNT(*) FROM daily_pred_score_v3_1_dataset_v1)
            =
            (SELECT COUNT(*) FROM daily_pred_score_v3_2_dataset_v1)
        THEN 'OK'
        ELSE 'MISMATCH'
    END AS status;
```

**Règle attendue :** `status = 'OK'` et `n_v3_1 = n_v3_2`

---

## 2. COUVERTURE DATES IDENTIQUE AVEC LA VOLATILITÉ

```sql
SELECT
    COUNT(DISTINCT v3.date) AS n_dates_v3_2,
    COUNT(DISTINCT vol.date) AS n_dates_vol,
    COUNT(DISTINCT CASE WHEN vol.date IS NULL THEN v3.date END) AS missing_in_vol
FROM daily_pred_score_v3_2_dataset_v1 v3
LEFT JOIN daily_eurusd_volatility_v1 vol
    ON v3.date = vol.date;
```

**Règles attendues :**
- `missing_in_vol = 0`
- `n_dates_v3_2 <= n_dates_vol`

---

## 3. NULLs SUR COLONNES CRITIQUES

```sql
SELECT
    COUNT(*) AS n_total,
    COUNT(CASE WHEN date IS NULL THEN 1 END) AS null_date,
    COUNT(CASE WHEN score_v2_1 IS NULL THEN 1 END) AS null_score,
    COUNT(CASE WHEN target_vol_pips IS NULL THEN 1 END) AS null_target,
    COUNT(CASE WHEN n_us_events_day IS NULL THEN 1 END) AS null_density
FROM daily_pred_score_v3_2_dataset_v1;
```

**Règle :** Tous les compteurs `null_* = 0`

---

## 4. BORNES & DISTRIBUTION DE n_us_events_day

```sql
SELECT
    MIN(n_us_events_day) AS min_events,
    MAX(n_us_events_day) AS max_events,
    MEDIAN(n_us_events_day) AS p50_events,
    AVG(n_us_events_day) AS avg_events,
    COUNT(CASE WHEN n_us_events_day < 0 THEN 1 END) AS negative_count
FROM daily_pred_score_v3_2_dataset_v1;
```

**Règles :**
- `negative_count = 0`
- `min_events >= 0`
- Distribution cohérente (pas de valeurs aberrantes non expliquées)

**Valeurs attendues (référence) :**
- `min_events = 0`
- `max_events ≈ 300-350`
- `p50_events ≈ 6-7`
- `avg_events ≈ 15-20`

---

## 5. COHÉRENCE n_us_events_day AVEC LA TABLE ÉVÉNEMENTS

```sql
WITH expected AS (
    SELECT
        DATE(ts_local) AS date,
        COUNT(CASE WHEN country = 'US' THEN 1 END) AS n_us_expected
    FROM events_with_ts_local_v1
    GROUP BY DATE(ts_local)
)
SELECT
    COUNT(*) AS n_mismatches
FROM daily_pred_score_v3_2_dataset_v1 v3
JOIN expected e
    ON v3.date = e.date
WHERE v3.n_us_events_day != e.n_us_expected;
```

**Règle :** `n_mismatches = 0`

---

## 6. GARANTIE EX-ANTE (STRUCTURELLE)

```sql
SELECT
    COUNT(*) AS n_rows,
    COUNT(CASE WHEN n_us_events_day > 0 AND target_vol_pips IS NULL THEN 1 END) AS suspicious_rows
FROM daily_pred_score_v3_2_dataset_v1;
```

**Règle :** `suspicious_rows` devrait être faible ou 0 (conceptuel, pas bloquant)

**Note :** On ne bloque pas dessus, mais toute valeur élevée serait un signal d'architecture suspecte.

---

## 7. VÉRIFICATION COMPLÈTE (ALL-IN-ONE)

```sql
WITH checks AS (
    -- 1. COUNT(*) cohérence
    SELECT
        'count_coherence' AS check_name,
        CASE
            WHEN (SELECT COUNT(*) FROM daily_pred_score_v3_1_dataset_v1)
                 = (SELECT COUNT(*) FROM daily_pred_score_v3_2_dataset_v1)
            THEN 'PASS'
            ELSE 'FAIL'
        END AS status
    UNION ALL
    -- 2. Couverture dates
    SELECT
        'date_coverage' AS check_name,
        CASE
            WHEN (
                SELECT COUNT(DISTINCT CASE WHEN vol.date IS NULL THEN v3.date END)
                FROM daily_pred_score_v3_2_dataset_v1 v3
                LEFT JOIN daily_eurusd_volatility_v1 vol ON v3.date = vol.date
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END AS status
    UNION ALL
    -- 3. NULLs
    SELECT
        'nulls_check' AS check_name,
        CASE
            WHEN (
                SELECT COUNT(*)
                FROM daily_pred_score_v3_2_dataset_v1
                WHERE date IS NULL
                   OR score_v2_1 IS NULL
                   OR target_vol_pips IS NULL
                   OR n_us_events_day IS NULL
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END AS status
    UNION ALL
    -- 4. Bornes
    SELECT
        'bounds_check' AS check_name,
        CASE
            WHEN (
                SELECT COUNT(*)
                FROM daily_pred_score_v3_2_dataset_v1
                WHERE n_us_events_day < 0
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END AS status
    UNION ALL
    -- 5. Cohérence événements
    SELECT
        'events_coherence' AS check_name,
        CASE
            WHEN (
                WITH expected AS (
                    SELECT
                        DATE(ts_local) AS date,
                        COUNT(CASE WHEN country = 'US' THEN 1 END) AS n_us_expected
                    FROM events_with_ts_local_v1
                    GROUP BY DATE(ts_local)
                )
                SELECT COUNT(*)
                FROM daily_pred_score_v3_2_dataset_v1 v3
                JOIN expected e ON v3.date = e.date
                WHERE v3.n_us_events_day != e.n_us_expected
            ) = 0
            THEN 'PASS'
            ELSE 'FAIL'
        END AS status
)
SELECT
    check_name,
    status,
    CASE WHEN status = 'PASS' THEN '✅' ELSE '❌' END AS icon
FROM checks
ORDER BY check_name;
```

**Résultat attendu :** Tous les checks = `PASS`

---

## 8. USAGE

### 8.1 Dans un notebook Python

```python
import duckdb

conn = duckdb.connect("data/warehouse.duckdb", read_only=True)

# Exécuter un check
result = conn.execute("""
    SELECT ... -- un des snippets ci-dessus
""").df()

print(result)
```

### 8.2 Dans CI/CD

```bash
# Exécuter le guardrail complet
duckdb data/warehouse.duckdb < guardrail_v3_2.sql
```

### 8.3 Debug rapide

```sql
-- Vérifier rapidement un check spécifique
-- Exemple : vérifier les NULLs
SELECT
    COUNT(CASE WHEN n_us_events_day IS NULL THEN 1 END) AS null_density
FROM daily_pred_score_v3_2_dataset_v1;
```

---

**Document créé le :** 2025-12-12  
**Version :** V3.2.1

