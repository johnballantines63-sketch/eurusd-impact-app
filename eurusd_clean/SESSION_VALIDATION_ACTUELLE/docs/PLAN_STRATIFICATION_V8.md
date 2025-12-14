# Plan Stratification V8 - Multi-Wave Patterns

## Objectif V8

**Stratifier les ratios Leg1/Leg2 par buckets** dès que N≥30, pour remplacer les ratios globaux Session 64 par des ratios adaptatifs selon le contexte.

---

## 1. Prérequis V8

### Extension Historique

**Action requise** : Générer `MOVEMENTS_FILE` pré-2024
- Source possible : Table `events` dans DB
- Algo : Reconstruire windows depuis events bruts
- Objectif : Atteindre N≥30 multi-waves uniques

### Validation TURN_PIPS Adaptatif

**Vérifier** : Si TURN_PIPS sort du floor sur gros impacts
- Seuil : `impact_total_pips_used > 53.3 pips`
- Attendu : Variation 8.0-12.0 selon impact leg1

---

## 2. Buckets Stratification (Plan)

### Bucket A - Par Cluster Type

| Bucket | N Minimum | Ratio Leg1 | Ratio Leg2 | CI90 |
|--------|-----------|------------|------------|------|
| **CPI** | 5 | 38.7% | 61.3% | [38.5%, 39.2%] |
| **Jobs** | 3 | - | - | - |
| **CPI+Jobs** | 1 | - | - | - |

**Status V7** : CPI seul a N≥5 (suffisant pour stats). Jobs et CPI+Jobs attendre N≥5.

**Critère robustesse** : N≥5 par bucket pour stats significatives.

### Bucket B - Par Strength (|z|)

| Bucket | Range | N Minimum | Ratio Leg1 | Ratio Leg2 |
|--------|-------|-----------|------------|------------|
| **Low** | |z| < 1.5 | 3 | - | - |
| **Medium** | 1.5 ≤ |z| < 2.0 | 4 | - | - |
| **High** | |z| ≥ 2.0 | 2 | - | - |

**Status V7** : 
- Low : 3 cas (limite)
- Medium : 4 cas (suffisant)
- High : 2 cas (insuffisant)

**Critère robustesse** : N≥5 par bucket pour stats significatives.

### Bucket C - Par Pattern Type

| Bucket | N Minimum | Ratio Leg1 | Ratio Leg2 | CI90 |
|--------|-----------|------------|------------|------|
| **Double-wave** | 2 | 38.8% | 61.2% | [38.5%, 39.2%] |
| **Zig-zag** | 7 | 39.2% | 60.8% | [38.4%, 39.2%] |

**Status V7** : Zig-zag a N=7 (suffisant). Double-wave attendre N≥5.

**Critère robustesse** : N≥5 par pattern pour stats significatives.

### Bucket D - Par Direction First-Leg

| Bucket | N | Ratio Leg1 | Ratio Leg2 |
|--------|---|------------|------------|
| **UP** | 3 | - | - |
| **DOWN** | 6 | - | - |

**Status V7** : DOWN dominant (67%), UP minoritaire (33%).

**Critère robustesse** : N≥5 par direction pour stats significatives.

---

## 3. Stratégie Stratification V8

### Phase 1 - Extension Historique (N≥30)

1. **Générer MOVEMENTS_FILE pré-2024**
   - Utiliser table `events` si disponible
   - Reconstruire windows depuis events bruts
   - Objectif : N≥30 multi-waves uniques

2. **Re-scanner avec historique étendu**
   - `scan_patterns_historique_complet.py --min-date 2018-01-01`
   - Vérifier N uniques ≥ 30

3. **Vérifier TURN_PIPS adaptatif**
   - Compter cas avec `turn_pips_used > 8.0`
   - Si > 0, adaptatif fonctionne en conditions variées

### Phase 2 - Stratification (N≥30)

1. **Stratifier par cluster_type**
   - CPI : N≥5 ✅
   - Jobs : N≥5 (objectif)
   - CPI+Jobs : N≥5 (objectif)

2. **Stratifier par strength**
   - Low : N≥5 (objectif)
   - Medium : N≥5 ✅
   - High : N≥5 (objectif)

