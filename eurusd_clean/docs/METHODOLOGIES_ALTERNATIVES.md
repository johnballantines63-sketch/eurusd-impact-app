# MÉTHODOLOGIES ALTERNATIVES - CATALOGUE COMPLET

**Date :** 3 novembre 2025  
**Contexte :** Session 109 - Analyse exhaustive  
**Objectif :** Documenter TOUTES les alternatives mathématiques disponibles

---

## 📐 PARTIE 1 : CARACTÉRISATION TENDANCE

### Méthode Actuelle (Session 107-108)

**R² Linéaire (Coefficient de Détermination)**

```python
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(X, y)
r2 = r_value ** 2  # 0 à 1
```

**Ce que ça mesure :**
- Proportion de variance expliquée par une ligne droite
- 0 = aucune relation linéaire
- 1 = relation linéaire parfaite

**Avantages :**
- ✅ Standard statistique
- ✅ Facile interpréter
- ✅ Rapide calculer

**Limitations :**
- ❌ Suppose tendance **LINÉAIRE**
- ❌ Sensible aux outliers
- ❌ Ignore direction (UP/DOWN)
- ❌ Pas de contexte temporel

---

## 🔢 ALTERNATIVES DISPONIBLES

### A. MÉTRIQUES LINÉAIRES

#### 1. R Pearson (avec signe)

**Formule :**
```python
r_pearson = linregress(X, y).rvalue  # -1 à +1
```

**Différence vs R² :**
- Garde le **signe** (UP = positif, DOWN = négatif)
- R² = r_pearson²

**Avantages :**
- ✅ Même que R² + garde direction

**Quand utiliser :**
- Direction importante pour prédiction

#### 2. Pente (Slope)

**Formule :**
```python
slope = linregress(X, y).slope
# Convertir en pips/heure
slope_pips_hour = slope * 10000 * 3600
```

**Ce que ça mesure :**
- Vitesse de la tendance
- Pips gagnés/perdus par heure

**Avantages :**
- ✅ Très intuitif
- ✅ Unité familière (pips/h)
- ✅ Capture vitesse

**Quand utiliser :**
- Momentum important

#### 3. Durée Tendance

**Formule :**
```python
duration_hours = (end_time - start_time).total_seconds() / 3600
```

**Ce que ça mesure :**
- Temps depuis début tendance
- Maturité tendance

**Avantages :**
- ✅ Simple
- ✅ Contexte temporel

**Quand utiliser :**
- Épuisement tendance

---

### B. MÉTRIQUES NON-LINÉAIRES

#### 4. R² Polynomial (degré 2)

**Formule :**
```python
# Fit parabole : y = ax² + bx + c
coeffs = np.polyfit(X, y, deg=2)
y_pred = np.polyval(coeffs, X)

# Calcul R²
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - np.mean(y))**2)
r2_poly2 = 1 - (ss_res / ss_tot)
```

**Ce que ça mesure :**
- Ajustement à une courbe (parabole)
- Capture accélération/décélération

**Avantages :**
- ✅ Détecte tendances courbes
- ✅ Capture sweet spots (maxima/minima)
- ✅ Pertinent pour Session 102 (U inversé)

**Quand utiliser :**
- Tendances paraboliques
- Marchés en accélération
- Bulles / Crashs

**Exemple Session 102 :**
```
R² linéaire = 0.08 (faible)
R² poly 2 = 0.35 (modéré)
→ Relation courbe U inversé !
```

#### 5. R² Polynomial (degré 3)

**Formule :**
```python
# Fit cubique : y = ax³ + bx² + cx + d
coeffs = np.polyfit(X, y, deg=3)
```

**Ce que ça mesure :**
- Courbes plus complexes (S)
- Multiples inflexions

**Avantages :**
- ✅ Plus flexible que deg 2

**Attention :**
- ⚠️ Risque overfitting avec N=17

