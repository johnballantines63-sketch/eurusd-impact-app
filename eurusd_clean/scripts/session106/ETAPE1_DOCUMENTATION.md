# 📊 SESSION 106 - DOCUMENTATION ÉTAPE 1

**Date :** 2 novembre 2025  
**Étape :** Analyse événements 11.09.2025  
**Script :** `step1_analyze_events_11_09.py`

---

## 🎯 OBJECTIF

Analyser les 11 événements CPI du 11.09.2025 pour comprendre comment construire la formule `calculate_adjusted_empirical_score()` qui doit donner **84.2**.

---

## 📊 RÉSULTATS ANALYSE

### Données brutes

**11 événements chargés :**
- 9 événements famille "Inflation"
- 2 événements famille "Other"

**Statistiques globales :**
```
Score empirique moyen : 44.31
Score empirique max   : 46.13 (inflation rate_yoy)
Score empirique min   : 40.78 (real earnings)
σ                     : 1.67

Surprise moyenne      : 3.73%
Surprise max          : 33.33% (inflation rate_mom) ⭐
Surprise min          : 0.00%
σ                     : 11.10%
```

### Événements dominants

**Top 3 scores :**
1. `inflation rate_yoy` : score=46.1, surprise=0.00%
2. `core inflation rate_yoy` : score=45.9, surprise=0.00%
3. `inflation rate_mom` : score=45.7, surprise=**33.33%** ⭐

**Top 3 surprises :**
1. `inflation rate_mom` : surprise=**33.33%**, score=45.7 ⭐⭐⭐
2. `cpi s.a` : surprise=0.11%, score=44.7
3. `cpi s a` : surprise=0.11%, score=42.0

**Corrélation score ↔ surprise : +0.268** (faible mais positive)

---

## ⚠️ PROBLÈME IDENTIFIÉ

### Événements sans estimate (NaN)

**2 événements sur 11 n'ont pas d'estimate :**
```
real earnings_mom : actual=-0.100, estimate=NaN, surprise=NaN, score=43.2
real earnings     : actual=-0.100, estimate=NaN, surprise=NaN, score=40.8
```

**Implications :**
- 18% des événements n'ont pas de surprise calculable
- Ils ont quand même un score empirique valide
- **Question :** Comment les intégrer dans la formule ?

**Options :**
1. **Exclure** ces événements du calcul (risqué - perte d'info)
2. **Surprise = 0** pour ces événements (conservateur)
3. **Pondération par score uniquement** pour ces événements

---

## 🔍 INSIGHTS CLÉS

### 1. Événement dominant unique ⭐

**`inflation rate_mom` est LE driver :**
- Seul événement avec surprise significative (33.33%)
- Score empirique élevé (45.7)
- **C'est cet événement qui explique l'amplification nécessaire !**

### 2. Amplification nécessaire

**Pour passer de 44.31 → 84.2 :**
```
Amplification = 84.2 / 44.31 = 1.900×
```

**Hypothèse formule simple :**
```python
# Option 1 : Moyenne pondérée par (1 + surprise)
weights = 1 + surprises  # Pour inflation_mom : 1 + 0.333 = 1.333
score_adjusted = mean_weighted(scores, weights)

# Vérification rapide :
# - 9 événements avec surprise ~0 : poids ≈ 1
# - 1 événement avec surprise 33.33% : poids = 1.333
# - 2 événements sans surprise : poids = 1 (ou exclus)

# Moyenne pondérée attendue :
# (9 × 44.8 × 1.0 + 1 × 45.7 × 1.333 + 2 × 42.0 × 1.0) / 11
# = (403.2 + 60.9 + 84.0) / 11
# = 548.1 / 11
# = 49.8

# ❌ Trop faible ! Doit donner 84.2, pas 49.8
```

**Option 1 ne marche pas !** L'amplification 1.9× par surprise n'est pas suffisante.

### 3. Analyse plus profonde nécessaire

**Pistes à explorer :**

**A) Amplification non-linéaire de la surprise**
```python
# Surprise 33.33% → amplification exponentielle ?
amplification = 1 + (surprise ** k)  # k > 1
```

**B) Score maximum amplifié**
```python
# Prendre le score max et l'amplifier par surprise
score_adjusted = max(scores) * (1 + max(surprise))
# = 46.13 × (1 + 0.333) = 46.13 × 1.333 = 61.5
# ❌ Encore trop faible !
```

**C) Combinaison linéaire calibrée**
```python
# Formule à 2 paramètres (alpha, beta)
score_adjusted = alpha × mean(scores) + beta × max(scores) × (1 + surprise_max)
```

**D) Somme amplifiée**
```python
# Somme des scores, amplifiée par surprise max
score_adjusted = sum(scores) / num_events × (1 + k × surprise_max)
```

---

## 🎯 OBJECTIF CALIBRATION

**Cible :** score_adjusted = 84.2

**Contraintes :**
1. Doit gérer événements sans estimate (NaN)
2. Doit amplifier suffisamment (1.9× simple insuffisant)
3. Doit rester scientifiquement justifiable
4. Pas d'over-fitting sur un seul cas

---

## 📋 PROCHAINE ÉTAPE

**ÉTAPE 2 : Tester formulations**

**Plan :**
1. Tester Option A (amplification non-linéaire)
2. Tester Option B (score max amplifié)
3. Tester Option C (combinaison linéaire calibrée)
4. Tester Option D (somme amplifiée)
5. Sélectionner formule qui donne ~84.2
6. Valider cohérence (amp=2.5 → 56.3 pips)

---

## 💾 FICHIERS GÉNÉRÉS

```
scripts/session106/
├── events_11_09_analysis.csv       ✅ Données brutes
└── events_11_09_analysis.json      ✅ Format JSON
```

---

**Conclusion Étape 1 :**
- ✅ Données chargées et analysées
- ✅ Problème NaN identifié (2 événements)
- ✅ Événement dominant : inflation_rate_mom (33.33% surprise)
- ⚠️ Formule simple (moyenne pondérée) insuffisante
- 🎯 Besoin formulation plus sophistiquée pour atteindre 84.2

**Prêt pour Étape 2 : Test formulations** 🚀
