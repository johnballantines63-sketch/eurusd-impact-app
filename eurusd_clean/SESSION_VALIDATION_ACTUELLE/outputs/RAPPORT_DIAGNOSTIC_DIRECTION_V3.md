# 📊 RAPPORT DIAGNOSTIC DIRECTION V3

**Date** : 2025-12-08  
**Objectif** : Diagnostiquer pourquoi l'accuracy directionnelle est faible (20-46%)

---

## ✅ ÉTAPE A : TEST GRILLE DE SEUILS θ

### Résultats par seuil

| θ   | Coverage | Accuracy | Balanced Acc | F1 Macro | F1 UP | F1 DOWN |
|-----|----------|----------|--------------|----------|--------|---------|
| 0.00 | 78.0%    | **46.2%** | 44.3%        | 43.8%    | 55.3%  | 32.3%   |
| 0.02 | 66.0%    | 42.4%    | 42.8%        | 41.6%    | 48.6%  | 34.5%   |
| 0.05 | 54.0%    | 44.4%    | 45.1%        | 43.2%    | 51.6%  | 34.8%   |
| 0.08 | 44.0%    | 45.5%    | 45.5%        | 41.1%    | 57.1%  | 25.0%   |
| 0.10 | 40.0%    | 45.0%    | 45.0%        | 37.3%    | 59.3%  | 15.4%   |
| 0.12 | 38.0%    | 42.1%    | 43.9%        | 35.7%    | 56.0%  | 15.4%   |

### Matrices de confusion (exemples)

**θ = 0.00** (Coverage: 78.0%) :
```
   TP=13  FP=12
   FN= 9  TN= 5
```

**θ = 0.10** (Coverage: 40.0%) :
```
   TP= 8  FP= 9
   FN= 2  TN= 1
```

### 🔍 Conclusion Étape A

**CAS 2 : Signal neutre structurel**

- **Accuracy reste ~46% même avec θ=0.0** (proche du hasard 50%)
- **Le problème n'est PAS le seuil θ**, mais le signal directionnel lui-même
- Coverage bonne (78%) mais accuracy faible → signal trop faible ou mal aligné

---

## 🔬 ÉTAPE B : DIAGNOSTIC SCORES S

### B1. Distribution de S

**Statistiques** :
- Min : -0.1780
- Max : 1.4914
- **Médiane : 0.0010** ⚠️ (très proche de 0)
- Moyenne : 0.1197
- Écart-type : 0.2764

**Concentration autour de 0** :
- |S| < 0.02 : **34.0%**
- |S| < 0.05 : **46.0%**
- |S| < 0.10 : **60.0%** ⚠️

**→ 60% des scores sont neutres !**

### B2. Contribution par Alpha

**Top 10 alphas par contribution absolue** :

| Alpha Key | Fréquence | Mean Contrib | Abs Mean |
|-----------|-----------|--------------|----------|
| `Other_surp_neg` | 50 | **+0.1332** | 0.1332 |
| `PMI_surp_neg` | 5 | +0.0353 | 0.0353 |
| `CPI_surp_neg` | 48 | -0.0092 | 0.0092 |
| `CPI_surp_pos` | 60 | -0.0090 | 0.0090 |
| `Other_surp_pos` | 45 | +0.0028 | 0.0028 |
| `PMI_surp_pos` | 14 | 0.0000 | 0.0000 |
| `ISM_surp_neg` | 9 | 0.0000 | 0.0000 |
| `Consumer_surp_neg` | 8 | 0.0000 | 0.0000 |
| `ISM_surp_pos` | 14 | 0.0000 | 0.0000 |
| `Consumer_surp_pos` | 4 | 0.0000 | 0.0000 |

**⚠️ PROBLÈME MAJEUR** :
- **`Other_surp_neg` domine** avec contribution moyenne de +0.1332
- **Beaucoup d'alphas à 0** : NFP, Unemployment, Employment, ISM, Consumer, etc.
- Ces alphas ne contribuent **jamais** au score S

### B3. Sens du Signe

