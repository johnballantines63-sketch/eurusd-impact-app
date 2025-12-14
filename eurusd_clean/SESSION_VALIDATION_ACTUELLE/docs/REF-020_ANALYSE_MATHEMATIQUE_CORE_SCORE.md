# REF-020 : Analyse Mathématique - core_score comme Calibration vs Feature RF

**Date :** 2025-12-06  
**Question :** Quelle approche est la plus pertinente mathématiquement : facteur de calibration ou feature Random Forest ?

---

## 📊 DONNÉES DISPONIBLES

### Données Test (4 dates)

| Date | Core Type | Score DB | Impact Réel | Ratio | Surprise |
|------|-----------|----------|-------------|-------|----------|
| 2025-09-11 | CPI | 75.06 | 62.40 | 0.831 | 33.36% |
| 2025-05-29 | JOBLESS_PCE | 53.51 | 89.40 | 1.671 | 3.03% |
| 2025-08-01 | NFP | 80.13 | 188.40 | 2.348 | 50.64% |
| 2025-11-20 | NFP | 80.13 | 35.50 | 0.443 | 194.45% |

**Observations :**
- Ratio variable : 0.443 à 2.348 (CV élevé)
- Même core_type (NFP) → ratios très différents (0.443 vs 2.348)
- Surprise élevée (194%) → ratio faible (0.443)

---

## 🔬 ANALYSE MATHÉMATIQUE

### Option 1 : Facteur de Calibration (Multiplicateur Fixe)

**Formule :**
```python
ratio_mean = mean(impact_real / core_score)  # Par core_type
impact_predicted = (impact_base * amplification) * ratio_mean
```

**Hypothèses :**
- Relation linéaire : `impact_real = core_score × ratio_mean`
- Ratio constant pour chaque core_type
- Pas de dépendance contextuelle

**Avantages Mathématiques :**
- ✅ Simplicité (1 paramètre par core_type)
- ✅ Interprétabilité (ratio = correction biais)
- ✅ Stabilité si ratio constant

**Inconvénients Mathématiques :**
- ❌ Perte d'information si ratio variable
- ❌ Pas de prise en compte du contexte (surprise, tendance, etc.)
- ❌ Erreur élevée si variance du ratio importante

**Critères de Validité :**
- **CV (Coefficient de Variation) < 0.3** : Ratio stable
- **R² > 0.5** : Relation linéaire forte
- **Corrélation > 0.5** : Relation significative

---

### Option 2 : Feature Random Forest

**Formule :**
```python
features = [
    impact_base,
    amplification,
    core_score,        # ← Feature supplémentaire
    surprise_abs,
    trend_direction,
    n_core_events,
    ...
]
impact_predicted = RF.predict(features)
```

**Hypothèses :**
- Relation non-linéaire ou contextuelle
- core_score interagit avec autres features
- RF apprend la relation complexe

**Avantages Mathématiques :**
- ✅ Capture relations non-linéaires
- ✅ Prise en compte du contexte (surprise, tendance, etc.)
- ✅ Interaction entre features
- ✅ Adaptation aux patterns complexes

**Inconvénients Mathématiques :**
- ❌ Complexité (plus de paramètres)
- ❌ Moins interprétable (boîte noire)
- ❌ Nécessite plus de données d'entraînement

**Critères de Validité :**
- **CV >= 0.3** : Ratio variable
- **R² <= 0.5** : Relation non-linéaire
- **Corrélation <= 0.5** : Relation faible

---

## 📈 ANALYSE DES DONNÉES TEST

### Calculs sur les 4 dates

**CPI (1 date) :**
- Ratio : 0.831
- CV : N/A (1 seule valeur)
- **Insufficient pour conclure**

**JOBLESS_PCE (1 date) :**
- Ratio : 1.671
- CV : N/A (1 seule valeur)
- **Insufficient pour conclure**

**NFP (2 dates) :**
- Ratios : 0.443, 2.348
- Ratio moyen : 1.396
- Ratio std : 1.348
- **CV = 0.966** (très élevé !)
- **Conclusion : Ratio très variable**

### Interprétation

**Pour NFP :**
- Ratio varie de 0.443 à 2.348 (facteur 5.3x)
- CV = 0.966 >> 0.3 → **Ratio instable**
- Même core_score (80.13) → impacts très différents (35.5 vs 188.4 pips)
- **Cause probable :** Contexte différent (surprise, tendance, etc.)

**Conclusion préliminaire :**
- ⚠️ **Ratios très variables** → Facteur de calibration risqué
- ✅ **Feature RF** plus approprié pour capturer la variabilité

---

## 🎯 ANALYSE THÉORIQUE

### Scénario A : Relation Linéaire Simple

**Si :** `impact_real = α × core_score + ε`

**Où :**
- `α` = ratio constant
- `ε` = erreur aléatoire (faible variance)

**Alors :**
- ✅ **Facteur de calibration** optimal
- Formule : `impact_predicted = core_score × α`
- Erreur minimale si variance(ε) faible

### Scénario B : Relation Contextuelle

