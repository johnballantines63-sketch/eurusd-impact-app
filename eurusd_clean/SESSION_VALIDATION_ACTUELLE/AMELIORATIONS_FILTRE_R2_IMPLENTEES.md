# Améliorations Implémentées : Filtre R² pour MOYEN et FORT/TRÈS_FORT

**Date** : 2025-12-07  
**Objectif** : Améliorer accuracy directionnelle en filtrant tendances de faible qualité (R² faible)

---

## ✅ Modifications Implémentées

### 1. Filtre R² Adaptatif selon Amplitude Prédite

**Principe** : Ne pas utiliser tendances avec R² trop faible pour prédire direction

```python
# Seuils R² adaptatifs selon amplitude prédite
if impact_predicted >= 60:  # FORT/TRÈS_FORT
    min_r2_threshold = 0.2  # Seuil plus strict pour meilleure qualité
elif impact_predicted >= 40:  # FORT
    min_r2_threshold = 0.18
else:  # MOYEN
    min_r2_threshold = 0.15  # Seuil plus permissif mais filtre quand même R² = 0.000

if r2 >= min_r2_threshold:
    direction_predicted = trend_result.get('direction', 'UNKNOWN')
    direction_method = 'trend_pre_event'
else:
    direction_predicted = 'UNKNOWN'
    direction_method = 'trend_low_quality'  # Pour tracking
```

**Logique** :
- **FORT/TRÈS_FORT** : Seuil R² = 0.2 (plus strict) car mouvements plus prévisibles
- **MOYEN** : Seuil R² = 0.15 (plus permissif) mais filtre quand même R² = 0.000
- Si R² < seuil → Utiliser fallback surprise au lieu de tendance

---

## 📊 Résultats

### Accuracy Globale

| Version | Accuracy | Amélioration |
|---------|----------|--------------|
| **Avant (surprise seule)** | 48.0% | - |
| **Avant filtre R²** | 68.0% | +20.0 points |
| **Après filtre R²** | **70.0%** | **+2.0 points** ✅ |

### Répartition Méthodes

- **trend_pre_event** : 45 cas (90.0%) - Tendance utilisée avec R² acceptable
- **surprise_fallback** : 5 cas (10.0%) - Fallback quand tendance non détectée ou R² faible

### Accuracy par Direction

- **UP réel** : 71.4% (20/28) ✅
- **DOWN réel** : 68.2% (15/22) ✅

---

## 🎯 Améliorations Attendues

### Pour MOYEN

**Objectif** : Filtrer tendances avec R² = 0.000 (très faible qualité)

**Résultat attendu** :
- Moins d'erreurs directionnelles dues à tendances non fiables
- Utilisation de fallback surprise quand tendance de mauvaise qualité
- Accuracy MOYEN devrait augmenter

### Pour FORT/TRÈS_FORT

**Objectif** : Utiliser seulement tendances de bonne qualité (R² ≥ 0.2)

**Résultat attendu** :
- Directions plus fiables pour mouvements forts
- Moins de fausses directions dues à tendances de qualité moyenne
- Accuracy FORT/TRÈS_FORT devrait se maintenir ou augmenter

---

## 📋 Prochaines Étapes

1. ⏳ **Analyser résultats détaillés** : Vérifier R² moyen par méthode et par classe
2. ⏳ **Ajuster seuils si nécessaire** : Optimiser min_r2_threshold selon résultats
3. ⏳ **Tester sur plus de dates** : Valider robustesse améliorations

---

**Status** : ✅ **Implémenté - Accuracy améliorée de 68% → 70% (+2 points)**


