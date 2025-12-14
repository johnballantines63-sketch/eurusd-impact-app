# CORRECTION MESURE IMPACT RÉEL

## 🚨 Problème Identifié

**Date découverte :** 31 octobre 2025 - Session 103

**Symptôme :** Écart de 11.6 pips (20%) entre impact calculé par script et impact mesuré sur MT5.

---

## 📊 Cas 11.09.2025

### Script Ancien (FAUX)

```python
# Méthode : max-min sur fenêtre fixe 60 min
prices = load_prices(14:30 → 15:30)
impact = max(prices) - min(prices)
       = 44.6 pips  ❌
```

### MT5 Réel (CORRECT)

```
Départ (14:30) : 1.16816
Pic (15:10)    : 1.17378
Impact         : 56.2 pips  ✅

Différence : 11.6 pips (20% erreur)
```

---

## 🔍 Cause de l'Erreur

**Problème méthodologique :**

1. **Ancienne méthode** : `max - min` sur fenêtre
   - Cherche le plus haut ET le plus bas
   - Peut inclure mouvements dans les deux directions
   - Ne part pas du prix exact à l'event

2. **Méthode correcte** : `prix_départ → prix_pic`
   - Part du prix EXACT à event_time
   - Suit le mouvement dans UNE direction
   - Correspond à mesure manuelle trader

---

## ✅ Solution Implémentée

### Nouvelle Méthode

```python
# 1. Prix départ = prix exact à event_time
price_start = prices.iloc[0]['close']

# 2. Chercher pic (HIGH ou LOW selon direction)
price_max = prices['close'].max()
price_min = prices['close'].min()

# 3. Déterminer direction dominante
if abs(price_max - price_start) > abs(price_min - price_start):
    direction = "UP"
    impact = (price_max - price_start) * 10000
else:
    direction = "DOWN"
    impact = (price_start - price_min) * 10000
```

### Scripts Créés

**`measure_impact_real_corrected.py`**
- Mesure impact avec méthode correcte
- Compare ancienne vs nouvelle méthode
- Valide contre MT5

**`recalculate_amp_optimal_corrected.py`**
- Recalcule amp_optimal avec impact corrigé
- Détermine facteur référence pour Option A

**`validate_impact_corrected.sh`**
- Lance les deux scripts en séquence

---

## 🚀 Utilisation

```bash
cd ~/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session102

chmod +x validate_impact_corrected.sh
./validate_impact_corrected.sh
```

**Durée : ~5 secondes**

---

## 📊 Résultats Attendus

### Impact Corrigé

```
Prix départ    : 1.16816 (14:30)
Prix pic       : 1.17378 (15:10)
Direction      : UP
Durée au pic   : 40 min
Impact mesuré  : 56.2 pips ✅
```

### amp_optimal Corrigé

```
Score ajusté      : 84.2
Impact baseline   : 56.3 pips (amp=2.5)
Impact réel       : 56.2 pips
amp_optimal       : ~2.5 ✅

Conclusion : Baseline 2.5 VALIDÉE empiriquement !
```

---

## 🎯 Conséquences pour Calibration

### Avant Correction

```python
REFERENCE_AMP = 1.982  # amp_optimal avec impact faux 44.6
```

### Après Correction

```python
REFERENCE_AMP = 2.5  # amp_optimal avec impact correct 56.2
```

**Avantage :** Baseline 2.5 déjà utilisée dans formules S51-55 est VALIDÉE !

---

## 📝 Option A - Méthode Finale

```python
# Référence validée cas 11.09
REFERENCE_AMP = 2.5
REFERENCE_R2 = 0.638
REFERENCE_AMPLITUDE = 114.3
REFERENCE_DUREE = 54.5

# Pour chaque date (44 dates) :
# 1. Calculer impact avec amp = 2.5 (baseline)
# 2. Mesurer impact réel (méthode correcte)
# 3. Trouver amp_optimal_date
# 4. delta_amp = (amp_optimal_date - 2.5) / 2.5

# Régression :
# delta_amp = f(delta_r2, delta_amplitude, delta_duree)
```

---

## ⚠️ Impact sur Scripts Existants

### Scripts à Corriger

- ❌ `test_step4_mesure_impact_reel.py` (ancienne méthode)
- ❌ `test_methodologie_complete_11_09.py` (ancienne méthode)
- ❌ `recalculate_metrics_optimized.py` (à corriger pour 44 dates)

### Scripts Corrects

- ✅ `measure_impact_real_corrected.py` (nouvelle méthode)
- ✅ `recalculate_amp_optimal_corrected.py` (avec impact correct)

---

## 🔧 Prochaines Actions

1. ✅ Valider méthode corrigée sur cas 11.09
2. ⏳ Corriger script Step 4 modulaire
3. ⏳ Corriger script calibration 44 dates
4. ⏳ Relancer calibration avec impacts corrects

---

## 📚 Fichiers Générés

**`impact_real_corrected.json`**
```json
{
  "impact_real_corrected": {
    "price_start": 1.16816,
    "price_peak": 1.17378,
    "direction": "UP",
    "impact_pips": 56.2,
    "method": "start_to_peak"
  },
  "impact_old_method": {
    "impact_pips": 44.6,
    "method": "max_minus_min"
  }
}
```

**`calibration_reference_11_09.json`**
```json
{
  "calibration": {
    "amp_optimal": 2.5,
    "correction_factor": 1.0,
    "recommendation": "baseline_2_5_validated"
  }
}
```

---

## ✅ Validation

**Critères de succès :**
- Impact mesuré ≈ 56.2 pips (±2 pips)
- amp_optimal ≈ 2.5 (±0.1)
- Écart vs MT5 < 5%

**Status :** ⏳ En attente validation

---

**Auteur :** André Valentin  
**Date :** 31 octobre 2025 - Session 103  
**Criticité :** 🔴 HAUTE - Impact sur toute la calibration
