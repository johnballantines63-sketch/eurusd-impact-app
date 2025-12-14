# Session 98 - Test Baseline V2.4

## 🎯 Objectif

Valider Baseline V2.4 sur 10 dates CPI en répliquant EXACTEMENT la méthodologie (pas améliorer).

## 📁 Fichiers

- `test_baseline_v2_4_multi_dates.py` - Script principal
- `test_validation_11sept.py` - Validation conformité rapide
- `scan_cpi_dates.py` - Scanner dates CPI (optionnel)
- `results_v2_4.csv` - Résultats (généré)

## 🚀 Utilisation

### 1. Validation Conformité (11 septembre)

**OBLIGATOIRE AVANT TESTS MULTI-DATES**

```bash
cd eurusd_clean/scripts/session98
python3 test_validation_11sept.py
```

**Résultat attendu :** MAE < 1 pip

Si MAE > 1 pip → STOP et analyser différences

### 2. Scan Dates CPI Disponibles

```bash
python3 test_baseline_v2_4_multi_dates.py --scan
```

### 3. Test Single Date

```bash
python3 test_baseline_v2_4_multi_dates.py --date 2025-09-11
```

### 4. Test Multi-Dates (AUTO)

**Mode principal - Test automatique 10 dates**

```bash
python3 test_baseline_v2_4_multi_dates.py --auto --output results_v2_4.csv
```

Résultats sauvegardés dans `results_v2_4.csv`

## 📊 Critères Succès

- ✅ MAE global < 10 pips : **EXCELLENT**
- ⚠️ MAE global 10-15 pips : Acceptable, investiguer limites
- ❌ MAE global > 15 pips : Problème, analyser causes

## ⚠️ Points Critiques

### Pullback Hardcodé

Le script réplique le bug V2.4 :

```python
pullback = calculate_pullback_v2(37.4, 10, 15)  # VALEURS FIXES
```

**Pas de correction** - Tester tel quel puis analyser impact.

### Timezone

- events.ts_utc : UTC+2 (Bern)
- prices_1m.datetime : UTC+2 (Bern)
- **PAS de conversion**

### Formules

Toutes issues de `fx_impact_app/src/formulas_validated.py` :
- calculate_adjusted_empirical_score() (S55)
- calculate_impact_d() (S51) - amplification 2.5
- calculate_ttr_c() (S52)
- calculate_pullback_v2() (S53)

## 📋 Checklist Conformité

- [ ] Query SQL identique
- [ ] Calcul surprise avec estimate
- [ ] Ajustement score zones (5%, 15%, 30%)
- [ ] Impact amplification 2.5 fixe
- [ ] Correction 0.758
- [ ] TTR multipliers 3.0, 2.5, 2.0
- [ ] Pullback hardcodé (37.4, 10, 15)
- [ ] Colonne datetime (pas timestamp)
- [ ] Timezone UTC+2 sans conversion
- [ ] Test 11 sept MAE < 1 pip

## 📖 Références

- Session 97 - PLANIFICATEUR_V2.4_METHODOLOGIE_EXACTE.md
- Session 97 - COMPARAISON_APPROCHES_AMPLIFICATION.md
- formulas_validated.py (v1.1)
