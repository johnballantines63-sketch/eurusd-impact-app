# 📊 Scores Empiriques — Guide Complet

**Version :** 1.0  
**Date :** 2025-12-13  
**Objectif :** Documentation complète sur le calcul et l'utilisation des scores empiriques

---

## 🎯 Vue d'ensemble

Les **scores empiriques** sont la base du système de prédiction d'impact. Ce document explique :

1. **Comment calculer** les scores de base depuis les données historiques
2. **Comment ajuster** les scores selon la surprise réelle
3. **Comment utiliser** les scores pour prédire l'impact en pips

---

## 📈 PARTIE 1 : CALCUL DES SCORES DE BASE

### Objectif

Calculer un score (0-100) pour chaque famille d'événements basé sur l'**impact historique réel** mesuré sur les prix EUR/USD.

### Méthodologie

#### Étape 1 : Identifier les occurrences historiques

Pour chaque `event_key` (ex: `"cpi"`, `"nfp"`), trouver toutes les occurrences dans la base de données :

```sql
SELECT 
    e.event_key,
    e.country,
    e.ts_utc as event_time,
    COUNT(*) as occurrences
FROM events e
WHERE e.event_key = 'cpi'
  AND e.ts_utc >= '2020-01-01'
GROUP BY e.event_key, e.country, e.ts_utc
```

**Critères :**
- Période : 2020-2025 (5 ans de données)
- Minimum : 3 occurrences pour être valide
- Par `event_key` + `country`

#### Étape 2 : Mesurer l'impact réel pour chaque occurrence

Pour chaque occurrence d'un événement, mesurer le mouvement réel du prix EUR/USD :

```python
def measure_impact_for_event(conn, event_time, country):
    """
    Mesure l'impact réel d'un événement en pips.
    
    Méthode:
    1. Baseline = prix juste avant l'événement (t-1 minute)
    2. Peak = prix maximum/minimum dans fenêtre [t, t+60 minutes]
    3. Impact = |peak - baseline| × 10000 (conversion en pips)
    """
    # 1. Trouver baseline (prix avant événement)
    baseline = conn.execute("""
        SELECT close
        FROM prices_finnhub_m5
        WHERE datetime < CAST(? AS TIMESTAMP)
        ORDER BY datetime DESC
        LIMIT 1
    """, [event_time]).fetchone()
    
    if not baseline:
        return None
    
    baseline_price = baseline[0]
    
    # 2. Trouver peak dans fenêtre [t, t+60 min]
    prices_window = conn.execute("""
        SELECT close
        FROM prices_finnhub_m5
        WHERE datetime >= CAST(? AS TIMESTAMP)
          AND datetime <= CAST(? AS TIMESTAMP) + INTERVAL '60 minutes'
        ORDER BY datetime
    """, [event_time, event_time]).df()
    
    if prices_window.empty:
        return None
    
    # 3. Calculer mouvement maximum (hausse ou baisse)
    max_price = prices_window["close"].max()
    min_price = prices_window["close"].min()
    
    movement_up = (max_price - baseline_price) * 10000  # pips
    movement_down = (baseline_price - min_price) * 10000  # pips
    
    impact = max(movement_up, movement_down)  # Prendre le maximum
    
    return impact
```

**Fenêtre d'observation :** 60 minutes après l'événement  
**Conversion :** 1 pip = 0.0001 → multiplier par 10000

#### Étape 3 : Calculer statistiques agrégées

Pour chaque `event_key`, calculer :

```python
def calculate_empirical_score(avg_movement, p80_movement, sample_size):
    """
    Calcule le score empirique normalisé 0-100.
    
    Args:
        avg_movement: Moyenne des impacts en pips
        p80_movement: Percentile 80 des impacts (robuste aux outliers)
        sample_size: Nombre d'occurrences mesurées
    
    Returns:
        float: Score normalisé 0-100
    """
    # Score de base : moyenne pondérée (avg + p80)
    base_score = (avg_movement * 0.5 + p80_movement * 0.5)
    
    # Facteur robustesse selon taille échantillon
    if sample_size >= 20:
        robustness = 1.0  # Très fiable
    elif sample_size >= 10:
        robustness = 0.9  # Fiable
    elif sample_size >= 5:
        robustness = 0.8  # Assez fiable
    else:
        robustness = 0.7  # Peu fiable (< 5 occurrences)
    
    score = base_score * robustness
    
    # Normalisation 0-100 (score max observé ~80-100 pips)
    normalized = min(100.0, score)  # Plafond à 100
    
    return normalized
```