**Si :** `impact_real = f(core_score, surprise, trend, ...)`

**Où :**
- `f` = fonction non-linéaire
- Dépend de plusieurs variables contextuelles

**Alors :**
- ✅ **Feature RF** optimal
- RF apprend : `impact_predicted = RF(core_score, surprise, trend, ...)`
- Capture interactions entre variables

### Scénario C : Relation Hybride

**Si :** `impact_real = α × core_score × g(surprise, trend, ...)`

**Où :**
- `α` = ratio de base
- `g` = facteur contextuel

**Alors :**
- ✅ **Feature RF** avec core_score comme feature
- RF apprend la fonction `g` et l'interaction avec `core_score`

---

## 💡 RECOMMANDATION MATHÉMATIQUE

### Analyse des Données Test

**Observations :**
1. **Ratio très variable** pour NFP (CV = 0.966)
2. **Même core_score** → impacts très différents
3. **Surprise élevée** (194%) → ratio faible (0.443)
4. **Surprise modérée** (50%) → ratio élevé (2.348)

**Conclusion :**
- La relation n'est **pas linéaire simple**
- Le ratio dépend du **contexte** (surprise, tendance, etc.)
- **Feature RF** plus approprié mathématiquement

### Recommandation Finale

**✅ Option 2 : Feature Random Forest (RECOMMANDÉ)**

**Raisons Mathématiques :**
1. **CV élevé** (0.966 pour NFP) → Ratio instable
2. **Relation contextuelle** → Dépend de surprise, tendance, etc.
3. **Interactions complexes** → RF peut les capturer
4. **Adaptation** → RF s'adapte aux patterns non-linéaires

**Implémentation :**
```python
# Features pour Random Forest
features = {
    'impact_base': impact_base,
    'amplification': amplification_predite,
    'core_score': core_score_db,           # ← Feature supplémentaire
    'surprise_abs': abs(surprise_net),
    'surprise_net': surprise_net,
    'trend_direction': trend_direction,
    'trend_strength': trend_strength,
    'n_core_events': n_core_events,
    'n_clusters_identiques': len(identical_clusters)
}

# RF apprend la relation
impact_predicted = rf_model.predict([features])
```

**Avantages :**
- ✅ Capture relations non-linéaires
- ✅ Prise en compte du contexte
- ✅ Interaction entre core_score et autres features
- ✅ Adaptation aux patterns complexes

---

## 🔄 APPROCHE HYBRIDE (Alternative)

### Option 3 : Calibration + Feature RF

**Principe :**
1. Utiliser **ratio moyen** comme baseline
2. Utiliser **core_score** comme feature RF pour ajustement

**Formule :**
```python
# Baseline avec ratio moyen
impact_baseline = (impact_base * amplification) * ratio_mean

# Ajustement RF avec core_score comme feature
features = {
    'impact_baseline': impact_baseline,
    'core_score': core_score_db,
    'surprise_abs': abs(surprise_net),
    ...
}
impact_adjusted = rf_model.predict([features])
```

**Avantages :**
- ✅ Combine simplicité (baseline) et flexibilité (RF)
- ✅ RF ajuste selon contexte
- ✅ Interprétabilité partielle (baseline visible)

**Inconvénients :**
- ❌ Plus complexe
- ❌ Nécessite plus de données

---

## 📊 COMPARAISON MATHÉMATIQUE

| Critère | Calibration | Feature RF | Hybride |
|---------|-------------|------------|---------|
| **Simplicité** | ✅ Très simple | ⚠️ Complexe | ⚠️ Moyen |
| **Interprétabilité** | ✅ Élevée | ❌ Faible | ⚠️ Moyenne |
| **Précision (ratio stable)** | ✅ Élevée | ⚠️ Moyenne | ✅ Élevée |
| **Précision (ratio variable)** | ❌ Faible | ✅ Élevée | ✅ Élevée |
| **Prise en compte contexte** | ❌ Non | ✅ Oui | ✅ Oui |
| **Données nécessaires** | ✅ Faible | ❌ Élevée | ❌ Élevée |
| **Robustesse** | ⚠️ Moyenne | ✅ Élevée | ✅ Élevée |

---

## ✅ CONCLUSION

### Recommandation Mathématique

**✅ Feature Random Forest (Option 2)**

**Justification :**
1. **CV élevé** (0.966) → Ratios instables
2. **Relation contextuelle** → Dépend de surprise, tendance
3. **Interactions complexes** → RF peut les capturer
4. **Adaptation** → RF s'adapte aux patterns

**Implémentation Prioritaire :**
- Ajouter `core_score` comme feature dans Random Forest
- Conserver clusters identiques pour entraînement
- RF apprend la relation : `impact = f(core_score, surprise, trend, ...)`

**Validation Requise :**
- Remplir `core_scores_by_date` avec plus de dates
- Calculer CV et R² pour chaque core_type
- Confirmer variabilité des ratios

---

**Document créé le :** 2025-12-06  
**Dernière mise à jour :** 2025-12-06




