# Résumé Analyses et Corrections - Mouvements Prédictibles

**Date** : 2025-01-XX  
**Objectif** : Identifier la meilleure formule de prédiction d'impact pour les mouvements prédictibles

---

## 📊 CONTEXTE

- **2,379 mouvements prédictibles** détectés (97.6% des mouvements avec événements)
- **59 mouvements non prédictibles** (2.4% sans événements) → exclus de l'analyse
- Base de données complète avec clusters, noyaux durs, scores, surprises

---

## 🔍 PROBLÈME IDENTIFIÉ

### Formule Actuelle (`calculate_impact_d`)
- **MAE** : 38.63 pips
- **Ratio médian** : 0.152 (prédictions ≈ 15% de la réalité)
- **Corrélation** : 0.232
- **Problème majeur** : Sous-estimation systématique, surtout pour mouvements FORT/TRÈS_FORT

### Analyse par Classe (Formule Actuelle)
| Classe | MAE | Ratio médian | Impact réel moy | Impact prédit moy |
|--------|-----|--------------|-----------------|-------------------|
| FAIBLE | 25.99 pips | 0.461 | 32.3 pips | 8.5 pips |
| MOYEN | 35.30 pips | 0.587 | 50.0 pips | 11.2 pips |
| **FORT** | **57.61 pips** | **0.401** | **77.2 pips** | **15.3 pips** |
| **TRÈS_FORT** | **73.72 pips** | **0.344** | **111.6 pips** | **17.2 pips** |

**Conclusion** : La formule actuelle est **défaillante** pour les mouvements forts.

---

## ✅ SOLUTIONS TESTÉES

### 1. Formule Linéaire Multiple (MEILLEURE GLOBALE)

**Formule** :
```
impact = 30.5450 
       + 0.4692 * base_score
       + 0.1882 * adjusted_score
       + 0.0201 * surprise_avg
       - 0.0034 * surprise_max
       + 0.7355 * n_events
```

**Performance** :
- **MAE** : 13.98 pips (vs 38.63 base) → **-64% d'erreur**
- **Ratio médian** : 1.091 (presque parfait)
- **Corrélation** : 0.364 (vs 0.232 base)

**Analyse par classe** :
| Classe | MAE | Ratio médian |
|--------|-----|--------------|
| FAIBLE | 14.34 pips | 1.414 |
| MOYEN | 7.79 pips | 0.994 ✅ |
| FORT | 23.10 pips | 0.685 ⚠️ |
| TRÈS_FORT | 55.18 pips | 0.501 ⚠️ |

**Avantages** :
- ✅ Meilleure performance globale
- ✅ Utilise uniquement features prédictives (calculables AVANT le mouvement)
- ✅ Pas besoin de connaître la classe de mouvement

**Inconvénients** :
- ⚠️ Sous-estime encore FORT (ratio 0.685) et TRÈS_FORT (ratio 0.501)

---

### 2. Formule Linéaire + Correctif Basé sur Prédiction

**Formule** :
1. Calculer prédiction linéaire (voir ci-dessus)
2. Si `impact_linear > 65.0 pips` → multiplier par 1.30x

**Performance** :
- **MAE** : 27.78 pips
- **Ratio médian** : 1.479
- **Corrélation** : 0.289

**Analyse par classe** :
| Classe | MAE | Ratio médian |
|--------|-----|--------------|
| FAIBLE | 32.79 pips | 1.744 |
| MOYEN | 24.48 pips | 1.360 |
| FORT | 23.11 pips | 1.191 ✅ |
| TRÈS_FORT | 32.42 pips | 0.719 ⚠️ |

**Avantages** :
- ✅ Améliore FORT (ratio 1.191)
- ✅ Simple à implémenter

**Inconvénients** :
- ⚠️ TRÈS_FORT encore sous-estimé (ratio 0.719)
- ⚠️ Surestime FAIBLE et MOYEN

---

### 3. Formule Puissance

**Formule** :
```
impact = 40.4205 * impact_base^0.0733
```

**Performance** :
- **MAE** : 14.27 pips
- **Ratio médian** : 1.042
- **Corrélation** : 0.185

