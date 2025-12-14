# Informations pour Backtest V8 Predictions

**Date** : 2025-01-XX  
**Objectif** : Fournir toutes les informations nécessaires pour créer le script de backtest

---

## 📁 SCHÉMAS DES FICHIERS CSV

### **1. patterns_detected.csv**

**Chemin** : `SESSION_VALIDATION_ACTUELLE/scripts/outputs/direction_router_test/patterns_detected.csv`

**Lignes** : 148

**Colonnes (19)** :
```python
[
    'date',                           # Date événement (YYYY-MM-DD)
    'cluster_type',                  # CPI/Jobs/CPI+Jobs
    'movement_start_time',           # Timestamp début mouvement (UTC)
    'direction_first_leg',           # UP/DOWN
    'pattern_type',                  # single_wave/double_wave/zig_zag
    'impact_pips',                   # Impact prédit (pips)
    'trigger_strength',              # max|z| des triggers
    'direction_score',               # Score directionnel S_cluster
    'leg1_direction',                # Direction jambe 1 (multi-wave uniquement)
    'leg1_amp_pips',                 # Amplitude jambe 1 (multi-wave)
    'leg1_t_peak_min',               # Temps pic jambe 1 (minutes)
    'leg2_direction',                # Direction jambe 2 (multi-wave)
    'leg2_amp_pips',                 # Amplitude jambe 2 (multi-wave)
    'leg2_t_peak_min',               # Temps pic jambe 2 (minutes)
    'total_amp_pips',                # Amplitude totale (multi-wave)
    'retrace_ratio',                 # Ratio retrace (double_wave uniquement)
    'turn_pips_used',                # TURN_PIPS utilisé
    'impact_total_pips_used',        # Impact utilisé pour TURN_PIPS
    'impact_used_for_turn_pips'      # Alias impact_total_pips_used
]
```

**Exemple** :
```python
{
    'date': '2022-10-27',
    'cluster_type': 'Jobs',
    'pattern_type': 'single_wave',
    'direction_first_leg': 'UP',
    'trigger_strength': 2.288088,
    'impact_pips': 42.3,
    'leg1_amp_pips': None,  # single_wave n'a pas de legs
    'leg2_amp_pips': None
}
```

---

### **2. movements_historical.csv**

**Chemin** : `SESSION_VALIDATION_ACTUELLE/scripts/outputs/direction_router_test/movements_historical.csv`

**Lignes** : 4,448

**Colonnes (10)** :
```python
[
    'date',                    # Date mouvement (YYYY-MM-DD)
    'movement_start_time',     # Timestamp début (UTC)
    'movement_start_pips',     # Pips au début
    'peak_time',               # Timestamp du pic (UTC)
    'peak_pips',               # Pips au pic (impact réel) ⭐ MÉTRIQUE CLÉ
    'movement_end_time',       # Timestamp fin mouvement
    'movement_class',          # FAIBLE/MOYEN/FORT/TRÈS_FORT
    'direction',               # UP/DOWN ⭐ MÉTRIQUE CLÉ
    'baseline_price',          # Prix baseline
    'confidence'               # Confiance (0-1)
]
```

**Exemple** :
```python
{
    'date': '2022-10-24',
    'movement_start_time': '2022-10-24 07:00:00+00:00',
    'peak_pips': 52.7,         # Impact réel à comparer avec prédiction
    'direction': 'DOWN',       # Direction réelle à comparer
    'movement_class': 'MOYEN'
}
```

---

## 🔧 FONCTIONS MOTEUR END-TO-END

### **Fonction principale : `calculate_cluster_impact_with_direction`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/integrate_direction_first_leg.py`

**Import** :
```python
from integrate_direction_first_leg import calculate_cluster_impact_with_direction
```

**Signature complète** :
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

**Input `cluster_events` (DataFrame requis)** :
```python
cluster_events = pd.DataFrame({
    'event_key': ['CPI y/y', 'CPI Core y/y'],      # ⭐ REQUIS
    'actual': [2.5, 2.3],                          # ⭐ REQUIS (valeurs historiques pour backtest)
    'estimate': [2.4, 2.2],                        # ⭐ REQUIS
    'country': ['US', 'US'],                        # ⭐ REQUIS (pour lookup stats_map)
    'family': ['CPI', 'CPI'],                       # Optionnel (sera mappé si absent)
    'empirical_score': [15.0, 12.0],                # Optionnel (défaut 10.0)
    'latency_median': [2.0, 2.0],                   # Optionnel (défaut 2.0)
    'previous': [2.3, 2.1],                         # Optionnel
    'forecast': [2.4, 2.2]                           # Optionnel
})
```

