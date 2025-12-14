# REF-005 : ANALYSE FONDEMENTS MATHÉMATIQUES - SCORES EMPIRIQUES

**Référence :** REF-005  
**Date de création :** 2025-12-06  
**Heure de création :** 12:10:00  
**Dernière mise à jour :** 2025-12-06 12:35:00  
**Auteur :** André Valentin avec Claude  
**Version :** 1.1

---

## 📋 OBJECTIF

Analyser les fondements mathématiques de la formule de calcul des scores empiriques pour valider sa robustesse avant un recalcul complet sur toutes les années.

---

## 🔍 FORMULE ACTUELLE (Session 123)

### Formule Complète

```python
base_score = (avg_movement * 0.5 + p80_movement * 0.5)
robustness = facteur basé sur sample_size
score = base_score * robustness
normalized = min(100.0, (score / 100.0) * 100.0)
```

### Composants

1. **Moyenne pondérée (50% avg + 50% p80)**
   - `avg_movement` : Impact moyen en pips
   - `p80_movement` : Impact au 80e percentile en pips
   - Pondération : 50% / 50%

2. **Facteur robustesse**
   - `sample_size >= 20` : robustness = 1.0
   - `sample_size >= 10` : robustness = 0.9
   - `sample_size >= 5` : robustness = 0.8
   - `sample_size < 5` : robustness = 0.7

3. **Normalisation**
   - `(score / 100.0) * 100.0` = score (redondant)
   - Plafond à 100.0

---

## ⚠️ PROBLÈMES IDENTIFIÉS

### 1. Normalisation Redondante

**Problème :**
```python
normalized = min(100.0, (score / 100.0) * 100.0)
```

**Analyse :**
- `(score / 100.0) * 100.0 = score` (opération redondante)
- Le `min(100.0, ...)` est le seul effet réel
- **Impact** : Code inutile, pas d'erreur fonctionnelle

**Correction proposée :**
```python
normalized = min(100.0, score)  # Plus simple et clair
```

### 2. Pondération 50/50 Non Justifiée

**Problème :**
- Pas de justification théorique pour la pondération 50/50
- Pourquoi 50% avg et 50% p80 ?
- Pourquoi pas 30/70, 70/30, ou 100% p80 ?

**Analyse :**
- **avg_movement** : Sensible aux outliers, représente l'impact moyen
- **p80_movement** : Robuste aux outliers, représente l'impact dans 80% des cas
- **50/50** : Compromis entre les deux, mais arbitraire

**Alternatives testées :**
- **P80 uniquement** : Plus robuste, plus simple
- **Moyenne géométrique** : Meilleure pour données asymétriques
- **P80 + facteur CV** : Prend en compte la variance

### 3. Facteur Robustesse Arbitraire

**Problème :**
- Seuils (5, 10, 20) non justifiés statistiquement
- Pas de validation empirique de ces seuils
- Pas de prise en compte de la variance

**Analyse :**
- **Logique** : Plus d'échantillons = plus de confiance ✅
- **Seuils** : Arbitraires (pourquoi 5, 10, 20 ?) ❌
- **Variance** : Ignorée (même variance, même robustesse) ❌

**Alternative proposée :**
- Utiliser le **coefficient de variation** (CV = std / mean)
- Robustesse = f(CV, sample_size)
- Plus faible variance → plus de robustesse

### 4. Pas de Prise en Compte de la Variance

**Problème :**
- La formule ignore complètement l'écart-type
- Deux événements avec même avg et p80 mais variances différentes → même score

**Exemple :**
- Événement A : avg=20, p80=25, std=5 (stable)
- Événement B : avg=20, p80=25, std=15 (variable)
- **Score identique** malgré variance différente

**Impact :**
- Événements instables peuvent avoir le même score que des événements stables
- Pas de distinction entre prédictibilité faible vs forte

---

## 📊 COMPARAISON MÉTHODES ALTERNATIVES

### Test sur Échantillon (50 événements CPI US)

| Méthode | Score | Différence vs Actuelle | Robustesse | Simplicité |
|---------|-------|------------------------|------------|------------|
| **Actuelle (50% avg + 50% p80)** | 22.93 | - | ⭐⭐⭐ | ⭐⭐⭐ |
| P80 uniquement | 25.87 | +2.94 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Médiane uniquement | 17.87 | -5.06 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Moyenne + Écart-type | 29.76 | +6.83 | ⭐⭐ | ⭐⭐⭐ |
| P80 + Robustesse CV | 13.24 | -9.69 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Moyenne géométrique | 17.94 | -4.99 | ⭐⭐⭐⭐ | ⭐⭐⭐ |

