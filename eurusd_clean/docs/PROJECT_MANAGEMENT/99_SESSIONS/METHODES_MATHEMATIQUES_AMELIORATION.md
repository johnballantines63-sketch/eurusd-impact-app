# 🧮 MÉTHODES MATHÉMATIQUES POUR AMÉLIORER PRÉDICTIONS

**Date :** 16 novembre 2025  
**Session :** Post-Session 142  
**Statut :** 📋 PROPOSITIONS MÉTHODES ALTERNATIVES

---

## 🎯 CONTEXTE

**Problème actuel :**
- MAE global : 14.69 pips (excellent)
- Mais certains groupes ont MAE élevé :
  - `DOUBLE_WAVE_DOWN 300-400` : 26.66 pips (n=9)
  - `CRASH_RECOVERY_UP 100-200` : 26.53 pips (n=2)
  - `SINGLE_WAVE_FORT_DOWN 0-100` : 16.18 pips (n=37)

**Méthodes actuelles :**
- Pattern-based : Moyenne/médiane par groupe
- Workflow original : Corrélation R² ↔ amplification

**Question :** Autres méthodes mathématiques pour améliorer ces groupes ?

---

## 💡 MÉTHODES PROPOSÉES

### **1. RÉGRESSION PONDÉRÉE PAR SIMILARITÉ** ⭐⭐⭐

**Principe :**
Au lieu de moyenne simple, utiliser moyenne pondérée où chaque cas historique est pondéré par sa similarité avec le cas à prédire.

**Formule :**
```
prediction = Σ(impact_i × weight_i) / Σ(weight_i)

où weight_i = similarity(cas_actuel, cas_historique_i)
```

**Similarité possible :**
- **Temps** : `weight = exp(-|date_diff| / τ)` (cas récents plus importants)
- **Score** : `weight = exp(-|score_diff|² / σ²)` (scores similaires plus importants)
- **Composition** : `weight = Jaccard(events_actuel, events_historique)`
- **R² tendance** : `weight = exp(-|R²_diff|² / σ²)`

**Avantages :**
- ✅ Utilise tous les cas historiques (pas seulement groupe)
- ✅ Donne plus de poids aux cas similaires
- ✅ Peut améliorer groupes petits (n=2-9)

**Implémentation :**
```python
def predict_weighted_similarity(
    current_case: Dict,
    historical_cases: List[Dict],
    similarity_features: List[str] = ['date', 'score', 'r2_trend']
) -> float:
    """
    Prédit avec moyenne pondérée par similarité.
    
    Features de similarité :
    - date : Proximité temporelle
    - score : Proximité score total
    - r2_trend : Proximité R² tendance
    - composition : Similarité composition événements
    """
    weights = []
    impacts = []
    
    for hist_case in historical_cases:
        # Calculer similarité multi-features
        similarity = 1.0
        
        if 'date' in similarity_features:
            date_diff = abs((current_case['date'] - hist_case['date']).days)
            date_sim = np.exp(-date_diff / 90)  # τ = 90 jours
            similarity *= date_sim
        
        if 'score' in similarity_features:
            score_diff = abs(current_case['total_score'] - hist_case['total_score'])
            score_sim = np.exp(-(score_diff ** 2) / (2 * (50 ** 2)))  # σ = 50
            similarity *= score_sim
        
        if 'r2_trend' in similarity_features:
            r2_diff = abs(current_case['r2_trend'] - hist_case['r2_trend'])
            r2_sim = np.exp(-(r2_diff ** 2) / (2 * (0.2 ** 2)))  # σ = 0.2
            similarity *= r2_sim
        
        weights.append(similarity)
        impacts.append(hist_case['impact_measured'])
    
    # Normaliser poids
    weights = np.array(weights)
    weights = weights / weights.sum()
    
    # Prédiction pondérée
    prediction = np.sum(weights * impacts)
    
    return prediction
```

**Gain estimé :** -2 à -5 pips pour groupes petits/hétérogènes

---

### **2. K-NEAREST NEIGHBORS (KNN)** ⭐⭐⭐

**Principe :**
Utiliser les k cas historiques les plus similaires (k=3-5) et prédire par moyenne/médiane de ces k voisins.

**Avantages :**
- ✅ Simple à implémenter
- ✅ Robuste aux outliers
- ✅ Adaptatif (k voisins les plus proches)