#### 6. Spearman Rho (Rank Correlation)

**Formule :**
```python
from scipy.stats import spearmanr
rho, p_value = spearmanr(X, y)
rho_squared = rho ** 2  # Pour comparaison avec R²
```

**Ce que ça mesure :**
- Corrélation sur **rangs** (ordre)
- Détecte relations **MONOTONES** (croissant/décroissant)
- Pas besoin linéarité

**Avantages :**
- ✅ Robuste aux outliers
- ✅ Détecte relations non-linéaires monotones
- ✅ Ne suppose PAS linéarité

**Exemple :**
```
Prix : 1.10, 1.12, 1.18, 1.20
Rangs : 1, 2, 3, 4
→ Ordre parfait = Rho = 1.0

Même si relation exponentielle !
```

**Quand utiliser :**
- Relations courbes mais croissantes
- Outliers présents
- Petits échantillons

---

### C. MÉTRIQUES TRADING STANDARD

#### 7. ADX (Average Directional Index)

**Formule :**
```python
from ta.trend import ADXIndicator

adx = ADXIndicator(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    window=14  # Standard
)
adx_value = adx.adx().iloc[-1]  # 0 à 100
```

**Ce que ça mesure :**
- Force d'une tendance (UP ou DOWN)
- Standard : ADX > 25 = tendance forte

**Avantages :**
- ✅ Conçu SPÉCIFIQUEMENT pour force tendance
- ✅ Standard industrie trading
- ✅ Ne suppose PAS linéarité
- ✅ Fonctionne tendances complexes

**Interprétation :**
```
ADX < 20  : Pas de tendance (latéral)
ADX 20-25 : Tendance naissante
ADX 25-50 : Tendance forte
ADX > 50  : Tendance très forte
ADX > 75  : Tendance extrême (rare)
```

**Quand utiliser :**
- **TOUJOURS** pour tendances forex !
- Alternative R² dans contexte trading

**Potentiel Session 109 :**
```
R² linéaire = 0.08 (faible)
ADX = 60 (fort)
→ Tendance forte NON-LINÉAIRE !
```

#### 8. Amplitude Tendance

**Formule :**
```python
amplitude_pips = (high_max - low_min) * 10000
```

**Ce que ça mesure :**
- Excursion totale prix durant tendance
- Range en pips

**Avantages :**
- ✅ Simple
- ✅ Indépendant temps
- ✅ Capture volatilité

**Quand utiliser :**
- Tendances explosives
- Combiné avec durée

#### 9. Volatilité Tendance

**Formule :**
```python
volatility_pips = df['close'].std() * 10000
```

**Ce que ça mesure :**
- Écart-type prix
- Agitation marché

**Avantages :**
- ✅ Standard statistique
- ✅ Mesure incertitude

**Quand utiliser :**
- Marché chaotique vs stable

---

### D. MÉTRIQUES STATISTIQUES AVANCÉES

#### 10. Hurst Exponent

**Formule :**
```python
from hurst import compute_Hc
H, c, data = compute_Hc(prices, kind='price')
```

**Ce que ça mesure :**
- Persistance / Anti-persistance série temporelle
- Prédictibilité marché

**Interprétation :**
```
H < 0.5  : Mean-reverting (retour moyenne)
H = 0.5  : Random walk (marche aléatoire)
H > 0.5  : Trending (tendance persistante)

Exemples :
H = 0.3  : Fort mean-revert (fausse tendance)
H = 0.7  : Vraie tendance (momentum)
```

**Avantages :**
- ✅ Distingue **vraie tendance** vs bruit
- ✅ Académique (quant finance)
- ✅ Théorie solide (fractals)

**Quand utiliser :**
- Valider qualité tendance
- R² élevé mais H < 0.5 → Fausse tendance !

**Potentiel Session 109 :**
```
Cas A : R²=0.9, H=0.3 → Fausse tendance (mean-revert)
Cas B : R²=0.9, H=0.7 → Vraie tendance (persistent)
```

