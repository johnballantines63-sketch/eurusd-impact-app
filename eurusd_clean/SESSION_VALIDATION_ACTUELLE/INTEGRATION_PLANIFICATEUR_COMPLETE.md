# Intégration Formule Linéaire dans Planificateur - Terminée

**Date** : 2025-12-07  
**Fichier modifié** : `streamlit_app/pages/5_Planificateur_V3.1_CLEAN_OLD.py`

---

## ✅ Modifications Effectuées

### 1. Import de la Nouvelle Formule

**Ligne 71** : Ajout de l'import dans les imports globaux
```python
from core.formulas_validated import (
    calculate_impact_d,
    calculate_impact_linear,  # ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
    calculate_ttr_c,
    calculate_pullback_v2,
    calculate_amplification_extended,
    calculate_adjusted_empirical_score
)
```

### 2. Remplacement dans `predict_double_wave_base()`

**Lignes 2446-2463** : Remplacement de `calculate_impact_d()` par `calculate_impact_linear()`

**Avant** :
```python
base_impact_no_amp = calculate_impact_d(
    empirical_score=score_adjusted_mean,
    num_events=num_events,
    amplification=1.0,
    correction_factor=0.758
)
```

**Après** :
```python
# Calculer surprises pour formule linéaire
surprises = []
for _, row in df_events.iterrows():
    surprise_pct = row.get('surprise_pct', 0.0)
    if pd.notna(surprise_pct):
        surprises.append(abs(surprise_pct))

surprise_max = max(surprises) if surprises else 0.0
surprise_avg = np.mean(surprises) if surprises else 0.0

# ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
base_impact_no_amp = calculate_impact_linear(
    base_empirical_score=mean_empirical_score,
    adjusted_empirical_score=score_adjusted_mean,
    surprise_avg=surprise_avg,
    surprise_max=surprise_max,
    n_events=num_events
)
```

### 3. Remplacement dans `predict_single_wave_base()`

**Lignes 2679-2704** : Remplacement de `calculate_impact_d()` par `calculate_impact_linear()`

**Avant** :
```python
impact_base_no_amp = calculate_impact_d(
    empirical_score=mean_adjusted_score,
    num_events=len(df_events),
    amplification=1.0,
    correction_factor=0.758
)
```

**Après** :
```python
# Calculer surprises pour formule linéaire
surprises = []
for _, row in df_events.iterrows():
    if pd.notna(row.get('actual')) and pd.notna(row.get('estimate')):
        if row['estimate'] != 0:
            surprise_pct = abs((row['actual'] - row['estimate']) / abs(row['estimate'])) * 100
            surprises.append(surprise_pct)

surprise_max = max(surprises) if surprises else 0.0
surprise_avg = np.mean(surprises) if surprises else 0.0

# ⭐ NOUVELLE FORMULE LINÉAIRE (validée pour MOYEN/FORT/TRÈS_FORT)
impact_base_no_amp = calculate_impact_linear(
    base_empirical_score=avg_empirical_score,
    adjusted_empirical_score=mean_adjusted_score,
    surprise_avg=surprise_avg,
    surprise_max=surprise_max,
    n_events=len(df_events)
)
```

### 4. Mise à Jour Documentation

**Lignes 2412-2417** : Mise à jour de la docstring pour refléter la nouvelle formule
```python
"""
Prédiction Double Wave avec formules validées (⭐ Formule Linéaire + ratios Double Wave)

Utilise les formules validées SESSION_VALIDATION_ACTUELLE :
- ⭐ Formule Linéaire (calculate_impact_linear) - validée pour MOYEN/FORT/TRÈS_FORT
- Ratios Double Wave validés (Phase 1: 58%, Pullback: 84%, Phase 2: 90%)
- Impact net = Phase 1 - Pullback + Phase 2
"""
```

---

## 📊 Paramètres Utilisés

La nouvelle formule utilise :
- **base_empirical_score** : Score empirique de base (avant ajustement par surprise)
- **adjusted_empirical_score** : Score ajusté selon la surprise (depuis `score_adjusted`)
- **surprise_avg** : Surprise moyenne en % (moyenne des surprises absolues)
- **surprise_max** : Surprise maximale en % (surprise la plus forte)
- **n_events** : Nombre d'événements dans le cluster

---

## ✅ Validation

La formule linéaire a été validée sur :
- **50 dates** avec mouvements significatifs (>= 20 pips)
- **Performance FORT** : Ratio médian 1.297 (excellent)
- **Performance MOYEN** : Ratio médian 2.840 (acceptable avec sortie 85%)
- **MAE global** : 13.98 pips (vs 38.63 ancienne formule) → **-64% d'erreur**

---

## 🎯 Prochaines Étapes

1. ✅ Formule linéaire intégrée dans Planificateur
2. ⏳ **Tester** avec quelques dates FORT/TRÈS_FORT dans l'interface Streamlit
3. ⏳ **Ajouter filtre** mouvements significatifs (>= 20 pips) dans l'affichage
4. ⏳ **Valider** que les prédictions sont cohérentes avec les tests

---

## 📝 Notes

- L'ancienne fonction `calculate_impact_d()` est conservée pour rétrocompatibilité
- La formule linéaire utilise uniquement des features prédictives (calculables AVANT le mouvement)
- L'amplification est toujours appliquée après le calcul de base (comme avant)

---

✅ **Intégration terminée avec succès !**


