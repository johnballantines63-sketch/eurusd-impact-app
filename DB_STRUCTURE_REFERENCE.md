# 📚 DOCUMENTATION STRUCTURE BASE DE DONNÉES - WAREHOUSE.DUCKDB

**Fichier de référence permanent**  
**Date de création :** 17 octobre 2025  
**Dernière mise à jour :** Session 7  
**Importance :** ⭐⭐⭐ CRITIQUE - À lire AVANT tout script d'analyse

---

## 🎯 OBJECTIF DE CE DOCUMENT

Ce document centralise **toutes les connaissances** sur la structure de la base de données pour :
- ✅ Éviter les erreurs récurrentes de conception de scripts
- ✅ Connaître les noms exacts des tables et colonnes
- ✅ Comprendre ce que contiennent réellement les données
- ✅ Savoir quelles jointures faire entre les tables

**⚠️ RÈGLE D'OR :** Avant d'écrire un script qui interroge la DB, **TOUJOURS consulter ce document** !

---

## 📁 LOCALISATION DE LA BASE DE DONNÉES

### Bases de données disponibles

```
fx_impact_app/data/
├── fx_news_impact.db          ❌ VIDE - Ne pas utiliser
├── eur_usd_events.db          ❌ CORROMPU - Ne pas utiliser
└── warehouse.duckdb           ✅ BASE PRINCIPALE - Utiliser celle-ci
```

**🔑 Chemin à utiliser dans les scripts :**
```python
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb', read_only=False)
```

---

## 📊 TABLES DISPONIBLES (19 tables)

### Tables principales

| Table | Lignes | Usage | Importance |
|-------|--------|-------|------------|
| **events** | 32,024 | Événements économiques avec dates/valeurs | ⭐⭐⭐ CRITIQUE |
| **event_families** | 241 | Métadonnées et scores par type d'événement | ⭐⭐⭐ CRITIQUE |
| **scores** | 991 | Scores alternatifs d'impact | ⭐⭐ Important |
| **prices_1m** | 1,130,233 | Prix minute par minute | ⭐⭐⭐ CRITIQUE |
| **prices_5m** | 226,329 | Prix 5 minutes | ⭐⭐ Important |
| **prices_1h** | 19,563 | Prix horaires | ⭐ Utile |

### Tables de vues (suffixe _v)

| Table | Description |
|-------|-------------|
| prices_1m_v | Vue simplifiée de prices_1m |
| prices_5m_v | Vue simplifiée de prices_5m |
| prices_1h_v | Vue simplifiée de prices_1h |
| price_v | Vue générique des prix |

**Note :** Les vues contiennent seulement `ts_utc` et `close`, sans OHLC complet.

---

## 🗂️ STRUCTURE DÉTAILLÉE DES TABLES

### 1. TABLE `events` - Événements économiques

**Nombre de lignes :** 32,024  
**Clé primaire :** Pas de clé unique définie  
**Usage :** Contient tous les événements économiques avec leurs valeurs réelles

#### Colonnes importantes

```sql
Column                Type                      Description
─────────────────────────────────────────────────────────────────────
ts_utc                TIMESTAMP WITH TIME ZONE  Date/heure UTC de l'événement
country               VARCHAR                    Code pays (US, GB, EU, etc.)
event_title           VARCHAR                    Nom de l'événement
event_key             VARCHAR                    Identifiant unique du type d'événement
importance_n          BIGINT                     Niveau d'importance (1-3)
actual                DOUBLE                     Valeur réelle publiée
previous              DOUBLE                     Valeur précédente
estimate              DOUBLE                     Estimation (parfois NULL)
forecast              DOUBLE                     Prévision consensus
unit                  VARCHAR                    Unité de mesure (%, K, B, etc.)
type                  VARCHAR                    Type de donnée
label                 VARCHAR                    Label alternatif
```

#### ⚠️ Pièges courants

