# 📦 REGISTRY MODULES VALIDÉS
**Mise à jour :** 04 novembre 2025 - Session 111  
**Usage :** Liste COMPLÈTE des modules/scripts validés avec signatures exactes

---

## 🎯 OBJECTIF

**Éviter les problèmes récurrents :**
- ❌ Noms de paramètres incorrects (`base_score` vs `base_empirical_score`)
- ❌ Chemins d'import incorrects
- ❌ Signatures de fonctions obsolètes
- ❌ Modules inexistants

**Solution :**
- ✅ Liste exhaustive des modules validés
- ✅ Signatures exactes COPIABLES
- ✅ Chemins d'import corrects
- ✅ Exemples d'utilisation

---

## 📁 MODULES VALIDÉS

### 1. formulas_validated.py ⭐⭐⭐

**Localisation :**
```
fx_impact_app/src/formulas_validated.py
```

**Import :**
```python
from formulas_validated import (
    calculate_adjusted_empirical_score,
    calculate_impact_d,
    calculate_ttr_c,
    calculate_pullback_v2
)
```

**Fonctions :**

#### calculate_adjusted_empirical_score()
```python
def calculate_adjusted_empirical_score(
    base_empirical_score: float,  # ⚠️ PAS base_score !
    surprise_pct: float
) -> float:
    """Ajuste score selon surprise"""
```

**Exemple :**
```python
adjusted = calculate_adjusted_empirical_score(
    base_empirical_score=44.8,  # ⚠️ Nom exact !
    surprise_pct=33.3
)
# Retour : 85.1
```

---

#### calculate_impact_d()
```python
def calculate_impact_d(
    empirical_score: float,       # Score (ajusté ou non)
    num_events: int = 1,           # Nombre événements
    amplification: float = 1.0,    # Facteur amp (défaut 1.0)
    correction_factor: float = 0.758  # Correction (défaut 0.758)
) -> float:
    """Calcule impact en pips"""
```

**Exemple :**
```python
impact = calculate_impact_d(
    empirical_score=85.1,
    num_events=9,
    amplification=2.5
)
# Retour : 57.0 pips
```

---

#### calculate_ttr_c()
```python
def calculate_ttr_c(
    latency_minutes: float,  # Latence médiane
    surprise_pct: float      # Surprise %
) -> float:
    """Calcule TTR en minutes"""
```

**Exemple :**
```python
ttr = calculate_ttr_c(
    latency_minutes=2.0,
    surprise_pct=33.3
)
# Retour : 4.0 min
```

---

#### calculate_pullback_v2()
```python
def calculate_pullback_v2(
    phase1_impact: float,         # Impact phase 1
    minutes_since_peak: float,    # Minutes depuis peak
    minutes_to_next_phase: float  # Minutes jusqu'à phase 2
) -> float:
    """Calcule pullback en pips"""
```

**Exemple :**
```python
pullback = calculate_pullback_v2(
    phase1_impact=37.4,
    minutes_since_peak=10,
    minutes_to_next_phase=15
)
# Retour : 26.9 pips
```

---

### 2. cluster_impact_calculator.py ⭐⭐⭐

**Localisation :**
```
fx_impact_app/src/cluster_impact_calculator.py
```

**Import :**
```python
from cluster_impact_calculator import (
    calculate_cluster_impact,
    calculate_cluster_ttr,
    calculate_pullback_characteristics,
    analyze_cluster_pattern
)
```

**Fonctions :**

#### calculate_cluster_impact()
```python
def calculate_cluster_impact(
    cluster_events: pd.DataFrame,  # DataFrame événements
    amplification: float = 2.5     # Facteur amp (défaut 2.5)
) -> Dict:
    """
    Calcule impact d'un cluster.
    
    Returns:
        dict: {
            'impact_pips': float,
            'base_score': float,
            'adjusted_score': float,
            'max_surprise': float,
            'num_events': int,
            'cluster_weight': float,
            'latency_median': float,
            'calculation_details': dict
        }
    """
```

**Colonnes DataFrame requises :**
- `empirical_score` (obligatoire)
- `actual` (obligatoire pour surprise)
- `estimate` (pour surprise)
- `previous` (fallback pour surprise)
- `latency_median` (optionnel, défaut 2.0)

**Exemple :**
```python
result = calculate_cluster_impact(
    cluster_events=df_cluster,
    amplification=2.5
)
print(f"Impact: {result['impact_pips']:.1f} pips")
```

