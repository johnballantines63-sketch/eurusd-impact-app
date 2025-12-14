# Résumé Investigations - Étapes 1 et 2

**Date** : 1er août 2025  
**Objectif** : Corriger les problèmes identifiés dans les étapes du pipeline

---

## ✅ ÉTAPE 1 : VÉRIFIER POURQUOI LA TENDANCE N'EST PAS DÉTECTÉE

### Problème Identifié

**Erreur** : `Pas assez de données (476 < 1000)`

### Cause

La fonction `detect_trend_by_inversion_s107` requiert **1000 barres minimum** pour M30, mais seulement **476 barres** sont disponibles.

**Détails** :
- Lookback : 14 jours
- Timeframe : M30 (48 barres/jour)
- Barres théoriques : 14 * 48 = 672 barres
- Après filtrage (event - 2h) : **476 barres disponibles**
- Seuil requis : **1000 barres** ❌

### Solution Proposée

**Réduire le seuil pour M30** de 1000 à 400 barres.

**Justification** :
- 476 barres > 400 barres ✅
- 14 jours suffisent pour détecter tendances
- Segments de 12h nécessitent ~24 barres chacun → 14 jours = 28 segments possibles

**Fichier à modifier** : `src/core/trend_detection_pre_event_s107.py`  
**Ligne** : ~95

**Modification** :
```python
# Avant
min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else 1000)

# Après
min_bars = 100 if timeframe == 'H1' else (500 if timeframe == 'M15' else (400 if timeframe == 'M30' else 1000))
```

---

## ✅ ÉTAPE 2 : ANALYSER POURQUOI AMPLIFICATION EST 1.0x AU LIEU DE 0.246x

### Problème Identifié

**Observation** :
- Log montre : `"RF par date (fallback moyenne): 0.246x"` ✅
- Mais `amplification_predite` reste à **1.0x** ❌
- Prédiction finale : **250.82 pips** (sans application de l'amplification)

### Cause Probable

L'amplification **0.246x est calculée correctement** (ligne 1077), mais :

1. **Soit** elle n'est pas appliquée dans le calcul final
2. **Soit** elle est écrasée par une valeur par défaut
3. **Soit** le calcul de `prediction_finale` utilise directement `impact_base` sans appliquer l'amplification

### Code Concerné

**Fichier** : `scripts/run_pipeline_complete.py`

**Lignes 1072-1079** : Calcul de l'amplification
```python
if num_clusters >= 5 and results_df is not None:
    try:
        if 'amplification_parfaite' in results_df.columns:
            amplification_predite = results_df['amplification_parfaite'].mean()  # ✅ 0.246x
            amplification_method = 'rf_per_date_fallback_mean'
            self._log(f"   ℹ️ RF par date (fallback moyenne): {amplification_predite:.3f}x", "INFO")
```

**Ligne 1064** : Initialisation (par défaut 1.0)
```python
amplification_predite = 1.0  # ⚠️ Valeur par défaut
amplification_method = 'default'
```

### Points à Vérifier

1. ✅ **Vérifier si `amplification_predite` est bien mis à jour** à 0.246x
2. ⏭️ **Vérifier où `prediction_finale` est calculée** et si elle utilise `amplification_predite`
3. ⏭️ **Vérifier si l'amplification est écrasée** après le calcul

### Action Immédiate

**Vérifier le calcul de `prediction_finale`** dans l'étape 8 (lignes ~1725-1750).

**Hypothèse** : `prediction_finale = impact_base * amplification_predite * adjustment_factor`, mais l'amplification n'est pas appliquée car le pattern prend le dessus.

---

## 📋 PROCHAINES ÉTAPES

### Correction Étape 1

1. ✅ Modifier `trend_detection_pre_event_s107.py` pour réduire le seuil M30
2. ⏭️ Tester la détection de tendance avec le nouveau seuil
3. ⏭️ Vérifier que R² est maintenant détecté pour le 1er août

### Correction Étape 2

1. ⏭️ Vérifier où `prediction_finale` est calculée
2. ⏭️ S'assurer que `amplification_predite` est bien appliquée
3. ⏭️ Corriger le calcul si nécessaire

---

**Status** : 
- ✅ Étape 1 : Problème identifié - Solution proposée
- ⏭️ Étape 2 : Investigation en cours - Vérification nécessaire