**Implémentation :**
```python
def predict_knn(
    current_case: Dict,
    historical_cases: List[Dict],
    k: int = 5,
    use_median: bool = False
) -> float:
    """
    Prédit avec K-Nearest Neighbors.
    
    Distance multi-dimensionnelle :
    d = sqrt(
        w_date * (date_diff/90)² +
        w_score * (score_diff/100)² +
        w_r2 * (r2_diff/0.5)²
    )
    """
    distances = []
    
    for hist_case in historical_cases:
        # Distance normalisée
        date_diff = abs((current_case['date'] - hist_case['date']).days) / 90
        score_diff = abs(current_case['total_score'] - hist_case['total_score']) / 100
        r2_diff = abs(current_case['r2_trend'] - hist_case['r2_trend']) / 0.5
        
        distance = np.sqrt(
            0.3 * date_diff**2 +
            0.5 * score_diff**2 +
            0.2 * r2_diff**2
        )
        
        distances.append((distance, hist_case['impact_measured']))
    
    # Trier par distance et prendre k plus proches
    distances.sort(key=lambda x: x[0])
    k_nearest = [impact for _, impact in distances[:k]]
    
    # Prédire par moyenne ou médiane
    if use_median:
        return np.median(k_nearest)
    else:
        return np.mean(k_nearest)
```

**Gain estimé :** -3 à -6 pips pour groupes hétérogènes

---

### **3. RÉGRESSION QUANTILE** ⭐⭐

**Principe :**
Au lieu de prédire la moyenne (minimise MAE en moyenne), prédire directement la médiane (minimise MAE médian).

**Avantages :**
- ✅ Robuste aux outliers
- ✅ Prédit médiane directement (pas besoin de tester)

**Implémentation :**
```python
from sklearn.linear_model import QuantileRegressor

def predict_quantile_regression(
    X_train: np.array,  # Features : [score, n_events, r2_trend, ...]
    y_train: np.array,  # Impacts réels
    X_test: np.array,
    quantile: float = 0.5  # 0.5 = médiane
) -> float:
    """
    Prédit médiane avec régression quantile.
    
    Features possibles :
    - total_score
    - n_events
    - r2_trend
    - surprise_factor
    - volatility_pre
    """
    model = QuantileRegressor(quantile=quantile, alpha=0.0)
    model.fit(X_train, y_train)
    
    prediction = model.predict(X_test.reshape(1, -1))[0]
    
    return prediction
```

**Gain estimé :** -2 à -4 pips (similaire à médiane simple)

---

### **4. ENSEMBLE METHODS** ⭐⭐⭐⭐

**Principe :**
Combiner plusieurs méthodes de prédiction (moyenne, médiane, KNN, régression) avec poids optimisés.

**Formule :**
```
prediction = w1 × mean + w2 × median + w3 × knn + w4 × regression
```

**Optimisation poids :**
- Minimiser MAE sur validation croisée
- Contraintes : Σw = 1, w ≥ 0