**Output (Dict)** :
```python
{
    'impact_pips': float,                    # ⭐ Impact prédit (pips)
    'direction_first_leg': str,              # ⭐ 'UP' | 'DOWN' | 'UNKNOWN'
    'direction_score': float,                # Score directionnel S_cluster
    'trigger_strength': float,                # max|z_core| des triggers
    'has_trigger': bool,                    # Si trigger activé
    'pattern_type': Optional[str],           # ⭐ 'single_wave' | 'double_wave' | 'zig_zag'
    'impact_details': dict,                  # Résultat calculate_cluster_impact()
    'direction_audit': List,                 # Audit log router
    'cluster_type': Optional[str],            # CPI/Jobs/CPI+Jobs
    'leg1': Optional[dict],                  # Détails jambe 1 (si multi-wave)
    'leg2': Optional[dict],                  # Détails jambe 2 (si multi-wave)
    'pattern_meta': Optional[dict],          # Métadonnées pattern
    'skipped': bool,                         # Si calcul sauté
    'skip_reason': Optional[str]             # Raison si skipped=True
}
```

**Pour multi-wave** (`leg1` et `leg2` présents) :
```python
leg1 = {
    'direction': 'UP',
    'amp_pips': 24.1,
    't_peak_min': 8.5
}
leg2 = {
    'direction': 'UP',
    'amp_pips': 38.6,
    't_peak_min': 45.2
}
```

---

### **Fonction direction : `predict_direction_for_cluster`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/direction_router_v6.py`

**Import** :
```python
from direction_router_v6 import predict_direction_for_cluster, DirectionResult
```

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

**Output** : `DirectionResult` (dataclass)
```python
@dataclass
class DirectionResult:
    direction: str          # 'UP' | 'DOWN' | 'UNKNOWN'
    score: float           # S_cluster (score directionnel)
    has_trigger: bool      # Si trigger activé
    n_active: int          # Nombre events actifs
    audit_log: List        # Liste EventContribution
```

---

