# 📊 SCHÉMA BASE DE DONNÉES COMPLET
**Source :** warehouse.duckdb  
**Date extraction :** 04 novembre 2025 - Session 111  
**Usage :** Référence EXACTE de toutes les tables et colonnes

---

## 🎯 TABLES PRINCIPALES

### 1. events (58,449 lignes) ⭐⭐⭐

**Événements économiques**

```sql
CREATE TABLE events (
    ts_utc              TIMESTAMP WITH TIME ZONE,  -- ⚠️ PAS "datetime" !
    country             VARCHAR,
    event_title         VARCHAR,
    event_key           VARCHAR,                    -- Clé pour JOIN
    importance_n        BIGINT,
    actual              DOUBLE,
    previous            DOUBLE,
    estimate            DOUBLE,
    forecast            DOUBLE,
    unit                VARCHAR,
    type                VARCHAR,
    label               VARCHAR,
    comparison          VARCHAR,
    period              VARCHAR,
    change              DOUBLE,
    change_percentage   DOUBLE,
    event_type          VARCHAR
)
```

**Exemple requête :**
```sql
SELECT 
    ts_utc,              -- ⚠️ Utiliser ts_utc
    country,
    event_title,
    event_key,
    actual,
    estimate,
    previous
FROM events
WHERE ts_utc = '2025-09-11 14:30:00+02:00'
ORDER BY importance_n DESC
```

---

### 2. event_families (747 lignes) ⭐⭐⭐

**Scores empiriques par famille d'événement**

```sql
CREATE TABLE event_families (
    event_key           VARCHAR,                    -- Clé unique
    country             VARCHAR,
    family              VARCHAR,
    empirical_score     DOUBLE,                     -- Score ⚠️
    avg_movement_pips   DOUBLE,
    sample_size         INTEGER,
    latency_median      DOUBLE,
    latency_p20         DOUBLE,
    latency_p80         DOUBLE,
    ttr_median          DOUBLE,
    ttr_p20             DOUBLE,
    ttr_p80             DOUBLE,
    mfe_p80             DOUBLE,
    n_events_latency    INTEGER
)
```

**JOIN avec events :**
```sql
SELECT 
    e.ts_utc,
    e.event_title,
    e.actual,
    e.estimate,
    ef.empirical_score,     -- ⚠️ PAS empirical_impact
    ef.latency_median
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
```

---

### 3. prices_1m (1,114,260 lignes) ⭐⭐⭐

**Prix EUR/USD minute par minute**

```sql
CREATE TABLE prices_1m (
    datetime            TIMESTAMP WITH TIME ZONE,   -- ⚠️ Nom correct ici
    timestamp           BIGINT,
    gmtoffset           BIGINT,
    open                DOUBLE,
    high                DOUBLE,
    low                 DOUBLE,
    close               DOUBLE,
    volume              BIGINT
)
```

**Exemple requête :**
```sql
SELECT 
    datetime,           -- ⚠️ Nom correct pour prices
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime BETWEEN '2025-09-11 14:00:00+02:00' 
                   AND '2025-09-11 15:30:00+02:00'
ORDER BY datetime
```

---

### 4. event_impacts_v2 (8,344 lignes) ⭐⭐

**Impacts calculés historiques**

```sql
CREATE TABLE event_impacts_v2 (
    ts_utc              TIMESTAMP WITH TIME ZONE,
    event_key           VARCHAR,
    event_title         VARCHAR,
    country             VARCHAR,
    actual              DOUBLE,
    forecast            DOUBLE,
    previous            DOUBLE,
    surprise_pct        DOUBLE,
    importance          BIGINT,
    phase1_pips         DOUBLE,
    ttr_minutes         INTEGER,
    direction           VARCHAR,
    start_price         DOUBLE,
    ttr_price           DOUBLE,
    source              VARCHAR,
    created_at          TIMESTAMP WITH TIME ZONE
)
```

---

## 🔗 REQUÊTES TYPES

### Extraire événements avec scores

```sql
SELECT 
    e.ts_utc,
    e.country,
    e.event_title,
    e.event_key,
    e.actual,
    e.estimate,
    e.previous,
    e.importance_n,
    ef.empirical_score,
    ef.latency_median
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
ORDER BY e.importance_n DESC, e.event_title
```

