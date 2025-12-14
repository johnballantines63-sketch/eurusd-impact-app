# Architecture Complète avec Finnhub

## Vue d'Ensemble

Le projet utilise désormais **Finnhub** comme source unique pour :
- ✅ **Événements économiques** (Economic Calendar)
- ✅ **Prix forex** (Forex Candles - OHLC)
- ✅ **Détection de patterns** (Pattern Recognition)
- ✅ **Support/Résistance** (Support/Resistance Detection)
- ✅ **Indicateurs techniques** (Aggregate Indicators)

## Plan Finnhub

**Plan actif :** Market Data Forex (Premium)
- Accès à tous les endpoints forex
- 10 ans d'historique disponible
- Détection de patterns automatique
- Support/Résistance calculés
- Indicateurs techniques agrégés

## Structure de la Base de Données

### Tables Prix Finnhub

Toutes les tables de prix Finnhub sont préfixées par `prices_finnhub_` pour éviter les conflits avec Dukascopy :

```
prices_finnhub_m1    # Prix M1 (1 minute)
prices_finnhub_m5    # Prix M5 (5 minutes)
prices_finnhub_m15   # Prix M15 (15 minutes)
prices_finnhub_m30   # Prix M30 (30 minutes)
prices_finnhub_h1    # Prix H1 (1 heure)
prices_finnhub_d     # Prix Daily (1 jour)
prices_finnhub_w     # Prix Weekly (1 semaine)
prices_finnhub_m     # Prix Monthly (1 mois)
```

**Structure de chaque table :**
```sql
CREATE TABLE prices_finnhub_* (
    datetime TIMESTAMP WITH TIME ZONE PRIMARY KEY,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT
)
```

### Tables Événements

```
economic_events      # Événements économiques (Finnhub)
event_families       # Familles d'événements (scores empiriques)
```

### Tables Patterns

```
finnhub_patterns     # Patterns détectés par Finnhub
```

**Structure :**
```sql
CREATE TABLE finnhub_patterns (
    pattern_id VARCHAR PRIMARY KEY,
    symbol VARCHAR,
    resolution VARCHAR,
    pattern_name VARCHAR,        # Ex: "Double Bottom", "Head and Shoulders"
    pattern_type VARCHAR,        # "bullish" ou "bearish"
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    start_price DOUBLE,
    end_price DOUBLE,
    entry_price DOUBLE,
    stop_loss DOUBLE,
    profit1 DOUBLE,
    profit2 DOUBLE,
    status VARCHAR,              # "complete", "incomplete"
    mature INTEGER,
    raw_data VARCHAR            # JSON complet du pattern
)
```

## Scripts d'Import

### 1. Import Prix (`scripts/finnhub_import_prices.py`)

**Usage :**
```bash
# Importer tous les timeframes avec 10 ans d'historique
python3 scripts/finnhub_import_prices.py --all-timeframes

# Importer un timeframe spécifique
python3 scripts/finnhub_import_prices.py --resolution H1

# Import incrémental (depuis dernière date)
python3 scripts/finnhub_import_prices.py --resolution M1 --incremental

# Import période spécifique
python3 scripts/finnhub_import_prices.py --resolution H1 --from-date 2025-09-01 --to-date 2025-09-30
```

**Fonctionnalités :**
- ✅ Support de tous les timeframes (M1, M5, M15, M30, H1, D, W, M)
- ✅ Import OHLC complet (Open, High, Low, Close) + Volume
- ✅ 10 ans d'historique disponible
- ✅ Rate limiting automatique (30 calls/second)
- ✅ Division en chunks pour éviter les limites
- ✅ UPSERT (mise à jour si données existantes)
- ✅ Tables préfixées `prices_finnhub_*` pour éviter conflits

### 2. Import Événements (`scripts/finnhub_import.py`)

**Usage :**
```bash
# Import événements (déjà fonctionnel)
python3 scripts/finnhub_import.py
```

### 3. Détection Patterns (`scripts/finnhub_detect_patterns.py`)

