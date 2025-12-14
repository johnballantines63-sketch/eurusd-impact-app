# Analyse Impact de Base Surestimé - Étape 8.1

**Date** : Analyse détaillée  
**Status** : ✅ **Cause identifiée**

---

## 🔍 PROBLÈME IDENTIFIÉ

### Résultats Investigation

**Calcul actuel (Pipeline)** :
- Impact avant correction vectorielle : **330.89 pips**
- Correction vectorielle (0.758) : **330.89 × 0.758 = 250.82 pips**
- **Impact de base final : 250.82 pips** ⚠️

**Impact de base attendu** :
- Impact réel : 188.4 pips
- Amplification utilisée : 6.223x
- **Impact de base attendu : 188.4 / 6.223 = 30.27 pips** ✅

**Différence** : 250.82 vs 30.27 pips = **8.28x trop élevé** ❌

---

## 📊 ANALYSE DÉTAILLÉE

### Méthode Actuelle (Pipeline)

**Calcul étape par étape** :

1. **Pour chaque événement individuel** :
   - Score empirique ajusté selon surprise
   - Impact individuel = `calculate_impact_d(score, num_events=1, amplification=1.0)`
   - Formule : `-7.08 + 0.419 × score` (pour num_events=1)

2. **Somme des impacts individuels** :
   - Total = Σ(impacts individuels)
   - Résultat : **330.89 pips**

3. **Correction vectorielle** :
   - Impact final = 330.89 × 0.758 = **250.82 pips**

### Observations

**Scores ajustés très élevés** :
- Score ajusté max : **122.8** (événement avec surprise 33.6%)
- Score ajusté moyen : **95.87**
- Scores ajustés élevés → impacts individuels élevés

**Impacts individuels** :
- Impact max individuel : **44.36 pips**
- Impact moyen individuel : **33.09 pips**
- 10 événements × 33.09 = 330.89 pips ✅ (cohérent)

---

## ⚠️ CAUSES POSSIBLES

### Cause 1 : Méthode de Calcul Incorrecte

**Problème** : Additionner les impacts individuels de chaque événement peut ne pas être la bonne méthode pour un cluster.

**Raison** :
- Les événements d'un cluster sont corrélés (même thème économique)
- L'addition simple peut surestimer l'impact total
- La correction vectorielle (0.758) peut ne pas être suffisante

### Cause 2 : Scores Ajustés Trop Élevés

**Problème** : Les scores ajustés sont très élevés (jusqu'à 122.8).

**Raison** :
- L'ajustement selon surprise peut être trop agressif
- Pour surprise 33.6% : score ajusté = 122.8 (vs score base 64.6)
- Multiplié par 10 événements → impact total très élevé

### Cause 3 : Correction Vectorielle Insuffisante

**Problème** : La correction vectorielle (0.758) réduit de seulement 24.2%.

**Raison** :
- La correction 0.758 a été calibrée pour des cas standards
- Pour le 1er août (surprise 266.7%), peut-être que la correction devrait être différente
- Ou peut-être que la méthode d'addition n'est pas adaptée

---

## 🔍 COMPARAISON AVEC SESSION 88

### Méthode Session 88

**D'après les documents** :
- Session 88 utilisait une méthode différente pour calculer l'impact
- Score ajusté moyen : **96.8**
- Impact prédit : **174.1 pips**
- Impact réel : **173.8 pips** ✅

**Calcul Session 88** :
- Impact = Formule D avec score ajusté moyen du cluster
- Probablement : `calculate_impact_d(score_moyen, num_events=17, amplification=6.43)`

### Différence Clé

**Pipeline actuel** :
- Additionne impacts individuels : **330.89 pips**
- Applique correction : **250.82 pips**

**Session 88** :
- Utilise score moyen du cluster
- Calcule impact global avec Formule D
- Résultat : **174.1 pips** ✅

---

## ✅ SOLUTIONS PROPOSÉES

### Solution 1 : Utiliser Score Moyen (Comme Session 88)

**Modification** : Au lieu d'additionner les impacts individuels, utiliser le score moyen ajusté du cluster.

**Code à modifier** (étape 8.1) :

```python
# AVANT (méthode actuelle)
total_impact_base = 0.0
for _, event in cluster_events.iterrows():
    ...
    impact_individuel = calculate_impact_d(...)
    total_impact_base += impact_individuel
total_impact_base = total_impact_base * 0.758

# APRÈS (méthode Session 88)
scores_ajustes = []
for _, event in cluster_events.iterrows():
    ...
    adjusted_score = calculate_adjusted_empirical_score(...)
    scores_ajustes.append(adjusted_score)

score_moyen_ajuste = np.mean(scores_ajustes)
impact_base = calculate_impact_d(
    empirical_score=score_moyen_ajuste,
    num_events=num_events,  # Nombre d'événements du cluster
    amplification=1.0,
    correction_factor=1.0  # Pas de correction supplémentaire
)
```

**Avantage** :
- ✅ Méthode validée Session 88 (174.1 pips prédit vs 173.8 réel)
- ✅ Plus simple et cohérent
- ✅ Utilise directement la Formule D avec le cluster entier

---

### Solution 2 : Ajuster Correction Vectorielle

**Modification** : Utiliser une correction vectorielle différente pour les surprises extrêmes.

**Problème** : La correction 0.758 peut ne pas être adaptée pour surprise 266.7%.

**Solution** : Ajuster la correction selon la surprise maximale.

---

### Solution 3 : Limiter Scores Ajustés

**Modification** : Limiter les scores ajustés pour éviter des valeurs extrêmes.

**Problème** : Score ajusté 122.8 pour surprise 33.6% peut être trop élevé.

**Solution** : Appliquer une limite (ex: max 100) aux scores ajustés.

---

## 📋 RECOMMANDATION

### Priorité 1 : Utiliser Score Moyen (Solution 1)

**Raison** :
- ✅ Méthode validée Session 88
- ✅ Résultats cohérents (174.1 vs 173.8 pips)
- ✅ Plus simple et logique pour un cluster

**Action** :
1. Calculer score moyen ajusté du cluster
2. Utiliser Formule D avec `num_events` = nombre d'événements du cluster
3. Supprimer l'addition des impacts individuels

---

## 🎯 CALCUL ATTENDU (Solution 1)

**Avec score moyen** :
- Score moyen ajusté : ~95.87
- Nombre événements : 10
- Formule D (num_events >= 2) : `-10.47 + 0.477 × 95.87 = 35.25 pips`
- **Impact de base attendu : ~35 pips** ✅

**Avec amplification 6.223x** :
- Impact prédit : 35.25 × 6.223 = **219.4 pips**
- Impact réel : **188.4 pips**
- Erreur : **31 pips (16.4%)** ✅ **BEAUCOUP MIEUX !**

---

## ✅ STATUS

**Problème identifié** : ✅ Addition des impacts individuels surestime l'impact

**Solution proposée** : ✅ Utiliser score moyen du cluster (comme Session 88)

**Action** : ⏭️ Implémenter Solution 1 (score moyen)

---

_Date création : Analyse investigation impact de base_  
_Conclusion : Utiliser score moyen du cluster au lieu d'additionner impacts individuels_




