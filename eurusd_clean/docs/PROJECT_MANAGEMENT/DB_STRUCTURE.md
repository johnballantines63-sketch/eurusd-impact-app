# 📋 DATABASE STRUCTURE - RÉFÉRENCE PERMANENTE

**Date création :** 14 novembre 2025 - Session 135  
**DB Path :** `/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/data/warehouse.duckdb`

⚠️ **LIRE CE FICHIER AVANT TOUT ACCÈS DB** - Évite recherches répétées structure

---

## 🗄️ TABLES PRINCIPALES

### **Table `events`** (125,625 événements) ✅ PRINCIPALE

**Période :** 2020-01-01 → 2026-01-01

**Structure :**
```sql
ts_utc               TIMESTAMP WITH TIME ZONE  -- Timestamp UTC
country              VARCHAR                   -- Code pays (US, EU, GB, etc.)
event_title          VARCHAR                   -- Titre événement
event_key            VARCHAR                   -- Clé unique
importance_n         BIGINT                    -- Importance NUMÉRIQUE
actual               DOUBLE                    -- Valeur réelle
previous             DOUBLE                    -- Valeur précédente
estimate             DOUBLE                    -- Estimation
forecast             DOUBLE                    -- Prévision
```

**⚠️ IMPORTANCE_N - VALEURS RÉELLES :**
```
importance_n = 2 : 125,625 événements (100%)
```

**❌ PAS D'ÉVÉNEMENTS HIGH (importance_n = 3) DANS CETTE TABLE !**

---

### **Table `economic_events`** (125,625 événements) ⚠️ ALTERNATIVE

**Structure :**
```sql
event_id         VARCHAR    -- ID unique
datetime_utc     TIMESTAMP  -- ⚠️ PAS "ts_utc" !
event_name       VARCHAR    -- Nom événement
country          VARCHAR    -- Pays
importance       VARCHAR    -- ⚠️ TEXTE : 'MEDIUM', 'HIGH', 'LOW'
actual           DOUBLE     -- Valeur actuelle
forecast         DOUBLE     -- Prévision
previous         DOUBLE     -- Valeur précédente
source           VARCHAR    -- Source données
raw_data         JSON       -- Données brutes
```

**⚠️ IMPORTANCE - VALEURS RÉELLES :**
```
importance = 'MEDIUM' : 125,625 événements (100%)
```

---

### **Table `event_families`** ✅ SCORES EMPIRIQUES

**Structure :**
```sql
event_key         VARCHAR  -- Clé événement
country           VARCHAR  -- Pays
empirical_score   DOUBLE   -- Score empirique validé
```

**Usage :** Enrichir événements avec scores pour calcul impact

---

### **Table `prices_bern`** ✅ PRIX 1-MINUTE

**Structure :**
```sql
datetime  TIMESTAMP WITH TIME ZONE  -- Timezone Europe/Zurich
open      DOUBLE                     -- Prix ouverture
high      DOUBLE                     -- Prix haut
low       DOUBLE                     -- Prix bas
close     DOUBLE                     -- Prix clôture
```

**Timezone :** Europe/Zurich (UTC+01:00 hiver / UTC+02:00 été)

---

## 🚨 ERREURS FRÉQUENTES À ÉVITER

### ❌ **Erreur #1 : Chercher importance_n = 3**
```python
# ❌ FAUX - Retourne 0 résultats
WHERE importance_n = 3  # Aucun événement HIGH !
```

### ✅ **Correct : Utiliser importance_n = 2 OU filtrer par score**
```python
# ✅ Option A : Tous les MEDIUM
WHERE importance_n = 2

# ✅ Option B : Filtrer par score empirique
SELECT e.*, f.empirical_score
FROM events e
LEFT JOIN event_families f 
  ON e.event_key = f.event_key AND e.country = f.country
WHERE f.empirical_score > 40.0  -- Équivalent HIGH
```

---