**Usage :**
```bash
# Détecter patterns pour un timeframe
python3 scripts/finnhub_detect_patterns.py --resolution D

# Détecter pour tous les timeframes
python3 scripts/finnhub_detect_patterns.py --all-resolutions
```

**Patterns détectés :**
- Double Top/Bottom
- Triple Top/Bottom
- Head and Shoulders
- Triangle, Wedge, Channel, Flag
- Candlestick patterns

### 4. Monitoring (`scripts/monitor_finnhub_import.py`)

**Usage :**
```bash
# Surveiller la progression de l'import
python3 scripts/monitor_finnhub_import.py
```

## Migration depuis Dukascopy

### Stratégie de Migration

**Phase 1 : Import Finnhub (EN COURS)**
- ✅ Import de tous les timeframes avec 10 ans d'historique
- ✅ Tables séparées (`prices_finnhub_*` vs `prices_bern`, `prices_1m`, etc.)
- ✅ Pas de conflit, données en parallèle

**Phase 2 : Validation**
- Comparer données Finnhub vs Dukascopy sur période test
- Valider cohérence des prix
- Valider détection de tendances

**Phase 3 : Migration Complète**
- Mettre à jour `detect_trend_pre_event` pour utiliser `prices_finnhub_*`
- Mettre à jour `Planificateur_V3_CLEAN` pour utiliser Finnhub
- Supprimer tables Dukascopy une fois validation complète

**Phase 4 : Nettoyage**
- Supprimer tables Dukascopy obsolètes :
  - `prices_bern` (vue)
  - `prices_1m`
  - `prices_1h` (ancienne vue)
  - `prices_15m` (si existe)
  - Backups Dukascopy

### Tables à Supprimer (après validation)

```sql
-- Tables Dukascopy obsolètes
DROP TABLE IF EXISTS prices_1m;
DROP VIEW IF EXISTS prices_bern;
DROP VIEW IF EXISTS prices_1h;
DROP VIEW IF EXISTS prices_15m;
-- + tous les backups Dukascopy
```

## Intégration dans le Planificateur

### Détection de Tendance

Le module `trend_detection_pre_event.py` supporte maintenant :
- **Timeframe** : M1, M15, H1 (et bientôt tous)
- **Source** : Finnhub (`prices_finnhub_*`)
- **Méthodes** : right-anchored, structural-break, swing-based

**Exemple d'utilisation :**
```python
result = detect_trend_pre_event(
    DB_PATH,
    event_datetime,
    timeframe='H1',  # Utilise prices_finnhub_h1
    method='swing-based'
)
```

### Détection de Patterns

Les patterns Finnhub peuvent être utilisés pour :
- Valider les patterns détectés par notre algorithme
- Identifier les patterns récurrents
- Améliorer les prédictions

**Exemple d'utilisation :**
```python
# Charger patterns Finnhub pour une date
patterns = load_finnhub_patterns(date, resolution='D')
```

## Avantages de Finnhub

1. **Source Unique**
   - Prix + Événements depuis la même API
   - Cohérence garantie
   - Timezone unifiée

2. **Données Premium**
   - 10 ans d'historique (vs 3 ans Dukascopy)
   - Données intraday précises
   - Stream temps réel disponible

3. **Outils Intégrés**
   - Détection de patterns automatique
   - Support/Résistance calculés
   - Indicateurs techniques agrégés

4. **Maintenance Simplifiée**
   - Une seule clé API
   - Une seule documentation
   - Moins de scripts à maintenir

## Prochaines Étapes

1. ✅ Import historique complet (EN COURS)
2. ⏳ Validation données vs Dukascopy
3. ⏳ Intégration patterns dans Planificateur
4. ⏳ Migration complète vers Finnhub
5. ⏳ Suppression données Dukascopy

## Notes Importantes

- **Pas de redondance** : Tables préfixées différemment
- **Migration progressive** : Validation avant suppression Dukascopy
- **Backup recommandé** : Avant suppression des tables Dukascopy
- **Rate limiting** : Respecter 30 calls/second (géré automatiquement)


