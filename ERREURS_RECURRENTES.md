# 🚨 ERREURS RÉCURRENTES - À LIRE EN PREMIER !

**Ce document liste les erreurs que Claude répète de session en session.**  
**OBLIGATOIRE : Consulter AVANT d'écrire un script SQL !**

---

## ❌ ERREUR #1 : Colonne `event_name` N'EXISTE PAS

### ⚠️ CE QUI EST FAUX

```sql
-- ❌ FAUX - event_families n'a PAS de colonne event_name
SELECT ef.event_name 
FROM event_families ef
```

### ✅ CE QUI EST CORRECT

La table `event_families` contient **SEULEMENT** :
- `event_key` (ex: "cpi", "nfp", "gdp")
- `country` (ex: "US", "EU", "GB")
- `family` (ex: "Inflation", "Employment")
- `empirical_score`, `avg_movement_pips`, etc.

**Il n'y a PAS de colonne descriptive avec le nom complet de l'événement.**

Pour avoir le nom complet, il faut :
1. Utiliser `e.event_title` depuis la table `events`
2. Ou utiliser `ef.event_key` (identifiant court)
3. Ou utiliser `ef.family` (catégorie)

```sql
-- ✅ CORRECT - Utiliser event_title depuis events
SELECT 
    e.event_title,        -- ✅ Depuis events
    ef.event_key,         -- ✅ Depuis event_families
    ef.family,            -- ✅ Depuis event_families
    ef.empirical_score
FROM events e
INNER JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

**FRÉQUENCE :** ⭐⭐⭐ TRÈS FRÉQUENT (répété Sessions 7, 9, 11, 15, 17, 18)

---

## ❌ ERREUR #2 : Conversion TIMESTAMP incorrecte

### ⚠️ CE QUI EST FAUX

```sql
-- ❌ FAUX - Type incompatible
CAST(ts_utc AS TIME)
CAST(ts_utc AS VARCHAR)
```

### ✅ CE QUI EST CORRECT

```sql
-- ✅ CORRECT - Utiliser strftime()
strftime(ts_utc, '%H:%M:%S')          -- Heure
strftime(ts_utc, '%Y-%m-%d')          -- Date
strftime(ts_utc, '%Y-%m-%d %H:%M:00') -- DateTime arrondi à la minute
CAST(ts_utc AS DATE)                  -- Date seulement
```

**FRÉQUENCE :** ⭐⭐⭐ TRÈS FRÉQUENT

---

## ❌ ERREUR #3 : Oublier `country` dans la jointure

### ⚠️ CE QUI EST FAUX

```sql
-- ❌ INCOMPLET - Peut joindre US CPI avec EU CPI !
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key
```

### ✅ CE QUI EST CORRECT

```sql
-- ✅ CORRECT - Toujours joindre sur event_key ET country
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

**FRÉQUENCE :** ⭐⭐ FRÉQUENT

---

## ❌ ERREUR #4 : Confondre `forecast` et `estimate`

### ⚠️ CE QUI EST FAUX

```sql
-- ❌ FAUX - forecast est presque toujours NULL
CASE WHEN e.forecast IS NOT NULL THEN ...
```

### ✅ CE QUI EST CORRECT

```sql
-- ✅ CORRECT - Utiliser estimate, pas forecast
CASE WHEN e.estimate IS NOT NULL AND e.estimate != 0 
    THEN ABS((e.actual - e.estimate) / e.estimate)
```

**Données réelles :**
- `forecast` : 11 valeurs sur 32,024 (0.03%) ❌
- `estimate` : 13,089 valeurs sur 32,024 (41%) ✅

**FRÉQUENCE :** ⭐⭐⭐ TRÈS FRÉQUENT (Session 7)

---

## ❌ ERREUR #5 : Supposer que `avg_movement_pips` = impact réel

### ⚠️ CE QUI EST FAUX

```python
# ❌ FAUX - avg_movement_pips est une MOYENNE historique
impact_reel_11_sept = event_families['avg_movement_pips']
```

### ✅ CE QUI EST CORRECT

`avg_movement_pips` = **MOYENNE** de tous les impacts historiques du type d'événement.

Pour avoir l'impact RÉEL d'une date spécifique :
1. Utiliser table `event_group_impacts` (si calculé)
2. Ou calculer manuellement depuis `prices_1m`