1. **Type de timestamp :** `TIMESTAMP WITH TIME ZONE`, pas un simple TIMESTAMP
   ```python
   # ❌ FAUX - Cause une erreur de conversion
   CAST(ts_utc AS TIME)
   
   # ✅ CORRECT
   strftime(ts_utc, '%H:%M:%S')
   ```

2. **Pas d'impacts en pips :** Cette table ne contient PAS les impacts réels !
   - Elle contient seulement les valeurs économiques (actual, forecast)
   - Pour les impacts, il faut joindre avec `event_families`

3. **Forecast vs Estimate :** 
   - `forecast` : Consensus des analystes (à privilégier)
   - `estimate` : Parfois NULL, moins fiable

#### Exemple de requête correcte

```sql
SELECT 
    CAST(ts_utc AS DATE) as event_date,
    strftime(ts_utc, '%H:%M:%S') as event_time,  -- ✅ Pas CAST AS TIME
    event_title,
    event_key,
    country,
    actual,
    forecast,
    previous
FROM events
WHERE country = 'US'
    AND CAST(ts_utc AS DATE) = '2025-09-11'
ORDER BY ts_utc
```

---

### 2. TABLE `event_families` - Métadonnées par type d'événement

**Nombre de lignes :** 241  
**Clé primaire :** (event_key, country)  
**Usage :** Contient les statistiques historiques MOYENNES par type d'événement

#### Colonnes importantes

```sql
Column                Type      Description
───────────────────────────────────────────────────────────────────
event_key             VARCHAR   Identifiant unique (ex: "cpi", "nfp")
country               VARCHAR   Code pays
family                VARCHAR   Famille d'événement (ex: "CPI", "Employment")
empirical_score       DOUBLE    Score d'impact historique (0-100) ⭐
avg_movement_pips     DOUBLE    Impact moyen en pips ⭐
mfe_p80               DOUBLE    Percentile 80 du MFE
ttr_median            DOUBLE    Temps de retour médian (minutes)
analyzed_occurrences  INTEGER   Nombre d'occurrences analysées
impact_level          VARCHAR   HIGH, MEDIUM, LOW
is_tradable           BOOLEAN   Si tradable ou non
```

#### ⚠️ ATTENTION - Données MOYENNES, pas réelles !

**Point crucial :** Les valeurs comme `avg_movement_pips` sont des **MOYENNES HISTORIQUES** calculées sur des dizaines/centaines d'occurrences passées.

```python
# Ce que contient avg_movement_pips :
# CPI (US) → 27.3 pips = MOYENNE de tous les CPI US historiques

# Ce que ça ne contient PAS :
# L'impact réel du CPI du 11 septembre 2025 spécifiquement
```

**Conséquence :** Pour avoir l'impact RÉEL d'une date précise, il faut :
1. Récupérer les prix dans `prices_1m` autour de la date
2. Calculer le MFE/MAE manuellement
3. Ne pas se fier uniquement à `avg_movement_pips`

#### Exemple de jointure avec events

```sql
-- ✅ CORRECT - Jointure sur event_key
SELECT 
    e.ts_utc,
    e.event_title,
    e.country,
    ef.empirical_score,
    ef.avg_movement_pips,
    ef.impact_level
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country  -- ⚠️ Ne pas oublier le country !
WHERE ef.empirical_score IS NOT NULL
```

---

### 3. TABLE `prices_1m` - Prix minute par minute

**Nombre de lignes :** 1,130,233  
**Période couverte :** Septembre 2022 → Aujourd'hui  
**Usage :** Prix OHLCV minute par minute pour calculs d'impact

#### Colonnes

```sql
Column       Type                      Description
──────────────────────────────────────────────────────
datetime     TIMESTAMP WITH TIME ZONE  Date/heure avec timezone
timestamp    BIGINT                    Unix timestamp
gmtoffset    BIGINT                    Offset GMT (toujours 0)
open         DOUBLE                    Prix d'ouverture
high         DOUBLE                    Prix max de la minute
low          DOUBLE                    Prix min de la minute
close        DOUBLE                    Prix de clôture
volume       BIGINT                    Volume échangé
```

