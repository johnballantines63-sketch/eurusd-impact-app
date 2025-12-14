# Runbook V8 - Extension Historique & Stratification

## Ordre Strict d'Exécution

### Étape 1 - Générer l'Historique Movements

```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 generate_movements_historical_v8.py
```

**Résultat attendu** :
- Fichier créé : `scripts/outputs/direction_router_test/movements_historical.csv`
- Bloc validation : "Drift median: X%"

**Vérifications** :
- ✅ DB_PATH trouvé (affiché au début)
- ✅ Tables events et prix détectées
- ✅ Movements générés > 0

---

### Étape 2 - Interpréter la Validation

#### Si drift < 10% ✅
→ **Safe-replay OK, on continue.**

#### Si drift ≥ 10% ⚠️
→ **Remplacer `compute_movement()` par la logique V7 exacte**

**Action** :
1. Identifier fonction exacte qui génère MOVEMENTS_FILE actuel
2. Remplacer `compute_movement()` dans `generate_movements_historical_v8.py`
3. Relancer génération
4. Re-valider

---

### Étape 3 - Injecter dans le Scan Historique

**Option A - Copie/Renomme (sans toucher code)** :
```bash
cp scripts/outputs/direction_router_test/movements_historical.csv \
   scripts/outputs/all_movements_detected.csv
```

**Option B - Ajuster constante MOVEMENTS_FILE** :
Modifier temporairement `MOVEMENTS_FILE` dans `scan_patterns_historique_complet.py` :
```python
MOVEMENTS_FILE = Path(__file__).parent / 'outputs' / 'direction_router_test' / 'movements_historical.csv'
```

---

### Étape 4 - Lancer le Scan 2018-2025

```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 scan_patterns_historique_complet.py \
  --min-date 2018-01-01 \
  --max-date 2025-12-31
```

**Résultat attendu** :
- Fichier : `outputs/direction_router_test/patterns_detected.csv`
- Patterns détectés : double_wave, zig_zag, single_wave

---

### Étape 5 - Vérifier N Multi-Wave Uniques

```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 - <<'EOF'
import pandas as pd
df = pd.read_csv('outputs/direction_router_test/patterns_detected.csv')
mw = df[df.pattern_type.isin(['double_wave','zig_zag'])].drop_duplicates('date')
print("N multi-wave uniques =", len(mw))
print("\nPar pattern:")
print(mw.pattern_type.value_counts())
print("\nPar cluster:")
print(mw.cluster_type.value_counts())
EOF
```

**Critère de succès** :
- **N ≥ 30** → V8 "vivante", passer à Étape 6
- **N < 30** → Étendre période ou vérifier données

---

### Étape 6 - Si N ≥ 30 → V8 "Vivante"

#### 6.1 Recalibrage Bootstrap

```bash
python3 recalibrate_ratios_bootstrap.py
```

**Résultat attendu** :
- Ratios globaux recalculés (median Leg1/Leg2)
- Comparaison avec prior Session 64 (40/60)
- CI bootstrap si N suffisant

#### 6.2 Stratification

```bash
python3 stratify_ratios_v8.py
```

**Résultat attendu** :
- Buckets générés dans `outputs/direction_router_test/v8_stratification/`
- Tags robustness : `final` (N≥30), `bootstrap_ok` (N≥10), `descriptive_only` (N≥5)

#### 6.3 Décision Ratios

**Critères** :
- Si médiane Leg1/Leg2 dérive >10% vs prior → Update prior
- Si buckets `robustness='final'` avec écart >10% vs global → Utiliser ratio bucket
- Sinon → Conserver prior Session 64 (40/60)

---

## Troubleshooting

### DB_PATH introuvable

**Symptôme** : `❌ DB introuvable: ...`

**Solution** :
1. Vérifier chemin affiché au début du script
2. Ajuster `ROOT_DIR` dans `generate_movements_historical_v8.py` :
   ```python
   # Essayer :
   ROOT_DIR = SCRIPT_DIR.parent  # ou
   ROOT_DIR = SCRIPT_DIR.parent.parent
   ```