---

#### calculate_cluster_ttr()
```python
def calculate_cluster_ttr(
    cluster_impact: Dict,           # Dict de calculate_cluster_impact()
    cluster_latency_median: float   # Latence médiane
) -> float:
    """Calcule TTR adaptatif"""
```

**Exemple :**
```python
ttr = calculate_cluster_ttr(
    cluster_impact=result,  # Résultat de calculate_cluster_impact()
    cluster_latency_median=2.0
)
# Retour : 5.2 min
```

---

#### calculate_pullback_characteristics()
```python
def calculate_pullback_characteristics(
    peak_impact: float,                      # Impact peak
    peak_surprise: float,                    # Surprise %
    num_events: int,                         # Nb événements
    has_following_cluster: bool = False,     # Cluster suivant ?
    minutes_to_next_cluster: Optional[int] = None  # Délai si existe
) -> Dict:
    """
    Calcule caractéristiques pullback.
    
    Returns:
        dict: {
            'pullback_pips': float,
            'pullback_duration': int,
            'pullback_ratio': float,
            'pullback_type': str,  # 'single', 'overlapping', 'sequential'
            'creux_expected_minutes': int
        }
    """
```

**Exemple :**
```python
pb = calculate_pullback_characteristics(
    peak_impact=37.4,
    peak_surprise=33.3,
    num_events=14,
    has_following_cluster=True,
    minutes_to_next_cluster=15
)
print(f"Type: {pb['pullback_type']}")  # 'overlapping'
```

---

#### analyze_cluster_pattern()
```python
def analyze_cluster_pattern(
    clusters: List[Dict],           # Liste clusters avec 'time', 'events_indices'
    clusters_impacts: List[Dict],   # Liste résultats calculate_cluster_impact()
    temporal_tolerance: int = 5     # Minutes tolérance (défaut 5)
) -> Dict:
    """
    Analyse pattern entre clusters.
    
    Returns:
        dict: {
            'pattern_type': str,  # 'single', 'cumulative', 'overlapping', 'sequential'
            'primary_cluster_index': int,
            'secondary_clusters': List[int],
            'expected_interactions': List[str],
            'confidence': float
        }
    """
```

**Exemple :**
```python
pattern = analyze_cluster_pattern(
    clusters=[
        {'time': datetime(...), 'events_indices': [0,1,2]},
        {'time': datetime(...), 'events_indices': [3]}
    ],
    clusters_impacts=[result1, result2]
)
print(pattern['pattern_type'])  # 'overlapping'
```

---

### 3. warehouse.duckdb (Base de données) 💾

**Localisation :**
```
eurusd_clean/app/data/warehouse.duckdb
```

**Connexion :**
```python
import duckdb
from pathlib import Path

db_path = Path("eurusd_clean/app/data/warehouse.duckdb")
con = duckdb.connect(str(db_path), read_only=True)
```

**Tables principales :**

#### Table `events`
```sql
SELECT 
    event_id,           -- ID unique
    datetime,           -- ⚠️ PAS timestamp (NULL) !
    name,               -- Nom événement
    country,            -- Pays
    actual,             -- Valeur réelle
    estimate,           -- Valeur estimée
    previous,           -- Valeur précédente
    importance,         -- HIGH, MEDIUM, LOW
    event_key           -- ⚠️ Clé pour JOIN avec event_families
FROM events
WHERE datetime = '2025-09-11 14:30:00'  -- ⚠️ Bern Time +02:00
```

**JOIN avec event_families :**
```sql
SELECT e.*, ef.empirical_score
FROM events e
LEFT JOIN event_families ef ON e.event_key = ef.event_key
-- ⚠️ Les deux tables ont la colonne event_key
```

#### Table `event_families`
```sql
SELECT
    event_key,          -- ⚠️ Clé unique (même nom que dans events)
    empirical_score     -- ⚠️ PAS empirical_impact !
FROM event_families
WHERE event_key = 'CPI_US'
```

#### Table `prices_1m`
```sql
SELECT
    datetime,           -- ⚠️ PAS timestamp !
    open,
    high,
    low,
    close
FROM prices_1m
WHERE datetime BETWEEN '2025-09-11 14:00:00' AND '2025-09-11 15:30:00'
ORDER BY datetime
```