### Analyse des Résultats

**Méthode actuelle (50% avg + 50% p80) :**
- ✅ Compromis entre moyenne et percentile
- ✅ Robuste partiellement aux outliers
- ❌ Pondération arbitraire

**P80 uniquement :**
- ✅ Plus robuste aux outliers
- ✅ Plus simple
- ✅ Représente les cas typiques (80% des cas)
- ⚠️ Ignore les cas exceptionnels

**Médiane uniquement :**
- ✅ Très robuste aux outliers
- ✅ Représente le cas "médian"
- ⚠️ Sous-estime les impacts réels (tend à être plus bas)

**Moyenne + Écart-type :**
- ✅ Prend en compte la variance
- ❌ Sensible aux outliers
- ❌ Peut sur-estimer

**P80 + Robustesse CV :**
- ✅ Robuste aux outliers
- ✅ Prend en compte la variance
- ❌ Plus complexe
- ⚠️ Peut sous-estimer (dans notre test)

---

## 📚 COMPARAISON AVEC LITTÉRATURE

### Méthodes Courantes

1. **Percentile-Based** (utilisé ici)
   - ✅ Robuste aux outliers
   - ✅ Simple et interprétable
   - ❌ Ignore la variance complète

2. **Regression-Based**
   - ✅ Capture relations complexes
   - ✅ Validation statistique (R², p-value)
   - ❌ Nécessite plus de données
   - ❌ Plus complexe

3. **Machine Learning**
   - ✅ Capture relations non-linéaires
   - ✅ Meilleure précision potentielle
   - ❌ Boîte noire
   - ❌ Nécessite beaucoup de données

4. **Bayesian**
   - ✅ Intègre incertitude
   - ✅ Mise à jour continue
   - ❌ Complexité mathématique
   - ❌ Nécessite priors

---

## ✅ VALIDATION MATHÉMATIQUE

### Propriétés Statistiques

1. **Sensibilité aux Outliers**
   - `avg_movement` : **SENSIBLE** (moyenne arithmétique)
   - `p80_movement` : **ROBUSTE** (percentile)
   - **Formule 50/50** : **Partiellement robuste**

2. **Distribution**
   - Si normale : avg ≈ médiane ≈ p50
   - Si asymétrique : avg ≠ médiane, p80 > avg
   - **Formule actuelle** : Privilégie p80 (cas typiques)

3. **Robustesse**
   - Facteur basé sur sample_size : **Logique** ✅
   - Seuils arbitraires : **Non justifiés** ❌
   - Pas de variance : **Limitation** ❌

### Validité Mathématique

**✅ ACCEPTABLE mais PERFECTIBLE**

**Points forts :**
- Utilise P80 (robuste aux outliers)
- Facteur robustesse basé sur sample_size
- Simple et interprétable

**Points faibles :**
- Pondération 50/50 non justifiée
- Seuils robustesse arbitraires
- Normalisation redondante
- Pas de prise en compte de la variance

---

## 🎯 RECOMMANDATIONS

### Option 1 : Conserver Formule Actuelle (Recommandé pour l'instant)

**Justification :**
- ✅ Fonctionne (validé Session 123)
- ✅ Simple et interprétable
- ✅ Robuste partiellement aux outliers
- ⚠️ Perfectible mais acceptable

**Améliorations mineures :**
1. Corriger normalisation redondante
2. Documenter choix pondération 50/50
3. Valider seuils robustesse empiriquement

### Option 2 : Simplifier (P80 Uniquement)

**Formule :**
```python
score = p80_movement * robustness
normalized = min(100.0, score)
```

**Avantages :**
- ✅ Plus simple
- ✅ Plus robuste aux outliers
- ✅ Représente les cas typiques

**Inconvénients :**
- ⚠️ Ignore les cas exceptionnels
- ⚠️ Nécessite validation

### Option 3 : Améliorer (P80 + Robustesse CV)

**Formule :**
```python
cv = std / avg  # Coefficient de variation
robustness_cv = max(0.5, 1.0 - cv)  # Plus faible variance = plus robuste
score = p80_movement * robustness_cv * robustness_sample_size
normalized = min(100.0, score)
```

