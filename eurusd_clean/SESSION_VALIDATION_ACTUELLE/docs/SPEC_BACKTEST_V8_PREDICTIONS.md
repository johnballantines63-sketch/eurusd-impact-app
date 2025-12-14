# Spécification Backtest V8 Predictions

**Date** : 2025-01-XX  
**Objectif** : Valider fiabilité moteur prédictions avant intégration UI

---

## 📋 INFORMATIONS NÉCESSAIRES POUR LE SCRIPT

### **1. Schémas des Fichiers CSV**

#### **patterns_detected.csv**

**Chemin** : `SESSION_VALIDATION_ACTUELLE/scripts/outputs/direction_router_test/patterns_detected.csv`

**Schéma** (148 lignes) :
```
Colonnes (19):
  1. date                           (object) - Date de l'événement
  2. cluster_type                   (object) - CPI/Jobs/CPI+Jobs
  3. movement_start_time            (object) - Timestamp début mouvement
  4. direction_first_leg            (object) - UP/DOWN
  5. pattern_type                   (object) - single_wave/double_wave/zig_zag
  6. impact_pips                   (float64) - Impact prédit en pips
  7. trigger_strength               (float64) - max|z| des triggers
  8. direction_score                (float64) - Score directionnel S_cluster
  9. leg1_direction                 (object) - Direction jambe 1 (multi-wave)
 10. leg1_amp_pips                  (float64) - Amplitude jambe 1 (multi-wave)
 11. leg1_t_peak_min                (float64) - Temps pic jambe 1 (min)
 12. leg2_direction                 (object) - Direction jambe 2 (multi-wave)
 13. leg2_amp_pips                  (float64) - Amplitude jambe 2 (multi-wave)
 14. leg2_t_peak_min                (float64) - Temps pic jambe 2 (min)
 15. total_amp_pips                 (float64) - Amplitude totale (multi-wave)
 16. retrace_ratio                  (float64) - Ratio retrace (double_wave)
 17. turn_pips_used                 (float64) - TURN_PIPS utilisé
 18. impact_total_pips_used         (float64) - Impact utilisé pour TURN_PIPS
 19. impact_used_for_turn_pips      (float64) - Alias impact_total_pips_used
```

**Exemple** :
```
date        cluster_type pattern_type direction_first_leg trigger_strength
2022-10-27  Jobs         single_wave  UP                  2.288088
2022-10-28  CPI          double_wave  DOWN                2.867819
```

---

#### **movements_historical.csv**

**Chemin** : `SESSION_VALIDATION_ACTUELLE/scripts/outputs/direction_router_test/movements_historical.csv`

**Schéma** (4,448 lignes) :
```
Colonnes (10):
  1. date                           (object) - Date du mouvement
  2. movement_start_time            (object) - Timestamp début mouvement
  3. movement_start_pips            (float64) - Pips au début
  4. peak_time                      (object) - Timestamp du pic
  5. peak_pips                      (float64) - Pips au pic (impact réel)
  6. movement_end_time              (object) - Timestamp fin mouvement
  7. movement_class                 (object) - FAIBLE/MOYEN/FORT/TRÈS_FORT
  8. direction                      (object) - UP/DOWN
  9. baseline_price                 (float64) - Prix baseline
 10. confidence                     (float64) - Confiance (0-1)
```

**Exemple** :
```
date        movement_start_time            peak_pips movement_class direction
2022-10-23  2022-10-23 20:09:00+00:00     28.1      FAIBLE          UP
2022-10-24  2022-10-24 07:00:00+00:00     52.7      MOYEN           DOWN
```

---

### **2. Fonctions Moteur End-to-End**

#### **Fonction principale : `calculate_cluster_impact_with_direction`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/integrate_direction_first_leg.py`

**Signature** :
```python
def calculate_cluster_impact_with_direction(
    cluster_events: pd.DataFrame,
    stats_map: Dict[str, Tuple[float, float]],
    alpha_map: Optional[Dict[str, float]] = None,
    trigger_z: float = 1.0,
    theta: float = 0.05,
    first_leg_mode: bool = True,
    use_linear_formula: bool = True,
    core_families: Optional[List[str]] = None,
    movement_start_time: Optional[pd.Timestamp] = None,
    conn: Optional[duckdb.DuckDBPyConnection] = None
) -> Dict
```

