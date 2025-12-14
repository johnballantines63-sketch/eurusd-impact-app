# 🏗️ V4 Build Truth Pipeline - Génération Vérité Terrain

**Version :** V4  
**Date :** 2025-12-13  
**Objectif :** Pipeline de génération massive de vérité terrain depuis prix M1

---

## 📋 Vue d'ensemble

Le pipeline V4 génère la table `daily_pattern_truth_v4` contenant la vérité terrain des patterns détectés depuis les prix M1 pour chaque jour de trading.

**Source de données :**
- **Prix :** `prices_finnhub_m1` (colonne `datetime`, `close`)
- **Événements :** `events_enriched_v1` (kernel basé sur `event_key`)
- **Pattern :** Module `research/pattern_labeler_m1.py`

**Table de sortie :** `daily_pattern_truth_v4`

---

## 🗄️ Structure de la table

### Création de la table

```bash
# Depuis la racine du projet
python3 << 'EOF'
import duckdb
from pathlib import Path

DB_PATH = Path("data/warehouse.duckdb")
conn = duckdb.connect(str(DB_PATH), read_only=False)

sql_file = Path("sql/create_daily_pattern_truth_v4.sql")
sql_content = sql_file.read_text()

# Exécuter les statements (séparés par ;)
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

for stmt in statements:
    if stmt:
        try:
            conn.execute(stmt)
            print(f"✅ Exécuté: {stmt[:50]}...")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"⚠️  {e}")

conn.close()
print("✅ Table créée")
EOF
```

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| `date_local` | DATE (PK) | Date locale |
| `timezone` | VARCHAR | Timezone utilisée (ex: 'Europe/Madrid') |
| `t0_local` | TIMESTAMP | Timestamp local du premier event kernel |
| `kernel_keys_json` | VARCHAR | JSON array des event_keys du kernel |
| `pattern` | VARCHAR | Pattern détecté ('single_wave', 'double_wave', 'zigzag', 'unknown') |
| `direction` | INTEGER | Direction initiale (+1, -1, 0) |
| `impact_mfe_pips` | DOUBLE | Maximum Favorable Excursion (pips) |
| `mae_pips` | DOUBLE | Maximum Adverse Excursion (pips) |
| `t_end_local` | TIMESTAMP | Fin du pattern détecté |
| `time_to_peak_min` | INTEGER | Temps jusqu'au pic (minutes) |
| `retracement_pips` | DOUBLE | Retracement depuis pic (pips) |
| `n_swings` | DOUBLE | Nombre total de swings |
| `n_alternances` | DOUBLE | Nombre d'alternances (zigzag) |
| `config_hash` | VARCHAR | Hash SHA256 de la configuration |
| `config_json` | VARCHAR | Configuration JSON complète |
| `created_at` | TIMESTAMP | Timestamp de création (auto) |

---

## 🚀 Utilisation

### Commande de base

```bash
# Générer pour 5 ans glissants (défaut)
python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --years 5

# Générer pour une plage spécifique
python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --start 2025-08-01 --end 2025-09-11

# Mode test (dry-run, n'écrit pas dans la DB)
python research/build_pattern_truth_v4.py --db data/warehouse.duckdb --years 5 --dry-run
```

### Arguments CLI