**Avantages :**
- ✅ Combine forces de chaque méthode
- ✅ Robuste (une méthode peut compenser l'autre)
- ✅ Peut améliorer tous les groupes

**Implémentation :**
```python
def predict_ensemble(
    current_case: Dict,
    historical_cases: List[Dict],
    weights: Dict[str, float] = None
) -> Dict:
    """
    Prédit avec ensemble de méthodes.
    
    Méthodes :
    - mean : Moyenne groupe
    - median : Médiane groupe
    - knn : K-Nearest Neighbors
    - weighted : Moyenne pondérée similarité
    """
    if weights is None:
        # Poids par défaut (à optimiser)
        weights = {
            'mean': 0.2,
            'median': 0.3,
            'knn': 0.3,
            'weighted': 0.2
        }
    
    predictions = {}
    
    # Moyenne
    impacts = [c['impact_measured'] for c in historical_cases]
    predictions['mean'] = np.mean(impacts)
    
    # Médiane
    predictions['median'] = np.median(impacts)
    
    # KNN
    predictions['knn'] = predict_knn(current_case, historical_cases, k=5)
    
    # Weighted
    predictions['weighted'] = predict_weighted_similarity(
        current_case, historical_cases
    )
    
    # Ensemble
    prediction_ensemble = sum(
        weights[method] * predictions[method]
        for method in weights
    )
    
    return {
        'prediction': prediction_ensemble,
        'individual': predictions,
        'weights': weights
    }
```

**Gain estimé :** -3 à -7 pips (meilleure méthode proposée)

---

### **5. FEATURE ENGINEERING + RÉGRESSION MULTIPLE** ⭐⭐⭐

**Principe :**
Ajouter features supplémentaires (surprise, volatilité, R²) et utiliser régression multiple au lieu de moyenne simple.

**Features proposées :**
1. **Surprise combinée** : `surprise_factor` (déjà calculé)
2. **Volatilité pré-event** : `volatility_24h` (écart-type prix 24h avant)
3. **R² tendance** : `r2_trend` (déjà calculé)
4. **Amplitude tendance** : `amplitude_trend_pips`
5. **Ratio score max/avg** : `max_score / avg_score` (dominance événement)

**Formule :**
```
impact = β₀ + β₁×score + β₂×n_events + β₃×surprise + β₄×volatility + β₅×r2_trend
```

**Avantages :**
- ✅ Utilise toutes informations disponibles
- ✅ Capture relations non-linéaires (avec features polynomiales)
- ✅ Interprétable (coefficients)

**Implémentation :**
```python
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

def predict_multiple_regression(
    X_train: np.array,  # Features : [score, n_events, surprise, volatility, r2]
    y_train: np.array,
    X_test: np.array,
    polynomial: bool = False
) -> float:
    """
    Prédit avec régression multiple.
    
    Features :
    - total_score
    - n_events
    - surprise_factor
    - volatility_24h
    - r2_trend
    """
    if polynomial:
        # Features polynomiales (interactions)
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_train = poly.fit_transform(X_train)
        X_test = poly.transform(X_test.reshape(1, -1))
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    prediction = model.predict(X_test)[0]
    
    return max(0, prediction)  # Pas d'impact négatif
```

**Gain estimé :** -4 à -8 pips (si features corrélées avec impact)

---

### **6. TIME-WEIGHTED AVERAGE** ⭐⭐

**Principe :**
Donner plus de poids aux cas récents (marché évolue, anciens cas moins pertinents).

**Formule :**
```
prediction = Σ(impact_i × exp(-age_i / τ)) / Σ(exp(-age_i / τ))

où age_i = jours depuis cas historique i
     τ = constante temps (ex: 180 jours)
```

**Avantages :**
- ✅ Simple à implémenter
- ✅ Adapte aux changements de marché
- ✅ Peut améliorer prédictions récentes

**Gain estimé :** -1 à -3 pips

---

### **7. ROBUST REGRESSION** ⭐⭐

**Principe :**
Utiliser régression robuste (Huber, RANSAC) qui ignore automatiquement les outliers.

**Avantages :**
- ✅ Robuste aux outliers
- ✅ Pas besoin de détecter outliers manuellement

**Gain estimé :** -2 à -4 pips (similaire à médiane)

---

### **8. BAYESIAN UPDATING** ⭐⭐⭐

**Principe :**
Mise à jour bayésienne : commencer avec prior (moyenne groupe), mettre à jour avec chaque nouveau cas.

**Formule :**
```
posterior = (prior × n_prior + new_impact) / (n_prior + 1)
```

**Avantages :**
- ✅ S'adapte automatiquement avec nouvelles données
- ✅ Gère incertitude (intervalles crédibles)

**Gain estimé :** -1 à -3 pips

---

## 🎯 RECOMMANDATIONS PAR PRIORITÉ

### **PRIORITÉ HAUTE** ⭐⭐⭐⭐

**1. Ensemble Methods**
- **Gain estimé :** -3 à -7 pips
- **Effort :** Moyen (2-3h)
- **Robustesse :** Très élevée
- **Recommandation :** ✅ **À IMPLÉMENTER EN PRIORITÉ**

**2. Feature Engineering + Régression Multiple**
- **Gain estimé :** -4 à -8 pips (si features corrélées)
- **Effort :** Élevé (4-6h)
- **Robustesse :** Élevée
- **Recommandation :** ✅ **À TESTER** (nécessite calcul volatilité)

**3. K-Nearest Neighbors**
- **Gain estimé :** -3 à -6 pips
- **Effort :** Faible (1-2h)
- **Robustesse :** Élevée
- **Recommandation :** ✅ **À IMPLÉMENTER**

---

### **PRIORITÉ MOYENNE** ⭐⭐⭐

**4. Régression Pondérée par Similarité**
- **Gain estimé :** -2 à -5 pips
- **Effort :** Moyen (2-3h)
- **Recommandation :** ⚠️ Tester après KNN (similaire)

**5. Régression Quantile**
- **Gain estimé :** -2 à -4 pips
- **Effort :** Faible (1h)
- **Recommandation :** ⚠️ Alternative à médiane simple

---

### **PRIORITÉ BASSE** ⭐⭐

**6. Time-Weighted Average**
- **Gain estimé :** -1 à -3 pips
- **Effort :** Très faible (30 min)
- **Recommandation :** ⚠️ Amélioration marginale

**7. Robust Regression**
- **Gain estimé :** -2 à -4 pips
- **Effort :** Faible (1h)
- **Recommandation :** ⚠️ Alternative à médiane

**8. Bayesian Updating**
- **Gain estimé :** -1 à -3 pips
- **Effort :** Moyen (2-3h)
- **Recommandation :** ⚠️ Complexité vs gain

---

## 📊 COMPARAISON MÉTHODES

| Méthode | Gain Estimé | Effort | Robustesse | Priorité |
|---------|-------------|--------|------------|----------|
| **Ensemble Methods** | -3 à -7 pips | Moyen | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Feature Engineering + Regression** | -4 à -8 pips | Élevé | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **K-Nearest Neighbors** | -3 à -6 pips | Faible | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Régression Pondérée** | -2 à -5 pips | Moyen | ⭐⭐⭐ | ⭐⭐⭐ |
| **Régression Quantile** | -2 à -4 pips | Faible | ⭐⭐⭐ | ⭐⭐⭐ |
| **Time-Weighted** | -1 à -3 pips | Très faible | ⭐⭐ | ⭐⭐ |
| **Robust Regression** | -2 à -4 pips | Faible | ⭐⭐⭐ | ⭐⭐ |
| **Bayesian** | -1 à -3 pips | Moyen | ⭐⭐⭐ | ⭐⭐ |

---

## 🚀 PLAN D'IMPLÉMENTATION RECOMMANDÉ

### **PHASE 1 : KNN (Rapide, Gain Élevé)** ⭐

**Objectif :** Implémenter KNN pour groupes avec MAE > 20 pips

**Actions :**
1. Créer fonction `predict_knn()` avec distance multi-features
2. Tester sur groupes problématiques (DOUBLE_WAVE_DOWN 300-400, etc.)
3. Valider avec LOO-CV
4. Comparer avec moyenne/médiane actuelle

**Durée estimée :** 1-2h

**Gain attendu :** -3 à -6 pips sur groupes hétérogènes

---

### **PHASE 2 : Ensemble Methods** ⭐⭐

**Objectif :** Combiner moyenne + médiane + KNN avec poids optimisés

**Actions :**
1. Implémenter `predict_ensemble()`
2. Optimiser poids avec validation croisée
3. Tester sur tous les groupes
4. Valider amélioration MAE global

**Durée estimée :** 2-3h

**Gain attendu :** -3 à -7 pips global

---

### **PHASE 3 : Feature Engineering** ⭐⭐⭐

**Objectif :** Ajouter features (volatilité, surprise) et régression multiple

**Actions :**
1. Calculer volatilité 24h pré-event pour tous les cas
2. Extraire surprise_factor pour tous les cas
3. Créer modèle régression multiple
4. Tester avec/sans features polynomiales
5. Valider amélioration

**Durée estimée :** 4-6h

**Gain attendu :** -4 à -8 pips (si corrélations fortes)

---

## 💡 MÉTHODE HYBRIDE RECOMMANDÉE

**Stratégie combinée :**

```
Si groupe taille >= 10 :
    → Ensemble (moyenne + médiane + KNN)
    
Si groupe taille 5-9 :
    → KNN (k=5) ou Médiane (si CV élevé)
    
Si groupe taille < 5 :
    → KNN global (tous groupes) ou Workflow Original (si cluster similaire)
```

**Avantages :**
- ✅ Adapte méthode selon taille groupe
- ✅ Combine forces de chaque approche
- ✅ Robuste pour tous les cas

---

## 📁 FICHIERS À CRÉER

```
scripts/investigation_clusters/methodes_amelioration/
├── predict_knn.py                    # K-Nearest Neighbors
├── predict_ensemble.py               # Ensemble Methods
├── predict_weighted_similarity.py   # Régression pondérée
├── predict_multiple_regression.py   # Feature engineering + régression
└── test_methodes_amelioration.py    # Script de test comparatif
```

---

## 🎯 CONCLUSION

### **Méthodes les Plus Prometteuses**

1. **Ensemble Methods** : Combinaison intelligente de plusieurs méthodes
2. **KNN** : Simple, efficace, robuste
3. **Feature Engineering + Régression** : Potentiel élevé si features corrélées

### **Recommandation**

**Commencer par KNN** (rapide, gain élevé), puis **Ensemble Methods** (meilleur gain potentiel).

**Gain total estimé :** -5 à -10 pips sur MAE global (14.69 → ~10-12 pips)

---

**Auteur :** André Valentin avec Claude  
**Date :** 16 novembre 2025  
**Statut :** 📋 PROPOSITIONS - PRÊT POUR IMPLÉMENTATION

