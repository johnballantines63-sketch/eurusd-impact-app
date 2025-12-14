# Pack Final V7/V8 - Validation & Stratification

## ✅ V7 - FREEZE - Baseline Officielle

### Ce qui est définitivement figé

#### Logique Patterns
- ✅ `_find_turning_points` en seuil constant `TURN_PIPS_BASE = 10`
- ✅ Nettoyage adaptatif dans `_analyze_turning_points_sequence`
- ✅ `pattern_meta` complet + propagé + exporté CSV
- ✅ Fix structurel : min/max entre peaks pour retrace (pas troughs baseline-centric)
- ✅ Nettoyage turning points alternés pour éviter bruit → zig_zag

#### TURN_PIPS Adaptatif
- ✅ Dépendance à leg1-only confirmée par `impact_total_pips_used`
- ✅ Formule : `TURN_PIPS = max(8.0, min(12.0, 0.15 * impact_total_pips))`
- ✅ Floor = comportement normal tant que leg1 < 53.3 pips
- ✅ Audit OK via `turn_pips_used` + `impact_total_pips_used` + alias

#### Ratios
- ✅ Empirique : 39.2% / 60.8%
- ✅ Écart 0.8% → prior Session 64 (40/60) validé
- ✅ Stable double_wave vs zig_zag

#### Résultats V7
- **153 triggers** (tradable + triggers)
- **35 multi-waves détectés** (6 double_wave + 29 zig_zag)
- **9 multi-waves uniques** (2 double_wave + 7 zig_zag)
- **N = 9 < 30** → Stratification descriptive seulement

---

## 🎯 V8 - Objectif Unique Prioritaire

**Augmenter N multi-wave uniques à ≥30**

Tout le reste dépend de ça. Sans N, pas de vraie stratification.

---

## 🧱 Comment Générer MOVEMENTS_FILE Pré-2024

### Stratégie Robuste

**Rejouer exactement la même logique de détection movements que pour 2024-2025, mais sur l'historique prix complet.**

### Pipeline

1. **Source events**
   - Table `events` (ou CSV events si disponible)
   - Pour chaque event : `baseline_time`, window d'analyse (ex. 0 → +60min)

2. **Source prix**
   - Table prix historique (M1)
   - Si la DB n'a pas les prix : loader externe identique au process actuel

3. **Reconstruction movement**
   - Réutiliser la fonction existante qui génère MOVEMENTS_FILE (ou la factoriser)
   - Output même schéma exact que fichier actuel :
     - `movement_start_time`, `baseline_price`, `impact_pips`, `direction`, ...
   - Injecter dans `scan_patterns_historique_complet.py` sans toucher le reste

4. **Validation rapide**
   - Comparer distributions 2024-2025 reconstruits vs MOVEMENTS_FILE actuel
   - Si match → OK pour pré-2024

### Pourquoi c'est Safe

- ✅ Tu ne modifies pas la logique V7
- ✅ Tu étends juste la matière première
- ✅ Reproductibilité garantie

---

## 📋 Checklist V8 Immédiate

### Étape 1 - Reconstruire MOVEMENTS_FILE Pré-2024

- [ ] Identifier source events historique (table `events` ou CSV)
- [ ] Identifier source prix historique (table prix M1 ou loader externe)
- [ ] Factoriser fonction génération MOVEMENTS_FILE (si pas déjà fait)
- [ ] Générer MOVEMENTS_FILE pré-2024 avec même schéma
- [ ] Valider distributions 2024-2025 reconstruits vs actuel

### Étape 2 - Re-scanner avec Historique Étendu

- [ ] Lancer `scan_patterns_historique_complet.py --min-date 2018-01-01 --max-date 2025-12-31`
- [ ] Vérifier N uniques multi-wave ≥ 30
- [ ] Vérifier que patterns détectés sont cohérents

### Étape 3 - Vérifier TURN_PIPS Adaptatif

- [ ] Compter cas avec `turn_pips_used > 8.0`
- [ ] Si > 20% des multi-waves avec TURN_PIPS > 8 → adaptatif "vivant"
- [ ] Analyser distribution TURN_PIPS (mean, std, range)

### Étape 4 - Recalibrage Bootstrap

