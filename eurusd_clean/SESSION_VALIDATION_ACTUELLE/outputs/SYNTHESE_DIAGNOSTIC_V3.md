# 📊 SYNTHÈSE DIAGNOSTIC DIRECTION V3

**Date** : 2025-12-08

---

## ✅ RÉSULTATS CALIBRATION V3

### Amplitude ✅ EXCELLENT
- **MAE** : 50.34 → **11.12 pips** (-78% d'amélioration)
- **Ratio médian** : 2.609 → **0.963** (proche de 1.0)
- **Erreur relative** : 177.7% → **29.9%** (-83%)

**→ Calibration amplitude V3 fonctionne parfaitement !**

### Direction ⚠️ PROBLÉMATIQUE
- **Accuracy** : 38.0% → **20.0%** (dégradation)
- **Coverage** : 85.7% → **28.6%** (θ=0.10 trop strict)

---

## 🔍 DIAGNOSTIC COMPLET

### Étape A : Test grille de seuils θ

**Résultats clés** :
- **θ=0.0** : Accuracy=46.2%, Coverage=78.0%
- **θ=0.10** : Accuracy=45.0%, Coverage=40.0%

**Conclusion** : Le problème **n'est PAS le seuil θ**. Même sans seuil (θ=0.0), l'accuracy reste ~46% (proche du hasard 50%).

### Étape B : Diagnostic scores S

**B1. Distribution** :
- **60% des scores sont neutres** (|S| < 0.1)
- Médiane : 0.0010 (très proche de 0)

**B2. Contributions alpha** :
- **`Other_surp_neg` domine** : contribution moyenne +0.1332
- **Beaucoup d'alphas à 0** : NFP, Unemployment, Employment, ISM, Consumer
- Ces alphas ne contribuent **jamais** au score S

**B3. Sens du signe** :
- **Corrélation S ↔ direction = -0.0024** (quasi-nulle)
- Signal directionnel très faible ou inexistant

**B4. Qualité stats** :
- 21 event_keys avec sigma < 0.01 (sur-normalisation)

---

## 🎯 PROBLÈMES IDENTIFIÉS

### 1. Alphas inactifs (weight = 0.0)

**Alphas avec weight = 0.0** :
- `NFP_surp_pos` : 0.0
- `Unemployment_surp_neg` : 0.0
- `Consumer_surp_neg` : 0.0
- `Consumer_surp_pos` : 0.0
- `ISM_surp_neg` : 0.0
- `ISM_surp_pos` : 0.0
- `Employment_surp_*` : 0.0
- Et beaucoup d'autres...

**Impact** : Ces événements ne contribuent jamais au score S, même s'ils sont présents.

### 2. Domination de `Other_surp_neg`

**Weight dans alpha_weights.csv** : **-0.191** (négatif)  
**Contribution moyenne observée** : **+0.1332** (positive)

**Hypothèse** : 
- Les surprises sont majoritairement négatives (z < 0)
- weight négatif × z négatif = contribution positive
- Mais peut-être que la convention de signe est incorrecte

### 3. Signal directionnel très faible

**Indicateurs** :
- Accuracy ~46% même sans seuil (proche du hasard)
- Corrélation S ↔ direction = -0.0024 (quasi-nulle)
- 60% des scores neutres

**→ Le modèle directionnel actuel n'est pas prédictif**

---

## 💡 RECOMMANDATIONS PRIORITAIRES

### 🔴 Priorité 1 : Analyser pourquoi alphas sont à 0

**Action** : Vérifier dans `build_v2_scores_composite.py` :
- Pourquoi NFP, Unemployment, etc. ont des weights = 0.0 ?
- Est-ce que ces événements apparaissent dans les données d'entraînement ?
- Est-ce que leurs scores empiriques sont calculés correctement ?

**Hypothèse** : Ces événements n'ont peut-être pas assez d'échantillons (n_1h < 50) pour être inclus dans le modèle.

### 🟡 Priorité 2 : Vérifier convention de signe `Other_surp_neg`

**Action** : 
- Identifier quels événements sont classés comme "Other"
- Vérifier si la contribution positive observée (+0.1332) est cohérente avec le weight négatif (-0.191)
- Analyser quelques cas concrets pour comprendre le signe

### 🟡 Priorité 3 : Corriger sur-normalisation

**Action** : Pour les 21 event_keys avec sigma < 0.01 :
- Utiliser un sigma minimum (ex. 0.1) dans `load_surprise_stats()`
- Ou exclure ces event_keys du calcul de z-score

### 🟢 Priorité 4 : Recalibrer avec événements actifs uniquement

**Action** : 
- Recalculer alpha weights en excluant les événements avec weight = 0.0
- Focus sur événements qui contribuent réellement (Other, PMI, CPI, etc.)
- Vérifier que les événements NFP, Unemployment apparaissent dans les données

---

## 📊 MÉTRIQUES CLÉS

| Métrique | Valeur |
|----------|--------|
| **Accuracy max (θ=0.0)** | 46.2% |
| **Coverage max (θ=0.0)** | 78.0% |
| **Corrélation S ↔ direction** | -0.0024 |
| **% scores neutres (|S|<0.1)** | 60.0% |
| **Alpha dominant** | `Other_surp_neg` (weight=-0.191, contrib=+0.1332) |
| **Alphas inactifs** | NFP, Unemployment, Employment, ISM, Consumer, etc. |

---

## ✅ CONCLUSION

### Ce qui fonctionne ✅
- **Calibration amplitude V3** : Excellent (MAE -78%, ratio ~1.0)
- **Couverture** : Bonne (78% avec θ=0.0)

### Ce qui ne fonctionne pas ⚠️
- **Signal directionnel** : Très faible (accuracy ~46%, corrélation quasi-nulle)
- **Alphas inactifs** : Beaucoup d'événements importants (NFP, Unemployment) ont weight = 0.0
- **Domination `Other`** : Un seul alpha (`Other_surp_neg`) domine, potentiellement mal calibré

### Prochaine étape 🎯

**Analyser et corriger les alpha weights** :
1. Vérifier pourquoi NFP, Unemployment, etc. ont weight = 0.0
2. Vérifier la convention de signe pour `Other_surp_neg`
3. Recalibrer avec événements actifs uniquement

**Objectif** : Atteindre accuracy directionnelle > 60% avec coverage > 70%