**Avantages :**
- ✅ Prend en compte la variance
- ✅ Robuste aux outliers
- ✅ Plus sophistiqué

**Inconvénients :**
- ⚠️ Plus complexe
- ⚠️ Nécessite validation

---

## 📊 TEST COMPARATIF SUR DONNÉES RÉELLES

**Date :** 2025-12-06  
**Script :** `test_formula_vs_p80_optimized.py`  
**Échantillon :** 50 événements US (les plus fréquents)

### Résultats

| Métrique | Valeur |
|----------|--------|
| **Différence moyenne** | 2.67 pips (13.0%) |
| **Différence médiane** | 2.38 pips (13.5%) |
| **Écart-type** | 0.80 pips |
| **Min** | 1.32 pips |
| **Max** | 5.03 pips (14.6%) |

### Observations

1. **Différence constante** : ~13% en moyenne
   - P80 uniquement donne des scores **plus élevés** que la formule actuelle
   - Écart stable entre les deux méthodes

2. **Exemples concrets** :
   - `initial jobless claims` : 34.57 (actuelle) vs 39.60 (P80) = **+5.03 pips (+14.5%)**
   - `mba purchase index` : 15.39 (actuelle) vs 17.50 (P80) = **+2.11 pips (+13.7%)**
   - `redbook yoy` : 20.87 (actuelle) vs 23.56 (P80) = **+2.69 pips (+12.9%)**

3. **Tous les événements ont un écart avg ≠ p80**
   - Indique des **distributions asymétriques**
   - P80 est systématiquement supérieur à la moyenne

### Conclusion Test

**⚠️ Les deux méthodes donnent des résultats proches mais avec des différences notables (~13%)**

**Analyse cas par cas :**
- Si beaucoup d'outliers → **P80 uniquement** (plus robuste)
- Si données propres → **Formule actuelle** (compromis)

**Pour EUR/USD :**
- P80 uniquement semble plus adapté car :
  1. Différence systématique de ~13% (P80 > moyenne)
  2. Distributions asymétriques (avg ≠ p80)
  3. Plus robuste aux outliers
  4. Plus simple (une seule métrique)

**Fichier de résultats :** `SESSION_VALIDATION_ACTUELLE/outputs/comparison_formula_vs_p80_optimized.csv`

---

## 📋 DÉCISION RECOMMANDÉE

### Pour le Recalcul Immédiat

**✅ RECOMMANDATION : Conserver formule actuelle avec corrections mineures**

**Justification :**
1. Formule validée (Session 123)
2. Fonctionne correctement
3. Simple et maintenable
4. Améliorations peuvent être faites après recalcul

**Corrections à appliquer :**
1. ✅ Corriger normalisation redondante
2. ✅ Documenter choix pondération 50/50
3. ⏳ Valider seuils robustesse (peut être fait après)

### Pour Amélioration Future

**⏳ À ÉTUDIER :**
1. Tester pondération alternative (30/70, 70/30, 100% p80)
2. Valider seuils robustesse empiriquement
3. Intégrer variance dans calcul (Option 3)
4. **Tester P80 uniquement sur recalcul complet** (différence ~13% observée)

### Pour Amélioration Future

**⏳ À ÉTUDIER :**
1. Tester pondération alternative (30/70, 70/30, 100% p80)
2. Valider seuils robustesse empiriquement
3. Intégrer variance dans calcul (Option 3)

---

## 📝 CONCLUSION

**La formule actuelle est mathématiquement valide et acceptable pour le recalcul.**

**Points à retenir :**
- ✅ Fondements mathématiques solides (percentile-based)
- ✅ Robuste partiellement aux outliers
- ⚠️ Perfectible mais fonctionnelle
- ✅ Simple et interprétable

**Action immédiate :**
- Appliquer corrections mineures (normalisation)
- Procéder au recalcul avec formule actuelle
- Étudier améliorations après recalcul

---

## 🔗 RÉFÉRENCES

- **REF-001** : Définitions et règles pour tests
- **REF-002** : Vérification scores empiriques Finnhub
- **REF-003** : Script recalcul scores Finnhub
- **REF-004** : Comparaison scores empiriques
- **Session 123** : Formule validée
- **Script d'analyse** : `SESSION_VALIDATION_ACTUELLE/scripts/analyze_empirical_score_formula.py`

---

**Fin du document REF-005**