- [ ] Lancer `recalibrate_ratios_bootstrap.py`
- [ ] Vérifier ratios globaux (median Leg1/Leg2)
- [ ] Comparer avec prior Session 64 (40/60)
- [ ] Si écart > 10% → update prior

### Étape 5 - Stratification

- [ ] Lancer `stratify_ratios_v8.py`
- [ ] Vérifier buckets avec `robustness='final'` (N≥30)
- [ ] Analyser ratios par bucket
- [ ] Décider si utiliser ratios bucketés ou globaux

### Étape 6 - Validation Finale

- [ ] Vérifier cohérence entre buckets
- [ ] Tester sur échantillon de validation
- [ ] Documenter décisions (ratios globaux vs bucketés)

---

## 📊 Critères de Décision V8

### Recalibrage Global

**Si médiane Leg1 ou Leg2 dérive de >10% relatif vs prior** :
- → Update prior
- Sinon → Conserver prior Session 64 (40/60)

### Recalibrage Bucket

**Seulement buckets `robustness='final'`** :
- Si écart bucket vs global > 10% → utiliser ratio bucket
- Sinon → conserver prior global

### TURN_PIPS

**Check proportion de cas sortant du floor** :
- Si >20% des multi-waves avec TURN_PIPS > 8
- → Adaptatif "vivant" sur divers régimes
- → Design validé empiriquement

---

## 🧪 Script Stratification V8

**Fichier** : `scripts/stratify_ratios_v8.py`

**Fonctionnalités** :
- Stratification par cluster_type, strength, pattern, direction
- Combo bucket (cluster × strength × pattern)
- Tag robustness (descriptive_only / bootstrap_ok / final)
- Export CSV par axe de stratification

**Usage** :
```bash
python3 scripts/stratify_ratios_v8.py
```

**Outputs** :
- `outputs/direction_router_test/v8_stratification/by_cluster.csv`
- `outputs/direction_router_test/v8_stratification/by_strength.csv`
- `outputs/direction_router_test/v8_stratification/by_pattern.csv`
- `outputs/direction_router_test/v8_stratification/by_direction.csv`
- `outputs/direction_router_test/v8_stratification/combo.csv`

**Résultats Actuels (N=9)** :
- ✅ Script fonctionnel
- ⚠️ Buckets avec N<5 filtrés (strength, combo)
- ⚠️ Tous buckets en `descriptive_only` (N<30)
- ✅ Prêt à tourner dès N≥30

---

## 📌 Tableau Brut 9 Uniques (Base V8)

**Fichier** : `outputs/direction_router_test/multi_wave_uniques_v7.csv`

**Stats** :
- Impact total : 57.6 - 72.9 pips (mean: 64.9)
- Impact used (leg1-only) : 38.9 - 48.7 pips (mean: 43.5)
- Strength : 1.06 - 2.34 (median: 1.51)
- Leg1 ratio : 38.2% - 39.2% (median: 39.2%)
- Leg2 ratio : 60.8% - 61.8% (median: 60.8%)

**Distribution** :
- CPI : 5 cas
- Jobs : 3 cas
- CPI+Jobs : 1 cas
- Double-wave : 2 cas
- Zig-zag : 7 cas
- DOWN : 6 cas
- UP : 3 cas

---

## ✅ Statut Final

- **V7** : ✅ **FREEZE - Baseline officielle**
- **V8** : ✅ **Plan prêt - Script stratification créé et testé**
- **Prochaine étape** : Générer MOVEMENTS_FILE pré-2024

---

## 📚 Documentation Associée

- `SYNTHESE_FINALE_V7.md` : Synthèse complète V7
- `SYNTHESE_FINALE_V7_COPIE_COLLER.md` : Version copier-coller
- `RESUME_CORRECTIONS_FINALES.md` : Résumé corrections finales
- `PLAN_STRATIFICATION_V8.md` : Plan détaillé stratification V8
- `V8_CHECKLIST.md` : Checklist V8 détaillée
- `V7_FINAL_CHECKLIST.md` : Checklist validation V7

---

**Version** : V7/V8 Final Pack
**Date** : 2025-01-XX
**Status** : ✅ **V7 FREEZE - V8 PRÊT**

