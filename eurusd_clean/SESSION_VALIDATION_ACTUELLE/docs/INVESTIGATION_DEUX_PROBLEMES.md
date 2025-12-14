# Investigation : Deux Problèmes

**Date** : 2025-01-XX  
**Statut** : 🔍 En cours

---

## 🔴 PROBLÈME 1 : Correction Baseline Ne Fonctionne Pas

### Symptôme

Pour 2025-05-29 :
- Correction implémentée : Utiliser `baseline_price_correct` (OPEN première bougie) au lieu de `baseline_price_pattern`
- Résultat attendu : `wave2_peak_pips_absolute = 74.40 pips`
- Résultat observé : `wave2_peak_pips_absolute = 10.3 pips` (valeur de `wave2_real`)

### Cause Probable

Les logs ne montrent pas les valeurs de `baseline_price_correct` ou `wave2_absolute_extended`, ce qui suggère que :
1. Le code n'entre pas dans la section `if not df_extended.empty:`
2. Ou `prices_at_event` est vide
3. Ou les logs sont filtrés

### Vérification Nécessaire

- Vérifier si `df_extended` contient des données
- Vérifier si `prices_at_event` contient des données après `anchor_time`
- Vérifier si `baseline_price_correct` est calculé correctement
- Vérifier si `wave2_absolute_extended` est calculé et si la condition est respectée

---

## 🔴 PROBLÈME 2 : Surprises Positives/Négatives Ne Se Neutralisent Pas

### Question

Est-ce que les événements sont utilisés correctement avec les surprises positives et négatives qui peuvent se neutraliser ?

### Analyse du Code Actuel

#### Dans `scripts/run_pipeline_complete.py` (Étape 6, ligne 1167) :

```python
# Calculer surprise si possible
surprise_pct = 0.0
if actual is not None and estimate is not None and estimate != 0:
    surprise_pct = abs(actual - estimate) / abs(estimate) * 100  # ⚠️ PROBLÈME : abs() empêche neutralisation
```

**Problème** : Utilise `abs()`, donc les surprises positives et négatives ne peuvent pas se neutraliser.

#### Dans `src/core/cluster_impact_calculator.py` (lignes 167-183) :

```python
# SOMME NETTE des surprises (vectorielle)
# Exemple : +10% (CPI) + 12% (Jobless) - 3% (Other) = +19% net
surprise_net = sum(signed_surprises) if signed_surprises else 0.0

# Pour formules existantes, utiliser valeur absolue de la surprise nette
max_surprise = abs(surprise_net)
```

**Solution existante** : Calcule la surprise nette (somme vectorielle) qui permet la neutralisation, puis utilise `abs()` seulement pour l'amplification.

### Problème Identifié

Le pipeline actuel (`scripts/run_pipeline_complete.py`) :
1. **Calcule chaque surprise individuellement avec `abs()`** (ligne 1167)
2. **Somme les impacts individuels** (ligne 1183)
3. **Applique correction vectorielle 0.758** (ligne 1187)

**Cela ne permet PAS la neutralisation** car chaque surprise est déjà en valeur absolue avant la somme.

### Solution Attendue

Selon `cluster_impact_calculator.py`, la logique correcte devrait être :
1. **Calculer surprise signée pour chaque événement** (sans `abs()`)
2. **Calculer surprise nette** (somme vectorielle des surprises signées)
3. **Utiliser `abs(surprise_net)` seulement pour l'amplification**

### Vérification Nécessaire

- Vérifier si le pipeline devrait utiliser la logique de `cluster_impact_calculator.py`
- Vérifier si la solution pour tenir compte de l'incidence des événements a été implémentée
- Vérifier dans la documentation/conversation si cette logique a été validée

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Investiguer pourquoi la correction baseline ne fonctionne pas
2. ⏳ Vérifier si la logique de neutralisation des surprises est utilisée dans le pipeline
3. ⏳ Implémenter la correction si nécessaire

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : 🔍 Investigation en cours