#### 11. Autocorrélation Lag 1

**Formule :**
```python
from statsmodels.tsa.stattools import acf
autocorr_lag1 = acf(prices, nlags=1, fft=False)[1]
```

**Ce que ça mesure :**
- Corrélation prix(t) avec prix(t-1)
- Mémoire série temporelle

**Interprétation :**
```
Autocorr proche 1  : Forte persistance (tendance)
Autocorr proche 0  : Pas de mémoire (random)
Autocorr proche -1 : Anti-persistance (oscillations)
```

**Avantages :**
- ✅ Simple
- ✅ Standard séries temporelles
- ✅ Mesure momentum

**Quand utiliser :**
- Validation tendance
- Alternative Hurst (plus simple)

#### 12. Entropie Shannon

**Formule :**
```python
from scipy.stats import entropy
# Discrétiser returns
returns_binned = pd.cut(returns, bins=10).value_counts()
ent = entropy(returns_binned)
```

**Ce que ça mesure :**
- Désordre / Prédictibilité
- Information contenue

**Interprétation :**
```
Entropie basse : Prévisible (tendance claire)
Entropie haute : Chaos (marché aléatoire)
```

**Avantages :**
- ✅ Théorie information
- ✅ Mesure complexité

**Quand utiliser :**
- Marchés complexes
- Académique

---

### E. MÉTRIQUES NON-PARAMÉTRIQUES

#### 13. Kendall Tau

**Formule :**
```python
from scipy.stats import kendalltau
tau, p_value = kendalltau(X, y)
```

**Ce que ça mesure :**
- Concordance rangs (comme Spearman)
- Encore plus robuste

**Avantages :**
- ✅ Plus robuste que Spearman
- ✅ Mieux pour petits échantillons (N=17)

**Quand utiliser :**
- Alternative Spearman
- Outliers extrêmes

---

## 📊 PARTIE 2 : MÉTHODES CORRÉLATION

### Méthode Actuelle (Session 108)

**Pearson Correlation (Linéaire)**

```python
from scipy.stats import pearsonr
r, p_value = pearsonr(metric_values, amp_optimal)
```

**Ce que ça mesure :**
- Relation **LINÉAIRE** entre deux variables
- amp = a × metric + b (ligne droite)

**Avantages :**
- ✅ Standard statistique
- ✅ Test significativité (p-value)

**Limitations :**
- ❌ Ne capte QUE relations linéaires
- ❌ Rate relations courbes (U inversé, exponentielle)
- ❌ Sensible outliers

---

## 🔢 ALTERNATIVES DISPONIBLES

### A. CORRÉLATIONS NON-LINÉAIRES

#### 1. Spearman Correlation

**Formule :**
```python
from scipy.stats import spearmanr
rho, p_value = spearmanr(metric_values, amp_optimal)
```

**Ce que ça mesure :**
- Relation **MONOTONE** (croissante ou décroissante)
- Pas besoin linéarité
- Travaille sur rangs

**Avantages :**
- ✅ Capte relations courbes monotones
- ✅ Robuste outliers
- ✅ Test significativité (p-value)

**Exemple Session 102 :**
```
Pearson r = +0.08 (nul)
Spearman rho = +0.45 (modéré)
→ Relation courbe croissante !
```

**Quand utiliser :**
- **TOUJOURS tester avec Pearson**
- Relations U, exponentielle, log
- Si Spearman >> Pearson → Relation non-linéaire

#### 2. Kendall Tau

**Formule :**
```python
from scipy.stats import kendalltau
tau, p_value = kendalltau(metric_values, amp_optimal)
```

**Ce que ça mesure :**
- Concordance (comme Spearman)
- Encore plus robuste

**Avantages :**
- ✅ Meilleur que Spearman pour N < 20
- ✅ Très robuste outliers

