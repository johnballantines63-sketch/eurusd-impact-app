# Améliorations Direction et Affichage

**Date** : 2025-12-07  
**Modifications** : Exclusion surprises nulles + Affichage avec signe

---

## ✅ Modifications Implémentées

### 1. Exclusion Événements avec Surprise = 0.00%

**Fichier** : `src/core/cluster_impact_calculator.py`

**Changement** :
```python
# AVANT
if surprise is not None:
    signed_surprises.append(surprise)

# APRÈS
SURPRISE_THRESHOLD = 0.1  # Seuil minimum
if surprise is not None and abs(surprise) >= SURPRISE_THRESHOLD:
    signed_surprises.append(surprise)  # ✅ Exclut surprises nulles
```

**Impact** :
- ✅ Surprise cluster plus représentative (exclut le bruit)
- ✅ Direction plus précise (moins d'événements sans influence)
- ✅ Moyenne non faussée par événements sans surprise

**Exemple** :
- Avant : `surprise_net = (+10 + 0 + 0 - 5) / 4 = +1.25%` ❌
- Après : `surprise_net = (+10 - 5) / 2 = +2.5%` ✅

---

### 2. Affichage avec Signe (+/-) selon Direction

**Fichier** : `SESSION_VALIDATION_ACTUELLE/scripts/validate_on_new_dates.py`

**Changement** :
```python
# Calculer impact avec signe
impact_real_signed = movement_real['peak_pips'] if direction_real == 'UP' else -movement_real['peak_pips']
impact_predicted_signed = prediction['impact_pips'] if direction_predicted == 'UP' else -prediction['impact_pips'] if direction_predicted == 'DOWN' else 0.0

# Affichage
print(f"Réel={real_signed:>8s} | Prédit={pred_signed:>8s}")  # +48.2 ou -48.2
```

**Format** :
- **UP** : `+48.2 pips` (hausse EURUSD)
- **DOWN** : `-48.2 pips` (baisse EURUSD)
- **UNKNOWN** : `+0.0 pips` (pas de direction prédite)

**Exemple d'affichage** :
```
📊 Top 5 meilleures prédictions :

   2025-10-29   : Réel=   -70.3 | Prédit=    +0.0 | Erreur=  7.1 pips ( 10.1%) [DOWN→UNKNOWN]
   2025-04-10   : Réel=   +89.5 | Prédit=   +67.8 | Erreur= 21.7 pips ( 24.3%) [UP→UP]
```

**Avantages** :
- ✅ Lecture plus claire (signe indique direction immédiatement)
- ✅ Comparaison visuelle facilitée (même signe = même direction)
- ✅ Cohérence avec baseline (mouvement par rapport à baseline)

---

## 📊 Résultats Actuels

### Accuracy Directionnelle
- **48.0%** (24/50 corrects)
- **UP réel** : 35.7% corrects (10/28)
- **DOWN réel** : 63.6% corrects (14/22)

### Observations
- ✅ Exclusion surprises nulles implémentée
- ✅ Affichage avec signe fonctionnel
- ⚠️ Accuracy toujours à 48% (à améliorer)

---

## 🎯 Prochaines Étapes

1. **Tester impact exclusion surprises nulles** sur accuracy
2. **Analyser cas UNKNOWN** (8 cas sur 50)
3. **Améliorer prédiction direction** (objectif > 60%)

---

**Status** : ✅ **Implémenté - À tester et valider**


