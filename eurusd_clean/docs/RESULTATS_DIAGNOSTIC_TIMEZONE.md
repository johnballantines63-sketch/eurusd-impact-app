# Résultats Diagnostic Timezone - Conclusions

**Date** : 2025-01-XX  
**Diagnostic exécuté** : ✅  
**Statut** : Conclusions importantes identifiées

---

## 🎯 CONCLUSIONS PRINCIPALES

### ✅ Bonne Nouvelle : DST est bien géré !

**Les timezones sont stockées correctement avec gestion automatique DST** :

1. **Événements** (`events.ts_utc`) :
   - ✅ Stockés en **Europe/Zurich** (timezone-aware)
   - ✅ DST automatique : UTC+2 (été) / UTC+1 (hiver)
   - Exemple été : `2025-09-11 14:30:00+02:00` (CEST)
   - Exemple hiver : `2025-01-15 14:30:00+01:00` (CET)

2. **Prix Finnhub** (`prices_finnhub_m1`) :
   - ✅ Stockés en **Europe/Zurich** (timezone-aware)
   - ✅ DST automatique : UTC+2 (été) / UTC+1 (hiver)
   - Exemple été : `2025-09-11 12:25:00+02:00`
   - Exemple hiver : `2025-01-15 13:25:00+01:00`

3. **Table Dukascopy** :
   - ❌ `prices_1m` n'existe plus (migration vers Finnhub effectuée)

---

## 🔍 PROBLÈME IDENTIFIÉ

### Problème de Correspondance

**Date été (11 sept 2025)** :
- Event CPI US : `14:30:00+02:00` (14:30 Bern = 12:30 UTC)
- Prix trouvés : `12:25:00+02:00`, `12:26:00+02:00`, `12:27:00+02:00`