**Quand utiliser :**
- Petits échantillons (N=17 ici !)
- Alternative Spearman

#### 3. Distance Correlation

**Formule :**
```python
# Utiliser library dcor
import dcor
dist_corr = dcor.distance_correlation(metric_values, amp_optimal)
```

**Ce que ça mesure :**
- **TOUTE dépendance** (linéaire + non-linéaire)
- Distance Corr = 0 ⟺ Indépendance complète

**Avantages :**
- ✅ Capte relations complexes
- ✅ Si = 0 → vraiment indépendant

**Quand utiliser :**
- Vérifier si dépendance existe
- Pearson et Spearman faibles

#### 4. Mutual Information

**Formule :**
```python
from sklearn.feature_selection import mutual_info_regression
mi = mutual_info_regression(
    metric_values.reshape(-1, 1),
    amp_optimal
)[0]
```

**Ce que ça mesure :**
- Information partagée entre variables
- Théorie information

**Avantages :**
- ✅ Capte dépendances complexes
- ✅ Pas d'hypothèse forme relation

**Quand utiliser :**
- Relations très complexes
- Machine Learning

---

### B. RÉGRESSIONS

#### 5. Régression Linéaire

**Formule :**
```python
from scipy.stats import linregress
slope, intercept, r, p, std_err = linregress(metric, amp_optimal)
r2 = r ** 2
```

**Ce que ça donne :**
- Équation : amp = slope × metric + intercept
- R² = proportion variance expliquée

**Avantages :**
- ✅ Formule utilisable directement
- ✅ Test significativité

**Quand utiliser :**
- Créer formule prédictive

#### 6. Régression Polynomiale Degré 2

**Formule :**
```python
# Fit parabole
coeffs = np.polyfit(metric, amp_optimal, deg=2)
# amp = a × metric² + b × metric + c

# Prédictions
amp_pred = np.polyval(coeffs, metric)

# R²
ss_res = np.sum((amp_optimal - amp_pred)**2)
ss_tot = np.sum((amp_optimal - np.mean(amp_optimal))**2)
r2_poly2 = 1 - (ss_res / ss_tot)
```

**Ce que ça donne :**
- Équation parabole
- Capture maxima/minima (sweet spots)

**Avantages :**
- ✅ Capte U inversé (Session 102 !)
- ✅ Formule utilisable

**Quand utiliser :**
- **PRIORITAIRE Session 109**
- Relation U inversé suspectée

**Exemple :**
```
R² linéaire = 0.08
R² poly 2 = 0.35
→ Relation courbe significative !

Formule : amp = -2.5×R² + 3.0×R² + 1.2
Sweet spot : R² = 0.6 → amp_max
```

#### 7. Régression Polynomiale Degré 3

**Formule :**
```python
coeffs = np.polyfit(metric, amp_optimal, deg=3)
# amp = a × metric³ + b × metric² + c × metric + d
```

**Avantages :**
- ✅ Encore plus flexible

**Attention :**
- ⚠️ Overfitting risque avec N=17

#### 8. LOWESS (Locally Weighted Scatterplot Smoothing)

**Formule :**
```python
from statsmodels.nonparametric.smoothers_lowess import lowess
smoothed = lowess(amp_optimal, metric, frac=0.3)
```

**Ce que ça donne :**
- Courbe lisse suivant données
- Révèle forme vraie relation

**Avantages :**
- ✅ Aucune hypothèse forme
- ✅ Visualisation excellente

**Quand utiliser :**
- Explorer forme relation
- Graphiques

#### 9. GAM (Generalized Additive Models)

**Formule :**
```python
from pygam import LinearGAM
gam = LinearGAM().fit(metric, amp_optimal)
```

**Avantages :**
- ✅ Maximum flexibilité
- ✅ Automatique

**Quand utiliser :**
- Relations très complexes

---

## 📊 RÉCAPITULATIF COMPARATIF

