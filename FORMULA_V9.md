# FORMULE V9 - PRÉDICTION D'IMPACT (CALCUL GROUPÉ)

**Date de génération :** 2025-10-17 23:49:50
**Session :** 9
**Méthode :** Régression linéaire sur impacts groupés par minute

---

## 📐 FORMULE

```
impact_pips = -9.9773 + 0.4878 × empirical_score
```

**Simplifié :**
```
impact_pips = -9.98 + 0.49 × score
```

---

## 📊 MÉTRIQUES DE QUALITÉ

- **R² :** 0.0430
- **MAE :** 8.07 pips
- **RMSE :** 33.65 pips

---

## 💡 INTERPRÉTATION

- Pour chaque point de score empirique → +0.49 pips d'impact
- Impact de base (score=0) : -9.98 pips

---

## 📋 EXEMPLES DE PRÉDICTION

| Score | Impact prédit |
|-------|---------------|
| 50    |   14.4 pips |
| 60    |   19.3 pips |
| 70    |   24.2 pips |
| 80    |   29.0 pips |
| 90    |   33.9 pips |
| 100   |   38.8 pips |

---

## ⚖️ DIFFÉRENCE AVEC V6

**v6 (Session 6) :**
- Formule : impact = -4.59 + 0.287 × score
- R² = 0.719
- ❌ Basée sur calcul INDIVIDUEL (incorrect)
- ❌ Dupliquait le MFE pour événements simultanés

**v9 (Session 9) :**
- Formule : impact = -9.98 + 0.488 × score
- R² = 0.0430
- ✅ Basée sur calcul GROUPÉ (correct)
- ✅ UN impact par groupe temporel

---

## 📝 UTILISATION

```python
def predict_impact_v9(empirical_score):
    return -9.9773 + 0.4878 * empirical_score
```

---

## ⚠️ LIMITES

- La formule prédit l'impact MOYEN basé sur le score empirique
- L'impact réel dépend aussi du contexte, sentiment, timing
- R² = 0.0430 signifie que ~4.3% de la variance est expliquée
- Les 95.7% restants dépendent d'autres facteurs

---

**Version :** 9.0  
**Statut :** ✅ Validé sur données Session 9
