# Résumé : Deux Problèmes et Solutions

**Date** : 2025-01-XX  
**Statut** : ✅ Problèmes identifiés, solutions proposées

---

## 🔴 PROBLÈME 1 : Correction Baseline Ne Fonctionne Pas

### Symptôme

Pour 2025-05-29 :
- Correction implémentée : Utiliser `baseline_price_correct` (OPEN première bougie) au lieu de `baseline_price_pattern`
- Résultat attendu : `wave2_peak_pips_absolute = 74.40 pips`
- Résultat observé : `wave2_peak_pips_absolute = 10.3 pips` (valeur de `wave2_real`)

### Cause Probable

Les logs ne montrent pas les valeurs de `baseline_price_correct` ou `wave2_absolute_extended`, ce qui suggère que le code n'entre pas dans la section ou que `prices_at_event` est vide.

### Solution

Vérifier et corriger la logique pour s'assurer que :
1. `df_extended` contient des données
2. `prices_at_event` contient des données après `anchor_time`
3. `baseline_price_correct` est calculé correctement
4. Les logs sont affichés correctement

---

## 🔴 PROBLÈME 2 : Surprises Positives/Négatives Ne Se Neutralisent Pas

### Problème Identifié

**Dans le pipeline actuel** (`scripts/run_pipeline_complete.py`, lignes 1167, 1367) :

```python
# ⚠️ PROBLÈME : Utilise abs() pour chaque surprise individuelle
surprise_pct = abs(actual - estimate) / abs(estimate) * 100
```

**Cela empêche la neutralisation** car chaque surprise est déjà en valeur absolue avant la somme.

### Solution Validée (Session 113)

**Documentation** : `docs/sessions/RAPPORT_SESSION_113.md`

**Correction majeure** :
- **AVANT (mauvais)** : `max_surprise = max(abs(surprises))`  # 100%
- **APRÈS (correct)** : `surprise_net = sum(signed_surprises)`  # 15.26%

**Implémentation existante** : `src/core/cluster_impact_calculator.py` (lignes 167-183)

```python
# SOMME NETTE des surprises (vectorielle)
# Exemple : +10% (CPI) + 12% (Jobless) - 3% (Other) = +19% net
surprise_net = sum(signed_surprises) if signed_surprises else 0.0

# Pour formules existantes, utiliser valeur absolue de la surprise nette
max_surprise = abs(surprise_net)
```

### Solution à Implémenter

Modifier `scripts/run_pipeline_complete.py` pour :
1. **Calculer surprise signée pour chaque événement** (sans `abs()`)
2. **Calculer surprise nette** (somme vectorielle des surprises signées)
3. **Utiliser `abs(surprise_net)` seulement pour l'amplification**

**Référence** : Session 113 - Correction calcul surprise - MAJEURE

---

## 📋 PROCHAINES ÉTAPES

1. ⏳ Investiguer et corriger le problème 1 (baseline)
2. ⏳ Implémenter la correction Session 113 pour le problème 2 (neutralisation)
3. ⏳ Tester sur 2025-05-29 et autres dates

---

**Dernière mise à jour** : 2025-01-XX  
**Statut** : ✅ Problèmes identifiés, solutions proposées