**Input `cluster_events`** (DataFrame requis) :
- `event_key` : Identifiant événement
- `actual` : Valeur réelle (historique pour backtest)
- `estimate` : Valeur estimée
- `family` : Famille événement (optionnel, sera mappé)
- `country` : Code pays (US/EU/GB/DE)
- `empirical_score` : Score base événement (pour impact)
- `latency_median` : Latence médiane (pour TTR)

**Output** (Dict) :
```python
{
    'impact_pips': float,                    # Impact prédit
    'direction_first_leg': str,              # 'UP' | 'DOWN' | 'UNKNOWN'
    'direction_score': float,               # S_cluster (score directionnel)
    'trigger_strength': float,               # max|z_core| des triggers
    'has_trigger': bool,                     # Si trigger activé
    'pattern_type': Optional[str],           # 'single_wave' | 'double_wave' | 'zig_zag'
    'impact_details': dict,                  # Résultat calculate_cluster_impact()
    'direction_audit': List,                 # Audit log router
    'cluster_type': Optional[str],           # CPI/Jobs/CPI+Jobs
    'leg1': Optional[dict],                  # Détails jambe 1 (multi-wave)
    'leg2': Optional[dict],                  # Détails jambe 2 (multi-wave)
    'pattern_meta': Optional[dict]           # Métadonnées pattern
}
```

---

#### **Fonction direction : `predict_direction_for_cluster`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/direction_router_v6.py`

**Signature** :
```python
def predict_direction_for_cluster(
    events_actuals: pd.DataFrame,
    stats_map: Dict[str, Tuple[float, float]],
    alpha_map: Dict[str, float] = None,
    core_families: Optional[List[str]] = None,
    trigger_z: float = 0.8,
    theta: float = 0.05,
    use_fallback_always_on: bool = False,
    first_leg_mode: bool = True
) -> DirectionResult
```

**Output** : `DirectionResult` avec `direction`, `score`, `has_trigger`, `audit_log`

---

#### **Fonction stats : `load_direction_router_dependencies`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/direction_router_v6.py`

**Signature** :
```python
def load_direction_router_dependencies(
    db_path: Optional[Path] = None,
    alpha_file: Optional[Path] = None,
    horizon: str = '1h',
    min_date: str = V8_MIN_STATS_DATE,  # "2022-01-01"
    max_date: str = V8_MAX_STATS_DATE   # "2025-12-31"
) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]
```

**Output** : `(stats_map, alpha_map)`

---

### **3. Imports Principaux**

**Depuis Planificateur V3.2** :
```python
# Configuration
import config
from pathlib import Path

# Event utils
from core.event_utils import (
    normalize_event_keys_list,
    create_event_key_set,
    normalize_event_key_with_variants
)

# Formules validées
from core.formulas_validated import (
    calculate_impact_d,
    calculate_impact_linear,
    calculate_ttr_c,
    calculate_pullback_v2,
    calculate_amplification_extended,
    calculate_adjusted_empirical_score,
    get_event_direction
)

# Double wave
from core.doublewave_prediction import predict_doublewave_overlap

# Ensemble
from core.ensemble_prediction import predict_pattern_based_ensemble
```

**Depuis scripts V8** :
```python
# Direction router
from direction_router_v6 import (
    predict_direction_for_cluster,
    load_direction_router_dependencies,
    CORE_FAMILIES_V6,
    DirectionResult,
    map_event_to_family
)

# Cluster impact avec direction
from integrate_direction_first_leg import calculate_cluster_impact_with_direction
```

---

### **4. Chemins et Constantes**

**Chemins** :
```python
SCRIPT_DIR = Path(__file__).parent
PATTERNS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "patterns_detected.csv"
MOVEMENTS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "movements_historical.csv"
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "backtest_v8"
```

**Constantes V8** :
```python
V8_MIN_STATS_DATE = "2022-01-01"
V8_MAX_STATS_DATE = "2025-12-31"
CORE_FAMILIES_V6 = [
    "CPI", "Jobless Claims", "NFP", "Unemployment",
    "Retail Sales", "GDP", "PPI", "Durable Goods", "FOMC"
]
```

---

## 🎯 PLAN DE BACKTEST

### **Bloc A : SAFE Checks Moteur**

**A1) Replay V7/V8** : ✅ Déjà fait (drift 0.5%)

**A2) Check cohérence stats_map et z-scores**