### **Fonction stats : `load_direction_router_dependencies`**

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/direction_router_v6.py`

**Import** :
```python
from direction_router_v6 import load_direction_router_dependencies
```

**Signature** :
```python
def load_direction_router_dependencies(
    db_path: Optional[Path] = None,
    alpha_file: Optional[Path] = None,
    horizon: str = '1h',
    min_date: Optional[str] = None,  # Défaut: "2022-01-01"
    max_date: Optional[str] = None   # Défaut: "2025-12-31"
) -> Tuple[Dict[str, Tuple[float, float]], Dict[str, float]]
```

**Output** : `(stats_map, alpha_map)`
```python
stats_map = {
    "cpi_us": (mean_surprise, std_surprise),
    "nfp_us": (mean_surprise, std_surprise),
    # ... 391 clés au total
}
alpha_map = {}  # Vide si first_leg_mode=True
```

---

## 📦 IMPORTS COMPLETS POUR BACKTEST

```python
#!/usr/bin/env python3
"""
Backtest V8 Predictions - Validation End-to-End
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configuration paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Ajouter au path
sys.path.insert(0, str(SCRIPT_DIR))

# Imports moteur V8
from direction_router_v6 import (
    load_direction_router_dependencies,
    predict_direction_for_cluster,
    CORE_FAMILIES_V6,
    DirectionResult,
    map_event_to_family,
    V8_MIN_STATS_DATE,  # "2022-01-01"
    V8_MAX_STATS_DATE   # "2025-12-31"
)

from integrate_direction_first_leg import calculate_cluster_impact_with_direction

# Chemins fichiers
PATTERNS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "patterns_detected.csv"
MOVEMENTS_FILE = SCRIPT_DIR / "outputs" / "direction_router_test" / "movements_historical.csv"
DB_PATH = Path("/Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/fx_impact_app/data/warehouse.duckdb")
OUTPUT_DIR = SCRIPT_DIR / "outputs" / "backtest_v8"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
```

---

## 🔄 WORKFLOW BACKTEST (Pseudo-code)

```python
# 1. Charger données
patterns_df = pd.read_csv(PATTERNS_FILE)
movements_df = pd.read_csv(MOVEMENTS_FILE)
conn = duckdb.connect(str(DB_PATH), read_only=True)

# 2. Charger stats_map V8
stats_map, alpha_map = load_direction_router_dependencies(
    db_path=DB_PATH,
    min_date=V8_MIN_STATS_DATE,
    max_date=V8_MAX_STATS_DATE
)

# 3. Pour chaque date dans patterns_detected.csv
results = []
for _, pattern_row in patterns_df.iterrows():
    date_str = pattern_row['date']
    movement_start = pd.to_datetime(pattern_row['movement_start_time'], utc=True)
    
    # 3a. Charger events de cette date depuis DB
    day_start = pd.Timestamp(date_str).tz_localize('UTC')
    day_end = day_start + timedelta(days=1)
    
    query_events = """
    SELECT 
        ts_utc, country, event_title, event_key,
        actual, estimate, previous, forecast,
        importance_n
    FROM events
    WHERE ts_utc >= ? AND ts_utc < ?
      AND country IN ('US', 'EU', 'GB', 'DE')
      AND actual IS NOT NULL
      AND estimate IS NOT NULL
    ORDER BY ts_utc
    """
    events_df = conn.execute(query_events, [day_start, day_end]).df()
    
    # 3b. Mapper vers familles et filtrer core
    from direction_router_v6 import map_event_to_family
    events_df['family'] = events_df['event_key'].apply(map_event_to_family)
    events_core = events_df[events_df['family'].isin(CORE_FAMILIES_V6)].copy()
    
    if len(events_core) == 0:
        continue
    
    # 3c. Préparer colonnes requises
    if 'empirical_score' not in events_core.columns:
        events_core['empirical_score'] = 10.0
    if 'latency_median' not in events_core.columns:
        events_core['latency_median'] = 2.0
    
    # 3d. Appeler moteur prédiction (comme à T-0 avec actuals historiques)
    prediction = calculate_cluster_impact_with_direction(
        cluster_events=events_core,
        stats_map=stats_map,
        alpha_map=alpha_map,
        trigger_z=1.0,
        theta=0.05,
        first_leg_mode=True,
        use_linear_formula=True,
        movement_start_time=movement_start,
        conn=conn
    )
    
    # 3e. Trouver mouvement réel correspondant
    movement_real = movements_df[
        (movements_df['date'] == date_str) &
        (movements_df['peak_pips'] >= 40.0)  # Filtrer mouvements significatifs
    ]
    
    if len(movement_real) == 0:
        continue
    
    # Prendre le mouvement le plus fort de la journée
    movement_real = movement_real.loc[movement_real['peak_pips'].idxmax()]
    
    # 3f. Comparer prédiction vs réel
    result = {
        'date': date_str,
        'cluster_type': pattern_row['cluster_type'],
        'pattern_type_pred': prediction.get('pattern_type'),
        'pattern_type_real': pattern_row.get('pattern_type'),  # Depuis patterns_detected
        'direction_pred': prediction.get('direction_first_leg'),
        'direction_real': movement_real['direction'],
        'impact_pred': prediction.get('impact_pips', 0.0),
        'impact_real': movement_real['peak_pips'],
        'trigger_strength': prediction.get('trigger_strength', 0.0),
        'has_trigger': prediction.get('has_trigger', False),
        'skipped': prediction.get('skipped', False)
    }
    
    # Ajouter legs si multi-wave
    if prediction.get('leg1') and prediction.get('leg2'):
        result['leg1_pred'] = prediction['leg1'].get('amp_pips', 0.0)
        result['leg2_pred'] = prediction['leg2'].get('amp_pips', 0.0)
        result['total_pred'] = prediction.get('impact_pips', 0.0)
        
        # Extraire legs réels depuis patterns_detected si disponible
        result['leg1_real'] = pattern_row.get('leg1_amp_pips')
        result['leg2_real'] = pattern_row.get('leg2_amp_pips')
        result['total_real'] = pattern_row.get('total_amp_pips')
    
    results.append(result)

# 4. Calculer métriques
results_df = pd.DataFrame(results)
# ... calculs direction accuracy, MAE, MAPE, etc.
```

---

## 📊 MÉTRIQUES À CALCULER

### **Direction Accuracy**
```python
direction_correct = (results_df['direction_pred'] == results_df['direction_real']).sum()
direction_accuracy = direction_correct / len(results_df) * 100
```

### **Hit Rate Impact**
```python
hit_rate = (results_df['impact_real'] >= 0.7 * results_df['impact_pred']).sum() / len(results_df) * 100
```

### **MAE / MAPE Impact**
```python
mae_pips = np.mean(np.abs(results_df['impact_real'] - results_df['impact_pred']))
mape = np.mean(np.abs(results_df['impact_real'] - results_df['impact_pred']) / results_df['impact_real']) * 100
```

### **Ratios Legs (multi-wave uniquement)**
```python
multi_wave = results_df[results_df['leg1_pred'].notna()].copy()
multi_wave['leg1_ratio_pred'] = multi_wave['leg1_pred'] / multi_wave['total_pred']
multi_wave['leg1_ratio_real'] = multi_wave['leg1_real'] / multi_wave['total_real']
leg1_ratio_mae = np.mean(np.abs(multi_wave['leg1_ratio_pred'] - multi_wave['leg1_ratio_real']))
```

---

## ✅ CRITÈRES SAFE (Go/No-Go)

- ✅ Direction accuracy > 55-60% global
- ✅ Pas de cluster core < 50% accuracy
- ✅ Impact MAPE < 35-40% sur dates fortes
- ✅ Pas de rupture 22-23 vs 24-25 (>10% écart accuracy)
- ✅ Ratios legs : prior 40/60 dans intervalle empirique

---

**Version** : Info Backtest V1  
**Date** : 2025-01-XX

