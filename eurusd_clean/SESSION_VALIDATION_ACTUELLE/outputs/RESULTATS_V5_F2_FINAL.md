# 📊 RÉSULTATS V5 + F2 + Exclusion Secondary + θ=0.05

**Date** : 2025-12-09  
**Modifications** : E1, E2, E3, F2, Exclusion Secondary, Seuil θ=0.05

---

## ✅ MODIFICATIONS APPLIQUÉES

### E1 : Exclusion Bills ✅
- Bills exclus (0 événements avec estimate)

### E2 : Seuil z-score adaptatif EIA ✅
- `MIN_Z_FOR_ZSCORE_EIA = 5`
- **Résultat** : EIA toujours absent

### E3 : Filtrage Secondary (top 40) ✅
- Secondary filtré : 995 → 943 événements (52 exclus)

### Étape A : Exclusion complète Secondary ✅
- **943 événements Secondary exclus**
- Secondary complètement absent des alpha_weights (0 lignes)

### F2 : Normalisation par √n_active ✅
- `S = S_raw / math.sqrt(max(1, n_active))`

### Seuil neutralité : θ=0.05 ✅
- Nouveau seuil de référence pour classification directionnelle

---

## 📊 LES 3 MÉTRIQUES CLÉS

### 1. % scores neutres (|S| < 0.05) : **82.0%**

**Évolution** :
- V4 : 76% (avec |S| < 0.1)
- V5 + F1 : 100% (avec |S| < 0.1)
- V5 + F2 : 94% (avec |S| < 0.1), 82% (avec |S| < 0.05)
- **V5 + F2 + Exclusion Secondary** : **82%** (avec |S| < 0.05)

**Objectif** : < 50% → **❌ Non atteint** (82% reste élevé)

### 2. Corrélation S ↔ direction réalisée : **-0.0128**

**Évolution** :
- V4 : -0.0024
- V5 + F1 : -0.0219
- V5 + F2 : -0.0128
- **V5 + F2 + Exclusion Secondary** : **-0.0128** (identique)

**Objectif** : > 0.03 → **❌ Non atteint** (corrélation très faible)

### 3. Accuracy

- **Accuracy à θ=0.0** : **51.2%** (Coverage: 86.0%)
- **Accuracy à θ=0.05** : **55.6%** (Coverage: 18.0%)

**Évolution** :
- V4 : 51.2% (θ=0.0)
- **V5 + F2 + Exclusion Secondary** : 51.2% (θ=0.0), **55.6%** (θ=0.05)

**Objectif** : > 52% → **✅ Atteint à θ=0.05** (55.6%), mais coverage très faible (18%)

---

## 📊 DISTRIBUTION DES SCORES S

**Statistiques** :
- Min : -0.1387
- Max : +0.1722
- Médiane : 0.0032
- Moyenne : 0.0067
- Écart-type : 0.0461

**Concentration autour de 0** :
- |S| < 0.02 : 54.0%
- |S| < 0.05 : 82.0% ⭐
- |S| < 0.10 : 94.0%

---

## 📊 ALPHA WEIGHTS (après exclusion Secondary)

**Total** : 225 lignes (75 event_keys uniques, 3 horizons)

**Top 10** :
1. Trade Balance_surp_pos (4h) : +0.353656
2. Unemployment_surp_neg (4h) : -0.318685
3. Unemployment_surp_pos (4h) : +0.308331
4. Trade Balance_surp_neg (4h) : +0.254323
5. PPI_surp_neg (4h) : +0.247698
6. PMI_surp_neg (1j) : -0.240764
7. Business Confidence_surp_neg (1j) : -0.235438
8. Business Confidence_surp_pos (1j) : -0.232347
9. Unemployment_surp_neg (1j) : -0.226805
10. Confidence_surp_pos (4h) : +0.219533

**✅ Secondary** : 0 lignes (complètement exclu)

---

## 🔍 DIAGNOSTIC

### Observations positives

1. **Secondary exclu** : Plus de bruit dans les alpha_weights
2. **Accuracy améliorée à θ=0.05** : 55.6% (vs 51.2% à θ=0.0)
3. **Amplitude S restaurée** : [-0.139, +0.172] (acceptable)

### Problèmes persistants

1. **82% de neutres** : Même avec exclusion Secondary, 82% des scores restent dans |S| < 0.05
2. **Corrélation très faible** : -0.0128 (quasi-nulle)
3. **Coverage faible à θ=0.05** : 18% seulement (9/50 échantillons)

### Causes probables

**Signal directionnel intrinsèque absent** :
- Même après nettoyage (exclusion Secondary, normalisation F2), la corrélation reste quasi-nulle
- Accuracy améliorée à θ=0.05 mais avec coverage très faible (18%)
- 82% des scores restent neutres même après exclusion

---

## 💡 CONCLUSION

### CAS : Signal directionnel quasi nul confirmé

**Résultats** :
- ✅ Accuracy améliorée à θ=0.05 (55.6%)
- ❌ Corrélation très faible (-0.0128)
- ❌ 82% de neutres
- ⚠️ Coverage très faible à θ=0.05 (18%)

**Diagnostic** : À feature-set constant, le signal directionnel est quasi nul.

**Recommandation** : Passer à **V6 structurelle** avec changement d'objectif/fit :
1. Re-fit directionnel sur label binaire (logit L1 ou LDA)
2. Changer l'horizon directionnel (4h/1j au lieu de 1h)

---

## 📋 SYNTHÈSE FINALE

| Métrique | Valeur | Objectif | Status |
|----------|--------|----------|--------|
| **% neutres (|S|<0.05)** | 82.0% | < 50% | ❌ |
| **Corrélation** | -0.0128 | > 0.03 | ❌ |
| **Accuracy θ=0.0** | 51.2% | > 52% | ⚠️ |
| **Accuracy θ=0.05** | 55.6% | > 52% | ✅ (mais coverage 18%) |