### Extraire prix autour d'un événement

```sql
SELECT 
    datetime,
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime BETWEEN '2025-09-11 14:00:00+02:00' 
                   AND '2025-09-11 15:30:00+02:00'
ORDER BY datetime
```

---

## ⚠️ PIÈGES CRITIQUES

### 1. Nom colonne datetime différent selon table

```sql
-- ❌ FAUX
SELECT datetime FROM events  -- Colonne n'existe pas !

-- ✅ CORRECT
SELECT ts_utc FROM events     -- Nom correct
SELECT datetime FROM prices_1m -- Nom correct
```

### 2. Colonnes inexistantes

```sql
-- ❌ FAUX
SELECT empirical_impact FROM event_families  -- N'existe pas !
SELECT timestamp FROM events                 -- Existe mais toujours NULL

-- ✅ CORRECT
SELECT empirical_score FROM event_families   -- Nom correct
SELECT ts_utc FROM events                    -- Colonne utilisée
```

### 3. JOIN events × event_families

```sql
-- ✅ CORRECT
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
-- Les deux tables ont event_key
```

---

## 📊 TABLES SECONDAIRES

### prices_5m (226,329 lignes)
```
datetime, open, high, low, close, volume
```

### prices_1h (19,563 lignes)
```
datetime, open, high, low, close, volume
```

### prices_h4 (4,843 lignes)
```
datetime, open, high, low, close, volume
```

### prices_m15 (77,057 lignes)
```
datetime, open, high, low, close, volume
```

### prices_m30 (38,834 lignes)
```
datetime, open, high, low, close, volume
```

---

## 📋 CHECKLIST AVANT REQUÊTE

Avant d'écrire une requête SQL :

- [ ] Table `events` → Utiliser `ts_utc` (pas `datetime`)
- [ ] Table `prices_*` → Utiliser `datetime` ✅
- [ ] Table `event_families` → Utiliser `empirical_score` (pas `empirical_impact`)
- [ ] JOIN → `e.event_key = ef.event_key` ✅
- [ ] Timezone → Toutes les dates en `+02:00` (Bern Time)

---

## 💡 EXEMPLES DE DONNÉES RÉELLES

### events (extrait)
```
ts_utc: 2022-09-13 04:45:00+02:00
country: NZ
event_title: Food Inflation
event_key: food inflation
importance_n: 1
actual: 8.3
previous: 7.4
estimate: NaN
```

### event_families (extrait)
```
event_key: construction spending_mom
country: US
family: Consumer
empirical_score: 100.0
avg_movement_pips: 84.25
sample_size: 18
latency_median: NaN
```

### prices_1m (extrait)
```
datetime: 2024-06-17 18:12:00+02:00
open: 1.07308
high: 1.07311
low: 1.07305
close: 1.07308
volume: 44
```

---

## 🎯 RÉSUMÉ ULTRA-RAPIDE

```python
# Table events
df = con.execute("""
    SELECT ts_utc, event_key, actual, estimate
    FROM events
    WHERE ts_utc = '2025-09-11 14:30:00+02:00'
""").df()

# Table event_families  
df = con.execute("""
    SELECT event_key, empirical_score, latency_median
    FROM event_families
    WHERE event_key = 'cpi_mom'
""").df()

# Table prices_1m
df = con.execute("""
    SELECT datetime, close
    FROM prices_1m
    WHERE datetime BETWEEN '2025-09-11 14:00:00+02:00' 
                       AND '2025-09-11 15:00:00+02:00'
""").df()

# JOIN
df = con.execute("""
    SELECT e.ts_utc, e.event_title, ef.empirical_score
    FROM events e
    LEFT JOIN event_families ef ON e.event_key = ef.event_key
    WHERE e.ts_utc = '2025-09-11 14:30:00+02:00'
""").df()
```

---

**VERSION :** 1.0  
**SOURCE :** Inspection réelle warehouse.duckdb  
**DERNIÈRE VÉRIFICATION :** 04 novembre 2025 - Session 111