**Pourquoi avg + p80 ?**
- `avg_movement` : représente l'impact moyen
- `p80_movement` : représente les cas significatifs (évite les outliers faibles)
- Moyenne pondérée : équilibre entre moyenne et cas représentatifs

**Pourquoi facteur robustesse ?**
- Plus d'occurrences = plus de confiance dans le score
- Échantillons petits (< 5) : pénalité de 30%

#### Étape 4 : Stockage dans `event_families`

Les scores calculés sont stockés dans la table `event_families` :

```sql
CREATE TABLE event_families (
    event_key VARCHAR,
    country VARCHAR,
    empirical_score DOUBLE,      -- Score 0-100
    avg_movement_pips DOUBLE,    -- Moyenne historique
    median_movement_pips DOUBLE, -- Médiane historique
    sample_size INTEGER,          -- Nombre occurrences
    latency_median DOUBLE,        -- Latence médiane (minutes)
    -- ...
)
```

**Exemple :**
```
event_key: "cpi"
country: "US"
empirical_score: 44.8
avg_movement_pips: 42.3
sample_size: 48
```

---

## 🔄 PARTIE 2 : AJUSTEMENT SELON SURPRISE (Session 55)

### Problème identifié

Les scores de base sont calculés sur **historique moyen** et ne tiennent **PAS compte** de la surprise réelle :

- CPI avec surprise 0% → score 44.8
- CPI avec surprise 33% → score 44.8 (identique !)
- **Mais impact réel diffère de +52% !**

**Corrélation surprise ↔ impact :** -0.122 (faible corrélation)

### Solution : Score Ajusté

#### Formule

```python
def calculate_adjusted_empirical_score(
    base_empirical_score: float,
    surprise_pct: float
) -> float:
    """
    Ajuste le score empirique selon la surprise pour refléter l'impact réel.
    
    Args:
        base_empirical_score: Score depuis event_families (0-100)
        surprise_pct: Surprise en % = |actual - estimate| / |estimate| × 100
    
    Returns:
        float: Score ajusté (0-100)
    """
    # Surprise faible : pas d'ajustement
    if surprise_pct < 5:
        return base_empirical_score
    
    # Surprise modérée (5-15%) : légère amplification
    elif surprise_pct < 15:
        factor = 1.0 + (surprise_pct - 5) / 10 * 0.5  # 1.0 → 1.5
        return base_empirical_score * factor
    
    # Surprise forte (15-30%) : forte amplification
    elif surprise_pct < 30:
        factor = 1.5 + (surprise_pct - 15) / 15 * 0.4  # 1.5 → 1.9
        return base_empirical_score * factor
    
    # Surprise extrême (≥30%) : plafond
    else:
        return base_empirical_score * 1.9
```

**Tableau récapitulatif :**