### Aucune table events/prix trouvée

**Symptôme** : `❌ Aucune table events trouvée`

**Solution** :
1. Vérifier tables disponibles :
   ```python
   import duckdb
   conn = duckdb.connect("path/to/warehouse.duckdb", read_only=True)
   print(conn.execute("SHOW TABLES").df())
   ```
2. Ajuster candidats dans `find_table()` si nécessaire

### Drift ≥ 10%

**Symptôme** : `⚠️ Drift >= 10% → remplacer compute_movement()`

**Solution** :
1. Identifier fonction exacte V7 (chercher dans codebase)
2. Remplacer `compute_movement()` dans script
3. Relancer génération

### N < 30 après scan étendu

**Symptôme** : N multi-wave uniques < 30

**Solutions** :
- Vérifier période données disponibles
- Vérifier filtres dans `scan_patterns_historique_complet.py`
- Étendre période si données disponibles

---

## Checklist Complète

- [ ] Étape 1 : Movements historiques générés
- [ ] Étape 2 : Validation drift < 10% (ou compute_movement() remplacé)
- [ ] Étape 3 : Movements injectés dans scan
- [ ] Étape 4 : Scan 2018-2025 lancé
- [ ] Étape 5 : N multi-wave uniques ≥ 30 vérifié
- [ ] Étape 6.1 : Recalibrage bootstrap lancé
- [ ] Étape 6.2 : Stratification lancée
- [ ] Étape 6.3 : Décision ratios prise

---

---

## Addendum V8 Final - Paramètres & Décisions

### Paramètres V8 Figés

**Stats Map** :
- Période : 2022-01-01 → 2025-12-31
- Format clé : `normalize_event_key(event_key) + "_" + country`
- Normalisation cohérente via `normalize_event_key()` dans construction et lookup

**Matching Events** :
- Fenêtre : journée complète (full-day matching)
- Au lieu de : fenêtre [-4h, +30min] autour du mouvement

**Movements File** :
- Fallback automatique vers `movements_historical.csv` si présent
- Contient période 2022-2025 (replay V7 strict validé)

### Décision Ratios Finale

**Prior maintenu : 40/60 (Session 64)**

**Justification** :
- Écart empirique vs prior : 1% (< 10% seuil)
- Ratios globaux : Leg1=39.1%, Leg2=60.9% (médiane)
- Tous buckets "final" (N≥30) cohérents avec global :
  - Jobs (N=40) : 39.2% / 60.8%
  - zig_zag (N=71) : 39.2% / 60.8%
  - DOWN (N=40) : 39.2% / 60.8%
  - UP (N=42) : 39.0% / 61.0%
- Aucun bucket ne justifie override (drift <10% partout)

**Conclusion** : Prior 40/60 confirmé empiriquement sur horizon étendu (2022-2025), stratification informative (robustesse universelle) mais pas prescriptive (aucun override).

---

## Notes Git / Tagging

### Tags Annotés (V8)

Le tag `v8-historical-replay-final` est un **tag annoté** (annotated tag).

**Comportement normal** :
- `git rev-parse v8-historical-replay-final` → SHA de l'objet tag (intermédiaire)
- `git rev-list -n 1 v8-historical-replay-final` → SHA du commit pointé (réel)
- `git show v8-historical-replay-final` → Affiche le commit pointé (60883f6)

**Vérification** :
```bash
HEAD_SHA=$(git rev-parse HEAD)
TAG_SHA=$(git rev-list -n 1 v8-historical-replay-final)
[ "$HEAD_SHA" = "$TAG_SHA" ] && echo "✅ Tag aligné" || echo "❌ Problème"
```

**Push** :
```bash
git push origin main
git push origin v8-historical-replay-final
```

---

**Version** : V8 Runbook Final
**Date** : 2025-01-XX
**Status** : ✅ **FINALISÉ - V8 READY**