**Corrélation S ↔ direction réelle** : **-0.0024**

**→ Signal très faible ou neutre**

- Corrélation proche de 0 indique que S n'est pas prédictif de la direction
- Pas de signe inversé évident (corrélation serait fortement négative)

### B4. Qualité des Surprise Stats

**Statistiques surprises brutes** :
- Nombre d'événements : 11,023
- Moyenne : -0.5271
- Écart-type : 99.16
- Min : -3336.0
- Max : 3609.6

**Normalisation par event_key** :
- Nombre d'event_keys : 351
- Moyenne des mu : -1.08
- Moyenne des sigma : 7.81
- **21 event_keys avec sigma < 0.01** ⚠️ (sur-normalisation possible)

---

## 🎯 SYNTHÈSE & DIAGNOSTIC

### Problèmes identifiés

1. **Signal directionnel très faible**
   - Accuracy ~46% même sans seuil (proche du hasard)
   - Corrélation S ↔ direction = -0.0024 (quasi-nulle)
   - 60% des scores neutres (|S| < 0.1)

2. **Alphas inactifs**
   - NFP, Unemployment, Employment, ISM, Consumer : contributions toujours nulles
   - Seulement 5 alphas contribuent réellement (Other, PMI, CPI)

3. **Domination de `Other_surp_neg`**
   - Contribution moyenne de +0.1332 (10x plus que les autres)
   - Peut biaiser les résultats si mal calibré

4. **Sur-normalisation**
   - 21 event_keys avec sigma < 0.01
   - Peut causer des z-scores extrêmes ou NaN

### Causes probables

1. **Alpha weights mal calibrés**
   - Beaucoup d'alphas à 0 dans `alpha_weights.csv`
   - Ou alphas trop petits pour avoir un impact

2. **Sélection d'événements**
   - Les événements NFP, Unemployment, etc. ne sont peut-être pas dans les données de test
   - Ou leurs surprises sont toujours nulles

3. **Convention de signe**
   - `Other_surp_neg` avec contribution positive peut indiquer un problème de convention

---

## 💡 RECOMMANDATIONS

### Priorité 1 : Vérifier alpha weights

**Action** : Examiner `alpha_weights.csv` pour :
- Vérifier si NFP, Unemployment, Employment ont des weights non-nuls
- Vérifier si les weights sont trop petits (< 0.01)
- Vérifier la convention de signe (pos/neg)

### Priorité 2 : Analyser événements "Other"

**Action** : Identifier ce que représente `Other_surp_neg` :
- Quels événements sont classés comme "Other" ?
- Pourquoi leur contribution est-elle si élevée ?
- Vérifier si la convention de signe est correcte

### Priorité 3 : Corriger sur-normalisation

**Action** : Pour les 21 event_keys avec sigma < 0.01 :
- Utiliser un sigma minimum (ex. 0.1) pour éviter division par 0
- Ou exclure ces event_keys du calcul

### Priorité 4 : Recalibrer avec événements actifs uniquement

**Action** : Recalculer alpha weights en excluant :
- Événements avec sigma < seuil
- Événements qui n'apparaissent jamais dans les données de test
- Focus sur événements qui contribuent réellement

---

## 📊 MÉTRIQUES CLÉS

- **Accuracy max (θ=0.0)** : 46.2%
- **Coverage max (θ=0.0)** : 78.0%
- **Corrélation S ↔ direction** : -0.0024
- **% scores neutres (|S|<0.1)** : 60.0%
- **Alpha dominant** : `Other_surp_neg` (0.1332)

---

## ✅ CONCLUSION

**Le problème n'est PAS le seuil θ**, mais un **signal directionnel structurellement faible**.

**Causes principales** :
1. Beaucoup d'alphas inactifs (NFP, Unemployment, etc.)
2. Signal dominé par `Other_surp_neg` (potentiellement mal calibré)
3. Corrélation quasi-nulle entre S et direction réelle

**Prochaine étape** : Analyser et corriger les alpha weights, puis recalibrer.