**Script** : `scripts/backtest_v8_safe_checks.py`

**Actions** :
1. Charger `stats_map` via `load_direction_router_dependencies()`
2. Compter clés core vs non-core
3. Pour chaque date dans `patterns_detected.csv` :
   - Charger events de la date depuis DB
   - Vérifier % events core sans stats
   - Vérifier std non-nulles et n>=5
4. Sortir :
   - `%missing_core_stats` par année, par famille
   - Alertes si famille core >10% missing

**Output** : `outputs/backtest_v8/safe_checks_stats_map.csv`

---

### **Bloc B : Backtest Empirique End-to-End**

**Script** : `scripts/backtest_v8_predictions.py`

**B1) Échantillon dates tradables**

- Prendre toutes les dates de `patterns_detected.csv` (148 dates)
- Pour chaque date :
  - Charger events depuis DB avec `actual` et `estimate` historiques
  - Reconstruire inputs comme à T-0 (estimate/previous OK, actuals = valeurs historiques)
  - Appeler `calculate_cluster_impact_with_direction()` avec ces inputs
  - Comparer prédiction vs mouvement réel depuis `movements_historical.csv`

**B2) Métriques à calculer**

**Direction accuracy** :
- Global : % où `direction_predicted == direction_real`
- Par `cluster_type` : CPI, Jobs, CPI+Jobs
- Par `pattern_type` : single_wave, double_wave, zig_zag

**Hit rate impact** :
- % où `impact_real >= 0.7 × impact_predicted` (tolérance 30%)

**MAE / MAPE impact** :
- MAE pips : `mean(|impact_real - impact_predicted|)`
- MAPE : `mean(|impact_real - impact_predicted| / impact_real) × 100`

**Latence/TTR calibration** :
- MAE minutes latence
- % dates où `latence_reelle ∈ [P25_historique, P75_historique]`

**Validation legs ratios** :
- Comparer `leg1_real / (leg1_real + leg2_real)` vs prior 40/60
- Distribution écart par pattern et cluster

**Robustesse temporelle** :
- Split 2022-2023 vs 2024-2025
- Comparer métriques entre périodes

**B3) Critères SAFE**

- ✅ Direction accuracy > 55-60% global
- ✅ Pas de cluster core < 50% accuracy
- ✅ Impact MAPE < 35-40% sur dates fortes
- ✅ Pas de rupture 22-23 vs 24-25 (>10% écart accuracy)
- ✅ Ratios legs : prior 40/60 dans intervalle empirique

**Outputs** :
- `outputs/backtest_v8/summary.csv` (métriques globales)
- `outputs/backtest_v8/by_cluster.csv` (par cluster_type)
- `outputs/backtest_v8/by_pattern.csv` (par pattern_type)
- `outputs/backtest_v8/by_year.csv` (par année)
- `outputs/backtest_v8/detailed_results.csv` (toutes dates avec prédiction vs réel)

---

### **Bloc C : Baselines & Amélioration**

**C1) Baselines à comparer**

**Baseline 1 : Always Prior**
- Direction = signe score global (sans pattern)
- Ratios = 40/60
- Impact = médiane historique cluster

**Baseline 2 : Impact Median Cluster-Only**
- Ignore actuals, juste médiane historique

**Baseline 3 : Direction par Surprise Sign Simple**
- Somme surprises signées, sans z-score ni alpha

**C2) Si fail → zones d'amélioration**

- `map_event_to_family` / `normalize_event_key` (mauvaise famille)
- Alphas trop agressifs
- Threshold triggers par famille
- Multi-event overlap mal timé

---

## 📝 STRUCTURE SCRIPT BACKTEST

```python
#!/usr/bin/env python3
"""
Backtest V8 Predictions - Validation End-to-End

Objectif : Valider fiabilité moteur prédictions avant intégration UI
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
PATTERNS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "patterns_detected.csv"
MOVEMENTS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "movements_historical.csv"
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "backtest_v8"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Imports moteur
sys.path.insert(0, str(SCRIPT_DIR))
from direction_router_v6 import (
    load_direction_router_dependencies,
    CORE_FAMILIES_V6,
    V8_MIN_STATS_DATE,
    V8_MAX_STATS_DATE
)
from integrate_direction_first_leg import calculate_cluster_impact_with_direction

# ... reste du script ...
```

---

**Version** : Spec Backtest V1  
**Date** : 2025-01-XX

