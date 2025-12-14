# FORMULAS VALIDATED V2.1 - README

**Date:** 25 octobre 2025  
**Version:** 2.1  
**Base:** V1 Session 75  
**Status:** ✅ Production Ready

---

## 📊 PERFORMANCE

| Métrique | Valeur |
|----------|--------|
| **R²** | 0.705 |
| **MAE** | 7.7 pips |
| **Features** | 8 |
| **Dataset** | 16 mouvements (seuil 80 pips) |
| **Validation** | Session 76 - LOO cross-validation |

---

## 🎯 DÉCISION V2.1 vs V2.2

### Pourquoi V2.1 (V1) et pas V2.2 (V3) ?

**V3 testé en Session 76 :**
- 12 features (4 features contextuelles ajoutées)
- R² training = 0.994 (apparemment excellent)
- **MAIS R² LOO = -22,879** ❌ (overfitting catastrophique)
- MAE LOO = 1,204 pips (vs 1.1 pips training)
- Prédictions aberrantes : -23,000 pips prédits

**V1 retenu (V2.1) :**
- 8 features (base solide)
- R² = 0.705 (>0.7 objectif ✅)
- MAE = 7.7 pips (acceptable)
- Généralisation robuste
- **Ratio points/features : 2.0** (vs 1.33 pour V3)

### Règle Apprise

> **Minimum 2-3 points par feature** pour éviter overfitting  
> Plus de features ≠ meilleur modèle

---

## 🚀 USAGE RAPIDE

```python
from formulas_validated_v2 import predict_impact_v2

events_data = {
    'nb_events': 1,
    'scores': [30],
    'surprises': [15.5],
    'directions': ['UP'],
    'families': ['CPI']
}

result = predict_impact_v2(events_data)
print(f"Impact: {result['impact_pips']} pips")
```

---

## 📚 DOCUMENTATION COMPLÈTE

Voir fichiers détaillés dans `docs/` :
- `FORMULAS_V2.1_GUIDE.md` - Guide utilisateur
- `FORMULAS_V2.1_TECHNICAL.md` - Documentation technique
- `WHY_NOT_V3.md` - Explication rejet V3

---

**Version:** 2.1 | **Status:** ✅ PRODUCTION READY