**Analyse par classe** :
| Classe | MAE | Ratio médian |
|--------|-----|--------------|
| FAIBLE | 13.01 pips | 1.403 |
| MOYEN | 7.28 pips | 0.946 ✅ |
| FORT | 29.77 pips | 0.620 ⚠️ |
| TRÈS_FORT | 63.88 pips | 0.448 ⚠️ |

**Problème** : Nécessite `impact_base` (formule actuelle défaillante)

---

## 🏆 RECOMMANDATION FINALE

### Solution Recommandée : **Formule Linéaire Multiple**

**Raisons** :
1. ✅ Meilleure performance globale (MAE 13.98 pips)
2. ✅ Utilise uniquement features prédictives (pas besoin de connaître classe)
3. ✅ Ratio médian proche de 1.0 (1.091)
4. ✅ Meilleure corrélation (0.364)

**Limitation acceptée** :
- ⚠️ Sous-estime FORT (ratio 0.685) et TRÈS_FORT (ratio 0.501)
- ✅ **Solution** : Utiliser stratégie de sortie à 85% de la prédiction pour maximiser win rate

---

## 💡 STRATÉGIE DE SORTIE OPTIMALE

Basée sur l'analyse du biais :

### Pour Tous les Mouvements
- **Sortir à 85% de la prédiction**
- **Win Rate attendu** : 99.2%
- **Gain moyen** : 8.89 pips/trade

### Pour Mouvements FORT/TRÈS_FORT Spécifiquement
- **Sortir à 85% de la prédiction**
- **Win Rate attendu** : 100.0% (159/159 trades gagnants)
- **Gain moyen** : 13.66 pips/trade

**Raison** : Même si les prédictions sont sous-estimées, sortir à 85% capture le mouvement dans la plupart des cas.

---

## 📋 FORMULE FINALE À IMPLÉMENTER

```python
def calculate_impact_corrected(row: pd.Series) -> float:
    """
    Calcule l'impact prédit avec formule linéaire multiple optimisée
    """
    intercept = 30.5450
    coef_base_score = 0.4692
    coef_adjusted_score = 0.1882
    coef_surprise_avg = 0.0201
    coef_surprise_max = -0.0034
    coef_n_events = 0.7355
    
    base_score = row['avg_base_empirical_score'] if pd.notna(row['avg_base_empirical_score']) else 0.0
    adjusted_score = row['avg_adjusted_empirical_score'] if pd.notna(row['avg_adjusted_empirical_score']) else 0.0
    surprise_avg = row['avg_surprise_pct'] if pd.notna(row['avg_surprise_pct']) else 0.0
    surprise_max = row['max_surprise_pct'] if pd.notna(row['max_surprise_pct']) else 0.0
    n_events = row['n_events_total'] if pd.notna(row['n_events_total']) else 0.0
    
    impact = (intercept +
              coef_base_score * base_score +
              coef_adjusted_score * adjusted_score +
              coef_surprise_avg * surprise_avg +
              coef_surprise_max * surprise_max +
              coef_n_events * n_events)
    
    return max(impact, 0.0)

def calculate_exit_target(impact_predicted: float, exit_pct: float = 85.0) -> float:
    """
    Calcule le target de sortie (85% de la prédiction par défaut)
    """
    return impact_predicted * (exit_pct / 100.0)
```

---

## 📊 FICHIERS GÉNÉRÉS

- `predictable_movements_database.csv` : Base complète (2,379 mouvements)
- `predictions_direct_from_features.csv` : Prédictions avec formule linéaire
- `best_direct_formula_from_features.csv` : Formule optimale
- `exit_strategies_filtered_us.csv` : Comparaison stratégies de sortie
- `recommended_exit_strategy_filtered_us.csv` : Recommandation finale

---

## ✅ PROCHAINES ÉTAPES

1. **Implémenter formule linéaire multiple** dans le pipeline
2. **Intégrer stratégie de sortie** (85% de la prédiction)
3. **Tester en conditions réelles** sur nouvelles dates
4. **Ajuster si nécessaire** selon résultats

---

**Dernière mise à jour** : 2025-01-XX