#### ⚠️ Pièges

1. **Timezone :** Les dates sont en `TIMESTAMP WITH TIME ZONE`
   - Toujours utiliser des comparaisons en UTC
   - Attention aux décalages horaires

2. **Données manquantes :** Certaines minutes peuvent manquer (weekend, faible liquidité)
   - Toujours vérifier que les données existent avant/après un événement

#### Exemple : Calculer l'impact d'un événement

```sql
-- Récupérer les prix 30 min avant → 120 min après un événement
WITH event_time AS (
    SELECT ts_utc 
    FROM events 
    WHERE event_key = 'cpi' 
        AND country = 'US' 
        AND CAST(ts_utc AS DATE) = '2025-09-11'
    LIMIT 1
)
SELECT 
    datetime,
    close,
    close - LAG(close) OVER (ORDER BY datetime) AS price_change
FROM prices_1m
WHERE datetime >= (SELECT ts_utc - INTERVAL '30 minutes' FROM event_time)
    AND datetime <= (SELECT ts_utc + INTERVAL '120 minutes' FROM event_time)
ORDER BY datetime
```

---

### 4. TABLE `scores` - Scores alternatifs

**Nombre de lignes :** 991  
**Usage :** Scores calculés différemment de event_families

#### Colonnes

```sql
Column                  Type    Description
─────────────────────────────────────────────────
event_key               VARCHAR Identifiant événement
impact_median_1h_pips   DOUBLE  Impact médian sur 1h
persistence_median_min  DOUBLE  Persistance médiane
score_impact_0_100      DOUBLE  Score d'impact 0-100
score_persist_0_100     DOUBLE  Score de persistance
```

**Note :** Rarement utilisée, event_families est plus complète.

---

## 🔗 JOINTURES RECOMMANDÉES

### Jointure type 1 : Events + Scores empiriques

```sql
-- Pour avoir les événements avec leurs scores
SELECT 
    e.ts_utc,
    e.event_title,
    e.country,
    ef.empirical_score,
    ef.avg_movement_pips
FROM events e
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
WHERE ef.empirical_score IS NOT NULL
```

### Jointure type 2 : Events + Prix pour calcul d'impact

```sql
-- Pour calculer l'impact réel d'un événement
WITH event_data AS (
    SELECT 
        e.ts_utc,
        e.event_key,
        e.country
    FROM events e
    WHERE CAST(e.ts_utc AS DATE) = '2025-09-11'
)
SELECT 
    ed.event_key,
    p.datetime,
    p.close
FROM event_data ed
JOIN prices_1m p 
    ON p.datetime BETWEEN ed.ts_utc - INTERVAL '30 minutes' 
                      AND ed.ts_utc + INTERVAL '120 minutes'
ORDER BY ed.event_key, p.datetime
```

---

## 🚨 ERREURS COURANTES ET SOLUTIONS

### Erreur 1 : Table introuvable

```python
# ❌ ERREUR
conn = duckdb.connect('fx_impact_app/data/fx_news_impact.db')
# → Table with name events does not exist!

# ✅ SOLUTION
conn = duckdb.connect('fx_impact_app/data/warehouse.duckdb')
```

### Erreur 2 : Conversion de TIMESTAMP WITH TIME ZONE

```sql
-- ❌ ERREUR
CAST(e.ts_utc AS TIME) as event_time
-- → Unimplemented type for cast (TIMESTAMP WITH TIME ZONE -> TIME)

-- ✅ SOLUTION
strftime(e.ts_utc, '%H:%M:%S') as event_time
```

### Erreur 3 : Valeurs NULL dans les agrégations

