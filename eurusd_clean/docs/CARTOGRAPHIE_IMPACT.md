# 📊 CARTOGRAPHIE COMPLÈTE DE L'IMPACT

**Date de création** : 2025-01-XX  
**Objectif** : Cartographier TOUT ce qui concerne la notion d'"impact" pour préparer une refonte propre de la prédiction.

---

## 📋 TABLE DES MATIÈRES

1. [Définitions de l'impact](#1-définitions-de-limpact)
2. [Calculs d'impact dans le code](#2-calculs-dimpact-dans-le-code)
3. [Stockage de l'impact](#3-stockage-de-limpact)
4. [Affichage de l'impact dans l'UI](#4-affichage-de-limpact-dans-lui)
5. [Table `event_impacts_v2`](#5-table-event_impacts_v2)
6. [Résumé et incohérences](#6-résumé-et-incohérences)

---

## 1. DÉFINITIONS DE L'IMPACT

### 1.1. `impact_pips` (Impact détecté dans le Planificateur)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Fonction** : `detect_pattern_type()` (lignes 2114-2412)

**Définition mathématique** :
- **Baseline** : Prix de référence au début du mouvement détecté
  - Pour mouvement UP : `baseline_price = segment.iloc[0]['low']` (ligne 1663)
  - Pour mouvement DOWN : `baseline_price = segment.iloc[0]['high']` (ligne 1689)
- **Pic** : 
  - Pour mouvement UP : `peak_price = segment['high'].max()` (ligne 1664)
  - Pour mouvement DOWN : `trough_price = segment['low'].min()` (ligne 1690)
- **Formule** :
  - UP : `impact_pips = (peak_price - baseline_price) * 10000` (ligne 1666)
  - DOWN : `impact_pips = (baseline_price - trough_price) * 10000` (ligne 1692)
- **Horizon** : Segment de prix détecté par `scan_price_movements()` avec seuil `min_pips` (défaut 35.0 pips)
- **Côté** : Absolu (toujours positif)
- **Filtres** : 
  - `min_pips` (défaut 35.0 pips)
  - Pour Double Wave : Impact NET = `(second_peak_high - baseline_price) * 10000` (ligne 2316)

**Contexte** :
```python
# Lignes 1655-1692
if inv['type'] == 'TROUGH':  # Mouvement UP
    baseline_price = segment.iloc[0]['low']
    peak_price = segment['high'].max()
    peak_idx = segment['high'].idxmax()
    impact_pips = (peak_price - baseline_price) * 10000
    direction = 'UP'
else:  # PEAK - Mouvement DOWN
    baseline_price = segment.iloc[0]['high']
    trough_price = segment['low'].min()
    trough_idx = segment['low'].idxmin()
    impact_pips = (baseline_price - trough_price) * 10000
    direction = 'DOWN'
```

---

### 1.2. `phase1_pips` (dans `event_impacts_v2`)

**Fichier** : `src/core/price_loader_finnhub.py`  
**Fonction** : `measure_impact_from_finnhub()` (lignes 96-292)

**Définition mathématique** :
- **Baseline** : `start_price = first_candle['open']` (ligne 205)
  - Où `first_candle` est la première bougie M1 **à l'événement ou après** (`prices_at_event.iloc[0]`)
  - Fallback : `start_price = last_candle_before['close']` si aucune bougie à l'événement (ligne 210)
- **Pic** : 
  - UP : `peak_price = prices_after.loc[peak_idx, 'high']` (ligne 236)
  - DOWN : `peak_price = prices_after.loc[peak_idx, 'low']` (ligne 242)
- **Formule** :
  - UP : `impact_pips = peak_high` où `peak_high = (prices_after['high'] - start_price).max() * 10000` (lignes 226, 233)
  - DOWN : `impact_pips = peak_low` où `peak_low = (start_price - prices_after['low']).max() * 10000` (lignes 227, 239)
- **Horizon** : Fenêtre après l'événement (`lookahead_minutes`, défaut 120 minutes)
- **Côté** : Absolu (toujours positif)
- **Filtres** : Aucun filtre de seuil minimum dans cette fonction

**Contexte** :
```python
# Lignes 224-243
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
else:
    impact_pips = peak_low
    direction = -1  # DOWN
    peak_idx = prices_after['pips_low'].idxmax()
    peak_price = prices_after.loc[peak_idx, 'low']
```

**⚠️ IMPORTANT** : Cette fonction est utilisée pour mesurer l'impact **réel** depuis les prix historiques. Elle est appelée dans `run_pipeline_complete.py` (ligne 1344) pour calculer `impact_reel` qui sera ensuite stocké dans `event_impacts_v2` comme `phase1_pips`.

---

### 1.3. `impact_median` / `impact_mean` (dans le cache des clusters)

**Fichier** : `scripts/catalog_all_clusters_from_db.py`  
**Fonction** : `catalog_all_clusters()` (lignes 262-422)

**Définition** :
- **Source** : Agrégation des `impact_pips` mesurés pour chaque occurrence d'un cluster
- **Calcul** :
  - `impact_median = safe_median(pd.Series(impacts))` (ligne 390)
  - `impact_mean = safe_mean(pd.Series(impacts))` (ligne 391)
- **Source des `impacts`** : 
  - Vient de `measure_impact_for_cluster()` (lignes 166-259)
  - Qui appelle `detect_pattern_type()` et récupère `movement.get('impact_pips', 0)` (ligne 221)
  - Donc **utilise la même définition que "Impact détecté"** (section 1.1)

**Contexte** :
```python
# Lignes 385-400
if impacts:
    catalogued_clusters.append({
        'cluster_signature': signature,
        'n_samples': len(impacts),
        'impact_median': safe_median(pd.Series(impacts)),
        'impact_mean': safe_mean(pd.Series(impacts)),
        'impact_std': float(pd.Series(impacts).std(ddof=0)) if len(impacts) > 1 else 0.0,
        # ...
    })
```

---

### 1.4. `impact_pips` (Impact prédit dans le Planificateur)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Fonctions** : 
- `predict_single_wave_base()` (lignes 2649-2838)
- `predict_double_wave_base()` (lignes 2430-2620)

**Définition** :
- **Single Wave** : Utilise `calculate_impact_linear()` ou `predict_impact_with_amplification()` (lignes 2733-2808)
- **Double Wave** : Utilise `calculate_impact_linear()` puis applique ratios Double Wave (Phase 1: 58%, Pullback: 84%, Phase 2: 90%) (lignes 2521-2620)
- **Formule linéaire** : `calculate_impact_linear(base_empirical_score, adjusted_empirical_score, surprise_avg, surprise_max, n_events)` (ligne 2521)
- **Résultat** : `prediction_result['prediction_pips']` (ligne 3913)

**Contexte** :
```python
# Lignes 2521-2527 (Double Wave)
base_impact_no_amp = calculate_impact_linear(
    base_empirical_score=mean_empirical_score,
    adjusted_empirical_score=score_adjusted_mean,
    surprise_avg=surprise_avg,
    surprise_max=surprise_max,
    n_events=num_events
)
```

---

## 2. CALCULS D'IMPACT DANS LE CODE

### 2.1. Détection de mouvement (`scan_price_movements`)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Fonction** : `scan_price_movements()` (lignes ~1850-1910)

**Calcul** :
- Détecte les mouvements explosifs ou progressifs dans les prix
- Calcule `impact_pips` pour chaque mouvement candidat
- Utilise `min_pips` comme seuil de filtrage

---

### 2.2. Mesure d'impact réel (`measure_impact_from_finnhub`)

**Fichier** : `src/core/price_loader_finnhub.py`  
**Fonction** : `measure_impact_from_finnhub()` (lignes 96-292)

**Utilisation** :
- Appelée dans `run_pipeline_complete.py` (ligne 1344) pour mesurer l'impact réel
- Appelée dans `scripts/catalog_all_clusters_from_db.py` via `measure_impact_for_cluster()` (ligne 204)

**Retourne** :
```python
{
    'impact_pips': float(impact_pips),
    'direction': int(direction),
    'start_price': float(start_price),
    'peak_price': float(peak_price),
    'peak_time': peak_time_naive,
    'time_to_peak_minutes': float(time_to_peak_minutes),
    # ...
}
```

---

### 2.3. Prédiction d'impact (`predict_single_wave_base`, `predict_double_wave_base`)

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`

**Fonctions** :
- `predict_single_wave_base()` (lignes 2649-2838)
- `predict_double_wave_base()` (lignes 2430-2620)

**Dépendances** :
- `calculate_impact_linear()` depuis `core.formulas_validated`
- `predict_impact_with_amplification()` depuis `core.amplification_prediction`

---

### 2.4. Calcul d'impact par cluster (`calculate_cluster_impact`)

**Fichier** : `src/core/cluster_impact_calculator.py`  
**Fonction** : `calculate_cluster_impact()` (lignes 50-229)

**Utilisation** :
- Utilisée pour calculer l'impact d'un cluster isolé
- Utilise `calculate_impact_linear()` ou `calculate_impact_d()` selon le paramètre `use_linear_formula`

---

## 3. STOCKAGE DE L'IMPACT

### 3.1. Table `event_impacts_v2`

**Schéma** :
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
    phase1_pips         DOUBLE,  -- ⭐ Impact réel mesuré
    ttr_minutes         INTEGER,
    direction           VARCHAR,
    start_price         DOUBLE,
    ttr_price           DOUBLE,
    source              VARCHAR,
    created_at          TIMESTAMP WITH TIME ZONE
)
```

**⚠️ IMPORTANT** : La table `event_impacts_v2` n'est **PAS créée ni écrite** dans le code actuel trouvé.  
- Le schéma existe dans `docs/__REFERENCE_CRITIQUE__/SCHEMA_DATABASE_COMPLET.md` (ligne 130)
- Aucun `INSERT INTO event_impacts_v2` ou `CREATE TABLE event_impacts_v2` trouvé dans le code
- La table semble être créée et alimentée par un processus externe ou un script non versionné

**Colonne `phase1_pips`** :
- Devrait contenir l'impact réel mesuré par `measure_impact_from_finnhub()`
- Définition : Voir section 1.2

---

### 3.2. Cache CSV (`cache_clusters.csv`)

**Fichier** : `scripts/catalog_all_clusters_from_db.py`  
**Fonction** : `catalog_all_clusters()` (lignes 262-422)

**Colonnes** :
- `impact_median` : Médiane des impacts historiques du cluster
- `impact_mean` : Moyenne des impacts historiques du cluster
- `impact_std` : Écart-type des impacts historiques

**Sauvegarde** :
```python
# Ligne 413
df_catalogued.to_csv(OUTPUT_CACHE, index=False)
```

---

## 4. AFFICHAGE DE L'IMPACT DANS L'UI

### 4.1. Planificateur (`5_Planificateur_V3.2_Formule_Lineaire.py`)

**"Impact détecté"** (ligne 3736) :
```python
if 'impact_pips' in metrics:
    st.metric("Impact détecté", f"{metrics['impact_pips']:.1f} pips")
```
- Source : `pattern_result['metrics']['impact_pips']` (ligne 2406)
- Définition : Voir section 1.1

**"Impact prédit"** (ligne 3912) :
```python
st.metric(
    "Impact prédit",
    f"{prediction_result['prediction_pips']:.1f} pips"
)
```
- Source : `prediction_result['prediction_pips']` (ligne 3913)
- Définition : Voir section 1.4

---

### 4.2. Calendrier (`1_Calendrier_Trading.py`)

**Affichage** : Via colonne `impact_candidate` dans le DataFrame filtré
- Source : Cache des clusters (`impact_median` ou `impact_mean`)

---

## 5. TABLE `event_impacts_v2`

### 5.1. Création de la table

**⚠️ NON TROUVÉE DANS LE CODE**  
- Le schéma existe dans la documentation (`docs/__REFERENCE_CRITIQUE__/SCHEMA_DATABASE_COMPLET.md`)
- Aucun `CREATE TABLE event_impacts_v2` trouvé dans le code source

---

### 5.2. Écriture dans la table

**⚠️ NON TROUVÉE DANS LE CODE**  
- Aucun `INSERT INTO event_impacts_v2` trouvé
- Aucun `UPDATE event_impacts_v2` trouvé
- La table semble être alimentée par un processus externe

**Hypothèse** : La table est peut-être créée et alimentée par :
- Un script non versionné
- Un processus ETL externe
- Un script de migration de données

---

### 5.3. Lecture depuis la table

**Fichier** : `app/services/data_service.py`  
**Fonction** : `get_event_impacts()` (lignes 475-529)

**Utilisation** :
```python
query = """
SELECT 
    ei.*
FROM event_impacts_v2 ei
WHERE ei.ts_utc >= '{start_date}'
  AND ei.ts_utc <= '{end_date}'
  AND ei.phase1_pips >= {min_phase1_pips}
ORDER BY ei.ts_utc
"""
```

---

## 6. RÉSUMÉ ET INCOHÉRENCES

### 6.1. Définitions différentes de l'impact

| Concept | Baseline | Pic | Horizon | Filtres |
|---------|---------|-----|---------|---------|
| **Impact détecté** (Planificateur) | `low`/`high` du segment détecté | `high.max()`/`low.min()` du segment | Segment détecté par `scan_price_movements()` | `min_pips` (35.0) |
| **phase1_pips** (`event_impacts_v2`) | `open` première bougie événement | `high.max()`/`low.min()` dans fenêtre 120 min | 120 minutes après événement | Aucun |
| **impact_median** (cache) | Même que "Impact détecté" | Même que "Impact détecté" | Même que "Impact détecté" | `min_pips` (35.0) |
| **Impact prédit** | N/A (formule) | N/A (formule) | N/A (formule) | N/A |

**⚠️ INCOHÉRENCE MAJEURE** :
- **"Impact détecté"** utilise le `low`/`high` du **segment détecté** (qui peut commencer avant l'événement)
- **`phase1_pips`** utilise l'`open` de la **première bougie à l'événement** (baseline fixe à l'événement)

**Conséquence** : Les deux mesures peuvent donner des valeurs très différentes pour le même événement.

---

### 6.2. Table `event_impacts_v2` non écrite

**Problème** : La table `event_impacts_v2` est référencée dans le code mais :
- N'est pas créée dans le code
- N'est pas alimentée dans le code
- Est seulement lue dans `data_service.py`

**Impact** : Impossible de savoir comment `phase1_pips` est réellement calculé et stocké.

---

### 6.3. Cache des clusters vs `event_impacts_v2`

**Problème** : 
- Le cache des clusters (`cache_clusters.csv`) utilise `impact_pips` de `detect_pattern_type()` (définition "Impact détecté")
- `event_impacts_v2` devrait utiliser `phase1_pips` de `measure_impact_from_finnhub()` (définition différente)

**Conséquence** : Les deux sources peuvent donner des valeurs différentes pour le même cluster.

---

## 7. RECOMMANDATIONS POUR REFONTE

### 7.1. Unifier la définition de l'impact

**Proposition** : Utiliser une seule fonction de calcul d'impact avec paramètres configurables :

```python
def calculate_impact_unified(
    df_prices: pd.DataFrame,
    event_timestamp: pd.Timestamp,
    baseline_method: str = 'event_open',  # 'event_open', 'segment_low', 'segment_high'
    horizon_minutes: int = 120,
    min_pips: Optional[float] = None
) -> Dict:
    """
    Calcule l'impact de manière unifiée.
    
    Args:
        baseline_method: 
            - 'event_open': open première bougie événement (comme phase1_pips)
            - 'segment_low': low segment détecté (comme impact détecté UP)
            - 'segment_high': high segment détecté (comme impact détecté DOWN)
        horizon_minutes: Fenêtre après événement
        min_pips: Seuil minimum (None = pas de filtre)
    """
    pass
```

---

### 7.2. Créer/écrire `event_impacts_v2` de manière explicite

**Proposition** : Créer un script dédié qui :
1. Crée la table `event_impacts_v2` si elle n'existe pas
2. Calcule `phase1_pips` pour chaque événement historique
3. Insère/mets à jour les données dans la table

---

### 7.3. Documenter les différences

**Proposition** : Ajouter des commentaires explicites dans le code indiquant :
- Quelle définition d'impact est utilisée
- Pourquoi cette définition est choisie
- Comment convertir entre les différentes définitions si nécessaire

---

## 8. FICHIERS CLÉS À MODIFIER

1. **`streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`**
   - `detect_pattern_type()` : Définit "Impact détecté"
   - `predict_single_wave_base()` : Définit "Impact prédit" (Single Wave)
   - `predict_double_wave_base()` : Définit "Impact prédit" (Double Wave)

2. **`src/core/price_loader_finnhub.py`**
   - `measure_impact_from_finnhub()` : Définit `phase1_pips`

3. **`scripts/catalog_all_clusters_from_db.py`**
   - `measure_impact_for_cluster()` : Utilise `detect_pattern_type()` pour calculer `impact_median`

4. **`src/core/cluster_impact_calculator.py`**
   - `calculate_cluster_impact()` : Calcule impact prédit pour un cluster

5. **`scripts/run_pipeline_complete.py`**
   - Appelle `measure_impact_from_finnhub()` pour mesurer impact réel (ligne 1344)

---

## 9. EXTRACTS DE CODE POUR AUDIT

### 9.1. Calcul "Impact détecté"

**Fichier** : `streamlit_app/pages/5_Planificateur_V3.2_Formule_Lineaire.py`  
**Lignes** : 1655-1692

```python
if inv['type'] == 'TROUGH':  # Mouvement UP
    baseline_price = segment.iloc[0]['low']
    peak_price = segment['high'].max()
    peak_idx = segment['high'].idxmax()
    impact_pips = (peak_price - baseline_price) * 10000
    direction = 'UP'
else:  # PEAK - Mouvement DOWN
    baseline_price = segment.iloc[0]['high']
    trough_price = segment['low'].min()
    trough_idx = segment['low'].idxmin()
    impact_pips = (baseline_price - trough_price) * 10000
    direction = 'DOWN'
```

---

### 9.2. Calcul `phase1_pips`

**Fichier** : `src/core/price_loader_finnhub.py`  
**Lignes** : 224-243

```python
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
else:
    impact_pips = peak_low
    direction = -1  # DOWN
    peak_idx = prices_after['pips_low'].idxmax()
    peak_price = prices_after.loc[peak_idx, 'low']
```

Où `start_price = first_candle['open']` (ligne 205) avec `first_candle = prices_at_event.iloc[0]` (ligne 204).

---

### 9.3. Calcul `impact_median` (cache)

**Fichier** : `scripts/catalog_all_clusters_from_db.py`  
**Lignes** : 385-400

```python
if impacts:
    catalogued_clusters.append({
        'cluster_signature': signature,
        'n_samples': len(impacts),
        'impact_median': safe_median(pd.Series(impacts)),
        'impact_mean': safe_mean(pd.Series(impacts)),
        'impact_std': float(pd.Series(impacts).std(ddof=0)) if len(impacts) > 1 else 0.0,
        # ...
    })
```

Où `impacts` vient de `measure_impact_for_cluster()` qui appelle `detect_pattern_type()` et récupère `movement.get('impact_pips', 0)`.

---

## 10. CONCLUSION

**Problèmes identifiés** :
1. **Définition incohérente** : "Impact détecté" vs `phase1_pips` utilisent des baselines différentes
2. **Table `event_impacts_v2` non écrite** : Impossible de savoir comment elle est alimentée
3. **Cache vs DB** : Deux sources de données historiques avec définitions différentes

**Actions recommandées** :
1. Unifier la définition de l'impact avec une fonction commune
2. Créer/écrire `event_impacts_v2` de manière explicite
3. Documenter les différences et conversions possibles

---

**Fin du document**