| Argument | Type | Défaut | Description |
|----------|------|--------|-------------|
| `--db` | string | `data/warehouse.duckdb` | Chemin vers warehouse.duckdb |
| `--start` | string | None | Date début (YYYY-MM-DD) |
| `--end` | string | None | Date fin (YYYY-MM-DD) |
| `--years` | int | 5 | Années glissantes (si --start/--end non spécifiés) |
| `--dry-run` | flag | False | Mode test (pas d'écriture DB) |

---

## 📝 Exemples d'utilisation

### Exemple 1 : Générer uniquement 2 dates panel

```bash
python research/build_pattern_truth_v4.py \
    --db data/warehouse.duckdb \
    --start 2025-08-01 \
    --end 2025-09-11
```

**Sortie attendue :**
```
================================================================================
BUILD PATTERN TRUTH V4
================================================================================
📁 DB: /path/to/data/warehouse.duckdb
📅 Start: 2025-08-01
📅 End: 2025-09-11
🧪 Dry-run: False
================================================================================

📋 Création table si nécessaire...
✅ Table OK

⚙️  Configuration hash: a1b2c3d4e5f6g7h8

📅 Détermination plage de dates...
✅ 2 dates à traiter
   Première: 2025-08-01
   Dernière: 2025-09-11

🔄 Traitement des dates...

✅ Transaction commitée

================================================================================
📊 STATISTIQUES FINALES
================================================================================
Total dates:     2
✅ Success:      2
⏭️  Skipped:      0
❌ Erreurs:       0
================================================================================

📋 Total lignes dans daily_pattern_truth_v4: 2
```

### Exemple 2 : Générer sur 5 ans

```bash
python research/build_pattern_truth_v4.py \
    --db data/warehouse.duckdb \
    --years 5
```

**Note :** Cela peut prendre 10-30 minutes selon le nombre de dates avec événements.

### Exemple 3 : Mode dry-run (test)

```bash
python research/build_pattern_truth_v4.py \
    --db data/warehouse.duckdb \
    --start 2025-08-01 \
    --end 2025-09-11 \
    --dry-run
```

**Sortie :** Identique mais avec `🧪 Mode dry-run: transaction annulée` et pas d'écriture dans la DB.

---

## 🔍 Vérification des résultats

### Requête SQL de base

```sql
-- Compter lignes
SELECT COUNT(*) as total_days
FROM daily_pattern_truth_v4;

-- Distribution des patterns
SELECT 
    pattern,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM daily_pattern_truth_v4
GROUP BY pattern
ORDER BY count DESC;

-- Top 10 jours par impact MFE
SELECT 
    date_local,
    pattern,
    impact_mfe_pips,
    direction,
    kernel_keys_json
FROM daily_pattern_truth_v4
ORDER BY impact_mfe_pips DESC
LIMIT 10;

-- Vérifier dates panel
SELECT 
    date_local,
    pattern,
    impact_mfe_pips,
    time_to_peak_min,
    kernel_keys_json
FROM daily_pattern_truth_v4
WHERE date_local IN ('2025-08-01', '2025-09-11')
ORDER BY date_local;
```

### Requête avec JSON parsing (kernel_keys)

```sql
-- Extraire kernel_keys depuis JSON
SELECT 
    date_local,
    pattern,
    impact_mfe_pips,
    JSON_EXTRACT(kernel_keys_json, '$') as kernel_keys
FROM daily_pattern_truth_v4
WHERE date_local = '2025-08-01';
```

### Statistiques par pattern

```sql
SELECT 
    pattern,
    COUNT(*) as count,
    AVG(impact_mfe_pips) as avg_mfe_pips,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY impact_mfe_pips) as median_mfe_pips,
    PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY impact_mfe_pips) as p80_mfe_pips,
    AVG(time_to_peak_min) as avg_time_to_peak,
    AVG(n_alternances) as avg_alternances
FROM daily_pattern_truth_v4
WHERE pattern != 'unknown'
GROUP BY pattern
ORDER BY count DESC;
```

---

## 🧪 Tests

### Test smoke (minimal)

```bash
# Exécuter le test
python research/tests/test_build_pattern_truth_v4_smoke.py
```

**Vérifications :**
- ✅ 2 dates traitées (2025-08-01, 2025-09-11)
- ✅ 2 lignes existent dans `daily_pattern_truth_v4`
- ✅ `pattern` n'est pas NULL

### Test manuel rapide

```bash
# 1. Générer 2 dates
python research/build_pattern_truth_v4.py \
    --db data/warehouse.duckdb \
    --start 2025-08-01 \
    --end 2025-09-11

# 2. Vérifier avec SQL
python3 << 'EOF'
import duckdb
conn = duckdb.connect('data/warehouse.duckdb', read_only=True)

# Vérifier lignes
count = conn.execute("SELECT COUNT(*) FROM daily_pattern_truth_v4").fetchone()[0]
print(f"✅ Lignes: {count}")

# Vérifier patterns non NULL
patterns = conn.execute("""
    SELECT date_local, pattern, impact_mfe_pips 
    FROM daily_pattern_truth_v4 
    WHERE date_local IN ('2025-08-01', '2025-09-11')
    ORDER BY date_local
""").df()

print("\n📊 Résultats:")
print(patterns)

conn.close()
EOF
```

---

## ⚙️ Configuration

Le pipeline utilise la configuration par défaut de `PatternConfig` (voir `research/pattern_labeler_m1.py`).

**Paramètres principaux :**
- `window_before_minutes`: 15 min
- `window_after_minutes`: 180 min
- `smoothing_window`: 5 points
- `kernel_country`: 'US'
- `kernel_window_start_local`: '13:00:00'
- `kernel_window_end_local`: '16:00:00'

**Reproductibilité :**
- Chaque ligne contient `config_hash` (SHA256) et `config_json` (configuration complète)
- Permet de vérifier/reproduire les calculs avec exactement les mêmes paramètres

---

## 🐛 Dépannage

### Erreur : "Table does not exist"

**Solution :** Créer la table d'abord (voir section "Création de la table")

### Erreur : "No kernel events"

**Cause :** Aucun événement kernel trouvé pour cette date (filtre pays/importance/fenêtre horaire).

**Action :** Normal, ces dates sont marquées `skipped` (pas de kernel).

### Erreur : "No M1 prices available"

**Cause :** Pas de données prix M1 pour la fenêtre autour de t0.

**Action :** Normal, ces dates sont marquées `skipped` (pas de prix).

### Performance lente

**Optimisation :** Traitement en transaction (déjà implémenté). Pour très grandes plages, considérer traiter par batch de 100-200 dates.

---

## 📚 Références

### Fichiers

- **SQL table :** `sql/create_daily_pattern_truth_v4.sql`
- **Script CLI :** `research/build_pattern_truth_v4.py`
- **Pattern labeler :** `research/pattern_labeler_m1.py`
- **Tests :** `research/tests/test_build_pattern_truth_v4_smoke.py`

### Tables DB

- **Source prix :** `prices_finnhub_m1`
- **Source événements :** `events_enriched_v1`
- **Sortie :** `daily_pattern_truth_v4`

---

**Auteur :** Documentation technique — 2025-12-13  
**Version :** 1.0  
**Statut :** ✅ VALIDÉ

