# 📊 STRUCTURE BASE DE DONNÉES (CERTIFIÉE)

**Dernière validation :** 21 octobre 2025 - Session 26  
**Base :** `fx_impact_app/data/warehouse.duckdb` (205 MB)

---

## 🎯 TABLES PRIMAIRES (ne pas modifier)

### `events` (58,449 lignes) ⭐

```sql
CREATE TABLE events (
    ts_utc TIMESTAMP WITH TIME ZONE,  -- ⚠️  Format: '2025-09-11 14:30:00+02:00'
    event_key VARCHAR,
    event_title VARCHAR,
    country VARCHAR,
    actual DOUBLE,
    forecast DOUBLE,                   -- ⚠️  À utiliser pour surprise
    previous DOUBLE,                   -- ⚠️  NE PAS utiliser pour surprise
    estimate DOUBLE,
    importance_n BIGINT,
    period VARCHAR,
    change DOUBLE,
    change_percentage DOUBLE,
    event_type VARCHAR
)
```

**RÈGLES CRITIQUES :**
- ✅ Surprise = `ABS((actual - forecast) / forecast) * 100`
- ❌ NE JAMAIS utiliser `previous` pour surprise
- ⚠️  `ts_utc` contient offset timezone (+02:00 en été, +01:00 en hiver)
- ⚠️  Pour requêtes, convertir en UTC pur

**Source :** EODHD API  
**Fréquence mise à jour :** Quotidienne

---

### `event_families` (747 lignes)

```sql
CREATE TABLE event_families (
    event_key VARCHAR,
    family_name VARCHAR,
    importance INTEGER
)
```

**Usage :** Mapping événements → familles  
**Source :** Manuel (Session 22)  
**Statut :** ✅ Validé

---

### `scores` (991 lignes)

```sql
CREATE TABLE scores (
    event_key_or_family VARCHAR,
    score DOUBLE
)
```

**Usage :** Scores empiriques par événement/famille  
**Source :** Calculs validés  
**Statut :** ✅ Validé

---

### `prices_1m` (1,114,260 lignes) ⭐⭐⭐

```sql
CREATE TABLE prices_1m (
    datetime TIMESTAMP WITH TIME ZONE,  -- Format: '2025-09-11 12:30:00+02:00'
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE
)
```

**RÈGLES CRITIQUES :**
- ⚠️  `datetime` contient offset timezone (+02:00)
- ⚠️  Pour requêtes, convertir timestamps en UTC
- ✅ Prix validés Session 26 : 11 sept 12:30 UTC = 1.16874

**Source :** Dukascopy (tick-by-tick agrégé M1)  
**Période :** 2022-10-23 21:00 UTC → 2025-10-20 21:59 UTC  
**Statut :** ✅ Validé Session 25/26

**Validation cas référence :**
```sql
SELECT datetime, open FROM prices_1m
WHERE datetime >= '2025-09-11 12:30:00'
AND datetime <= '2025-09-11 12:45:00'
ORDER BY datetime LIMIT 1
-- Résultat attendu : open ≈ 1.16874
```

---

## 🆕 TABLES DÉRIVÉES V2 (Session 26)

### `event_impacts_v2` (16,660 lignes) ⭐

```sql
CREATE TABLE event_impacts_v2 (
    ts_utc TIMESTAMP WITH TIME ZONE,
    event_key VARCHAR,
    event_title VARCHAR,
    country VARCHAR,
    actual DOUBLE,
    forecast DOUBLE,
    previous DOUBLE,
    surprise_pct DOUBLE,              -- Calculé avec forecast uniquement
    importance INTEGER,
    phase1_pips DOUBLE,               -- Depuis prices_1m Dukascopy
    ttr_minutes INTEGER,
    direction VARCHAR,                -- UP ou DOWN
    start_price DOUBLE,
    ttr_price DOUBLE,
    source VARCHAR,                   -- 'dukascopy_session26_v2'
    created_at TIMESTAMP
)
```

**Usage :** Événements individuels avec impacts calculés  
**Filtre :** surprise > 30%  
**Source :** Calculé depuis `events` + `prices_1m`  
**Statut :** ✅ Validé Session 26

**Validation :**
```sql
SELECT ts_utc, phase1_pips FROM event_impacts_v2
WHERE ts_utc::DATE = '2025-09-11' 
AND EXTRACT(HOUR FROM ts_utc) = 12
ORDER BY phase1_pips DESC LIMIT 1
-- Résultat attendu : phase1_pips ≈ 33.7 pips
```

---

### `event_groups_v2` (à créer)

```sql
CREATE TABLE event_groups_v2 (
    group_id VARCHAR PRIMARY KEY,
    ts_utc TIMESTAMP WITH TIME ZONE,
    num_events INTEGER,
    event_keys VARCHAR,
    event_titles VARCHAR,
    countries VARCHAR,
    max_surprise_pct DOUBLE,
    avg_surprise_pct DOUBLE,
    phase1_pips DOUBLE,
    ttr_minutes INTEGER,
    direction VARCHAR,
    max_score DOUBLE,
    start_price DOUBLE,
    ttr_price DOUBLE,
    source VARCHAR,
    created_at TIMESTAMP
)
```

**Usage :** Groupes multi-événements (fenêtre 5 min)  
**Source :** À calculer depuis `events` + `prices_1m`  
**Statut :** ⏳ À créer

---

## ❌ TABLES OBSOLÈTES (supprimées)

- `event_impacts_calculated` - Corrompue (anciennes sources)
- `event_group_impacts` - Corrompue (anciennes sources)

---

## 🔍 REQUÊTES STANDARDS

### Lire événement avec surprise

```sql
SELECT 
    ts_utc,
    event_title,
    country,
    actual,
    forecast,
    CASE 
        WHEN forecast IS NOT NULL AND forecast != 0 
        THEN ABS((actual - forecast) / forecast) * 100
        ELSE NULL
    END as surprise_pct
FROM events
WHERE actual IS NOT NULL AND forecast IS NOT NULL
```

### Lire prix pour un événement

```python
# Python avec conversion timezone
import pandas as pd

event_time = pd.to_datetime('2025-09-11 14:30:00+02:00', utc=True)
event_time_str = event_time.strftime('%Y-%m-%d %H:%M:%S')

query = f"""
SELECT datetime, open, high, low, close
FROM prices_1m
WHERE datetime >= '{event_time_str}'::timestamp
AND datetime <= ('{event_time_str}'::timestamp + INTERVAL '15 minutes')
ORDER BY datetime
"""
```

---

## 📋 CHECKLIST UTILISATION

Avant d'interroger la base :

- [ ] Surprise calculée avec `forecast` (pas `previous`)
- [ ] Timezone convertie en UTC pour requêtes
- [ ] Validation cas référence si calculs d'impact
- [ ] Tables V2 utilisées (pas obsolètes)

---

**FIN DOCUMENT**

**Prochaine mise à jour :** Ajout event_groups_v2 après création