3. **Stratifier par pattern**
   - Double-wave : N≥5 (objectif)
   - Zig-zag : N≥7 ✅

4. **Stratifier par direction**
   - UP : N≥5 (objectif)
   - DOWN : N≥6 ✅

### Phase 3 - Recalibrage Ratios

1. **Calculer ratios par bucket**
   - Median Leg1/Leg2 par bucket
   - Bootstrap CI90 par bucket
   - Comparer avec ratios globaux

2. **Décider ajustement**
   - Si écart bucket vs global > 10% → utiliser ratio bucket
   - Sinon → garder ratio global (40/60)

3. **Validation**
   - Vérifier cohérence entre buckets
   - Tester sur échantillon de validation

---

## 4. Métriques par Bucket (Quand N≥30)

### Format Output

```python
{
    'bucket_name': 'CPI',
    'n_samples': 15,
    'leg1_ratio_median': 0.387,
    'leg2_ratio_median': 0.613,
    'leg1_ratio_ci90': [0.385, 0.392],
    'leg2_ratio_ci90': [0.608, 0.615],
    'retrace_ratio_median': 0.45,  # Si double-wave
    'turn_pips_mean': 8.5,  # Vérifier si > 8.0
    'impact_used_mean': 45.2
}
```

### Critères Robustesse

- **N≥5** : Stats descriptives OK
- **N≥10** : Bootstrap CI fiables
- **N≥20** : Stratification robuste
- **N≥30** : Recalibrage définitif possible

---

## 5. Script Stratification V8 (À Créer)

### `stratify_ratios_v8.py`

```python
def stratify_by_cluster_type(df_multi_wave):
    """Stratifie ratios par cluster_type."""
    buckets = {}
    for ctype in df_multi_wave['cluster_type'].unique():
        sub = df_multi_wave[df_multi_wave['cluster_type'] == ctype]
        if len(sub) >= 5:  # Minimum robustesse
            buckets[ctype] = calculate_bucket_stats(sub)
    return buckets

def stratify_by_strength(df_multi_wave):
    """Stratifie ratios par strength bucket."""
    buckets = {
        'low': df_multi_wave[df_multi_wave['trigger_strength'] < 1.5],
        'medium': df_multi_wave[(df_multi_wave['trigger_strength'] >= 1.5) & 
                                (df_multi_wave['trigger_strength'] < 2.0)],
        'high': df_multi_wave[df_multi_wave['trigger_strength'] >= 2.0]
    }
    return {k: calculate_bucket_stats(v) for k, v in buckets.items() if len(v) >= 5}

def calculate_bucket_stats(df_bucket):
    """Calcule stats + bootstrap CI pour un bucket."""
    # Ratios
    leg1_ratios = df_bucket['leg1_amp_pips'] / df_bucket['impact_pips']
    leg2_ratios = df_bucket['leg2_amp_pips'] / df_bucket['impact_pips']
    
    # Bootstrap CI
    leg1_ci = bootstrap_ci(leg1_ratios.values, ci=(5, 95))
    leg2_ci = bootstrap_ci(leg2_ratios.values, ci=(5, 95))
    
    return {
        'n': len(df_bucket),
        'leg1_median': np.median(leg1_ratios),
        'leg2_median': np.median(leg2_ratios),
        'leg1_ci90': leg1_ci,
        'leg2_ci90': leg2_ci
    }
```

---

## 6. Tableau Brut 9 Uniques (Base V8)

Voir fichier : `outputs/direction_router_test/multi_wave_uniques_v7.csv`

**Colonnes** :
- `date`, `cluster_type`, `pattern_type`, `direction_first_leg`
- `impact_pips`, `trigger_strength`
- `leg1_amp_pips`, `leg2_amp_pips`
- `retrace_ratio`, `turn_pips_used`, `impact_total_pips_used`

---

## 7. Prochaines Actions V8

1. **Générer MOVEMENTS_FILE pré-2024** (priorité #1)
2. **Re-scanner avec historique étendu**
3. **Vérifier TURN_PIPS adaptatif** (cas > 8.0)
4. **Créer `stratify_ratios_v8.py`** (quand N≥30)
5. **Stratifier et recalibrer** par buckets

---

**Status** : ✅ **V7 FREEZE - PLAN V8 PRÊT**

