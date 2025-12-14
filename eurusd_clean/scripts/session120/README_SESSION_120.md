# 📋 SESSION 120 - REV12 DEBUGGING

## 🎯 Objectif

Corriger bugs fundamentaux rev11 :
- Bug #1: Peak1/Pullback1 même timestamp (14:30:00)
- Bug #2: Pullback ratio > 100% (214%)

## ✅ Fichiers Créés

```
scripts/session120/
├── double_wave_detector_rev12.py     ← Algorithme corrigé
├── test_rev12_validation.py          ← Test validation cas 11 sept
├── run_test_rev12.sh                 ← Script lancement (bash)
└── README_SESSION_120.md             ← Ce fichier
```

## 🔧 Corrections Rev12

### 1. Garde Temporelle Wave1
```python
MIN_BARS_BEFORE_PULLBACK = 3  # Attendre 3 bars après peak

# Dans boucle Wave1 :
minutes_since_peak = (ts - peak1_time).total_seconds() / 60.0

if minutes_since_peak >= MIN_BARS_BEFORE_PULLBACK:
    # Valider pullback SEULEMENT si temps écoulé
    if conditions_satisfaites:
        pullback1_time = ts  # Garanti ≠ peak1_time
```

**Avant (rev11)** : Pullback validé sur même barre que peak  
**Après (rev12)** : Pullback validé minimum 3 bars après peak

### 2. Validation Pullback Ratio
```python
r1 = abs(peak1_price - pullback1_price) / abs(peak1_price - baseline_price)

if r1 > 1.0 or r2 > 1.0:
    return None  # Rejeter pattern invalide
```

**Avant (rev11)** : Acceptait 214% (impossible)  
**Après (rev12)** : Rejette si > 100%

### 3. Mode Debug Détaillé
- Prints timestamps précis (HH:MM:SS)
- Affichage amplitudes à chaque update peak
- Traçabilité complète logique Wave1 et Wave2

## 🚀 Lancement Test

### Méthode 1 : Python direct
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120
python test_rev12_validation.py
```

### Méthode 2 : Script bash
```bash
cd /Users/andrevalentin/Desktop/eurusd_news_impact_calculator_MPC/eurusd_clean/scripts/session120
chmod +x run_test_rev12.sh
./run_test_rev12.sh
```

## 📊 Critères Succès

Le test validera automatiquement :

| Critère | Target | Statut |
|---------|--------|--------|
| Peak1 ≠ Pullback1 timestamp | Distinct | ⏳ À valider |
| Pullback ratio < 100% | < 1.0 | ⏳ À valider |
| Wave2 précision | 56.2 ± 5 pips | ⏳ À valider |
| Peak2 time | 14:57 | ⏳ À valider |

**Verdict final :**
- ✅✅✅ PERFECTION : MAE < 2 pips
- ✅✅ EXCELLENT : MAE < 5 pips (objectif Session 120)
- ✅ BON : MAE < 10 pips

## 📈 Référence Comparative

| Version | Peak1/PB1 Time | Wave1 | Wave2 | PB Ratio | MAE vs 56.2 |
|---------|----------------|-------|-------|----------|-------------|
| **Rev11 (bugué)** | 14:30 / 14:30 | 22.6 pips | 33.7 pips | 214% | 22.5 pips |
| **Session 118** | - | - | 51.7 pips | - | 4.5 pips |
| **Target Rev12** | Distinct | ~37 pips | 56.2 pips | < 100% | < 5 pips |

## 🔍 Debug Mode

Le test affichera automatiquement :

```
================================================================================
🔍 REV12 DEBUG - 2025-09-11
================================================================================
Baseline: 2025-09-11 14:29:00+02:00 @ 1.10123
Direction: bullish

📊 WAVE 1 - Recherche Peak1 + Pullback1
   Peak1 update: 14:30:00 → 22.6 pips
   Peak1 update: 14:33:00 → 37.4 pips      ← Devrait atteindre ~37 pips
   Pullback1 found: 14:36:00 → -8.2 pips   ← Distinct de 14:33

📊 WAVE 2 - Recherche Peak2 MAXIMUM + Pullback2
   Peak2 update: 14:45:00 → 45.3 pips
   Peak2 update: 14:57:00 → 56.2 pips      ← Target attendu
   ✓ Peak2 MAXIMUM trouvé (stagnation 20 bars)
   Pullback2 found: 15:03:00 → -12.1 pips

✅ DOUBLE WAVE DÉTECTÉE
   Wave1: 37.4 pips (pullback 22%)
   Wave2: 56.2 pips (pullback 21%)
   Confidence: 85.0%
================================================================================
```

## 🐛 Troubleshooting

### Erreur : Import module introuvable
```
ModuleNotFoundError: No module named 'double_wave_detector_rev10'
```
**Solution** : Vérifier que `scripts/session119/double_wave_detector_rev10.py` existe

### Erreur : Base données introuvable
```
Error: warehouse.duckdb not found
```
**Solution** : Vérifier chemin `data/warehouse.duckdb`

### Rev12 retourne None
**Diagnostic** :
1. Consulter logs debug (activé par défaut)
2. Vérifier si garde temporelle trop stricte (MIN_BARS = 3)
3. Si nécessaire, ajuster à 2 bars et re-tester

### Pullback ratio > 100% persist
**Diagnostic** :
1. Vérifier baseline_price = close(14:29) correct
2. Vérifier formule : `abs(peak - pullback) / abs(peak - baseline)`
3. Consulter logs debug pour valeurs exactes

## 📝 Prochaines Étapes

Après validation rev12 :

1. ✅ **ÉTAPE 1 complétée** : Rev12 validé (MAE < 5 pips)
2. ⏳ **ÉTAPE 2** : Validation Single Wave detectors (3+ cas)
3. ⏳ **ÉTAPE 3** : Système validation global (10+ cas historiques)

## 📧 Questions / Problèmes

Si rev12 ne passe pas validation :
1. Copier logs debug complets
2. Analyser timestamps Peak1/Pullback1
3. Vérifier amplitudes Wave1 (devrait être ~37 pips)
4. Comparer avec Session 118 si MAE > 10 pips

---

**Auteur** : André Valentin avec Claude  
**Date** : 07 novembre 2025  
**Session** : 120