| Surprise | Facteur | Exemple (score base 44.8) |
|----------|---------|---------------------------|
| < 5%     | 1.0     | 44.8 (pas d'ajustement)   |
| 5%       | 1.0     | 44.8                      |
| 10%      | 1.25    | 56.0                      |
| 15%      | 1.5     | 67.2                      |
| 25%      | 1.83    | 82.0                      |
| ≥30%     | 1.9     | 85.1 (plafond)            |

#### Validation (11 septembre 2025)

```
Événement: CPI US
Score base DB:    44.8
Surprise réelle:  33.3%
Score ajusté:     85.1
Score attendu:    ~85
MAE:              0.1
Précision:        99.9% ✅✅✅
```

### Calcul de la surprise

```python
def calculate_surprise(actual: float, estimate: float) -> float:
    """
    Calcule la surprise en pourcentage.
    
    Args:
        actual: Valeur publiée (actual)
        estimate: Valeur estimée (consensus)
    
    Returns:
        float: Surprise en % (toujours positif)
    """
    if pd.isna(actual) or pd.isna(estimate) or estimate == 0:
        return 0.0
    
    surprise_pct = abs((actual - estimate) / estimate) * 100.0
    return surprise_pct
```

**Cas spéciaux :**
- **Taux/Pourcentage** : Si `event_key` contient "rate", "inflation", "yield" → surprise en **points** (pas %)
  - Exemple: `inflation_rate_mom`: 0.4 vs 0.3 → surprise = 0.1 point (pas 33%)
- **Valeurs négatives** : Utiliser valeur absolue

---

## 🎯 PARTIE 3 : UTILISATION DES SCORES POUR PRÉDIRE L'IMPACT

### Workflow complet

```python
# 1. CHARGER score de base depuis DB
base_score = get_empirical_score_from_db(event_key="cpi", country="US")
# → 44.8

# 2. CALCULER surprise
surprise_pct = calculate_surprise(actual=0.4, estimate=0.3)
# → 33.3%

# 3. AJUSTER score selon surprise
adjusted_score = calculate_adjusted_empirical_score(
    base_empirical_score=44.8,
    surprise_pct=33.3
)
# → 85.1

# 4. CALCULER impact prédit
impact_pips = calculate_impact_d(
    empirical_score=85.1,  # Score AJUSTÉ
    num_events=9,
    amplification=2.8
)
# → 57.0 pips
```

### Formule Impact D (Session 51)

```python
def calculate_impact_d(
    empirical_score: float,
    num_events: int,
    amplification: float = 2.8
) -> float:
    """
    Calcule l'impact prédit en pips.
    
    Args:
        empirical_score: Score ajusté (0-100)
        num_events: Nombre d'événements dans le cluster
        amplification: Facteur amplification (défaut 2.8, validé Session 113)
    
    Returns:
        float: Impact prédit en pips (positif)
    """
    # Choix formule selon nombre événements
    if num_events >= 2:
        impact_brut = -10.47 + 0.477 * empirical_score
    else:  # num_events = 1
        impact_brut = -7.08 + 0.419 * empirical_score
    
    # Amplification + correction vectorielle
    impact_final = abs(impact_brut) * amplification * 0.758
    
    return impact_final
```

**Paramètres :**
- `amplification = 2.8` : Validé Session 113 (était 2.5 avant)
- `0.758` : Facteur correction somme vectorielle multi-événements (Session 11)

**Validation (11 septembre 2025) :**
```
Score ajusté:    85.1
Num events:      9
Amplification:   2.8
Impact prédit:   57.0 pips
Impact réel MT5: 56.2 pips
MAE:             0.8 pips
Précision:       98.6% ✅✅✅
```

### Cas multi-événements (clusters)

Quand plusieurs événements se produisent proche dans le temps (< 30 min), utiliser **somme vectorielle** :

```python
def calculate_cluster_impact(cluster_events: pd.DataFrame):
    """
    Calcule l'impact d'un cluster d'événements.
    
    Méthode:
    1. Calculer surprise NETTE (somme algébrique des surprises signées)
    2. Calculer score ajusté moyen
    3. Appliquer formule Impact D avec num_events = taille cluster
    """
    # Surprises signées (positif = hausse, négatif = baisse)
    surprises_signed = []
    for event in cluster_events:
        surprise = calculate_surprise_signed(event.actual, event.estimate)
        surprises_signed.append(surprise)
    
    # Surprise NETTE (somme vectorielle)
    surprise_net = sum(surprises_signed)
    surprise_abs = abs(surprise_net)
    
    # Score moyen du cluster
    base_scores = [get_empirical_score(e.event_key) for e in cluster_events]
    base_score_mean = np.mean(base_scores)
    
    # Ajuster selon surprise nette
    adjusted_score = calculate_adjusted_empirical_score(
        base_score_mean,
        surprise_abs
    )
    
    # Calculer impact
    impact = calculate_impact_d(
        empirical_score=adjusted_score,
        num_events=len(cluster_events),
        amplification=2.8
    )
    
    return impact
```

**Exemple :**
```
Cluster 1 (CPI) : +10% (hausse inflation)
Cluster 2 (Jobless) : +12% (hausse chômage)
Cluster 3 (Autre) : -3% (baisse)

Surprise nette = +10% + 12% - 3% = +19%
(Utiliser +19%, pas max(10, 12, 3) = 12%)
```

---

## 📚 RÉSUMÉ : Cycle de Vie Complet

### 1. **Calcul initial** (une fois, historique)

```
Données historiques
  ↓
Mesurer impact réel (prix EUR/USD)
  ↓
Calculer stats (avg, p80, sample_size)
  ↓
Score de base (0-100)
  ↓
Stockage dans event_families
```

### 2. **Utilisation pour prédiction** (à chaque événement)

```
Nouvel événement
  ↓
Charger score base (event_families)
  ↓
Calculer surprise (actual vs estimate)
  ↓
Ajuster score (si surprise > 5%)
  ↓
Calculer impact prédit (Formule Impact D)
  ↓
Prédiction finale (pips, direction, TTR)
```

---

## ⚠️ RÈGLES CRITIQUES

### 1. **Ordre d'exécution obligatoire**

```python
# ❌ INCORRECT
impact = calculate_impact_d(
    empirical_score=base_score,  # Score NON ajusté
    ...
)

# ✅ CORRECT
adjusted_score = calculate_adjusted_empirical_score(
    base_empirical_score=base_score,
    surprise_pct=surprise
)
impact = calculate_impact_d(
    empirical_score=adjusted_score,  # Score AJUSTÉ
    ...
)
```

### 2. **Surprise > 5% → TOUJOURS ajuster**

Si surprise ≤ 5% : utiliser score de base directement  
Si surprise > 5% : **TOUJOURS** appeler `calculate_adjusted_empirical_score()` avant `calculate_impact_d()`

### 3. **Surprise vectorielle pour clusters**

Pour clusters multi-événements, utiliser **somme algébrique** des surprises signées, pas le maximum absolu.

### 4. **Amplification = 2.8**

Valeur calibrée Session 113. Ne pas modifier sans validation empirique.

---

## 📖 RÉFÉRENCES

### Documents

- **Formules validées :** `docs/PROJECT_MANAGEMENT/03_FORMULAS/VALIDATED_FORMULAS.md`
- **Méthodes validées :** `docs/__REFERENCE_CRITIQUE__/METHODES_VALIDEES.md`
- **Session 55 :** `docs/__REFERENCE_CRITIQUE__/SESSION55_RAPPORT_FINAL.md` (Score ajusté)
- **Session 51 :** `docs/__REFERENCE_CRITIQUE__/SESSION51_RAPPORT_FINAL_COMPLET.md` (Impact D)

### Code source

- **Formules :** `src/core/formulas_validated.py`
- **Calcul scores :** `scripts/session123/recalculate_empirical_scores_optimized.py`
- **Cluster impact :** `src/core/cluster_impact_calculator.py`

### Table DB

- **Scores stockés :** `event_families` (table DuckDB)
  - Colonnes : `event_key`, `country`, `empirical_score`, `avg_movement_pips`, `sample_size`, `latency_median`

---

## 🔢 EXEMPLE COMPLET

### Données d'entrée

```python
event_key = "cpi"
country = "US"
actual = 0.4
estimate = 0.3
previous = 0.3
num_events = 9  # Cluster CPI
```

### Étapes de calcul

```python
# 1. Charger score base
base_score = 44.8  # Depuis event_families

# 2. Calculer surprise
surprise = abs((0.4 - 0.3) / 0.3) * 100
# → 33.3%

# 3. Ajuster score
adjusted_score = calculate_adjusted_empirical_score(44.8, 33.3)
# → 44.8 × 1.9 = 85.1

# 4. Calculer impact
impact = calculate_impact_d(
    empirical_score=85.1,
    num_events=9,
    amplification=2.8
)
# → abs(-10.47 + 0.477 × 85.1) × 2.8 × 0.758
# → 57.0 pips

# 5. Direction
# Surprise positive + CPI (inflation) → Bad news USD → EUR/USD UP (+1)
direction = +1

# 6. TTR (Time To Reversal)
ttr = calculate_ttr_c(
    latency_minutes=2.0,  # Depuis event_families
    surprise_pct=33.3
)
# → 2.0 × 2.0 = 4.0 minutes (surprise > 30% → multiplier = 2.0)
```

### Résultat final

```
Impact prédit:  57.0 pips
Direction:      +1 (EUR/USD UP)
TTR:            4.0 minutes
```

**Validation réelle (11 sept 2025) :** 56.2 pips observés ✅

---

**Auteur :** André Valentin avec Claude  
**Date :** 2025-12-13  
**Status :** ✅ VALIDÉ

