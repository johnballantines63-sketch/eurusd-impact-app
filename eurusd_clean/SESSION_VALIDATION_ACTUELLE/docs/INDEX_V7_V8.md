# Index V7/V8 - Référence Rapide

## 📁 Fichiers Créés

### Scripts
- **`scripts/stratify_ratios_v8.py`** (7.5K)
  - Script de stratification V8
  - Prêt à utiliser dès N≥30
  - Testé avec N=9 : ✅ fonctionnel

### Documentation
- **`docs/V8_CHECKLIST.md`** (5.4K)
  - Checklist complète V8 étape par étape
  - Critères de décision
  - Pipeline reconstruction MOVEMENTS_FILE

- **`docs/V7_V8_FINAL_PACK.md`** (6.5K)
  - Synthèse complète V7/V8
  - Statut freeze V7
  - Plan V8 détaillé

- **`docs/INDEX_V7_V8.md`** (ce fichier)
  - Index de référence rapide

## ✅ Statut V7

**FREEZE - Baseline officielle**

### Points Clés
- Logique patterns : Fix structurel min/max entre peaks ✅
- TURN_PIPS adaptatif : Floor 8.0 validé ✅
- Ratios : 39.2% / 60.8% (prior 40/60 validé) ✅
- Résultats : 9 multi-waves uniques (N<30)

## 🎯 Statut V8

**PRÊT - Script stratification créé et testé**

### Objectif Unique
**Augmenter N multi-wave uniques à ≥30**

### Prochaine Étape
**Générer MOVEMENTS_FILE pré-2024**

### Scripts Disponibles
- ✅ `generate_movements_historical_v8.py` : Génération MOVEMENTS_FILE pré-2024
- ✅ `stratify_ratios_v8.py` : Stratification ratios (N≥30)
- ✅ `recalibrate_ratios_bootstrap.py` : Recalibrage bootstrap
- ✅ `scan_patterns_historique_complet.py` : Scan historique complet

## 📊 Résultats Actuels (N=9)

### Buckets Générés
- `by_cluster` : CPI (N=5, Leg1=38.7%, Leg2=61.3%)
- `by_pattern` : zig_zag (N=7, Leg1=39.2%, Leg2=60.8%)
- `by_direction` : DOWN (N=6, Leg1=39.0%, Leg2=61.0%)

### Robustness
- Tous buckets : `descriptive_only` (N<30, normal)

## 🚀 Commandes Rapides

### Générer MOVEMENTS_FILE Historique
```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 generate_movements_historical_v8.py
```

### Re-scanner Historique Étendu
```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 scan_patterns_historique_complet.py \
  --min-date 2018-01-01 \
  --max-date 2025-12-31
```

### Lancer Stratification V8
```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 stratify_ratios_v8.py
```

### Recalibrage Bootstrap
```bash
cd SESSION_VALIDATION_ACTUELLE/scripts
python3 recalibrate_ratios_bootstrap.py
```

## 📚 Documentation Complète

### V7
- `SYNTHESE_FINALE_V7.md` : Synthèse complète
- `SYNTHESE_FINALE_V7_COPIE_COLLER.md` : Version copier-coller
- `RESUME_CORRECTIONS_FINALES.md` : Résumé corrections
- `V7_FINAL_CHECKLIST.md` : Checklist validation V7

### V8
- `V8_CHECKLIST.md` : Checklist V8 détaillée
- `PLAN_STRATIFICATION_V8.md` : Plan détaillé stratification
- `V7_V8_FINAL_PACK.md` : Pack final V7/V8

## 🔍 Fichiers de Données

### Inputs
- `scripts/outputs/direction_router_test/patterns_detected.csv`
  - Résultats scan historique complet
  - Contient `movement_start_time`, `pattern_meta`, etc.
  - ⚠️ Chemin relatif au script (lancer depuis `scripts/`)

### Outputs V8
**Chemin réel** : `scripts/outputs/direction_router_test/v8_stratification/`

⚠️ **Important** : Lancer depuis `scripts/` pour que les chemins soient corrects.

- `scripts/outputs/direction_router_test/v8_stratification/by_cluster.csv`
- `scripts/outputs/direction_router_test/v8_stratification/by_strength.csv`
- `scripts/outputs/direction_router_test/v8_stratification/by_pattern.csv`
- `scripts/outputs/direction_router_test/v8_stratification/by_direction.csv`
- `scripts/outputs/direction_router_test/v8_stratification/combo.csv`

### Base V8
- `scripts/outputs/direction_router_test/multi_wave_uniques_v7.csv`
  - 9 multi-waves uniques (base pour V8)

---

**Version** : Index V7/V8
**Date** : 2025-01-XX
**Status** : ✅ **V7 FREEZE - V8 PRÊT**