```python
# ✅ CORRECT
SELECT mfe_pips 
FROM event_group_impacts
WHERE time_group = '2025-09-11 14:30:00'
```

**FRÉQUENCE :** ⭐⭐ FRÉQUENT (Session 7)

---

## ❌ ERREUR #6 : NULL dans agrégations de texte

### ⚠️ CE QUI EST FAUX

```python
# ❌ FAUX - Crash si une valeur est NULL
lambda x: ' + '.join(sorted(set(x)))
```

### ✅ CE QUI EST CORRECT

```python
# ✅ CORRECT - Filtrer les NULL
lambda x: ' + '.join(sorted(set(str(v) for v in x if v is not None)))
```

**FRÉQUENCE :** ⭐⭐ FRÉQUENT (Session 7)

---

## ❌ ERREUR #7 : Utiliser mauvaise base de données

### ⚠️ CE QUI EST FAUX

```python
# ❌ FAUX - Bases vides ou corrompues
conn = duckdb.connect('fx_impact_app/data/fx_news_impact.db')
conn = duckdb.connect('fx_impact_app/data/eur_usd_events.db')
```

### ✅ CE QUI EST CORRECT

```python
# ✅ CORRECT - Toujours warehouse.duckdb
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
```

**FRÉQUENCE :** ⭐⭐⭐ TRÈS FRÉQUENT (Session 7)

---

## ❌ ERREUR #8 : Fenêtre temporelle trop large

### ⚠️ CE QUI EST FAUX

```python
# ❌ FAUX - 120 minutes capte mouvements non liés
window = 120 minutes
```

### ✅ CE QUI EST CORRECT

```python
# ✅ CORRECT - 60 minutes est optimal
window = 60 minutes
```

**Impact observé :**
- Max aberrant : 3,703 → 1,056 pips
- Corrélation : 0.108 → 0.292

**FRÉQUENCE :** ⭐ (Session 7)

---

## ❌ ERREUR #9 : Calculer impacts individuellement au lieu de par groupe

### ⚠️ CE QUI EST FAUX

```python
# ❌ FAUX - Calculer impact pour chaque événement séparément
for event in events_at_1430:
    impact = calculate_mfe(event)  # Même MFE dupliqué 33 fois !
```

### ✅ CE QUI EST CORRECT

```python
# ✅ CORRECT - Grouper par minute PUIS calculer UN impact par groupe
events_df['time_group'] = events_df['ts_utc'].dt.floor('1min')
grouped = events_df.groupby('time_group')

for time_group, group_events in grouped:
    impact = calculate_group_impact(time_group)  # UN seul impact
```

**Impact :**
- Ancien : 4,801 lignes dupliquées
- Nouveau : 2,089 groupes uniques
- R² : 0.719 (biaisé) → 0.264 (correct)

**FRÉQUENCE :** ⭐⭐⭐ TRÈS CRITIQUE (Sessions 8-9)

---

## 📋 CHECKLIST AVANT D'ÉCRIRE UN SCRIPT SQL

Avant d'écrire un script qui interroge la DB, vérifie :

- [ ] ✅ J'utilise `warehouse.duckdb` (pas les autres)
- [ ] ✅ Je n'utilise PAS `ef.event_name` (n'existe pas)
- [ ] ✅ J'utilise `strftime()` pour les timestamps (pas CAST AS TIME)
- [ ] ✅ Je joins sur `event_key` ET `country` (pas juste event_key)
- [ ] ✅ J'utilise `estimate` (pas forecast)
- [ ] ✅ Je filtre les NULL dans les agrégations de texte
- [ ] ✅ Je groupe par minute pour multi-événements
- [ ] ✅ Je n'utilise `avg_movement_pips` que pour référence, pas impact réel

---

## 🎯 COMMENT UTILISER CE DOCUMENT

**Pour Claude :**
1. Lire ce fichier EN PREMIER avant toute requête SQL
2. Vérifier chaque erreur listée
3. Appliquer les bonnes pratiques

**Pour André :**
1. Ajouter toute nouvelle erreur répétée
2. Marquer la fréquence (⭐⭐⭐ si répété 3+ fois)
3. Documenter la session où l'erreur a été corrigée

---

**Version :** 1.0  
**Date création :** 19 octobre 2025 - Session 18  
**Dernière mise à jour :** Session 18  
**Importance :** ⭐⭐⭐ CRITIQUE - LIRE EN PREMIER !