### Pour Caractérisation Tendance

| Métrique | Type | Complexité | Robustesse | Interprétabilité |
|----------|------|------------|------------|------------------|
| **R²** | Linéaire | Faible | Moyenne | ✅ Excellente |
| **R Pearson** | Linéaire | Faible | Moyenne | ✅ Excellente |
| **Pente** | Linéaire | Faible | Moyenne | ✅ Excellente |
| **R² Poly 2** | Non-linéaire | Moyenne | Moyenne | ✅ Bonne |
| **Spearman** | Non-linéaire | Faible | ✅ Haute | ✅ Bonne |
| **ADX** | Trading | Moyenne | ✅ Haute | ✅ Excellente |
| **Hurst** | Avancée | Haute | Moyenne | ⚠️ Moyenne |
| **Autocorr** | Avancée | Faible | Moyenne | ✅ Bonne |

### Pour Méthodes Corrélation

| Méthode | Capte Linéaire | Capte Non-Linéaire | P-value | Formule Utilisable |
|---------|----------------|-------------------|---------|-------------------|
| **Pearson** | ✅ | ❌ | ✅ | ✅ (y=ax+b) |
| **Spearman** | ✅ | ✅ (monotone) | ✅ | ❌ |
| **Kendall** | ✅ | ✅ (monotone) | ✅ | ❌ |
| **Linéaire** | ✅ | ❌ | ✅ | ✅ (y=ax+b) |
| **Poly 2** | ✅ | ✅ (parabole) | ⚠️ | ✅ (y=ax²+bx+c) |
| **Poly 3** | ✅ | ✅ (cubique) | ⚠️ | ✅ (complexe) |
| **Distance** | ✅ | ✅ (tout) | ❌ | ❌ |
| **MI** | ✅ | ✅ (tout) | ❌ | ❌ |

---

## 🎯 RECOMMANDATIONS SESSION 109

### Priorité 1 : OBLIGATOIRES

**Ces métriques/méthodes DOIVENT être testées :**

1. **ADX** (standard trading)
2. **Spearman** (corrélation robuste)
3. **Poly 2** (U inversé Session 102)
4. **Hurst** (persistance)

### Priorité 2 : IMPORTANTES

5. R Pearson (avec signe)
6. Pente (pips/heure)
7. Kendall (robuste N=17)
8. R² Poly 2

### Priorité 3 : COMPLÉMENTAIRES

9. Durée, Amplitude, Volatilité
10. Autocorrélation
11. R² Poly 3
12. Distance, MI (si temps)

### Combinaisons Prometteuses

**À surveiller spécialement :**
- **ADX + Spearman** (robuste trading)
- **Hurst + Poly 2** (persistance + U inversé)
- **R² + Poly 2** (linéaire + courbe)
- **Pente + Spearman** (vitesse + monotone)

---

## 📚 RÉFÉRENCES

### Librairies Python

```python
# Statistiques
from scipy.stats import pearsonr, spearmanr, kendalltau, linregress
from scipy.stats import entropy
from scipy.spatial.distance import pdist, squareform

# Trading
from ta.trend import ADXIndicator

# Avancées
from hurst import compute_Hc
from statsmodels.tsa.stattools import acf
from statsmodels.nonparametric.smoothers_lowess import lowess
from pygam import LinearGAM

# ML
from sklearn.metrics import mutual_info_score
from sklearn.feature_selection import mutual_info_regression
import dcor  # Distance correlation
```

### Installation

```bash
pip install scipy
pip install ta  # Technical Analysis
pip install hurst
pip install statsmodels
pip install pygam
pip install scikit-learn
pip install dcor
```

---

**FIN METHODOLOGIES_ALTERNATIVES.md**

*Document créé : 3 novembre 2025*  
*Catalogue exhaustif : 12 métriques × 9 corrélations*  
*Référence complète Session 109*