**⚠️ ERREURS COMMUNES :**
```python
# ❌ FAUX
df = con.execute("SELECT timestamp FROM events").df()  # NULL !
df = con.execute("SELECT empirical_impact FROM event_families").df()  # N'existe pas !
query = "LEFT JOIN event_families ef ON e.event_family_key = ef.event_family_key"  # Colonne n'existe pas !

# ✅ CORRECT
df = con.execute("SELECT datetime FROM events").df()
df = con.execute("SELECT empirical_score FROM event_families").df()
query = "LEFT JOIN event_families ef ON e.event_key = ef.event_key"  # Les deux tables ont event_key
```

---

## 📝 SCRIPTS VALIDÉS

### test_cluster_calculator_11sept.py ✅

**Localisation :**
```
eurusd_clean/scripts/session111/test_cluster_calculator_11sept.py
```

**Exécution :**
```bash
cd eurusd_clean/scripts/session111
python test_cluster_calculator_11sept.py
```

**Note :** Les données de test sont APPROXIMATIVES (scores empiriques estimés). Pour tests précis, utiliser vraies données DB.

---

### validate_predictions_vs_reality.py ✅

**Localisation :**
```
eurusd_clean/scripts/session84/validate_predictions_vs_reality.py
```

**Usage :** Validation prédictions vs réalité MT5

---

### list_available_dates.py ✅

**Localisation :**
```
eurusd_clean/scripts/session82/list_available_dates.py
```

**Usage :** Scanner dates disponibles dans DB

---

## 🚨 PIÈGES COURANTS

### 1. Noms de paramètres

❌ **FAUX :**
```python
calculate_adjusted_empirical_score(base_score=44.8, surprise_pct=33.3)
```

✅ **CORRECT :**
```python
calculate_adjusted_empirical_score(base_empirical_score=44.8, surprise_pct=33.3)
```

---

### 2. Colonnes base de données

❌ **FAUX :**
```python
df['timestamp']       # NULL !
df['empirical_impact']  # N'existe pas !

# JOIN incorrect
query = """
LEFT JOIN event_families ef 
ON e.event_family_key = ef.event_family_key  # Colonne n'existe pas !
"""
```

✅ **CORRECT :**
```python
df['datetime']
df['empirical_score']

# JOIN correct
query = """
LEFT JOIN event_families ef 
ON e.event_key = ef.event_key  # Les deux tables ont event_key
"""
```

---

### 3. Timezone

❌ **FAUX :**
```python
event_time_utc = datetime(2025, 9, 11, 12, 30)  # UTC
# Puis convertir en Bern
```

✅ **CORRECT :**
```python
event_time = datetime(2025, 9, 11, 14, 30)  # Déjà en Bern +02:00
# AUCUNE conversion nécessaire
```

---

### 4. Chemins d'import

❌ **FAUX :**
```python
from cluster_calculator import calculate_cluster_impact  # Nom incomplet
```

✅ **CORRECT :**
```python
from cluster_impact_calculator import calculate_cluster_impact  # Nom complet
```

---

## 📋 CHECKLIST AVANT IMPORT

**Avant d'utiliser un module, vérifier :**

- [ ] Nom exact du module dans ce registry
- [ ] Chemin d'import correct
- [ ] Noms exacts des paramètres
- [ ] Types de paramètres corrects
- [ ] Valeurs de retour attendues

**Si doute → Consulter ce registry AVANT de coder**

---

## 🔄 MISE À JOUR

**Ce document est mis à jour quand :**
- Nouveau module validé créé
- Signature de fonction modifiée
- Problème récurrent identifié

**Maintenance :** André + Claude après chaque session majeure

---

## 🎯 UTILISATION

**Workflow recommandé :**

1. **Avant d'importer un module :**
   ```
   Consulter REGISTRY_MODULES_VALIDES.md
   → Copier signature exacte
   → Utiliser sans modification
   ```

2. **Si erreur d'import :**
   ```
   Vérifier nom module dans registry
   → Vérifier chemin d'import
   → Vérifier que module existe
   ```

3. **Si erreur de paramètre :**
   ```
   Vérifier signature dans registry
   → Copier-coller noms exacts
   → Vérifier types de paramètres
   ```

---

## 💡 PRINCIPE

> **"Ne jamais deviner un nom de fonction ou paramètre"**
> 
> **"Toujours vérifier dans le registry AVANT"**
> 
> **"Copier-coller > Se souvenir"**

---

**VERSION :** 1.0  
**DERNIÈRE MISE À JOUR :** 04 novembre 2025 - Session 111  
**STATUT :** Document vivant (mis à jour régulièrement)