### ❌ **Erreur #2 : Utiliser ts_utc dans economic_events**
```python
# ❌ FAUX - Colonne n'existe pas
SELECT * FROM economic_events WHERE ts_utc = ...
```

### ✅ **Correct : Utiliser datetime_utc**
```python
# ✅ CORRECT
SELECT * FROM economic_events WHERE datetime_utc = ...
```

---

### ❌ **Erreur #3 : Chercher importance = 'HIGH' dans events**
```python
# ❌ FAUX - Colonne importance est numérique (importance_n)
SELECT * FROM events WHERE importance = 'HIGH'
```

### ✅ **Correct : Utiliser importance_n numérique**
```python
# ✅ CORRECT
SELECT * FROM events WHERE importance_n = 2
```

---

## 📋 REQUÊTES STANDARDS (COPIER-COLLER)

### **1. Charger événements pour une date (avec scores)**
```python
import duckdb
import pandas as pd

conn = duckdb.connect(db_path, read_only=True)

query = """
SELECT 
    e.ts_utc,
    e.country,
    e.event_title,
    e.event_key,
    e.actual,
    e.estimate,
    e.previous,
    f.empirical_score
FROM events e
LEFT JOIN event_families f 
    ON e.event_key = f.event_key 
    AND e.country = f.country
WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
  AND f.empirical_score > 40.0  -- Filtre "HIGH"
ORDER BY e.ts_utc
"""

df = conn.execute(query, ['2025-09-11']).df()
conn.close()
```

### **2. Charger prix 1-minute pour une date**
```python
query = """
SELECT datetime, open, high, low, close
FROM prices_bern
WHERE DATE(datetime) = ?
ORDER BY datetime
"""

df = conn.execute(query, ['2025-09-11']).df()

# Convertir timezone
df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert('Europe/Zurich')
df = df.set_index('datetime')
```

### **3. Vérifier événements disponibles pour une date**
```python
query = """
SELECT 
    e.ts_utc,
    e.country,
    e.event_title,
    f.empirical_score
FROM events e
LEFT JOIN event_families f 
    ON e.event_key = f.event_key 
    AND e.country = f.country
WHERE DATE(e.ts_utc AT TIME ZONE 'Europe/Zurich') = ?
ORDER BY f.empirical_score DESC NULLS LAST
LIMIT 10
"""

df = conn.execute(query, ['2025-09-11']).df()
print(df)
```

---

## 🎯 CRITÈRES "HIGH IMPORTANCE"

Puisqu'il n'y a **PAS de colonne importance = HIGH**, on utilise le **score empirique** :

**Seuils validés (Session 131) :**
- **HIGH** : `empirical_score > 40.0`
- **MEDIUM** : `15.0 < empirical_score <= 40.0`
- **LOW** : `empirical_score <= 15.0`

**Événements typiques HIGH (score > 40) :**
- 🇺🇸 Non-Farm Payrolls (NFP) : ~100 points
- 🇺🇸 CPI (Inflation) : ~80 points
- 🇺🇸 Fed Interest Rate Decision : ~70 points
- 🇪🇺 ECB Interest Rate Decision : ~60 points

---

## 📊 STATISTIQUES DB (14 nov 2025)

**Total événements :** 125,625  
**Période couverte :** 2020-01-01 → 2026-01-01 (6 ans)  
**Événements par jour (moyenne) :** ~57 événements/jour  
**Pays couverts :** 140+ pays  

**Distribution réelle importance_n :**
```
importance_n = 2 (MEDIUM) : 125,625 (100%)
```

**Événements avec scores empiriques :** ~228 types d'événements scorés (Session 127)

---

## ⚠️ MISE À JOUR OBLIGATOIRE

**Si structure DB change :**
1. Mettre à jour CE fichier immédiatement
2. Tester requêtes standards
3. Informer prochaine session

**Dernière validation :** 14 novembre 2025 - Session 135

---

**Auteur :** André Valentin avec Claude  
**Version :** 1.0  
**Session :** 135
