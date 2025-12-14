# Guide Génération MOVEMENTS_FILE Historique V8

## Objectif

Générer un `MOVEMENTS_FILE` historique pré-2024 en mode **safe-replay** (zéro modification logique V7).

## Script

**Fichier** : `scripts/generate_movements_historical_v8.py`

## Prérequis

- DuckDB avec table `events` (ou `validation_events`, `calendar_events`)
- Table prix M1 (ex: `prices_bern`, `prices_m1`, etc.)
- MOVEMENTS_FILE actuel (2024-2025) pour validation : `outputs/all_movements_detected.csv`

## Usage

```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 generate_movements_historical_v8.py
```

## Fonctionnement

### 1. Détection Automatique

Le script détecte automatiquement :
- **Table events** : cherche `events`, `validation_events`, `calendar_events`
- **Colonne datetime** : cherche `datetime`, `date_time`, `timestamp`, etc.
- **Table prix** : cherche table avec `prices` dans le nom

### 2. Génération Movements

Pour chaque event :
- `baseline_time` = event datetime
- `window` = [baseline_time, baseline_time + 60min]
- `baseline_price` = close à baseline_time
- `impact_pips` = max excursion (high/low) vs baseline
- `direction` = UP/DOWN selon excursion gagnante

### 3. Validation 2024-2025

Le script compare automatiquement :
- Distributions `impact_pips` rebuild vs current
- Calcule drift median
- Affiche recommandation

## Output

**Fichier** : `scripts/outputs/direction_router_test/movements_historical.csv`

**Colonnes** :
- `movement_start_time` : datetime du début mouvement
- `baseline_price` : prix baseline
- `impact_pips` : impact en pips
- `direction` : UP/DOWN
- `peak_time` : datetime du pic
- `peak_price` : prix du pic
- `total_amp_pips` : alias impact_pips
- `peak_pips` : alias impact_pips
- Champs events propagés : `cluster_type`, `event_type`, `name`, `country`, `event_key` (si présents)

## Validation

### Critère de Succès

**Drift median < 10%** → Replay OK

Si drift ≥ 10%, remplacer `compute_movement()` par la logique V7 exacte.

### Exemple Output Validation

```
VALIDATION SAFE-REPLAY SUR 2024-2025
Rebuild 2024-2025 : 150 lignes
Current 2024-2025 : 153 lignes

Impact_pips stats:
   Rebuild: n=150, median=42.3, mean=45.1
   Current: n=153, median=41.8, mean=44.5

Drift median: 1.2%
✅ Drift < 10% → replay OK
```

## Personnalisation

### Remplacer `compute_movement()` par Logique V7

Si drift ≥ 10%, identifier la fonction exacte qui génère MOVEMENTS_FILE actuel et remplacer :

```python
def compute_movement(df_prices, t0):
    """
    Remplace ce bloc par ta fonction V7 exacte.
    """
    # ... logique V7 ...
```

### Ajuster Fenêtre

Modifier `WINDOW_MINUTES` si nécessaire :

```python
WINDOW_MINUTES = 60  # Par défaut 60min
```

## Prochaines Étapes

Une fois `movements_historical.csv` généré et validé :

1. **Option A** : Modifier temporairement `MOVEMENTS_FILE` dans `scan_patterns_historique_complet.py`
2. **Option B** : Ajouter flag `--movements-file` au script scan
3. **Lancer scan étendu** :
   ```bash
   python3 scan_patterns_historique_complet.py \
     --min-date 2018-01-01 \
     --max-date 2025-12-31
   ```
4. **Vérifier N uniques multi-wave** :
   ```bash
   python3 -c "
   import pandas as pd
   df = pd.read_csv('outputs/direction_router_test/patterns_detected.csv')
   mw = df[df.pattern_type.isin(['double_wave','zig_zag'])].drop_duplicates('date')
   print('N multi-wave uniques =', len(mw))
   print(mw.pattern_type.value_counts())
   "
   ```
5. **Si N≥30** :
   - `recalibrate_ratios_bootstrap.py`
   - `stratify_ratios_v8.py`

## Troubleshooting

### Erreur : "Aucune table events trouvée"

Vérifier tables disponibles :
```python
import duckdb
conn = duckdb.connect("path/to/warehouse.duckdb", read_only=True)
print(conn.execute("SHOW TABLES").df())
```

### Erreur : "Aucune table prix trouvée"

Vérifier tables avec "prices" :
```python
tables = conn.execute("SHOW TABLES").df()["name"].tolist()
print([t for t in tables if "price" in t.lower()])
```

### Erreur : "Pas assez de prix"

Certains events peuvent ne pas avoir assez de prix M1 dans la fenêtre. C'est normal, le script les ignore et continue.

### Drift ≥ 10%

1. Identifier fonction exacte qui génère MOVEMENTS_FILE actuel
2. Remplacer `compute_movement()` dans le script
3. Relancer génération
4. Re-valider

---

**Version** : V8 Guide Génération Movements
**Date** : 2025-01-XX
**Status** : ✅ **PRÊT**