```python
# ❌ ERREUR
'event_name': lambda x: ' + '.join(sorted(set(x))[:3])
# → TypeError: sequence item 0: expected str instance, NoneType found

# ✅ SOLUTION
'event_name': lambda x: ' + '.join(sorted(set(str(v) for v in x if v is not None))[:3])
```

### Erreur 4 : Oublier la jointure sur country

```sql
-- ❌ ERREUR - Jointure incomplète
LEFT JOIN event_families ef ON e.event_key = ef.event_key
-- → Peut dupliquer les lignes si plusieurs pays

-- ✅ SOLUTION
LEFT JOIN event_families ef 
    ON e.event_key = ef.event_key 
    AND e.country = ef.country
```

### Erreur 5 : Supposer que avg_movement_pips = impact réel

```python
# ❌ ERREUR CONCEPTUELLE
# Utiliser avg_movement_pips comme si c'était l'impact du 11 sept 2025

# ✅ SOLUTION
# avg_movement_pips = MOYENNE historique
# Pour l'impact réel du 11 sept, calculer à partir de prices_1m
```

---

## 📐 FORMULES DÉCOUVERTES (Session 7)

### Impact d'un événement SEUL (régression linéaire)

```python
Impact = -2.84 + 0.352 × empirical_score
```

**Statistiques :**
- R² = 0.719 (72% de variance expliquée)
- Corrélation score/impact = 0.848
- Basé sur 289 événements seuls

**Exemples :**
- Score 70 → 21.8 pips
- Score 80 → 25.3 pips
- Score 90 → 28.8 pips

### Facteur de synergie (événements simultanés)

```python
synergy_factor = 1.05
```

**Signification :** Quand plusieurs événements arrivent simultanément, l'impact total ≈ impact de l'événement dominant × 1.05

Les événements multiples ne s'additionnent PAS, ils amplifient légèrement (+5%).

---

## 🎯 CHECKLIST AVANT D'ÉCRIRE UN SCRIPT

Avant d'écrire un script qui interroge la base de données :

- [ ] Je consulte ce document pour les noms exacts des tables
- [ ] Je vérifie le type des colonnes (TIMESTAMP WITH TIME ZONE !)
- [ ] J'utilise `warehouse.duckdb`, pas `fx_news_impact.db`
- [ ] Je gère les valeurs NULL dans les agrégations
- [ ] Je joins sur event_key ET country si nécessaire
- [ ] Je comprends que avg_movement_pips = moyenne historique, pas impact réel
- [ ] J'utilise strftime() pour extraire l'heure, pas CAST AS TIME

---

## 🔄 MISE À JOUR DE CE DOCUMENT

**Ce document doit être mis à jour quand :**
- ✅ Une nouvelle table est ajoutée
- ✅ Une nouvelle erreur courante est identifiée
- ✅ Une nouvelle formule est découverte
- ✅ La structure de la DB change

**Historique des mises à jour :**
- **Session 7 (17 oct 2025) :** Création initiale avec toutes les erreurs rencontrées

---

## 📚 DOCUMENTS CONNEXES

**À lire également :**
- `RAPPORT_SESSION6_FINAL.md` : Corrections des scores empiriques
- `SESSION7_INTRO.md` : État actuel du projet
- `analyze_impact_patterns_warehouse.py` : Script d'analyse des patterns

---

## 💡 PROCHAINE AMÉLIORATION RECOMMANDÉE

**Créer une table `event_impacts_calculated` :**

Actuellement, on n'a que des moyennes historiques. Il faudrait :
1. Calculer les impacts réels de chaque événement individuellement
2. Stocker dans une nouvelle table avec :
   - event_id, date, event_key, country
   - mfe_pips, mae_pips, ttr_minutes
   - direction (bullish/bearish)
   - surprise_index

Cette table permettrait d'avoir des données précises au lieu de moyennes.

---

**FIN DE LA DOCUMENTATION**

**Version :** 1.0  
**Date :** 17 octobre 2025  
**Tokens utilisés pour créer ce document :** Session 7
