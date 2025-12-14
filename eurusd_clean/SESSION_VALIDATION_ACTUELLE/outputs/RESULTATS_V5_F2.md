# 📊 RÉSULTATS V5 AVEC F2 (Normalisation √n_active)

**Date** : 2025-12-09  
**Correction** : F1 → F2 (normalisation par √n_active)

---

## ✅ MODIFICATION F2 APPLIQUÉE

**Avant (F1)** : `S = S_raw / n_active`  
**Après (F2)** : `S = S_raw / math.sqrt(max(1, n_active))`

**Impact attendu** : Moins de compression → scores moins comprimés → neutres ↓

---

## 📊 LES 3 MÉTRIQUES CLÉS (V5 + F2)

### 1. % scores neutres (|S| < 0.1)

**Résultat** : **94.0%**

- F1 (avant) : 100.0%
- F2 (après) : 94.0%
- **Amélioration** : -6 points

**Objectif** : < 50% d'abord, puis < 35%

### 2. Corrélation S ↔ direction réalisée

**Résultat** : **-0.0128**

- F1 (avant) : -0.0219
- F2 (après) : -0.0128
- **Amélioration** : +0.0091 (moins négative)

**Objectif** : > 0.03 minimum

### 3. Accuracy à θ=0.0

**Résultat** : **51.2%**

- F1 (avant) : 51.2%
- F2 (après) : 51.2%
- **Évolution** : = (identique)

**Objectif** : > 52%

---

## 📊 DISTRIBUTION DES SCORES S (F2)

**Statistiques** :
- Min : -0.1387
- Max : +0.1722
- Médiane : 0.0032
- Moyenne : 0.0067
- Écart-type : 0.0461

**Concentration autour de 0** :
- |S| < 0.02 : 54.0%
- |S| < 0.05 : 82.0%
- |S| < 0.10 : 94.0%

**Comparaison F1 vs F2** :
- **F1** : min=-0.049, max=+0.099, %neutres=100%
- **F2** : min=-0.139, max=+0.172, %neutres=94%
- **Amélioration** : Scores moins comprimés (×2.8 en amplitude), mais 94% restent neutres

---

## ✅ AUTRES MÉTRIQUES

| Métrique | Valeur |
|----------|--------|
| **Coverage (θ=0.0)** | 86.0% |
| **Balanced Accuracy** | 49.7% |
| **F1 Macro** | 49.4% |

---

## 🔍 OBSERVATIONS

### ✅ Améliorations F2

1. **Amplitude des scores augmentée** : ×2.8 (de [-0.049, +0.099] à [-0.139, +0.172])
2. **Neutres réduits** : 100% → 94% (-6 points)
3. **Corrélation améliorée** : -0.0219 → -0.0128 (moins négative)

### ⚠️ Problèmes persistants

1. **94% de neutres** : Toujours trop élevé (objectif < 50%)
2. **Corrélation très faible** : -0.0128 (objectif > 0.03)
3. **Accuracy stagnante** : 51.2% (objectif > 52%)

### Points à investiguer

1. **Secondary avec weights = 0.0** : Même les top 35 event_keys n'ont pas de poids
   - → Exclusion totale de Secondary recommandée

2. **EIA toujours absent** : Pas assez d'occurrences même avec MIN_Z=5
   - → Regrouper EIA en un seul key ou augmenter fenêtre d'entraînement

---

## 💡 RECOMMANDATIONS

### Option 1 : Abaisser seuil de neutralité

**Si neutres ~40-55% et accuracy 52-54%** :
- Abaisser seuil de |S| < 0.1 → |S| < 0.05 ou 0.02

### Option 2 : Exclure Secondary totalement

**Si Secondary weights = 0.0** :
- Exclusion complète de Secondary du training directionnel
- Simplifie le modèle et réduit le bruit

### Option 3 : Passer à un fit directionnel différent

**Si accuracy stagne ~51%** :
- Logit/LDA direct sur les alphas actifs au lieu de Ridge

---

## 📋 SYNTHÈSE

**F2 a amélioré les choses** :
- ✅ Amplitude des scores restaurée
- ✅ Neutres réduits de 6 points
- ✅ Corrélation légèrement améliorée

**Mais pas encore suffisant** :
- ⚠️ 94% de neutres reste trop élevé
- ⚠️ Corrélation très faible (-0.0128)
- ⚠️ Accuracy stagnante (51.2%)

**Prochaine étape recommandée** : Exclure Secondary totalement ou abaisser seuil de neutralité