**⚠️ PROBLÈME** :
- Le diagnostic cherchait à `12:30 UTC` (heure UTC de l'événement)
- Mais les prix sont stockés en **Bern time**
- La recherche ne trouve pas les prix à `14:30 Bern` car elle cherche en UTC

**Date hiver (15 jan 2025)** :
- Event CPI US : `14:30:00+01:00` (14:30 Bern = 13:30 UTC)
- Prix trouvés : `13:25:00+01:00`, `13:26:00+01:00`, `13:27:00+01:00`

**Même problème** : Recherche en UTC mais prix en Bern time.

---

## 📋 ANALYSE DÉTAILLÉE

### Correspondance Événements ↔ Prix

**Les deux sont stockés en Europe/Zurich** :
- ✅ **Même timezone** : Pas de conversion nécessaire si on utilise la timezone correcte
- ✅ **DST géré** : Les deux changent automatiquement (été/hiver)
- ⚠️ **Problème** : Les requêtes doivent utiliser la timezone Bern, pas UTC

### Exemple Concret

**11 septembre 2025 (ÉTÉ)** :
- Event : `14:30:00+02:00` (14:30 Bern CEST)
- Prix à chercher : `14:30:00+02:00` (même heure, même timezone)
- ✅ **Pas de conversion nécessaire si on utilise Bern time**

**15 janvier 2025 (HIVER)** :
- Event : `14:30:00+01:00` (14:30 Bern CET)
- Prix à chercher : `14:30:00+01:00` (même heure, même timezone)
- ✅ **Pas de conversion nécessaire si on utilise Bern time**

---

## ⚠️ PROBLÈMES DANS LE CODE ACTUEL

### Dans `run_pipeline_complete.py` (lignes 830-884)

**Code actuel** :
```python
# Event stocké en Bern time
anchor_time = ...  # 14:30:00+02:00 (Bern)

# Requête prix cherche en UTC
query = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE datetime >= '{event_datetime}'::TIMESTAMP - INTERVAL '5 minutes'
  AND datetime <= '{event_datetime}'::TIMESTAMP + INTERVAL '120 minutes'
"""
```

**Problème** :
- `event_datetime` est extrait de `anchor_time` (Bern time)
- Requête SQL peut interpréter en UTC
- Risque de décalage de 1-2h selon saison

### Solution : Utiliser la Timezone Correcte

**Option 1 : Requête directe en Bern time** :
```python
# Event déjà en Bern time
event_bern = anchor_time  # 14:30:00+02:00

# Requête prix en Bern time (même timezone)
query = f"""
SELECT datetime, open, high, low, close
FROM prices_finnhub_m1
WHERE datetime >= '{event_bern}'::TIMESTAMP WITH TIME ZONE - INTERVAL '5 minutes'
  AND datetime <= '{event_bern}'::TIMESTAMP WITH TIME ZONE + INTERVAL '120 minutes'
"""
```

**Option 2 : Fonction de conversion explicite** :
```python
def get_prices_at_event_time(event_ts_bern: datetime) -> pd.DataFrame:
    """
    Charge prix correspondant à un événement.
    Les deux sont en Bern time, donc pas de conversion nécessaire.
    """
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE datetime >= '{event_ts_bern}'::TIMESTAMP WITH TIME ZONE - INTERVAL '5 minutes'
      AND datetime <= '{event_ts_bern}'::TIMESTAMP WITH TIME ZONE + INTERVAL '120 minutes'
    ORDER BY datetime ASC
    """
    return conn.execute(query).df()
```

---

## ✅ RECOMMANDATIONS

### 1. Simplifier les Conversions

**Comme les événements et prix sont dans la même timezone** :
- ✅ Pas besoin de conversion UTC ↔ Bern
- ✅ Utiliser directement la timezone Bern
- ✅ DST géré automatiquement par DuckDB

### 2. Corriger le Pipeline

**Dans `run_pipeline_complete.py`** :
- Supprimer les conversions UTC complexes (lignes 850-866)
- Utiliser directement `anchor_time` (déjà en Bern time)
- Simplifier la requête prix

### 3. Fonction Standardisée

**Créer** : `src/core/price_loader_finnhub.py`

```python
def get_finnhub_prices_at_event_time(
    db_path: Path,
    event_timestamp_bern: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120
) -> pd.DataFrame:
    """
    Charge prix Finnhub correspondant à un événement.
    
    Les deux sont stockés en Europe/Zurich (Bern time),
    donc pas de conversion nécessaire.
    
    Args:
        event_timestamp_bern: Timestamp événement en Bern time
        lookback_minutes: Minutes avant
        lookahead_minutes: Minutes après
    
    Returns:
        DataFrame avec prix
    """
    # S'assurer que le timestamp a la timezone Bern
    if event_timestamp_bern.tzinfo is None:
        tz_bern = pytz.timezone('Europe/Zurich')
        event_timestamp_bern = tz_bern.localize(event_timestamp_bern)
    
    # Requête directe (même timezone)
    query = f"""
    SELECT datetime, open, high, low, close
    FROM prices_finnhub_m1
    WHERE datetime >= '{event_timestamp_bern}'::TIMESTAMP WITH TIME ZONE - INTERVAL '{lookback_minutes} minutes'
      AND datetime <= '{event_timestamp_bern}'::TIMESTAMP WITH TIME ZONE + INTERVAL '{lookahead_minutes} minutes'
    ORDER BY datetime ASC
    """
    
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        return conn.execute(query).df()
    finally:
        conn.close()
```

### 4. Adapter `measure_impact_from_dukascopy()`

**Renommer/Adapter** : `measure_impact_from_finnhub()`

```python
def measure_impact_from_finnhub(
    db_path: Path,
    event_timestamp_bern: datetime,
    lookback_minutes: int = 5,
    lookahead_minutes: int = 120
) -> Dict:
    """
    Mesure impact depuis prix Finnhub.
    
    Les événements et prix sont tous les deux en Bern time,
    donc logique simple : même heure, même timezone.
    """
    # Charger prix
    df_prices = get_finnhub_prices_at_event_time(
        db_path, event_timestamp_bern, lookback_minutes, lookahead_minutes
    )
    
    # Calcul impact (même logique que Dukascopy)
    # ...
```

---

## 📊 TABLEAU RÉCAPITULATIF

| Élément | Timezone Stockée | DST Géré | Conversion Nécessaire |
|---------|-----------------|----------|----------------------|
| **Events** (`events.ts_utc`) | Europe/Zurich | ✅ Oui | ❌ Non |
| **Prix Finnhub** (`prices_finnhub_m1`) | Europe/Zurich | ✅ Oui | ❌ Non |
| **Correspondance** | Même timezone | ✅ Oui | ✅ **Logique pure** : Event 14:30 = Prix 14:30 |

---

## 🎯 RÈGLE SIMPLIFIÉE

### Nouvelle Règle (Plus Simple que Dukascopy !)

> **Event et Prix sont tous les deux en Europe/Zurich (Bern time).**
> **Pas de conversion nécessaire : Event 14:30 = Prix 14:30**
> **DST géré automatiquement par DuckDB.**

**Avant (avec Dukascopy)** :
- Event 14:30 Bern → Chercher prix 12:30 UTC (via vue prices_bern)
- Conversion -2h nécessaire

**Maintenant (avec Finnhub)** :
- Event 14:30 Bern → Chercher prix 14:30 Bern
- **Aucune conversion nécessaire !** ✅

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ **Diagnostic terminé** - Timezones identifiées
2. ⏳ **Créer fonction standardisée** - `get_finnhub_prices_at_event_time()`
3. ⏳ **Adapter `measure_impact_from_dukascopy()`** - Version Finnhub
4. ⏳ **Simplifier pipeline** - Supprimer conversions UTC inutiles
5. ⏳ **Tester sur dates référence** - Valider corrections

---

## 📚 FICHIERS À MODIFIER

1. `scripts/run_pipeline_complete.py` :
   - Lignes 830-884 : Simplifier mesure d'impact
   - Supprimer conversions UTC complexes

2. `src/core/impact_measurement.py` :
   - Créer `measure_impact_from_finnhub()`
   - Adapter pour utiliser Bern time directement

3. Créer `src/core/price_loader_finnhub.py` :
   - Fonction standardisée pour charger prix

---

**Status** : ✅ DIAGNOSTIC TERMINÉ - Solutions identifiées - Prêt pour implémentation




