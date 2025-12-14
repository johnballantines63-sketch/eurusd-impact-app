# 📋 RÉSUMÉ CARTOGRAPHIE IMPACT - POUR AUDIT/REFONTE

**Date** : 2025-01-XX  
**Destinataire** : Assistant chargé de l'audit et de la refonte de la prédiction  
**Objectif** : Fournir un résumé structuré des définitions d'impact et des incohérences identifiées

---

## 🎯 DÉFINITIONS ACTUELLES DE L'IMPACT

### 1. "Impact détecté" (Planificateur UI)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Fonction** : `detect_pattern_type()` (lignes 2114-2412)

**Formule** :
- **Baseline** : `low` (UP) ou `high` (DOWN) du **segment détecté** par `scan_price_movements()`
- **Pic** : `high.max()` (UP) ou `low.min()` (DOWN) du **même segment**
- **Calcul** : `impact_pips = (peak_price - baseline_price) * 10000` (UP) ou `(baseline_price - trough_price) * 10000` (DOWN)
- **Horizon** : Segment détecté (peut commencer avant l'événement)
- **Filtres** : `min_pips` (défaut 35.0 pips)

**Extrait clé** :
```python
# Lignes 1662-1692
if inv['type'] == 'TROUGH':  # Mouvement UP
    baseline_price = segment.iloc[0]['low']  # ⚠️ Baseline = low du segment détecté
    peak_price = segment['high'].max()
    impact_pips = (peak_price - baseline_price) * 10000
```

---

### 2. `phase1_pips` (table `event_impacts_v2`)

**Fichier** : `src/core/price_loader_finnhub.py`  
**Fonction** : `measure_impact_from_finnhub()` (lignes 96-292)

**Formule** :
- **Baseline** : `open` de la **première bougie M1 à l'événement ou après** (`prices_at_event.iloc[0]['open']`)
- **Pic** : `high.max()` (UP) ou `low.min()` (DOWN) dans une **fenêtre de 120 minutes après l'événement**
- **Calcul** : `impact_pips = max(peak_high, peak_low)` où :
  - `peak_high = (prices_after['high'] - start_price).max() * 10000`
  - `peak_low = (start_price - prices_after['low']).max() * 10000`
- **Horizon** : 120 minutes après l'événement (fixe)
- **Filtres** : Aucun

**Extrait clé** :
```python
# Lignes 203-205, 224-233
first_candle = prices_at_event.iloc[0]
start_price = first_candle['open']  # ⚠️ Baseline = open première bougie événement

prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
peak_high = prices_after['pips_high'].max()
if peak_high > peak_low:
    impact_pips = peak_high
```

---

### 3. `impact_median` / `impact_mean` (cache clusters)

**Fichier** : `scripts/catalog_all_clusters_from_db.py`  
**Fonction** : `catalog_all_clusters()` (lignes 262-422)

**Formule** :
- **Source** : Agrégation des `impact_pips` mesurés pour chaque occurrence d'un cluster
- **Calcul** : `impact_median = median(impacts)` où `impacts` vient de `measure_impact_for_cluster()`
- **Définition sous-jacente** : **Même que "Impact détecté"** (utilise `detect_pattern_type()`)

**Extrait clé** :
```python
# Lignes 166-259, 390-391
impact_pips = movement.get('impact_pips', 0)  # Vient de detect_pattern_type()
# ...
'impact_median': safe_median(pd.Series(impacts)),
'impact_mean': safe_mean(pd.Series(impacts)),
```

---

### 4. "Impact prédit" (Planificateur UI)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Fonctions** : `predict_single_wave_base()`, `predict_double_wave_base()`

**Formule** :
- **Single Wave** : `calculate_impact_linear(base_empirical_score, adjusted_empirical_score, surprise_avg, surprise_max, n_events)`
- **Double Wave** : Même formule linéaire + ratios (Phase 1: 58%, Pullback: 84%, Phase 2: 90%)
- **Baseline** : N/A (formule mathématique, pas basée sur prix)

---

## ⚠️ INCOHÉRENCES IDENTIFIÉES

### Incohérence 1 : Baseline différente

| Concept | Baseline | Conséquence |
|---------|----------|-------------|
| **Impact détecté** | `low`/`high` du segment détecté (peut être avant l'événement) | Baseline peut être différente de l'événement |
| **phase1_pips** | `open` première bougie événement (fixe à l'événement) | Baseline toujours à l'événement |

**Impact** : Pour le même événement, les deux mesures peuvent donner des valeurs très différentes.

**Exemple** :
- Événement à 14:30
- Mouvement détecté commence à 14:25 avec `low = 1.08500`
- `open` première bougie événement (14:30) = `1.08550`
- Impact détecté : baseline = 1.08500
- phase1_pips : baseline = 1.08550
- **Différence de 5 pips sur la baseline seule**

---

### Incohérence 2 : Table `event_impacts_v2` non écrite

**Problème** :
- La table `event_impacts_v2` est référencée dans le code (lecture dans `data_service.py`)
- **Aucun `CREATE TABLE event_impacts_v2` trouvé**
- **Aucun `INSERT INTO event_impacts_v2` trouvé**
- **Aucun `UPDATE event_impacts_v2` trouvé**

**Impact** : Impossible de savoir comment `phase1_pips` est réellement calculé et stocké dans la base de données.

**Hypothèses** :
- Script non versionné
- Processus ETL externe
- Migration de données manuelle

---

### Incohérence 3 : Cache vs DB

**Problème** :
- Le cache des clusters (`cache_clusters.csv`) utilise `impact_pips` de `detect_pattern_type()` (définition "Impact détecté")
- `event_impacts_v2` devrait utiliser `phase1_pips` de `measure_impact_from_finnhub()` (définition différente)

**Impact** : Les deux sources de données historiques peuvent donner des valeurs différentes pour le même cluster.

---

## 📁 FICHIERS CLÉS À MODIFIER

1. **`streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`**
   - `detect_pattern_type()` : Définit "Impact détecté" (lignes 2114-2412)
   - `predict_single_wave_base()` : Définit "Impact prédit" Single Wave (lignes 2649-2838)
   - `predict_double_wave_base()` : Définit "Impact prédit" Double Wave (lignes 2430-2620)

2. **`src/core/price_loader_finnhub.py`**
   - `measure_impact_from_finnhub()` : Définit `phase1_pips` (lignes 96-292)

3. **`scripts/catalog_all_clusters_from_db.py`**
   - `measure_impact_for_cluster()` : Utilise `detect_pattern_type()` pour calculer `impact_median` (lignes 166-259)
   - `catalog_all_clusters()` : Agrège les impacts en `impact_median`/`impact_mean` (lignes 262-422)

4. **`src/core/cluster_impact_calculator.py`**
   - `calculate_cluster_impact()` : Calcule impact prédit pour un cluster (lignes 50-229)

5. **`scripts/run_pipeline_complete.py`**
   - Appelle `measure_impact_from_finnhub()` pour mesurer impact réel (ligne 1344)

---

## 🔧 RECOMMANDATIONS POUR REFONTE

### 1. Unifier la définition de l'impact

**Proposition** : Créer une fonction unique avec paramètres configurables :

```python
def calculate_impact_unified(
    df_prices: pd.DataFrame,
    event_timestamp: pd.Timestamp,
    baseline_method: str = 'event_open',  # 'event_open', 'segment_low', 'segment_high', 'custom'
    horizon_minutes: int = 120,
    min_pips: Optional[float] = None,
    custom_baseline_price: Optional[float] = None
) -> Dict:
    """
    Calcule l'impact de manière unifiée.
    
    Args:
        baseline_method: 
            - 'event_open': open première bougie événement (comme phase1_pips)
            - 'segment_low': low segment détecté (comme impact détecté UP)
            - 'segment_high': high segment détecté (comme impact détecté DOWN)
            - 'custom': utiliser custom_baseline_price
        horizon_minutes: Fenêtre après événement
        min_pips: Seuil minimum (None = pas de filtre)
    """
    pass
```

**Avantages** :
- Une seule fonction à maintenir
- Paramètres explicites pour chaque cas d'usage
- Conversion facile entre définitions

---

### 2. Créer/écrire `event_impacts_v2` de manière explicite

**Proposition** : Créer un script dédié `scripts/populate_event_impacts_v2.py` qui :
1. Crée la table `event_impacts_v2` si elle n'existe pas
2. Calcule `phase1_pips` pour chaque événement historique avec `measure_impact_from_finnhub()`
3. Insère/mets à jour les données dans la table avec `INSERT ... ON CONFLICT UPDATE`

**Schéma proposé** :
```sql
CREATE TABLE IF NOT EXISTS event_impacts_v2 (
    ts_utc              TIMESTAMP WITH TIME ZONE,
    event_key           VARCHAR,
    event_title         VARCHAR,
    country             VARCHAR,
    actual              DOUBLE,
    forecast            DOUBLE,
    previous            DOUBLE,
    surprise_pct        DOUBLE,
    importance          BIGINT,
    phase1_pips         DOUBLE,  -- Impact réel mesuré (baseline = event_open)
    ttr_minutes         INTEGER,
    direction           VARCHAR,
    start_price         DOUBLE,
    ttr_price           DOUBLE,
    source              VARCHAR DEFAULT 'measure_impact_from_finnhub',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ts_utc, event_key, country)
);
```

---

### 3. Documenter les différences et conversions

**Proposition** : Ajouter des commentaires explicites dans le code :

```python
# ⚠️ DÉFINITION IMPACT : "Impact détecté"
# Baseline: low/high du segment détecté (peut être avant événement)
# Horizon: Segment détecté par scan_price_movements()
# Usage: Affichage UI Planificateur, cache clusters
impact_pips = (peak_price - baseline_price) * 10000

# ⚠️ DÉFINITION IMPACT : phase1_pips
# Baseline: open première bougie événement (fixe à l'événement)
# Horizon: 120 minutes après événement (fixe)
# Usage: Table event_impacts_v2, historique événements individuels
phase1_pips = measure_impact_from_finnhub(...)['impact_pips']
```

---

## 📊 TABLEAU COMPARATIF

| Aspect | Impact détecté | phase1_pips | impact_median | Impact prédit |
|--------|----------------|-------------|---------------|---------------|
| **Baseline** | Segment détecté | Event open | Segment détecté | N/A (formule) |
| **Horizon** | Segment détecté | 120 min fixe | Segment détecté | N/A (formule) |
| **Filtres** | min_pips (35.0) | Aucun | min_pips (35.0) | N/A |
| **Usage** | UI Planificateur | DB historique | Cache clusters | UI Planificateur |
| **Fonction** | `detect_pattern_type()` | `measure_impact_from_finnhub()` | `detect_pattern_type()` | `predict_*_base()` |

---

## 🎯 QUESTIONS À RÉSOUDRE

1. **Quelle définition d'impact doit être utilisée comme référence ?**
   - Option A : `phase1_pips` (baseline fixe à l'événement)
   - Option B : "Impact détecté" (baseline du segment détecté)
   - Option C : Nouvelle définition unifiée

2. **Comment alimenter `event_impacts_v2` ?**
   - Créer un script dédié ?
   - Intégrer dans le pipeline existant ?
   - Migrer depuis une source externe ?

3. **Comment gérer la conversion entre définitions ?**
   - Fonction de conversion explicite ?
   - Normalisation à l'entrée ?
   - Garder les deux définitions avec documentation claire ?

---

## 📝 EXTRACTS DE CODE COMPLETS

### Extract 1 : Calcul "Impact détecté"

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Lignes** : 1655-1692

```python
if inv['type'] == 'TROUGH':  # Mouvement UP
    baseline_price = segment.iloc[0]['low']
    peak_price = segment['high'].max()
    peak_idx = segment['high'].idxmax()
    impact_pips = (peak_price - baseline_price) * 10000
    direction = 'UP'
    
    # Trouver le vrai début : remonter AVANT le segment
    start_time = segment.iloc[0]['datetime']
    start_idx_in_prices = start_idx
    
    search_back_minutes = 30
    search_back_start = max(0, start_idx - search_back_minutes)
    
    for j in range(start_idx - 1, search_back_start - 1, -1):
        if j < 0 or j >= len(prices):
            break
        check_row = prices.iloc[j]
        check_impact = (check_row['high'] - baseline_price) * 10000
        if check_impact >= 5.0:  # seuil pour trouver le début progressif
            start_time = check_row['datetime']
            start_idx_in_prices = j
        else:
            break
    
    peak_time = segment.loc[peak_idx, 'datetime']
else:  # PEAK - Mouvement DOWN
    baseline_price = segment.iloc[0]['high']
    trough_price = segment['low'].min()
    trough_idx = segment['low'].idxmin()
    impact_pips = (baseline_price - trough_price) * 10000
    direction = 'DOWN'
```

---

### Extract 2 : Calcul `phase1_pips`

**Fichier** : `src/core/price_loader_finnhub.py`  
**Lignes** : 196-243

```python
# Trouver prix à l'événement
prices_at_event = df_prices[df_prices['datetime'] >= event_ts_pd].copy()
prices_before_event = df_prices[df_prices['datetime'] < event_ts_pd].copy()

# PRIX RÉFÉRENCE = OPEN PREMIÈRE BOUGIE ÉVÉNEMENT
if not prices_at_event.empty:
    first_candle = prices_at_event.iloc[0]
    start_price = first_candle['open']  # ✅ Méthode Session 100/106 validée
    baseline_time = first_candle['datetime']
elif not prices_before_event.empty:
    # Fallback : utiliser CLOSE dernière bougie avant événement
    last_candle_before = prices_before_event.iloc[-1]
    start_price = last_candle_before['close']
    baseline_time = last_candle_before['datetime']
else:
    return None

# CALCUL IMPACT BIDIRECTIONNEL
prices_after = prices_at_event.copy()
prices_after['pips_high'] = (prices_after['high'] - start_price) * 10000
prices_after['pips_low'] = (start_price - prices_after['low']) * 10000

peak_high = prices_after['pips_high'].max()
peak_low = prices_after['pips_low'].max()

if peak_high > peak_low:
    impact_pips = peak_high
    direction = 1  # UP
    peak_idx = prices_after['pips_high'].idxmax()
    peak_price = prices_after.loc[peak_idx, 'high']
    peak_time = prices_after.loc[peak_idx, 'datetime']
else:
    impact_pips = peak_low
    direction = -1  # DOWN
    peak_idx = prices_after['pips_low'].idxmax()
    peak_price = prices_after.loc[peak_idx, 'low']
    peak_time = prices_after.loc[peak_idx, 'datetime']
```

---

### Extract 3 : Calcul `impact_median` (cache)

**Fichier** : `scripts/catalog_all_clusters_from_db.py`  
**Lignes** : 166-259, 385-400

```python
def measure_impact_for_cluster(
    date: datetime,
    cluster: Dict,
    conn,
    timezone_str: str = TIMEZONE_BERN,
    min_pips: float = MIN_IMPACT_PIPS
) -> Optional[Dict]:
    """
    Mesure l'impact réel d'un cluster en analysant les prix
    """
    # Charger les prix pour cette date
    df_prices = conn.execute(query_prices, [date.strftime('%Y-%m-%d')]).df()
    
    # Enrichir les événements
    df_events_enriched = enrich_events_with_surprises(df_events)
    
    # Détecter le pattern
    pattern_result = detect_pattern_type(
        df_prices,
        df_events_enriched,
        min_pips=min_pips,
        timezone=timezone_str,
        cluster_anchor_time=anchor_time
    )
    
    movement = pattern_result.get('movement')
    impact_pips = movement.get('impact_pips', 0)  # ⚠️ Utilise detect_pattern_type()
    
    return {
        'impact_pips': impact_pips,
        # ...
    }

# Dans catalog_all_clusters()
if impacts:
    catalogued_clusters.append({
        'cluster_signature': signature,
        'impact_median': safe_median(pd.Series(impacts)),  # ⚠️ Médiane des impacts détectés
        'impact_mean': safe_mean(pd.Series(impacts)),
        # ...
    })
```

---

## ✅ CHECKLIST POUR REFONTE

- [ ] Unifier la définition de l'impact avec une fonction commune
- [ ] Créer/écrire `event_impacts_v2` de manière explicite
- [ ] Documenter les différences entre définitions
- [ ] Ajouter des fonctions de conversion entre définitions
- [ ] Mettre à jour le cache des clusters pour utiliser la définition unifiée
- [ ] Mettre à jour l'UI pour afficher la définition utilisée
- [ ] Valider la cohérence entre cache et DB

---

**Fin du résumé**
